"""cache/admin.py — Admin cache metrics, invalidation, and inspection (B-05).

Extracted from cache/manager.py to keep manager.py under 600 LOC.
Re-exported via search_cache facade for backward compatibility.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from cache.enums import (
    LOCAL_CACHE_DIR,
    get_cache_status,
)

logger = logging.getLogger(__name__)


async def get_cache_metrics() -> dict:
    """B-05 AC3/AC4/AC10: Aggregate cache metrics for admin dashboard."""
    from supabase_client import get_supabase, sb_execute
    from redis_pool import get_fallback_cache

    metrics: dict = {}

    try:
        cache = get_fallback_cache()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        hits = int(cache.get(f"cache_counter:hits:{today}") or "0") + int(
            cache.get(f"cache_counter:hits:{yesterday}") or "0"
        )
        misses = int(cache.get(f"cache_counter:misses:{today}") or "0") + int(
            cache.get(f"cache_counter:misses:{yesterday}") or "0"
        )
        stale = int(cache.get(f"cache_counter:stale_served:{today}") or "0") + int(
            cache.get(f"cache_counter:stale_served:{yesterday}") or "0"
        )
        fresh = int(cache.get(f"cache_counter:fresh_served:{today}") or "0") + int(
            cache.get(f"cache_counter:fresh_served:{yesterday}") or "0"
        )

        total = hits + misses
        metrics["hit_rate_24h"] = round(hits / total, 2) if total > 0 else 0.0
        metrics["miss_rate_24h"] = round(misses / total, 2) if total > 0 else 0.0
        metrics["stale_served_24h"] = stale
        metrics["fresh_served_24h"] = fresh
    except Exception as e:
        logger.debug(f"Counter metrics failed: {e}")
        metrics.update({"hit_rate_24h": 0.0, "miss_rate_24h": 0.0, "stale_served_24h": 0, "fresh_served_24h": 0})

    try:
        sb = get_supabase()

        all_entries = await sb_execute(
            sb.table("search_results_cache")
            .select("params_hash, priority, fetched_at, access_count, fail_streak, degraded_until, fetch_duration_ms")
        )
        rows = all_entries.data or []
        metrics["total_entries"] = len(rows)

        priority_dist = {"hot": 0, "warm": 0, "cold": 0}
        for row in rows:
            p = row.get("priority", "cold")
            if p in priority_dist:
                priority_dist[p] += 1
        metrics["priority_distribution"] = priority_dist

        now = datetime.now(timezone.utc)
        age_dist = {"0-1h": 0, "1-6h": 0, "6-12h": 0, "12-24h": 0}
        for row in rows:
            fetched_str = row.get("fetched_at")
            if not fetched_str:
                continue
            try:
                fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                if fetched.tzinfo is None:
                    fetched = fetched.replace(tzinfo=timezone.utc)
                age_h = (now - fetched).total_seconds() / 3600
                if age_h <= 1:
                    age_dist["0-1h"] += 1
                elif age_h <= 6:
                    age_dist["1-6h"] += 1
                elif age_h <= 12:
                    age_dist["6-12h"] += 1
                elif age_h <= 24:
                    age_dist["12-24h"] += 1
            except (ValueError, TypeError):
                continue
        metrics["age_distribution"] = age_dist

        degraded = 0
        for row in rows:
            deg_str = row.get("degraded_until")
            if not deg_str:
                continue
            try:
                deg = datetime.fromisoformat(str(deg_str).replace("Z", "+00:00"))
                if deg.tzinfo is None:
                    deg = deg.replace(tzinfo=timezone.utc)
                if deg > now:
                    degraded += 1
            except (ValueError, TypeError):
                continue
        metrics["degraded_keys"] = degraded

        durations = [
            row.get("fetch_duration_ms") for row in rows
            if row.get("fetch_duration_ms") is not None
        ]
        metrics["avg_fetch_duration_ms"] = (
            round(sum(float(d) for d in durations) / len(durations))
            if durations else 0
        )

        sorted_rows = sorted(rows, key=lambda r: r.get("access_count", 0) or 0, reverse=True)[:10]
        top_keys = []
        for row in sorted_rows:
            fetched_str = row.get("fetched_at", "")
            age_h = 0.0
            if fetched_str:
                try:
                    fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                    if fetched.tzinfo is None:
                        fetched = fetched.replace(tzinfo=timezone.utc)
                    age_h = round((now - fetched).total_seconds() / 3600, 1)
                except (ValueError, TypeError):
                    pass
            top_keys.append({
                "params_hash": row.get("params_hash", ""),
                "access_count": row.get("access_count", 0) or 0,
                "priority": row.get("priority", "cold"),
                "age_hours": age_h,
            })
        metrics["top_keys"] = top_keys

    except Exception as e:
        logger.warning(f"Supabase cache metrics query failed: {e}")
        metrics.setdefault("total_entries", 0)
        metrics.setdefault("priority_distribution", {"hot": 0, "warm": 0, "cold": 0})
        metrics.setdefault("age_distribution", {"0-1h": 0, "1-6h": 0, "6-12h": 0, "12-24h": 0})
        metrics.setdefault("degraded_keys", 0)
        metrics.setdefault("avg_fetch_duration_ms", 0)
        metrics.setdefault("top_keys", [])

    return metrics


async def invalidate_cache_entry(params_hash: str) -> dict:
    """B-05 AC5: Invalidate a specific cache entry across all 3 levels."""
    deleted_levels: list = []

    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        await sb_execute(sb.table("search_results_cache").delete().eq("params_hash", params_hash))
        deleted_levels.append("supabase")
    except Exception as e:
        logger.warning(f"Supabase invalidation failed for {params_hash[:12]}: {e}")

    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()
        cache.delete(f"search_cache:{params_hash}")
        deleted_levels.append("redis")
    except Exception as e:
        logger.warning(f"Redis invalidation failed for {params_hash[:12]}: {e}")

    try:
        cache_file = LOCAL_CACHE_DIR / f"{params_hash[:32]}.json"
        if cache_file.exists():
            cache_file.unlink()
        deleted_levels.append("local")
    except Exception as e:
        logger.warning(f"Local invalidation failed for {params_hash[:12]}: {e}")

    logger.info(f"Cache entry {params_hash[:12]} invalidated from: {deleted_levels}")
    return {"deleted_levels": deleted_levels}


async def invalidate_all_cache() -> dict:
    """B-05 AC6: Invalidate ALL cache entries across all levels."""
    counts = {"supabase": 0, "redis": 0, "local": 0}

    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        result = await sb_execute(
            sb.table("search_results_cache").delete().gte("created_at", "2000-01-01")
        )
        counts["supabase"] = len(result.data) if result.data else 0
    except Exception as e:
        logger.warning(f"Supabase bulk invalidation failed: {e}")

    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()
        keys = cache.keys_by_prefix("search_cache:")
        for k in keys:
            cache.delete(k)
        counts["redis"] = len(keys)
    except Exception as e:
        logger.warning(f"Redis bulk invalidation failed: {e}")

    try:
        if LOCAL_CACHE_DIR.exists():
            files = list(LOCAL_CACHE_DIR.glob("*.json"))
            for f in files:
                f.unlink(missing_ok=True)
            counts["local"] = len(files)
    except Exception as e:
        logger.warning(f"Local bulk invalidation failed: {e}")

    logger.info(f"All cache invalidated: {counts}")
    return {"deleted_counts": counts}


async def inspect_cache_entry(params_hash: str) -> Optional[dict]:
    """B-05 AC7: Return full details of a specific cache entry."""
    try:
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()

        response = await sb_execute(
            sb.table("search_results_cache")
            .select(
                "params_hash, user_id, search_params, total_results, sources_json, "
                "fetched_at, created_at, priority, access_count, last_accessed_at, "
                "fail_streak, degraded_until, coverage, fetch_duration_ms, "
                "last_success_at, last_attempt_at"
            )
            .eq("params_hash", params_hash)
            .limit(1)
        )

        if not response.data:
            return None

        row = response.data[0]

        fetched_str = row.get("fetched_at") or row.get("created_at")
        age_hours = 0.0
        cache_status = "unknown"
        if fetched_str:
            try:
                fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                if fetched.tzinfo is None:
                    fetched = fetched.replace(tzinfo=timezone.utc)
                age_hours = round((datetime.now(timezone.utc) - fetched).total_seconds() / 3600, 1)
                status = get_cache_status(fetched)
                cache_status = status.value
            except (ValueError, TypeError):
                pass

        return {
            "params_hash": row.get("params_hash"),
            "user_id": row.get("user_id"),
            "search_params": row.get("search_params"),
            "results_count": row.get("total_results", 0),
            "sources": row.get("sources_json", []),
            "fetched_at": row.get("fetched_at"),
            "created_at": row.get("created_at"),
            "priority": row.get("priority", "cold"),
            "access_count": row.get("access_count", 0) or 0,
            "last_accessed_at": row.get("last_accessed_at"),
            "fail_streak": row.get("fail_streak", 0) or 0,
            "degraded_until": row.get("degraded_until"),
            "coverage": row.get("coverage"),
            "fetch_duration_ms": row.get("fetch_duration_ms"),
            "last_success_at": row.get("last_success_at"),
            "last_attempt_at": row.get("last_attempt_at"),
            "age_hours": age_hours,
            "cache_status": cache_status,
        }
    except Exception as e:
        logger.warning(f"Cache inspection failed for {params_hash[:12]}: {e}")
        return None


# Note: get_stale_entries_for_refresh, get_top_popular_params, and
# get_popular_ufs_from_sessions were removed on 2026-04-18 (STORY-CIG-BE-
# cache-warming-deprecate). They were consumed only by the deprecated
# warming/refresh cron jobs; DataLake Supabase is now the primary query path.
