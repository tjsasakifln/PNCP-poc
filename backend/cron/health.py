"""STORY-316: Health canary cron job (every 5 minutes)."""

import asyncio
import logging
import time as _time

from cron._loop import cron_loop, is_cb_or_connection_error
from cron.pncp_status import update_pncp_cron_status

logger = logging.getLogger(__name__)

HEALTH_CANARY_INTERVAL_SECONDS = 5 * 60


async def run_health_canary() -> dict:
    """STORY-316 AC6: Execute a single health canary check."""
    from config import HEALTH_CANARY_ENABLED

    if not HEALTH_CANARY_ENABLED:
        return {"status": "disabled"}

    start = _time.time()
    try:
        from health import get_public_status, save_health_check, detect_incident, cleanup_old_health_checks
        from metrics import HEALTH_CANARY_DURATION, HEALTH_CANARY_STATUS

        status_data = await get_public_status()
        duration = _time.time() - start

        overall = status_data.get("status", "unhealthy")
        sources = status_data.get("sources", {})
        components = status_data.get("components", {})

        latencies = [
            s.get("latency_ms", 0) for s in sources.values()
            if isinstance(s, dict) and s.get("latency_ms") is not None
        ]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else None

        # CRIT-052 AC3: Update PNCP global status
        pncp_source = sources.get("pncp", {})
        if isinstance(pncp_source, dict):
            pncp_status_str = pncp_source.get("status", "unknown")
            pncp_latency = pncp_source.get("latency_ms")
            if pncp_status_str == "healthy" and pncp_latency is not None:
                update_pncp_cron_status("healthy" if pncp_latency < 2000 else "degraded", pncp_latency)
            elif pncp_status_str in ("degraded", "unhealthy"):
                update_pncp_cron_status("degraded" if pncp_status_str == "degraded" else "down", pncp_latency)
            else:
                update_pncp_cron_status("unknown", pncp_latency)

        await save_health_check(overall, sources, components, avg_latency)
        await detect_incident(overall, sources)

        try:
            HEALTH_CANARY_DURATION.observe(duration)
            HEALTH_CANARY_STATUS.set({"healthy": 1.0, "degraded": 0.5, "unhealthy": 0.0}.get(overall, 0.0))
        except Exception:
            pass

        await cleanup_old_health_checks()

        logger.info("STORY-316 canary: status=%s, latency=%s ms, duration=%.1fs", overall, avg_latency, duration)
        return {
            "status": overall, "latency_ms": avg_latency, "duration_s": round(duration, 2),
            "sources": {k: v.get("status") for k, v in sources.items() if isinstance(v, dict)},
        }
    except Exception as e:
        if is_cb_or_connection_error(e):
            logger.warning("STORY-316 canary: Supabase unavailable, skipping: %s", e)
        else:
            logger.error("STORY-316 canary error: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


async def start_health_canary_task() -> asyncio.Task:
    from config import HEALTH_CANARY_ENABLED, HEALTH_CANARY_INTERVAL_SECONDS as interval

    if not HEALTH_CANARY_ENABLED:
        logger.info("STORY-316: Health canary disabled")
        return asyncio.create_task(asyncio.sleep(0), name="health_canary_noop")

    task = asyncio.create_task(
        cron_loop("STORY-316 canary", run_health_canary, interval, initial_delay=30, error_retry_seconds=60),
        name="health_canary",
    )
    logger.info("STORY-316: Health canary task started (interval: 5m)")
    return task
