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
        key = f"bidiq:job_result:{search_id}:{field}"
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
        key = f"bidiq:job_result:{search_id}:{field}"
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

async def llm_summary_job(ctx: dict, search_id: str, licitacoes: list, sector_name: str, **kwargs) -> dict:
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
        resumo = gerar_resumo(licitacoes, sector_name=sector_name)
        logger.info(f"[LLM Job] AI summary generated for {search_id}")
    except Exception as e:
        logger.warning(f"[LLM Job] LLM failed ({type(e).__name__}), using fallback: {e}")
        resumo = gerar_resumo_fallback(licitacoes, sector_name=sector_name)

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
        response = await executar_busca_completa(
            search_id=search_id,
            request_data=request_data,
            user_data=user_data,
            tracker=tracker,
            quota_pre_consumed=True,  # AC8: Quota consumed in POST before enqueue
        )

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
            from schemas import SearchErrorCode
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
    from search_cache import trigger_background_revalidation, compute_search_hash

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
# GTM-STAB-007: Cache Warming Job
# ==========================================================================

async def cache_warming_job(ctx: dict) -> dict:
    """GTM-STAB-007 AC1: Pre-warm cache for popular search combinations.

    Queries search_sessions for top combinations by frequency,
    then executes searches to populate cache. Rate-limited to avoid
    interfering with user searches.
    """
    import uuid
    from config import (
        CACHE_WARMING_ENABLED,
        CACHE_WARMING_CONCURRENCY,
        CACHE_WARMING_BUDGET_MINUTES,
    )
    from metrics import ACTIVE_SEARCHES

    cycle_id = str(uuid.uuid4())[:8]
    start = time.monotonic()

    if not CACHE_WARMING_ENABLED:
        logger.info(f"[CacheWarming {cycle_id}] Skipped — CACHE_WARMING_ENABLED=false")
        return {"status": "disabled", "cycle_id": cycle_id}

    stats = {"cycle_id": cycle_id, "warmed": 0, "skipped": 0, "failed": 0}
    budget_s = CACHE_WARMING_BUDGET_MINUTES * 60

    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        result = sb.table("search_sessions").select(
            "search_params"
        ).eq("status", "completed").order(
            "created_at", desc=True
        ).limit(200).execute()

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

        # Sort by frequency, take top 50
        top_combos = sorted(combo_counts.values(), key=lambda x: x["count"], reverse=True)[:50]

        from datetime import date, timedelta
        today = date.today()
        data_final = today.isoformat()
        data_inicial = (today - timedelta(days=10)).isoformat()

        for combo in top_combos:
            if time.monotonic() - start > budget_s:
                logger.info(f"[CacheWarming {cycle_id}] Budget exhausted ({CACHE_WARMING_BUDGET_MINUTES}min)")
                break

            # Skip if active user searches running
            try:
                active = ACTIVE_SEARCHES._value.get()
                if active > 0:
                    stats["skipped"] += 1
                    await asyncio.sleep(5)
                    continue
            except Exception:
                pass

            try:
                from search_cache import trigger_background_revalidation
                request_data = {
                    "ufs": combo["ufs"],
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "setor_id": combo["setor_id"],
                }
                dispatched = await trigger_background_revalidation(
                    user_id=None,
                    params=request_data,
                    request_data=request_data,
                )
                if dispatched:
                    stats["warmed"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                stats["failed"] += 1
                logger.debug(f"[CacheWarming {cycle_id}] Failed: {e}")

            await asyncio.sleep(5)  # Rate limit: 5s between warming calls

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
except Exception:
    _worker_cron_jobs = []


class WorkerSettings:
    """ARQ worker configuration.

    Start the worker with:
        arq backend.job_queue.WorkerSettings

    Or in production (Railway):
        cd backend && arq job_queue.WorkerSettings
    """

    functions = [llm_summary_job, excel_generation_job, cache_refresh_job, search_job, bid_analysis_job, cache_warming_job]
    cron_jobs = _worker_cron_jobs  # CRIT-032 AC2: periodic cache refresh
    redis_settings = _worker_redis_settings
    max_jobs = 10
    job_timeout = 300  # GTM-ARCH-001: search_job needs up to 300s for multi-UF
    max_tries = 3      # AC10/AC15: 1 initial + 2 retries
    health_check_interval = 30
    retry_delay = 2.0  # seconds between retries
