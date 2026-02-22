#!/bin/bash
# =============================================================================
# GTM-RESILIENCE-F01 AC6: Multi-process start script
# =============================================================================
# Supports two modes via PROCESS_TYPE env var:
#   web (default): Gunicorn + Uvicorn workers (FastAPI)
#   worker:        ARQ background job worker (LLM + Excel)
#
# Railway deployment: Create two services from the same Dockerfile,
# setting PROCESS_TYPE=web for one and PROCESS_TYPE=worker for the other.

set -e

PROCESS_TYPE="${PROCESS_TYPE:-web}"

case "$PROCESS_TYPE" in
  web)
    echo "Starting web process (gunicorn + uvicorn)..."

    # CRIT-010 AC1+AC3: --preload loads the ASGI app in master BEFORE forking workers.
    # This ensures all imports are resolved and routes registered before any worker
    # accepts traffic — eliminating 404s during startup.
    PRELOAD_FLAG=""
    if [ "${GUNICORN_PRELOAD:-true}" = "true" ]; then
      PRELOAD_FLAG="--preload"
      echo "  --preload enabled: app loaded in master before forking workers"
    fi

    # CRIT-026 AC1+AC2+AC4: Increased timeout 600→900s for SSE long-lived streams,
    # WEB_CONCURRENCY 2→3 to prevent total downtime when 1 worker dies,
    # added --keep-alive for persistent connections.
    echo "  timeout=${GUNICORN_TIMEOUT:-900}s, workers=${WEB_CONCURRENCY:-3}, graceful=${GUNICORN_GRACEFUL_TIMEOUT:-120}s"

    exec gunicorn main:app \
      -k uvicorn.workers.UvicornWorker \
      -w "${WEB_CONCURRENCY:-3}" \
      --bind "0.0.0.0:${PORT:-8000}" \
      --timeout "${GUNICORN_TIMEOUT:-900}" \
      --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-120}" \
      --keep-alive "${GUNICORN_KEEP_ALIVE:-5}" \
      $PRELOAD_FLAG
    ;;
  worker)
    echo "Starting ARQ worker process..."
    exec arq job_queue.WorkerSettings
    ;;
  *)
    echo "ERROR: Unknown PROCESS_TYPE='$PROCESS_TYPE'. Use 'web' or 'worker'."
    exit 1
    ;;
esac
