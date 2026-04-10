"""CRIT-004 AC21: Search trace endpoint for observability.

GET /v1/admin/search-trace/{search_id} — aggregates search journey data
from multiple sources (search sessions, cache, jobs).
POST /v1/admin/trigger-contracts-backfill — enqueue contracts full crawl to Worker.
POST /v1/admin/trigger-bids-backfill — enqueue historical bids backfill to Worker.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from admin import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.post("/trigger-contracts-backfill")
async def trigger_contracts_backfill(user=Depends(require_admin)) -> dict:
    """Enqueue contracts_full_crawl_job to ARQ Worker.

    Runs on Railway Worker (better network for PNCP).
    Safe to call multiple times — ARQ deduplicates by job name.
    """
    try:
        from job_queue import get_arq_pool
        from ingestion.contracts_crawler import CONTRACTS_FULL_CRAWL_TIMEOUT
        pool = await get_arq_pool()
        if not pool:
            return {"status": "error", "detail": "ARQ pool unavailable — Worker offline?"}

        # Timeout set via @arq_func(timeout=CONTRACTS_FULL_CRAWL_TIMEOUT) on the function.
        # Do NOT pass _timeout/_job_timeout as kwargs — ARQ forwards unknown kwargs to the function.
        job = await pool.enqueue_job("contracts_full_crawl_job")
        if job:
            return {"status": "enqueued", "job_id": job.job_id, "timeout_s": CONTRACTS_FULL_CRAWL_TIMEOUT}
        return {"status": "skipped", "detail": "Job already queued or duplicate"}
    except Exception as e:
        logger.error("trigger_contracts_backfill failed: %s", e)
        return {"status": "error", "detail": str(e)}


@router.post("/trigger-bids-backfill")
async def trigger_bids_backfill(user=Depends(require_admin)) -> dict:
    """Enqueue ingestion_backfill_job to ARQ Worker.

    One-time historical crawl: fetches up to 365 days of PNCP bids
    to capture all currently open opportunities.
    Expected runtime: 4-8h. Safe to call multiple times (ARQ dedup).
    """
    try:
        from job_queue import get_arq_pool
        pool = await get_arq_pool()
        if not pool:
            return {"status": "error", "detail": "ARQ pool unavailable — Worker offline?"}

        job = await pool.enqueue_job("ingestion_backfill_job")
        if job:
            return {"status": "enqueued", "job_id": job.job_id, "timeout_s": 36000}
        return {"status": "skipped", "detail": "Job already queued or duplicate"}
    except Exception as e:
        logger.error("trigger_bids_backfill failed: %s", e)
        return {"status": "error", "detail": str(e)}


@router.post("/clear-contracts-checkpoints")
async def clear_contracts_checkpoints(user=Depends(require_admin)) -> dict:
    """Clear all Redis checkpoints for contracts crawler.

    Use before re-triggering a full crawl when stale checkpoints
    cause windows to be incorrectly skipped.
    """
    try:
        from ingestion.contracts_crawler import clear_all_checkpoints
        deleted = await clear_all_checkpoints()
        return {"status": "ok", "checkpoints_deleted": deleted}
    except Exception as e:
        logger.error("clear_contracts_checkpoints failed: %s", e)
        return {"status": "error", "detail": str(e)}


@router.get("/search-trace/{search_id}")
async def get_search_trace(search_id: str, user=Depends(require_admin)) -> dict[str, Any]:
    """Reconstruct complete search journey from search_id.

    Aggregates:
    - Progress tracker state (if still active)
    - Cache entries matching this search
    - Job queue results (if ARQ available)
    """
    trace: dict[str, Any] = {
        "search_id": search_id,
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "progress": None,
        "cache": None,
        "jobs": None,
    }

    # 1. Check active progress tracker
    try:
        from progress import get_tracker
        tracker = await get_tracker(search_id)
        if tracker:
            trace["progress"] = {
                "uf_count": tracker.uf_count,
                "ufs_completed": tracker._ufs_completed,
                "is_complete": tracker._is_complete,
                "created_at": tracker.created_at,
                "mode": "redis" if tracker._use_redis else "in-memory",
            }
    except Exception as e:
        trace["progress"] = {"error": str(e)}

    # 2. Check job results in Redis
    try:
        from job_queue import get_job_result
        resumo = await get_job_result(search_id, "resumo_json")
        excel = await get_job_result(search_id, "excel_result")
        trace["jobs"] = {
            "llm_summary": "completed" if resumo else "not_found",
            "excel_generation": "completed" if excel else "not_found",
        }
    except Exception as e:
        trace["jobs"] = {"error": str(e)}

    # 3. Check cache for this search
    try:
        from redis_pool import get_redis_pool
        redis = await get_redis_pool()
        if redis:
            # Look for revalidation key
            reval_key = f"revalidating:{search_id[:16]}"
            is_revalidating = await redis.exists(reval_key)
            trace["cache"] = {
                "is_revalidating": bool(is_revalidating),
            }
        else:
            trace["cache"] = {"redis": "unavailable"}
    except Exception as e:
        trace["cache"] = {"error": str(e)}

    return trace
