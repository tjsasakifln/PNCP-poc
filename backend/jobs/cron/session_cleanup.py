"""jobs.cron.session_cleanup — Session and expired results cleanup crons."""
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from jobs.cron.canary import _is_cb_or_connection_error

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60
SESSION_STALE_HOURS = 1
SESSION_OLD_DAYS = 7
RESULTS_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def cleanup_stale_sessions() -> dict:
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        stale_cutoff = (now - timedelta(hours=SESSION_STALE_HOURS)).isoformat()
        old_cutoff = (now - timedelta(days=SESSION_OLD_DAYS)).isoformat()
        try:
            marked_stale = 0
            for stale_status in ("in_progress", "created", "processing"):
                r = await sb_execute(
                    sb.table("search_sessions").update({
                        "status": "timed_out",
                        "error_message": "Session timed out (cleanup)",
                        "error_code": "session_timeout",
                        "completed_at": now.isoformat(),
                    }).eq("status", stale_status).lt("created_at", stale_cutoff)
                )
                marked_stale += len(r.data) if r.data else 0
            deleted_old = 0
            for terminal_status in ("failed", "timeout", "timed_out"):
                r = await sb_execute(sb.table("search_sessions").delete().eq("status", terminal_status).lt("created_at", old_cutoff))
                deleted_old += len(r.data) if r.data else 0
            return {"marked_stale": marked_stale, "deleted_old": deleted_old}
        except Exception as col_err:
            if "42703" in str(col_err):
                logger.warning("Session cleanup: status column not found, falling back to created_at-only cleanup")
                r = await sb_execute(sb.table("search_sessions").delete().lt("created_at", old_cutoff))
                return {"marked_stale": 0, "deleted_old": len(r.data) if r.data else 0}
            raise
    except Exception as e:
        logger.error(f"Session cleanup error: {e}", exc_info=True)
        return {"marked_stale": 0, "deleted_old": 0, "error": str(e)}


async def cleanup_expired_results() -> dict:
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        result = await sb_execute(sb.table("search_results_store").delete().lt("expires_at", now))
        deleted = len(result.data) if result and result.data else 0
        logger.info("STORY-362: Cleaned up %d expired search results at %s", deleted, now)
        return {"deleted": deleted, "cleaned_at": now}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-362: Results cleanup skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-362: Results cleanup error: %s", e, exc_info=True)
        return {"deleted": 0, "error": str(e)}


async def _session_cleanup_loop() -> None:
    try:
        result = await cleanup_stale_sessions()
        logger.info("Session cleanup (startup): marked %d stale, deleted %d old", result["marked_stale"], result["deleted_old"])
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("Session cleanup skipped on startup (Supabase unavailable): %s", e)
        else:
            logger.error(f"Session cleanup error on startup: {e}", exc_info=True)
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            result = await cleanup_stale_sessions()
            logger.info("Session cleanup: marked %d stale, deleted %d old", result["marked_stale"], result["deleted_old"])
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Session cleanup skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Session cleanup error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def _results_cleanup_loop() -> None:
    while True:
        try:
            result = await cleanup_expired_results()
            logger.info("STORY-362 results cleanup cycle: %s", result)
            await asyncio.sleep(RESULTS_CLEANUP_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("STORY-362: Results cleanup task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-362 results cleanup loop skipped: %s", e)
            else:
                logger.error("STORY-362 results cleanup loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


async def start_session_cleanup_task() -> asyncio.Task:
    task = asyncio.create_task(_session_cleanup_loop(), name="session_cleanup")
    logger.info("Session cleanup background task started (interval: 6h)")
    return task


async def start_results_cleanup_task() -> asyncio.Task:
    task = asyncio.create_task(_results_cleanup_loop(), name="results_cleanup")
    logger.info("STORY-362: Expired results cleanup task started (interval: 6h)")
    return task
