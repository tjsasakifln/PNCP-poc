"""Pipeline cache management — extracted from search_pipeline.py (TD-008 AC20).

Handles search results caching (L1 InMemory + L2 Supabase),
cache key computation, stale-while-revalidate, and cache fallback logic.

CRIT-051: Per-UF composable cache — caches results per individual UF so that
warmup (per-UF) and multi-UF searches share the same cache entries.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

from redis_pool import get_fallback_cache
from cache.manager import (
    _dedup_cross_uf,
)
from schemas import DataSourceStatus

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL = 4 * 3600  # 4 hours


def _compute_cache_key(request) -> str:
    """Compute deterministic cache key from search params (excluding dates)."""
    params = {
        "setor_id": request.setor_id,
        "ufs": sorted(request.ufs),
        "status": request.status.value if request.status else None,
        "modalidades": sorted(request.modalidades) if request.modalidades else None,
        "modo_busca": request.modo_busca,
    }
    params_json = json.dumps(params, sort_keys=True)
    return f"search_cache:{hashlib.sha256(params_json.encode()).hexdigest()}"


def _compute_cache_key_per_uf(request, uf: str) -> str:
    """CRIT-051 AC1: Compute cache key for a SINGLE UF."""
    params = {
        "setor_id": request.setor_id,
        "ufs": [uf],
        "status": request.status.value if request.status else None,
        "modalidades": sorted(request.modalidades) if request.modalidades else None,
        "modo_busca": request.modo_busca,
    }
    params_json = json.dumps(params, sort_keys=True)
    return f"search_cache:{hashlib.sha256(params_json.encode()).hexdigest()}"


def _read_cache(cache_key: str):
    """Read from InMemoryCache. Returns parsed dict or None.

    CRIT-056 AC2/AC4: If quality_score < 1.0 and PNCP has recovered,
    marks entry as stale (_swr_stale=True) to trigger background revalidation.
    """
    cache = get_fallback_cache()
    raw = cache.get(cache_key)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    # CRIT-056 AC2: Check quality vs current PNCP health
    qs = data.get("quality_score", 1.0)  # backward compat: assume full if missing
    if qs < 1.0:
        from cron_jobs import get_pncp_cron_status, get_pncp_recovery_epoch
        pncp_status = get_pncp_cron_status().get("status")
        if pncp_status == "healthy":
            data["_swr_stale"] = True
            logger.info(
                f"CRIT-056: Cache HIT (quality={qs}) but primary source recovered "
                f"— marking stale for revalidation"
            )
    # CRIT-056 AC4: Check recovery epoch
    entry_epoch = data.get("recovery_epoch", 0)
    if entry_epoch is not None:
        from cron_jobs import get_pncp_recovery_epoch
        current_epoch = get_pncp_recovery_epoch()
        if entry_epoch < current_epoch:
            data["_swr_stale"] = True
            logger.info(
                f"CRIT-056: Cache entry epoch={entry_epoch} < recovery epoch={current_epoch} "
                f"— marking stale for revalidation"
            )

    return data


def _read_cache_composed(request) -> dict | None:
    """CRIT-051 AC2: Compose InMemory cache results from per-UF entries.

    Returns composed dict with cached_ufs/missing_ufs, or None if insufficient coverage.
    """
    from cache.manager import CACHE_PARTIAL_HIT_THRESHOLD
    from metrics import CACHE_COMPOSITION_TOTAL, CACHE_COMPOSITION_COVERAGE

    ufs = sorted(request.ufs) if request.ufs else []
    if len(ufs) <= 1:
        return None  # Single UF — use regular cache

    cached_ufs = []
    missing_ufs = []
    all_licitacoes = []
    oldest_cached_at = None
    any_stale = False  # CRIT-056: Track if any entry is quality-stale
    worst_quality = 1.0  # CRIT-056: Track worst quality across UF entries

    for uf in ufs:
        key = _compute_cache_key_per_uf(request, uf)
        entry = _read_cache(key)
        if entry and entry.get("licitacoes"):
            cached_ufs.append(uf)
            all_licitacoes.extend(entry["licitacoes"])
            entry_cached_at = entry.get("cached_at")
            if entry_cached_at:
                if oldest_cached_at is None or entry_cached_at < oldest_cached_at:
                    oldest_cached_at = entry_cached_at
            # CRIT-056: Propagate stale flag from quality check
            if entry.get("_swr_stale"):
                any_stale = True
            entry_qs = entry.get("quality_score", 1.0)
            if entry_qs < worst_quality:
                worst_quality = entry_qs
        else:
            missing_ufs.append(uf)

    coverage = len(cached_ufs) / len(ufs) if ufs else 0
    coverage_pct = coverage * 100
    CACHE_COMPOSITION_COVERAGE.observe(coverage_pct)

    if coverage < CACHE_PARTIAL_HIT_THRESHOLD:
        CACHE_COMPOSITION_TOTAL.labels(result="miss").inc()
        return None

    # CRIT-051 AC5: Dedup cross-UF
    all_licitacoes = _dedup_cross_uf(all_licitacoes)

    result_type = "full_hit" if not missing_ufs else "partial_hit"
    CACHE_COMPOSITION_TOTAL.labels(result=result_type).inc()

    logger.info(
        f"CRIT-051: InMemory composition {result_type} — "
        f"{len(cached_ufs)}/{len(ufs)} UFs, {len(all_licitacoes)} results"
        + (f" (quality={worst_quality}, stale={any_stale})" if worst_quality < 1.0 else "")
    )

    result = {
        "licitacoes": all_licitacoes,
        "total": len(all_licitacoes),
        "cached_at": oldest_cached_at,
        "cached_ufs": cached_ufs,
        "missing_ufs": missing_ufs,
        "composition_coverage": coverage_pct,
    }
    # CRIT-056: Propagate quality stale flag to composed result
    if any_stale:
        result["_swr_stale"] = True
    return result


def _write_cache(cache_key: str, data: dict) -> None:
    """Write search results to InMemoryCache with TTL."""
    cache = get_fallback_cache()
    try:
        cache.setex(cache_key, SEARCH_CACHE_TTL, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Failed to write search cache: {e}")


def _write_cache_per_uf(request, results: list, *,
                        quality_score: float = 1.0,
                        sources_succeeded: list | None = None,
                        sources_degraded: list | None = None) -> int:
    """CRIT-051 AC1: Write results to InMemory cache grouped by UF.

    Groups results by their 'uf' field and writes one cache entry per UF.
    CRIT-056 AC1: Propagates quality metadata to per-UF entries.
    Returns number of UFs successfully cached.
    """
    from cron_jobs import get_pncp_recovery_epoch

    results_by_uf: dict[str, list] = {}
    for r in results:
        uf = r.get("uf", "").upper()
        if uf:
            results_by_uf.setdefault(uf, []).append(r)

    ufs_saved = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    _epoch = get_pncp_recovery_epoch()
    for uf, uf_results in results_by_uf.items():
        key = _compute_cache_key_per_uf(request, uf)
        data = {
            "licitacoes": uf_results,
            "total": len(uf_results),
            "cached_at": now_iso,
            "search_params": {
                "setor_id": request.setor_id,
                "ufs": [uf],
                "status": request.status.value if request.status else None,
            },
            # CRIT-056 AC1: Quality metadata
            "quality_score": quality_score,
            "sources_succeeded": sources_succeeded or [],
            "sources_degraded": sources_degraded or [],
            "recovery_epoch": _epoch,
        }
        _write_cache(key, data)
        ufs_saved += 1

    if ufs_saved > 0:
        logger.debug(
            f"CRIT-051: Per-UF InMemory cache wrote {ufs_saved} UFs "
            f"({len(results)} total results, quality={quality_score})"
        )
    return ufs_saved


def _build_cache_params(request) -> dict:
    """Build normalized params dict from BuscaRequest for cache lookup."""
    return {
        "setor_id": request.setor_id,
        "ufs": request.ufs,
        "status": request.status.value if request.status else None,
        "modalidades": request.modalidades,
        "modo_busca": request.modo_busca,
    }


async def _maybe_trigger_revalidation(user_id: str, request, stale_cache: dict | None) -> None:
    """Trigger background revalidation after serving stale cache. Non-blocking."""
    if not stale_cache or not stale_cache.get("is_stale"):
        return
    try:
        from search_cache import trigger_background_revalidation
        await trigger_background_revalidation(
            user_id=user_id,
            params=_build_cache_params(request),
            request_data={
                "ufs": request.ufs,
                "data_inicial": request.data_inicial,
                "data_final": request.data_final,
                "modalidades": request.modalidades,
                "setor_id": request.setor_id,
            },
            search_id=getattr(request, "search_id", None),
        )
    except Exception as e:
        logger.debug(f"Revalidation trigger failed (non-fatal): {e}")


def _build_degraded_detail(ctx) -> dict:
    """Build SSE degraded event detail dict from SearchContext."""
    detail: dict = {}
    if ctx.cached_at:
        try:
            cached_dt = datetime.fromisoformat(ctx.cached_at.replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - cached_dt).total_seconds() / 3600
            detail["cache_age_hours"] = round(age_hours, 1)
        except (ValueError, TypeError):
            pass
    if ctx.cache_level:
        detail["cache_level"] = ctx.cache_level

    sources_failed = []
    sources_ok = []
    if ctx.data_sources:
        for ds in ctx.data_sources:
            if ds.status in ("error", "timeout"):
                sources_failed.append(ds.source)
            elif ds.status == "ok":
                sources_ok.append(ds.source)
    detail["sources_failed"] = sources_failed
    detail["sources_ok"] = sources_ok

    total_ufs = len(ctx.request.ufs) if ctx.request else 0
    succeeded = len(ctx.succeeded_ufs) if ctx.succeeded_ufs else 0
    detail["coverage_pct"] = int((succeeded / total_ufs * 100) if total_ufs > 0 else 0)

    return detail


def apply_stale_cache(ctx, stale_cache: dict, degradation_reason: str,
                      response_state: str = "cached", source_errors: dict | None = None) -> None:
    """Apply stale cache results to search context — shared helper for all fetch failure paths."""
    ctx.licitacoes_raw = stale_cache["results"]
    ctx.cached = True
    ctx.cached_at = stale_cache.get("cached_at")
    ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
    ctx.cache_status = (
        stale_cache.get("cache_status", "stale")
        if isinstance(stale_cache.get("cache_status"), str)
        else ("stale" if stale_cache.get("is_stale") else "fresh")
    )
    ctx.cache_level = stale_cache.get("cache_level", "supabase")
    ctx.cache_fallback = stale_cache.get("cache_fallback", False)
    ctx.cache_date_range = stale_cache.get("cache_date_range")
    ctx.is_partial = True
    ctx.response_state = response_state
    ctx.degradation_reason = degradation_reason

    if source_errors:
        ctx.data_sources = [
            DataSourceStatus(source=src, status="error", records=0)
            for src in source_errors
        ]
        ctx.source_stats_data = [
            {"source_code": src, "record_count": 0, "duration_ms": 0,
             "error": err, "status": "error"}
            for src, err in source_errors.items()
        ]
    else:
        ctx.data_sources = []
        ctx.source_stats_data = []


def set_empty_failure(ctx, degradation_reason: str, guidance: str,
                      source_errors: dict | None = None) -> None:
    """Set empty failure state on search context — shared helper for no-cache failure paths."""
    ctx.licitacoes_raw = []
    ctx.is_partial = True
    ctx.response_state = "empty_failure"
    ctx.degradation_guidance = guidance
    ctx.degradation_reason = degradation_reason

    if source_errors:
        ctx.data_sources = [
            DataSourceStatus(source=src, status="error", records=0)
            for src in source_errors
        ]
        ctx.source_stats_data = [
            {"source_code": src, "record_count": 0, "duration_ms": 0,
             "error": err, "status": "error"}
            for src, err in source_errors.items()
        ]
    else:
        ctx.data_sources = []
        ctx.source_stats_data = []
