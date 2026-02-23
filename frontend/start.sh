#!/bin/sh
# =============================================================================
# SLA-001 + SLA-002: Graceful shutdown wrapper for Next.js standalone server
# =============================================================================
# Handles SIGTERM from Railway during deploys/scaling by:
#   1. Forwarding SIGTERM to the Node.js process
#   2. Allowing drainingSeconds (set in railway.toml) for in-flight requests
#   3. Exiting cleanly so Railway doesn't force-kill the container
#
# SLA-002: Logs memory usage on startup and crash for OOM diagnosis.

set -e

echo "[START] Next.js server starting on port ${PORT:-3000}..."
echo "[START] HOSTNAME=${HOSTNAME:-0.0.0.0}"
echo "[START] NODE_ENV=${NODE_ENV:-production}"
echo "[START] NODE_OPTIONS=${NODE_OPTIONS:-not set}"

# SLA-002: Log initial memory available for OOM diagnosis
if [ -f /sys/fs/cgroup/memory.max ]; then
  MEM_LIMIT=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo "unknown")
  MEM_CURRENT=$(cat /sys/fs/cgroup/memory.current 2>/dev/null || echo "unknown")
  echo "[START] Container memory: limit=${MEM_LIMIT} current=${MEM_CURRENT}"
elif [ -f /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then
  MEM_LIMIT=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo "unknown")
  echo "[START] Container memory limit: ${MEM_LIMIT}"
fi

# Trap SIGTERM and SIGINT to forward to child process
cleanup() {
  echo "[SHUTDOWN] Received signal, draining connections..."
  if [ -n "$SERVER_PID" ]; then
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    # Wait for graceful shutdown (Railway's drainingSeconds handles the timeout)
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  echo "[SHUTDOWN] Server stopped cleanly."
  exit 0
}

trap cleanup TERM INT

# Start Next.js standalone server in background so we can trap signals
node server.js &
SERVER_PID=$!

echo "[START] Server PID: $SERVER_PID"

# Wait for server process (this allows trap to fire)
wait "$SERVER_PID"
EXIT_CODE=$?

# SLA-002: Diagnose exit code for OOM kills
if [ "$EXIT_CODE" -eq 137 ]; then
  echo "[FATAL] Server killed by OOM (exit 137 = SIGKILL). Increase memory or reduce NODE_OPTIONS --max-old-space-size"
elif [ "$EXIT_CODE" -ne 0 ]; then
  echo "[ERROR] Server exited with code: $EXIT_CODE"
else
  echo "[EXIT] Server exited cleanly (code 0)"
fi
exit $EXIT_CODE
