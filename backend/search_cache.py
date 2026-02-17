"""GTM-FIX-010: Supabase-backed SWR cache for search results.

Implements Stale-While-Revalidate pattern:
  - Fresh (0-6h): Serve directly, skip live fetch
  - Stale (6-24h): Serve as fallback when ALL live sources fail
  - Expired (>24h): Not served, cleaned up periodically

The InMemoryCache in search_pipeline.py handles the "fresh" proactive path.
This module handles the persistent Supabase fallback for resilience.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# TTL boundaries (hours)
CACHE_FRESH_HOURS = 6
CACHE_STALE_HOURS = 24


def compute_search_hash(params: dict) -> str:
    """AC2: Deterministic hash from search params for deduplication.

    Excludes dates intentionally — stale cache should serve regardless of
    date range since it's better than nothing when all sources are down.
    """
    normalized = {
        "setor_id": params.get("setor_id"),
        "ufs": sorted(params.get("ufs", [])),
        "status": params.get("status"),
        "modalidades": sorted(params.get("modalidades") or []) or None,
        "modo_busca": params.get("modo_busca"),
    }
    params_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(params_json.encode()).hexdigest()


async def save_to_cache(
    user_id: str,
    params: dict,
    results: list,
    sources: list[str],
) -> None:
    """AC3: Persist search results to Supabase after successful fetch.

    Uses UPSERT on (user_id, params_hash) to update existing entries.
    AC1 revised: includes sources_json tracking which sources contributed.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        params_hash = compute_search_hash(params)
        now = datetime.now(timezone.utc).isoformat()

        row = {
            "user_id": user_id,
            "params_hash": params_hash,
            "search_params": params,
            "results": results,
            "total_results": len(results),
            "sources_json": sources,
            "fetched_at": now,
            "created_at": now,
        }

        sb.table("search_results_cache").upsert(
            row,
            on_conflict="user_id,params_hash",
        ).execute()

        logger.info(
            f"Cache SAVE: {len(results)} results for hash {params_hash[:12]}... "
            f"(sources: {sources})"
        )
    except Exception as e:
        # Cache save failures are non-fatal — log and continue
        logger.warning(f"Failed to save to Supabase cache: {e}")


async def get_from_cache(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """AC4: Retrieve cached results when all live sources fail.

    Returns dict with keys: results, cached_at, cached_sources, cache_age_hours, is_stale
    Returns None if no cache entry exists or entry is expired (>24h).
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        params_hash = compute_search_hash(params)

        response = (
            sb.table("search_results_cache")
            .select("results, total_results, sources_json, fetched_at, created_at")
            .eq("user_id", user_id)
            .eq("params_hash", params_hash)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not response.data:
            logger.info(f"Cache MISS for hash {params_hash[:12]}...")
            return None

        row = response.data[0]
        fetched_at_str = row.get("fetched_at") or row.get("created_at")
        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = now - fetched_at
        age_hours = age.total_seconds() / 3600

        # AC12: Expired entries (>24h) are not served
        if age_hours > CACHE_STALE_HOURS:
            logger.info(
                f"Cache EXPIRED for hash {params_hash[:12]}... "
                f"(age={age_hours:.1f}h > {CACHE_STALE_HOURS}h)"
            )
            return None

        is_stale = age_hours > CACHE_FRESH_HOURS

        logger.info(
            f"Cache HIT for hash {params_hash[:12]}... "
            f"(age={age_hours:.1f}h, stale={is_stale})"
        )

        return {
            "results": row.get("results", []),
            "cached_at": fetched_at_str,
            "cached_sources": row.get("sources_json") or ["pncp"],
            "cache_age_hours": round(age_hours, 1),
            "is_stale": is_stale,
        }

    except Exception as e:
        logger.warning(f"Failed to read from Supabase cache: {e}")
        return None
