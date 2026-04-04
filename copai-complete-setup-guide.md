# COPAI Ministry RAG — Complete Setup Guide
### Gemma-SEA-LION-v4 · vLLM · Qdrant · Langfuse · Prometheus · Grafana
### MISTI HPC — A40 48GB — Fresh Install

---

## Architecture at a Glance

```
                        ┌─────────────────────────────────┐
                        │         MISTI HPC Host          │
                        │                                 │
  Ministry Users        │  ┌─────────────────────────┐   │
  ──────────────►  8080 │  │      Open WebUI         │   │
                        │  │  (custom build)         │   │
                        │  └────┬──────────┬──────────┘   │
                        │       │          │               │
                        │  8000 ▼          │ 6333          │
                        │  ┌─────────┐  ┌──▼──────┐       │
                        │  │  vLLM   │  │  Qdrant │       │
                        │  │ SEA-LION│  │ vectors │       │
                        │  │  FP8    │  └─────────┘       │
                        │  └─────────┘                    │
                        │                                 │
                        │  ── Monitoring ─────────────    │
                        │  3000  Langfuse  (traces)       │
                        │  9090  Prometheus (metrics)     │
                        │  3001  Grafana   (dashboards)   │
                        └─────────────────────────────────┘
```

**Ports reference:**
| Service | Port |
|---|---|
| Open WebUI | 8080 |
| vLLM | 8000 |
| Qdrant | 6333 |
| Extraction utility | 8002 |
| Langfuse | 3000 |
| PostgreSQL (Langfuse) | 5432 |
| ClickHouse (Langfuse) | 8123 |
| Redis (Langfuse) | 6379 |
| MinIO (Langfuse) | 9010 |
| Prometheus | 9090 |
| Grafana | 3001 |
| Node Exporter | 9100 |

---

## Prerequisites

```bash
# 1. Check GPU
nvidia-smi
# Need: A40, Driver >= 525

# 2. Check CUDA
nvcc --version
# Need: CUDA >= 12.1

# 3. Check Docker
docker --version
docker compose version
# Need: Docker >= 24, Compose >= 2.20

# 4. Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
# Must show GPU. If not, install toolkit:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# 5. Check disk space
df -h ~
# Need: >= 100GB free (model is 30GB, traces/metrics add up)
```

---

## Step 1 — Project Structure

```bash
mkdir -p ~/copai-stack
cd ~/copai-stack

mkdir -p \
  models \
  extraction \
  prometheus \
  grafana/provisioning/datasources \
  grafana/provisioning/dashboards \
  static
```

Your final directory layout:

```
~/copai-stack/
├── .env                          ← all secrets/config
├── docker-compose.yml            ← all services
├── Dockerfile                    ← custom Open WebUI build
├── static/                       ← your custom static files
├── models/                       ← downloaded model weights
├── extraction/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── prometheus/
│   └── prometheus.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── prometheus.yml
        └── dashboards/
            └── dashboards.yml
```

---

## Step 2 — Environment File

Create `~/copai-stack/.env`:

```env
# ── Open WebUI ────────────────────────────────────────────
WEBUI_SECRET_KEY=change-this-to-a-random-64-char-string
OPEN_WEBUI_PORT=8080
WEBUI_URL=https://chat.copai.ai

# ── Langfuse ──────────────────────────────────────────────
# Generated after Langfuse first boot — fill in after Step 9
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Langfuse internal secrets — generate random values
LANGFUSE_SALT=change-this-random-32-char-string
LANGFUSE_ENCRYPTION_KEY=change-this-to-64-char-hex-string
NEXTAUTH_SECRET=change-this-random-32-char-string

# Langfuse DB
POSTGRES_USER=langfuse
POSTGRES_PASSWORD=change-this-strong-password
POSTGRES_DB=langfuse

# Langfuse ClickHouse
CLICKHOUSE_USER=clickhouse
CLICKHOUSE_PASSWORD=change-this-strong-password

# Langfuse MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change-this-strong-password

# ── Grafana ───────────────────────────────────────────────
GF_SECURITY_ADMIN_PASSWORD=change-this-strong-password
```

Generate secure random values:
```bash
# For LANGFUSE_SALT and NEXTAUTH_SECRET (32 chars)
openssl rand -hex 16

# For LANGFUSE_ENCRYPTION_KEY (64 hex chars)
openssl rand -hex 32

# For WEBUI_SECRET_KEY
openssl rand -hex 32
```

---

## Step 3 — Download the Model

