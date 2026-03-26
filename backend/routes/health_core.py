"""Core health endpoints — liveness, readiness, comprehensive health, sources.

DEBT-015 SYS-005: Extracted from main.py to reduce its line count.
Mounted at root level (not /v1/) for container probe compatibility.
"""

import asyncio
import logging
import os
import time

from fastapi import APIRouter, Response

import startup.state as _state

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health-core"])

# HARDEN-016 AC3: Individual dependency timeouts
_READINESS_REDIS_TIMEOUT_S = 2.0
_READINESS_SUPABASE_TIMEOUT_S = 3.0


@router.get("/health/live")
async def health_live():
    """HARDEN-016 AC1: Pure liveness probe — ALWAYS returns 200."""
    is_ready = _state.startup_time is not None
    uptime = round(time.monotonic() - _state.startup_time, 3) if is_ready else 0.0
    process_uptime = round(time.monotonic() - _state.process_start_time, 3)
    return {
        "live": True,
        "ready": is_ready,
        "uptime_seconds": uptime,
        "process_uptime_seconds": process_uptime,
    }


@router.get("/health/ready")
async def health_ready(response: Response):
    """HARDEN-016 AC2: Readiness probe — checks Redis + Supabase.

    DEBT-124 AC6: Returns 503 during graceful shutdown drain phase.
    """
    # DEBT-124 AC6: Health returns 503 during drain so LB stops sending new requests
    if _state.shutting_down:
        response.status_code = 503
        return {"ready": False, "checks": {}, "uptime_seconds": 0.0, "shutting_down": True}

    checks: dict[str, dict] = {}
    all_ok = True

    # Redis check
    redis_start = time.monotonic()
    try:
        from redis_pool import get_redis_pool
        redis = await asyncio.wait_for(get_redis_pool(), timeout=_READINESS_REDIS_TIMEOUT_S)
        if redis:
            await asyncio.wait_for(redis.ping(), timeout=_READINESS_REDIS_TIMEOUT_S)
            checks["redis"] = {"status": "up", "latency_ms": round((time.monotonic() - redis_start) * 1000)}
        else:
            checks["redis"] = {"status": "down", "error": "pool unavailable"}
            all_ok = False
    except asyncio.TimeoutError:
        checks["redis"] = {"status": "down", "error": "timeout", "latency_ms": round((time.monotonic() - redis_start) * 1000)}
        all_ok = False
    except Exception as e:
        checks["redis"] = {"status": "down", "error": str(e)[:100], "latency_ms": round((time.monotonic() - redis_start) * 1000)}
        all_ok = False

    # Supabase check
    sb_start = time.monotonic()
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        await asyncio.wait_for(sb_execute(sb.table("profiles").select("id").limit(1)), timeout=_READINESS_SUPABASE_TIMEOUT_S)
        checks["supabase"] = {"status": "up", "latency_ms": round((time.monotonic() - sb_start) * 1000)}
    except asyncio.TimeoutError:
        checks["supabase"] = {"status": "down", "error": "timeout", "latency_ms": round((time.monotonic() - sb_start) * 1000)}
        all_ok = False
    except Exception as e:
        checks["supabase"] = {"status": "down", "error": str(e)[:100], "latency_ms": round((time.monotonic() - sb_start) * 1000)}
        all_ok = False

    is_ready = _state.startup_time is not None and all_ok
    uptime = round(time.monotonic() - _state.startup_time, 3) if _state.startup_time else 0.0

    if not is_ready:
        response.status_code = 503

    return {"ready": is_ready, "checks": checks, "uptime_seconds": uptime}


