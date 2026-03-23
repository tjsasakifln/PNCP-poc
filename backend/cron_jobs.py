"""UX-303 AC8 + CRIT-011 AC7 + GTM-ARCH-002 AC5-AC7: Periodic cache, session cleanup, and warmup tasks.

Runs as background asyncio tasks during FastAPI lifespan.
"""

import asyncio
import logging
import os
import threading
import time as _time_mod
from datetime import datetime, timezone, timedelta, date

logger = logging.getLogger(__name__)


# ============================================================================
# CRIT-052: Thread-safe global PNCP cron canary status
# ============================================================================

_pncp_cron_status_lock = threading.Lock()
_pncp_cron_status: dict = {"status": "unknown", "latency_ms": None, "updated_at": None}

# CRIT-056 AC4: Recovery epoch — increments when PNCP transitions degraded/down → healthy.
# Cache entries written before the latest recovery are treated as stale on next read.
_pncp_recovery_epoch: int = 0


def get_pncp_cron_status() -> dict:
    """Return last known PNCP status from cron canary (CRIT-052 AC3).

    Returns dict with keys: status ('healthy'|'degraded'|'down'|'unknown'),
    latency_ms (int|None), updated_at (float timestamp|None).
    """
    with _pncp_cron_status_lock:
        return dict(_pncp_cron_status)


def get_pncp_recovery_epoch() -> int:
    """CRIT-056 AC4: Return current PNCP recovery epoch (thread-safe)."""
    with _pncp_cron_status_lock:
        return _pncp_recovery_epoch


def _update_pncp_cron_status(status: str, latency_ms: int | None) -> None:
    """Update global PNCP cron status (CRIT-052 AC3).

    CRIT-056 AC4: If transitioning from degraded/down → healthy, increment recovery epoch.
    """
    global _pncp_recovery_epoch
    with _pncp_cron_status_lock:
        old_status = _pncp_cron_status["status"]
        _pncp_cron_status["status"] = status
        _pncp_cron_status["latency_ms"] = latency_ms
        _pncp_cron_status["updated_at"] = _time_mod.time()
        # CRIT-056 AC4: Detect recovery transition
        if old_status in ("degraded", "down") and status == "healthy":
            _pncp_recovery_epoch += 1
            logger.info(
                f"CRIT-056: PNCP recovered (epoch={_pncp_recovery_epoch}) — "
                f"degraded cache entries will be revalidated on next read"
            )


