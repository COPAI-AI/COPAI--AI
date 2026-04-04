"""
Khmer/English scanned PDF extraction service.
Renders PDF pages as images, sends to vLLM vision for OCR.
Use for scanned PDFs before uploading to Open WebUI.

Usage:
  curl -X POST http://localhost:8002/extract \
    -F "file=@scanned_doc.pdf" \
    --output extracted.txt
"""

import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
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


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/extract", response_class=PlainTextResponse)
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files supported")

    content = await file.read()
    try:
        images = convert_from_bytes(content, dpi=200)
    except Exception as e:
        raise HTTPException(500, f"PDF conversion failed: {e}")

    pages = []
    for i, img in enumerate(images):
        try:
            text = extract_page(img)
            pages.append(f"--- Page {i+1} ---\n\n{text}")
        except Exception as e:
            pages.append(f"--- Page {i+1} ---\n\n[Extraction failed: {e}]")

    return "\n\n".join(pages)
