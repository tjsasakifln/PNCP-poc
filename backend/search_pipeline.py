"""SearchPipeline — 7-stage decomposition of the buscar_licitacoes god function.

STORY-216: Decomposes the 860+ line buscar_licitacoes() into a clean pipeline:
  Stage 1: ValidateRequest — validate input, check quota, resolve plan
  Stage 2: PrepareSearch — parse terms, configure sector, build query params
  Stage 3: ExecuteSearch — call PNCP API (+ other sources), collect raw results
  Stage 4: FilterResults — keyword filter, status filter, modality filter, value filter
  Stage 5: EnrichResults — relevance scoring, sorting
  Stage 6: GenerateOutput — LLM summary, Excel generation, item conversion
  Stage 7: Persist — save session, build response

AC1: SearchPipeline class with 7 stages.
AC2: Each stage is an independent method that takes/returns SearchContext.
AC4: Each stage has its own error handling — failure in Stage 6 preserves Stage 4.
AC8: No deferred imports — all imports at module level.
"""

import asyncio
import json
import logging
import os
import time as sync_time_module
from datetime import datetime, timezone as _tz
from types import SimpleNamespace

from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
import quota  # Module-level import; accessed via quota.func() for mock compatibility

from search_context import SearchContext
from schemas import BuscaResponse, FilterStats, ResumoEstrategico, LicitacaoItem, DataSourceStatus, UfStatusDetail, CoverageMetadata
from pncp_client import get_circuit_breaker, PNCPDegradedError, ParallelFetchResult
from consolidation import AllSourcesFailedError
from term_parser import parse_search_terms
from relevance import calculate_min_matches, score_relevance, count_phrase_matches
from status_inference import enriquecer_com_status_inferido
from utils.ordenacao import ordenar_licitacoes
from sectors import get_sector
from storage import upload_excel
from llm import gerar_resumo, gerar_resumo_fallback
from authorization import get_admin_ids, get_master_quota_info
from log_sanitizer import mask_user_id
from search_cache import save_to_cache as _supabase_save_cache, get_from_cache as _supabase_get_cache, get_from_cache_cascade
from fastapi import HTTPException
from metrics import SEARCH_DURATION, FETCH_DURATION, CACHE_HITS, CACHE_MISSES, ACTIVE_SEARCHES, SEARCHES, FILTER_DECISIONS, SEARCH_RESPONSE_STATE, FILTER_INPUT_TOTAL, FILTER_OUTPUT_TOTAL, FILTER_DISCARD_RATE, BIDS_PROCESSED_TOTAL, SOURCE_DEGRADATION_TOTAL, PARTIAL_RESULTS_SERVED_TOTAL
from viability import assess_batch as viability_assess_batch
from telemetry import get_tracer, optional_span

logger = logging.getLogger(__name__)

# F-02 AC10: Tracer for pipeline spans
_tracer = get_tracer("search_pipeline")

# ============================================================================
# TD-008 AC20: Helper functions delegated to pipeline/ package
# Re-exported here for backward compatibility with existing imports.
# ============================================================================
from pipeline.helpers import (  # noqa: E402
    _build_pncp_link,
    _calcular_urgencia,
    _calcular_dias_restantes,
    _map_confidence,
    _convert_to_licitacao_items,
    _build_coverage_metrics,
    _build_coverage_metadata,
    _maybe_send_quota_email,
)
from pipeline.cache_manager import (  # noqa: E402
    SEARCH_CACHE_TTL,
    _compute_cache_key,
    _read_cache,
    _write_cache,
    _build_cache_params,
    _maybe_trigger_revalidation,
    _build_degraded_detail,
    apply_stale_cache,
    set_empty_failure,
)

# ============================================================================
# SearchPipeline
# ============================================================================

