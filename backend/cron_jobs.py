"""UX-303 AC8: Periodic cache cleanup and maintenance tasks.

Runs as a background asyncio task during FastAPI lifespan.
"""

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Cleanup interval: every 6 hours
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def start_cache_cleanup_task() -> asyncio.Task:
    """Start the periodic local cache cleanup background task.

    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_cache_cleanup_loop(), name="cache_cleanup")
    logger.info("Cache cleanup background task started (interval: 6h)")
    return task


async def _cache_cleanup_loop() -> None:
    """Run cleanup every CLEANUP_INTERVAL_SECONDS."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            from search_cache import cleanup_local_cache
            deleted = cleanup_local_cache()
            logger.info(
                f"Periodic cache cleanup: deleted {deleted} expired files "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}", exc_info=True)
            # Don't crash the loop on transient errors
            await asyncio.sleep(60)
