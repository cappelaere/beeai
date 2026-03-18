# Multi-stage Dockerfile for Piper TTS Service
# Stage 1: Download Piper voice models
FROM python:3.11-slim AS voice-downloader

RUN apt-get update && \
    apt-get install -y wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /voices

# Download Piper voice models from HuggingFace
# en_US-lessac-medium (female, high quality)
RUN wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# en_US-ryan-high (male, high quality)
RUN wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx.json

# en_GB-alan-medium (British male)
RUN wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json

# Verify downloads
RUN ls -lh /voices/ && \
    echo "Voice models downloaded successfully"

# Stage 2: Runtime image
FROM python:3.11-slim

LABEL maintainer="RealtyIQ Team"
LABEL description="Piper TTS Microservice"

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy voice models from downloader stage
COPY --from=voice-downloader /voices /voices

# Copy application code
COPY app/ ./app/

# Create audio cache directory
RUN mkdir -p /audio && \
    chmod 777 /audio

# Expose port
EXPOSE 8088

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8088/healthz || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088", "--log-level", "info"]