class SearchPipeline:
    """7-stage search pipeline for procurement opportunity discovery.

    Dependencies that tests mock via routes.search are passed via `deps`
    to maintain backward compatibility with existing test mock paths (AC11).
    """

    def __init__(self, deps: SimpleNamespace):
        """
        Args:
            deps: Namespace with mockable dependencies from routes/search.py:
                - ENABLE_NEW_PRICING (bool)
                - PNCPClient (class)
                - buscar_todas_ufs_paralelo (async function)
                - aplicar_todos_filtros (function)
                - create_excel (function)
                - rate_limiter (RateLimiter instance)
                - check_user_roles (function)
                - match_keywords (function)
                - KEYWORDS_UNIFORMES (set)
                - KEYWORDS_EXCLUSAO (set)
                - validate_terms (function)
        """
        self.deps = deps

    async def run(self, ctx: SearchContext) -> BuscaResponse:
        """Execute all 7 stages in sequence. Returns BuscaResponse."""
        ACTIVE_SEARCHES.inc()

        logger.info(
            "Starting procurement search",
            extra={
                "ufs": ctx.request.ufs,
                "data_inicial": ctx.request.data_inicial,
                "data_final": ctx.request.data_final,
                "setor_id": ctx.request.setor_id,
                "status": ctx.request.status.value if ctx.request.status else None,
                "modalidades": ctx.request.modalidades,
                "valor_minimo": ctx.request.valor_minimo,
                "valor_maximo": ctx.request.valor_maximo,
                "esferas": [e.value for e in ctx.request.esferas] if ctx.request.esferas else None,
                "municipios": ctx.request.municipios,
                "ordenacao": ctx.request.ordenacao,
            },
        )

        # F-02 AC10: Root span for the entire pipeline
        with optional_span(_tracer, "search_pipeline", {
            "search.id": getattr(ctx.request, "search_id", None) or "",
            "search.sector": ctx.request.setor_id or "",
            "search.ufs": ",".join(ctx.request.ufs),
            "search.user_id": ctx.user.get("id", "") if ctx.user else "",
        }) as root_span:
            return await self._run_stages(ctx, root_span)

    async def _run_stages(self, ctx: SearchContext, root_span) -> BuscaResponse:
        """Internal: execute pipeline stages under the root span."""
        # CRIT-003: Get state machine for this search (if available)
        from search_state_manager import get_state_machine
        from models.search_state import SearchState
        sm = get_state_machine(getattr(ctx.request, "search_id", None) or "")

        # Stages 1-3: Critical — exceptions propagate to wrapper
        if sm:
            await sm.transition_to(SearchState.VALIDATING, stage="validate")
        await self._traced_stage(ctx, "pipeline.validate", self.stage_validate)
        await self._traced_stage(ctx, "pipeline.prepare", self.stage_prepare)

        if sm:
            await sm.transition_to(SearchState.FETCHING, stage="execute")
        await self._traced_stage(ctx, "pipeline.fetch", self.stage_execute)

        # Stages 4-5: Filter and enrich
        if sm:
            await sm.transition_to(SearchState.FILTERING, stage="filter")
        await self._traced_stage(ctx, "pipeline.filter", self.stage_filter)

        # GTM-STAB-003 AC4: Time budget guard — skip expensive stages if over budget
        _elapsed_after_filter = sync_time_module.time() - ctx.start_time
        if _elapsed_after_filter > 90:
            logger.warning(
                f"[STAB-003] Time budget exceeded after filter ({_elapsed_after_filter:.1f}s > 90s) — "
                f"skipping LLM and viability, marking is_simplified=True"
            )
            ctx.is_simplified = True
            # STORY-329 AC5: Emit llm_skipped event when LLM skipped due to timeout
            if ctx.tracker:
                await ctx.tracker.emit(
                    "filtering", 70,
                    "Classificação IA ignorada (timeout)",
                    llm_skipped=True, reason="timeout",
                )

        if sm:
            await sm.transition_to(SearchState.ENRICHING, stage="enrich")
        await self._traced_stage(ctx, "pipeline.enrich", self.stage_enrich)

        # Stage 6: Generate output (has internal error boundaries)
        if sm:
            await sm.transition_to(SearchState.GENERATING, stage="generate")
        await self._traced_stage(ctx, "pipeline.generate", self.stage_generate)

        # Stage 7: Persist and build response
        if sm:
            await sm.transition_to(SearchState.PERSISTING, stage="persist")
        try:
            result = await self._traced_stage(ctx, "pipeline.persist", self.stage_persist)
            if sm:
                await sm.transition_to(SearchState.COMPLETED, stage="persist")
            return result
        finally:
            ACTIVE_SEARCHES.dec()
            elapsed_s = sync_time_module.time() - ctx.start_time
            uf_count = str(len(ctx.request.ufs))
            SEARCH_DURATION.labels(
                sector=ctx.request.setor_id or "unknown",
                uf_count=uf_count,
                cache_status=ctx.cache_status or "miss",
            ).observe(elapsed_s)
            result_status = (
                "success" if ctx.licitacoes_filtradas
                else "empty" if not ctx.is_partial
                else "partial"
            )
            _search_mode = "terms" if ctx.custom_terms else "sector"
            SEARCHES.labels(
                sector=ctx.request.setor_id or "unknown",
                result_status=result_status,
                search_mode=_search_mode,
            ).inc()
            # F-02 AC12: Record final status on root span
            root_span.set_attribute("search.result_status", result_status)
            root_span.set_attribute("search.duration_ms", int(elapsed_s * 1000))
            root_span.set_attribute("search.total_raw", len(ctx.licitacoes_raw))
            root_span.set_attribute("search.total_filtered", len(ctx.licitacoes_filtradas))

    @staticmethod
    def _validate_stage_outputs(stage_name: str, ctx: SearchContext) -> None:
        """CRIT-050 AC10-AC12: Validate outputs are correctly typed after each stage.

        Ensures pipeline contracts are met so downstream stages never get None
        where a list or dict is expected.
        """
        if stage_name == "pipeline.fetch":
            # AC12: data_sources must be list (can be empty) after Stage 3
            if ctx.data_sources is None:
                ctx.data_sources = []
            if not isinstance(ctx.licitacoes_raw, list):
                ctx.licitacoes_raw = []
        elif stage_name == "pipeline.filter":
            # AC11: filter_stats must be dict (never None) after Stage 4
            if ctx.filter_stats is None:
                ctx.filter_stats = {}
            if not isinstance(ctx.licitacoes_filtradas, list):
                ctx.licitacoes_filtradas = []

    async def _traced_stage(self, ctx: SearchContext, span_name: str, stage_fn):
        """AC11-AC12: Run a pipeline stage wrapped in a child span with timing and counts."""
        stage_start = sync_time_module.time()
        items_in = len(ctx.licitacoes_raw) if hasattr(ctx, "licitacoes_raw") and ctx.licitacoes_raw else 0

        with optional_span(_tracer, span_name) as span:
            try:
                result = await stage_fn(ctx)
                # CRIT-050 AC10: Validate stage outputs after each stage
                self._validate_stage_outputs(span_name, ctx)
                duration_ms = int((sync_time_module.time() - stage_start) * 1000)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("status", "ok")

                # AC12: items_in / items_out where applicable
                if span_name == "pipeline.fetch":
                    span.set_attribute("items_out", len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0)
                elif span_name == "pipeline.filter":
                    span.set_attribute("items_in", items_in)
                    span.set_attribute("items_out", len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0)

                return result
            except Exception as e:
                duration_ms = int((sync_time_module.time() - stage_start) * 1000)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("status", "error")
                # AC16: Record exception on span
                span.record_exception(e)
                try:
                    from opentelemetry.trace import StatusCode
                    span.set_status(StatusCode.ERROR, str(e))
                except ImportError:
                    pass
                raise

    # ------------------------------------------------------------------
    # Stage 1: ValidateRequest
    # ------------------------------------------------------------------
    async def stage_validate(self, ctx: SearchContext) -> None:
        """Validate request, check quota, resolve plan capabilities.

        May raise HTTPException (403, 429, 503) — these propagate to the wrapper.
        """
        deps = self.deps

        # Admin/Master detection
        ctx.is_admin, ctx.is_master = await deps.check_user_roles(ctx.user["id"])
        if ctx.user["id"].lower() in get_admin_ids():
            ctx.is_admin = True
            ctx.is_master = True

        # Rate limiting (before quota check)
        if not (ctx.is_admin or ctx.is_master):
            try:
                quick_quota = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
                max_rpm = quick_quota.capabilities.get("max_requests_per_min", 10)
            except Exception as e:
                logger.warning(f"Failed to get rate limit for user {mask_user_id(ctx.user['id'])}: {e}")
                max_rpm = 10

            rate_allowed, retry_after = await deps.rate_limiter.check_rate_limit(ctx.user["id"], max_rpm)

            if not rate_allowed:
                logger.warning(
                    f"Rate limit exceeded for user {mask_user_id(ctx.user['id'])}: "
                    f"{max_rpm} req/min limit, retry after {retry_after}s"
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Limite de requisições excedido ({max_rpm}/min). Aguarde {retry_after} segundos.",
                    headers={"Retry-After": str(retry_after)},
                )

            logger.debug(f"Rate limit check passed for user {mask_user_id(ctx.user['id'])}: {max_rpm} req/min")

        # CRIT-002 AC5: Register session BEFORE quota consumption
        try:
            ctx.session_id = await quota.register_search_session(
                user_id=ctx.user["id"],
                sectors=[ctx.request.setor_id],
                ufs=ctx.request.ufs,
                data_inicial=ctx.request.data_inicial,
                data_final=ctx.request.data_final,
                custom_keywords=ctx.request.termos_busca.split(",") if ctx.request.termos_busca else None,
                search_id=ctx.request.search_id,
            )
            if ctx.session_id is None:
                # AC23: Graceful degradation — continue without session tracking
                logger.critical(
                    "Failed to register search session — continuing without session tracking"
                )
        except Exception as reg_err:
            # AC23: Registration failure does NOT block search
            logger.critical(
                f"Failed to register search session — continuing without session tracking: {reg_err}"
            )
            ctx.session_id = None

        # GTM-ARCH-001 AC8: Skip quota consumption if already done in POST (async path)
        if ctx.quota_pre_consumed:
            logger.debug(f"ARCH-001: Quota pre-consumed for {mask_user_id(ctx.user['id'])} — skipping quota check")
            ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
            return

        # GTM-INFRA-003 AC5-AC8: Check cache BEFORE quota — skip quota if fully cached
        if not (ctx.is_admin or ctx.is_master) and deps.ENABLE_NEW_PRICING:
            try:
                _cache_params = {
                    "setor_id": ctx.request.setor_id,
                    "ufs": ctx.request.ufs,
                    "status": ctx.request.status.value if ctx.request.status else None,
                    "modalidades": ctx.request.modalidades,
                    "modo_busca": ctx.request.modo_busca if hasattr(ctx.request, "modo_busca") else None,
                }
                _cache_result = await _supabase_get_cache(ctx.user["id"], _cache_params)
                if _cache_result and _cache_result.get("results"):
                    # AC5: Cache hit — skip quota consumption entirely
                    ctx.from_cache = True
                    ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])
                    if not ctx.quota_info.allowed:
                        raise HTTPException(status_code=403, detail=ctx.quota_info.error_message)
                    # AC10: Structured log
                    from search_cache import compute_search_hash
                    _ph = compute_search_hash(_cache_params)
                    logger.info(
                        f"Quota skipped for user {mask_user_id(ctx.user['id'])}: "
                        f"response fully cached (params_hash={_ph[:12]})"
                    )
                    # AC9: Increment metric
                    from metrics import CACHE_QUOTA_SKIPPED
                    CACHE_QUOTA_SKIPPED.inc()
                    # CRIT-002 AC7: Still mark session as processing
                    if ctx.session_id:
                        asyncio.create_task(
                            quota.update_search_session_status(
                                ctx.session_id, status="processing", pipeline_stage="validate"
                            )
                        )
                    return
            except HTTPException:
                raise
            except Exception as cache_check_err:
                # Cache check failed — proceed with normal quota flow
                logger.debug(f"INFRA-003: Pre-quota cache check failed (proceeding normally): {cache_check_err}")

        # Quota resolution
        if ctx.is_admin or ctx.is_master:
            role = "ADMIN" if ctx.is_admin else "MASTER"
            logger.info(f"{role} user detected: {mask_user_id(ctx.user['id'])} - bypassing quota check")
            ctx.quota_info = get_master_quota_info(is_admin=ctx.is_admin)
        elif deps.ENABLE_NEW_PRICING:
            logger.debug("New pricing enabled, checking quota and plan capabilities")
            try:
                ctx.quota_info = await asyncio.to_thread(quota.check_quota, ctx.user["id"])

                if not ctx.quota_info.allowed:
                    raise HTTPException(status_code=403, detail=ctx.quota_info.error_message)

                # CRIT-050 AC7: Safe .get() access on capabilities dict
                _max_monthly = ctx.quota_info.capabilities.get("max_requests_per_month", 1000)
                allowed, new_quota_used, quota_remaining_after = await asyncio.to_thread(
                    quota.check_and_increment_quota_atomic,
                    ctx.user["id"],
                    _max_monthly,
                )

                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            f"Limite de {_max_monthly} "
                            f"análises mensais atingido. Renova em "
                            f"{ctx.quota_info.quota_reset_date.strftime('%d/%m/%Y')}."
                        )
                    )

                ctx.quota_info.quota_used = new_quota_used
                ctx.quota_info.quota_remaining = quota_remaining_after

                # CRIT-002 AC7: Set status='processing' after quota passes
                if ctx.session_id:
                    asyncio.create_task(
                        quota.update_search_session_status(
                            ctx.session_id, status="processing", pipeline_stage="validate"
                        )
                    )

                # STORY-225 AC10/AC11: Quota email notifications (fire-and-forget)
                # STORY-290-patch: offload sync Supabase query to thread pool
                asyncio.create_task(
                    asyncio.to_thread(_maybe_send_quota_email, ctx.user["id"], new_quota_used, ctx.quota_info)
                )
            except HTTPException as http_exc:
                # CRIT-002 AC5: If quota fails after registration, mark session as failed
                if ctx.session_id:
                    asyncio.create_task(
                        quota.update_search_session_status(
                            ctx.session_id,
                            status="failed",
                            error_code="quota_exceeded",
                            error_message=str(http_exc.detail)[:500],
                            pipeline_stage="validate",
                            completed_at=datetime.now(_tz.utc).isoformat(),
                            duration_ms=int((sync_time_module.time() - ctx.start_time) * 1000),
                        )
                    )
                raise
            except RuntimeError as e:
                logger.error(f"Supabase configuration error: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
                )
            except Exception as e:
                logger.warning(f"Quota check failed (continuing with fallback): {e}")
                ctx.quota_info = quota.create_fallback_quota_info(ctx.user["id"])
        else:
            logger.debug("New pricing disabled, using legacy behavior (no quota limits)")
            ctx.quota_info = quota.create_legacy_quota_info()

    # ------------------------------------------------------------------
    # Stage 2: PrepareSearch
    # ------------------------------------------------------------------
    async def stage_prepare(self, ctx: SearchContext) -> None:
        """Load sector, parse custom terms, configure keywords and exclusions."""
        # GTM-FIX-032 AC3: Override dates for "abertas" mode using explicit UTC
        if ctx.request.modo_busca == "abertas":
            from datetime import timedelta, timezone, datetime as dt
            today = dt.now(timezone.utc).date()  # AC3.2: explicit UTC
            ctx.request.data_inicial = (today - timedelta(days=10)).isoformat()
            ctx.request.data_final = today.isoformat()
            logger.info(
                f"modo_busca='abertas': date range overridden to "
                f"{ctx.request.data_inicial} → {ctx.request.data_final} (10 days, UTC)"
            )

        # GTM-FIX-032 AC3.1: Normalize all dates to canonical YYYY-MM-DD
        from datetime import date as date_type
        d_ini = date_type.fromisoformat(ctx.request.data_inicial)
        d_fin = date_type.fromisoformat(ctx.request.data_final)
        ctx.request.data_inicial = d_ini.isoformat()
        ctx.request.data_final = d_fin.isoformat()
        logger.debug(f"stage_prepare: dates normalized to {ctx.request.data_inicial} → {ctx.request.data_final}")

        try:
            ctx.sector = get_sector(ctx.request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.debug(f"Using sector: {ctx.sector.name} ({len(ctx.sector.keywords)} keywords)")

        ctx.custom_terms = []
        ctx.stopwords_removed = []
        ctx.min_match_floor_value = None

        if ctx.request.termos_busca and ctx.request.termos_busca.strip():
            parsed_terms = parse_search_terms(ctx.request.termos_busca)
            validated = self.deps.validate_terms(parsed_terms)

            if not validated['valid']:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Nenhum termo válido para busca",
                        "termos_ignorados": validated['ignored'],
                        "motivos_ignorados": validated['reasons'],
                        "sugestao": "Use termos mais específicos (mínimo 4 caracteres, evite palavras comuns como 'de', 'da', etc.)"
                    }
                )

            ctx.custom_terms = validated['valid']
            ctx.stopwords_removed = validated['ignored']

            logger.debug(
                f"Term validation: {len(ctx.custom_terms)} valid, {len(ctx.stopwords_removed)} ignored. "
                f"Valid={ctx.custom_terms}, Ignored={list(validated['reasons'].keys())}"
            )

            if ctx.custom_terms and not ctx.request.show_all_matches:
                ctx.min_match_floor_value = calculate_min_matches(len(ctx.custom_terms))
                logger.debug(
                    f"Min match floor: {ctx.min_match_floor_value} "
                    f"(total_terms={len(ctx.custom_terms)})"
                )

        if ctx.custom_terms:
            ctx.active_keywords = set(ctx.custom_terms)
            logger.debug(f"Using {len(ctx.custom_terms)} custom search terms: {ctx.custom_terms}")
        else:
            ctx.active_keywords = set(ctx.sector.keywords)
            logger.debug(f"Using sector keywords ({len(ctx.active_keywords)} terms)")

        # Determine exclusions
        # STORY-267 AC11: Partial exclusions for custom_terms + vestuario
        if ctx.request.exclusion_terms:
            ctx.active_exclusions = set(ctx.request.exclusion_terms)
            ctx.active_context_required = None
        elif ctx.custom_terms and ctx.request.setor_id and ctx.request.setor_id != "vestuario":
            ctx.active_exclusions = ctx.sector.exclusions
            ctx.active_context_required = ctx.sector.context_required_keywords
        elif not ctx.custom_terms:
            ctx.active_exclusions = ctx.sector.exclusions
            ctx.active_context_required = ctx.sector.context_required_keywords
        else:
            # STORY-267 AC11: custom_terms + vestuario — apply PARTIAL exclusions
            # Remove exclusions that contain any of the user's custom terms (avoid self-exclusion)
            # Keep exclusions unrelated to custom terms (reduce noise)
            from config import get_feature_flag
            if get_feature_flag("TERM_SEARCH_FILTER_CONTEXT"):
                all_exclusions = ctx.sector.exclusions
                terms_lower = {t.lower() for t in ctx.custom_terms}
                partial_exclusions = set()
                for exc in all_exclusions:
                    exc_lower = exc.lower()
                    # Keep exclusion only if it does NOT contain any custom term
                    if not any(term in exc_lower for term in terms_lower):
                        partial_exclusions.add(exc)
                removed_count = len(all_exclusions) - len(partial_exclusions)
                if removed_count > 0:
                    logger.debug(
                        f"STORY-267 AC11: Removed {removed_count} self-exclusions "
                        f"for custom terms {ctx.custom_terms}"
                    )
                ctx.active_exclusions = partial_exclusions
            else:
                ctx.active_exclusions = set()
            ctx.active_context_required = None

        # STORY-260 AC5: Load user profile for LLM analysis
        try:
            from supabase_client import get_supabase, sb_execute
            _db = get_supabase()
            _profile_row = await sb_execute(
                _db.table("profiles").select("context_data").eq("id", ctx.user["id"]).single()
            )
            ctx.user_profile = (_profile_row.data or {}).get("context_data") or {}
        except Exception as _prof_err:
            logger.debug(f"Could not load user profile: {_prof_err}")
            ctx.user_profile = None

        # SSE: Sector ready
        if ctx.tracker:
            await ctx.tracker.emit("connecting", 8, f"Setor '{ctx.sector.name}' configurado, conectando ao PNCP...")

    # ------------------------------------------------------------------
    # Stage 3: ExecuteSearch
    # ------------------------------------------------------------------
    async def stage_execute(self, ctx: SearchContext) -> None:
        """Fetch procurement data from PNCP API (and optionally other sources)."""
        # CRIT-002 AC8: Track pipeline stage
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(ctx.session_id, pipeline_stage="execute")
            )

        deps = self.deps
        request = ctx.request

        # STORY-257A AC8-10: Search results cache
        cache_key = _compute_cache_key(request)

        # AC10: Respect force_fresh flag
        if not request.force_fresh:
            cached = _read_cache(cache_key)
            if cached:
                logger.debug(f"Cache HIT for search (cached_at={cached.get('cached_at', 'unknown')})")
                ctx.licitacoes_raw = cached.get("licitacoes", [])
                ctx.cached = True
                ctx.cached_at = cached.get("cached_at")
                ctx.cache_status = "fresh"  # InMemory cache is always fresh (< 6h TTL)
                ctx.cache_level = "redis"  # InMemory serves as L2 cache
                CACHE_HITS.labels(level="memory", freshness="fresh").inc()
                # Skip the actual fetch — go straight to filtering
                return
            else:
                CACHE_MISSES.labels(level="memory").inc()

            # STORY-282 AC3: Cache-first — check Supabase/cascade for stale cache
            # If stale cache exists, return it IMMEDIATELY and dispatch background refresh
            if ctx.user and ctx.user.get("id"):
                try:
                    from search_cache import trigger_background_revalidation
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

        # GTM-FIX-029 AC16/AC17: Raised from 4min→6min, configurable via env
        # Hierarchy: FE proxy (480s) > Pipeline (360s) > Consolidation (300s) > Per-Source (180s) > Per-UF (90s)
        FETCH_TIMEOUT = int(os.environ.get("SEARCH_FETCH_TIMEOUT", str(6 * 60)))  # 6 minutes

        if enable_multi_source:
            await self._execute_multi_source(
                ctx, request, deps, modalidades_to_fetch, status_value,
                uf_progress_callback, FETCH_TIMEOUT,
                uf_status_callback=uf_status_callback,
            )
        else:
            await self._execute_pncp_only(
                ctx, request, deps, use_parallel, modalidades_to_fetch,
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

        # STORY-257A AC8 + GTM-FIX-010 AC3: Cache write-through on successful fetch
        if ctx.licitacoes_raw and len(ctx.licitacoes_raw) > 0:
            cache_data = {
                "licitacoes": ctx.licitacoes_raw,
                "total": len(ctx.licitacoes_raw),
                "cached_at": datetime.now(_tz.utc).isoformat(),
                "search_params": {
                    "setor_id": request.setor_id,
                    "ufs": request.ufs,
                    "status": request.status.value if request.status else None,
                },
            }
            _write_cache(cache_key, cache_data)
            logger.debug(f"Cache WRITE: {len(ctx.licitacoes_raw)} results cached (TTL={SEARCH_CACHE_TTL}s)")

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
                try:
                    await _supabase_save_cache(
                        user_id=ctx.user["id"],
                        params={
                            "setor_id": request.setor_id,
                            "ufs": request.ufs,
                            "status": request.status.value if request.status else None,
                            "modalidades": request.modalidades,
                            "modo_busca": request.modo_busca,
                        },
                        results=ctx.licitacoes_raw,
                        sources=sources,
                        fetch_duration_ms=fetch_elapsed_ms,
                        coverage=coverage_data,
                    )
                except Exception as e:
                    logger.warning(f"Supabase cache write failed (non-fatal): {e}")

    async def _execute_multi_source(
        self, ctx, request, deps, modalidades_to_fetch, status_value,
        uf_progress_callback, fetch_timeout, uf_status_callback=None,
    ):
        """Multi-source consolidation path (STORY-177)."""
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
        skipped_sources: list[str] = []  # STORY-305 AC9: CB OPEN → skip source

        # STORY-305 AC8-AC9: Check circuit breaker before adding each source
        pncp_cb = get_circuit_breaker("pncp")
        pcp_cb = get_circuit_breaker("pcp")
        comprasgov_cb = get_circuit_breaker("comprasgov")

        if source_config.pncp.enabled:
            if pncp_cb.is_degraded:
                logger.warning("[MULTI-SOURCE] PNCP circuit breaker OPEN — skipping source")
                skipped_sources.append("PNCP")
            else:
                adapters["PNCP"] = PNCPLegacyAdapter(
                    ufs=request.ufs,
                    modalidades=modalidades_to_fetch,
                    status=status_value,
                    on_uf_complete=uf_progress_callback,
                    on_uf_status=uf_status_callback,
                )

        if source_config.compras_gov.enabled:
            from config import COMPRASGOV_CB_ENABLED
            if COMPRASGOV_CB_ENABLED and comprasgov_cb.is_degraded:
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
        # ConsolidationService handles empty adapters → AllSourcesFailedError → cache stale path.
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
                    ufs=set(request.ufs),
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

            # A-03 AC7: Unified cache cascade (L2 → L1 → L3)
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

            # A-03 AC5: Unified cache cascade (L2 → L1 → L3)
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

            # A-03 AC6: Unified cache cascade (L2 → L1 → L3)
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
        self, ctx, request, deps, use_parallel, modalidades_to_fetch,
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
                    logger.warning(f"Parallel fetch failed, falling back to sequential: {e}")
                    # GTM-INFRA-001 AC1/AC3: Wrap sync PNCPClient in asyncio.to_thread()
                    # to prevent blocking the event loop with requests.Session + time.sleep()
                    client = deps.PNCPClient()
                    return await asyncio.to_thread(
                        lambda: list(
                            client.fetch_all(
                                data_inicial=request.data_inicial,
                                data_final=request.data_final,
                                ufs=request.ufs,
                                modalidades=modalidades_to_fetch,
                            )
                        )
                    )
            else:
                # GTM-INFRA-001 AC1/AC3: Wrap sync PNCPClient in asyncio.to_thread()
                # to prevent blocking the event loop with requests.Session + time.sleep()
                client = deps.PNCPClient()
                return await asyncio.to_thread(
                    lambda: list(
                        client.fetch_all(
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            ufs=request.ufs,
                            modalidades=modalidades_to_fetch,
                        )
                    )
                )

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

            # A-03 AC7: Unified cache cascade (L2 → L1 → L3)
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

            # A-03 AC5: Unified cache cascade (L2 → L1 → L3)
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

    # ------------------------------------------------------------------
    # Stage 4: FilterResults
    # ------------------------------------------------------------------
    async def stage_filter(self, ctx: SearchContext) -> None:
        """Apply all filters (UF, status, esfera, modalidade, municipio, valor, keyword)."""
        # CRIT-002 AC9: Track pipeline stage
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(ctx.session_id, pipeline_stage="filter")
            )

        deps = self.deps
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
                    # AC2: interpolate 60→65 for keyword matching
                    pct = 60 + int((processed / max(total, 1)) * 5)
                    msg = f"Filtrando: {processed}/{total}"
                elif phase == "llm_classify":
                    # AC3: interpolate 65→70 for LLM zero-match
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
        from filter_stats import discard_rate_tracker
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
        # Level 0 = normal (no relaxation), 1 = no min_match_floor, 2 = no keyword filter
        # NOTE: level 1 is already handled above via the min_match relaxation block (ctx.filter_relaxed)
        ctx.relaxation_level = 0
        if ctx.filter_relaxed:
            ctx.relaxation_level = 1
        if (
            ctx.custom_terms
            and len(ctx.licitacoes_filtradas) == 0
            and len(ctx.licitacoes_raw) > 0
        ):
            # Level 2: re-run without any keyword exclusions (accept any UF/valor match)
            logger.info(
                "[STAB-005] Zero results with custom_terms — "
                "attempting keyword-free relaxation (level 2)"
            )
            _l2_filtered, _l2_stats = deps.aplicar_todos_filtros(
                ctx.licitacoes_raw,
                ufs_selecionadas=set(request.ufs),
                status=status_filter,
                modalidades=request.modalidades,
                valor_min=request.valor_minimo,
                valor_max=request.valor_maximo,
                esferas=esferas_values,
                municipios=request.municipios,
                keywords=None,  # STAB-005 AC4 level 2: remove keyword filter
                exclusions=None,
                context_required=None,
                min_match_floor=None,
                setor=ctx.request.setor_id,
                modo_busca=request.modo_busca or "publicacao",
                custom_terms=None,  # no keyword matching
            )
            if _l2_filtered:
                ctx.licitacoes_filtradas = _l2_filtered
                ctx.filter_stats = _l2_stats
                ctx.relaxation_level = 2
                logger.info(
                    f"[STAB-005] Level-2 relaxation recovered {len(_l2_filtered)} results"
                )
            else:
                # Level 3: return top 10 by value without any filter
                logger.info(
                    "[STAB-005] Level-3 relaxation: top 10 by value (no keyword filter)"
                )
                _l3_candidates = sorted(
                    ctx.licitacoes_raw,
                    key=lambda bid: float(bid.get("valorTotalEstimado") or bid.get("valorEstimado") or 0),
                    reverse=True,
                )[:10]
                if _l3_candidates:
                    ctx.licitacoes_filtradas = _l3_candidates
                    ctx.relaxation_level = 3
                    logger.info(
                        f"[STAB-005] Level-3 relaxation returned {len(_l3_candidates)} results by value"
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

    # ------------------------------------------------------------------
    # Stage 5: EnrichResults
    # ------------------------------------------------------------------
    async def stage_enrich(self, ctx: SearchContext) -> None:
        """Compute relevance scores, viability assessment, confidence-based re-ranking, and sorting."""

        # D-04 AC7: Viability assessment (Stage 4.5 — post-filter, pre-ranking)
        from config import get_feature_flag
        if get_feature_flag("VIABILITY_ASSESSMENT_ENABLED") and ctx.licitacoes_filtradas and not ctx.is_simplified:
            # Get sector-specific value range
            vr = None
            if ctx.sector and hasattr(ctx.sector, "viability_value_range"):
                vr = ctx.sector.viability_value_range
            ufs_busca = set(ctx.request.ufs) if ctx.request.ufs else set()
            viability_assess_batch(ctx.licitacoes_filtradas, ufs_busca, vr, user_profile=ctx.user_profile, custom_terms=ctx.custom_terms or None)
            # CRIT-FLT-003 AC4: Log zero-value proportion
            total = len(ctx.licitacoes_filtradas)
            zero_count = sum(
                1 for bid in ctx.licitacoes_filtradas
                if bid.get("_value_source") == "missing"
            )
            zero_pct = round(zero_count / total * 100, 1) if total else 0.0
            logger.info(
                "CRIT-FLT-003: zero_value_stats",
                extra={"zero_value_count": zero_count, "total_bids": total, "zero_value_pct": zero_pct},
            )
            logger.debug(
                f"D-04: Viability assessed for {total} bids. "
                f"Alta: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'alta')}, "
                f"Media: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'media')}, "
                f"Baixa: {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_viability_level') == 'baixa')}, "
                f"Zero-value: {zero_count}/{total} ({zero_pct}%)"
            )

        # Relevance scoring (STORY-178)
        if ctx.custom_terms and ctx.licitacoes_filtradas:
            for lic in ctx.licitacoes_filtradas:
                matched_terms = lic.get("_matched_terms", [])
                phrase_count = count_phrase_matches(matched_terms)
                lic["_relevance_score"] = score_relevance(
                    len(matched_terms), len(ctx.custom_terms), phrase_count
                )

        # D-02 AC5 + D-04 AC9: Re-ranking by combined score when viability active
        # Falls back to confidence-only when viability is disabled
        if ctx.licitacoes_filtradas:
            viability_active = get_feature_flag("VIABILITY_ASSESSMENT_ENABLED") and any(
                bid.get("_viability_score") is not None for bid in ctx.licitacoes_filtradas
            )

            def _confidence_sort_key(lic: dict) -> tuple:
                conf = lic.get("_confidence_score", 50)
                valor = float(lic.get("valorTotalEstimado") or lic.get("valorEstimado") or 0)

                if viability_active:
                    # D-04 AC9: combined_score = confidence * 0.6 + viability * 0.4
                    viab = lic.get("_viability_score", 50)
                    combined = conf * 0.6 + viab * 0.4
                    lic["_combined_score"] = round(combined)
                    return (-combined, -valor)

                # Band: 0=high(>=80), 1=medium(50-79), 2=low(<50)
                if conf >= 80:
                    band = 0
                elif conf >= 50:
                    band = 1
                else:
                    band = 2
                return (band, -conf, -valor)

            ctx.licitacoes_filtradas.sort(key=_confidence_sort_key)
            logger.debug(
                f"D-02 AC5: Re-ranked {len(ctx.licitacoes_filtradas)} results by confidence. "
                f"High(>=80): {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_confidence_score', 50) >= 80)}, "
                f"Medium(50-79): {sum(1 for bid in ctx.licitacoes_filtradas if 50 <= bid.get('_confidence_score', 50) < 80)}, "
                f"Low(<50): {sum(1 for bid in ctx.licitacoes_filtradas if bid.get('_confidence_score', 50) < 50)}"
            )

        # User-requested sorting (applied AFTER confidence re-ranking for non-default)
        if ctx.licitacoes_filtradas and ctx.request.ordenacao != "data_desc":
            logger.debug(f"Applying user sorting: ordenacao='{ctx.request.ordenacao}'")
            ctx.licitacoes_filtradas = ordenar_licitacoes(
                ctx.licitacoes_filtradas,
                ordenacao=ctx.request.ordenacao,
                termos_busca=ctx.custom_terms if ctx.custom_terms else list(ctx.active_keywords)[:10],
            )

        if ctx.licitacoes_filtradas:
            filter_elapsed = sync_time_module.time() - ctx.start_time
            logger.debug(
                f"Filtering and sorting complete in {filter_elapsed:.2f}s: "
                f"{len(ctx.licitacoes_filtradas)} results ordered by '{ctx.request.ordenacao}'"
            )

    # ------------------------------------------------------------------
    # Stage 6: GenerateOutput
    # ------------------------------------------------------------------
    async def stage_generate(self, ctx: SearchContext) -> None:
        """Generate LLM summary, Excel report, and convert to LicitacaoItems."""
        # CRIT-002 AC10: Track pipeline stage
        if ctx.session_id:
            asyncio.create_task(
                quota.update_search_session_status(ctx.session_id, pipeline_stage="generate")
            )

        deps = self.deps

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
        )

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

        if queue_available and search_id:
            # === QUEUE MODE: Dispatch to background, return fast ===
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
            await self._enrich_with_sanctions(ctx)

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
                    from job_queue import store_pending_review_bids, is_queue_available, enqueue_job
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

                    if await is_queue_available():
                        await enqueue_job(
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
    async def _enrich_with_sanctions(self, ctx: SearchContext) -> None:
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

    # ------------------------------------------------------------------
    # Stage 7: Persist
    # ------------------------------------------------------------------
    async def stage_persist(self, ctx: SearchContext) -> BuscaResponse:
        """Save search session to history and return response.

        Errors in session save do NOT fail the search request.
        """
        # CRIT-050 AC8: Ensure resumo is never None (fallback if stage_generate crashed)
        if ctx.resumo is None:
            from llm import gerar_resumo_fallback
            ctx.resumo = gerar_resumo_fallback(
                ctx.licitacoes_filtradas,
                sector_name=ctx.sector.name if ctx.sector else "geral",
            )

        # AC26: Emit structured log per search completion
        elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)
        # CRIT-005 AC3: Increment response state counter
        SEARCH_RESPONSE_STATE.labels(state=ctx.response_state).inc()
        # CRIT-053 AC7: Track partial results served
        if ctx.is_partial:
            PARTIAL_RESULTS_SERVED_TOTAL.inc()

        # Determine which sources were attempted, succeeded, and failed
        sources_attempted = []
        sources_succeeded = []
        sources_failed_with_reason = []

        if ctx.source_stats_data:
            # Multi-source path
            for stat in ctx.source_stats_data:
                src_code = stat.get("source_code", "unknown")
                sources_attempted.append(src_code)
                if stat.get("error"):
                    sources_failed_with_reason.append({
                        "source": src_code,
                        "reason": stat["error"][:100]  # Truncate long error messages
                    })
                elif stat.get("status") == "degraded":
                    # CRIT-053 AC1: Degraded sources NOT counted as succeeded
                    pass
                else:
                    sources_succeeded.append(src_code)
        else:
            # PNCP-only path
            sources_attempted = ["PNCP"]
            if ctx.licitacoes_raw is not None:
                sources_succeeded = ["PNCP"]
            else:
                sources_failed_with_reason = [{"source": "PNCP", "reason": "unknown"}]

        # CRIT-052 AC4: Include canary telemetry in search_complete
        canary_info = getattr(ctx, "_pncp_canary_result", None) or {}
        logger.info(json.dumps({
            "event": "search_complete",
            "search_id": ctx.request.search_id or "no_id",
            "sources_attempted": sources_attempted,
            "sources_succeeded": sources_succeeded,
            "sources_failed": [s["source"] for s in sources_failed_with_reason],
            "cache_hit": ctx.cached,
            "pncp_circuit_breaker": "degraded" if get_circuit_breaker("pncp").is_degraded else "healthy",
            "pcp_circuit_breaker": "degraded" if get_circuit_breaker("pcp").is_degraded else "healthy",
            "comprasgov_circuit_breaker": "degraded" if get_circuit_breaker("comprasgov").is_degraded else "healthy",
            "pncp_canary_status": canary_info.get("cron_status", "unknown"),
            "pncp_canary_latency_ms": canary_info.get("latency_ms"),
            "sources_degraded": ctx.sources_degraded or [],
            "total_results": len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
            "total_filtered": len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0,
            "ufs_requested": len(ctx.request.ufs),
            "ufs_succeeded": len(ctx.succeeded_ufs) if ctx.succeeded_ufs else 0,
            "ufs_failed": len(ctx.failed_ufs) if ctx.failed_ufs else 0,
            "failed_ufs": ctx.failed_ufs or [],
            "is_partial": ctx.is_partial,
            "latency_ms": elapsed_ms,
        }))

        # CRIT-002 AC11: Update existing session OR fallback to full INSERT
        if ctx.user:
            total_filtered = len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0
            valor_total = ctx.resumo.valor_total if ctx.resumo else 0.0
            resumo_exec = ctx.resumo.resumo_executivo if ctx.resumo else None
            destaques_val = (ctx.resumo.destaques if ctx.licitacoes_filtradas else []) if ctx.resumo else None

            if ctx.session_id:
                # AC11: Session was pre-registered — UPDATE with results
                try:
                    await quota.update_search_session_status(
                        ctx.session_id,
                        status="completed",
                        pipeline_stage="persist",
                        completed_at=datetime.now(_tz.utc).isoformat(),
                        duration_ms=elapsed_ms,
                        raw_count=len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
                        total_filtered=total_filtered,
                        valor_total=valor_total,
                        resumo_executivo=resumo_exec,
                        destaques=destaques_val,
                        response_state=ctx.response_state,
                    )
                    logger.debug(
                        f"Search session updated to completed: {ctx.session_id[:8]}*** "
                        f"for user {mask_user_id(ctx.user['id'])}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to update session {ctx.session_id[:8]}***: "
                        f"{type(e).__name__}: {e}",
                        exc_info=True,
                    )
            else:
                # AC23: Fallback — no pre-registered session (graceful degradation)
                try:
                    ctx.session_id = await quota.save_search_session(
                        user_id=ctx.user["id"],
                        sectors=[ctx.request.setor_id],
                        ufs=ctx.request.ufs,
                        data_inicial=ctx.request.data_inicial,
                        data_final=ctx.request.data_final,
                        custom_keywords=ctx.custom_terms if ctx.custom_terms else None,
                        total_raw=len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
                        total_filtered=total_filtered,
                        valor_total=valor_total,
                        resumo_executivo=resumo_exec,
                        destaques=destaques_val,
                    )
                    logger.debug(
                        f"Search session saved (fallback): {ctx.session_id[:8] if ctx.session_id else 'None'}*** "
                        f"for user {mask_user_id(ctx.user['id'])}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to save search session for user "
                        f"{mask_user_id(ctx.user['id'])}: {type(e).__name__}: {e}",
                        exc_info=True,
                    )

        # If response was already built (e.g., empty results early return in stage_generate)
        if ctx.response is not None and not ctx.licitacoes_filtradas:
            return ctx.response

        return ctx.response


