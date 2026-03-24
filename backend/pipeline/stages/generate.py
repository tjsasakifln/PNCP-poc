"""Stage 6: GenerateOutput — LLM summary, Excel report, item conversion.

Extracted from SearchPipeline.stage_generate + _enrich_with_sanctions (DEBT-015 SYS-002).
"""

import asyncio
import logging
import time as sync_time_module
from datetime import datetime, timezone as _tz

from search_context import SearchContext
from schemas import BuscaResponse, FilterStats, ResumoEstrategico, DataSourceStatus
from sectors import get_sector
from telemetry import get_tracer, optional_span
from pipeline.helpers import (
    _convert_to_licitacao_items,
    _build_coverage_metrics,
    _build_coverage_metadata,
)
from pipeline.cache_manager import _build_degraded_detail

logger = logging.getLogger(__name__)

# F-02 AC10: Tracer for pipeline spans
_tracer = get_tracer("search_pipeline")


import quota
from storage import upload_excel
from llm import gerar_resumo, gerar_resumo_fallback


async def stage_generate(pipeline, ctx: SearchContext) -> None:
    """Generate LLM summary, Excel report, and convert to LicitacaoItems."""

    # CRIT-002 AC10: Track pipeline stage
    if ctx.session_id:
        asyncio.create_task(
            quota.update_search_session_status(ctx.session_id, pipeline_stage="generate")
        )

    deps = pipeline.deps

    # Build filter stats for frontend
    fs = FilterStats(
        rejeitadas_uf=ctx.filter_stats.get("rejeitadas_uf", 0),
        rejeitadas_valor=ctx.filter_stats.get("rejeitadas_valor", 0),
        rejeitadas_keyword=ctx.filter_stats.get("rejeitadas_keyword", 0),
        rejeitadas_min_match=ctx.filter_stats.get("rejeitadas_min_match", 0),
        rejeitadas_prazo=ctx.filter_stats.get("rejeitadas_prazo", 0),
        rejeitadas_outros=ctx.filter_stats.get("rejeitadas_outros", 0),
        # GTM-FIX-028 AC7: LLM zero-match stats
        llm_zero_match_calls=ctx.filter_stats.get("llm_zero_match_calls", 0),
        llm_zero_match_aprovadas=ctx.filter_stats.get("llm_zero_match_aprovadas", 0),
        llm_zero_match_rejeitadas=ctx.filter_stats.get("llm_zero_match_rejeitadas", 0),
        llm_zero_match_skipped_short=ctx.filter_stats.get("llm_zero_match_skipped_short", 0),
        # CRIT-057 AC4: Budget tracking
        zero_match_budget_exceeded=ctx.filter_stats.get("zero_match_budget_exceeded", 0),
    )
    # CRIT-057 AC4: Propagate budget status to SearchContext
    if ctx.filter_stats.get("zero_match_budget_exceeded", 0) > 0:
        ctx.zero_match_budget_exceeded = True
        ctx.zero_match_classified = ctx.filter_stats.get("llm_zero_match_calls", 0)
        ctx.zero_match_deferred = ctx.filter_stats.get("zero_match_budget_exceeded", 0)

    # Early return path: no results passed filters
    if not ctx.licitacoes_filtradas:
        logger.info("No bids passed filters — skipping LLM and Excel generation")
        # A-02 AC3-AC5: Emit degraded or complete based on response_state
        # (the wrapper in routes/search.py handles the main terminal event,
        #  but early return bypasses it, so we emit here)
        if ctx.tracker:
            if ctx.response_state in ("cached", "degraded"):
                await ctx.tracker.emit_degraded(
                    reason="timeout" if "expirou" in (ctx.degradation_reason or "") else "source_failure",
                    detail=_build_degraded_detail(ctx),
                )
            else:
                await ctx.tracker.emit_complete()
            from progress import remove_tracker
            await remove_tracker(ctx.request.search_id)

        ctx.resumo = ResumoEstrategico(
            resumo_executivo=(
                f"Nenhuma licitação de {ctx.sector.name.lower()} encontrada "
                f"nos estados selecionados para o período informado."
            ),
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
            alerta_urgencia=None,
            recomendacoes=[],
            alertas_urgencia=[],
            insight_setorial=f"Não foram encontradas oportunidades de {ctx.sector.name.lower()} nos filtros selecionados. Considere ampliar o período ou os estados da análise.",
        )

        new_quota_used = ctx.quota_info.quota_used if ctx.quota_info else 0
        quota_remaining = ctx.quota_info.quota_remaining if ctx.quota_info else 0

        # GTM-RESILIENCE-A05 AC1-AC2: Coverage metrics
        _cov_pct, _ufs_detail = _build_coverage_metrics(ctx)

        ctx.response = BuscaResponse(
            resumo=ctx.resumo,
            licitacoes=[],
            excel_base64=None if not ctx.quota_info or not (ctx.quota_info.capabilities or {}).get("allow_excel", False) else "",
            excel_available=(ctx.quota_info.capabilities or {}).get("allow_excel", False) if ctx.quota_info else False,
            quota_used=new_quota_used,
            quota_remaining=quota_remaining,
            total_raw=len(ctx.licitacoes_raw),
            total_filtrado=0,
            filter_stats=fs,
            termos_utilizados=ctx.custom_terms if ctx.custom_terms else None,
            stopwords_removidas=ctx.stopwords_removed if ctx.stopwords_removed else None,
            upgrade_message="Assine o SmartLic Pro para exportar resultados em Excel." if ctx.quota_info and not (ctx.quota_info.capabilities or {}).get("allow_excel", False) else None,
            sources_used=[ds.source for ds in ctx.data_sources if ds.records > 0] if ctx.data_sources else None,
            source_stats=ctx.source_stats_data,
            hidden_by_min_match=ctx.hidden_by_min_match if ctx.custom_terms else None,
            filter_relaxed=ctx.filter_relaxed if ctx.custom_terms else None,
            match_relaxed=ctx.filter_relaxed,  # STORY-267 AC15
            is_partial=ctx.is_partial,
            data_sources=ctx.data_sources,
            degradation_reason=ctx.degradation_reason,
            failed_ufs=ctx.failed_ufs,
            succeeded_ufs=ctx.succeeded_ufs,
            total_ufs_requested=len(ctx.request.ufs),
            cached=ctx.cached,
            from_cache=ctx.from_cache,
            cached_at=ctx.cached_at,
            cached_sources=ctx.cached_sources,
            cache_status=ctx.cache_status,
            cache_level=ctx.cache_level,
            cache_fallback=ctx.cache_fallback,
            cache_date_range=ctx.cache_date_range,
            is_truncated=ctx.is_truncated,
            truncated_ufs=ctx.truncated_ufs,
            truncation_details=ctx.truncation_details,
            response_state=ctx.response_state,
            degradation_guidance=ctx.degradation_guidance,
            coverage_pct=_cov_pct,
            ufs_status_detail=_ufs_detail,
            coverage_metadata=_build_coverage_metadata(ctx),
            live_fetch_in_progress=ctx.live_fetch_in_progress,
            llm_status=None,
            excel_status=None,
            llm_source=None,  # CRIT-005 AC13: No LLM for empty results
            # GTM-STAB new fields
            filter_summary=ctx.filter_summary,
            is_simplified=ctx.is_simplified,
            relaxation_level=ctx.relaxation_level,
        )
        return  # Skip stages 6b-7 (handled here for early return)

    # ---------------------------------------------------------------
    # GTM-RESILIENCE-F01: Queue-first LLM + Excel (AC17, AC22)
    # If ARQ queue is available, dispatch jobs and return immediately.
    # Otherwise, execute inline (zero regression).
    # ---------------------------------------------------------------
    from job_queue import is_queue_available, enqueue_job

    queue_available = await is_queue_available()
    search_id = ctx.request.search_id

    ctx.excel_base64 = None
    ctx.download_url = None
    ctx.excel_available = (ctx.quota_info.capabilities or {}).get("allow_excel", False) if ctx.quota_info else False
    ctx.upgrade_message = None

    if queue_available and search_id and ctx.tracker is not None:
        # === QUEUE MODE: Dispatch to background, return fast ===
        # NOTE: Requires tracker (SSE) to deliver excel_ready/llm_ready events.
        # Cache-first path has tracker=None — falls through to inline mode.
        logger.info(f"Queue mode: dispatching LLM + Excel jobs for search_id={search_id}")
        ctx.queue_mode = True

        # Immediate fallback summary (pure Python, <1ms)
        ctx.resumo = gerar_resumo_fallback(ctx.licitacoes_filtradas, sector_name=ctx.sector.name, termos_busca=ctx.request.termos_busca)
        ctx.llm_status = "processing"
        ctx.llm_source = "processing"  # CRIT-005 AC13: LLM queued for background

        # CRIT-033: Enqueue LLM job — check return to detect enqueue failure
        llm_enqueued = await enqueue_job(
            "llm_summary_job",
            search_id,
            ctx.licitacoes_filtradas,
            ctx.sector.name,
            ctx.request.termos_busca,  # GTM-FIX-041
            _job_id=f"llm:{search_id}",
        )
        if llm_enqueued is None:
            # CRIT-033: Enqueue failed — mark as fallback, not "processing"
            logger.warning(
                f"CRIT-033: LLM enqueue failed for search_id={search_id} — "
                "using fallback summary (llm_ready SSE will not fire)"
            )
            ctx.llm_status = "ready"
            ctx.llm_source = "fallback"

        # CRIT-033: Enqueue Excel job — check return for failure
        if ctx.excel_available:
            excel_enqueued = await enqueue_job(
                "excel_generation_job",
                search_id,
                ctx.licitacoes_filtradas,
                ctx.excel_available,
                _job_id=f"excel:{search_id}",
            )
            if excel_enqueued is not None:
                ctx.excel_status = "processing"
            else:
                # CRIT-033: Excel enqueue failed — mark as failed, not "processing"
                logger.warning(
                    f"CRIT-033: Excel enqueue failed for search_id={search_id} — "
                    "excel_ready SSE will not fire"
                )
                ctx.excel_status = "failed"
        else:
            ctx.excel_status = "skipped"
            ctx.upgrade_message = "Assine o SmartLic Pro para exportar resultados em Excel."

        # STORY-259 AC3: Dispatch bid analysis job (parallel to LLM + Excel)
        from config import get_feature_flag as _gff
        if _gff("BID_ANALYSIS_ENABLED"):
            bid_analysis_enqueued = await enqueue_job(
                "bid_analysis_job",
                search_id,
                ctx.licitacoes_filtradas,
                user_profile=ctx.user_profile,
                sector_name=ctx.sector.name,
                _job_id=f"bid_analysis:{search_id}",
            )
            if bid_analysis_enqueued is not None:
                ctx.bid_analysis_status = "processing"
            else:
                ctx.bid_analysis_status = None

        # SSE: Notify frontend that results are ready (LLM/Excel arriving later)
        if ctx.tracker:
            await ctx.tracker.emit("filtering_complete", 70, "Resultados prontos! Gerando resumo e planilha em segundo plano...")

    else:
        # === INLINE MODE: Current behavior (AC22 fallback) ===
        ctx.queue_mode = False

        # SSE: Starting LLM
        if ctx.tracker:
            await ctx.tracker.emit("llm", 75, "Avaliando oportunidades com IA...")

        # AC15: Sub-span for LLM summary generation
        logger.debug("Generating executive summary")
        with optional_span(_tracer, "generate.llm_summary", {
            "llm.input_count": len(ctx.licitacoes_filtradas),
        }) as llm_span:
            try:
                ctx.resumo = gerar_resumo(ctx.licitacoes_filtradas, sector_name=ctx.sector.name, termos_busca=ctx.request.termos_busca)
                llm_span.set_attribute("llm.status", "success")
                logger.debug("LLM summary generated successfully")
                ctx.llm_source = "ai"  # CRIT-005 AC13
            except Exception as e:
                llm_span.set_attribute("llm.status", "fallback")
                llm_span.record_exception(e)
                logger.warning(
                    f"LLM generation failed, using fallback mechanism: {type(e).__name__}: {e}",
                )
                ctx.resumo = gerar_resumo_fallback(ctx.licitacoes_filtradas, sector_name=ctx.sector.name, termos_busca=ctx.request.termos_busca)
                logger.debug("Fallback summary generated successfully")
                ctx.llm_source = "fallback"  # CRIT-005 AC13

        # Override LLM-generated counts with actual values
        actual_total = len(ctx.licitacoes_filtradas)
        actual_valor = sum(
            lic.get("valorTotalEstimado", 0) or 0 for lic in ctx.licitacoes_filtradas
        )
        if ctx.resumo.total_oportunidades != actual_total:
            logger.warning(
                f"LLM returned total_oportunidades={ctx.resumo.total_oportunidades}, "
                f"overriding with actual count={actual_total}"
            )
        ctx.resumo.total_oportunidades = actual_total
        ctx.resumo.valor_total = actual_valor
        ctx.llm_status = "ready"

        # SSE: Starting Excel
        if ctx.tracker:
            await ctx.tracker.emit("excel", 92, "Gerando planilha Excel...")

        # AC15: Sub-span for Excel generation + upload
        if ctx.excel_available:
            with optional_span(_tracer, "generate.excel", {
                "excel.input_count": len(ctx.licitacoes_filtradas),
            }) as excel_span:
                logger.debug("Generating Excel report")
                # STORY-290-patch: offload CPU-bound Excel generation to thread pool
                excel_buffer = await asyncio.to_thread(deps.create_excel, ctx.licitacoes_filtradas)
                excel_bytes = excel_buffer.read()

                with optional_span(_tracer, "generate.upload"):
                    # STORY-290-patch: offload sync storage upload to thread pool
                    storage_result = await asyncio.to_thread(upload_excel, excel_bytes, ctx.request.search_id)

                if storage_result:
                    ctx.download_url = storage_result["signed_url"]
                    logger.debug(
                        f"Excel uploaded to storage: {storage_result['file_path']} "
                        f"(signed URL valid for {storage_result['expires_in']}s)"
                    )
                    ctx.excel_base64 = None
                    ctx.excel_status = "ready"
                    excel_span.set_attribute("excel.status", "ready")
                else:
                    logger.error(
                        "Excel storage upload failed — no fallback. "
                        "Excel will be unavailable for this search."
                    )
                    ctx.excel_base64 = None
                    ctx.download_url = None
                    ctx.excel_available = False
                    ctx.excel_status = "failed"
                    excel_span.set_attribute("excel.status", "failed")
                    ctx.upgrade_message = (
                        "Erro temporário ao gerar Excel. Tente novamente em alguns instantes."
                    )
        else:
            logger.debug("Excel generation skipped (not allowed for user's plan)")
            ctx.excel_status = "skipped"
            ctx.upgrade_message = "Assine o SmartLic Pro para exportar resultados em Excel."

    # Convert to LicitacaoItems
    ctx.licitacao_items = _convert_to_licitacao_items(ctx.licitacoes_filtradas)

    # STORY-256 AC13: Sanctions enrichment (opt-in)
    if ctx.request.check_sanctions and ctx.licitacao_items:
        await _enrich_with_sanctions(ctx)

    new_quota_used = ctx.quota_info.quota_used if ctx.quota_info else 0
    quota_remaining = ctx.quota_info.quota_remaining if ctx.quota_info else 0

    # GTM-RESILIENCE-A05 AC1-AC2: Coverage metrics
    _cov_pct, _ufs_detail = _build_coverage_metrics(ctx)

    ctx.response = BuscaResponse(
        resumo=ctx.resumo,
        licitacoes=ctx.licitacao_items,
        excel_base64=ctx.excel_base64,
        download_url=ctx.download_url,
        excel_available=ctx.excel_available,
        quota_used=new_quota_used,
        quota_remaining=quota_remaining,
        total_raw=len(ctx.licitacoes_raw),
        total_filtrado=len(ctx.licitacoes_filtradas),
        filter_stats=fs,
        termos_utilizados=ctx.custom_terms if ctx.custom_terms else None,
        stopwords_removidas=ctx.stopwords_removed if ctx.stopwords_removed else None,
        upgrade_message=ctx.upgrade_message,
        sources_used=[ds.source for ds in ctx.data_sources if ds.records > 0] if ctx.data_sources else None,
        source_stats=ctx.source_stats_data,
        hidden_by_min_match=ctx.hidden_by_min_match if ctx.custom_terms else None,
        filter_relaxed=ctx.filter_relaxed if ctx.custom_terms else None,
        match_relaxed=ctx.filter_relaxed,  # STORY-267 AC15
        ultima_atualizacao=datetime.now(_tz.utc).isoformat(),
        is_partial=ctx.is_partial,
        data_sources=ctx.data_sources,
        degradation_reason=ctx.degradation_reason,
        sources_degraded=ctx.sources_degraded if ctx.sources_degraded else None,
        failed_ufs=ctx.failed_ufs,
        succeeded_ufs=ctx.succeeded_ufs,
        total_ufs_requested=len(ctx.request.ufs),
        cached=ctx.cached,
        from_cache=ctx.from_cache,
        cached_at=ctx.cached_at,
        cached_sources=ctx.cached_sources,
        cache_status=ctx.cache_status,
        cache_level=ctx.cache_level,
        cache_fallback=ctx.cache_fallback,
        cache_date_range=ctx.cache_date_range,
        is_truncated=ctx.is_truncated,
        truncated_ufs=ctx.truncated_ufs,
        truncation_details=ctx.truncation_details,
        response_state=ctx.response_state,
        degradation_guidance=ctx.degradation_guidance,
        coverage_pct=_cov_pct,
        ufs_status_detail=_ufs_detail,
        coverage_metadata=_build_coverage_metadata(ctx),
        live_fetch_in_progress=ctx.live_fetch_in_progress,
        # GTM-RESILIENCE-F01 AC18: Background job status
        llm_status=ctx.llm_status,
        excel_status=ctx.excel_status,
        # CRIT-005 AC13: LLM summary provenance
        llm_source=ctx.llm_source,
        # GTM-STAB new fields
        filter_summary=ctx.filter_summary,
        is_simplified=ctx.is_simplified,
        relaxation_level=ctx.relaxation_level,
        # STORY-354 AC2: Pending review count
        pending_review_count=ctx.filter_stats.get("pending_review_count", 0),
        # CRIT-059 AC6: Async zero-match job info
        zero_match_job_id=ctx.zero_match_job_id,
        zero_match_candidates_count=ctx.zero_match_candidates_count,
    )

    logger.info(
        "Search completed successfully",
        extra={
            "total_raw": ctx.response.total_raw,
            "total_filtrado": ctx.response.total_filtrado,
            "valor_total": ctx.resumo.valor_total,
            "queue_mode": ctx.queue_mode,
            "llm_status": ctx.llm_status,
            "excel_status": ctx.excel_status,
            "pending_review_count": ctx.response.pending_review_count,
        },
    )

    # STORY-354 AC4+AC7: Store pending bids in Redis and enqueue reclassify job
    _pr_count = ctx.filter_stats.get("pending_review_count", 0)
    if _pr_count > 0:
        try:
            # Collect pending review bids from filtered results
            _pending_bids = [
                lic for lic in ctx.licitacoes_filtradas
                if lic.get("_pending_review")
            ]
            if _pending_bids:
                from job_queue import store_pending_review_bids, is_queue_available as _is_q, enqueue_job as _enq
                _sector_name = ""
                _sector_id = ""
                if ctx.request.setor:
                    try:
                        _sec = get_sector(ctx.request.setor)
                        _sector_name = _sec.name
                        _sector_id = ctx.request.setor
                    except Exception:
                        pass

                _ctx_search_id = getattr(ctx.request, "search_id", None) or ""
                await store_pending_review_bids(
                    search_id=_ctx_search_id,
                    bids=_pending_bids,
                    sector_name=_sector_name,
                )

                if await _is_q():
                    await _enq(
                        "reclassify_pending_bids_job",
                        search_id=_ctx_search_id,
                        sector_name=_sector_name,
                        sector_id=_sector_id,
                        attempt=1,
                        _defer_by=300,  # 5 min delay — give LLM time to recover
                    )
                    logger.info(
                        f"STORY-354: Enqueued reclassify job for {len(_pending_bids)} bids "
                        f"(search_id={_ctx_search_id})"
                    )
        except Exception as _pr_err:
            logger.warning(f"STORY-354: Failed to enqueue reclassify job: {_pr_err}")


