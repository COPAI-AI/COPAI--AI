"""
Khmer/English PDF extraction service.
Renders PDF pages as images, sends to vLLM vision for OCR.

Two modes:
  1. Manual: POST /extract  — returns plain text
  2. Auto:   PUT  /tika     — Tika-compatible API for Open WebUI integration
"""

import os
import base64
import requests
import fitz  # pymupdf
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pdf2image import convert_from_bytes
from PIL import Image
import io

app = FastAPI(title="COPAI Extraction Service")

VLLM_URL = os.getenv("VLLM_URL", "http://127.0.0.1:8000/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma-sealion-v4")

EXTRACT_PROMPT = """Extract ALL text from this document page exactly as it appears.
- Preserve Khmer text (ភាសាខ្មែរ) accurately
- Preserve English text accurately
- For tables: format as markdown table
- For lists: format as bullet points
- For headings: use markdown headings (#, ##)
- Output only the extracted text, no commentary"""


def image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def extract_page(img: Image.Image) -> str:
    b64 = image_to_base64(img)
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{b64}"
                    }},
                    {"type": "text", "text": EXTRACT_PROMPT}
                ]
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.0
    }
    resp = requests.post(VLLM_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


MIN_CHARS_EMBEDDED = 50  # pages with fewer chars are treated as scanned images


def extract_pdf_bytes(content: bytes) -> str:
    # Try embedded text first (fast — milliseconds)
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        embedded_pages = []
        image_page_indices = []

        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if len(text) >= MIN_CHARS_EMBEDDED:
                embedded_pages.append((i, text))
            else:
                image_page_indices.append(i)

        doc.close()

        # All pages have embedded text — return immediately, no vLLM needed
        if not image_page_indices:
            return "\n\n".join(
                f"--- Page {i+1} ---\n\n{text}" for i, text in embedded_pages
            )

    except Exception:
        embedded_pages = []
        image_page_indices = list(range(0))  # will be filled below

    # Some or all pages need vision OCR — render only those pages
    try:
        images = convert_from_bytes(content, dpi=200)
    except Exception as e:
        raise HTTPException(500, f"PDF conversion failed: {e}")

    if not image_page_indices:
        # embed extraction above failed entirely — process all pages
        image_page_indices = list(range(len(images)))

    # Build result: use embedded text where available, vLLM for image pages
    embedded_map = {i: text for i, text in embedded_pages}
    pages = []
    for i, img in enumerate(images):
        if i in embedded_map:
            pages.append(f"--- Page {i+1} ---\n\n{embedded_map[i]}")
        else:
            try:
                text = extract_page(img)
                pages.append(f"--- Page {i+1} ---\n\n{text}")
            except Exception as e:
                pages.append(f"--- Page {i+1} ---\n\n[Extraction failed: {e}]")

    return "\n\n".join(pages)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


# ── Manual endpoint ────────────────────────────────────────────────────────────
@app.post("/extract", response_class=PlainTextResponse)
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")
    content = await file.read()
    return extract_pdf_bytes(content)


# ── Tika-compatible endpoint for Open WebUI ────────────────────────────────────
# Open WebUI sends: PUT /tika with raw file bytes in request body
# Content-Type header tells us the file type
# Returns: plain text
@app.put("/tika", response_class=PlainTextResponse)
async def tika(request: Request):
    content_type = request.headers.get("content-type", "")
    content = await request.body()

    if not content:
        raise HTTPException(400, "Empty request body")

    # Only process PDFs — pass other types back as-is (Open WebUI handles them)
    if "pdf" not in content_type.lower():
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    return extract_pdf_bytes(content)


# ── Tika /tika/text endpoint (Open WebUI calls this path) ─────────────────────
@app.put("/tika/text", response_class=PlainTextResponse)
async def tika_text(request: Request):
    content_type = request.headers.get("content-type", "")
    content = await request.body()

    if not content:
        raise HTTPException(400, "Empty request body")

    if "pdf" not in content_type.lower():
        try:
            return content.decode("utf-8", errors="replace")
        except Exception:
            return ""

    return extract_pdf_bytes(content)


# ── Tika meta endpoint (Open WebUI checks this) ────────────────────────────────
@app.get("/tika", response_class=PlainTextResponse)
async def tika_meta():
    return "This is Tika Server (COPAI custom extraction). Apache Tika 2.0.0."
