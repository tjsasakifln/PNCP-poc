"""Application lifespan context manager — startup and shutdown orchestration."""

import asyncio
import logging
import os
import signal
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI

import startup.state as _state

logger = logging.getLogger(__name__)


async def _check_cache_schema() -> None:
    """CRIT-001 AC4: Validate search_results_cache schema on startup."""
    try:
        from models.cache import SearchResultsCacheRow
        from supabase_client import get_supabase

        db = get_supabase()
        try:
            result = db.rpc(
                "get_table_columns_simple",
                {"p_table_name": "search_results_cache"},
            ).execute()
            actual_columns = {row["column_name"] for row in result.data} if result.data else set()
        except Exception as rpc_err:
            logger.warning(f"CRIT-004: RPC get_table_columns_simple failed ({rpc_err}) — trying direct query")
            try:
                db.table("search_results_cache").select("*").limit(0).execute()
                logger.info("CRIT-004: Table search_results_cache exists (column validation skipped)")
                return
            except Exception as fallback_err:
                logger.warning(f"CRIT-004: Schema validation FAILED — RPC: {rpc_err}, Fallback: {fallback_err}")
                return

        expected_columns = SearchResultsCacheRow.expected_columns()
        missing = expected_columns - actual_columns
        extra = actual_columns - expected_columns

        if missing:
            logger.critical(f"CRIT-001: search_results_cache MISSING columns: {sorted(missing)}. Run migration 033_fix_missing_cache_columns.sql")
        if extra:
            logger.warning(f"CRIT-001: search_results_cache has EXTRA columns not in model: {sorted(extra)}")
        if not missing and not extra:
            logger.info(f"CRIT-001: Schema validation passed for search_results_cache ({len(expected_columns)} columns)")
    except Exception as e:
        logger.warning(f"CRIT-001: Schema health check failed (non-fatal): {type(e).__name__}: {e}")


def _log_registered_routes(app_instance: FastAPI) -> None:
    """Diagnostic logging for route registration."""
    logger.info("=" * 60)
    logger.info("REGISTERED ROUTES:")
    logger.info("=" * 60)
    for route in app_instance.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            logger.info(f"  {methods:8s} {route.path}")
    logger.info("=" * 60)

    export_routes = [r for r in app_instance.routes if hasattr(r, 'path') and '/export' in r.path]
    if export_routes:
        logger.info(f"Export routes found: {len(export_routes)}")
        for r in export_routes:
            methods = ','.join(r.methods) if hasattr(r, 'methods') and r.methods else 'N/A'
            logger.info(f"   {methods:8s} {r.path}")
    else:
        logger.error("NO EXPORT ROUTES FOUND - /api/export/google-sheets will return 404!")
    logger.info("=" * 60)


