# =============================================================================
# SmartLic - Backend Dockerfile
# =============================================================================
# Production-ready Python FastAPI application for Railway deployment
# Base: Python 3.12 slim for smaller image size

FROM python:3.12-slim

# CACHE BUST - This label forces Railway to rebuild when changed
# Update timestamp to invalidate all cached layers: 2026-02-28T18:00:00
LABEL build.timestamp="2026-03-24T14:20:00"
ARG CACHEBUST=20260324v1

# Set working directory
WORKDIR /app

# Install system dependencies (invalidated by ARG above)
# HARDEN-002: jemalloc reduces RSS fragmentation in async FastAPI
RUN echo "Build: ${CACHEBUST}" && apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*

# HARDEN-002: jemalloc DISABLED — causes SIGSEGV with cryptography>=46 OpenSSL bindings
# when processing HTTP requests through Starlette BaseHTTPMiddleware threading.
# jemalloc + OpenSSL malloc hooks = segfault on POST body parsing.
# ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
# CRIT-041: Aggressive removal of ALL fork-unsafe C extensions.
# Previous fix (CRIT-SIGSEGV) only removed grpcio/grpcio-status, but
# opentelemetry-exporter-otlp (umbrella) re-pulls otlp-proto-grpc → grpcio.
# httptools also sneaks in as transitive dep and is fork-unsafe.
# We only need otlp-proto-http (not gRPC), so remove the entire gRPC chain.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y \
        grpcio \
        grpcio-status \
        opentelemetry-exporter-otlp-proto-grpc \
        opentelemetry-exporter-otlp \
        httptools \
        uvloop \
    2>/dev/null || true && \
    echo "=== CRIT-041: Verifying no fork-unsafe packages remain ===" && \
    pip list | grep -iE "grpc|uvloop|httptools" && echo "WARNING: fork-unsafe packages still present!" || echo "OK: all fork-unsafe packages removed"

# Copy application code
COPY . .

# MED-SEC-003: Non-root user for container security
RUN addgroup --system --gid 1001 appuser && \
    adduser --system --uid 1001 --ingroup appuser appuser && \
    mkdir -p /tmp/smartlic_cache && \
    chown appuser:appuser /tmp/smartlic_cache

# Expose port (Railway injects PORT env var)
EXPOSE 8000

# NOTE: Railway handles healthcheck via railway.toml (healthcheckPath = "/health")
# Do NOT add HEALTHCHECK instruction here - it conflicts with Railway's system

# GTM-RESILIENCE-F01 AC6: Entrypoint script supports both web and worker modes
# Usage:
#   Web process (default):  CMD (below) or PROCESS_TYPE=web
#   ARQ worker:             PROCESS_TYPE=worker
# Using shell form for guaranteed variable expansion
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# MED-SEC-003: Run as non-root user
USER appuser

# CRIT-083: start.sh is authoritative for all runner modes.
# Default: uvicorn spawn-based workers (RUNNER=uvicorn, safe with cryptography>=46).
# Opt-in: RUNNER=gunicorn for Gunicorn prefork mode.
# Railway overrides this via railway.toml startCommand.
CMD ["/app/start.sh"]
