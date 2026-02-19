"""UX-303 AC7: Cache health check endpoint.

GET /v1/health/cache — Returns status of each cache level with latency.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/cache")
async def cache_health():
    """AC7: Health check for all cache levels.

    Returns status of Supabase, Redis/InMemory, and Local file caches
    with latency measurements and error details.
    B-03 AC9: Includes degraded_keys_count and avg_fail_streak from health metadata.
    """
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "supabase": await _check_supabase_cache(),
        "redis": _check_redis_cache(),
        "local": _check_local_cache(),
        "degradation": await _check_cache_degradation(),
    }

    # Determine overall status
    statuses = [result["supabase"]["status"], result["redis"]["status"], result["local"]["status"]]
    if all(s == "healthy" for s in statuses):
        result["overall"] = "healthy"
    elif all(s == "down" for s in statuses):
        result["overall"] = "down"
    else:
        result["overall"] = "degraded"

    return result


async def _check_supabase_cache() -> dict:
    """Probe Supabase search_results_cache table."""
    start = time.monotonic()
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Light probe: count recent entries
        response = (
            sb.table("search_results_cache")
            .select("id", count="exact")
            .limit(1)
            .execute()
        )

        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "total_entries": response.count if hasattr(response, "count") and response.count is not None else len(response.data),
            "last_error": None,
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        logger.warning(f"Supabase cache health check failed: {e}")
        return {
            "status": "down",
            "latency_ms": latency_ms,
            "total_entries": 0,
            "last_error": str(e)[:200],
        }


def _check_redis_cache() -> dict:
    """Probe Redis/InMemory cache."""
    start = time.monotonic()
    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()

        alive = cache.ping()
        latency_ms = round((time.monotonic() - start) * 1000)
        entries = len(cache)

        return {
            "status": "healthy" if alive else "down",
            "latency_ms": latency_ms,
            "entries": entries,
            "last_error": None,
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "down",
            "latency_ms": latency_ms,
            "entries": 0,
            "last_error": str(e)[:200],
        }


def _check_local_cache() -> dict:
    """Probe local file cache directory."""
    start = time.monotonic()
    try:
        from search_cache import get_local_cache_stats
        stats = get_local_cache_stats()
        latency_ms = round((time.monotonic() - start) * 1000)

        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "files_count": stats["files_count"],
            "total_size_mb": stats["total_size_mb"],
            "last_error": None,
        }
    except Exception as e:
        latency_ms = round((time.monotonic() - start) * 1000)
        return {
            "status": "down",
            "latency_ms": latency_ms,
            "files_count": 0,
            "total_size_mb": 0.0,
            "last_error": str(e)[:200],
        }


async def _check_cache_degradation() -> dict:
    """B-03 AC9: Aggregate fail_streak and degradation metrics from Supabase."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Count keys where degraded_until > now()
        now_iso = datetime.now(timezone.utc).isoformat()
        degraded_resp = (
            sb.table("search_results_cache")
            .select("id", count="exact")
            .gt("degraded_until", now_iso)
            .limit(0)
            .execute()
        )
        degraded_count = degraded_resp.count if hasattr(degraded_resp, "count") and degraded_resp.count is not None else 0

        # Aggregate fail_streak stats (only for keys with fail_streak > 0)
        streak_resp = (
            sb.table("search_results_cache")
            .select("fail_streak")
            .gt("fail_streak", 0)
            .execute()
        )
        streaks = [row.get("fail_streak", 0) for row in (streak_resp.data or [])]
        avg_streak = round(sum(streaks) / len(streaks), 1) if streaks else 0.0

        return {
            "degraded_keys_count": degraded_count,
            "avg_fail_streak": avg_streak,
            "keys_with_failures": len(streaks),
        }
    except Exception as e:
        logger.warning(f"Cache degradation check failed: {e}")
        return {
            "degraded_keys_count": 0,
            "avg_fail_streak": 0.0,
            "keys_with_failures": 0,
            "error": str(e)[:200],
        }
