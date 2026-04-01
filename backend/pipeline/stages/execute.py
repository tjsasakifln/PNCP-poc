"""Stage 3: ExecuteSearch — fetch procurement data from APIs.

Extracted from SearchPipeline.stage_execute, _execute_multi_source,
and _execute_pncp_only (DEBT-015 SYS-002).
"""

import asyncio
import json
import logging
import time as sync_time_module
from datetime import datetime, timezone as _tz

from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
from search_context import SearchContext
from schemas import DataSourceStatus
from pncp_client import get_circuit_breaker, PNCPDegradedError, ParallelFetchResult
from consolidation import AllSourcesFailedError
from fastapi import HTTPException
from metrics import (
    CACHE_HITS, CACHE_MISSES, FETCH_DURATION,
    SOURCE_DEGRADATION_TOTAL, BIDS_PROCESSED_TOTAL,
)
from pipeline.cache_manager import (
    SEARCH_CACHE_TTL,
    _compute_cache_key,
    _read_cache,
    _read_cache_composed,
    _write_cache,
    _write_cache_per_uf,
    _build_cache_params,
    _maybe_trigger_revalidation,
)

logger = logging.getLogger(__name__)


import quota  # noqa: E402
from status_inference import enriquecer_com_status_inferido  # noqa: E402
from cache.cascade import get_from_cache_cascade  # noqa: E402


