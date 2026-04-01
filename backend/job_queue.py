"""job_queue.py — ARQ pool + enqueue (state lives here for test compat).

Job function implementations moved to jobs/queue/ sub-package (DEBT-v3-S3 Phase 2.3).
Import from this module continues to work unchanged.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

arq_log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"arq_fmt": {"format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"}},
    "handlers": {"stdout": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "arq_fmt"}},
    "root": {"level": "INFO", "handlers": ["stdout"]},
}

# Pool state lives here so tests can mutate job_queue._arq_pool directly
_arq_pool = None
_pool_lock = asyncio.Lock()
_worker_alive_cache: tuple[float, bool] = (0.0, False)
_WORKER_CHECK_INTERVAL = 15


def _get_redis_settings():
    from arq.connections import RedisSettings
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        raise ValueError("REDIS_URL not set — ARQ worker cannot start without Redis")
    parsed = urlparse(redis_url)
    ssl = parsed.scheme == "rediss"
    return RedisSettings(
        host=parsed.hostname or "localhost", port=parsed.port or 6379,
        password=parsed.password, database=int(parsed.path.lstrip("/") or 0),
        conn_timeout=10, conn_retries=5, conn_retry_delay=2.0, ssl=ssl,
        retry_on_timeout=True, retry_on_error=[TimeoutError, ConnectionError, OSError],
        max_connections=50,
    )


async def get_arq_pool():
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
        for attempt in range(1, 4):
            try:
                from arq import create_pool
                _arq_pool = await create_pool(_get_redis_settings())
                logger.info(f"ARQ connection pool created (attempt {attempt})")
                return _arq_pool
            except Exception as e:
                delay = 2 ** attempt
                logger.warning(f"redis_pool_reconnect attempt={attempt}/3 delay={delay}s error={type(e).__name__}: {e}")
                if attempt < 3:
                    await asyncio.sleep(delay)
        logger.warning("ARQ pool creation failed after all retries")
        return None


async def close_arq_pool() -> None:
    global _arq_pool
    if _arq_pool is not None:
        try:
            await _arq_pool.close()
        except Exception as e:
            logger.warning(f"Error closing ARQ pool: {e}")
        _arq_pool = None
        logger.info("ARQ pool closed")


async def _check_worker_alive(pool) -> bool:
    global _worker_alive_cache
    now = time.monotonic()
    last_check, last_result = _worker_alive_cache
    if now - last_check < _WORKER_CHECK_INTERVAL:
        return last_result
    try:
        alive = bool(await pool.exists("arq:queue:health-check"))
        _worker_alive_cache = (now, alive)
        if not alive:
            logger.info("CRIT-033: No active ARQ worker detected — pipeline will use inline mode")
        return alive
    except Exception as e:
        logger.debug(f"CRIT-033: Worker health check failed: {e}")
        _worker_alive_cache = (now, False)
        return False


async def is_queue_available() -> bool:
    pool = await get_arq_pool()
    if pool is None:
        return False
    try:
        await pool.ping()
    except Exception:
        return False
    return await _check_worker_alive(pool)


async def get_queue_health() -> str:
    return "healthy" if await is_queue_available() else "unavailable"


async def enqueue_job(function_name: str, *args: Any, _job_id: Optional[str] = None, **kwargs: Any):
    pool = await get_arq_pool()
    if pool is None:
        logger.warning(f"Queue unavailable — cannot enqueue {function_name}")
        return None
    try:
        from telemetry import get_trace_id, get_span_id
        trace_id = get_trace_id()
        if trace_id:
            kwargs["_trace_id"] = trace_id
            kwargs["_span_id"] = get_span_id()
    except Exception:
        pass
    try:
        job = await pool.enqueue_job(function_name, *args, _job_id=_job_id, **kwargs)
        if job is None:
            logger.warning(f"CRIT-033: pool.enqueue_job returned None for {function_name} (job_id={_job_id})")
            return None
        logger.info(f"Enqueued job: {function_name} (id={job.job_id})")
        return job
    except Exception as e:
        logger.warning(f"Failed to enqueue {function_name}: {e}")
        return None


# --- Result store / cancel flags / concurrent slots ---
from jobs.queue.result_store import (  # noqa: F401
    _CANCEL_KEY_PREFIX, _CANCEL_TTL,
    _CONCURRENT_SEARCH_KEY_PREFIX, _CONCURRENT_SEARCH_TTL,
    _PENDING_REVIEW_KEY_PREFIX, _ZERO_MATCH_KEY_PREFIX,
    set_cancel_flag, check_cancel_flag, clear_cancel_flag,
    persist_job_result, get_job_result, _update_results_excel_url,
    acquire_search_slot, release_search_slot,
    store_pending_review_bids, store_zero_match_results, get_zero_match_results,
)

# --- Job functions ---
from jobs.queue.jobs import (  # noqa: F401
    llm_summary_job, excel_generation_job, bid_analysis_job,
    cache_refresh_job, cache_warming_job,
    daily_digest_job, email_alerts_job,
    reclassify_pending_bids_job, classify_zero_match_job,
    _get_active_search_count, _warming_wait_for_idle,
)

# --- Search job ---
from jobs.queue.search import (  # noqa: F401
    search_job, _persist_search_results_to_redis,
    _persist_search_results_to_supabase, _update_search_session,
)

# --- Worker config ---
from jobs.queue.config import (  # noqa: F401
    _worker_redis_settings, _worker_cron_jobs, _worker_on_startup, WorkerSettings,
)