# ============================================================================
# GTM-ARCH-001: Standalone functions for ARQ Worker consumption
# ============================================================================

def build_default_deps() -> SimpleNamespace:
    """GTM-ARCH-001 AC2: Build default deps namespace for Worker context.

    The Worker process doesn't have the route-level module imports, so we
    import everything directly here. These are the same deps that
    routes/search.py passes via SimpleNamespace.
    """
    from config import ENABLE_NEW_PRICING
    from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
    from filter import (
        aplicar_todos_filtros,
        match_keywords,
        KEYWORDS_UNIFORMES,
        KEYWORDS_EXCLUSAO,
        validate_terms,
    )
    from excel import create_excel
    from rate_limiter import rate_limiter
    from authorization import check_user_roles

    return SimpleNamespace(
        ENABLE_NEW_PRICING=ENABLE_NEW_PRICING,
        PNCPClient=PNCPClient,
        buscar_todas_ufs_paralelo=buscar_todas_ufs_paralelo,
        aplicar_todos_filtros=aplicar_todos_filtros,
        create_excel=create_excel,
        rate_limiter=rate_limiter,
        check_user_roles=check_user_roles,
        match_keywords=match_keywords,
        KEYWORDS_UNIFORMES=KEYWORDS_UNIFORMES,
        KEYWORDS_EXCLUSAO=KEYWORDS_EXCLUSAO,
        validate_terms=validate_terms,
    )