async def stage_execute(pipeline, ctx: SearchContext) -> None:
    """Fetch procurement data from PNCP API (and optionally other sources)."""
    import os

    # CRIT-002 AC8: Track pipeline stage
    if ctx.session_id:
        asyncio.create_task(
            quota.update_search_session_status(ctx.session_id, pipeline_stage="execute")
        )

    deps = pipeline.deps
    request = ctx.request

    # DATALAKE: Shortcut to local DB query when DATALAKE_QUERY_ENABLED=true.
    # Returns records in identical format to _normalize_item() so all downstream
    # stages (filter, LLM, Excel) work without modification.
    try:
        from ingestion.config import DATALAKE_QUERY_ENABLED
        if DATALAKE_QUERY_ENABLED:
            from datalake_query import query_datalake
            logger.info(
                f"[stage_execute] DATALAKE_QUERY_ENABLED — querying local DB "
                f"(ufs={request.ufs}, {request.data_inicial}/{request.data_final})"
            )
            # Resolve sector keywords for full-text search
            _keywords: list[str] = []
            _custom_terms: list[str] = getattr(request, "termos_customizados", None) or []
            try:
                from sectors import get_sector
                if request.setor_id:
                    sector = get_sector(request.setor_id)
                    if sector and sector.keywords:
                        _keywords = list(sector.keywords)
            except Exception:
                pass

            ctx.licitacoes_raw = await query_datalake(
                ufs=request.ufs,
                data_inicial=request.data_inicial,
                data_final=request.data_final,
                modalidades=request.modalidades,
                keywords=_keywords or None,
                custom_terms=_custom_terms or None,
                valor_min=getattr(request, "valor_min", None),
                valor_max=getattr(request, "valor_max", None),
                modo_busca=getattr(request, "modo_busca", "publicacao"),
            )
            ctx.cached = False
            ctx.cache_status = "datalake"
            ctx.source_stats_data = [{"source_code": "datalake", "record_count": len(ctx.licitacoes_raw), "duration_ms": 0, "status": "success"}]
            BIDS_PROCESSED_TOTAL.labels(source="datalake").inc(len(ctx.licitacoes_raw))
            logger.info(
                f"[stage_execute] Datalake returned {len(ctx.licitacoes_raw)} records"
            )
            if len(ctx.licitacoes_raw) == 0:
                logger.warning(
                    "[stage_execute] Datalake returned 0 records — falling through to live API"
                )
                # Reset datalake state so live API sources populate ctx correctly
                ctx.licitacoes_raw = []
                ctx.cache_status = None
                ctx.source_stats_data = []
            else:
                return
    except ImportError:
        pass  # ingestion module not installed — fall through to live API
    except Exception as _dl_err:
        logger.warning(
            f"[stage_execute] Datalake query failed (falling back to live API): {_dl_err}"
        )

    # STORY-257A AC8-10: Search results cache
    cache_key = _compute_cache_key(request)

    # AC10: Respect force_fresh flag
    if not request.force_fresh:
        # CRIT-051 AC2: Try composed per-UF cache first (multi-UF requests)
        composed = _read_cache_composed(request)
        if composed and composed.get("licitacoes"):
            logger.info(
                f"CRIT-051: Composed cache HIT — "
                f"{len(composed.get('cached_ufs', []))} UFs cached, "
                f"{len(composed.get('missing_ufs', []))} missing, "
                f"{len(composed['licitacoes'])} results"
            )
            missing_ufs = composed.get("missing_ufs", [])
            if not missing_ufs:
                # Full hit — all UFs from cache
                ctx.licitacoes_raw = composed["licitacoes"]
                ctx.cached = True
                ctx.cached_at = composed.get("cached_at")
                ctx.cache_status = "fresh"
                ctx.cache_level = "composed"
                CACHE_HITS.labels(level="composed", freshness="fresh").inc()
                # CRIT-056 AC2: Quality-stale -> serve but trigger revalidation
                if composed.get("_swr_stale") and ctx.user and ctx.user.get("id"):
                    from metrics import CACHE_QUALITY_REVALIDATION_TOTAL
                    from cache.swr import trigger_background_revalidation as _trigger_reval
                    CACHE_QUALITY_REVALIDATION_TOTAL.inc()
                    _cache_params = _build_cache_params(request)
                    _request_data = {
                        "ufs": request.ufs,
                        "data_inicial": request.data_inicial,
                        "data_final": request.data_final,
                        "modalidades": request.modalidades,
                        "setor_id": request.setor_id,
                    }
                    asyncio.create_task(
                        _trigger_reval(
                            user_id=ctx.user["id"],
                            params=_cache_params,
                            request_data=_request_data,
                        )
                    )
                return
            else:
                # CRIT-051 AC3: Partial hit — store cached results, fetch missing UFs only
                ctx._composed_cached_results = composed["licitacoes"]
                ctx._missing_ufs = missing_ufs
                ctx._cached_ufs = composed.get("cached_ufs", [])
                logger.info(
                    f"CRIT-051: Hybrid fetch — {len(ctx._cached_ufs)} UFs from cache, "
                    f"{len(missing_ufs)} from live sources"
                )

        cached = _read_cache(cache_key)
        if cached:
            logger.debug(f"Cache HIT for search (cached_at={cached.get('cached_at', 'unknown')})")
            ctx.licitacoes_raw = cached.get("licitacoes", [])
            ctx.cached = True
            ctx.cached_at = cached.get("cached_at")
            ctx.cache_status = "fresh"  # InMemory cache is always fresh (< 6h TTL)
            ctx.cache_level = "redis"  # InMemory serves as L2 cache
            CACHE_HITS.labels(level="memory", freshness="fresh").inc()
            # CRIT-056 AC2: Quality-stale -> serve but trigger revalidation
            if cached.get("_swr_stale") and ctx.user and ctx.user.get("id"):
                from metrics import CACHE_QUALITY_REVALIDATION_TOTAL
                from cache.swr import trigger_background_revalidation as _trigger_reval
                CACHE_QUALITY_REVALIDATION_TOTAL.inc()
                _cache_params = _build_cache_params(request)
                _request_data = {
                    "ufs": request.ufs,
                    "data_inicial": request.data_inicial,
                    "data_final": request.data_final,
                    "modalidades": request.modalidades,
                    "setor_id": request.setor_id,
                }
                asyncio.create_task(
                    _trigger_reval(
                        user_id=ctx.user["id"],
                        params=_cache_params,
                        request_data=_request_data,
                    )
                )
            # Skip the actual fetch — go straight to filtering
            return
        else:
            CACHE_MISSES.labels(level="memory").inc()

        # STORY-282 AC3: Cache-first — check Supabase/cascade for stale cache
        # If stale cache exists, return it IMMEDIATELY and dispatch background refresh
        if ctx.user and ctx.user.get("id"):
            try:
                from cache.swr import trigger_background_revalidation
                _cache_params = {
                    "setor_id": request.setor_id,
                    "ufs": request.ufs,
                    "status": request.status.value if request.status else None,
                    "modalidades": request.modalidades,
                    "modo_busca": request.modo_busca if hasattr(request, "modo_busca") else None,
                }
                _stale = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_cache_params,
                )
                if _stale and _stale.get("results"):
                    _age_h = _stale.get("cache_age_hours", 0)
                    logger.info(
                        f"STORY-282: Cache-first — serving {len(_stale['results'])} results "
                        f"from {_stale.get('cache_level', 'unknown')} ({_age_h:.1f}h old). "
                        f"Background revalidation dispatched."
                    )
                    ctx.licitacoes_raw = _stale["results"]
                    ctx.cached = True
                    ctx.cached_at = _stale.get("cached_at")
                    ctx.cached_sources = _stale.get("cached_sources", ["PNCP"])
                    ctx.cache_status = _stale.get("cache_status", "stale")
                    ctx.cache_level = _stale.get("cache_level", "supabase")
                    ctx.cache_fallback = _stale.get("cache_fallback", False)
                    ctx.cache_date_range = _stale.get("cache_date_range")
                    ctx.response_state = "cached"
                    CACHE_HITS.labels(
                        level=_stale.get("cache_level", "supabase"),
                        freshness=_stale.get("cache_status", "stale"),
                    ).inc()

                    # Dispatch background revalidation (fire-and-forget)
                    _request_data = {
                        "ufs": request.ufs,
                        "data_inicial": request.data_inicial,
                        "data_final": request.data_final,
                        "modalidades": request.modalidades,
                    }
                    asyncio.create_task(
                        trigger_background_revalidation(
                            user_id=ctx.user["id"],
                            params=_cache_params,
                            request_data=_request_data,
                        )
                    )
                    return
            except Exception as cache_first_err:
                logger.debug(f"STORY-282: Cache-first check failed (proceeding with fresh fetch): {cache_first_err}")

    enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "true").lower() == "true"
    ctx.source_stats_data = None

    use_parallel = len(request.ufs) > 1
    status_value = request.status.value if request.status else None
    modalidades_to_fetch = request.modalidades if request.modalidades else None

    # SSE: Starting fetch
    if ctx.tracker:
        msg = f"Iniciando análise em {len(request.ufs)} estados..."
        if enable_multi_source:
            msg += " (multi-fonte ativo)"
        await ctx.tracker.emit("fetching", 10, msg)

    # Build per-UF progress callbacks for SSE
    uf_progress_callback = None
    uf_status_callback = None
    if ctx.tracker:
        async def uf_progress_callback(uf: str, items_count: int):
            await ctx.tracker.emit_uf_complete(uf, items_count)

        # STORY-257A AC6: Per-UF status callback for detailed tracking grid
        async def uf_status_callback(uf: str, status: str, **detail):
            await ctx.tracker.emit_uf_status(uf, status, **detail)

    # GTM-FIX-029 AC16/AC17: Raised from 4min->6min, configurable via env
    # Hierarchy: FE proxy (480s) > Pipeline (360s) > Consolidation (300s) > Per-Source (180s) > Per-UF (90s)
    FETCH_TIMEOUT = int(os.environ.get("SEARCH_FETCH_TIMEOUT", str(6 * 60)))  # 6 minutes

    # CRIT-051 AC3: Hybrid fetch — only fetch missing UFs if partial cache hit
    _hybrid_ufs = getattr(ctx, "_missing_ufs", None)

    if enable_multi_source:
        await _execute_multi_source(
            pipeline, ctx, request, deps, modalidades_to_fetch, status_value,
            uf_progress_callback, FETCH_TIMEOUT,
            uf_status_callback=uf_status_callback,
            ufs_override=_hybrid_ufs,
        )
    else:
        await _execute_pncp_only(
            pipeline, ctx, request, deps, use_parallel, modalidades_to_fetch,
            status_value, uf_progress_callback, FETCH_TIMEOUT,
            uf_status_callback=uf_status_callback,
        )

    fetch_elapsed = sync_time_module.time() - ctx.start_time
    logger.info(f"Fetched {len(ctx.licitacoes_raw)} raw bids in {fetch_elapsed:.2f}s")
    FETCH_DURATION.labels(source="pipeline").observe(fetch_elapsed)

    # CRIT-002 AC8: Update raw_count after fetch
    if ctx.session_id and ctx.licitacoes_raw:
        asyncio.create_task(
            quota.update_search_session_status(
                ctx.session_id, raw_count=len(ctx.licitacoes_raw)
            )
        )

    # SSE: Fetch complete
    if ctx.tracker:
        await ctx.tracker.emit(
            "fetching", 55,
            f"Busca concluida: {len(ctx.licitacoes_raw)} licitacoes encontradas",
            total_raw=len(ctx.licitacoes_raw),
        )

    # Enrich with inferred status
    logger.debug("Enriching bids with inferred status...")
    enriquecer_com_status_inferido(ctx.licitacoes_raw)
    logger.debug(f"Status inference complete for {len(ctx.licitacoes_raw)} bids")

    # CRIT-071: Emit partial_data SSE event with raw results before filtering
    if ctx.tracker and ctx.licitacoes_raw:
        from config import get_feature_flag as _gff_071
        if _gff_071("PARTIAL_DATA_SSE_ENABLED"):
            await ctx.tracker.emit_partial_data(
                licitacoes=ctx.licitacoes_raw,
                batch_index=1,
                ufs_completed=list(ctx.succeeded_ufs or ctx.request.ufs),
                is_final=False,
            )
            ctx.tracker.add_partial_licitacoes(ctx.licitacoes_raw)

    # CRIT-051 AC3: Merge cached results with fresh results (hybrid fetch)
    _composed_cached = getattr(ctx, "_composed_cached_results", None)
    if _composed_cached:
        from cache.manager import _dedup_cross_uf
        _cached_count = len(_composed_cached)
        _fresh_count = len(ctx.licitacoes_raw)
        ctx.licitacoes_raw = _dedup_cross_uf(_composed_cached + ctx.licitacoes_raw)
        logger.info(
            f"CRIT-051: Hybrid merge — {_cached_count} cached + {_fresh_count} fresh "
            f"= {len(ctx.licitacoes_raw)} after dedup"
        )
        # Clean up temporary attributes
        del ctx._composed_cached_results
        if hasattr(ctx, "_missing_ufs"):
            del ctx._missing_ufs
        if hasattr(ctx, "_cached_ufs"):
            del ctx._cached_ufs

    # STORY-257A AC8 + GTM-FIX-010 AC3: Cache write-through on successful fetch
    # CRIT-056 AC1: Compute quality score based on source status
    _sources_ok = (
        [ds.source for ds in ctx.data_sources if ds.status == "succeeded"]
        if ctx.data_sources else []
    )
    _sources_deg = list(ctx.sources_degraded or [])
    if "PNCP" in _sources_ok:
        _quality = 1.0 if not _sources_deg else 0.7
    elif _sources_ok:
        _quality = 0.3  # No primary, but secondary ok
    else:
        _quality = 0.0

    # CRIT-056 AC5: Track quality metrics
    from metrics import CACHE_QUALITY_WRITE_TOTAL, CACHE_QUALITY_SCORE
    _q_bucket = "full" if _quality >= 1.0 else ("partial" if _quality > 0 else "empty")

    # CRIT-056 AC3: Don't cache empty results from degraded sources
    if _quality < 0.5 and not ctx.licitacoes_raw:
        logger.info("CRIT-056: Cache SKIP — sources degraded and zero results")
        CACHE_QUALITY_WRITE_TOTAL.labels(quality_bucket="empty").inc()
    elif ctx.licitacoes_raw and len(ctx.licitacoes_raw) > 0:
        from cron_jobs import get_pncp_recovery_epoch
        cache_data = {
            "licitacoes": ctx.licitacoes_raw,
            "total": len(ctx.licitacoes_raw),
            "cached_at": datetime.now(_tz.utc).isoformat(),
            "search_params": {
                "setor_id": request.setor_id,
                "ufs": request.ufs,
                "status": request.status.value if request.status else None,
            },
            # CRIT-056 AC1: Quality metadata
            "quality_score": _quality,
            "sources_succeeded": _sources_ok,
            "sources_degraded": _sources_deg,
            "recovery_epoch": get_pncp_recovery_epoch(),
        }
        _write_cache(cache_key, cache_data)
        # CRIT-051 AC1: Also write per-UF entries for composable cache
        _write_cache_per_uf(request, ctx.licitacoes_raw, quality_score=_quality,
                            sources_succeeded=_sources_ok, sources_degraded=_sources_deg)
        CACHE_QUALITY_WRITE_TOTAL.labels(quality_bucket=_q_bucket).inc()
        CACHE_QUALITY_SCORE.observe(_quality)
        logger.debug(f"Cache WRITE: {len(ctx.licitacoes_raw)} results cached (TTL={SEARCH_CACHE_TTL}s, quality={_quality})")

        # GTM-FIX-010 AC3: Also persist to Supabase for cross-restart resilience
        # B-03 AC2/AC6/AC7: Include health metadata (fetch_duration_ms, coverage)
        if ctx.user and ctx.user.get("id"):
            sources = (
                [ds.source for ds in ctx.data_sources if ds.records > 0]
                if ctx.data_sources else ["PNCP"]
            )
            fetch_elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)
            coverage_data = {
                "succeeded_ufs": list(ctx.succeeded_ufs or []),
                "failed_ufs": list(ctx.failed_ufs or []),
                "total_requested": len(request.ufs),
            }
            _cache_params = {
                "setor_id": request.setor_id,
                "ufs": request.ufs,
                "status": request.status.value if request.status else None,
                "modalidades": request.modalidades,
                "modo_busca": request.modo_busca,
            }
            try:
                # CRIT-051 AC1: Save per-UF to Supabase (also saves combined for retrocompat)
                from cache.manager import save_to_cache_per_uf
                await save_to_cache_per_uf(
                    user_id=ctx.user["id"],
                    params=_cache_params,
                    results=ctx.licitacoes_raw,
                    sources=sources,
                    fetch_duration_ms=fetch_elapsed_ms,
                    coverage=coverage_data,
                )
            except Exception as e:
                logger.warning(f"Supabase cache write failed (non-fatal): {e}")