def _is_cb_or_connection_error(e: Exception) -> bool:
    """SHIP-003 AC3: Check if an exception is a circuit breaker or connection error.

    Used by cron tasks to log WARNING instead of ERROR for transient infra issues.
    """
    err_name = type(e).__name__
    err_str = str(e)
    return (
        "CircuitBreaker" in err_name
        or "ConnectionError" in err_name
        or "ConnectError" in err_str
        or "PGRST205" in err_str
    )


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
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()

        now = datetime.now(timezone.utc)
        stale_cutoff = (now - timedelta(hours=SESSION_STALE_HOURS)).isoformat()
        old_cutoff = (now - timedelta(days=SESSION_OLD_DAYS)).isoformat()

        # Try status-based cleanup first; fall back if column doesn't exist
        try:
            # Mark stale in_progress sessions as timed_out
            marked_result = await sb_execute(
                sb.table("search_sessions")
                .update({
                    "status": "timed_out",
                    "error_message": "Session timed out (cleanup)",
                    "error_code": "session_timeout",
                    "completed_at": now.isoformat(),
                })
                .eq("status", "in_progress")
                .lt("created_at", stale_cutoff)
            )
            marked_stale = len(marked_result.data) if marked_result.data else 0

            # Also mark stale 'created' and 'processing' sessions
            for stale_status in ("created", "processing"):
                extra_result = await sb_execute(
                    sb.table("search_sessions")
                    .update({
                        "status": "timed_out",
                        "error_message": "Session timed out (cleanup)",
                        "error_code": "session_timeout",
                        "completed_at": now.isoformat(),
                    })
                    .eq("status", stale_status)
                    .lt("created_at", stale_cutoff)
                )
                marked_stale += len(extra_result.data) if extra_result.data else 0

            # Delete old terminal sessions
            deleted_old = 0
            for terminal_status in ("failed", "timeout", "timed_out"):
                del_result = await sb_execute(
                    sb.table("search_sessions")
                    .delete()
                    .eq("status", terminal_status)
                    .lt("created_at", old_cutoff)
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
                del_result = await sb_execute(
                    sb.table("search_sessions")
                    .delete()
                    .lt("created_at", old_cutoff)
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
        top_params = await get_top_popular_params(limit=30)

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


async def _get_prioritized_ufs(all_ufs: list[str]) -> list[str]:
    """CRIT-055 AC2: Return UFs ordered by search history popularity.

    Queries recent search sessions for UF frequency, puts popular UFs first,
    then appends remaining UFs from the default priority order.
    Falls back to DEFAULT_UF_PRIORITY if no history available.
    """
    from search_cache import get_popular_ufs_from_sessions
    from config import DEFAULT_UF_PRIORITY

    try:
        popular = await get_popular_ufs_from_sessions(days=7)
    except Exception:
        popular = []

    if not popular:
        # No history — use default priority order, ensuring all_ufs coverage
        ordered = [uf for uf in DEFAULT_UF_PRIORITY if uf in set(all_ufs)]
        remaining = [uf for uf in all_ufs if uf not in set(ordered)]
        return ordered + remaining

    # Popular UFs first, then remaining from all_ufs
    all_set = set(all_ufs)
    ordered = [uf for uf in popular if uf in all_set]
    remaining = [uf for uf in all_ufs if uf not in set(ordered)]
    return ordered + remaining


async def warmup_specific_combinations(ufs: list[str], sectors: list[str]) -> dict:
    """CRIT-055 AC1/AC2/AC4: Pre-warm cache for sector+UF combinations.

    Iterates over each sector x UF pair with:
    - History-based UF priority (AC2)
    - Batch grouping of 5 UFs with delay between groups (AC1)
    - Rate limiting: respects WARMUP_RATE_LIMIT_RPS (AC4)
    - PNCP degraded pause: pauses warmup when canary reports degraded (AC4)

    Returns:
        dict with keys: dispatched, skipped, failed, paused, total, ufs_covered.
    """
    from search_cache import trigger_background_revalidation
    from config import (
        WARMUP_BATCH_DELAY_SECONDS, WARMUP_RATE_LIMIT_RPS,
        WARMUP_PNCP_DEGRADED_PAUSE_S, WARMUP_UF_BATCH_SIZE,
    )

    # AC2: Prioritize UFs by search history
    prioritized_ufs = await _get_prioritized_ufs(ufs)

    dispatched = 0
    skipped = 0
    failed = 0
    paused = 0
    total = len(sectors) * len(prioritized_ufs)
    ufs_covered: set[str] = set()

    # Rate limit interval (seconds between requests)
    rate_interval = 1.0 / WARMUP_RATE_LIMIT_RPS if WARMUP_RATE_LIMIT_RPS > 0 else 0.5

    logger.info(
        "CRIT-055 warmup: starting %d combinations "
        "(%d sectors x %d UFs, rate=%.1f rps, batch=%d)",
        total, len(sectors), len(prioritized_ufs),
        WARMUP_RATE_LIMIT_RPS, WARMUP_UF_BATCH_SIZE,
    )

    for sector_id in sectors:
        for i, uf in enumerate(prioritized_ufs):
            # AC4: Check PNCP canary — pause if degraded
            pncp_status = get_pncp_cron_status()
            if pncp_status.get("status") in ("degraded", "down"):
                logger.warning(
                    "CRIT-055 warmup: PNCP %s — pausing %.0fs",
                    pncp_status["status"], WARMUP_PNCP_DEGRADED_PAUSE_S,
                )
                paused += 1
                await asyncio.sleep(WARMUP_PNCP_DEGRADED_PAUSE_S)

            try:
                params = {
                    "setor_id": sector_id,
                    "ufs": [uf],
                    "status": None,
                    "modalidades": None,
                    "modo_busca": None,
                }
                request_data = {
                    "ufs": [uf],
                    "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                    "data_final": date.today().isoformat(),
                    "modalidades": None,
                }

                dispatched_ok = await trigger_background_revalidation(
                    user_id="00000000-0000-0000-0000-000000000000",
                    params=params,
                    request_data=request_data,
                )

                if dispatched_ok:
                    dispatched += 1
                    ufs_covered.add(uf)
                else:
                    skipped += 1

                # AC4: Rate limiting between individual requests
                await asyncio.sleep(rate_interval)

            except Exception as e:
                failed += 1
                logger.warning("CRIT-055 warmup: failed sector=%s uf=%s: %s", sector_id, uf, e)

            # AC1: Extra delay between UF batches
            if (i + 1) % WARMUP_UF_BATCH_SIZE == 0 and i + 1 < len(prioritized_ufs):
                await asyncio.sleep(WARMUP_BATCH_DELAY_SECONDS)

    # AC5: Coverage metric
    try:
        from metrics import WARMUP_COVERAGE_RATIO
        coverage = len(ufs_covered) / len(prioritized_ufs) if prioritized_ufs else 0
        WARMUP_COVERAGE_RATIO.set(coverage)
    except Exception:
        pass

    # AC5: Summary log
    logger.info(
        "CRIT-055 warmup complete: %d/%d dispatched, %d failed, "
        "coverage: %d/%d UFs, paused %d times",
        dispatched, total, failed,
        len(ufs_covered), len(prioritized_ufs), paused,
    )
    return {
        "dispatched": dispatched, "skipped": skipped, "failed": failed,
        "paused": paused, "total": total,
        "ufs_covered": len(ufs_covered), "ufs_total": len(prioritized_ufs),
    }


async def start_warmup_task() -> asyncio.Task:
    """CRIT-055: Start the startup + periodic cache warm-up background task.

    Startup warmup waits WARMUP_STARTUP_DELAY_SECONDS, then warms all 27 UFs x 5 sectors.
    Periodic warmup re-warms top 10 combinations every WARMUP_PERIODIC_INTERVAL_HOURS.

    Returns:
        asyncio.Task that can be cancelled during shutdown.
    """
    from config import WARMUP_ENABLED, WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS

    if not WARMUP_ENABLED:
        logger.info("CRIT-055 warmup: disabled via WARMUP_ENABLED=false — skipping")
        task = asyncio.create_task(asyncio.sleep(0), name="warmup_noop")
        return task

    task = asyncio.create_task(
        _warmup_startup_and_periodic(WARMUP_UFS, WARMUP_SECTORS, WARMUP_STARTUP_DELAY_SECONDS),
        name="cache_warmup",
    )
    logger.info(
        "CRIT-055 warmup: task started — delay=%ds, sectors=%s, ufs=%d total",
        WARMUP_STARTUP_DELAY_SECONDS, WARMUP_SECTORS, len(WARMUP_UFS),
    )
    return task


async def _warmup_startup_and_periodic(
    ufs: list[str],
    sectors: list[str],
    delay_seconds: int,
) -> None:
    """CRIT-055: Startup warmup + periodic re-warm loop."""
    from config import WARMUP_PERIODIC_INTERVAL_HOURS

    try:
        # Phase 1: Startup warmup (after delay)
        logger.info("CRIT-055 warmup: waiting %ds before startup warm-up", delay_seconds)
        await asyncio.sleep(delay_seconds)
        result = await warmup_specific_combinations(ufs, sectors)
        logger.info("CRIT-055 warmup: startup warm-up finished: %s", result)

        # Phase 2: AC3 — Periodic re-warm every N hours
        interval_seconds = WARMUP_PERIODIC_INTERVAL_HOURS * 3600
        while True:
            await asyncio.sleep(interval_seconds)
            logger.info("CRIT-055 warmup: periodic re-warm starting")
            periodic_result = await warmup_top_params()
            logger.info("CRIT-055 warmup: periodic re-warm finished: %s", periodic_result)

    except asyncio.CancelledError:
        logger.info("CRIT-055 warmup: task cancelled (shutdown)")
    except Exception as e:
        logger.error("CRIT-055 warmup: task failed: %s", e, exc_info=True)


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
        if _is_cb_or_connection_error(e):
            logger.warning("Session cleanup skipped on startup (Supabase unavailable): %s", e)
        else:
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
            if _is_cb_or_connection_error(e):
                logger.warning("Session cleanup skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Session cleanup error: {e}", exc_info=True)
            await asyncio.sleep(60)


async def _cache_cleanup_loop() -> None:
    """Run cleanup every CLEANUP_INTERVAL_SECONDS."""
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            from search_cache import cleanup_local_cache
            deleted = cleanup_local_cache()

            # DEBT-014 SYS-010: Cleanup filter stats trackers
            try:
                from filter_stats import filter_stats_tracker, discard_rate_tracker
                fs_removed = filter_stats_tracker.cleanup_old()
                dr_removed = discard_rate_tracker.cleanup_old()
                if fs_removed or dr_removed:
                    logger.info(
                        "Filter stats cleanup: %d filter entries, %d discard entries removed",
                        fs_removed, dr_removed,
                    )
            except Exception as e:
                logger.warning("Filter stats cleanup failed: %s", e)

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
            # CRIT-050 AC6: Respect feature flag each iteration
            from config import CACHE_REFRESH_ENABLED
            if not CACHE_REFRESH_ENABLED:
                await asyncio.sleep(CACHE_REFRESH_INTERVAL_SECONDS)
                continue

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


# ============================================================================
# STORY-316: Health Canary Cron Job (every 5 minutes)
# ============================================================================

HEALTH_CANARY_INTERVAL_SECONDS = 5 * 60  # 5 minutes


async def start_health_canary_task() -> asyncio.Task:
    """STORY-316 AC6: Start the periodic health canary background task.

    Runs every 5 minutes. Saves results to health_checks table.
    Detects incidents and auto-resolves after 3 consecutive healthy.
    Respects HEALTH_CANARY_ENABLED feature flag.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_health_canary_loop(), name="health_canary")
    logger.info("STORY-316: Health canary task started (interval: 5m)")
    return task


async def run_health_canary() -> dict:
    """STORY-316 AC6: Execute a single health canary check.

    1. Run realistic source checks (PNCP tamanhoPagina=50, PCP v2, ComprasGov)
    2. Check component health (Redis, Supabase, ARQ)
    3. Save result to health_checks table
    4. Detect incidents (AC8) and auto-resolve (AC10)
    5. Update Prometheus metrics (AC18)
    """
    import time as _time
    from config import HEALTH_CANARY_ENABLED

    if not HEALTH_CANARY_ENABLED:
        return {"status": "disabled"}

    start = _time.time()

    try:
        from health import get_public_status, save_health_check, detect_incident
        from metrics import HEALTH_CANARY_DURATION, HEALTH_CANARY_STATUS

        # Get full status (AC1: realistic canary)
        status_data = await get_public_status()
        duration = _time.time() - start

        overall = status_data.get("status", "unhealthy")
        sources = status_data.get("sources", {})
        components = status_data.get("components", {})

        # Calculate average latency
        latencies = [
            s.get("latency_ms", 0) for s in sources.values()
            if isinstance(s, dict) and s.get("latency_ms") is not None
        ]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else None

        # CRIT-052 AC3: Extract PNCP source status and update global
        pncp_source = sources.get("pncp", {})
        if isinstance(pncp_source, dict):
            pncp_status_str = pncp_source.get("status", "unknown")
            pncp_latency = pncp_source.get("latency_ms")
            # Map to CRIT-052 status: healthy (<2s), degraded (2-10s), down (no response)
            if pncp_status_str == "healthy" and pncp_latency is not None:
                if pncp_latency < 2000:
                    _update_pncp_cron_status("healthy", pncp_latency)
                else:
                    _update_pncp_cron_status("degraded", pncp_latency)
            elif pncp_status_str in ("degraded", "unhealthy"):
                _update_pncp_cron_status(
                    "degraded" if pncp_status_str == "degraded" else "down",
                    pncp_latency,
                )
            else:
                _update_pncp_cron_status("unknown", pncp_latency)

        # Save to DB (AC6)
        await save_health_check(overall, sources, components, avg_latency)

        # Detect incidents (AC8/AC10)
        await detect_incident(overall, sources)

        # Update metrics (AC18)
        try:
            HEALTH_CANARY_DURATION.observe(duration)
            status_value = {"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}.get(overall, 0.0)
            HEALTH_CANARY_STATUS.set(status_value)
        except Exception:
            pass

        # Periodic cleanup of old health checks
        from health import cleanup_old_health_checks
        await cleanup_old_health_checks()

        logger.info(
            "STORY-316 canary: status=%s, latency=%s ms, duration=%.1fs",
            overall, avg_latency, duration,
        )

        return {
            "status": overall,
            "latency_ms": avg_latency,
            "duration_s": round(duration, 2),
            "sources": {k: v.get("status") for k, v in sources.items() if isinstance(v, dict)},
        }

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-316 canary: Supabase unavailable, skipping: %s", e)
        else:
            logger.error("STORY-316 canary error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def _health_canary_loop() -> None:
    """STORY-316 AC6: Run health canary every 5 minutes."""
    from config import HEALTH_CANARY_ENABLED, HEALTH_CANARY_INTERVAL_SECONDS as interval

    if not HEALTH_CANARY_ENABLED:
        logger.info("STORY-316: Health canary disabled (HEALTH_CANARY_ENABLED=false)")
        return

    # Wait 30s after startup to let app stabilize
    await asyncio.sleep(30)

    while True:
        try:
            await run_health_canary()
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("STORY-316: Health canary task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-316 canary loop: Supabase unavailable, skipping: %s", e)
            else:
                logger.error("STORY-316 canary loop error: %s", e, exc_info=True)
            await asyncio.sleep(60)


# ============================================================================
# STORY-266: Trial Reminder Emails (legacy — replaced by STORY-310 sequence)
# ============================================================================
# ============================================================================
# STORY-310: Trial Email Sequence (daily, 08:00 BRT)
# ============================================================================

# Daily check interval (24h). Cron runs daily at 08:00 BRT (11:00 UTC).
TRIAL_SEQUENCE_INTERVAL_SECONDS = 24 * 60 * 60

# Max emails per execution cycle (AC9)
TRIAL_SEQUENCE_BATCH_SIZE = 50



# ============================================================================
# STORY-309 AC4: Pre-Dunning Card Expiry Warning
# ============================================================================

# Check interval: every 24 hours (check once per day)
PRE_DUNNING_INTERVAL_SECONDS = 24 * 60 * 60


async def start_pre_dunning_task() -> asyncio.Task:
    """STORY-309 AC4: Start the periodic pre-dunning card expiry check.

    Runs once on startup (after 120s delay), then every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_pre_dunning_loop(), name="pre_dunning")
    logger.info("Pre-dunning card expiry check started (interval: 24h)")
    return task


async def check_pre_dunning_cards() -> dict:
    """STORY-309 AC4: Check for cards expiring within 7 days and send warnings.

    Uses Stripe API to list customers with cards about to expire.
    For each expiring card, sends a pre-dunning email via the dunning service.

    Returns:
        dict with counts: {"sent": N, "skipped": M, "errors": E}
    """
    import os

    try:
        import stripe
        stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe_key:
            logger.debug("Pre-dunning: STRIPE_SECRET_KEY not set, skipping")
            return {"sent": 0, "skipped": 0, "errors": 0, "disabled": True}

        from supabase_client import get_supabase, sb_execute
        from services.dunning import send_pre_dunning_email

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Target: cards expiring in the current month (7 days from now)
        target_date = now + timedelta(days=7)
        target_month = target_date.month
        target_year = target_date.year

        sent = 0
        skipped = 0
        errors = 0

        # Find active subscribers with Stripe customer IDs
        subs_result = await sb_execute(
            sb.table("user_subscriptions")
            .select("user_id, stripe_customer_id")
            .eq("is_active", True)
            .eq("subscription_status", "active")
            .not_.is_("stripe_customer_id", "null")
        )

        if not subs_result.data:
            return {"sent": 0, "skipped": 0, "errors": 0}

        for sub in subs_result.data:
            try:
                customer_id = sub.get("stripe_customer_id")
                user_id = sub.get("user_id")

                if not customer_id or not user_id:
                    continue

                # Check customer's default payment method via Stripe API
                customer = stripe.Customer.retrieve(
                    customer_id,
                    api_key=stripe_key,
                    expand=["default_source", "invoice_settings.default_payment_method"],
                )

                # Get card details from default payment method
                pm = customer.get("invoice_settings", {}).get("default_payment_method")
                card_info = None

                if pm and hasattr(pm, "card"):
                    card_info = pm.card
                elif customer.get("default_source") and hasattr(customer.default_source, "exp_month"):
                    card_info = customer.default_source

                if not card_info:
                    skipped += 1
                    continue

                exp_month = getattr(card_info, "exp_month", None) or card_info.get("exp_month")
                exp_year = getattr(card_info, "exp_year", None) or card_info.get("exp_year")
                last4 = getattr(card_info, "last4", None) or card_info.get("last4", "****")

                if not exp_month or not exp_year:
                    skipped += 1
                    continue

                # Check if card expires this target month
                if exp_year == target_year and exp_month == target_month:
                    await send_pre_dunning_email(user_id, last4, exp_month, exp_year)
                    sent += 1
                else:
                    skipped += 1

            except Exception as e:
                errors += 1
                logger.debug(f"Pre-dunning check failed for customer: {e}")

        logger.info(f"Pre-dunning check: sent={sent}, skipped={skipped}, errors={errors}")
        return {"sent": sent, "skipped": skipped, "errors": errors}

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("Pre-dunning check skipped (Supabase unavailable): %s", e)
        else:
            logger.error(f"Pre-dunning check failed: {e}", exc_info=True)
        return {"sent": 0, "skipped": 0, "errors": 1, "error": str(e)}


async def _pre_dunning_loop() -> None:
    """STORY-309 AC4: Run pre-dunning card check periodically."""
    # Delay 120s after startup
    await asyncio.sleep(120)

    while True:
        try:
            result = await check_pre_dunning_cards()
            logger.info(
                f"Pre-dunning cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(PRE_DUNNING_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Pre-dunning task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Pre-dunning loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Pre-dunning loop error: {e}", exc_info=True)
            await asyncio.sleep(60)


# ============================================================================
# STORY-310: Trial Email Sequence (daily at 08:00 BRT)
# ============================================================================

# ============================================================================
# STORY-315 AC8: Search Alerts (daily at 08:00 BRT = 11:00 UTC)
# ============================================================================

ALERTS_LOCK_KEY = "smartlic:alerts:lock"
ALERTS_LOCK_TTL = 30 * 60  # 30 minutes


async def start_alerts_task() -> asyncio.Task:
    """STORY-315 AC8: Start the daily search alerts background task.

    Calculates initial delay to align with ALERTS_HOUR_UTC (08:00 BRT),
    then runs every 24 hours with Redis lock protection.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_alerts_loop(), name="search_alerts")
    logger.info("STORY-315: Search alerts task started (daily at 08:00 BRT)")
    return task


async def run_search_alerts() -> dict:
    """Execute a single search alerts run with lock protection.

    AC8: Uses Redis lock with 30min TTL to prevent duplicate execution.
    Processes max 100 alerts per run, 10 concurrent.
    Respects ALERTS_ENABLED flag.
    """
    import time as _time

    from config import ALERTS_ENABLED, ALERTS_SYSTEM_ENABLED

    if not ALERTS_SYSTEM_ENABLED:
        return {"status": "disabled", "reason": "ALERTS_SYSTEM_ENABLED=false"}

    if not ALERTS_ENABLED:
        logger.info("STORY-315: Alerts disabled (ALERTS_ENABLED=false)")
        return {"status": "disabled"}

    # Acquire Redis lock
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                ALERTS_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=ALERTS_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("STORY-315: Alerts skipped — lock already held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"STORY-315: Redis lock check failed (proceeding): {e}")
        lock_acquired = True  # Proceed without lock on Redis failure

    try:
        from services.alert_matcher import match_alerts, finalize_matched_alert
        from services.alert_service import get_sent_item_ids
        from templates.emails.alert_digest import (
            render_alert_digest_email,
            get_alert_digest_subject,
        )
        from routes.alerts import get_alert_unsubscribe_url
        from email_service import send_email_async
        from metrics import (
            ALERTS_PROCESSED,
            ALERTS_ITEMS_MATCHED,
            ALERTS_EMAILS_SENT,
            ALERTS_PROCESSING_DURATION,
        )

        start = _time.time()

        # AC8: Run matching engine (max 100 alerts)
        result = await match_alerts(max_alerts=100, batch_size=10)

        # Send emails for matched alerts
        emails_sent = 0
        for payload in result.get("payloads", []):
            try:
                items = payload.get("new_items", [])
                if not items:
                    continue

                alert_id = payload["alert_id"]
                unsubscribe_url = get_alert_unsubscribe_url(alert_id)
                alert_name = payload.get("alert_name", "suas licitacoes")

                # AC5: Render email (max 20 items)
                html = render_alert_digest_email(
                    user_name=payload["full_name"],
                    alert_name=alert_name,
                    opportunities=items[:20],
                    total_count=len(items),
                    unsubscribe_url=unsubscribe_url,
                )
                subject = get_alert_digest_subject(len(items), alert_name)

                # AC7: Send with List-Unsubscribe header
                send_email_async(
                    to=payload["email"],
                    subject=subject,
                    html=html,
                    headers={
                        "List-Unsubscribe": f"<{unsubscribe_url}>",
                        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                    },
                    tags=[
                        {"name": "category", "value": "alert_digest"},
                        {"name": "alert_id", "value": alert_id[:8]},
                    ],
                )

                # Track sent items for dedup
                item_ids = [item["id"] for item in items if item.get("id")]
                await finalize_matched_alert(alert_id, item_ids)

                emails_sent += 1
                ALERTS_EMAILS_SENT.labels(mode="individual").inc()
                ALERTS_ITEMS_MATCHED.inc(len(items))

            except Exception as e:
                logger.error(
                    "STORY-315: Failed to send alert email for %s: %s",
                    payload.get("alert_id", "?")[:8], e,
                )

        # Record metrics
        ALERTS_PROCESSED.labels(outcome="matched").inc(result.get("matched", 0))
        ALERTS_PROCESSED.labels(outcome="skipped").inc(result.get("skipped", 0))
        ALERTS_PROCESSED.labels(outcome="error").inc(result.get("errors", 0))

        duration = _time.time() - start
        ALERTS_PROCESSING_DURATION.observe(duration)

        result["emails_sent"] = emails_sent
        result["duration_s"] = round(duration, 2)

        logger.info(
            "STORY-315: Alert cycle complete — "
            "matched=%d, emails=%d, skipped=%d, errors=%d, duration=%.1fs",
            result.get("matched", 0),
            emails_sent,
            result.get("skipped", 0),
            result.get("errors", 0),
            duration,
        )

        return result

    finally:
        # Release lock
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(ALERTS_LOCK_KEY)
            except Exception:
                pass


async def _alerts_loop() -> None:
    """STORY-315 AC8: Run search alerts daily at configured hour."""
    from config import ALERTS_ENABLED, ALERTS_SYSTEM_ENABLED, ALERTS_HOUR_UTC

    if not ALERTS_SYSTEM_ENABLED:
        logger.info("SHIP-002: Alert system disabled (ALERTS_SYSTEM_ENABLED=false)")
        return

    if not ALERTS_ENABLED:
        logger.info("STORY-315: Alerts disabled (ALERTS_ENABLED=false)")
        return

    # Calculate delay until next target hour
    now = datetime.now(timezone.utc)
    next_run = now.replace(
        hour=ALERTS_HOUR_UTC, minute=0, second=0, microsecond=0,
    )
    if now.hour >= ALERTS_HOUR_UTC:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        "STORY-315: Alerts first run in %.0fs (target: %s)",
        initial_delay, next_run.isoformat(),
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await run_search_alerts()
            logger.info(
                "STORY-315 alert cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-315: Alerts task cancelled")
            break
        except Exception as e:
            logger.error(f"STORY-315: Alerts loop error: {e}", exc_info=True)
            await asyncio.sleep(300)


# ============================================================================
# STORY-314: Stripe ⇄ DB Reconciliation (daily at 03:00 BRT = 06:00 UTC)
# ============================================================================

RECONCILIATION_LOCK_KEY = "smartlic:reconciliation:lock"
RECONCILIATION_LOCK_TTL = 30 * 60  # 30 minutes


async def start_reconciliation_task() -> asyncio.Task:
    """STORY-314 AC5: Start the daily Stripe reconciliation background task.

    Calculates initial delay to align with RECONCILIATION_HOUR_UTC,
    then runs every 24 hours with Redis lock protection.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_reconciliation_loop(), name="stripe_reconciliation")
    logger.info("STORY-314: Stripe reconciliation task started (daily at 03:00 BRT)")
    return task