async def executar_busca_completa(
    search_id: str,
    request_data: dict,
    user_data: dict,
    tracker=None,
    quota_pre_consumed: bool = False,
) -> "BuscaResponse":
    """GTM-ARCH-001 AC2: Execute full search pipeline — designed for ARQ Worker.

    Reconstructs the BuscaRequest and SearchContext from serializable dicts,
    builds default deps, and runs the full 7-stage pipeline.

    Args:
        search_id: UUID for SSE correlation and result persistence.
        request_data: Serialized BuscaRequest dict (from model_dump()).
        user_data: User dict with id, plan, roles, etc.
        tracker: Optional ProgressTracker (if None, creates one from Redis).
        quota_pre_consumed: AC8 — True when quota consumed in POST before enqueue.

    Returns:
        BuscaResponse with full search results.
    """
    from schemas import BuscaRequest
    from progress import get_tracker, create_tracker
    import time as _time

    # Reconstruct request from serialized data
    request = BuscaRequest(**request_data)
    request.search_id = search_id

    # Get or create tracker
    if tracker is None:
        tracker = await get_tracker(search_id)
    if tracker is None:
        tracker = await create_tracker(search_id, len(request.ufs))

    deps = build_default_deps()
    pipeline = SearchPipeline(deps)
    ctx = SearchContext(
        request=request,
        user=user_data,
        tracker=tracker,
        start_time=_time.time(),
        quota_pre_consumed=quota_pre_consumed,
    )

    return await pipeline.run(ctx)