async def _execute_multi_source(
    pipeline, ctx, request, deps, modalidades_to_fetch, status_value,
    uf_progress_callback, fetch_timeout, uf_status_callback=None,
    ufs_override: list[str] | None = None,
):
    """Multi-source consolidation path (STORY-177).

    Args:
        ufs_override: CRIT-051 AC3 — if set, fetch only these UFs (hybrid fetch).
    """

    logger.debug("Multi-source fetch enabled, using ConsolidationService")
    from consolidation import ConsolidationService
    from clients.compras_gov_client import ComprasGovAdapter
    from clients.portal_compras_client import PortalComprasAdapter
    from source_config.sources import get_source_config
    from pncp_client import PNCPLegacyAdapter

    source_config = get_source_config()

    # STORY-257A AC13: Only include sources that are actually available
    available_sources = source_config.get_enabled_source_configs()
    logger.debug(f"Available sources: {[s.code.value for s in available_sources]}")
    pending_creds = source_config.get_pending_credentials()
    if pending_creds:
        logger.warning(f"Sources with pending credentials: {pending_creds}")

    adapters = {}
    skipped_sources: list[str] = []  # STORY-305 AC9: CB OPEN -> skip source

    # STORY-305 AC8-AC9: Check circuit breaker before adding each source
    pncp_cb = get_circuit_breaker("pncp")
    pcp_cb = get_circuit_breaker("pcp")
    comprasgov_cb = get_circuit_breaker("comprasgov")

    # CRIT-051 AC3: Use overridden UFs for hybrid fetch
    _fetch_ufs = ufs_override if ufs_override else request.ufs

    if source_config.pncp.enabled:
        if pncp_cb.is_degraded:
            logger.warning("[MULTI-SOURCE] PNCP circuit breaker OPEN — skipping source")
            skipped_sources.append("PNCP")
        else:
            adapters["PNCP"] = PNCPLegacyAdapter(
                ufs=_fetch_ufs,
                modalidades=modalidades_to_fetch,
                status=status_value,
                on_uf_complete=uf_progress_callback,
                on_uf_status=uf_status_callback,
            )

    if source_config.compras_gov.enabled:
        from config import COMPRASGOV_CB_ENABLED, COMPRASGOV_ENABLED
        if not COMPRASGOV_ENABLED:
            logger.info("[MULTI-SOURCE] ComprasGov DISABLED via COMPRASGOV_ENABLED flag — skipping")
            skipped_sources.append("COMPRAS_GOV")
        elif COMPRASGOV_CB_ENABLED and comprasgov_cb.is_degraded:
            logger.warning("[MULTI-SOURCE] ComprasGov circuit breaker OPEN — skipping source")
            skipped_sources.append("COMPRAS_GOV")
        else:
            adapters["COMPRAS_GOV"] = ComprasGovAdapter(
                timeout=source_config.compras_gov.timeout
            )

    # GTM-FIX-024 T2: PCP v2 API is public — no API key required
    # CRIT-047 AC8: Also check health registry — skip if source is DOWN
    if source_config.portal.enabled:
        from source_config.sources import source_health_registry as _pcp_health
        pcp_health_status = _pcp_health.get_status("PORTAL_COMPRAS")
        if pcp_cb.is_degraded:
            logger.warning("[MULTI-SOURCE] PCP circuit breaker OPEN — skipping source")
            skipped_sources.append("PORTAL_COMPRAS")
        elif pcp_health_status == "down":
            logger.warning("[MULTI-SOURCE] PCP health registry DOWN — skipping source")
            skipped_sources.append("PORTAL_COMPRAS")
        else:
            adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                timeout=source_config.portal.timeout,
            )

    # STORY-305 AC10: If ALL sources are CB OPEN, pipeline will get no adapters.
    # ConsolidationService handles empty adapters -> AllSourcesFailedError -> cache stale path.
    if skipped_sources:
        logger.info(f"[MULTI-SOURCE] CB-skipped sources: {skipped_sources}")

    # GTM-FIX-025 T1: ComprasGov v1 is permanently unstable (503s).
    # Removed as fallback — PNCP+PCP provide sufficient coverage.
    # Will be restored when ComprasGov v3 migration is ready (GTM-FIX-026).
    fallback_adapter = None

    # STORY-296: Inject per-source bulkheads for concurrency isolation
    from bulkhead import get_all_bulkheads
    bulkheads = get_all_bulkheads()

    consolidation_svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=source_config.consolidation.timeout_per_source,
        timeout_global=source_config.consolidation.timeout_global,
        fail_on_all_errors=source_config.consolidation.fail_on_all_errors,
        fallback_adapter=fallback_adapter,
        bulkheads=bulkheads,
    )

    source_complete_cb = None
    if ctx.tracker:
        def source_complete_cb(src_code, count, error):
            logger.debug(f"[MULTI-SOURCE] {src_code}: {count} records, error={error}")

    # GTM-STAB-003 AC3: Early return callback emits progress event
    early_return_cb = None
    if ctx.tracker:
        async def early_return_cb(ufs_completed, ufs_pending):
            await ctx.tracker.emit(
                "fetching", 55,
                "Retornando resultados parciais...",
                ufs_completed=ufs_completed,
                ufs_pending=ufs_pending,
                early_return=True,
            )

    # STORY-295 AC1-AC8: Progressive results callback
    # Tracks total across sources for incremental count
    _progressive_total = [0]
    _completed_sources: list[str] = []
    _all_source_codes = list(adapters.keys())
    source_done_cb = None
    if ctx.tracker:
        async def source_done_cb(src_code, status, legacy_records, duration_ms, error):
            _completed_sources.append(src_code)
            _pending = [s for s in _all_source_codes if s not in _completed_sources]

            if status in ("success", "partial"):
                _progressive_total[0] += len(legacy_records)
                # AC1-AC2: Emit partial results with items
                await ctx.tracker.emit_progressive_results(
                    source=src_code,
                    items_count=len(legacy_records),
                    total_so_far=_progressive_total[0],
                    sources_completed=list(_completed_sources),
                    sources_pending=_pending,
                )
                # AC7: Emit source_complete
                await ctx.tracker.emit_source_complete(
                    source=src_code,
                    status=status,
                    record_count=len(legacy_records),
                    duration_ms=duration_ms,
                    error=error,
                )
            elif status in ("error", "timeout"):
                # AC8: Emit source_error
                await ctx.tracker.emit_source_error(
                    source=src_code,
                    error=error or f"Source {src_code} failed with status={status}",
                    duration_ms=duration_ms,
                )
                # AC7: Also emit source_complete for timeout/error
                await ctx.tracker.emit_source_complete(
                    source=src_code,
                    status=status,
                    record_count=0,
                    duration_ms=duration_ms,
                    error=error,
                )

    try:
        consolidation_result = await asyncio.wait_for(
            consolidation_svc.fetch_all(
                data_inicial=request.data_inicial,
                data_final=request.data_final,
                ufs=set(_fetch_ufs),
                on_source_complete=source_complete_cb,
                on_early_return=early_return_cb,
                on_source_done=source_done_cb,
            ),
            timeout=fetch_timeout,
        )
        ctx.licitacoes_raw = consolidation_result.records
        ctx.source_stats_data = [
            {
                "source_code": sr.source_code,
                "record_count": sr.record_count,
                "duration_ms": sr.duration_ms,
                "error": sr.error,
                "status": sr.status,
                "skipped_reason": sr.skipped_reason,
            }
            for sr in consolidation_result.source_results
        ]

        # CRIT-053 AC1/AC3: Detect degraded sources — canary failed + 0 records
        canary_info = getattr(ctx, "_pncp_canary_result", None)
        if canary_info and not canary_info.get("ok", True):
            for sr in consolidation_result.source_results:
                if sr.source_code == "PNCP" and sr.record_count == 0 and sr.status == "success":
                    sr.status = "degraded"
                    sr.skipped_reason = "health_canary_timeout"
                    ctx.sources_degraded.append("PNCP")
                    # Update source_stats_data to reflect degraded status
                    for stat in ctx.source_stats_data:
                        if stat["source_code"] == "PNCP":
                            stat["status"] = "degraded"
                            stat["skipped_reason"] = "health_canary_timeout"
                    # CRIT-053 AC7: Metrics
                    SOURCE_DEGRADATION_TOTAL.labels(
                        source="PNCP", reason="health_canary_timeout"
                    ).inc()
                    logger.warning(
                        "CRIT-053: PNCP marked as degraded (canary failed, 0 records returned, "
                        "cron_status=%s)", canary_info.get("cron_status", "unknown")
                    )

        # STORY-305 AC3: Record CB success/failure per source after consolidation
        # Each source result counts as exactly 1 CB event (retry exhaustion = 1 failure, not N)
        _cb_map = {"PNCP": pncp_cb, "PORTAL_COMPRAS": pcp_cb, "COMPRAS_GOV": comprasgov_cb}
        for sr in consolidation_result.source_results:
            _src_cb = _cb_map.get(sr.source_code)
            if _src_cb:
                if sr.status == "success":
                    asyncio.ensure_future(_src_cb.record_success())
                elif sr.status in ("error", "timeout", "degraded"):
                    asyncio.ensure_future(_src_cb.record_failure())

        # STORY-252 T8: Map consolidation degradation state to pipeline context
        ctx.is_partial = consolidation_result.is_partial
        ctx.degradation_reason = consolidation_result.degradation_reason

        # CRIT-053 AC2: If primary source (PNCP) is degraded, force is_partial=true
        if ctx.sources_degraded and not ctx.is_partial:
            ctx.is_partial = True
            ctx.degradation_reason = (
                f"PNCP health canary timeout (cron status: "
                f"{canary_info.get('cron_status', 'unknown') if canary_info else 'unknown'})"
            )
        # GTM-STAB-003 AC3: Propagate UF tracking from consolidation
        if consolidation_result.ufs_completed:
            ctx.succeeded_ufs = consolidation_result.ufs_completed
        if consolidation_result.ufs_pending:
            ctx.failed_ufs = consolidation_result.ufs_pending
        ctx.data_sources = [
            DataSourceStatus(
                source=sr.source_code,
                status="ok" if sr.status == "success" else sr.status,
                records=sr.record_count,
            )
            for sr in consolidation_result.source_results
        ]

        # CRIT-053 AC1: Ensure degraded sources show "degraded" in data_sources too
        if ctx.sources_degraded:
            for ds in ctx.data_sources:
                if ds.source in ctx.sources_degraded:
                    ds.status = "degraded"

        # GTM-FIX-004: Collect per-source truncation flags from adapters
        truncation_details = {}
        for code, adapter in adapters.items():
            if hasattr(adapter, "was_truncated"):
                truncation_details[code.lower()] = adapter.was_truncated
                if adapter.was_truncated:
                    ctx.is_truncated = True
                    # Merge truncated UFs from PNCP adapter
                    if hasattr(adapter, "truncated_ufs") and adapter.truncated_ufs:
                        if ctx.truncated_ufs is None:
                            ctx.truncated_ufs = []
                        ctx.truncated_ufs.extend(adapter.truncated_ufs)

        if any(truncation_details.values()):
            ctx.truncation_details = truncation_details
            logger.warning(
                f"GTM-FIX-004: Multi-source truncation detected: {truncation_details}"
            )

        logger.info(
            f"Multi-source fetch: {consolidation_result.total_before_dedup} raw -> "
            f"{consolidation_result.total_after_dedup} deduped "
            f"({consolidation_result.duplicates_removed} dupes removed)"
            f"{' [PARTIAL]' if ctx.is_partial else ''}"
        )

        # STORY-358 AC1: Increment bids processed counter per source
        for sr in consolidation_result.source_results:
            if sr.record_count > 0:
                BIDS_PROCESSED_TOTAL.labels(source=sr.source_code).inc(sr.record_count)
    except AllSourcesFailedError as e:
        # CRIT-002 AC13: Update session on AllSourcesFailedError
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(
                    ctx.session_id, pipeline_stage="execute",
                    response_state="empty_failure",
                )
            )

        # GTM-FIX-010 AC4/AC16r/AC17r: All sources failed — try Supabase cache fallback
        # GTM-RESILIENCE-E02: centralized reporting (no double stdout+Sentry)
        report_error(
            e, "All sources failed during multi-source fetch",
            expected=True, tags={"data_source": "all_sources"}, log=logger,
        )

        # A-03 AC7: Unified cache cascade (L2 -> L1 -> L3)
        # P1.3: If cascade returns nothing (no fresh/stale cache), retry with allow_expired=True
        stale_cache = None
        expired_cache_used = False
        if ctx.user and ctx.user.get("id"):
            try:
                stale_cache = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_build_cache_params(request),
                )
            except Exception as cache_err:
                logger.warning(f"Cache cascade failed after AllSourcesFailedError: {cache_err}")

            if stale_cache is None:
                # P1.3: Last-resort — try expired cache (>24h) rather than returning empty
                try:
                    stale_cache = await get_from_cache_cascade(
                        user_id=ctx.user["id"],
                        params=_build_cache_params(request),
                        allow_expired=True,
                    )
                    if stale_cache:
                        expired_cache_used = True
                        logger.warning(json.dumps({
                            "event": "cache_expired_served_as_fallback",
                            "cache_age_hours": stale_cache["cache_age_hours"],
                            "results_count": len(stale_cache.get("results", [])),
                            "cache_level": str(stale_cache.get("cache_level", "unknown")),
                            "reason": "all_sources_failed_no_fresh_cache",
                        }))
                except Exception as expired_err:
                    logger.warning(f"Expired cache fallback failed after AllSourcesFailedError: {expired_err}")

        if stale_cache:
            # AC5: Serve stale/expired cache with cache metadata
            _cache_age = stale_cache["cache_age_hours"]
            if expired_cache_used:
                # P1.3: Expired cache — distinct state so frontend can show appropriate warning
                logger.warning(
                    f"Serving expired cache ({_cache_age}h old) as last-resort fallback "
                    f"after all sources failed — response_state=degraded_expired"
                )
                ctx.response_state = "degraded_expired"  # P1.3
                ctx.degradation_guidance = (
                    f"Fontes de dados estão temporariamente indisponíveis. "
                    f"Exibindo dados do cache com {_cache_age:.0f}h — podem estar desatualizados."
                )
            else:
                logger.info(
                    f"Serving stale cache ({_cache_age}h old) "
                    f"after all sources failed"
                )
                ctx.response_state = "cached"  # GTM-RESILIENCE-A01 AC6
            ctx.licitacoes_raw = stale_cache["results"]
            ctx.cached = True
            ctx.cached_at = stale_cache["cached_at"]
            ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
            ctx.cache_status = stale_cache.get("cache_status", "stale") if isinstance(stale_cache.get("cache_status"), str) else ("stale" if stale_cache.get("is_stale") else "fresh")
            ctx.cache_level = stale_cache.get("cache_level", "supabase")  # AC8: real level from cascade
            ctx.cache_fallback = stale_cache.get("cache_fallback", False)
            ctx.cache_date_range = stale_cache.get("cache_date_range")
            ctx.is_partial = True
            ctx.degradation_reason = str(e)
            ctx.data_sources = [
                DataSourceStatus(
                    source=src,
                    status="error",
                    records=0,
                )
                for src in e.source_errors
            ]
            ctx.source_stats_data = [
                {
                    "source_code": src,
                    "record_count": 0,
                    "duration_ms": 0,
                    "error": err,
                    "status": "error",
                }
                for src, err in e.source_errors.items()
            ]
            # B-01: Background revalidation
            await _maybe_trigger_revalidation(ctx.user["id"], request, stale_cache)
        else:
            # AC6/AC17r: No cache — return empty with degradation info
            logger.warning("No stale cache available — returning empty results")
            ctx.licitacoes_raw = []
            ctx.is_partial = True
            ctx.response_state = "empty_failure"  # GTM-RESILIENCE-A01 AC5
            ctx.degradation_guidance = (
                "Fontes de dados governamentais estão temporariamente indisponíveis. "
                "Tente novamente em alguns minutos ou reduza o número de estados."
            )
            ctx.degradation_reason = str(e)
            ctx.data_sources = [
                DataSourceStatus(
                    source=src,
                    status="error",
                    records=0,
                )
                for src in e.source_errors
            ]
            ctx.source_stats_data = [
                {
                    "source_code": src,
                    "record_count": 0,
                    "duration_ms": 0,
                    "error": err,
                    "status": "error",
                }
                for src, err in e.source_errors.items()
            ]
    except asyncio.TimeoutError:
        # CRIT-002 AC13/AC14: Update session on timeout
        if ctx.session_id:
            elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)
            asyncio.create_task(
                quota.update_search_session_status(
                    ctx.session_id, status="timed_out",
                    pipeline_stage="execute", response_state="degraded",
                    error_code="timeout",
                    error_message=f"Pipeline timeout after {elapsed_ms}ms (limit: {fetch_timeout * 1000}ms)",
                    completed_at=datetime.now(_tz.utc).isoformat(),
                    duration_ms=elapsed_ms,
                )
            )

        # GTM-RESILIENCE-A01 AC1-AC3: Try cache before returning 504
        logger.error(f"Multi-source fetch timed out after {fetch_timeout}s")
        # A-02 AC3: Do NOT emit_error here — let wrapper decide terminal SSE event
        # based on whether cache is found (degraded) or not (error/504)

        # A-03 AC5: Unified cache cascade (L2 -> L1 -> L3)
        stale_cache = None
        if ctx.user and ctx.user.get("id"):
            try:
                stale_cache = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_build_cache_params(request),
                )
            except Exception as cache_err:
                logger.warning(f"Cache cascade failed after timeout: {cache_err}")

        if stale_cache:
            # Serve cached data with HTTP 200
            cache_level_used = stale_cache.get("cache_level", "unknown")
            cache_age = stale_cache.get("cache_age_hours", 0)
            results_count = len(stale_cache.get("results", []))
            # AC8: Structured log
            logger.info(json.dumps({
                "event": "timeout_cache_fallback",
                "cache_level": cache_level_used,
                "cache_age_hours": cache_age,
                "results_count": results_count,
            }))
            ctx.licitacoes_raw = stale_cache["results"]
            ctx.cached = True
            ctx.cached_at = stale_cache.get("cached_at")
            ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
            ctx.cache_status = stale_cache.get("cache_status", "stale") if isinstance(stale_cache.get("cache_status"), str) else "stale"
            ctx.cache_level = cache_level_used  # AC8: real level from cascade
            ctx.cache_fallback = stale_cache.get("cache_fallback", False)
            ctx.cache_date_range = stale_cache.get("cache_date_range")
            ctx.is_partial = True
            ctx.response_state = "cached"  # AC6
            ctx.degradation_reason = f"Busca expirou após {fetch_timeout}s. Resultados de cache servidos."
            ctx.data_sources = []
            ctx.source_stats_data = []
            # B-01: Background revalidation
            await _maybe_trigger_revalidation(ctx.user["id"], request, stale_cache)
        else:
            # GTM-STAB-004 AC5+AC6: No cache — return empty with degradation guidance
            # instead of HTTP 504. Never 5xx when we can degrade gracefully.
            logger.warning(
                f"No stale cache available after timeout ({fetch_timeout}s) — "
                f"returning empty results with guidance"
            )
            if ctx.tracker:
                await ctx.tracker.emit_degraded(
                    "timeout_no_cache",
                    {"timeout_s": fetch_timeout, "cache_available": False},
                )
            ctx.licitacoes_raw = []
            ctx.is_partial = True
            ctx.response_state = "empty_failure"
            ctx.degradation_guidance = (
                f"A análise excedeu o tempo limite de {fetch_timeout // 60} minutos "
                f"e não há resultados em cache disponíveis. "
                f"Tente com menos estados ou um período menor."
            )
            ctx.degradation_reason = f"Pipeline timeout after {fetch_timeout}s, no cache"
            ctx.data_sources = []
            ctx.source_stats_data = []
    except Exception as e:
        # CRIT-002 AC13: Update session on unexpected error
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(
                    ctx.session_id, pipeline_stage="execute",
                    response_state="empty_failure",
                )
            )

        # GTM-FIX-025 T2: Generic catch — no consolidation exception should
        # result in HTTP 500. Log, send to Sentry, try cache, degrade gracefully.
        # GTM-RESILIENCE-E02: centralized reporting (unexpected = full traceback)
        report_error(
            e, "Unexpected exception in multi-source fetch",
            expected=False, tags={"data_source": "consolidation_unexpected"}, log=logger,
        )

        # A-03 AC6: Unified cache cascade (L2 -> L1 -> L3)
        stale_cache = None
        if ctx.user and ctx.user.get("id"):
            try:
                stale_cache = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_build_cache_params(request),
                )
            except Exception as cache_err:
                logger.warning(f"Cache cascade failed after {type(e).__name__}: {cache_err}")

        if stale_cache:
            logger.info(
                f"Serving stale cache ({stale_cache['cache_age_hours']}h old) "
                f"after unexpected {type(e).__name__}"
            )
            ctx.licitacoes_raw = stale_cache["results"]
            ctx.cached = True
            ctx.cached_at = stale_cache["cached_at"]
            ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
            ctx.cache_status = stale_cache.get("cache_status", "stale") if isinstance(stale_cache.get("cache_status"), str) else ("stale" if stale_cache.get("is_stale") else "fresh")
            ctx.cache_level = stale_cache.get("cache_level", "supabase")  # AC8: real level from cascade
            ctx.cache_fallback = stale_cache.get("cache_fallback", False)
            ctx.cache_date_range = stale_cache.get("cache_date_range")
            ctx.is_partial = True
            ctx.response_state = "cached"  # GTM-RESILIENCE-A01 AC6
            ctx.degradation_reason = f"Erro inesperado: {type(e).__name__}: {str(e)[:200]}"
            ctx.data_sources = []
            ctx.source_stats_data = []
            # B-01: Background revalidation
            await _maybe_trigger_revalidation(ctx.user["id"], request, stale_cache)
        else:
            logger.warning(
                f"No stale cache available after {type(e).__name__} — returning empty"
            )
            ctx.licitacoes_raw = []
            ctx.is_partial = True
            ctx.response_state = "empty_failure"  # GTM-RESILIENCE-A01 AC5
            ctx.degradation_guidance = (
                "Fontes de dados governamentais estão temporariamente indisponíveis. "
                "Tente novamente em alguns minutos ou reduza o número de estados."
            )
            ctx.degradation_reason = f"Erro inesperado: {type(e).__name__}: {str(e)[:200]}"
            ctx.data_sources = []
            ctx.source_stats_data = []
    finally:
        await consolidation_svc.close()