@router.get("/health")
async def health():
    """Comprehensive health check with dependency status, circuit breakers, bulkheads."""
    from datetime import datetime, timezone

    dependencies = {"supabase": "unconfigured", "openai": "unconfigured", "redis": "unconfigured"}

    # Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase_client import get_supabase
            get_supabase()
            dependencies["supabase"] = "healthy"
        except Exception as e:
            dependencies["supabase"] = f"error: {str(e)[:50]}"
    else:
        dependencies["supabase"] = "missing_env_vars"

    # OpenAI
    dependencies["openai"] = "configured" if os.getenv("OPENAI_API_KEY") else "missing_api_key"

    # Redis
    redis_url = os.getenv("REDIS_URL")
    redis_metrics = None
    if redis_url:
        try:
            from redis_pool import get_redis_pool, is_redis_available
            import time as _time
            redis_available = await is_redis_available()
            dependencies["redis"] = "healthy" if redis_available else "unavailable"

            if redis_available:
                pool = await get_redis_pool()
                t0 = _time.monotonic()
                await pool.ping()
                latency_ms = round((_time.monotonic() - t0) * 1000, 2)
                memory_mb = None
                try:
                    info = await pool.info("memory")
                    used_bytes = info.get("used_memory", 0)
                    memory_mb = round(used_bytes / (1024 * 1024), 2)
                except Exception:
                    pass
                redis_metrics = {"connected": True, "latency_ms": latency_ms, "memory_used_mb": memory_mb}
            else:
                redis_metrics = {"connected": False, "latency_ms": None, "memory_used_mb": None}
        except Exception as e:
            dependencies["redis"] = f"error: {str(e)[:50]}"
            redis_metrics = {"connected": False, "latency_ms": None, "memory_used_mb": None}
    else:
        dependencies["redis"] = "not_configured"

    # Source health
    from source_config.sources import source_health_registry
    from pncp_client import get_circuit_breaker

    sources = {}
    for source_name in ["PNCP", "Portal Transparência", "Licitar Digital", "ComprasGov", "BLL", "BNC"]:
        sources[source_name] = source_health_registry.get_status(source_name)

    # Circuit breakers
    pncp_cb = get_circuit_breaker("pncp")
    pcp_cb = get_circuit_breaker("pcp")
    comprasgov_cb = get_circuit_breaker("comprasgov")
    if hasattr(pncp_cb, "get_state"):
        sources["PNCP_circuit_breaker"] = await pncp_cb.get_state()
        sources["PCP_circuit_breaker"] = await pcp_cb.get_state()
        sources["COMPRASGOV_circuit_breaker"] = await comprasgov_cb.get_state()
    else:
        for cb_name, cb in [("PNCP", pncp_cb), ("PCP", pcp_cb), ("COMPRASGOV", comprasgov_cb)]:
            sources[f"{cb_name}_circuit_breaker"] = {
                "status": "degraded" if cb.is_degraded else "healthy",
                "failures": cb.consecutive_failures,
                "degraded": cb.is_degraded,
                "backend": "local",
            }

    # Rate limiter
    from rate_limiter import pncp_rate_limiter, pcp_rate_limiter
    sources["rate_limiter"] = {
        "pncp": await pncp_rate_limiter.get_stats(),
        "pcp": await pcp_rate_limiter.get_stats(),
    }

    # Overall status
    supabase_ok = not dependencies["supabase"].startswith("error")
    redis_degraded = dependencies["redis"].startswith("error") or dependencies["redis"] == "unavailable"
    if not supabase_ok:
        status = "unhealthy"
    elif redis_degraded and redis_url:
        status = "degraded"
    else:
        status = "healthy"

    if redis_metrics:
        dependencies["redis_metrics"] = redis_metrics

    # ARQ queue health
    try:
        from job_queue import get_queue_health
        dependencies["queue"] = await get_queue_health()
    except Exception:
        dependencies["queue"] = "unavailable"

    # Tracing
    from telemetry import is_tracing_enabled
    dependencies["tracing"] = "enabled" if is_tracing_enabled() else "disabled"

    is_ready = _state.startup_time is not None
    uptime = round(time.monotonic() - _state.startup_time, 3) if is_ready else 0.0

    # Bulkheads
    from bulkhead import get_all_bulkheads
    bulkhead_status = {bh_name: bh.to_dict() for bh_name, bh in get_all_bulkheads().items()}

    return {
        "status": status,
        "ready": is_ready,
        "uptime_seconds": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": os.getenv("APP_VERSION", "dev"),
        "dependencies": dependencies,
        "sources": sources,
        "bulkheads": bulkhead_status,
    }


@router.get("/sources/health")
async def sources_health():
    """Health check for all configured procurement data sources."""
    from datetime import datetime, timezone

    enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
    from source_config.sources import get_source_config
    source_config = get_source_config()

    sources_info = []

    if source_config.pncp.enabled:
        sources_info.append({"code": "PNCP", "name": source_config.pncp.name, "enabled": True, "priority": source_config.pncp.priority})

    if source_config.compras_gov.enabled:
        from config import COMPRASGOV_ENABLED as _cg_enabled
        sources_info.append({"code": "COMPRAS_GOV", "name": source_config.compras_gov.name, "enabled": _cg_enabled, "priority": source_config.compras_gov.priority})

    if source_config.portal.enabled:
        sources_info.append({"code": "PORTAL_COMPRAS", "name": source_config.portal.name, "enabled": True, "priority": source_config.portal.priority})

    if enable_multi_source:
        from consolidation import ConsolidationService
        from clients.compras_gov_client import ComprasGovAdapter
        from clients.portal_compras_client import PortalComprasAdapter

        adapters = {}
        if source_config.compras_gov.enabled:
            from config import COMPRASGOV_ENABLED as _cg_on
            if _cg_on:
                adapters["COMPRAS_GOV"] = ComprasGovAdapter(timeout=source_config.compras_gov.timeout)
        if source_config.portal.enabled:
            from source_config.sources import source_health_registry as _hr
            if _hr.is_available("PORTAL_COMPRAS"):
                adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(timeout=source_config.portal.timeout)
            else:
                logger.info("[HEALTH] PCP v2 source is DOWN — excluded from health check")

        if adapters:
            svc = ConsolidationService(adapters=adapters)
            health_results = await svc.health_check_all()
            await svc.close()
            for info in sources_info:
                code = info["code"]
                if code in health_results:
                    info["status"] = health_results[code]["status"]
                    info["response_ms"] = health_results[code]["response_ms"]
                elif code == "PNCP":
                    info["status"] = "available"
                    info["response_ms"] = 0
                else:
                    info["status"] = "unknown"
                    info["response_ms"] = 0
        else:
            for info in sources_info:
                info["status"] = "available" if info["code"] == "PNCP" else "unknown"
                info["response_ms"] = 0
    else:
        for info in sources_info:
            info["status"] = "available" if info["code"] == "PNCP" else "disabled"
            info["response_ms"] = 0

    total_enabled = len([s for s in sources_info if s["enabled"]])
    total_available = len([s for s in sources_info if s.get("status") == "available"])

    return {
        "sources": sources_info,
        "multi_source_enabled": enable_multi_source,
        "total_enabled": total_enabled,
        "total_available": total_available,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
