# =============================================================================
# BidIQ Uniformes - Backend Dockerfile
# =============================================================================
# Production-ready Python FastAPI application for Railway deployment
# Base: Python 3.11 slim for smaller image size

FROM python:3.11-slim

# CACHE BUST - This label forces Railway to rebuild when changed
# Update timestamp to invalidate all cached layers: 2026-01-28T12:50:00
LABEL build.timestamp="2026-01-28T22:00:00"
ARG CACHEBUST=20260128v6

# Set working directory
WORKDIR /app

# Install system dependencies (invalidated by ARG above)
RUN echo "Build: ${CACHEBUST}" && apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway injects PORT env var)
EXPOSE 8000

# NOTE: Railway handles healthcheck via railway.toml (healthcheckPath = "/health")
# Do NOT add HEALTHCHECK instruction here - it conflicts with Railway's system

# Run with uvicorn - Railway will inject $PORT
# Using shell form for guaranteed variable expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