async def _execute_pncp_only(
    pipeline, ctx, request, deps, use_parallel, modalidades_to_fetch,
    status_value, uf_progress_callback, fetch_timeout,
    uf_status_callback=None,
):
    """PNCP-only fetch path (default)."""

    logger.debug(f"Fetching bids from PNCP API for {len(request.ufs)} UFs")

    # STORY-257A AC1: Circuit breaker try_recover only (degraded mode tries with reduced concurrency)
    cb = get_circuit_breaker()
    await cb.try_recover()

    async def _do_fetch() -> list:
        if use_parallel:
            logger.debug(f"Using parallel fetch for {len(request.ufs)} UFs (max_concurrent=10)")
            try:
                fetch_result = await deps.buscar_todas_ufs_paralelo(
                    ufs=request.ufs,
                    data_inicial=request.data_inicial,
                    data_final=request.data_final,
                    modalidades=modalidades_to_fetch,
                    status=status_value,
                    max_concurrent=10,
                    on_uf_complete=uf_progress_callback,
                    on_uf_status=uf_status_callback,
                )
                # Handle both ParallelFetchResult and plain list (backward compat)
                if isinstance(fetch_result, ParallelFetchResult):
                    ctx.succeeded_ufs = fetch_result.succeeded_ufs
                    ctx.failed_ufs = fetch_result.failed_ufs
                    # CRIT-052 AC4: Propagate canary telemetry to context
                    if fetch_result.canary_result:
                        ctx._pncp_canary_result = fetch_result.canary_result
                    # GTM-FIX-004: Propagate truncation metadata
                    if fetch_result.truncated_ufs:
                        ctx.is_truncated = True
                        ctx.truncated_ufs = fetch_result.truncated_ufs
                        # Per-source truncation details (PNCP-only path)
                        ctx.truncation_details = {"pncp": True}
                    return fetch_result.items
                return fetch_result
            except PNCPDegradedError:
                raise  # Re-raise to be handled by outer try/except
            except Exception as e:
                logger.warning(f"Parallel fetch failed, falling back to sequential async: {e}")
                # DEBT-v3-S3 Phase 1.2: Replaced sync PNCPClient + asyncio.to_thread()
                # with native async buscar_todas_ufs_paralelo — no thread overhead.
                fetch_result = await deps.buscar_todas_ufs_paralelo(
                    ufs=request.ufs,
                    data_inicial=request.data_inicial,
                    data_final=request.data_final,
                    modalidades=modalidades_to_fetch,
                )
                from pncp_client import ParallelFetchResult
                if isinstance(fetch_result, ParallelFetchResult):
                    return fetch_result.items
                return list(fetch_result)
        else:
            # DEBT-v3-S3 Phase 1.2: Replaced sync PNCPClient + asyncio.to_thread()
            # with native async buscar_todas_ufs_paralelo — no thread overhead.
            fetch_result = await deps.buscar_todas_ufs_paralelo(
                ufs=request.ufs,
                data_inicial=request.data_inicial,
                data_final=request.data_final,
                modalidades=modalidades_to_fetch,
            )
            from pncp_client import ParallelFetchResult
            if isinstance(fetch_result, ParallelFetchResult):
                return fetch_result.items
            return list(fetch_result)

    try:
        ctx.licitacoes_raw = await asyncio.wait_for(_do_fetch(), timeout=fetch_timeout)
        # STORY-257A AC5: Track UF metadata
        if ctx.failed_ufs is None:
            ctx.failed_ufs = []
        if ctx.succeeded_ufs is None:
            ctx.succeeded_ufs = list(request.ufs)

        # STORY-252 T8: Successful PNCP fetch — populate data source status
        ctx.data_sources = [
            DataSourceStatus(
                source="PNCP",
                status="ok" if not ctx.failed_ufs else "partial",
                records=len(ctx.licitacoes_raw),
            )
        ]

        # STORY-257A AC5: Mark as partial if UFs failed
        if ctx.failed_ufs:
            ctx.is_partial = True
    except PNCPDegradedError as e:
        # CRIT-002 AC13: Update session on PNCP degradation
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(
                    ctx.session_id, pipeline_stage="execute",
                    response_state="degraded",
                )
            )

        # GTM-FIX-010 AC4/AC17r: PNCP circuit breaker tripped — try stale cache
        # GTM-RESILIENCE-E02: centralized reporting (no double stdout+Sentry)
        report_error(
            e, "PNCP degraded during fetch",
            expected=True, tags={"data_source": "pncp"}, log=logger,
        )

        # A-03 AC7: Unified cache cascade (L2 -> L1 -> L3)
        stale_cache = None
        if ctx.user and ctx.user.get("id"):
            try:
                stale_cache = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_build_cache_params(request),
                )
            except Exception as cache_err:
                logger.warning(f"Cache cascade failed after PNCPDegradedError: {cache_err}")

        if stale_cache:
            logger.info(
                f"Serving stale cache ({stale_cache['cache_age_hours']}h old) "
                f"after PNCP degradation"
            )
            ctx.licitacoes_raw = stale_cache["results"]
            ctx.cached = True
            ctx.cached_at = stale_cache["cached_at"]
            ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
            ctx.cache_status = stale_cache.get("cache_status", "stale") if isinstance(stale_cache.get("cache_status"), str) else ("stale" if stale_cache.get("is_stale") else "fresh")
            ctx.cache_level = stale_cache.get("cache_level", "supabase")  # AC8: real level from cascade
            ctx.cache_fallback = stale_cache.get("cache_fallback", False)
            ctx.cache_date_range = stale_cache.get("cache_date_range")
            ctx.is_partial = True
            ctx.response_state = "cached"  # GTM-RESILIENCE-A01 AC6
            ctx.degradation_reason = (
                "PNCP ficou indisponível durante a análise (circuit breaker ativado). "
                "Mostrando resultados do cache."
            )
            ctx.data_sources = [
                DataSourceStatus(source="PNCP", status="error", records=0)
            ]
            # B-01: Background revalidation
            await _maybe_trigger_revalidation(ctx.user["id"], request, stale_cache)
        else:
            ctx.licitacoes_raw = []
            ctx.is_partial = True
            ctx.response_state = "empty_failure"  # GTM-RESILIENCE-A01 AC5
            ctx.degradation_guidance = (
                "Fontes de dados governamentais estão temporariamente indisponíveis. "
                "Tente novamente em alguns minutos ou reduza o número de estados."
            )
            ctx.degradation_reason = (
                "PNCP ficou indisponível durante a análise (circuit breaker ativado). "
                "Tente novamente em alguns minutos."
            )
            ctx.data_sources = [
                DataSourceStatus(source="PNCP", status="error", records=0)
            ]
    except asyncio.TimeoutError:
        # CRIT-002 AC13/AC14: Update session on PNCP timeout
        if ctx.session_id:
            elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)
            asyncio.create_task(
                quota.update_search_session_status(
                    ctx.session_id, status="timed_out",
                    pipeline_stage="execute", response_state="degraded",
                    error_code="timeout",
                    error_message=f"PNCP timeout after {elapsed_ms}ms (limit: {fetch_timeout * 1000}ms)",
                    completed_at=datetime.now(_tz.utc).isoformat(),
                    duration_ms=elapsed_ms,
                )
            )

        # GTM-RESILIENCE-A01 AC1-AC3: Try cache before returning 504 (PNCP-only path)
        logger.error(f"PNCP fetch timed out after {fetch_timeout}s for {len(request.ufs)} UFs")
        # A-02 AC3: Do NOT emit_error here — let wrapper decide terminal SSE event

        # A-03 AC5: Unified cache cascade (L2 -> L1 -> L3)
        stale_cache = None
        if ctx.user and ctx.user.get("id"):
            try:
                stale_cache = await get_from_cache_cascade(
                    user_id=ctx.user["id"],
                    params=_build_cache_params(request),
                )
            except Exception as cache_err:
                logger.warning(f"Cache cascade failed after PNCP timeout: {cache_err}")

        if stale_cache:
            cache_level_used = stale_cache.get("cache_level", "unknown")
            cache_age = stale_cache.get("cache_age_hours", 0)
            results_count = len(stale_cache.get("results", []))
            logger.info(json.dumps({
                "event": "timeout_cache_fallback",
                "cache_level": cache_level_used,
                "cache_age_hours": cache_age,
                "results_count": results_count,
            }))
            ctx.licitacoes_raw = stale_cache["results"]
            ctx.cached = True
            ctx.cached_at = stale_cache.get("cached_at")
            ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
            ctx.cache_status = stale_cache.get("cache_status", "stale") if isinstance(stale_cache.get("cache_status"), str) else "stale"
            ctx.cache_level = cache_level_used  # AC8: real level from cascade
            ctx.cache_fallback = stale_cache.get("cache_fallback", False)
            ctx.cache_date_range = stale_cache.get("cache_date_range")
            ctx.is_partial = True
            ctx.response_state = "cached"
            ctx.degradation_reason = f"PNCP expirou após {fetch_timeout}s. Resultados de cache servidos."
            ctx.data_sources = [
                DataSourceStatus(source="PNCP", status="timeout", records=0)
            ]
            # B-01: Background revalidation
            await _maybe_trigger_revalidation(ctx.user["id"], request, stale_cache)
        else:
            # No cache — emit error and raise 504
            if ctx.tracker:
                await ctx.tracker.emit_error("Busca expirou por tempo")
                from progress import remove_tracker
                await remove_tracker(ctx.request.search_id)
            raise HTTPException(
                status_code=504,
                detail=(
                    f"A análise excedeu o tempo limite de {fetch_timeout // 60} minutos "
                    f"e não há resultados em cache disponíveis. "
                    f"Tente com menos estados ou um período menor."
                ),
            )