```bash
cd ~/copai-stack

pip install huggingface_hub hf_transfer

export HF_HUB_ENABLE_HF_TRANSFER=1

huggingface-cli download \
  aisingapore/Gemma-SEA-LION-v4-27B-IT-FP8-Dynamic \
  --local-dir ./models/Gemma-SEA-LION-v4-27B-IT-FP8-Dynamic

# Verify
ls ./models/Gemma-SEA-LION-v4-27B-IT-FP8-Dynamic/
# Should show: config.json, model files, tokenizer files
```

> Takes 20–40 min depending on internet speed. Model is ~28GB.

---

## Step 4 — Open WebUI Dockerfile

Create `~/copai-stack/Dockerfile`:

```dockerfile
FROM ghcr.io/open-webui/open-webui:main

# Extra deps for sentence-transformers (embedding model)
RUN pip install --no-cache-dir \
    sentence-transformers \
    docling \
    pdf2image \
    pytesseract

# Khmer Tesseract language pack
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-khm \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

---

## Step 5 — Extraction Service

This is a utility service for **scanned Khmer PDFs** that can't be parsed by Docling. It renders pages as images and sends them to your vLLM vision endpoint.

### `extraction/requirements.txt`
```
fastapi==0.115.0
uvicorn==0.30.0
pdf2image==1.17.0
Pillow==10.4.0
requests==2.32.0
python-multipart==0.0.9
```

### `extraction/Dockerfile`
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### `extraction/main.py`
```python
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
```

---

## Step 6 — Prometheus Config

Create `~/copai-stack/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: vllm
    static_configs:
      - targets: ['127.0.0.1:8000']
    metrics_path: /metrics

  - job_name: node
    static_configs:
      - targets: ['127.0.0.1:9100']

  - job_name: qdrant
    static_configs:
      - targets: ['127.0.0.1:6333']
    metrics_path: /metrics
```

---

## Step 7 — Grafana Provisioning

### `grafana/provisioning/datasources/prometheus.yml`
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://127.0.0.1:9090
    isDefault: true
    editable: true
```

### `grafana/provisioning/dashboards/dashboards.yml`
```yaml
apiVersion: 1
providers:
  - name: default
    folder: COPAI
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

After Grafana starts, import the official vLLM dashboard:
- Go to `http://YOUR_IP:3001`
- Dashboards → Import → ID `25043` → Load → Select Prometheus → Import

---

## Step 8 — Main docker-compose.yml

Create `~/copai-stack/docker-compose.yml`:

```yaml
# COPAI Ministry RAG Stack
# All services use network_mode: host — no Docker networking needed

services:

  # ── LLM Server ──────────────────────────────────────────
  vllm:
    image: vllm/vllm-openai:latest
    container_name: copai-vllm
    network_mode: host
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    volumes:
      - ./models:/models
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - HF_HOME=/root/.cache/huggingface
    command: >
      --model /models/Gemma-SEA-LION-v4-27B-IT-FP8-Dynamic
      --served-model-name gemma-sealion-v4
      --host 0.0.0.0
      --port 8000
      --max-model-len 65536
      --max-num-seqs 40
      --gpu-memory-utilization 0.88
      --dtype bfloat16
      --trust-remote-code
      --disable-log-requests
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s

  # ── Vector Database ──────────────────────────────────────
  qdrant:
    image: qdrant/qdrant:latest
    container_name: copai-qdrant
    network_mode: host
    restart: unless-stopped
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334

  # ── Open WebUI ───────────────────────────────────────────
  open-webui:
    build:
      context: .
      dockerfile: Dockerfile
    image: copai-webui:latest
    container_name: copai-webui
    network_mode: host
    restart: unless-stopped
    depends_on:
      vllm:
        condition: service_healthy
      qdrant:
        condition: service_started
    volumes:
      - open_webui_data:/app/backend/data
      - ./static:/app/static/custom:ro
    environment:
      # LLM — vLLM via OpenAI-compatible API
      - OPENAI_API_BASE_URL=http://127.0.0.1:8000/v1
      - OPENAI_API_KEY=not-required
      - OLLAMA_BASE_URL=

      # Auth
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}
      - WEBUI_URL=${WEBUI_URL}
      - PORT=${OPEN_WEBUI_PORT:-8080}

      # Vector store
      - VECTOR_DB=qdrant
      - QDRANT_URI=http://127.0.0.1:6333

      # Embedding — loaded locally via sentence-transformers
      - RAG_EMBEDDING_ENGINE=sentence_transformers
      - RAG_EMBEDDING_MODEL=aisingapore/SEA-LION-E5-Embedding-600M

      # Content extraction — docling for digital PDFs
      - RAG_CONTENT_EXTRACTION_ENGINE=docling

      # RAG performance — KV cache efficiency
      - RAG_SYSTEM_CONTEXT=true
      - RAG_EMBEDDING_BATCH_SIZE=16
      - ENABLE_ASYNC_EMBEDDING=true

      # Langfuse tracing
      - ENABLE_LANGFUSE=true
      - LANGFUSE_HOST=http://127.0.0.1:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}

      # Disable broken features
      - ENABLE_RAGAS_EVALUATION=false

  # ── PDF Extraction Utility ───────────────────────────────
  extraction:
    build:
      context: ./extraction
    container_name: copai-extraction
    network_mode: host
    restart: unless-stopped
    environment:
      - VLLM_URL=http://127.0.0.1:8000/v1/chat/completions
      - MODEL_NAME=gemma-sealion-v4

  # ── Langfuse: PostgreSQL ─────────────────────────────────
  langfuse-postgres:
    image: postgres:15-alpine
    container_name: copai-langfuse-postgres
    network_mode: host
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - PGPORT=5432
    volumes:
      - langfuse_postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Langfuse: ClickHouse ─────────────────────────────────
  langfuse-clickhouse:
    image: clickhouse/clickhouse-server:24.12
    container_name: copai-langfuse-clickhouse
    network_mode: host
    restart: unless-stopped
    environment:
      - CLICKHOUSE_USER=${CLICKHOUSE_USER}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
      - CLICKHOUSE_DB=default
    volumes:
      - langfuse_clickhouse:/var/lib/clickhouse
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Langfuse: Redis ──────────────────────────────────────
  langfuse-redis:
    image: redis:7-alpine
    container_name: copai-langfuse-redis
    network_mode: host
    restart: unless-stopped
    command: redis-server --port 6379
    volumes:
      - langfuse_redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-p", "6379", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Langfuse: MinIO (blob storage) ──────────────────────
  langfuse-minio:
    image: minio/minio:latest
    container_name: copai-langfuse-minio
    network_mode: host
    restart: unless-stopped
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
    command: server /data --address ":9010" --console-address ":9011"
    volumes:
      - langfuse_minio:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:9010/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Langfuse: Web + Worker ───────────────────────────────
  langfuse-web:
    image: langfuse/langfuse:latest
    container_name: copai-langfuse-web
    network_mode: host
    restart: unless-stopped
    depends_on:
      langfuse-postgres:
        condition: service_healthy
      langfuse-clickhouse:
        condition: service_healthy
      langfuse-redis:
        condition: service_healthy
      langfuse-minio:
        condition: service_healthy
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}
      - CLICKHOUSE_MIGRATION_URL=clickhouse://127.0.0.1:9000
      - CLICKHOUSE_URL=http://127.0.0.1:8123
      - CLICKHOUSE_USER=${CLICKHOUSE_USER}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
      - REDIS_HOST=127.0.0.1
      - REDIS_PORT=6379
      - BLOB_STORAGE_ENDPOINT=http://127.0.0.1:9010
      - BLOB_STORAGE_ACCESS_KEY_ID=${MINIO_ROOT_USER}
      - BLOB_STORAGE_SECRET_ACCESS_KEY=${MINIO_ROOT_PASSWORD}
      - BLOB_STORAGE_BUCKET_NAME=langfuse
      - NEXTAUTH_URL=http://127.0.0.1:3000
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - SALT=${LANGFUSE_SALT}
      - ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}
      - PORT=3000
      - HOSTNAME=0.0.0.0
      - LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=true

  langfuse-worker:
    image: langfuse/langfuse-worker:latest
    container_name: copai-langfuse-worker
    network_mode: host
    restart: unless-stopped
    depends_on:
      langfuse-postgres:
        condition: service_healthy
      langfuse-clickhouse:
        condition: service_healthy
      langfuse-redis:
        condition: service_healthy
      langfuse-minio:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:5432/${POSTGRES_DB}
      - CLICKHOUSE_MIGRATION_URL=clickhouse://127.0.0.1:9000
      - CLICKHOUSE_URL=http://127.0.0.1:8123
      - CLICKHOUSE_USER=${CLICKHOUSE_USER}
      - CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD}
      - REDIS_HOST=127.0.0.1
      - REDIS_PORT=6379
      - BLOB_STORAGE_ENDPOINT=http://127.0.0.1:9010
      - BLOB_STORAGE_ACCESS_KEY_ID=${MINIO_ROOT_USER}
      - BLOB_STORAGE_SECRET_ACCESS_KEY=${MINIO_ROOT_PASSWORD}
      - BLOB_STORAGE_BUCKET_NAME=langfuse
      - SALT=${LANGFUSE_SALT}
      - ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}

  # ── Prometheus ───────────────────────────────────────────
  prometheus:
    image: prom/prometheus:latest
    container_name: copai-prometheus
    network_mode: host
    restart: unless-stopped
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=30d
      - --web.listen-address=0.0.0.0:9090

  # ── Node Exporter (host metrics) ────────────────────────
  node-exporter:
    image: prom/node-exporter:latest
    container_name: copai-node-exporter
    network_mode: host
    restart: unless-stopped
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - --path.procfs=/host/proc
      - --path.sysfs=/host/sys
      - --web.listen-address=0.0.0.0:9100

  # ── Grafana ──────────────────────────────────────────────
  grafana:
    image: grafana/grafana:latest
    container_name: copai-grafana
    network_mode: host
    restart: unless-stopped
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SERVER_HTTP_PORT=3001
      - GF_SECURITY_ADMIN_PASSWORD=${GF_SECURITY_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=http://127.0.0.1:3001

volumes:
  open_webui_data:
  qdrant_data:
  langfuse_postgres:
  langfuse_clickhouse:
  langfuse_redis:
  langfuse_minio:
  prometheus_data:
  grafana_data:
```

