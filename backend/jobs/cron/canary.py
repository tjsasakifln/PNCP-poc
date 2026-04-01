"""jobs.cron.canary — PNCP health canary and status tracking.

State (_pncp_cron_status, _pncp_cron_status_lock, _pncp_recovery_epoch) lives in
cron_jobs.py so that test fixtures that do ``cron_jobs._pncp_recovery_epoch = 0``
keep working.  All state access here goes through a lazy ``import cron_jobs``.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

HEALTH_CANARY_INTERVAL_SECONDS = 5 * 60


def _state():
    """Return the cron_jobs module (lazy, avoids circular import at load time)."""
    import cron_jobs as _cj
    return _cj


def get_pncp_cron_status() -> dict:
    m = _state()
    with m._pncp_cron_status_lock:
        return dict(m._pncp_cron_status)


def get_pncp_recovery_epoch() -> int:
    m = _state()
    with m._pncp_cron_status_lock:
        return m._pncp_recovery_epoch


def _update_pncp_cron_status(status: str, latency_ms: int | None) -> None:
    import time as _time_mod
    m = _state()
    with m._pncp_cron_status_lock:
        old_status = m._pncp_cron_status["status"]
        m._pncp_cron_status.update({"status": status, "latency_ms": latency_ms, "updated_at": _time_mod.time()})
        if old_status in ("degraded", "down") and status == "healthy":
            m._pncp_recovery_epoch += 1
            logger.info(f"CRIT-056: PNCP recovered (epoch={m._pncp_recovery_epoch})")


def _is_cb_or_connection_error(e: Exception) -> bool:
    err_name = type(e).__name__
    err_str = str(e)
    return (
        "CircuitBreaker" in err_name
        or "ConnectionError" in err_name
        or "ConnectError" in err_str
        or "PGRST205" in err_str
    )


async def run_health_canary() -> dict:
    import time as _time
    from config import HEALTH_CANARY_ENABLED
    if not HEALTH_CANARY_ENABLED:
        return {"status": "disabled"}
    start = _time.time()
    try:
        from health import get_public_status, save_health_check, detect_incident
        from metrics import HEALTH_CANARY_DURATION, HEALTH_CANARY_STATUS
        status_data = await get_public_status()
        duration = _time.time() - start
        overall = status_data.get("status", "unhealthy")
        sources = status_data.get("sources", {})
        components = status_data.get("components", {})
        latencies = [s.get("latency_ms", 0) for s in sources.values() if isinstance(s, dict) and s.get("latency_ms") is not None]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else None
        pncp_source = sources.get("pncp", {})
        if isinstance(pncp_source, dict):
            pncp_status_str = pncp_source.get("status", "unknown")
            pncp_latency = pncp_source.get("latency_ms")
            if pncp_status_str == "healthy" and pncp_latency is not None:
                _update_pncp_cron_status("healthy" if pncp_latency < 2000 else "degraded", pncp_latency)
            elif pncp_status_str in ("degraded", "unhealthy"):
                _update_pncp_cron_status("degraded" if pncp_status_str == "degraded" else "down", pncp_latency)
            else:
                _update_pncp_cron_status("unknown", pncp_latency)
        await save_health_check(overall, sources, components, avg_latency)
        await detect_incident(overall, sources)
        try:
            HEALTH_CANARY_DURATION.observe(duration)
            HEALTH_CANARY_STATUS.set({"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}.get(overall, 0.0))
        except Exception:
            pass
        from health import cleanup_old_health_checks
        await cleanup_old_health_checks()
        logger.info("STORY-316 canary: status=%s, latency=%s ms, duration=%.1fs", overall, avg_latency, duration)
        return {"status": overall, "latency_ms": avg_latency, "duration_s": round(duration, 2),
                "sources": {k: v.get("status") for k, v in sources.items() if isinstance(v, dict)}}
    except Exception as e:
        if _is_cb_or_connection_error(e):
            logger.warning("STORY-316 canary: Supabase unavailable, skipping: %s", e)
        else:
            logger.error("STORY-316 canary error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def _health_canary_loop() -> None:
    from config import HEALTH_CANARY_ENABLED, HEALTH_CANARY_INTERVAL_SECONDS as interval
    if not HEALTH_CANARY_ENABLED:
        logger.info("STORY-316: Health canary disabled")
        return
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
                logger.warning("STORY-316 canary loop: Supabase unavailable: %s", e)
            else:
                logger.error("STORY-316 canary loop error: %s", e, exc_info=True)
            await asyncio.sleep(60)


async def start_health_canary_task() -> asyncio.Task:
    task = asyncio.create_task(_health_canary_loop(), name="health_canary")
    logger.info("STORY-316: Health canary task started (interval: 5m)")
    return task