async def run_reconciliation() -> dict:
    """Execute a single reconciliation run with lock protection.

    AC6: Uses Redis lock with 30min TTL to prevent duplicate execution.
    Returns the reconciliation result dict, or a skip-status dict if locked.
    """
    from services.stripe_reconciliation import (
        reconcile_subscriptions,
        save_reconciliation_report,
        send_reconciliation_alert,
    )

    # AC6: Acquire Redis lock
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                RECONCILIATION_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=RECONCILIATION_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("Reconciliation skipped — lock already held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"Redis lock check failed (proceeding without lock): {e}")
        lock_acquired = True  # Proceed without lock on Redis failure

    try:
        result = await reconcile_subscriptions()
        await save_reconciliation_report(result)
        await send_reconciliation_alert(result)
        return result
    finally:
        # Release lock
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(RECONCILIATION_LOCK_KEY)
            except Exception:
                pass  # Lock will expire via TTL


async def _reconciliation_loop() -> None:
    """STORY-314 AC5: Run Stripe reconciliation daily at configured hour."""
    from config import RECONCILIATION_ENABLED, RECONCILIATION_HOUR_UTC

    if not RECONCILIATION_ENABLED:
        logger.info("Reconciliation disabled (RECONCILIATION_ENABLED=false)")
        return

    # Calculate delay until next target hour
    now = datetime.now(timezone.utc)
    next_run = now.replace(
        hour=RECONCILIATION_HOUR_UTC, minute=0, second=0, microsecond=0
    )
    if now.hour >= RECONCILIATION_HOUR_UTC:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        f"STORY-314: Reconciliation first run in {initial_delay:.0f}s "
        f"(target: {next_run.isoformat()})"
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await run_reconciliation()
            logger.info(
                f"STORY-314 reconciliation cycle: "
                f"checked={result.get('total_checked', 0)}, "
                f"divergences={result.get('divergences_found', 0)} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(24 * 60 * 60)  # 24 hours
        except asyncio.CancelledError:
            logger.info("Reconciliation task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Reconciliation skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Reconciliation loop error: {e}", exc_info=True)
            await asyncio.sleep(300)  # Retry in 5min on error


# ============================================================================
# STORY-323: Monthly Partner Revenue Share Report (day 1, 09:00 BRT = 12:00 UTC)
# ============================================================================

REVENUE_SHARE_LOCK_KEY = "smartlic:revenue_share:lock"
REVENUE_SHARE_LOCK_TTL = 30 * 60  # 30 minutes


async def start_revenue_share_task() -> asyncio.Task:
    """STORY-323 AC9: Start the monthly revenue share report task.

    Runs on the 1st of each month at 09:00 BRT (12:00 UTC).
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_revenue_share_loop(), name="revenue_share_report")
    logger.info("STORY-323: Revenue share report task started (monthly, day 1, 09:00 BRT)")
    return task


async def run_revenue_share_report() -> dict:
    """Execute monthly revenue share report with lock protection."""
    # Acquire Redis lock
    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                REVENUE_SHARE_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=REVENUE_SHARE_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("STORY-323: Revenue share report skipped — lock held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"STORY-323: Redis lock check failed (proceeding): {e}")
        lock_acquired = True

    try:
        from services.partner_service import generate_monthly_revenue_report

        # Report for previous month
        now = datetime.now(timezone.utc)
        if now.month == 1:
            report_year = now.year - 1
            report_month = 12
        else:
            report_year = now.year
            report_month = now.month - 1

        result = await generate_monthly_revenue_report(report_year, report_month)

        logger.info(
            "STORY-323: Revenue share report generated — %d/%d, "
            "%d partners, total_share=R$%.2f",
            report_month, report_year,
            len(result.get("partner_reports", [])),
            result.get("total_share", 0),
        )
        return result

    finally:
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(REVENUE_SHARE_LOCK_KEY)
            except Exception:
                pass


async def _revenue_share_loop() -> None:
    """STORY-323 AC9: Run revenue share report monthly on day 1."""
    # Calculate delay until next 1st of month at 12:00 UTC (09:00 BRT)
    now = datetime.now(timezone.utc)
    target_hour = 12  # 09:00 BRT = 12:00 UTC

    # Next 1st of month
    if now.month == 12:
        next_run = datetime(now.year + 1, 1, 1, target_hour, 0, 0, tzinfo=timezone.utc)
    else:
        next_run = datetime(now.year, now.month + 1, 1, target_hour, 0, 0, tzinfo=timezone.utc)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 31 * 86400))

    logger.info(
        "STORY-323: Revenue share report first run in %.0fs (target: %s)",
        initial_delay, next_run.isoformat(),
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await run_revenue_share_report()
            logger.info(
                "STORY-323 revenue share cycle: %s at %s",
                result.get("total_share", "N/A"),
                datetime.now(timezone.utc).isoformat(),
            )
            # Wait ~30 days for next run
            await asyncio.sleep(30 * 24 * 60 * 60)
        except asyncio.CancelledError:
            logger.info("STORY-323: Revenue share report task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-323: Revenue share skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"STORY-323: Revenue share loop error: {e}", exc_info=True)
            await asyncio.sleep(3600)  # Retry in 1h on error


async def start_trial_sequence_task() -> asyncio.Task:
    """STORY-310 AC9: Start the daily trial email sequence background task.

    Calculates initial delay to align with 08:00 BRT (11:00 UTC),
    then runs every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_trial_sequence_loop(), name="trial_email_sequence")
    logger.info("STORY-310: Trial email sequence task started (daily at 08:00 BRT)")
    return task


async def _trial_sequence_loop() -> None:
    """STORY-310 AC9: Run trial email sequence daily at ~08:00 BRT."""
    # Calculate delay until next 11:00 UTC (08:00 BRT)
    now = datetime.now(timezone.utc)
    target_hour = 11  # 08:00 BRT = 11:00 UTC
    next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    if now.hour >= target_hour:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    # Cap at 24h max, minimum 60s
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        f"STORY-310: Trial sequence first run in {initial_delay:.0f}s "
        f"(target: {next_run.isoformat()})"
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            from services.trial_email_sequence import process_trial_emails
            result = await process_trial_emails(batch_size=TRIAL_SEQUENCE_BATCH_SIZE)
            logger.info(
                f"STORY-310 trial sequence cycle: {result} "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(TRIAL_SEQUENCE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Trial email sequence task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("Trial email sequence skipped (Supabase unavailable): %s", e)
            else:
                logger.error(f"Trial email sequence loop error: {e}", exc_info=True)
            await asyncio.sleep(300)  # Retry in 5min on error


# ============================================================================
# STORY-324 AC3: Daily sector stats refresh for SEO landing pages
# ============================================================================

# Sector stats refresh interval: every 24 hours
SECTOR_STATS_INTERVAL_SECONDS = 24 * 60 * 60
SECTOR_STATS_HOUR_UTC = 6  # 06:00 UTC = 03:00 BRT


async def start_sector_stats_task() -> asyncio.Task:
    """STORY-324 AC3: Start the daily sector stats refresh background task.

    Calculates initial delay to align with 06:00 UTC,
    then runs every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_sector_stats_loop(), name="sector_stats_refresh")
    logger.info("STORY-324: Sector stats refresh task started (daily at 06:00 UTC)")
    return task


async def _sector_stats_loop() -> None:
    """STORY-324 AC3: Refresh all sector stats daily at 06:00 UTC."""
    # Calculate delay until next 06:00 UTC
    now = datetime.now(timezone.utc)
    next_run = now.replace(hour=SECTOR_STATS_HOUR_UTC, minute=0, second=0, microsecond=0)
    if now.hour >= SECTOR_STATS_HOUR_UTC:
        next_run += timedelta(days=1)

    initial_delay = (next_run - now).total_seconds()
    initial_delay = max(60, min(initial_delay, 86400))

    logger.info(
        f"STORY-324: Sector stats first refresh in {initial_delay:.0f}s "
        f"(target: {next_run.isoformat()})"
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            from routes.sectors_public import refresh_all_sector_stats
            refreshed = await refresh_all_sector_stats()
            logger.info(
                f"STORY-324: Sector stats refreshed: {refreshed}/15 sectors "
                f"at {datetime.now(timezone.utc).isoformat()}"
            )
            await asyncio.sleep(SECTOR_STATS_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("Sector stats refresh task cancelled")
            break
        except Exception as e:
            logger.error(f"Sector stats refresh error: {e}", exc_info=True)
            await asyncio.sleep(600)  # Retry in 10min on error


# ============================================================================
# STORY-353: Support SLA — check unanswered messages (every 4h)
# ============================================================================


async def start_support_sla_task() -> asyncio.Task:
    """STORY-353 AC3: Start the periodic support SLA check task.

    Runs every 4 hours. Checks for unanswered conversations exceeding
    20 business hours and sends admin email alerts.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_support_sla_loop(), name="support_sla")
    logger.info("STORY-353: Support SLA check started (interval: 4h)")
    return task


async def check_unanswered_messages() -> dict:
    """STORY-353 AC3+AC4: Check for unanswered support messages.

    Finds conversations with status != 'resolvido' and first_response_at IS NULL,
    calculates elapsed business hours since created_at, and sends email alerts
    for those exceeding 20 business hours.

    SHIP-002 AC7: Early return when MESSAGES_ENABLED=False.

    Returns:
        dict with counts: {"checked": N, "breached": M, "alerted": A}
    """
    import os

    from config import MESSAGES_ENABLED
    if not MESSAGES_ENABLED:
        return {"checked": 0, "breached": 0, "alerted": 0, "disabled": True}

    try:
        from supabase_client import get_supabase, sb_execute
        from business_hours import calculate_business_hours
        from config import SUPPORT_SLA_ALERT_THRESHOLD_HOURS
        from metrics import SUPPORT_PENDING_MESSAGES

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        # Find unanswered conversations (no first_response_at, not resolved)
        result = await sb_execute(
            sb.table("conversations")
            .select("id, user_id, subject, category, created_at")
            .is_("first_response_at", "null")
            .neq("status", "resolvido")
            .order("created_at", desc=False)
        )

        conversations = result.data or []
        SUPPORT_PENDING_MESSAGES.set(len(conversations))

        if not conversations:
            return {"checked": 0, "breached": 0, "alerted": 0}

        breached = []
        for conv in conversations:
            from dateutil.parser import isoparse
            created_at = isoparse(conv["created_at"])
            elapsed_hours = calculate_business_hours(created_at, now)

            if elapsed_hours >= SUPPORT_SLA_ALERT_THRESHOLD_HOURS:
                breached.append({
                    "id": conv["id"],
                    "subject": conv["subject"],
                    "category": conv["category"],
                    "elapsed_hours": elapsed_hours,
                    "created_at": conv["created_at"],
                })

        # Send alert email if breaches found
        alerted = 0
        if breached:
            admin_email = os.getenv("ADMIN_EMAIL", "tiago.sasaki@gmail.com")
            try:
                from email_service import send_email_async

                items_html = "".join(
                    f"<tr><td>{b['subject']}</td>"
                    f"<td>{b['category']}</td>"
                    f"<td>{b['elapsed_hours']:.1f}h</td>"
                    f"<td>{b['created_at'][:16]}</td></tr>"
                    for b in breached
                )

                html = f"""
                <h2>Alerta de SLA de Suporte</h2>
                <p>{len(breached)} mensagem(ns) sem resposta excederam {SUPPORT_SLA_ALERT_THRESHOLD_HOURS}h uteis.</p>
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
                    <tr style="background:#f0f0f0;">
                        <th>Assunto</th><th>Categoria</th>
                        <th>Horas uteis</th><th>Criada em</th>
                    </tr>
                    {items_html}
                </table>
                <p>Acesse <a href="https://smartlic.tech/mensagens">SmartLic Mensagens</a> para responder.</p>
                """

                send_email_async(
                    to=admin_email,
                    subject=f"[SLA] {len(breached)} mensagem(ns) sem resposta > {SUPPORT_SLA_ALERT_THRESHOLD_HOURS}h",
                    html=html,
                    tags=[{"name": "category", "value": "sla_alert"}],
                )
                alerted = len(breached)
                logger.warning(
                    "STORY-353 SLA alert: %d breached conversations, email sent to %s",
                    len(breached), admin_email,
                )
            except Exception as e:
                logger.error("STORY-353: Failed to send SLA alert email: %s", e)

        logger.info(
            "STORY-353 SLA check: checked=%d, breached=%d, alerted=%d",
            len(conversations), len(breached), alerted,
        )
        return {"checked": len(conversations), "breached": len(breached), "alerted": alerted}

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-353: Support SLA check skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-353: Support SLA check error: %s", e, exc_info=True)
        return {"checked": 0, "breached": 0, "alerted": 0, "error": str(e)}


async def _support_sla_loop() -> None:
    """STORY-353 AC3: Run support SLA check every 4 hours."""
    from config import SUPPORT_SLA_CHECK_INTERVAL_SECONDS

    # Delay 60s after startup
    await asyncio.sleep(60)

    while True:
        try:
            result = await check_unanswered_messages()
            logger.info(
                "STORY-353 SLA cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(SUPPORT_SLA_CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("STORY-353: Support SLA task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-353 SLA loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error("STORY-353 SLA loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


# ============================================================================
# STORY-358: Daily volume recording (daily at 07:00 UTC = 04:00 BRT)
# ============================================================================

DAILY_VOLUME_INTERVAL_SECONDS = 24 * 60 * 60
DAILY_VOLUME_HOUR_UTC = 7  # 07:00 UTC = 04:00 BRT


async def start_daily_volume_task() -> asyncio.Task:
    """STORY-358 AC2: Start the daily volume recording background task.

    Calculates initial delay to align with 07:00 UTC,
    then runs every 24 hours.
    Returns the Task so it can be cancelled during shutdown.
    """
    task = asyncio.create_task(_daily_volume_loop(), name="daily_volume")
    logger.info("STORY-358: Daily volume recording task started (daily at 07:00 UTC)")
    return task


async def record_daily_volume() -> dict:
    """STORY-358 AC2: Record count of bids processed in the last 24 hours.

    Queries search_sessions for sessions completed in the last 24h,
    sums total_raw to get total bids processed.
    Logs the result for observability.

    Returns dict with volume stats.
    """
    try:
        from supabase_client import get_supabase, sb_execute

        sb = get_supabase()
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(hours=24)).isoformat()

        # Sum total_raw from all completed sessions in the last 24h
        result = await sb_execute(
            sb.table("search_sessions")
            .select("total_raw")
            .gte("created_at", yesterday)
            .in_("status", ["completed", "completed_partial"])
        )

        sessions = result.data or []
        total_bids = sum(s.get("total_raw") or 0 for s in sessions)
        session_count = len(sessions)

        logger.info(
            "STORY-358 daily volume: %d bids processed across %d sessions in last 24h (at %s)",
            total_bids, session_count, now.isoformat(),
        )

        return {
            "total_bids_24h": total_bids,
            "session_count": session_count,
            "recorded_at": now.isoformat(),
        }

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-358: Daily volume recording skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-358: Daily volume recording error: %s", e, exc_info=True)
        return {"total_bids_24h": 0, "session_count": 0, "error": str(e)}


async def _daily_volume_loop() -> None:
    """STORY-358 AC2: Record daily volume at 07:00 UTC."""
    # Calculate delay until next 07:00 UTC
    now = datetime.now(timezone.utc)
    target = now.replace(hour=DAILY_VOLUME_HOUR_UTC, minute=0, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    initial_delay = (target - now).total_seconds()
    logger.info(
        "STORY-358: Daily volume first run in %.0f seconds (at %s)",
        initial_delay, target.isoformat(),
    )
    await asyncio.sleep(initial_delay)

    while True:
        try:
            result = await record_daily_volume()
            logger.info(
                "STORY-358 daily volume cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(DAILY_VOLUME_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("STORY-358: Daily volume task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("STORY-358 daily volume loop skipped (Supabase unavailable): %s", e)
            else:
                logger.error("STORY-358 daily volume loop error: %s", e, exc_info=True)
            await asyncio.sleep(600)


# ============================================================================
# STORY-362 AC7: Expired search results cleanup (every 6 hours)
# ============================================================================

RESULTS_CLEANUP_INTERVAL_SECONDS = 6 * 60 * 60


async def start_results_cleanup_task() -> asyncio.Task:
    """STORY-362 AC7: Start periodic expired search results cleanup.

    Deletes rows from search_results_store where expires_at < now().
    Runs immediately on startup, then every 6 hours.
    """
    task = asyncio.create_task(_results_cleanup_loop(), name="results_cleanup")
    logger.info("STORY-362: Expired results cleanup task started (interval: 6h)")
    return task


async def cleanup_expired_results() -> dict:
    """STORY-362 AC7: Delete expired search results from Supabase L3.

    Returns dict with count of deleted rows.
    """
    try:
        from supabase_client import get_supabase, sb_execute

        sb = get_supabase()
        now = datetime.now(timezone.utc).isoformat()

        result = await sb_execute(
            sb.table("search_results_store")
            .delete()
            .lt("expires_at", now)
        )

        deleted = len(result.data) if result and result.data else 0
        logger.info(
            "STORY-362: Cleaned up %d expired search results at %s",
            deleted, now,
        )
        return {"deleted": deleted, "cleaned_at": now}

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-362: Results cleanup skipped (Supabase unavailable): %s", e)
        else:
            logger.error("STORY-362: Results cleanup error: %s", e, exc_info=True)
        return {"deleted": 0, "error": str(e)}


async def _results_cleanup_loop() -> None:
    """STORY-362 AC7: Cleanup loop — runs immediately, then every 6h."""
    while True:
        try:
            result = await cleanup_expired_results()
            logger.info(
                "STORY-362 results cleanup cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
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


# ============================================================================
# DEBT-010 DB-015: Plan reconciliation (profiles.plan_type vs user_subscriptions)
# DEBT-010 DB-031: JSONB table size monitoring (Prometheus gauge)
# ============================================================================

PLAN_RECONCILIATION_LOCK_KEY = "smartlic:plan_reconciliation:lock"
PLAN_RECONCILIATION_LOCK_TTL = 10 * 60  # 10 minutes
PLAN_RECONCILIATION_INTERVAL = 12 * 60 * 60  # 12 hours

# Tables to monitor for size (JSONB-heavy)
_MONITORED_TABLES = [
    "search_results_cache",
    "search_results_store",
    "search_sessions",
    "stripe_webhook_events",
    "profiles",
    "user_subscriptions",
    "conversations",
    "messages",
    "alert_runs",
    "classification_feedback",
]


async def start_plan_reconciliation_task() -> asyncio.Task:
    """DEBT-010 DB-015: Start periodic plan reconciliation + table size monitoring."""
    task = asyncio.create_task(
        _plan_reconciliation_loop(), name="plan_reconciliation"
    )
    logger.info("DEBT-010: Plan reconciliation task started (interval: 12h)")
    return task


async def run_plan_reconciliation() -> dict:
    """DEBT-010 DB-015: Compare profiles.plan_type vs user_subscriptions.plan_id.

    Detects drift but does NOT auto-fix — logs for manual review.
    Returns dict with drift details.
    """
    from supabase_client import get_supabase, sb_execute
    from metrics import PLAN_RECONCILIATION_RUNS, PLAN_RECONCILIATION_DRIFT

    PLAN_RECONCILIATION_RUNS.inc()

    lock_acquired = False
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            lock_acquired = await redis.set(
                PLAN_RECONCILIATION_LOCK_KEY,
                datetime.now(timezone.utc).isoformat(),
                nx=True,
                ex=PLAN_RECONCILIATION_LOCK_TTL,
            )
            if not lock_acquired:
                logger.info("DEBT-010: Plan reconciliation skipped — lock held")
                return {"status": "skipped", "reason": "lock_held"}
    except Exception as e:
        logger.warning(f"DEBT-010: Redis lock failed (proceeding): {e}")
        lock_acquired = True

    drift_details = []
    try:
        sb = get_supabase()

        # Fetch profiles with plan_type
        profiles_result = await sb_execute(
            sb.table("profiles").select("id, plan_type")
        )
        profiles = {p["id"]: p["plan_type"] for p in (profiles_result.data or [])}

        # Fetch active subscriptions with plan_id
        subs_result = await sb_execute(
            sb.table("user_subscriptions")
            .select("user_id, plan_id")
            .eq("is_active", True)
        )
        subs = {s["user_id"]: s["plan_id"] for s in (subs_result.data or [])}

        # Detect drift
        for user_id, plan_type in profiles.items():
            sub_plan = subs.get(user_id)
            if sub_plan is None:
                # No active subscription — ok if free_trial or cancelled
                if plan_type not in ("free_trial", "cancelled", None, ""):
                    drift_details.append({
                        "user_id": user_id[:8] + "...",
                        "profile_plan": plan_type,
                        "sub_plan": None,
                        "direction": "orphan_profile",
                    })
                    PLAN_RECONCILIATION_DRIFT.labels(direction="orphan_profile").inc()
            elif plan_type != sub_plan:
                drift_details.append({
                    "user_id": user_id[:8] + "...",
                    "profile_plan": plan_type,
                    "sub_plan": sub_plan,
                    "direction": "profiles_stale",
                })
                PLAN_RECONCILIATION_DRIFT.labels(direction="profiles_stale").inc()

        result = {
            "status": "completed",
            "total_profiles": len(profiles),
            "total_active_subs": len(subs),
            "drift_count": len(drift_details),
            "drift_details": drift_details[:20],  # Cap log size
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        if drift_details:
            logger.warning(
                "DEBT-010: Plan reconciliation found %d drifts: %s",
                len(drift_details), drift_details[:5],
            )
        else:
            logger.info(
                "DEBT-010: Plan reconciliation clean — %d profiles, %d active subs",
                len(profiles), len(subs),
            )
        return result

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("DEBT-010: Plan reconciliation skipped (Supabase unavailable): %s", e)
        else:
            logger.error("DEBT-010: Plan reconciliation error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        if lock_acquired:
            try:
                from redis_pool import get_redis_pool
                redis = await get_redis_pool()
                if redis:
                    await redis.delete(PLAN_RECONCILIATION_LOCK_KEY)
            except Exception:
                pass


async def update_table_size_metrics() -> dict:
    """DEBT-010 DB-031: Update Prometheus gauge with JSONB-heavy table sizes.

    Uses pg_total_relation_size() via Supabase RPC for each monitored table.
    Falls back gracefully if RPC function not available.
    """
    from supabase_client import get_supabase, sb_execute_direct
    from metrics import DB_TABLE_SIZE_BYTES

    sizes = {}
    try:
        sb = get_supabase()
        for table_name in _MONITORED_TABLES:
            try:
                result = await sb_execute_direct(
                    sb.rpc("pg_total_relation_size_safe", {"tbl": table_name})
                )
                if result and result.data is not None:
                    size_bytes = int(result.data) if not isinstance(result.data, list) else int(result.data[0]) if result.data else 0
                    DB_TABLE_SIZE_BYTES.labels(table_name=table_name).set(size_bytes)
                    sizes[table_name] = size_bytes
            except Exception as e:
                logger.debug("DEBT-010: Table size query failed for %s: %s", table_name, e)
                sizes[table_name] = -1

        logger.info("DEBT-010: Table sizes updated — %d tables", len(sizes))
        return {"status": "ok", "sizes": sizes}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("DEBT-010: Table size metrics skipped (Supabase unavailable): %s", e)
        else:
            logger.error("DEBT-010: Table size metrics error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def _plan_reconciliation_loop() -> None:
    """DEBT-010: Plan reconciliation + table sizes — runs every 12h."""
    # Initial delay: 5 minutes after startup
    await asyncio.sleep(300)

    table_size_counter = 0
    while True:
        try:
            await run_plan_reconciliation()

            # Table sizes on every cycle
            table_size_counter += 1
            await update_table_size_metrics()

            await asyncio.sleep(PLAN_RECONCILIATION_INTERVAL)
        except asyncio.CancelledError:
            logger.info("DEBT-010: Plan reconciliation task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("DEBT-010: Reconciliation loop skipped: %s", e)
            else:
                logger.error("DEBT-010: Reconciliation loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)


# ============================================================================
# CRIT-081: Periodic cache coverage check (every hour)
# ============================================================================

COVERAGE_CHECK_INTERVAL = int(os.environ.get("ENSURE_COVERAGE_INTERVAL_HOURS", "1")) * 3600


async def ensure_minimum_cache_coverage() -> dict:
    """CRIT-081: Ensure all active sector×UF combos have fresh cache (<12h).

    Checks the top 5 UFs against all configured sectors.
    Triggers background revalidation for any sector/UF combo missing fresh cache.

    Returns dict with: deficit, dispatched.
    """
    from search_cache import trigger_background_revalidation
    from sectors import SECTORS
    from config import ALL_BRAZILIAN_UFS, WARMUP_ENABLED

    if not WARMUP_ENABLED:
        logger.debug("CRIT-081: coverage check skipped (WARMUP_ENABLED=false)")
        return {"deficit": 0, "dispatched": 0, "skipped": True}

    deficit = 0
    dispatched = 0

    try:
        # Use top 5 UFs from priority list
        prioritized = await _get_prioritized_ufs(ALL_BRAZILIAN_UFS)
        top_ufs = prioritized[:5]

        all_sectors = list(SECTORS.values())

        for sector in all_sectors:
            for uf in top_ufs:
                age_hours = await _get_cache_entry_age(sector.id, uf)
                if age_hours is None or age_hours > 12:
                    deficit += 1
                    try:
                        params = {
                            "setor_id": sector.id,
                            "ufs": [uf],
                            "status": None,
                            "modalidades": None,
                            "modo_busca": None,
                        }
                        request_data = {
                            "ufs": [uf],
                            "data_inicial": (date.today() - timedelta(days=10)).isoformat(),
                            "data_final": date.today().isoformat(),
                            "modalidades": None,
                        }
                        ok = await trigger_background_revalidation(
                            user_id="00000000-0000-0000-0000-000000000000",
                            params=params,
                            request_data=request_data,
                        )
                        if ok:
                            dispatched += 1
                        await asyncio.sleep(0.5)  # Rate limit
                    except Exception as e:
                        logger.warning(
                            "CRIT-081: coverage revalidation failed for %s:%s: %s",
                            sector.id, uf, e,
                        )

        logger.info(
            "CRIT-081: coverage check complete: deficit=%d, dispatched=%d, "
            "sectors=%d, ufs=%d",
            deficit, dispatched, len(all_sectors), len(top_ufs),
        )

        # Update metric if available
        try:
            from metrics import WARMUP_COVERAGE_RATIO
            total = len(all_sectors) * len(top_ufs)
            covered = total - deficit
            WARMUP_COVERAGE_RATIO.set(covered / total if total > 0 else 0)
        except Exception:
            pass

    except Exception as e:
        logger.error("CRIT-081: ensure_minimum_cache_coverage failed: %s", e, exc_info=True)

    return {"deficit": deficit, "dispatched": dispatched}


async def _get_cache_entry_age(sector_id: str, uf: str) -> float | None:
    """CRIT-081: Get age in hours of the most recent cache entry for sector+UF.

    Returns age in hours (float), or None if no cache entry exists.
    Uses Supabase search_results_cache table — looks for entries whose
    search_params contain the given sector_id and uf.
    """
    try:
        from supabase_client import get_supabase, sb_execute
        from datetime import datetime, timezone

        sb = get_supabase()
        # Query for entries matching this sector_id
        resp = await sb_execute(
            sb.table("search_results_cache")
            .select("fetched_at, search_params")
            .eq("search_params->>setor_id", sector_id)
            .order("fetched_at", desc=True)
            .limit(50)
        )

        if not resp.data:
            return None

        now = datetime.now(timezone.utc)

        for row in resp.data:
            # Check if this entry covers the UF
            sp = row.get("search_params", {})
            if not isinstance(sp, dict):
                continue
            entry_ufs = sp.get("ufs") or []
            if uf not in entry_ufs:
                continue

            fetched_at_raw = row.get("fetched_at")
            if not fetched_at_raw:
                continue
            try:
                fetched_at = datetime.fromisoformat(
                    str(fetched_at_raw).replace("Z", "+00:00")
                )
                if fetched_at.tzinfo is None:
                    fetched_at = fetched_at.replace(tzinfo=timezone.utc)
                age_hours = (now - fetched_at).total_seconds() / 3600
                return age_hours
            except (ValueError, TypeError):
                continue

        return None

    except Exception as e:
        logger.debug("CRIT-081: _get_cache_entry_age error for %s:%s: %s", sector_id, uf, e)
        return None


async def start_coverage_check_task() -> asyncio.Task:
    """CRIT-081: Start periodic cache coverage check (every hour)."""
    task = asyncio.create_task(
        _coverage_check_loop(),
        name="coverage_check",
    )
    logger.info(
        "CRIT-081: Coverage check task started (interval: %ds, initial_delay: 300s)",
        COVERAGE_CHECK_INTERVAL,
    )
    return task


async def _coverage_check_loop() -> None:
    """CRIT-081: Run coverage check after startup delay then every hour."""
    # Wait 5 minutes after startup (let warmup run first)
    await asyncio.sleep(300)

    while True:
        try:
            result = await ensure_minimum_cache_coverage()
            logger.info("CRIT-081: coverage check result: %s", result)
        except asyncio.CancelledError:
            logger.info("CRIT-081: coverage check task cancelled")
            return
        except Exception as e:
            logger.error("CRIT-081: coverage check task error: %s", e, exc_info=True)

        try:
            await asyncio.sleep(COVERAGE_CHECK_INTERVAL)
        except asyncio.CancelledError:
            logger.info("CRIT-081: coverage check task cancelled during sleep")
            return


# ============================================================================
# HARDEN-028: Stripe webhook events purge (> 90 days)
# ============================================================================

STRIPE_EVENTS_RETENTION_DAYS = 90
STRIPE_PURGE_INTERVAL_SECONDS = 24 * 60 * 60  # daily


async def start_stripe_events_purge_task() -> asyncio.Task:
    """HARDEN-028 AC2: Start daily Stripe webhook events purge."""
    task = asyncio.create_task(_stripe_events_purge_loop(), name="stripe_events_purge")
    logger.info("HARDEN-028: Stripe events purge task started (interval: 24h, retention: %dd)", STRIPE_EVENTS_RETENTION_DAYS)
    return task


async def purge_old_stripe_events() -> dict:
    """HARDEN-028 AC1: Delete stripe_webhook_events older than 90 days.

    Returns dict with count of deleted rows.
    """
    try:
        from supabase_client import get_supabase, sb_execute

        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=STRIPE_EVENTS_RETENTION_DAYS)).isoformat()

        result = await sb_execute(
            sb.table("stripe_webhook_events")
            .delete()
            .lt("processed_at", cutoff)
        )

        deleted = len(result.data) if result and result.data else 0
        # AC3: Log count of deleted events
        logger.info(
            "HARDEN-028: Purged %d Stripe webhook events older than %d days (cutoff=%s)",
            deleted, STRIPE_EVENTS_RETENTION_DAYS, cutoff,
        )
        return {"deleted": deleted, "cutoff": cutoff}

    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("HARDEN-028: Stripe events purge skipped (Supabase unavailable): %s", e)
        else:
            logger.error("HARDEN-028: Stripe events purge error: %s", e, exc_info=True)
        return {"deleted": 0, "error": str(e)}


async def _stripe_events_purge_loop() -> None:
    """HARDEN-028 AC2: Purge loop — runs immediately, then every 24h."""
    while True:
        try:
            result = await purge_old_stripe_events()
            logger.info(
                "HARDEN-028 purge cycle: %s at %s",
                result, datetime.now(timezone.utc).isoformat(),
            )
            await asyncio.sleep(STRIPE_PURGE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("HARDEN-028: Stripe events purge task cancelled")
            break
        except Exception as e:
            if _is_cb_or_connection_error(e):
                logger.warning("HARDEN-028 purge loop skipped: %s", e)
            else:
                logger.error("HARDEN-028 purge loop error: %s", e, exc_info=True)
            await asyncio.sleep(300)