---

## Step 9 — Start Everything

```bash
cd ~/copai-stack

# Start infrastructure first (Langfuse deps, Qdrant)
docker compose up -d \
  langfuse-postgres \
  langfuse-clickhouse \
  langfuse-redis \
  langfuse-minio \
  qdrant \
  node-exporter \
  prometheus

# Wait 60 seconds for databases to initialize
sleep 60

# Start Langfuse
docker compose up -d langfuse-web langfuse-worker

# Wait for Langfuse to be ready (watch for "Ready" log)
docker compose logs -f langfuse-web
# Press Ctrl+C when you see "Ready" or "Listening on port 3000"

# Start vLLM (takes 3-5 min to load model)
docker compose up -d vllm

# Watch vLLM load
docker compose logs -f vllm
# Press Ctrl+C when you see "Application startup complete"

# Start Grafana and extraction service
docker compose up -d grafana extraction

# Start Open WebUI last
docker compose up -d open-webui
```

---

## Step 10 — Get Langfuse API Keys

1. Open `http://YOUR_HPC_IP:3000`
2. Click **Sign Up** — create your admin account
3. Create an **Organization**: `COPAI`
4. Create a **Project**: `Ministry RAG`
5. Go to **Settings → API Keys**
6. Click **Create new API key**
7. Copy both `Public Key` (`pk-lf-...`) and `Secret Key` (`sk-lf-...`)

8. Update your `.env` file:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-key
LANGFUSE_SECRET_KEY=sk-lf-your-actual-key
```

9. Restart Open WebUI to pick up the keys:
```bash
docker compose restart open-webui
```

---

## Step 11 — Configure Open WebUI (Admin Settings)

Go to `http://YOUR_HPC_IP:8080` → **Admin Settings**

### Documents tab
```
Content Extraction Engine:  Docling
Embedding Engine:           sentence_transformers (local)
Embedding Model:            aisingapore/SEA-LION-E5-Embedding-600M
Chunk Size:                 400
Chunk Overlap:              50
Top K:                      5
Score Threshold:            0.3
```

> First time setting the embedding model — Open WebUI will download it
> (~2GB). Wait for the download to complete before uploading documents.

### Connections tab
```
OpenAI API Base URL:  http://127.0.0.1:8000/v1
API Key:              not-required
```
Click **Verify** — should show green.

### Models tab

Create a model preset:
- **Name**: Ministry RAG
- **Base Model**: gemma-sealion-v4
- **System Prompt**:
```
You are a helpful bilingual AI assistant for the Ministry.
Answer only from the provided document context.
Always respond in the same language the user writes in.
For Khmer queries, respond in Khmer (ភាសាខ្មែរ).
For English queries, respond in English.
If the answer is not in the documents, say:
  Khmer: "ព័ត៌មាននេះមិនមាននៅក្នុងឯកសារដែលបានផ្តល់ជូនទេ។"
  English: "This information is not available in the provided documents."
Always cite the source document when answering.
```

---

## Step 12 — Import Grafana Dashboard