async def _mark_inflight_sessions_timed_out() -> None:
    """CRIT-002 AC15: Mark in-flight sessions as timed_out on shutdown."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        async def _do_update():
            from datetime import datetime, timezone
            result = (
                sb.table("search_sessions")
                .update({
                    "status": "timed_out",
                    "error_message": "O servidor foi reiniciado. Tente novamente.",
                    "error_code": "timeout",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                .in_("status", ["created", "processing"])
                .execute()
            )
            n = len(result.data) if result.data else 0
            if n > 0:
                logger.critical(f"CRIT-002 AC15: Marked {n} in-flight sessions as timed_out due to shutdown")
            else:
                logger.info("CRIT-002 AC15: No in-flight sessions to mark on shutdown")

        await asyncio.wait_for(_do_update(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("CRIT-002 AC15: Timeout marking in-flight sessions (5s limit)")
    except Exception as e:
        logger.error(f"CRIT-002 AC15: Failed to mark in-flight sessions: {e}")


_SATURATION_INTERVAL = 30


async def _periodic_saturation_metrics() -> None:
    """HARDEN-024 AC6: Report pool/queue saturation metrics every 30s."""
    from metrics import (
        REDIS_POOL_CONNECTIONS_USED, REDIS_POOL_CONNECTIONS_MAX,
        HTTPX_POOL_CONNECTIONS_USED, TRACKER_ACTIVE_COUNT,
        BACKGROUND_RESULTS_COUNT,
    )
    from redis_pool import get_pool_stats
    from progress import get_active_tracker_count
    from routes.search import get_background_results_count
    from config import (
        PNCP_BULKHEAD_CONCURRENCY, PCP_BULKHEAD_CONCURRENCY,
        COMPRASGOV_BULKHEAD_CONCURRENCY,
    )

    while True:
        try:
            await asyncio.sleep(_SATURATION_INTERVAL)
            stats = get_pool_stats()
            REDIS_POOL_CONNECTIONS_USED.set(stats["used"])
            REDIS_POOL_CONNECTIONS_MAX.set(stats["max"])
            HTTPX_POOL_CONNECTIONS_USED.labels(source="pncp").set(PNCP_BULKHEAD_CONCURRENCY + 2)
            HTTPX_POOL_CONNECTIONS_USED.labels(source="pcp").set(PCP_BULKHEAD_CONCURRENCY + 2)
            HTTPX_POOL_CONNECTIONS_USED.labels(source="comprasgov").set(COMPRASGOV_BULKHEAD_CONCURRENCY + 2)
            TRACKER_ACTIVE_COUNT.set(get_active_tracker_count())
            BACKGROUND_RESULTS_COUNT.set(get_background_results_count())
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning("HARDEN-024: Saturation metrics error: %s", e)


def _check_async_multiworker_mismatch() -> None:
    """CRIT-SYNC-FIX: Warn if async search is enabled with multiple workers.

    Async mode uses an in-memory progress tracker that is not shared across
    Gunicorn workers. When WEB_CONCURRENCY > 1 the POST and SSE requests may
    hit different workers, causing the tracker-mismatch bug.
    """
    from config.pipeline import ASYNC_SEARCH_DEFAULT, SEARCH_ASYNC_ENABLED

    web_concurrency = int(os.getenv("WEB_CONCURRENCY", "1"))
    async_enabled = ASYNC_SEARCH_DEFAULT or SEARCH_ASYNC_ENABLED

    if async_enabled and web_concurrency > 1:
        logger.critical(
            "CRIT-SYNC-FIX: ASYNC_SEARCH_DEFAULT=%s and WEB_CONCURRENCY=%d — "
            "this combination causes in-memory tracker mismatch across workers. "
            "Set ASYNC_SEARCH_DEFAULT=false or WEB_CONCURRENCY=1 to avoid broken SSE progress.",
            ASYNC_SEARCH_DEFAULT, web_concurrency,
        )


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan context manager — startup and shutdown."""
    from config import validate_env_vars
    from telemetry import shutdown_tracing
    from redis_pool import startup_redis, shutdown_redis

    # === STARTUP ===
    validate_env_vars()

    # CRIT-SYNC-FIX: Detect dangerous async + multi-worker combination
    _check_async_multiworker_mismatch()

    # DEBT-008: Memory baseline
    from health import get_memory_usage, update_memory_metrics
    mem = get_memory_usage()
    logger.info("DEBT-008: Startup memory — RSS=%.1fMB, VMS=%.1fMB, Peak=%.1fMB",
                mem["rss_mb"], mem["vms_mb"], mem["peak_rss_mb"])
    update_memory_metrics()

    # Thread pool for asyncio.to_thread()
    import concurrent.futures
    _thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=20, thread_name_prefix="smartlic-io-")
    asyncio.get_event_loop().set_default_executor(_thread_pool)
    logger.info("STORY-290-patch: thread pool executor configured (max_workers=20)")

    await startup_redis()

    from bulkhead import initialize_bulkheads
    initialize_bulkheads()

    from job_queue import get_arq_pool
    await get_arq_pool()

    # DEBT-014 SYS-006: Register background tasks
    from task_registry import task_registry
    from cron_jobs import (
        start_cache_cleanup_task, start_session_cleanup_task,
        start_cache_refresh_task, warmup_top_params, start_warmup_task,
        start_trial_sequence_task, start_reconciliation_task,
        start_health_canary_task, start_revenue_share_task,
        start_sector_stats_task, start_support_sla_task,
        start_daily_volume_task, start_results_cleanup_task,
        start_stripe_events_purge_task, start_plan_reconciliation_task,
        start_coverage_check_task, start_trial_risk_task,
        start_indice_municipal_task,  # STORY-435 AC7
    )
    from progress import _periodic_tracker_cleanup

    task_registry.register("cache_cleanup", start_cache_cleanup_task)
    task_registry.register("session_cleanup", start_session_cleanup_task)
    task_registry.register("cache_refresh", start_cache_refresh_task)
    task_registry.register("trial_sequence", start_trial_sequence_task)
    task_registry.register("reconciliation", start_reconciliation_task)
    task_registry.register("health_canary", start_health_canary_task)
    task_registry.register("revenue_share", start_revenue_share_task)
    task_registry.register("sector_stats", start_sector_stats_task)
    task_registry.register("support_sla", start_support_sla_task)
    task_registry.register("daily_volume", start_daily_volume_task)
    task_registry.register("results_cleanup", start_results_cleanup_task)
    task_registry.register("stripe_purge", start_stripe_events_purge_task)
    task_registry.register("plan_reconciliation", start_plan_reconciliation_task)
    task_registry.register("tracker_cleanup", _periodic_tracker_cleanup, is_coroutine=True)
    task_registry.register("saturation_metrics", _periodic_saturation_metrics, is_coroutine=True)
    task_registry.register("warmup", start_warmup_task)
    task_registry.register("coverage_check", start_coverage_check_task)
    task_registry.register("trial_risk", start_trial_risk_task)
    task_registry.register("indice_municipal_quarterly", start_indice_municipal_task)

    await task_registry.start_all()

    try:
        from metrics import TASK_REGISTRY_TOTAL, TASK_REGISTRY_HEALTHY
        health = task_registry.get_health()
        TASK_REGISTRY_TOTAL.set(health["total"])
        TASK_REGISTRY_HEALTHY.set(health["healthy"])
    except Exception:
        pass

    await _check_cache_schema()

    # Initialize circuit breakers from Redis
    from pncp_client import get_circuit_breaker
    pncp_cb = get_circuit_breaker("pncp")
    pcp_cb = get_circuit_breaker("pcp")
    comprasgov_cb = get_circuit_breaker("comprasgov")
    await pncp_cb.initialize()
    await pcp_cb.initialize()
    await comprasgov_cb.initialize()
    logger.info("GTM-CRIT-005: Circuit breakers initialized from Redis (pncp, pcp, comprasgov)")

    # Schema contract validation — STORY-414 strict-mode gate.
    # When SCHEMA_CONTRACT_STRICT=true, a contract violation raises
    # SchemaContractViolation which we re-raise here to abort startup;
    # Gunicorn + Railway treat the RuntimeError as a failed boot and
    # trigger a redeploy/rollback instead of serving broken traffic.
    # When false (default), we log CRITICAL and proceed degraded — the
    # pre-STORY-414 behaviour, kept during the 14d rollout window.
    from schemas.contract import enforce_schema_contract, SchemaContractViolation
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        try:
            enforce_schema_contract(db)
        except SchemaContractViolation:
            logger.critical(
                "STORY-414: Aborting startup because SCHEMA_CONTRACT_STRICT=true "
                "and the contract is violated. Apply migrations before re-deploying."
            )
            raise
    except SchemaContractViolation:
        raise
    except Exception as e:
        logger.warning(f"CRIT-004: Schema validation could not run ({e}) — proceeding with caution")

    # Recover stale searches
    from search_state_manager import recover_stale_searches
    await recover_stale_searches(max_age_minutes=10)

    _log_registered_routes(app_instance)

    # Supabase connectivity probe
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        db.table("profiles").select("id").limit(1).execute()
        logger.info("STARTUP GATE: Supabase connectivity confirmed")
    except Exception as e:
        logger.critical(f"STARTUP GATE: Supabase unreachable — {e}. SERVICE DEGRADED but staying alive.")

    # Redis connectivity check
    if os.getenv("REDIS_URL"):
        from redis_pool import is_redis_available
        if await is_redis_available():
            logger.info("STARTUP GATE: Redis connectivity confirmed")
        else:
            logger.warning("STARTUP GATE: Redis configured but unavailable — proceeding without Redis")

    _redis_status = "not configured"
    if os.getenv("REDIS_URL"):
        from redis_pool import is_redis_available
        _redis_status = "OK" if await is_redis_available() else "unavailable"
    logger.info("STARTUP GATE: Redis %s — setting ready=true", _redis_status)

    _state.startup_time = time.monotonic()

    try:
        warmup_result = await warmup_top_params()
        logger.info(f"GTM-ARCH-002: Post-deploy warmup complete: {warmup_result}")
    except Exception as e:
        logger.warning(f"GTM-ARCH-002: Post-deploy warmup failed (non-fatal): {e}")

    logger.info("APPLICATION READY — all routes registered, accepting traffic")

    def _sigterm_handler(signum, frame):
        logger.info("SIGTERM received — starting graceful shutdown")
        # DEBT-124 AC1: Set shutting_down flag immediately on SIGTERM
        _state.shutting_down = True

    signal.signal(signal.SIGTERM, _sigterm_handler)

    yield

    # === SHUTDOWN ===
    from config import GRACEFUL_SHUTDOWN_TIMEOUT
    logger.info("DEBT-124: Graceful shutdown initiated (drain_timeout=%ds)", GRACEFUL_SHUTDOWN_TIMEOUT)

    # DEBT-124 AC1: Set flag (also set by SIGTERM handler, but ensure it's set for lifespan shutdown)
    _state.shutting_down = True

    # DEBT-124 AC5: Emit shutdown event to all active SSE connections
    from progress import _active_trackers
    if _active_trackers:
        logger.info("DEBT-124 AC5: Emitting shutdown event to %d active SSE connections", len(_active_trackers))
        for sid, tracker in list(_active_trackers.items()):
            try:
                await tracker.emit(
                    stage="shutdown",
                    progress=-1,
                    message="Servidor em manutenção. Sua busca será retomada automaticamente.",
                )
            except Exception as e:
                logger.debug("DEBT-124: Failed to emit shutdown to tracker %s: %s", sid, e)

    # DEBT-124 AC2+AC3: Wait for in-flight requests to complete (up to drain timeout)
    from routes.search import _active_background_tasks
    if _active_background_tasks:
        bg_count = len(_active_background_tasks)
        drain_timeout = min(GRACEFUL_SHUTDOWN_TIMEOUT, 30)
        logger.info("DEBT-124 AC2: Draining %d in-flight searches (timeout=%ds)", bg_count, drain_timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*_active_background_tasks.values(), return_exceptions=True),
                timeout=drain_timeout,
            )
            logger.info("DEBT-124: All %d background tasks drained successfully", bg_count)
        except asyncio.TimeoutError:
            logger.warning("DEBT-124 AC2: Drain timeout after %ds — cancelling remaining %d tasks",
                           drain_timeout, sum(1 for t in _active_background_tasks.values() if not t.done()))
            for sid, task in _active_background_tasks.items():
                if not task.done():
                    task.cancel()
            # Brief wait for cancellation to propagate
            await asyncio.gather(*_active_background_tasks.values(), return_exceptions=True)
        _active_background_tasks.clear()
    else:
        logger.info("DEBT-124: No active background tasks to drain")

    await _mark_inflight_sessions_timed_out()

    from task_registry import task_registry
    stop_results = await task_registry.stop_all(timeout=10.0)
    logger.info("DEBT-124: TaskRegistry stopped %d tasks: %s",
                len(stop_results), {k: v for k, v in stop_results.items() if v != "cancelled"})

    from job_queue import close_arq_pool
    await close_arq_pool()

    shutdown_tracing()

    _thread_pool.shutdown(wait=False)
    logger.info("STORY-290-patch: thread pool executor shut down")

    await shutdown_redis()

    logger.info("DEBT-124: Graceful shutdown complete")
