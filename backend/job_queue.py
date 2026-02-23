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
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Singleton pool
_arq_pool = None
_pool_lock = asyncio.Lock()


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
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


async def get_arq_pool():
    """Get or create the ARQ connection pool (singleton).

    Returns:
        ArqRedis instance or None if Redis unavailable.
    """
    global _arq_pool

    if _arq_pool is not None:
        try:
            await _arq_pool.ping()
            return _arq_pool
        except Exception:
            _arq_pool = None

    async with _pool_lock:
        # Double-check after acquiring lock
        if _arq_pool is not None:
            return _arq_pool
        try:
            from arq import create_pool
            settings = _get_redis_settings()
            _arq_pool = await create_pool(settings)
            logger.info("ARQ connection pool created")
            return _arq_pool
        except Exception as e:
            logger.warning(f"Failed to create ARQ pool: {e}")
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


async def is_queue_available() -> bool:
    """Check if the job queue is healthy and ready to accept work.

    Used by the pipeline to decide between queue mode and inline mode.
    """
    pool = await get_arq_pool()
    if pool is None:
        return False
    try:
        await pool.ping()
        return True
    except Exception:
        return False


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
        logger.info(f"Enqueued job: {function_name} (id={job.job_id})")
        return job
    except Exception as e:
        logger.error(f"Failed to enqueue {function_name}: {e}")
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
except Exception:
    _worker_cron_jobs = []


class WorkerSettings:
    """ARQ worker configuration.

    Start the worker with:
        arq backend.job_queue.WorkerSettings

    Or in production (Railway):
        cd backend && arq job_queue.WorkerSettings
    """

    functions = [llm_summary_job, excel_generation_job, cache_refresh_job]
    cron_jobs = _worker_cron_jobs  # CRIT-032 AC2: periodic cache refresh
    redis_settings = _worker_redis_settings
    max_jobs = 10
    job_timeout = 60   # AC16: worst case (Excel can take longer than LLM)
    max_tries = 3      # AC10/AC15: 1 initial + 2 retries
    health_check_interval = 30
    retry_delay = 2.0  # seconds between retries