1. Open `http://YOUR_HPC_IP:3001`
2. Login: `admin` / your `GF_SECURITY_ADMIN_PASSWORD`
3. Go to **Dashboards → Import**
4. Enter dashboard ID: `25043`
5. Click **Load**
6. Select **Prometheus** datasource
7. Click **Import**

You now have a live vLLM dashboard showing:
- Request latency (P50, P95, P99)
- Tokens per second
- Queue depth (waiting requests)
- KV cache usage %
- Time to first token

---

## Step 13 — Verify Everything Works

```bash
# All containers running?
docker compose ps

# vLLM health
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok"}

# vLLM model available
curl http://127.0.0.1:8000/v1/models
# Expected: shows gemma-sealion-v4

# Khmer test query
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma-sealion-v4",
    "messages": [{"role":"user","content":"សួស្ដី! AI គឺជាអ្វី?"}],
    "max_tokens": 100
  }'

# Qdrant health
curl http://127.0.0.1:6333/healthz
# Expected: {"title":"qdrant - vector search engine"}

# Langfuse health
curl http://127.0.0.1:3000/api/public/health
# Expected: {"status":"OK"}

# Extraction service
curl http://127.0.0.1:8002/health
# Expected: {"status":"ok","model":"gemma-sealion-v4"}

# Prometheus scraping vLLM
curl http://127.0.0.1:9090/api/v1/query?query=vllm:num_requests_running
# Expected: returns JSON with metric value

# GPU usage
nvidia-smi
# Expected: ~28GB used by vllm process
```

---

## Step 14 — Upload Documents to Open WebUI

### For digital PDFs (most ministry docs)
1. Admin → Knowledge → **Create Knowledge Base**
2. Name: e.g., `ច្បាប់ និងបទប្បញ្ញត្តិ` (Laws and Regulations)
3. Upload PDFs directly — Docling extracts text automatically

### For scanned Khmer PDFs
Pre-process first, then upload the text:
```bash
# Extract scanned PDF using the service
curl -X POST http://127.0.0.1:8002/extract \
  -F "file=@scanned_ministry_doc.pdf" \
  -o extracted_text.txt

# Then upload extracted_text.txt to Open WebUI Knowledge Base
```

---

## Step 15 — Verify Langfuse Traces

1. Open `http://YOUR_HPC_IP:3000`
2. Go to your **Ministry RAG** project
3. Click **Traces**
4. Send a test message in Open WebUI
5. Within 30 seconds you should see the trace with:
   - Full prompt (including RAG context)
   - Full response
   - Token counts (input/output)
   - Latency
   - User ID

---

## Quick Reference Commands

```bash
cd ~/copai-stack

# Start all services
docker compose up -d

# Stop all services
docker compose down

# View logs
docker compose logs -f vllm           # LLM server
docker compose logs -f open-webui     # WebUI
docker compose logs -f langfuse-web   # Langfuse

# Restart single service
docker compose restart open-webui

# Check GPU
nvidia-smi

# Update all images
docker compose pull
docker compose up -d

# Check disk usage
docker system df
```

---

## Service URLs Summary

| Service | URL |
|---|---|
| Open WebUI | `http://YOUR_IP:8080` |
| Langfuse (traces) | `http://YOUR_IP:3000` |
| Grafana (metrics) | `http://YOUR_IP:3001` |
| Prometheus (raw) | `http://YOUR_IP:9090` |
| vLLM API | `http://YOUR_IP:8000/v1` |
| Qdrant dashboard | `http://YOUR_IP:6333/dashboard` |
| MinIO console | `http://YOUR_IP:9011` |

---

## Troubleshooting

**vLLM fails to start — CUDA out of memory**
```bash
# Reduce memory utilization in docker-compose.yml
# --gpu-memory-utilization 0.82
# --max-num-seqs 24
docker compose up -d vllm
```

**Open WebUI can't connect to vLLM**
```bash
# Test from inside the container
docker exec copai-webui curl http://127.0.0.1:8000/health
```

**Langfuse web keeps restarting**
```bash
docker compose logs langfuse-web
# Usually ClickHouse not ready — wait longer, then:
docker compose restart langfuse-web langfuse-worker
```

**Embedding model downloading very slowly**
```bash
# Check logs
docker compose logs -f open-webui
# The ~2GB download happens once on first startup
# Do not restart during download
```

**Qdrant data lost after restart**
```bash
# Verify volume is mounted
docker volume ls | grep qdrant
# Should show: copai-stack_qdrant_data
```

---

*COPAI Lab — RUPP / MISTI HPC*
*Stack version: April 2026*
