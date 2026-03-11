"""Shared startup state — process timing and readiness flags."""

import time

# CRIT-010 AC5: Startup readiness tracking
process_start_time: float = time.monotonic()
startup_time: float | None = None  # Set when lifespan startup completes

# DEBT-124: Graceful shutdown drain flag
shutting_down: bool = False
