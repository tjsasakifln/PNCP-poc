"""CRIT-004 AC21: Search trace endpoint for observability.

GET /v1/admin/search-trace/{search_id} — aggregates search journey data
from multiple sources (search sessions, cache, jobs).
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/search-trace/{search_id}")
async def get_search_trace(search_id: str, user=Depends(require_auth)) -> dict[str, Any]:
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
