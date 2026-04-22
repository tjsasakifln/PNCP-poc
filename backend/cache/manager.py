"""cache/manager.py — Multi-level cache orchestration (entry point).

Coordinates L1 (Supabase), L2 (Redis/InMemory), L3 (local file) layers.
Uses submodule references for I/O functions so tests can patch them via
patch("cache.redis._get_from_redis"), patch("cache.local_file._get_from_local"), etc.

Admin functions (metrics, invalidation, inspection) live in cache.admin.
Hit processing, tracking, and degradation ops live in cache._ops.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from utils.error_reporting import report_error
from metrics import CACHE_HITS as METRICS_CACHE_HITS, CACHE_MISSES as METRICS_CACHE_MISSES

from cache.enums import (
    CacheLevel, CacheStatus, CachePriority,
    CACHE_FRESH_HOURS, CACHE_STALE_HOURS,
    LOCAL_CACHE_DIR,
    classify_priority,
    compute_search_hash, compute_search_hash_without_dates,
    compute_global_hash, calculate_backoff_minutes,
    get_cache_status,
)

# Import submodules as objects so test patches work:
#   patch("cache.redis._get_from_redis") patches the attribute in the module object,
#   and since we call _redis._get_from_redis(...) the patched version is used.
import cache.redis as _redis
import cache.local_file as _local
import cache.supabase as _supa

# Import ops and admin for use and re-export
from cache._ops import (
    record_cache_fetch_failure, is_cache_key_degraded,
    _process_cache_hit, _process_cache_hit_allow_expired,
    _level_num, _track_cache_operation, _increment_and_reclassify,
)
from cache.admin import (
    get_cache_metrics, invalidate_cache_entry, invalidate_all_cache,
    inspect_cache_entry,
)
from cache.cascade import get_from_cache_cascade, _cascade_read_levels, _format_cache_date_range  # noqa: F401

logger = logging.getLogger(__name__)

# Configurable threshold for partial cache hits (AC2)
CACHE_PARTIAL_HIT_THRESHOLD = float(os.getenv("CACHE_PARTIAL_HIT_THRESHOLD", "0.5"))


# ============================================================================
# Multi-level save
# ============================================================================


async def save_to_cache(
    user_id: str,
    params: dict,
    results: list,
    sources: list,
    *,
    fetch_duration_ms: Optional[int] = None,
    coverage: Optional[dict] = None,
) -> dict:
    """Save results to cache with 3-level fallback (AC2)."""
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    from config import WARMING_USER_ID
    skip_supabase = (user_id == WARMING_USER_ID)

    # Level 1: Supabase
    if skip_supabase:
        logger.debug(
            f"Cache SAVE skipping L1/supabase for warming user "
            f"(key={params_hash[:12]}, n={len(results)})"
        )
    else:
        try:
            await _supa._save_to_supabase(
                user_id, params_hash, params, results, sources,
                fetch_duration_ms=fetch_duration_ms, coverage=coverage,
            )
            elapsed = (time.monotonic() - start) * 1000
            logger.info(
                f"Cache SAVE L1/supabase: {len(results)} results "
                f"for hash {params_hash[:12]}... ({elapsed:.0f}ms, sources: {sources})"
            )
            _track_cache_operation("save", True, CacheLevel.SUPABASE, len(results), elapsed)
            return {"level": CacheLevel.SUPABASE, "success": True}
        except Exception as e:
            report_error(
                e, f"Supabase cache save failed (key={params_hash[:12]}, n={len(results)})",
                expected=True, tags={"cache_operation": "save", "cache_level": "supabase"}, log=logger,
            )

    # Level 2: Redis/InMemory
    try:
        _redis._save_to_redis(params_hash, results, sources)
        elapsed = (time.monotonic() - start) * 1000
        logger.warning(
            f"Cache SAVE L2/redis fallback: {len(results)} results "
            f"for hash {params_hash[:12]}... ({elapsed:.0f}ms)"
        )
        _track_cache_operation("save", True, CacheLevel.REDIS, len(results), elapsed)
        return {"level": CacheLevel.REDIS, "success": True}
    except Exception as e:
        logger.error(f"Redis cache save failed: {e}")

    # Level 3: Local file
    try:
        _local._save_to_local(params_hash, results, sources)
        elapsed = (time.monotonic() - start) * 1000
        logger.warning(
            f"Cache SAVE L3/local fallback: {len(results)} results "
            f"for hash {params_hash[:12]}... ({elapsed:.0f}ms)"
        )
        _track_cache_operation("save", True, CacheLevel.LOCAL, len(results), elapsed)
        return {"level": CacheLevel.LOCAL, "success": True}
    except Exception as e:
        logger.error(f"All cache levels failed for save: {e}")
        _track_cache_operation("save", False, CacheLevel.MISS, len(results), 0)
        return {"level": CacheLevel.MISS, "success": False}


async def save_to_cache_per_uf(
    user_id: str,
    params: dict,
    results: list,
    sources: list,
    *,
    fetch_duration_ms: Optional[int] = None,
    coverage: Optional[dict] = None,
) -> dict:
    """CRIT-051 AC1: Save results grouped by UF — one cache entry per UF."""
    results_by_uf: dict = {}
    no_uf_results = []
    for r in results:
        uf = r.get("uf", "").upper()
        if uf:
            results_by_uf.setdefault(uf, []).append(r)
        else:
            no_uf_results.append(r)

    ufs_saved = []
    first_result = {"level": CacheLevel.MISS, "success": False}

    for uf, uf_results in results_by_uf.items():
        per_uf_params = {**params, "ufs": [uf]}
        try:
            result = await save_to_cache(
                user_id, per_uf_params, uf_results, sources,
                fetch_duration_ms=fetch_duration_ms, coverage=coverage,
            )
            if result.get("success"):
                ufs_saved.append(uf)
                if first_result["level"] == CacheLevel.MISS:
                    first_result = result
        except Exception as e:
            logger.warning(f"CRIT-051: Failed to save per-UF cache for {uf}: {e}")

    try:
        await save_to_cache(
            user_id, params, results, sources,
            fetch_duration_ms=fetch_duration_ms, coverage=coverage,
        )
    except Exception as e:
        logger.debug(f"CRIT-051: Combined cache save failed (non-fatal, per-UF already saved): {e}")

    logger.info(
        f"CRIT-051: Per-UF cache saved {len(ufs_saved)}/{len(results_by_uf)} UFs "
        f"({len(results)} total results, {len(no_uf_results)} without UF)"
    )
    first_result["ufs_saved"] = ufs_saved
    return first_result


# ============================================================================
# Per-UF composable cache read
# ============================================================================


async def get_from_cache_composed(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """CRIT-051 AC2: Compose cache results from individual UF entries."""
    from metrics import CACHE_COMPOSITION_TOTAL, CACHE_COMPOSITION_COVERAGE

    ufs = sorted(params.get("ufs", []))
    if not ufs or len(ufs) <= 1:
        return await get_from_cache(user_id, params)

    cached_ufs = []
    missing_ufs = []
    all_results = []
    oldest_cached_at = None
    worst_status = "fresh"
    sources_seen = set()
    cache_levels_seen = set()

    for uf in ufs:
        per_uf_params = {**params, "ufs": [uf]}
        try:
            entry = await get_from_cache(user_id, per_uf_params)
            if entry and entry.get("results"):
                cached_ufs.append(uf)
                all_results.extend(entry["results"])

                entry_cached_at = entry.get("cached_at")
                if entry_cached_at:
                    if oldest_cached_at is None or entry_cached_at < oldest_cached_at:
                        oldest_cached_at = entry_cached_at

                entry_status = entry.get("cache_status", "fresh")
                if entry_status == "expired" or (entry_status == "stale" and worst_status == "fresh"):
                    worst_status = entry_status

                for src in (entry.get("cached_sources") or []):
                    sources_seen.add(src)
                if entry.get("cache_level"):
                    cache_levels_seen.add(entry["cache_level"])
            else:
                missing_ufs.append(uf)
        except Exception as e:
            logger.debug(f"CRIT-051: Per-UF cache read failed for {uf}: {e}")
            missing_ufs.append(uf)

    coverage = len(cached_ufs) / len(ufs) if ufs else 0
    coverage_pct = coverage * 100
    CACHE_COMPOSITION_COVERAGE.observe(coverage_pct)

    if coverage < CACHE_PARTIAL_HIT_THRESHOLD:
        CACHE_COMPOSITION_TOTAL.labels(result="miss").inc()
        logger.info(
            f"CRIT-051: Cache composition MISS — {len(cached_ufs)}/{len(ufs)} UFs "
            f"({coverage_pct:.0f}% < {CACHE_PARTIAL_HIT_THRESHOLD*100:.0f}% threshold)"
        )
        return None

    all_results = _dedup_cross_uf(all_results)

    result_type = "full_hit" if not missing_ufs else "partial_hit"
    CACHE_COMPOSITION_TOTAL.labels(result=result_type).inc()

    logger.info(
        f"CRIT-051: Cache composition {result_type} — {len(cached_ufs)}/{len(ufs)} UFs, "
        f"{len(all_results)} results (deduped)"
    )

    return {
        "results": all_results,
        "cached_at": oldest_cached_at,
        "cached_sources": sorted(sources_seen),
        "cache_age_hours": _compute_age_hours(oldest_cached_at),
        "is_stale": worst_status != "fresh",
        "cache_level": "composed",
        "cache_status": worst_status,
        "cache_priority": "warm",
        "cache_fallback": False,
        "cache_date_range": None,
        "cached_ufs": cached_ufs,
        "missing_ufs": missing_ufs,
        "composition_coverage": coverage_pct,
    }


def _dedup_cross_uf(results: list) -> list:
    """CRIT-051 AC5: Deduplicate results that appear in multiple UFs."""
    seen: dict = {}
    deduped = []
    for r in results:
        key = r.get("codigoCompra") or r.get("numeroControlePNCP", "")
        if not key:
            orgao = (r.get("nomeOrgao") or "").lower().strip()
            obj = " ".join((r.get("objetoCompra") or "")[:100].lower().split())
            key = f"{orgao}|{obj}" if orgao and obj else ""

        if not key:
            deduped.append(r)
            continue

        if key not in seen:
            seen[key] = r
            deduped.append(r)

    return deduped


def _compute_age_hours(cached_at: Optional[str]) -> float:
    """Compute age in hours from an ISO timestamp string."""
    if not cached_at:
        return 0.0
    try:
        dt = datetime.fromisoformat(str(cached_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


# ============================================================================
# Multi-level read
# ============================================================================


async def get_from_cache(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """Retrieve cached results with 3-level fallback (AC2)."""
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    result = await _read_all_levels(user_id, params_hash, params, start)
    if result:
        return result

    from config import CACHE_LEGACY_KEY_FALLBACK
    if CACHE_LEGACY_KEY_FALLBACK:
        legacy_hash = compute_search_hash_without_dates(params)
        if legacy_hash != params_hash:
            result = await _read_all_levels(user_id, legacy_hash, params, start)
            if result:
                result["cache_fallback"] = True
                cached_at = result.get("cached_at")
                result["cache_date_range"] = _format_cache_date_range(cached_at)
                logger.info(
                    f"Cache HIT via legacy key (without dates) for hash "
                    f"{legacy_hash[:12]}... (fallback from {params_hash[:12]})"
                )
                return result

    elapsed = (time.monotonic() - start) * 1000
    from middleware import search_id_var
    _search_id_miss = search_id_var.get("-")
    logger.info(f"Cache MISS all levels [search={_search_id_miss}] for hash {params_hash[:12]}... ({elapsed:.0f}ms)")
    _track_cache_operation("read", False, CacheLevel.MISS, 0, elapsed)
    METRICS_CACHE_MISSES.labels(level="all").inc()
    return None


async def _read_all_levels(
    user_id: str,
    params_hash: str,
    params: dict,
    start: float,
) -> Optional[dict]:
    """STORY-306: Read cache across all levels for a given hash key."""
    # Level 1: Supabase
    try:
        data = await _supa._get_from_supabase(user_id, params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.SUPABASE)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.SUPABASE,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="supabase", freshness=_freshness).inc()
                await _increment_and_reclassify(user_id, params_hash, params, result)
                return result
    except Exception as e:
        report_error(
            e, f"Supabase cache read failed (key={params_hash[:12]})",
            expected=True, tags={"cache_operation": "read", "cache_level": "supabase"}, log=logger,
        )

    # Level 2: Redis/InMemory
    try:
        data = _redis._get_from_redis(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.REDIS)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.REDIS,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="memory", freshness=_freshness).inc()
                try:
                    await _increment_and_reclassify(user_id, params_hash, params, result)
                except Exception:
                    pass
                return result
    except Exception as e:
        logger.error(f"Redis cache read failed: {e}")

    # Level 3: Local file
    try:
        data = _local._get_from_local(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.LOCAL)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.LOCAL,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="local", freshness=_freshness).inc()
                return result
    except Exception as e:
        logger.error(f"Local cache read failed: {e}")

    # GTM-ARCH-002 AC1: Global cross-user fallback
    try:
        global_data = await _supa._get_global_fallback_from_supabase(params)
        if global_data:
            result = _process_cache_hit(global_data, params_hash, CacheLevel.SUPABASE)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                result["cache_level"] = "global"
                _track_cache_operation(
                    "read", True, CacheLevel.SUPABASE,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                METRICS_CACHE_HITS.labels(level="global", freshness=result.get("cache_status", "stale")).inc()
                logger.info(
                    f"Cache HIT global fallback for hash {params_hash[:12]}... "
                    f"({elapsed:.0f}ms, {len(result['results'])} results)"
                )
                return result
    except Exception as e:
        logger.debug(f"Global cache fallback failed: {e}")

    return None


# Cascade read functions live in cache.cascade (DEBT-203: keep manager.py ≤ 600 LOC)
# get_from_cache_cascade and _cascade_read_levels imported above for backward compat.
