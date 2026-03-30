"""Stage 4: FilterResults — apply all filters to raw procurement data.

Named filter_stage.py to avoid conflict with Python builtin `filter`.
Extracted from SearchPipeline.stage_filter (DEBT-015 SYS-002).
"""

import asyncio
import json
import logging
import time as sync_time_module

from search_context import SearchContext
from metrics import FILTER_DECISIONS, FILTER_INPUT_TOTAL, FILTER_OUTPUT_TOTAL, FILTER_DISCARD_RATE
from status_inference import enriquecer_com_status_inferido

import quota

logger = logging.getLogger(__name__)


async def stage_filter(pipeline, ctx: SearchContext) -> None:
    """Apply all filters (UF, status, esfera, modalidade, municipio, valor, keyword)."""

    # ISSUE-047 FIX: Always enrich with inferred status before filtering.
    # Cache paths in execute.py return before calling this, so bids from cache
    # arrive without _status_inferido. Re-inferring is safe and correct because
    # status inference is time-dependent (compares deadlines to now()).
    if ctx.licitacoes_raw:
        enriquecer_com_status_inferido(ctx.licitacoes_raw)

    # CRIT-002 AC9: Track pipeline stage
    if ctx.session_id:
        asyncio.create_task(
            quota.update_search_session_status(ctx.session_id, pipeline_stage="filter")
        )

    deps = pipeline.deps
    request = ctx.request

    # SSE: Starting filtering
    if ctx.tracker:
        await ctx.tracker.emit("filtering", 60, f"Aplicando filtros em {len(ctx.licitacoes_raw)} licitacoes...")

    esferas_values = [e.value for e in request.esferas] if request.esferas else None
    status_filter = request.status.value if request.status else "todos"

    logger.info(
        f"Applying filters: status={status_filter}, modalidades={request.modalidades}, "
        f"valor=[{request.valor_minimo}, {request.valor_maximo}], esferas={esferas_values}, "
        f"municipios={len(request.municipios) if request.municipios else 0}"
    )

    # STORY-329 AC2/AC4: Create progress callback for real-time SSE during filtering
    _filter_start = sync_time_module.monotonic()
    _long_running_emitted = [False]  # list for thread-safe mutation

    if ctx.tracker:
        _loop = asyncio.get_running_loop()

        def _on_filter_progress(processed: int, total: int, phase: str = "filter") -> None:
            """Thread-safe callback: schedules SSE emit on event loop."""
            elapsed = sync_time_module.monotonic() - _filter_start

            if phase == "filter":
                # AC2: interpolate 60->65 for keyword matching
                pct = 60 + int((processed / max(total, 1)) * 5)
                msg = f"Filtrando: {processed}/{total}"
            elif phase == "llm_classify":
                # AC3: interpolate 65->70 for LLM zero-match
                pct = 65 + int((processed / max(total, 1)) * 5)
                msg = f"Classificação IA: {processed}/{total} sem keywords"
            else:
                return

            detail: dict = {}
            # AC4: flag long-running filter after 30s
            if elapsed > 30 and not _long_running_emitted[0]:
                _long_running_emitted[0] = True
                detail["is_long_running"] = True

            coro = ctx.tracker.emit("filtering", pct, msg, **detail)
            _loop.call_soon_threadsafe(_loop.create_task, coro)
    else:
        _on_filter_progress = None

    # STORY-329 AC2: Run filter in thread so event loop can send SSE events in real-time
    ctx.licitacoes_filtradas, ctx.filter_stats = await asyncio.to_thread(
        deps.aplicar_todos_filtros,
        ctx.licitacoes_raw,
        ufs_selecionadas=set(request.ufs),
        status=status_filter,
        modalidades=request.modalidades,
        valor_min=request.valor_minimo,
        valor_max=request.valor_maximo,
        esferas=esferas_values,
        municipios=request.municipios,
        keywords=ctx.active_keywords,
        exclusions=ctx.active_exclusions,
        context_required=ctx.active_context_required,
        min_match_floor=ctx.min_match_floor_value,
        setor=ctx.request.setor_id,  # CRIT-019 AC1: pass sector to enable 6 classification paths
        modo_busca=request.modo_busca or "publicacao",
        custom_terms=ctx.custom_terms or None,  # STORY-267: pass custom terms for quality parity
        on_progress=_on_filter_progress,
        pncp_degraded="PNCP" in (ctx.sources_degraded or []),  # CRIT-054 AC4
    )
    # Let pending progress events flush before continuing
    await asyncio.sleep(0)

    # Min-match relaxation
    ctx.hidden_by_min_match = ctx.filter_stats.get("rejeitadas_min_match", 0)
    ctx.filter_relaxed = False

    if (
        ctx.custom_terms
        and ctx.min_match_floor_value is not None
        and ctx.min_match_floor_value > 1
        and len(ctx.licitacoes_filtradas) == 0
        and ctx.hidden_by_min_match > 0
    ):
        logger.warning(
            f"Min match floor relaxed from {ctx.min_match_floor_value} to 1 — "
            f"zero results with strict filter"
        )
        ctx.filter_relaxed = True
        ctx.licitacoes_filtradas, ctx.filter_stats = deps.aplicar_todos_filtros(
            ctx.licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            status=status_filter,
            modalidades=request.modalidades,
            valor_min=request.valor_minimo,
            valor_max=request.valor_maximo,
            esferas=esferas_values,
            municipios=request.municipios,
            keywords=ctx.active_keywords,
            exclusions=ctx.active_exclusions,
            context_required=ctx.active_context_required,
            min_match_floor=None,
            setor=ctx.request.setor_id,  # CRIT-019 AC2: pass sector in relaxed retry too
            modo_busca=request.modo_busca or "publicacao",
            custom_terms=ctx.custom_terms or None,  # STORY-267: pass custom terms in relaxed retry too
            pncp_degraded="PNCP" in (ctx.sources_degraded or []),  # CRIT-054 AC4
        )
        ctx.hidden_by_min_match = 0

    # E-01 AC1 + CRIT-050 AC14: Consolidated filter stats covering ALL reason codes
    stats = ctx.filter_stats
    logger.info(json.dumps({
        "event": "filter_complete",
        "total": stats.get("total", len(ctx.licitacoes_raw)) if stats else len(ctx.licitacoes_raw),
        "passed": stats.get("aprovadas", len(ctx.licitacoes_filtradas)) if stats else len(ctx.licitacoes_filtradas),
        "rejected": {
            "uf": stats.get("rejeitadas_uf", 0),
            "status": stats.get("rejeitadas_status", 0),
            "esfera": stats.get("rejeitadas_esfera", 0),
            "modalidade": stats.get("rejeitadas_modalidade", 0),
            "municipio": stats.get("rejeitadas_municipio", 0),
            "orgao": stats.get("rejeitadas_orgao", 0),
            "valor": stats.get("rejeitadas_valor", 0),
            "valor_alto": stats.get("rejeitadas_valor_alto", 0),
            "keyword": stats.get("rejeitadas_keyword", 0),
            "min_match": stats.get("rejeitadas_min_match", 0),
            "prazo": stats.get("rejeitadas_prazo", 0),
            "prazo_aberto": stats.get("rejeitadas_prazo_aberto", 0),
            "baixa_densidade": stats.get("rejeitadas_baixa_densidade", 0),
            "red_flags": stats.get("rejeitadas_red_flags", 0),
            "red_flags_setorial": stats.get("rejeitadas_red_flags_setorial", 0),
            "llm_arbiter": stats.get("rejeitadas_llm_arbiter", 0),
            "outros": stats.get("rejeitadas_outros", 0),
        },
    }) if stats else f"Filtering complete: {len(ctx.licitacoes_filtradas)}/{len(ctx.licitacoes_raw)} bids passed")

    # E-03: Emit Prometheus filter decision counters
    if stats:
        for stage_key, stage_label in [
            ("rejeitadas_uf", "uf"), ("rejeitadas_status", "status"),
            ("rejeitadas_esfera", "esfera"), ("rejeitadas_modalidade", "modalidade"),
            ("rejeitadas_municipio", "municipio"), ("rejeitadas_valor", "valor"),
            ("rejeitadas_keyword", "keyword"), ("rejeitadas_min_match", "min_match"),
            ("rejeitadas_prazo", "prazo"), ("rejeitadas_outros", "outros"),
        ]:
            count = stats.get(stage_key, 0)
            if count > 0:
                FILTER_DECISIONS.labels(stage=stage_label, decision="reject").inc(count)
        passed = stats.get("aprovadas", len(ctx.licitacoes_filtradas))
        if passed > 0:
            FILTER_DECISIONS.labels(stage="final", decision="pass").inc(passed)

    # STORY-351 AC1+AC2: Filter input/output counters + discard rate histogram
    _input_count = stats.get("total", len(ctx.licitacoes_raw)) if stats else len(ctx.licitacoes_raw)
    _output_count = stats.get("aprovadas", len(ctx.licitacoes_filtradas)) if stats else len(ctx.licitacoes_filtradas)
    _sector = ctx.request.setor_id or "unknown"
    FILTER_INPUT_TOTAL.labels(sector=_sector, source="all").inc(_input_count)
    FILTER_OUTPUT_TOTAL.labels(sector=_sector, source="all").inc(_output_count)
    if _input_count > 0:
        _discard_ratio = 1 - (_output_count / _input_count)
        FILTER_DISCARD_RATE.labels(sector=_sector).observe(_discard_ratio)

    # STORY-351 AC9+AC3: Record for discard rate endpoint (30-day moving average)
    from filter.stats import discard_rate_tracker
    discard_rate_tracker.record(
        input_count=_input_count,
        output_count=_output_count,
        sector=_sector,
        search_id=getattr(ctx.request, "search_id", "") or "",
    )

    # Diagnostic sample
    if stats.get('rejeitadas_keyword', 0) > 0:
        keyword_rejected_sample = []
        for lic in ctx.licitacoes_raw[:200]:
            obj = lic.get("objetoCompra", "")
            matched, _ = deps.match_keywords(obj, deps.KEYWORDS_UNIFORMES, deps.KEYWORDS_EXCLUSAO)
            if not matched:
                keyword_rejected_sample.append(obj[:120])
                if len(keyword_rejected_sample) >= 3:
                    break
        if keyword_rejected_sample:
            logger.debug(f"  - Sample keyword-rejected objects: {keyword_rejected_sample}")

    # GTM-STAB-005 AC3: Build human-readable filter summary when results=0
    if len(ctx.licitacoes_filtradas) == 0 and stats:
        _fs_parts = []
        for label, key in [
            ("UF", "rejeitadas_uf"),
            ("valor", "rejeitadas_valor"),
            ("keyword", "rejeitadas_keyword"),
            ("min_match", "rejeitadas_min_match"),
            ("prazo", "rejeitadas_prazo"),
            ("outros", "rejeitadas_outros"),
        ]:
            count = stats.get(key, 0)
            if count > 0:
                _fs_parts.append(f"{count} por {label}")
        ctx.filter_summary = (
            "Nenhum resultado: " + ", ".join(_fs_parts) if _fs_parts else "Nenhum resultado encontrado"
        )
        logger.info(f"[STAB-005] filter_summary: {ctx.filter_summary}")

    # GTM-STAB-005 AC4: Auto-relaxation for term searches with zero results
    # Level 0 = normal (no relaxation), 1 = no min_match_floor, 2 = substring match, 3 = empty with guidance
    # NOTE: level 1 is already handled above via the min_match relaxation block (ctx.filter_relaxed)
    ctx.relaxation_level = 0
    if ctx.filter_relaxed:
        ctx.relaxation_level = 1
    if (
        ctx.custom_terms
        and len(ctx.licitacoes_filtradas) == 0
        and len(ctx.licitacoes_raw) > 0
    ):
        # ISSUE-017 FIX: Level 2 — substring matching (looser than word-boundary regex)
        # Instead of immediately dropping ALL keyword filters and returning garbage,
        # try a simpler substring match that may catch partial mentions.
        from filter import normalize_text as _normalize_text_l2
        _custom_norms = [_normalize_text_l2(t) for t in ctx.custom_terms]
        _l2_substring = []
        for _bid in ctx.licitacoes_raw:
            _obj_norm = _normalize_text_l2(_bid.get("objetoCompra", ""))
            if any(_term in _obj_norm for _term in _custom_norms):
                _bid["_relevance_source"] = "substring_relaxation"
                _bid["_term_density"] = 0.5
                _bid["_matched_terms"] = ctx.custom_terms
                _l2_substring.append(_bid)

        if _l2_substring:
            ctx.licitacoes_filtradas = _l2_substring
            ctx.relaxation_level = 2
            logger.info(
                f"[STAB-005] Level-2 substring relaxation recovered {len(_l2_substring)} results "
                f"for custom_terms={ctx.custom_terms}"
            )
        else:
            # ISSUE-017 FIX: Level 3 — return EMPTY with guidance message.
            # NEVER return top-by-value irrelevant results. Showing biodescontaminação
            # for a "uniformes escolares" search destroys user trust.
            ctx.relaxation_level = 3
            ctx.filter_summary = (
                f"Nenhuma licitação encontrada para os termos: "
                f"{', '.join(ctx.custom_terms)}. "
                f"Tente termos mais genéricos ou amplie o período de busca."
            )
            logger.info(
                f"[STAB-005] Level-3: No results for custom_terms={ctx.custom_terms} "
                f"in {len(ctx.licitacoes_raw)} bids — returning empty with guidance "
                f"(NOT top-by-value garbage)"
            )

    # ISSUE-044: Sector-based searches with zero results return empty with guidance.
    # Previously (ISSUE-025 fix), zero results triggered a "relaxation" that dropped
    # ALL keyword/sector/value-ceiling filters and returned top-20-by-value — mixing
    # cestas básicas, medicamentos, and construction bids into Software/Saúde/etc.
    # This destroyed classification precision for 14/15 sectors.
    #
    # The cure was worse than the disease: showing irrelevant results as "Alta relevância"
    # breaks user trust far more than showing "0 results found".
    #
    # New behavior: return 0 results + helpful guidance message.
    if (
        not ctx.custom_terms
        and ctx.request.setor_id
        and len(ctx.licitacoes_filtradas) == 0
        and len(ctx.licitacoes_raw) > 0
        and ctx.relaxation_level == 0
    ):
        # ISSUE-044 DIAG: Log status distribution for debugging
        _diag_statuses = {}
        for _d in ctx.licitacoes_raw[:200]:
            _s = _d.get("_status_inferido", _d.get("situacaoCompraItemNome", "unknown"))
            _diag_statuses[_s] = _diag_statuses.get(_s, 0) + 1
        logger.info(
            f"[ISSUE-044] Zero results for sector={ctx.request.setor_id} — "
            f"returning empty with guidance (NOT relaxing to garbage). "
            f"Status distribution: {_diag_statuses}, raw_pool={len(ctx.licitacoes_raw)}"
        )
        ctx.filter_summary = (
            f"Nenhuma licitação encontrada para o setor selecionado nos estados "
            f"e período informados. Tente ampliar os estados ou o período de busca."
        )

    # SSE: Filtering complete
    if ctx.tracker:
        await ctx.tracker.emit(
            "filtering", 70,
            f"Filtragem concluida: {len(ctx.licitacoes_filtradas)} resultados",
            total_filtered=len(ctx.licitacoes_filtradas),
        )
        # STORY-327 AC5: Emit unified filter_summary with raw vs filtered breakdown
        await ctx.tracker.emit_filter_summary(
            total_raw=len(ctx.licitacoes_raw),
            total_filtered=len(ctx.licitacoes_filtradas),
            rejected_keyword=stats.get("rejeitadas_keyword", 0) if stats else 0,
            rejected_value=stats.get("rejeitadas_valor", 0) if stats else 0,
            rejected_llm=stats.get("rejeitadas_llm", 0) if stats else 0,
            filter_stats=stats,
        )

        # CRIT-071: Emit partial_data with filtered results
        if ctx.licitacoes_filtradas:
            from config import get_feature_flag as _gff_071b
            if _gff_071b("PARTIAL_DATA_SSE_ENABLED"):
                await ctx.tracker.emit_partial_data(
                    licitacoes=ctx.licitacoes_filtradas,
                    batch_index=2,
                    ufs_completed=list(ctx.succeeded_ufs or ctx.request.ufs),
                    is_final=True,
                )

    # CRIT-059: Dispatch async zero-match job if candidates were collected
    _zm_candidates = ctx.filter_stats.get("zero_match_candidates", [])
    if _zm_candidates:
        ctx.zero_match_candidates = _zm_candidates
        ctx.zero_match_candidates_count = len(_zm_candidates)
        try:
            from job_queue import is_queue_available, enqueue_job
            if await is_queue_available():
                _sector_name = ctx.sector.name if ctx.sector else (ctx.request.setor_id or "")
                _sector_id = ctx.request.setor_id or ""
                _search_id = getattr(ctx.request, "search_id", None) or ""
                job = await enqueue_job(
                    "classify_zero_match_job",
                    search_id=_search_id,
                    candidates=_zm_candidates,
                    setor=_sector_id,
                    sector_name=_sector_name,
                    custom_terms=ctx.custom_terms or None,
                    enqueued_at=sync_time_module.time(),
                    _job_id=f"zm:{_search_id}",
                )
                if job:
                    ctx.zero_match_job_id = getattr(job, "job_id", None) or f"zm:{_search_id}"
                    logger.info(
                        f"[CRIT-059] Enqueued zero-match job for {len(_zm_candidates)} candidates "
                        f"(search_id={_search_id}, job_id={ctx.zero_match_job_id})"
                    )
                else:
                    logger.warning("[CRIT-059] enqueue_job returned None — marking as pending_review")
                    ctx.zero_match_job_id = None
            else:
                logger.warning("[CRIT-059] ARQ unavailable — zero-match candidates become pending_review")
                ctx.zero_match_job_id = None
        except Exception as _zm_err:
            logger.warning(f"[CRIT-059] Failed to dispatch zero-match job: {_zm_err}")
            ctx.zero_match_job_id = None