# ------------------------------------------------------------------
# STORY-256 AC13: Sanctions enrichment helper
# ------------------------------------------------------------------
async def _enrich_with_sanctions(ctx: SearchContext) -> None:
    """Enrich LicitacaoItems with sanctions data when check_sanctions=true.

    Extracts unique CNPJs from filtered results (cnpjOrgao field),
    batch-checks them against CEIS+CNEP via SanctionsService,
    and populates supplier_sanctions on each LicitacaoItem.

    Graceful degradation: if sanctions check fails, items are
    left without sanctions data (supplier_sanctions=None).
    """
    from services.sanctions_service import SanctionsService
    from schemas import SanctionsSummarySchema

    try:
        # Extract unique CNPJs from raw results
        cnpj_map: dict[str, list[int]] = {}  # cnpj -> [item indices]
        for idx, lic in enumerate(ctx.licitacoes_filtradas):
            cnpj = lic.get("cnpjOrgao", "")
            if cnpj:
                cleaned = cnpj.replace(".", "").replace("/", "").replace("-", "")
                if len(cleaned) == 14 and cleaned.isdigit():
                    cnpj_map.setdefault(cleaned, []).append(idx)

        if not cnpj_map:
            logger.debug("[SANCTIONS] No valid CNPJs found in results, skipping")
            return

        unique_cnpjs = list(cnpj_map.keys())
        logger.debug(f"[SANCTIONS] Checking {len(unique_cnpjs)} unique CNPJs from {len(ctx.licitacao_items)} results")

        # Batch check
        service = SanctionsService()
        try:
            reports = await service.check_companies(unique_cnpjs)
        finally:
            await service.close()

        # Map results back to LicitacaoItems
        enriched = 0
        for cnpj, indices in cnpj_map.items():
            report = reports.get(cnpj)
            if not report or report.status == "unavailable":
                continue

            summary = SanctionsService.build_summary(report)
            schema = SanctionsSummarySchema(
                is_clean=summary.is_clean,
                active_sanctions_count=summary.active_sanctions_count,
                sanction_types=summary.sanction_types,
                checked_at=summary.checked_at.isoformat() if summary.checked_at else None,
            )

            for idx in indices:
                if idx < len(ctx.licitacao_items):
                    ctx.licitacao_items[idx].supplier_sanctions = schema
                    enriched += 1

        logger.debug(
            f"[SANCTIONS] Enrichment complete: {enriched} items enriched, "
            f"{sum(1 for r in reports.values() if r.is_sanctioned)} CNPJs sanctioned"
        )

    except Exception as exc:
        # AC5: Graceful degradation — sanctions failure should never block search
        logger.warning(f"[SANCTIONS] Enrichment failed (graceful degradation): {exc}")
