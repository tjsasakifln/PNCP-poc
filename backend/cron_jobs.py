"""UX-303 AC8 + CRIT-011 AC7 + GTM-ARCH-002 AC5-AC7: Periodic cache, session cleanup, and warmup tasks.

Runs as background asyncio tasks during FastAPI lifespan.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta, date

logger = logging.getLogger(__name__)

# Cleanup interval: every 6 hours
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60

# GTM-ARCH-002 AC5: Cache refresh interval — every 4 hours
CACHE_REFRESH_INTERVAL_SECONDS = 4 * 60 * 60

# CRIT-011 AC7: Session cleanup thresholds
SESSION_STALE_HOURS = 1        # in_progress > 1h → timeout
SESSION_OLD_DAYS = 7           # failed/timeout > 7d → delete


async def start_cache_cleanup_task() -> asyncio.Task:
    """Start the periodic local cache cleanup background task.

    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_cache_cleanup_loop(), name="cache_cleanup")
    logger.info("Cache cleanup background task started (interval: 6h)")
    return task


async def start_session_cleanup_task() -> asyncio.Task:
    """CRIT-011 AC7: Start the periodic session cleanup background task.

    Runs immediately on startup, then every 6 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_session_cleanup_loop(), name="session_cleanup")
    logger.info("Session cleanup background task started (interval: 6h)")
    return task


async def start_cache_refresh_task() -> asyncio.Task:
    """GTM-ARCH-002 AC5: Start the periodic cache refresh background task.

    Connects get_stale_entries_for_refresh() to a cron loop that runs every 4h.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_cache_refresh_loop(), name="cache_refresh")
    logger.info("Cache refresh background task started (interval: 4h)")
    return task


