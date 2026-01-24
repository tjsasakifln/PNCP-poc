# =============================================================================
# BidIQ Uniformes - Backend Dockerfile (Development)
# =============================================================================
# Multi-stage build for production-ready Python FastAPI application
# Base: Python 3.11 slim for smaller image size

# Stage 1: Base dependencies
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for future dependencies)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Development
FROM base as development

# Copy application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run with hot-reload for development
# Note: --reload watches for file changes and auto-restarts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
