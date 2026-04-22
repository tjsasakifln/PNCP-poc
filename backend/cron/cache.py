"""Cache cron jobs: local file cache cleanup only.

Cache warming (proactive) was deprecated on 2026-04-18 — DataLake Supabase
(50k bids + 2M contracts) is now the primary query path with <100ms latency.
Pre-populating `search_results_cache` via background jobs became pure overhead.
See STORY-CIG-BE-cache-warming-deprecate.

Passive cache (Layer 3 on-demand) and SWR per-request reactivity remain.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def _do_cache_cleanup() -> dict:
    """Run local cache + filter stats cleanup."""
    from cache.local_file import cleanup_local_cache
    deleted = cleanup_local_cache()
    try:
        from filter.stats import filter_stats_tracker, discard_rate_tracker
        fs = filter_stats_tracker.cleanup_old()
        dr = discard_rate_tracker.cleanup_old()
        if fs or dr:
            logger.info("Filter stats cleanup: %d filter, %d discard entries removed", fs, dr)
    except Exception as e:
        logger.warning("Filter stats cleanup failed: %s", e)
    return {"deleted": deleted}


async def start_cache_cleanup_task() -> asyncio.Task:
    from cron._loop import cron_loop
    task = asyncio.create_task(
        cron_loop("Cache cleanup", _do_cache_cleanup, CLEANUP_INTERVAL_SECONDS,
                  initial_delay=CLEANUP_INTERVAL_SECONDS),
        name="cache_cleanup",
    )
    logger.info("Cache cleanup background task started (interval: 6h)")
    return task
