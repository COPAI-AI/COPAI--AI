FROM python:3.11-slim

# Switch to Hong Kong Debian mirror (faster from Cambodia ministry network)
RUN echo "deb http://ftp.hk.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://ftp.hk.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://ftp.hk.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