async def cleanup_stale_sessions() -> dict:
    """CRIT-011 AC7: Clean up stale search sessions.

    - Sessions with status='in_progress' and created_at > 1 hour → mark as 'timeout'
    - Sessions with status IN ('failed', 'timeout', 'timed_out') and created_at > 7 days → delete
    - If status column doesn't exist: delete sessions with created_at > 7 days (graceful fallback)

    Returns dict with counts: {"marked_stale": N, "deleted_old": M}
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        now = datetime.now(timezone.utc)
        stale_cutoff = (now - timedelta(hours=SESSION_STALE_HOURS)).isoformat()
        old_cutoff = (now - timedelta(days=SESSION_OLD_DAYS)).isoformat()

        # Try status-based cleanup first; fall back if column doesn't exist
        try:
            # Mark stale in_progress sessions as timed_out
            marked_result = (
                sb.table("search_sessions")
                .update({
                    "status": "timed_out",
                    "error_message": "Session timed out (cleanup)",
                    "error_code": "session_timeout",
                    "completed_at": now.isoformat(),
                })
                .eq("status", "in_progress")
                .lt("created_at", stale_cutoff)
                .execute()
            )
            marked_stale = len(marked_result.data) if marked_result.data else 0

            # Also mark stale 'created' and 'processing' sessions
            for stale_status in ("created", "processing"):
                extra_result = (
                    sb.table("search_sessions")
                    .update({
                        "status": "timed_out",
                        "error_message": "Session timed out (cleanup)",
                        "error_code": "session_timeout",
                        "completed_at": now.isoformat(),
                    })
                    .eq("status", stale_status)
                    .lt("created_at", stale_cutoff)
                    .execute()
                )
                marked_stale += len(extra_result.data) if extra_result.data else 0

            # Delete old terminal sessions
            deleted_old = 0
            for terminal_status in ("failed", "timeout", "timed_out"):
                del_result = (
                    sb.table("search_sessions")
                    .delete()
                    .eq("status", terminal_status)
                    .lt("created_at", old_cutoff)
                    .execute()
                )
                deleted_old += len(del_result.data) if del_result.data else 0

            return {"marked_stale": marked_stale, "deleted_old": deleted_old}

        except Exception as col_err:
            if "42703" in str(col_err):
                # status/error columns don't exist — fallback to created_at-only cleanup
                logger.warning(
                    "Session cleanup: status column not found, "
                    "falling back to created_at-only cleanup"
                )
                del_result = (
                    sb.table("search_sessions")
                    .delete()
                    .lt("created_at", old_cutoff)
                    .execute()
                )
                deleted_old = len(del_result.data) if del_result.data else 0
                return {"marked_stale": 0, "deleted_old": deleted_old}
            raise

    except Exception as e:
        logger.error(f"Session cleanup error: {e}", exc_info=True)
        return {"marked_stale": 0, "deleted_old": 0, "error": str(e)}


async def refresh_stale_cache_entries() -> dict:
    """GTM-ARCH-002 AC5: Refresh stale HOT/WARM cache entries.

    Connects get_stale_entries_for_refresh() to trigger_background_revalidation().
    Returns dict with refresh stats.
    """
    from search_cache import get_stale_entries_for_refresh, trigger_background_revalidation

    try:
        entries = await get_stale_entries_for_refresh(batch_size=25)

        if not entries:
            return {"status": "no_stale_entries", "refreshed": 0}

        refreshed = 0
        failed = 0

        for entry in entries:
            try:
                # Build request_data with dates (last 10 days as default)
                search_params = entry.get("search_params", {})
                request_data = {
                    "ufs": search_params.get("ufs", []),
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": search_params.get("modalidades"),
                }

                dispatched = await trigger_background_revalidation(
                    user_id=entry["user_id"],
                    params=search_params,
                    request_data=request_data,
                )
                if dispatched:
                    refreshed += 1

                # Small delay between dispatches to avoid hammering sources
                await asyncio.sleep(2)

            except Exception as e:
                failed += 1
                logger.debug(f"Cache refresh dispatch failed for {entry.get('params_hash', '?')[:12]}: {e}")

        logger.info(
            f"Cache refresh cycle: {refreshed} dispatched, {failed} failed "
            f"out of {len(entries)} stale entries"
        )
        return {"status": "completed", "refreshed": refreshed, "failed": failed, "total": len(entries)}

    except Exception as e:
        logger.error(f"Cache refresh error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "refreshed": 0}


async def warmup_top_params() -> dict:
    """GTM-ARCH-002 AC6/AC7: Pre-warm top 10 popular sector+UF combinations.

    Enqueues background revalidation for the most popular search parameters.
    Used both on startup (AC7) and periodically via cron (AC6).
    """
    from search_cache import get_top_popular_params, trigger_background_revalidation

    try:
        top_params = await get_top_popular_params(limit=10)

        if not top_params:
            logger.info("Warmup: no popular params found to pre-warm")
            return {"status": "no_params", "warmed": 0}

        warmed = 0
        for params in top_params:
            try:
                request_data = {
                    "ufs": params.get("ufs", []),
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": params.get("modalidades"),
                }

                # Use a system user_id for warmup (entries go into global cache)
                dispatched = await trigger_background_revalidation(
                    user_id="00000000-0000-0000-0000-000000000000",
                    params=params,
                    request_data=request_data,
                )
                if dispatched:
                    warmed += 1

                await asyncio.sleep(1)

            except Exception as e:
                logger.debug(f"Warmup dispatch failed: {e}")

        logger.info(f"Warmup: {warmed}/{len(top_params)} popular params enqueued")
        return {"status": "completed", "warmed": warmed, "total": len(top_params)}

    except Exception as e:
        logger.error(f"Warmup error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), "warmed": 0}


async def _session_cleanup_loop() -> None:
    """CRIT-011 AC7: Run session cleanup on startup and every 6 hours."""
    # Run immediately on startup
    try:
        result = await cleanup_stale_sessions()
        logger.info(
            f"Session cleanup (startup): marked {result['marked_stale']} stale, "
            f"deleted {result['deleted_old']} old "
            f"at {datetime.now(timezone.utc).isoformat()}"
        )
    except Exception as e:
        logger.error(f"Session cleanup error on startup: {e}", exc_info=True)

    # Then every 6 hours
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            result = await cleanup_stale_sessions()
            logger.info(
                f"Session cleanup: marked {result['marked_stale']} stale, "
                f"deleted {result['deleted_old']} old "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Session cleanup error: {e}", exc_info=True)
            await asyncio.sleep(60)


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


async def _cache_refresh_loop() -> None:
    """GTM-ARCH-002 AC5: Run cache refresh every 4 hours."""
    # Wait a bit after startup to avoid overloading (warmup runs on startup separately)
    await asyncio.sleep(60)

    while True:
        try:
            result = await refresh_stale_cache_entries()
            logger.info(
                f"Cache refresh cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(CACHE_REFRESH_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Cache refresh task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache refresh loop error: {e}", exc_info=True)
            await asyncio.sleep(60)
