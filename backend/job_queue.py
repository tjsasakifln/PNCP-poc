"""ARQ job queue for background LLM + Excel processing.

GTM-RESILIENCE-F01: Decouples LLM summary and Excel generation from the HTTP
request cycle. After stage 5 (filtering), the pipeline enqueues background jobs
and returns results immediately. LLM and Excel arrive via SSE events.

Architecture:
    Web process:  get_arq_pool() → enqueue_job("llm_summary_job", ...)
    Worker process:  arq backend.job_queue.WorkerSettings
    Communication:  SSE events via ProgressTracker (Redis pub/sub or in-memory)

Fallback:
    If Redis/ARQ unavailable, is_queue_available() returns False and the pipeline
    executes LLM/Excel inline (zero regression vs current behavior).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Singleton pool
_arq_pool = None
_pool_lock = asyncio.Lock()

# CRIT-033: Worker liveness cache (monotonic_time, is_alive)
_worker_alive_cache: tuple[float, bool] = (0.0, False)
_WORKER_CHECK_INTERVAL = 15  # GTM-STAB-002 AC4: faster failover detection


def _get_redis_settings():
    """Build ARQ RedisSettings from REDIS_URL env var.

    CRIT-038: Hardened with retry_on_timeout + retry_on_error to prevent
    worker crash on transient Redis failures during finish_job().
    Previously only conn_timeout/conn_retries were set (initial connection only),
    leaving the worker unprotected against operational timeouts.

    Returns:
        arq.connections.RedisSettings configured from environment.

    Raises:
        ValueError: If REDIS_URL is not set.
    """
    from arq.connections import RedisSettings

    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        raise ValueError("REDIS_URL not set — ARQ worker cannot start without Redis")

    parsed = urlparse(redis_url)
    ssl = parsed.scheme == "rediss"
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
        conn_timeout=10,
        conn_retries=5,
        conn_retry_delay=2.0,
        ssl=ssl,
        # CRIT-038: Prevent worker crash on Redis timeout during finish_job()
        retry_on_timeout=True,
        retry_on_error=[TimeoutError, ConnectionError, OSError],
        max_connections=50,
    )


async def get_arq_pool():
    """Get or create the ARQ connection pool (singleton).

    GTM-STAB-002 AC2: Retry with exponential backoff on connection failure.
    """
    global _arq_pool

    if _arq_pool is not None:
        try:
            await _arq_pool.ping()
            return _arq_pool
        except Exception:
            _arq_pool = None

    async with _pool_lock:
        if _arq_pool is not None:
            return _arq_pool

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                from arq import create_pool
                settings = _get_redis_settings()
                _arq_pool = await create_pool(settings)
                logger.info(f"ARQ connection pool created (attempt {attempt})")
                return _arq_pool
            except Exception as e:
                delay = 2 ** attempt
                logger.warning(
                    f"redis_pool_reconnect attempt={attempt}/{max_attempts} "
                    f"delay={delay}s error={type(e).__name__}: {e}"
                )
                if attempt < max_attempts:
                    await asyncio.sleep(delay)

        logger.warning("ARQ pool creation failed after all retries")
        return None


async def close_arq_pool() -> None:
    """Close the ARQ pool gracefully (called at shutdown)."""
    global _arq_pool
    if _arq_pool is not None:
        try:
            await _arq_pool.close()
        except Exception as e:
            logger.warning(f"Error closing ARQ pool: {e}")
        _arq_pool = None
        logger.info("ARQ pool closed")


async def _check_worker_alive(pool) -> bool:
    """CRIT-033: Check if any ARQ worker is actively running.

    ARQ workers periodically write a health-check key to Redis
    (default: ``arq:queue:health-check``, TTL = 2× health_check_interval).
    If this key is absent, no worker is consuming jobs and queue mode
    should NOT be used.

    Result is cached for ``_WORKER_CHECK_INTERVAL`` seconds to avoid
    a Redis round-trip on every search.
    """
    global _worker_alive_cache

    now = time.monotonic()
    last_check, last_result = _worker_alive_cache
    if now - last_check < _WORKER_CHECK_INTERVAL:
        return last_result

    try:
        # ARQ default queue_name is "arq:queue", health-check key = "<queue>:health-check"
        alive = bool(await pool.exists("arq:queue:health-check"))
        _worker_alive_cache = (now, alive)
        if not alive:
            logger.info(
                "CRIT-033: No active ARQ worker detected (arq:queue:health-check absent) "
                "— pipeline will use inline mode"
            )
        return alive
    except Exception as e:
        logger.debug(f"CRIT-033: Worker health check failed: {e}")
        _worker_alive_cache = (now, False)
        return False


async def is_queue_available() -> bool:
    """Check if the job queue is healthy and ready to accept work.

    Used by the pipeline to decide between queue mode and inline mode.

    CRIT-033: Now also verifies that at least one ARQ worker is alive
    (via Redis health-check key) — prevents entering queue mode when
    no worker is consuming jobs.
    """
    pool = await get_arq_pool()
    if pool is None:
        return False
    try:
        await pool.ping()
    except Exception:
        return False

    # CRIT-033: Redis is up, but is a worker actually running?
    return await _check_worker_alive(pool)


async def enqueue_job(
    function_name: str,
    *args: Any,
    _job_id: Optional[str] = None,
    **kwargs: Any,
):
    """Enqueue a job to the ARQ worker.

    Args:
        function_name: Name of the registered job function.
        *args: Positional arguments for the job.
        _job_id: Optional custom job ID (for deduplication).
        **kwargs: Keyword arguments for the job.

    Returns:
        arq.jobs.Job instance if enqueued, None if queue unavailable.
    """
    pool = await get_arq_pool()
    if pool is None:
        logger.warning(f"Queue unavailable — cannot enqueue {function_name}")
        return None

    # F-02 AC18: Propagate trace context to background jobs
    try:
        from telemetry import get_trace_id, get_span_id
        trace_id = get_trace_id()
        span_id = get_span_id()
        if trace_id:
            kwargs["_trace_id"] = trace_id
            kwargs["_span_id"] = span_id
    except Exception:
        pass

    try:
        job = await pool.enqueue_job(
            function_name,
            *args,
            _job_id=_job_id,
            **kwargs,
        )
        # CRIT-033: ARQ returns None when a job with the same _job_id
        # already exists (dedup) or when the queue is in an invalid state.
        if job is None:
            logger.warning(
                f"CRIT-033: pool.enqueue_job returned None for {function_name} "
                f"(job_id={_job_id}) — job may already exist or worker unavailable"
            )
            return None
        logger.info(f"Enqueued job: {function_name} (id={job.job_id})")
        return job
    except Exception as e:
        logger.warning(f"Failed to enqueue {function_name}: {e}")
        return None


async def get_queue_health() -> str:
    """Check queue health for /v1/health endpoint.

    Returns:
        "healthy" if ARQ pool responsive, "unavailable" otherwise.
    """
    available = await is_queue_available()
    return "healthy" if available else "unavailable"


# ==========================================================================
# STORY-281 AC2: Search Job Cancellation via Redis Flag
# ==========================================================================

_CANCEL_KEY_PREFIX = "smartlic:search_cancel:"
_CANCEL_TTL = 600  # 10 minutes — safety net for stale flags


async def set_cancel_flag(search_id: str) -> bool:
    """STORY-281 AC2: Signal worker to stop processing a search.

    Called by the inline fallback watchdog when it takes over execution.
    The worker checks this flag periodically and aborts if set.

    Args:
        search_id: The search UUID to cancel.

    Returns:
        True if flag was set successfully, False if Redis unavailable.
    """
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        logger.debug(f"STORY-281: Cannot set cancel flag for {search_id} — Redis unavailable")
        return False

    try:
        key = f"{_CANCEL_KEY_PREFIX}{search_id}"
        await redis.set(key, "1", ex=_CANCEL_TTL)
        logger.info(f"STORY-281: Cancel flag SET for search_id={search_id}")
        return True
    except Exception as e:
        logger.warning(f"STORY-281: Failed to set cancel flag for {search_id}: {e}")
        return False


async def check_cancel_flag(search_id: str) -> bool:
    """STORY-281 AC2: Check if a search has been cancelled.

    Called by search_job worker periodically (after each source fetch).

    Args:
        search_id: The search UUID to check.

    Returns:
        True if the search should be cancelled, False otherwise.
    """
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return False

    try:
        key = f"{_CANCEL_KEY_PREFIX}{search_id}"
        result = await redis.get(key)
        if result:
            logger.info(f"STORY-281: Cancel flag DETECTED for search_id={search_id} — aborting worker")
        return result is not None
    except Exception:
        return False


async def clear_cancel_flag(search_id: str) -> None:
    """STORY-281 AC2: Clean up cancel flag after processing completes."""
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return

    try:
        key = f"{_CANCEL_KEY_PREFIX}{search_id}"
        await redis.delete(key)
    except Exception:
        pass


# ==========================================================================
# Job Result Persistence (Redis-backed, 1h TTL)
# ==========================================================================

async def persist_job_result(search_id: str, field: str, value: Any) -> None:
    """Persist a job result to Redis for later retrieval.

    Used when SSE connection drops — frontend can poll for results.

    Args:
        search_id: The search UUID.
        field: Result field name (e.g., "resumo_json", "excel_url").
        value: The result data (will be JSON-serialized if not a string).
    """
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return

    try:
        key = f"smartlic:job_result:{search_id}:{field}"
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await redis.set(key, serialized, ex=3600)  # 1 hour TTL
    except Exception as e:
        logger.warning(f"Failed to persist job result {field} for {search_id}: {e}")


async def get_job_result(search_id: str, field: str) -> Optional[Any]:
    """Retrieve a persisted job result from Redis.

    Args:
        search_id: The search UUID.
        field: Result field name.

    Returns:
        Deserialized result data, or None if not found.
    """
    from redis_pool import get_redis_pool
    redis = await get_redis_pool()
    if redis is None:
        return None

    try:
        key = f"smartlic:job_result:{search_id}:{field}"
        raw = await redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw
    except Exception as e:
        logger.warning(f"Failed to get job result {field} for {search_id}: {e}")
        return None


# ==========================================================================
# Job Functions (Track 2 + Track 3)
# ==========================================================================

async def llm_summary_job(ctx: dict, search_id: str, licitacoes: list, sector_name: str, termos_busca: str | None = None, **kwargs) -> dict:
    """Background job: Generate LLM summary and notify via SSE.

    AC7: Registered in WorkerSettings.
    AC8: Executes gerar_resumo() with fallback to gerar_resumo_fallback().
    AC9: Result persisted in Redis (keyed by search_id).
    AC10: After max_tries exhausted, ARQ persists fallback (never None).
    AC11: Timeout enforced by ARQ job_timeout setting (30s).
    """
    # CRIT-004 AC16-AC17: Restore trace context from parent span
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from llm import gerar_resumo, gerar_resumo_fallback
    from progress import get_tracker

    logger.info(f"[LLM Job] search_id={search_id}, bids={len(licitacoes)}, sector={sector_name}")

    try:
        resumo = gerar_resumo(licitacoes, sector_name=sector_name, termos_busca=termos_busca)
        logger.info(f"[LLM Job] AI summary generated for {search_id}")
    except Exception as e:
        logger.warning(f"[LLM Job] LLM failed ({type(e).__name__}), using fallback: {e}")
        resumo = gerar_resumo_fallback(licitacoes, sector_name=sector_name, termos_busca=termos_busca)

    # Override LLM counts with actuals
    resumo.total_oportunidades = len(licitacoes)
    resumo.valor_total = sum(lic.get("valorTotalEstimado", 0) or 0 for lic in licitacoes)

    result_data = resumo.model_dump()

    # Persist result
    await persist_job_result(search_id, "resumo_json", result_data)

    # AC19: Emit SSE event
    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit(
            "llm_ready", 85,
            "Resumo pronto",
            resumo=result_data,
        )

    return result_data


async def excel_generation_job(
    ctx: dict,
    search_id: str,
    licitacoes: list,
    allow_excel: bool,
    **kwargs,
) -> dict:
    """Background job: Generate Excel report and upload to storage.

    AC12: Registered in WorkerSettings.
    AC13: Executes create_excel() + upload_excel().
    AC14: Signed URL persisted in Redis.
    AC15: On failure after retries, returns excel_status="failed".
    AC16: Timeout enforced by ARQ job_timeout setting (60s).
    """
    # CRIT-004 AC16-AC17: Restore trace context from parent span
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from excel import create_excel
    from storage import upload_excel
    from progress import get_tracker

    logger.info(f"[Excel Job] search_id={search_id}, bids={len(licitacoes)}, allow={allow_excel}")

    if not allow_excel:
        result = {"excel_status": "skipped", "download_url": None}
        await persist_job_result(search_id, "excel_result", result)
        return result

    download_url = None
    try:
        excel_buffer = create_excel(licitacoes)
        excel_bytes = excel_buffer.read()

        storage_result = upload_excel(excel_bytes, search_id)

        if storage_result:
            download_url = storage_result["signed_url"]
            logger.info(f"[Excel Job] Uploaded: {storage_result['file_path']}")
        else:
            logger.error("[Excel Job] Storage upload returned None")
    except Exception as e:
        logger.error(f"[Excel Job] Generation/upload failed: {e}", exc_info=True)

    excel_status = "ready" if download_url else "failed"
    result = {"excel_status": excel_status, "download_url": download_url}
    await persist_job_result(search_id, "excel_result", result)

    # AC20: Emit SSE event
    tracker = await get_tracker(search_id)
    if tracker:
        if download_url:
            await tracker.emit(
                "excel_ready", 98,
                "Planilha pronta para download",
                download_url=download_url,
            )
        else:
            await tracker.emit(
                "excel_ready", 98,
                "Erro ao gerar planilha. Tente novamente.",
                excel_status="failed",
            )

    return result


# ==========================================================================
# GTM-ARCH-001: Async Search Job
# ==========================================================================

async def search_job(
    ctx: dict,
    search_id: str,
    request_data: dict,
    user_data: dict,
    **kwargs,
) -> dict:
    """GTM-ARCH-001 AC2: Background job — execute full search pipeline.

    Runs the 7-stage SearchPipeline in the ARQ Worker, completely decoupled
    from the HTTP request cycle. Railway's ~120s proxy timeout becomes
    irrelevant because POST /buscar already returned 202.

    AC18: Emits search_job_duration_seconds histogram metric.
    AC19: Structured log with search_id, queued_at, started_at, completed_at, status.
    AC17: Worker uses existing tracker for heartbeat emission.

    Args:
        ctx: ARQ worker context dict.
        search_id: UUID correlating POST → SSE → Worker.
        request_data: Serialized BuscaRequest (from model_dump()).
        user_data: User dict (id, plan, roles).
        **kwargs: Trace context (_trace_id, _span_id).

    Returns:
        Dict with status, total_results, duration_ms.
    """
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from search_pipeline import executar_busca_completa
    from progress import get_tracker, remove_tracker
    from metrics import SEARCH_JOB_DURATION
    from datetime import datetime, timezone

    started_at = datetime.now(timezone.utc)
    start_mono = time.monotonic()

    logger.info(json.dumps({
        "event": "search_job_started",
        "search_id": search_id,
        "queued_at": kwargs.get("_queued_at"),
        "started_at": started_at.isoformat(),
        "ufs": request_data.get("ufs", []),
    }))

    tracker = await get_tracker(search_id)
    status = "completed"

    try:
        # STORY-281 AC2: Check cancel flag before starting heavy work
        if await check_cancel_flag(search_id):
            status = "cancelled"
            logger.info(f"[Search Job] Cancelled before start: search_id={search_id}")
            return {"status": "cancelled", "total_results": 0}

        response = await executar_busca_completa(
            search_id=search_id,
            request_data=request_data,
            user_data=user_data,
            tracker=tracker,
            quota_pre_consumed=True,  # AC8: Quota consumed in POST before enqueue
        )

        # STORY-281 AC2: Check cancel flag after pipeline completes
        # If cancelled while running, discard results — inline fallback is handling it
        if await check_cancel_flag(search_id):
            status = "cancelled"
            logger.info(
                f"[Search Job] Cancelled after completion: search_id={search_id} "
                f"(inline fallback took over)"
            )
            await clear_cancel_flag(search_id)
            return {"status": "cancelled", "total_results": 0}

        total_results = response.total_filtrado if response else 0

        # Persist full result for /buscar-results/{search_id} retrieval
        if response:
            await persist_job_result(
                search_id, "search_result", response.model_dump()
            )

        # Emit search_complete via SSE (AC3, AC16)
        tracker = await get_tracker(search_id)
        if tracker:
            await tracker.emit_search_complete(search_id, total_results)
            await remove_tracker(search_id)

        logger.info(f"[Search Job] Completed: search_id={search_id}, results={total_results}")
        await clear_cancel_flag(search_id)
        return {"status": "completed", "total_results": total_results}

    except Exception as e:
        status = "failed"
        logger.error(
            f"[Search Job] Failed: search_id={search_id}, "
            f"error={type(e).__name__}: {e}",
            exc_info=True,
        )
        # Emit error via SSE (AC20)
        tracker = await get_tracker(search_id)
        if tracker:
            await tracker.emit_error(str(e)[:300])
            await remove_tracker(search_id)
        raise

    finally:
        duration_s = time.monotonic() - start_mono
        duration_ms = int(duration_s * 1000)
        SEARCH_JOB_DURATION.observe(duration_s)
        completed_at = datetime.now(timezone.utc)
        logger.info(json.dumps({
            "event": "search_job_finished",
            "search_id": search_id,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "status": status,
        }))
        await clear_cancel_flag(search_id)


# ==========================================================================
# CRIT-032: Periodic Cache Refresh Job
# ==========================================================================

async def cache_refresh_job(ctx: dict) -> dict:
    """CRIT-032 AC1: Periodic cache refresh — re-fetches stale and empty cache entries.

    Runs as ARQ cron job every N hours. Queries search_results_cache for:
      - HOT + WARM entries older than 6h
      - Empty entries (total_results=0)
    Re-executes each via trigger_background_revalidation().

    Returns summary dict with refresh stats.
    """
    import uuid
    import time as _time

    from config import (
        CACHE_REFRESH_ENABLED,
        CACHE_REFRESH_BATCH_SIZE,
        CACHE_REFRESH_STAGGER_SECONDS,
    )
    from metrics import CACHE_REFRESH_TOTAL, CACHE_REFRESH_DURATION

    cycle_id = str(uuid.uuid4())[:8]
    start = _time.monotonic()

    # AC3: Feature flag check
    if not CACHE_REFRESH_ENABLED:
        logger.info(f"[CacheRefresh {cycle_id}] Skipped — CACHE_REFRESH_ENABLED=false")
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {
        "cycle_id": cycle_id,
        "total_candidates": 0,
        "refreshed": 0,
        "skipped_cooldown": 0,
        "skipped_degraded": 0,
        "skipped_cb_open": 0,
        "failed": 0,
        "empty_retried": 0,
    }

    # AC14: Graceful on Redis unavailable
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis is None:
            logger.warning(f"[CacheRefresh {cycle_id}] Redis unavailable — skipping cycle")
            return {"status": "redis_unavailable", "cycle_id": cycle_id}
    except Exception as e:
        logger.warning(f"[CacheRefresh {cycle_id}] Redis check failed: {e}")
        return {"status": "redis_unavailable", "cycle_id": cycle_id}

    # AC15: Graceful on Supabase unavailable
    try:
        from search_cache import get_stale_entries_for_refresh
        entries = await get_stale_entries_for_refresh(batch_size=CACHE_REFRESH_BATCH_SIZE)
    except Exception as e:
        logger.error(f"[CacheRefresh {cycle_id}] Supabase query failed: {e}")
        return {"status": "supabase_unavailable", "cycle_id": cycle_id}

    stats["total_candidates"] = len(entries)

    if not entries:
        logger.info(f"[CacheRefresh {cycle_id}] No stale entries found")
        duration_s = _time.monotonic() - start
        CACHE_REFRESH_DURATION.observe(duration_s)
        return {"status": "no_candidates", "cycle_id": cycle_id, **stats}

    # AC10-13: Replay each entry with stagger
    from datetime import date, timedelta
    from search_cache import trigger_background_revalidation

    today = date.today()
    data_final = today.isoformat()
    data_inicial = (today - timedelta(days=10)).isoformat()

    for i, entry in enumerate(entries):
        # AC13: Check circuit breaker before each dispatch
        try:
            from pncp_client import get_circuit_breaker
            cb = get_circuit_breaker("pncp")
            if hasattr(cb, "is_degraded") and cb.is_degraded:
                remaining = len(entries) - i
                stats["skipped_cb_open"] += remaining
                logger.warning(
                    f"[CacheRefresh {cycle_id}] PNCP circuit breaker degraded — "
                    f"stopping cycle ({remaining} entries skipped)"
                )
                break
        except Exception:
            pass

        search_params = entry.get("search_params", {})
        user_id = entry.get("user_id")
        is_empty = entry.get("total_results", 0) == 0

        # AC10: Build request_data with fresh date window
        request_data = {
            "ufs": search_params.get("ufs", []),
            "data_inicial": data_inicial,
            "data_final": data_final,
            "modalidades": search_params.get("modalidades"),
            "setor_id": search_params.get("setor_id"),
            "status": search_params.get("status"),
            "modo_busca": search_params.get("modo_busca"),
        }

        # AC11: Dispatch via existing revalidation infrastructure
        try:
            dispatched = await trigger_background_revalidation(
                user_id=user_id,
                params=search_params,
                request_data=request_data,
            )

            if dispatched:
                stats["refreshed"] += 1
                if is_empty:
                    stats["empty_retried"] += 1
                CACHE_REFRESH_TOTAL.labels(
                    result="empty_retry" if is_empty else "success"
                ).inc()
            else:
                stats["skipped_cooldown"] += 1
                CACHE_REFRESH_TOTAL.labels(result="skipped").inc()

        except Exception as e:
            stats["failed"] += 1
            CACHE_REFRESH_TOTAL.labels(result="failed").inc()
            logger.debug(f"[CacheRefresh {cycle_id}] Entry {entry['params_hash'][:12]} failed: {e}")

        # AC12: Stagger between dispatches (skip after last)
        if i < len(entries) - 1:
            await asyncio.sleep(CACHE_REFRESH_STAGGER_SECONDS)

    # AC17: Structured log summary
    duration_s = _time.monotonic() - start
    duration_ms = int(duration_s * 1000)
    stats["duration_ms"] = duration_ms
    CACHE_REFRESH_DURATION.observe(duration_s)

    import json as _json
    logger.info(_json.dumps({"event": "cache_refresh_cycle", **stats}))

    return {"status": "completed", **stats}


# ==========================================================================
# STORY-259: Bid Analysis Job
# ==========================================================================

async def bid_analysis_job(
    ctx: dict,
    search_id: str,
    licitacoes: list,
    user_profile: dict | None = None,
    sector_name: str = "",
    **kwargs,
) -> dict:
    """Background job: Batch bid analysis via LLM.

    STORY-259 AC3: Generates per-bid justifications and compatibility %.
    Dispatched in parallel with LLM summary and Excel.
    """
    from middleware import search_id_var, request_id_var
    search_id_var.set(search_id)
    request_id_var.set(kwargs.get("_trace_id", search_id))

    from bid_analyzer import batch_analyze_bids
    from progress import get_tracker

    logger.info(f"[BidAnalysis Job] search_id={search_id}, bids={len(licitacoes)}, sector={sector_name}")

    try:
        results = batch_analyze_bids(
            bids=licitacoes,
            user_profile=user_profile,
            sector_name=sector_name,
        )
        result_data = [r.model_dump() for r in results]
    except Exception as e:
        logger.warning(f"[BidAnalysis Job] Failed ({type(e).__name__}): {e}")
        result_data = []

    # Persist result
    await persist_job_result(search_id, "bid_analysis", result_data)

    # Emit SSE event
    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit(
            "bid_analysis_ready", 90,
            "Análise de editais pronta",
            bid_analysis=result_data,
        )

    return {"status": "completed", "count": len(result_data)}


# ==========================================================================
# STORY-278: Daily Digest Email Job
# ==========================================================================

async def daily_digest_job(ctx: dict) -> dict:
    """STORY-278 AC5: Send daily digest emails to eligible users.

    Runs as ARQ cron job at DIGEST_HOUR_UTC (default 10:00 = 7:00 BRT).
    Queries users with digest_enabled=true, builds per-user digests,
    sends via Resend Batch API, and updates last_digest_sent_at.

    Returns:
        Dict with job stats (users_queried, emails_sent, failed, skipped).
    """
    import uuid as _uuid
    from config import DIGEST_ENABLED, DIGEST_MAX_PER_EMAIL, DIGEST_BATCH_SIZE
    from metrics import DIGEST_EMAILS_SENT, DIGEST_JOB_DURATION

    cycle_id = str(_uuid.uuid4())[:8]
    start = time.monotonic()

    if not DIGEST_ENABLED:
        logger.info(f"[Digest {cycle_id}] Skipped — DIGEST_ENABLED=false")
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {
        "cycle_id": cycle_id,
        "users_queried": 0,
        "emails_sent": 0,
        "emails_failed": 0,
        "emails_skipped": 0,
    }

    try:
        from supabase_client import get_supabase
        db = get_supabase()
    except Exception as e:
        logger.error(f"[Digest {cycle_id}] Supabase unavailable: {e}")
        return {"status": "db_unavailable", **stats}

    try:
        from services.digest_service import (
            get_digest_eligible_users,
            build_digest_for_user,
            mark_digest_sent,
        )
        from templates.emails.digest import render_daily_digest_email
        from email_service import send_batch_email

        eligible = await get_digest_eligible_users(db)
        stats["users_queried"] = len(eligible)

        if not eligible:
            logger.info(f"[Digest {cycle_id}] No eligible users")
            duration_s = time.monotonic() - start
            DIGEST_JOB_DURATION.observe(duration_s)
            return {"status": "no_users", **stats}

        # Build digests for all eligible users
        batch_messages = []
        user_ids_in_batch = []

        for user_prefs in eligible:
            user_id = user_prefs["user_id"]

            try:
                digest = await build_digest_for_user(
                    user_id=user_id,
                    db=db,
                    max_items=DIGEST_MAX_PER_EMAIL,
                )

                if not digest or not digest.get("email"):
                    stats["emails_skipped"] += 1
                    DIGEST_EMAILS_SENT.labels(status="skipped").inc()
                    continue

                html = render_daily_digest_email(
                    user_name=digest["user_name"],
                    opportunities=digest["opportunities"],
                    stats=digest["stats"],
                )

                batch_messages.append({
                    "to": digest["email"],
                    "subject": f"{digest['stats']['total_novas']} oportunidades no seu setor — SmartLic",
                    "html": html,
                    "tags": [
                        {"name": "category", "value": "digest"},
                        {"name": "cycle_id", "value": cycle_id},
                    ],
                })
                user_ids_in_batch.append(user_id)

            except Exception as e:
                stats["emails_failed"] += 1
                DIGEST_EMAILS_SENT.labels(status="failed").inc()
                logger.warning(f"[Digest {cycle_id}] Failed to build digest for {user_id[:8]}: {e}")

        if not batch_messages:
            logger.info(f"[Digest {cycle_id}] No messages to send after building")
            duration_s = time.monotonic() - start
            DIGEST_JOB_DURATION.observe(duration_s)
            return {"status": "no_messages", **stats}

        # Send in batches of DIGEST_BATCH_SIZE (Resend max 100)
        for batch_start in range(0, len(batch_messages), DIGEST_BATCH_SIZE):
            batch_end = min(batch_start + DIGEST_BATCH_SIZE, len(batch_messages))
            batch_slice = batch_messages[batch_start:batch_end]
            batch_user_ids = user_ids_in_batch[batch_start:batch_end]

            idempotency_key = f"digest-{cycle_id}-{batch_start}"
            result = send_batch_email(batch_slice, idempotency_key=idempotency_key)

            if result is not None:
                stats["emails_sent"] += len(batch_slice)
                DIGEST_EMAILS_SENT.labels(status="success").inc(len(batch_slice))

                # Update last_digest_sent_at for each user in this batch
                for uid in batch_user_ids:
                    await mark_digest_sent(uid, db)
            else:
                stats["emails_failed"] += len(batch_slice)
                DIGEST_EMAILS_SENT.labels(status="failed").inc(len(batch_slice))
                logger.error(f"[Digest {cycle_id}] Batch send failed: {batch_start}-{batch_end}")

    except Exception as e:
        logger.error(f"[Digest {cycle_id}] Unexpected error: {e}", exc_info=True)
        return {"status": "error", "error": str(e), **stats}

    duration_s = time.monotonic() - start
    duration_ms = int(duration_s * 1000)
    stats["duration_ms"] = duration_ms
    DIGEST_JOB_DURATION.observe(duration_s)

    logger.info(json.dumps({"event": "digest_sent", **stats}))

    return {"status": "completed", **stats}


# ==========================================================================
# GTM-STAB-007: Cache Warming Job
# ==========================================================================

async def _get_active_search_count() -> int:
    """Read the current value of the ACTIVE_SEARCHES Prometheus gauge.

    Returns 0 if the gauge is not available or reading fails.
    """
    try:
        from metrics import ACTIVE_SEARCHES
        return int(ACTIVE_SEARCHES._value.get())
    except Exception:
        return 0


async def _warming_wait_for_idle(
    cycle_id: str,
    combo_label: str,
    pause_delay: float,
    max_cycles: int,
) -> bool:
    """Wait until no active user searches are running.

    Returns True if idle was reached, False if max pause cycles exhausted.
    """
    from metrics import WARMING_PAUSES_TOTAL

    for pause_i in range(max_cycles):
        active = await _get_active_search_count()
        if active <= 0:
            return True

        WARMING_PAUSES_TOTAL.inc()
        logger.info(
            "warming_paused",
            extra={
                "reason": "active_user_search",
                "combo": combo_label,
                "cycle_id": cycle_id,
                "active_searches": active,
                "pause_cycle": pause_i + 1,
                "max_cycles": max_cycles,
            },
        )
        await asyncio.sleep(pause_delay)

    # Exhausted all pause cycles — still active
    return False


async def cache_warming_job(ctx: dict) -> dict:
    """GTM-STAB-007 AC1+AC4: Pre-warm cache for popular search combinations.

    AC4 non-interference guarantees:
      1. Low-priority batching: WARMING_BATCH_DELAY_S (3s) between each request,
         sequential processing (one combo at a time).
      2. Pause on active searches: checks ACTIVE_SEARCHES gauge before each
         request; waits up to WARMING_MAX_PAUSE_CYCLES * WARMING_PAUSE_ON_ACTIVE_S.
      3. PNCP rate limit awareness: stops on circuit breaker OPEN or 429.
      4. Budget timeout: WARMING_BUDGET_TIMEOUT_S (30 min) hard cap.
      5. System UUID: WARMING_USER_ID avoids counting against real user quotas.
    """
    import uuid
    from config import (
        CACHE_WARMING_ENABLED,
        WARMING_BATCH_DELAY_S,
        WARMING_BUDGET_TIMEOUT_S,
        WARMING_PAUSE_ON_ACTIVE_S,
        WARMING_MAX_PAUSE_CYCLES,
        WARMING_USER_ID,
        WARMING_RATE_LIMIT_BACKOFF_S,
    )
    from metrics import WARMING_COMBINATIONS_TOTAL

    cycle_id = str(uuid.uuid4())[:8]
    start = time.monotonic()

    if not CACHE_WARMING_ENABLED:
        logger.info(f"[CacheWarming {cycle_id}] Skipped — CACHE_WARMING_ENABLED=false")
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {
        "cycle_id": cycle_id,
        "warmed": 0,
        "skipped_active": 0,
        "skipped_cb_open": 0,
        "skipped_rate_limit": 0,
        "skipped_budget": 0,
        "failed": 0,
    }

    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        result = await sb_execute(
            sb.table("search_sessions").select(
                "search_params"
            ).eq("status", "completed").order(
                "created_at", desc=True
            ).limit(200)
        )

        if not result.data:
            return {"status": "no_data", **stats}

        # Count frequency of setor+ufs combinations
        combo_counts: dict[str, dict] = {}
        for row in result.data:
            params = row.get("search_params") or {}
            setor = params.get("setor_id", "")
            ufs = tuple(sorted(params.get("ufs", [])))
            key = f"{setor}:{','.join(ufs)}"
            if key not in combo_counts:
                combo_counts[key] = {"setor_id": setor, "ufs": list(ufs), "count": 0}
            combo_counts[key]["count"] += 1

        # Sort by frequency, take top 50 — sequential processing (one at a time)
        top_combos = sorted(combo_counts.values(), key=lambda x: x["count"], reverse=True)[:50]

        from datetime import date, timedelta
        today = date.today()
        data_final = today.isoformat()
        data_inicial = (today - timedelta(days=10)).isoformat()

        for i, combo in enumerate(top_combos):
            combo_label = f"{combo['setor_id']}:{','.join(combo['ufs'])}"

            # --- Guard 1: Budget timeout ---
            elapsed = time.monotonic() - start
            if elapsed > WARMING_BUDGET_TIMEOUT_S:
                remaining = len(top_combos) - i
                stats["skipped_budget"] += remaining
                WARMING_COMBINATIONS_TOTAL.labels(result="skipped_budget").inc(remaining)
                logger.info(
                    f"[CacheWarming {cycle_id}] Budget exhausted "
                    f"({elapsed:.0f}s > {WARMING_BUDGET_TIMEOUT_S:.0f}s) — "
                    f"{remaining} combos skipped"
                )
                break

            # --- Guard 2: Circuit breaker check ---
            try:
                from pncp_client import get_circuit_breaker
                cb = get_circuit_breaker("pncp")
                if cb.is_degraded:
                    remaining = len(top_combos) - i
                    stats["skipped_cb_open"] += remaining
                    WARMING_COMBINATIONS_TOTAL.labels(result="skipped_cb_open").inc(remaining)
                    logger.warning(
                        f"[CacheWarming {cycle_id}] PNCP circuit breaker OPEN — "
                        f"stopping warming ({remaining} combos skipped)"
                    )
                    break
            except Exception:
                pass

            # --- Guard 3: Pause on active user searches ---
            idle = await _warming_wait_for_idle(
                cycle_id=cycle_id,
                combo_label=combo_label,
                pause_delay=WARMING_PAUSE_ON_ACTIVE_S,
                max_cycles=WARMING_MAX_PAUSE_CYCLES,
            )
            if not idle:
                stats["skipped_active"] += 1
                WARMING_COMBINATIONS_TOTAL.labels(result="skipped_active").inc()
                logger.info(
                    f"[CacheWarming {cycle_id}] Skipping {combo_label} — "
                    f"active searches after {WARMING_MAX_PAUSE_CYCLES} pause cycles"
                )
                # Still apply batch delay before next combo
                await asyncio.sleep(WARMING_BATCH_DELAY_S)
                continue

            # --- Dispatch warming request ---
            try:
                from search_cache import trigger_background_revalidation
                request_data = {
                    "ufs": combo["ufs"],
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "setor_id": combo["setor_id"],
                }
                dispatched = await trigger_background_revalidation(
                    user_id=WARMING_USER_ID,
                    params=request_data,
                    request_data=request_data,
                )
                if dispatched:
                    stats["warmed"] += 1
                    WARMING_COMBINATIONS_TOTAL.labels(result="warmed").inc()
                else:
                    stats["failed"] += 1
                    WARMING_COMBINATIONS_TOTAL.labels(result="failed").inc()
            except Exception as e:
                error_str = str(e).lower()
                # --- Guard 4: Rate limit (429) detection ---
                if "429" in error_str or "rate limit" in error_str or "too many" in error_str:
                    remaining = len(top_combos) - i - 1
                    stats["skipped_rate_limit"] += 1 + remaining
                    WARMING_COMBINATIONS_TOTAL.labels(result="skipped_rate_limit").inc(1 + remaining)
                    logger.warning(
                        f"[CacheWarming {cycle_id}] PNCP 429 rate limit hit — "
                        f"stopping warming for {WARMING_RATE_LIMIT_BACKOFF_S}s "
                        f"({remaining} combos skipped)"
                    )
                    break
                else:
                    stats["failed"] += 1
                    WARMING_COMBINATIONS_TOTAL.labels(result="failed").inc()
                    logger.debug(f"[CacheWarming {cycle_id}] {combo_label} failed: {e}")

            # --- Low-priority batch delay (skip after last combo) ---
            if i < len(top_combos) - 1:
                await asyncio.sleep(WARMING_BATCH_DELAY_S)

    except Exception as e:
        logger.warning(f"[CacheWarming {cycle_id}] Error: {e}")
        return {"status": "error", "error": str(e), **stats}

    duration_ms = int((time.monotonic() - start) * 1000)
    stats["duration_ms"] = duration_ms
    logger.info(json.dumps({"event": "cache_warming_cycle", **stats}))
    return {"status": "completed", **stats}


# ==========================================================================
# ARQ Worker Settings (AC5)
# ==========================================================================

# Compute redis settings at module level for worker process
try:
    _worker_redis_settings = _get_redis_settings()
except Exception:
    # Web process without REDIS_URL — WorkerSettings won't be used
    _worker_redis_settings = None

# CRIT-032 AC2: Build cron_jobs at module level (arq expects list attribute)
try:
    from arq.cron import cron as _arq_cron
    from config import CACHE_REFRESH_INTERVAL_HOURS, CACHE_REFRESH_BATCH_SIZE

    _cron_timeout = max(300, CACHE_REFRESH_BATCH_SIZE * 10)
    _cron_hours = set(range(0, 24, CACHE_REFRESH_INTERVAL_HOURS))
    _worker_cron_jobs = [
        _arq_cron(cache_refresh_job, hour=_cron_hours, minute=0, timeout=_cron_timeout),
    ]

    from config import CACHE_WARMING_ENABLED, CACHE_WARMING_INTERVAL_HOURS as _warming_hours
    if CACHE_WARMING_ENABLED:
        _warming_cron_hours = set(range(0, 24, _warming_hours))
        _worker_cron_jobs.append(
            _arq_cron(cache_warming_job, hour=_warming_cron_hours, minute=30, timeout=1800),
        )

    # STORY-278 AC5: Daily digest cron job
    from config import DIGEST_ENABLED, DIGEST_HOUR_UTC
    if DIGEST_ENABLED:
        _worker_cron_jobs.append(
            _arq_cron(daily_digest_job, hour={DIGEST_HOUR_UTC}, minute=0, timeout=1800),
        )
except Exception:
    _worker_cron_jobs = []


async def _worker_on_startup(ctx: dict) -> None:
    """CRIT-038: Harden ARQ worker's Redis pool with socket_timeout.

    ARQ's RedisSettings doesn't expose socket_timeout (only conn_timeout which
    maps to socket_connect_timeout). Without socket_timeout, individual Redis
    operations (SETEX, DELETE in finish_job) can hang indefinitely on network
    hiccups, causing the entire worker process to crash.

    This injects the same socket_timeout=30s used by the web process (redis_pool.py)
    directly into the worker's connection pool kwargs, ensuring all new connections
    inherit hardened timeout settings.
    """
    redis = ctx.get("redis")
    if redis and hasattr(redis, "connection_pool"):
        pool = redis.connection_pool
        if hasattr(pool, "connection_kwargs"):
            pool.connection_kwargs.setdefault("socket_timeout", 30)
            pool.connection_kwargs.setdefault("socket_connect_timeout", 10)
            pool.connection_kwargs.setdefault("socket_keepalive", True)
            logger.info(
                "CRIT-038: Worker Redis pool hardened — "
                f"socket_timeout={pool.connection_kwargs.get('socket_timeout')}s, "
                f"socket_connect_timeout={pool.connection_kwargs.get('socket_connect_timeout')}s, "
                f"keepalive={pool.connection_kwargs.get('socket_keepalive')}"
            )
    else:
        logger.warning("CRIT-038: Could not access worker Redis connection pool for hardening")


class WorkerSettings:
    """ARQ worker configuration.

    Start the worker with:
        arq backend.job_queue.WorkerSettings

    Or in production (Railway):
        cd backend && arq job_queue.WorkerSettings
    """

    functions = [llm_summary_job, excel_generation_job, cache_refresh_job, search_job, bid_analysis_job, cache_warming_job, daily_digest_job]
    cron_jobs = _worker_cron_jobs  # CRIT-032 AC2: periodic cache refresh
    on_startup = _worker_on_startup  # CRIT-038: Inject socket_timeout into Redis pool
    redis_settings = _worker_redis_settings
    max_jobs = 10
    job_timeout = 300  # GTM-ARCH-001: search_job needs up to 300s for multi-UF
    max_tries = 3      # AC10/AC15: 1 initial + 2 retries
    health_check_interval = 30
    retry_delay = 5.0  # CRIT-038: Increased from 2.0 → 5.0 to allow Redis recovery
