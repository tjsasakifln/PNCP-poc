# =============================================================================
# BidIQ Uniformes - Backend Dockerfile
# =============================================================================
# Production-ready Python FastAPI application for Railway deployment
# Base: Python 3.11 slim for smaller image size

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Cache bust - change this value to force complete rebuild
ARG CACHE_BUST=2026-01-28-v3-fix-port

# Install Python dependencies (force reinstall with pinned versions)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway injects PORT env var)
EXPOSE 8000

# NOTE: Railway handles healthcheck via railway.toml (healthcheckPath = "/health")
# Do NOT add HEALTHCHECK instruction here - it conflicts with Railway's system

# Run with uvicorn - Railway will inject $PORT
# Using shell form for guaranteed variable expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
