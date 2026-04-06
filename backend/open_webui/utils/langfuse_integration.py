"""
Langfuse integration for Open WebUI.

Provides LLM tracing, RAG retrieval spans, and async RAGAS evaluation.
All public functions are individually exception-safe — Langfuse errors never
propagate to the caller or interrupt chat completions.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from loguru import logger as log

# Module-level singleton — set by initialize_langfuse_client()
_langfuse_client = None


def initialize_langfuse_client(
    host: str, public_key: str, secret_key: str
) -> Optional[object]:
    """
    Initialize the Langfuse SDK client. Called once at app startup.
    Returns the client, or None if credentials are missing / SDK unavailable.
    """
    global _langfuse_client
    if not public_key or not secret_key:
        log.info("Langfuse: public_key or secret_key not set — tracing disabled.")
        _langfuse_client = None
        return None
    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        log.info(f"Langfuse client initialized (host={host})")
        try:
            ok = _langfuse_client.auth_check()
            if ok:
                log.info("Langfuse auth_check passed — credentials valid.")
            else:
                log.warning(
                    "Langfuse auth_check FAILED — check LANGFUSE_PUBLIC_KEY / SECRET_KEY and host."
                )
        except Exception as auth_exc:
            log.warning(f"Langfuse auth_check error: {auth_exc}")
    except Exception as exc:
        log.warning(f"Langfuse client initialization failed: {exc}")
        _langfuse_client = None
    return _langfuse_client


def shutdown_langfuse_client() -> None:
    """Flush all pending traces and shut down the background worker."""
    global _langfuse_client
    if _langfuse_client is None:
        return
    try:
        _langfuse_client.flush()
        log.info("Langfuse: flushed pending traces on shutdown.")
    except Exception as exc:
        log.debug(f"Langfuse shutdown flush error: {exc}")


def get_langfuse_client() -> Optional[object]:
    return _langfuse_client


def start_trace(
    *,
    trace_id: str,
    user_id: str,
    session_id: Optional[str],
    chat_id: Optional[str],
    model_id: str,
    input_messages: list,
    metadata: dict,
) -> Optional[object]:
    """
    Create a Langfuse trace for a chat completion request.
    Returns the trace object, or None if Langfuse is unavailable.
    """
    client = get_langfuse_client()
    if client is None:
        return None
    try:
        trace = client.trace(
            id=trace_id,
            name="chat_completion",
            user_id=str(user_id),
            session_id=session_id,
            metadata={
                "chat_id": chat_id,
                "model_id": model_id,
                **{
                    k: v
                    for k, v in metadata.items()
                    if k not in ("files",) and isinstance(v, (str, int, float, bool))
                },
            },
            input=input_messages,
        )
        return trace
    except Exception as exc:
        log.debug(f"Langfuse start_trace error: {exc}")
        return None


def start_retrieval_span(
    trace,
    *,
    query: str,
    files: list,
    top_k: int,
) -> Optional[object]:
    """
    Create a 'rag_retrieval' child span under the given trace.
    Returns the span object, or None.
    """
    if trace is None:
        return None
    try:
        span = trace.span(
            name="rag_retrieval",
            input={"query": query, "top_k": top_k, "file_count": len(files)},
        )
        return span
    except Exception as exc:
        log.debug(f"Langfuse start_retrieval_span error: {exc}")
        return None


def end_retrieval_span(span, *, sources: list) -> None:
    """
    Finalise the retrieval span with the retrieved documents.
    """
    if span is None:
        return
    try:
        contexts = []
        for source in sources:
            for doc, meta in zip(
                source.get("document", []), source.get("metadata", [])
            ):
                contexts.append(
                    {
                        "content": doc[:500] if doc else "",  # truncate for readability
                        "file_id": meta.get("file_id"),
                        "name": meta.get("name"),
                        "score": meta.get("score"),
                    }
                )
        span.end(
            output={"contexts": contexts, "retrieved_count": len(contexts)}
        )
    except Exception as exc:
        log.debug(f"Langfuse end_retrieval_span error: {exc}")


def log_generation(
    trace,
    *,
    model_id: str,
    input_messages: list,
    output_content: str,
    usage: Optional[dict],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
) -> None:
    """
    Log the LLM generation event on the trace and update the trace output.
    """
    if trace is None:
        return
    try:
        gen_kwargs = dict(
            name="llm_generation",
            model=model_id,
            input=input_messages,
            output=output_content,
        )
        if start_time:
            gen_kwargs["start_time"] = start_time
        if end_time:
            gen_kwargs["end_time"] = end_time
        if usage:
            _in = usage.get("prompt_tokens") or usage.get("prompt_eval_count")
            _out = usage.get("completion_tokens") or usage.get("eval_count")
            gen_kwargs["usage"] = {
                "input": _in,
                "output": _out,
                "total": usage.get("total_tokens") or ((_in or 0) + (_out or 0)) or None,
                "unit": "TOKENS",
            }
        trace.generation(**gen_kwargs)
        trace.update(output=output_content)
    except Exception as exc:
        log.debug(f"Langfuse log_generation error: {exc}")


async def run_ragas_evaluation(
    trace,
    *,
    question: str,
    answer: str,
    contexts: list[str],
) -> None:
    """
    Run RAGAS evaluation in a thread executor (RAGAS is synchronous/CPU-bound)
    and submit metric scores to Langfuse. Silently no-ops on any error.
    """
    if trace is None or not contexts or not answer:
        return
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            _ragas_evaluate_sync,
            trace,
            question,
            answer,
            contexts,
        )
    except Exception as exc:
        log.debug(f"Langfuse RAGAS async wrapper error: {exc}")


def _ragas_evaluate_sync(
    trace,
    question: str,
    answer: str,
    contexts: list[str],
) -> None:
    """Synchronous RAGAS evaluation — runs inside a thread executor."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
        )

        dataset = Dataset.from_dict(
            {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
        )

        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )

        scores = result.to_pandas().iloc[0].to_dict()
        metric_keys = ["faithfulness", "answer_relevancy", "context_precision"]

        for name in metric_keys:
            value = scores.get(name)
            if value is not None:
                try:
                    trace.score(name=name, value=float(value))
                except Exception as exc:
                    log.debug(f"Langfuse score submission failed for {name}: {exc}")

    except ImportError:
        log.warning(
            "RAGAS or datasets package not installed; "
            "install ragas>=0.1.21 and datasets>=2.19.0 to enable evaluation."
        )
    except Exception as exc:
        log.debug(f"RAGAS evaluation error: {exc}")
