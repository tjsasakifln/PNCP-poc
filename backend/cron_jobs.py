"""UX-303 AC8 + CRIT-011 AC7: Periodic cache and session cleanup tasks.

Runs as background asyncio tasks during FastAPI lifespan.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Cleanup interval: every 6 hours
CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60

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
