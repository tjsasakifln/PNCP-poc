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
import hashlib
import json
import logging
import os
import time as sync_time_module
from datetime import datetime, timezone
from types import SimpleNamespace

import quota  # Module-level import; accessed via quota.func() for mock compatibility

from search_context import SearchContext
from schemas import BuscaResponse, FilterStats, ResumoLicitacoes, ResumoEstrategico, LicitacaoItem, DataSourceStatus
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
from redis_pool import get_fallback_cache
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ============================================================================
# STORY-225: Quota email notification helper
# ============================================================================

def _maybe_send_quota_email(user_id: str, quota_used: int, quota_info) -> None:
    """Send quota warning/exhaustion email if threshold reached.

    AC10: Warning at 80% usage.
    AC11: Exhaustion at 100% usage.
    Fire-and-forget: never blocks the search pipeline.
    """
    try:
        max_quota = quota_info.capabilities.get("max_requests_per_month", 0)
        if max_quota <= 0:
            return

        pct = quota_used / max_quota
        reset_date = quota_info.quota_reset_date.strftime("%d/%m/%Y")

        # Get user email
        from supabase_client import get_supabase
        sb = get_supabase()
        profile = sb.table("profiles").select("email, full_name, email_unsubscribed").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return
        if profile.data.get("email_unsubscribed"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = quota_info.plan_name

        from email_service import send_email_async

        if pct >= 1.0:
            from templates.emails.quota import render_quota_exhausted_email
            html = render_quota_exhausted_email(
                user_name=name, plan_name=plan_name,
                quota_limit=max_quota, reset_date=reset_date,
            )
            send_email_async(
                to=email,
                subject=f"Limite de buscas atingido — {plan_name}",
                html=html,
                tags=[{"name": "category", "value": "quota_exhausted"}],
            )
        elif pct >= 0.8 and (quota_used - 1) / max_quota < 0.8:
            # Only send at the exact crossing of 80% threshold
            from templates.emails.quota import render_quota_warning_email
            html = render_quota_warning_email(
                user_name=name, plan_name=plan_name,
                quota_used=quota_used, quota_limit=max_quota,
                reset_date=reset_date,
            )
            send_email_async(
                to=email,
                subject=f"Aviso de cota: {quota_used}/{max_quota} buscas usadas",
                html=html,
                tags=[{"name": "category", "value": "quota_warning"}],
            )
    except Exception as e:
        # Never fail the search pipeline due to email errors
        logger.warning(f"Failed to send quota email for user {mask_user_id(user_id)}: {e}")


# ============================================================================
# Helper functions (moved from routes/search.py)
# ============================================================================

def _build_pncp_link(lic: dict) -> str:
    """Build PNCP link from bid data.

    Priority: linkSistemaOrigem > linkProcessoEletronico > constructed URL.
    """
    link = lic.get("linkSistemaOrigem") or lic.get("linkProcessoEletronico")

    if not link:
        numero_controle = lic.get("numeroControlePNCP", "")
        if numero_controle:
            try:
                partes = numero_controle.split("/")
                if len(partes) == 2:
                    ano = partes[1]
                    cnpj_tipo_seq = partes[0].split("-")
                    if len(cnpj_tipo_seq) >= 3:
                        cnpj = cnpj_tipo_seq[0]
                        sequencial = cnpj_tipo_seq[2].lstrip("0")
                        if cnpj and ano and sequencial:
                            link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial}"
            except Exception:
                pass

    return link or ""


def _calcular_urgencia(dias_restantes: int | None) -> str | None:
    """Classify urgency based on days remaining until deadline."""
    if dias_restantes is None:
        return None
    if dias_restantes < 0:
        return "encerrada"
    if dias_restantes < 7:
        return "critica"
    if dias_restantes < 14:
        return "alta"
    if dias_restantes <= 30:
        return "media"
    return "baixa"


def _calcular_dias_restantes(data_encerramento_str: str | None) -> int | None:
    """Calculate days remaining from today to the deadline date."""
    if not data_encerramento_str:
        return None
    try:
        from datetime import date
        enc = date.fromisoformat(data_encerramento_str[:10])
        return (enc - date.today()).days
    except (ValueError, TypeError):
        return None


def _convert_to_licitacao_items(licitacoes: list[dict]) -> list[LicitacaoItem]:
    """Convert raw bid dictionaries to LicitacaoItem objects for frontend display."""
    items = []
    for lic in licitacoes:
        try:
            data_enc = lic.get("dataEncerramentoProposta", "")[:10] if lic.get("dataEncerramentoProposta") else None
            dias_rest = _calcular_dias_restantes(data_enc)
            item = LicitacaoItem(
                pncp_id=lic.get("codigoCompra", lic.get("numeroControlePNCP", "")),
                objeto=lic.get("objetoCompra", "")[:500],
                orgao=lic.get("nomeOrgao", ""),
                uf=lic.get("uf", ""),
                municipio=lic.get("municipio"),
                valor=lic.get("valorTotalEstimado") or 0.0,
                modalidade=lic.get("modalidadeNome"),
                data_publicacao=lic.get("dataPublicacaoPncp", "")[:10] if lic.get("dataPublicacaoPncp") else None,
                data_abertura=lic.get("dataAberturaProposta", "")[:10] if lic.get("dataAberturaProposta") else None,
                data_encerramento=data_enc,
                dias_restantes=dias_rest,
                urgencia=_calcular_urgencia(dias_rest),
                link=_build_pncp_link(lic),
                source=lic.get("_source"),
                relevance_score=lic.get("_relevance_score"),
                matched_terms=lic.get("_matched_terms"),
            )
            items.append(item)
        except Exception as e:
            logger.warning(f"Failed to convert bid to LicitacaoItem: {e}")
            continue
    return items


# ============================================================================
# STORY-257A: Search results cache helpers
# ============================================================================

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


def _read_cache(cache_key: str):
    """Read from InMemoryCache. Returns parsed dict or None."""
    cache = get_fallback_cache()
    raw = cache.get(cache_key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _write_cache(cache_key: str, data: dict) -> None:
    """Write search results to InMemoryCache with TTL."""
    cache = get_fallback_cache()
    try:
        cache.setex(cache_key, SEARCH_CACHE_TTL, json.dumps(data, default=str))
    except Exception as e:
        logger.warning(f"Failed to write search cache: {e}")


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

        # Stages 1-3: Critical — exceptions propagate to wrapper
        await self.stage_validate(ctx)
        await self.stage_prepare(ctx)
        await self.stage_execute(ctx)

        # Stages 4-5: Filter and enrich
        await self.stage_filter(ctx)
        await self.stage_enrich(ctx)

        # Stage 6: Generate output (has internal error boundaries)
        await self.stage_generate(ctx)

        # Stage 7: Persist and build response
        return await self.stage_persist(ctx)

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
                quick_quota = quota.check_quota(ctx.user["id"])
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

        # Quota resolution
        if ctx.is_admin or ctx.is_master:
            role = "ADMIN" if ctx.is_admin else "MASTER"
            logger.info(f"{role} user detected: {mask_user_id(ctx.user['id'])} - bypassing quota check")
            ctx.quota_info = get_master_quota_info(is_admin=ctx.is_admin)
        elif deps.ENABLE_NEW_PRICING:
            logger.debug("New pricing enabled, checking quota and plan capabilities")
            try:
                ctx.quota_info = quota.check_quota(ctx.user["id"])

                if not ctx.quota_info.allowed:
                    raise HTTPException(status_code=403, detail=ctx.quota_info.error_message)

                allowed, new_quota_used, quota_remaining_after = quota.check_and_increment_quota_atomic(
                    ctx.user["id"],
                    ctx.quota_info.capabilities["max_requests_per_month"]
                )

                if not allowed:
                    raise HTTPException(
                        status_code=429,
                        detail=(
                            f"Limite de {ctx.quota_info.capabilities['max_requests_per_month']} "
                            f"buscas mensais atingido. Renova em "
                            f"{ctx.quota_info.quota_reset_date.strftime('%d/%m/%Y')}."
                        )
                    )

                ctx.quota_info.quota_used = new_quota_used
                ctx.quota_info.quota_remaining = quota_remaining_after

                # STORY-225 AC10/AC11: Quota email notifications (fire-and-forget)
                _maybe_send_quota_email(ctx.user["id"], new_quota_used, ctx.quota_info)
            except HTTPException:
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
        # STORY-240 AC2: Override dates for "abertas" mode
        if ctx.request.modo_busca == "abertas":
            from datetime import date, timedelta
            today = date.today()
            ctx.request.data_inicial = (today - timedelta(days=180)).isoformat()
            ctx.request.data_final = today.isoformat()
            logger.info(
                f"modo_busca='abertas': date range overridden to "
                f"{ctx.request.data_inicial} → {ctx.request.data_final} (180 days)"
            )

        try:
            ctx.sector = get_sector(ctx.request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Using sector: {ctx.sector.name} ({len(ctx.sector.keywords)} keywords)")

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

            logger.info(
                f"Term validation: {len(ctx.custom_terms)} valid, {len(ctx.stopwords_removed)} ignored. "
                f"Valid={ctx.custom_terms}, Ignored={list(validated['reasons'].keys())}"
            )

            if ctx.custom_terms and not ctx.request.show_all_matches:
                ctx.min_match_floor_value = calculate_min_matches(len(ctx.custom_terms))
                logger.info(
                    f"Min match floor: {ctx.min_match_floor_value} "
                    f"(total_terms={len(ctx.custom_terms)})"
                )

        if ctx.custom_terms:
            ctx.active_keywords = set(ctx.custom_terms)
            logger.info(f"Using {len(ctx.custom_terms)} custom search terms: {ctx.custom_terms}")
        else:
            ctx.active_keywords = set(ctx.sector.keywords)
            logger.info(f"Using sector keywords ({len(ctx.active_keywords)} terms)")

        # Determine exclusions
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
            ctx.active_exclusions = set()
            ctx.active_context_required = None

        # SSE: Sector ready
        if ctx.tracker:
            await ctx.tracker.emit("connecting", 8, f"Setor '{ctx.sector.name}' configurado, conectando ao PNCP...")

    # ------------------------------------------------------------------
    # Stage 3: ExecuteSearch
    # ------------------------------------------------------------------
    async def stage_execute(self, ctx: SearchContext) -> None:
        """Fetch procurement data from PNCP API (and optionally other sources)."""
        deps = self.deps
        request = ctx.request

        # STORY-257A AC8-10: Search results cache
        cache_key = _compute_cache_key(request)

        # AC10: Respect force_fresh flag
        if not request.force_fresh:
            cached = _read_cache(cache_key)
            if cached:
                logger.info(f"Cache HIT for search (cached_at={cached.get('cached_at', 'unknown')})")
                ctx.licitacoes_raw = cached.get("licitacoes", [])
                ctx.cached = True
                ctx.cached_at = cached.get("cached_at")
                # Skip the actual fetch — go straight to filtering
                return

        enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
        ctx.source_stats_data = None

        use_parallel = len(request.ufs) > 1
        status_value = request.status.value if request.status else None
        modalidades_to_fetch = request.modalidades if request.modalidades else None

        # SSE: Starting fetch
        if ctx.tracker:
            msg = f"Iniciando busca em {len(request.ufs)} estados..."
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

        FETCH_TIMEOUT = 4 * 60  # 4 minutes

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

        # SSE: Fetch complete
        if ctx.tracker:
            await ctx.tracker.emit(
                "fetching", 55,
                f"Busca concluida: {len(ctx.licitacoes_raw)} licitacoes encontradas",
                total_raw=len(ctx.licitacoes_raw),
            )

        # Enrich with inferred status
        logger.info("Enriching bids with inferred status...")
        enriquecer_com_status_inferido(ctx.licitacoes_raw)
        logger.info(f"Status inference complete for {len(ctx.licitacoes_raw)} bids")

        # STORY-257A AC8: Cache write-through on successful fetch
        if ctx.licitacoes_raw and len(ctx.licitacoes_raw) > 0:
            cache_data = {
                "licitacoes": ctx.licitacoes_raw,
                "total": len(ctx.licitacoes_raw),
                "cached_at": datetime.now().isoformat() + "Z",
                "search_params": {
                    "setor_id": request.setor_id,
                    "ufs": request.ufs,
                    "status": request.status.value if request.status else None,
                },
            }
            _write_cache(cache_key, cache_data)
            logger.info(f"Cache WRITE: {len(ctx.licitacoes_raw)} results cached (TTL={SEARCH_CACHE_TTL}s)")

    async def _execute_multi_source(
        self, ctx, request, deps, modalidades_to_fetch, status_value,
        uf_progress_callback, fetch_timeout, uf_status_callback=None,
    ):
        """Multi-source consolidation path (STORY-177)."""
        logger.info("Multi-source fetch enabled, using ConsolidationService")
        from consolidation import ConsolidationService
        from clients.compras_gov_client import ComprasGovAdapter
        from clients.portal_compras_client import PortalComprasAdapter
        from source_config.sources import get_source_config
        from pncp_client import PNCPLegacyAdapter

        source_config = get_source_config()

        # STORY-257A AC13: Only include sources that are actually available
        available_sources = source_config.get_available_sources()
        logger.info(f"Available sources: {[s.code.value for s in available_sources]}")
        pending_creds = source_config.get_pending_credentials()
        if pending_creds:
            logger.warning(f"Sources with pending credentials: {pending_creds}")

        adapters = {}

        if source_config.pncp.enabled:
            adapters["PNCP"] = PNCPLegacyAdapter(
                ufs=request.ufs,
                modalidades=modalidades_to_fetch,
                status=status_value,
                on_uf_complete=uf_progress_callback,
                on_uf_status=uf_status_callback,
            )

        if source_config.compras_gov.enabled:
            adapters["COMPRAS_GOV"] = ComprasGovAdapter(
                timeout=source_config.compras_gov.timeout
            )

        if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
            adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                api_key=source_config.portal.credentials.api_key,
                timeout=source_config.portal.timeout,
            )

        # STORY-252 T8: Create ComprasGov fallback adapter for last-resort use
        # when all primary sources fail (AC15). Only effective if ComprasGov
        # is NOT already included as a primary adapter.
        fallback_adapter = ComprasGovAdapter(
            timeout=source_config.compras_gov.timeout
        )

        consolidation_svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=source_config.consolidation.timeout_per_source,
            timeout_global=source_config.consolidation.timeout_global,
            fail_on_all_errors=source_config.consolidation.fail_on_all_errors,
            fallback_adapter=fallback_adapter,
        )

        source_complete_cb = None
        if ctx.tracker:
            def source_complete_cb(src_code, count, error):
                logger.info(f"[MULTI-SOURCE] {src_code}: {count} records, error={error}")

        try:
            consolidation_result = await asyncio.wait_for(
                consolidation_svc.fetch_all(
                    data_inicial=request.data_inicial,
                    data_final=request.data_final,
                    ufs=set(request.ufs),
                    on_source_complete=source_complete_cb,
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
                }
                for sr in consolidation_result.source_results
            ]

            # STORY-252 T8: Map consolidation degradation state to pipeline context
            ctx.is_partial = consolidation_result.is_partial
            ctx.degradation_reason = consolidation_result.degradation_reason
            ctx.data_sources = [
                DataSourceStatus(
                    source=sr.source_code,
                    status="ok" if sr.status == "success" else sr.status,
                    records=sr.record_count,
                )
                for sr in consolidation_result.source_results
            ]

            logger.info(
                f"Multi-source fetch: {consolidation_result.total_before_dedup} raw -> "
                f"{consolidation_result.total_after_dedup} deduped "
                f"({consolidation_result.duplicates_removed} dupes removed)"
                f"{' [PARTIAL]' if ctx.is_partial else ''}"
            )
        except AllSourcesFailedError as e:
            # STORY-252 T8: All sources failed — return empty results with
            # detailed degradation info instead of crashing the request.
            logger.error(f"All sources failed during multi-source fetch: {e}")
            ctx.licitacoes_raw = []
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
        except asyncio.TimeoutError:
            logger.error(f"Multi-source fetch timed out after {fetch_timeout}s")
            if ctx.tracker:
                await ctx.tracker.emit_error("Busca expirou por tempo")
                from progress import remove_tracker
                await remove_tracker(ctx.request.search_id)
            raise HTTPException(
                status_code=504,
                detail=(
                    f"A busca excedeu o tempo limite de {fetch_timeout // 60} minutos. "
                    f"Tente com menos estados ou um período menor."
                ),
            )
        finally:
            await consolidation_svc.close()

    async def _execute_pncp_only(
        self, ctx, request, deps, use_parallel, modalidades_to_fetch,
        status_value, uf_progress_callback, fetch_timeout,
        uf_status_callback=None,
    ):
        """PNCP-only fetch path (default)."""
        logger.info(f"Fetching bids from PNCP API for {len(request.ufs)} UFs")

        # STORY-257A AC1: Circuit breaker try_recover only (degraded mode tries with reduced concurrency)
        cb = get_circuit_breaker()
        await cb.try_recover()

        async def _do_fetch() -> list:
            if use_parallel:
                logger.info(f"Using parallel fetch for {len(request.ufs)} UFs (max_concurrent=10)")
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
                        return fetch_result.items
                    return fetch_result
                except PNCPDegradedError:
                    raise  # Re-raise to be handled by outer try/except
                except Exception as e:
                    logger.warning(f"Parallel fetch failed, falling back to sequential: {e}")
                    client = deps.PNCPClient()
                    return list(
                        client.fetch_all(
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            ufs=request.ufs,
                            modalidades=modalidades_to_fetch,
                        )
                    )
            else:
                client = deps.PNCPClient()
                return list(
                    client.fetch_all(
                        data_inicial=request.data_inicial,
                        data_final=request.data_final,
                        ufs=request.ufs,
                        modalidades=modalidades_to_fetch,
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
            # STORY-252 T8: PNCP circuit breaker tripped during fetch.
            # Return empty results with degradation info rather than crashing.
            logger.warning(f"PNCP degraded during fetch: {e}")
            ctx.licitacoes_raw = []
            ctx.is_partial = True
            ctx.degradation_reason = (
                "PNCP ficou indisponivel durante a busca (circuit breaker ativado). "
                "Tente novamente em alguns minutos."
            )
            ctx.data_sources = [
                DataSourceStatus(source="PNCP", status="error", records=0)
            ]
        except asyncio.TimeoutError:
            logger.error(f"PNCP fetch timed out after {fetch_timeout}s for {len(request.ufs)} UFs")
            if ctx.tracker:
                await ctx.tracker.emit_error("Busca expirou por tempo")
                from progress import remove_tracker
                await remove_tracker(ctx.request.search_id)
            raise HTTPException(
                status_code=504,
                detail=(
                    f"A busca excedeu o tempo limite de {fetch_timeout // 60} minutos. "
                    f"Tente com menos estados ou um periodo menor."
                ),
            )

    # ------------------------------------------------------------------
    # Stage 4: FilterResults
    # ------------------------------------------------------------------
    async def stage_filter(self, ctx: SearchContext) -> None:
        """Apply all filters (UF, status, esfera, modalidade, municipio, valor, keyword)."""
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
            min_match_floor=ctx.min_match_floor_value,
            modo_busca=request.modo_busca or "publicacao",
        )

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
                modo_busca=request.modo_busca or "publicacao",
            )
            ctx.hidden_by_min_match = 0

        # Detailed logging
        logger.info(
            f"Filtering complete: {len(ctx.licitacoes_filtradas)}/{len(ctx.licitacoes_raw)} bids passed"
        )
        stats = ctx.filter_stats
        if stats:
            logger.info(f"  - Total processadas: {stats.get('total', len(ctx.licitacoes_raw))}")
            logger.info(f"  - Aprovadas: {stats.get('aprovadas', len(ctx.licitacoes_filtradas))}")
            logger.info(f"  - Rejeitadas (UF): {stats.get('rejeitadas_uf', 0)}")
            logger.info(f"  - Rejeitadas (Status): {stats.get('rejeitadas_status', 0)}")
            logger.info(f"  - Rejeitadas (Esfera): {stats.get('rejeitadas_esfera', 0)}")
            logger.info(f"  - Rejeitadas (Modalidade): {stats.get('rejeitadas_modalidade', 0)}")
            logger.info(f"  - Rejeitadas (Município): {stats.get('rejeitadas_municipio', 0)}")
            logger.info(f"  - Rejeitadas (Valor): {stats.get('rejeitadas_valor', 0)}")
            logger.info(f"  - Rejeitadas (Keyword): {stats.get('rejeitadas_keyword', 0)}")
            logger.info(f"  - Rejeitadas (Min Match): {stats.get('rejeitadas_min_match', 0)}")
            logger.info(f"  - Rejeitadas (Outros): {stats.get('rejeitadas_outros', 0)}")

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

        # SSE: Filtering complete
        if ctx.tracker:
            await ctx.tracker.emit(
                "filtering", 70,
                f"Filtragem concluida: {len(ctx.licitacoes_filtradas)} resultados",
                total_filtered=len(ctx.licitacoes_filtradas),
            )

    # ------------------------------------------------------------------
    # Stage 5: EnrichResults
    # ------------------------------------------------------------------
    async def stage_enrich(self, ctx: SearchContext) -> None:
        """Compute relevance scores and apply sorting."""

        # Relevance scoring (STORY-178)
        if ctx.custom_terms and ctx.licitacoes_filtradas:
            for lic in ctx.licitacoes_filtradas:
                matched_terms = lic.get("_matched_terms", [])
                phrase_count = count_phrase_matches(matched_terms)
                lic["_relevance_score"] = score_relevance(
                    len(matched_terms), len(ctx.custom_terms), phrase_count
                )

        # Sorting
        if ctx.licitacoes_filtradas:
            logger.info(f"Applying sorting: ordenacao='{ctx.request.ordenacao}'")
            ctx.licitacoes_filtradas = ordenar_licitacoes(
                ctx.licitacoes_filtradas,
                ordenacao=ctx.request.ordenacao,
                termos_busca=ctx.custom_terms if ctx.custom_terms else list(ctx.active_keywords)[:10],
            )

            filter_elapsed = sync_time_module.time() - ctx.start_time
            logger.info(
                f"Filtering and sorting complete in {filter_elapsed:.2f}s: "
                f"{len(ctx.licitacoes_filtradas)} results ordered by '{ctx.request.ordenacao}'"
            )

    # ------------------------------------------------------------------
    # Stage 6: GenerateOutput
    # ------------------------------------------------------------------
    async def stage_generate(self, ctx: SearchContext) -> None:
        """Generate LLM summary, Excel report, and convert to LicitacaoItems."""
        deps = self.deps

        # Build filter stats for frontend
        fs = FilterStats(
            rejeitadas_uf=ctx.filter_stats.get("rejeitadas_uf", 0),
            rejeitadas_valor=ctx.filter_stats.get("rejeitadas_valor", 0),
            rejeitadas_keyword=ctx.filter_stats.get("rejeitadas_keyword", 0),
            rejeitadas_min_match=ctx.filter_stats.get("rejeitadas_min_match", 0),
            rejeitadas_prazo=ctx.filter_stats.get("rejeitadas_prazo", 0),
            rejeitadas_outros=ctx.filter_stats.get("rejeitadas_outros", 0),
        )

        # Early return path: no results passed filters
        if not ctx.licitacoes_filtradas:
            logger.info("No bids passed filters — skipping LLM and Excel generation")
            if ctx.tracker:
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
                insight_setorial=f"Não foram encontradas oportunidades de {ctx.sector.name.lower()} nos filtros selecionados. Considere ampliar o período ou os estados de busca.",
            )

            new_quota_used = ctx.quota_info.quota_used if ctx.quota_info else 0
            quota_remaining = ctx.quota_info.quota_remaining if ctx.quota_info else 0

            ctx.response = BuscaResponse(
                resumo=ctx.resumo,
                licitacoes=[],
                excel_base64=None if not ctx.quota_info or not ctx.quota_info.capabilities["allow_excel"] else "",
                excel_available=ctx.quota_info.capabilities["allow_excel"] if ctx.quota_info else False,
                quota_used=new_quota_used,
                quota_remaining=quota_remaining,
                total_raw=len(ctx.licitacoes_raw),
                total_filtrado=0,
                filter_stats=fs,
                termos_utilizados=ctx.custom_terms if ctx.custom_terms else None,
                stopwords_removidas=ctx.stopwords_removed if ctx.stopwords_removed else None,
                upgrade_message="Exportar Excel disponível no plano Máquina (R$ 597/mês)." if ctx.quota_info and not ctx.quota_info.capabilities["allow_excel"] else None,
                source_stats=ctx.source_stats_data,
                hidden_by_min_match=ctx.hidden_by_min_match if ctx.custom_terms else None,
                filter_relaxed=ctx.filter_relaxed if ctx.custom_terms else None,
                is_partial=ctx.is_partial,
                data_sources=ctx.data_sources,
                degradation_reason=ctx.degradation_reason,
                failed_ufs=ctx.failed_ufs,
                succeeded_ufs=ctx.succeeded_ufs,
                total_ufs_requested=len(ctx.request.ufs),
                cached=getattr(ctx, 'cached', False),
                cached_at=getattr(ctx, 'cached_at', None),
            )
            return  # Skip stages 6b-7 (handled here for early return)

        # SSE: Starting LLM
        if ctx.tracker:
            await ctx.tracker.emit("llm", 75, "Gerando resumo executivo com IA...")

        # LLM summary (with fallback)
        logger.info("Generating executive summary")
        try:
            ctx.resumo = gerar_resumo(ctx.licitacoes_filtradas, sector_name=ctx.sector.name)
            logger.info("LLM summary generated successfully")
        except Exception as e:
            logger.warning(
                f"LLM generation failed, using fallback mechanism: {e}",
                exc_info=True,
            )
            ctx.resumo = gerar_resumo_fallback(ctx.licitacoes_filtradas, sector_name=ctx.sector.name)
            logger.info("Fallback summary generated successfully")

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

        # SSE: Starting Excel
        if ctx.tracker:
            await ctx.tracker.emit("excel", 92, "Gerando planilha Excel...")

        # Excel generation (conditional on plan)
        ctx.excel_base64 = None
        ctx.download_url = None
        ctx.excel_available = ctx.quota_info.capabilities["allow_excel"] if ctx.quota_info else False
        ctx.upgrade_message = None

        if ctx.excel_available:
            logger.info("Generating Excel report")
            excel_buffer = deps.create_excel(ctx.licitacoes_filtradas)
            excel_bytes = excel_buffer.read()

            storage_result = upload_excel(excel_bytes, ctx.request.search_id)

            if storage_result:
                ctx.download_url = storage_result["signed_url"]
                logger.info(
                    f"Excel uploaded to storage: {storage_result['file_path']} "
                    f"(signed URL valid for {storage_result['expires_in']}s)"
                )
                ctx.excel_base64 = None
            else:
                # STORY-226 AC15: Removed filesystem/base64 fallback.
                # Rely exclusively on object storage. If upload fails,
                # report Excel as temporarily unavailable.
                logger.error(
                    "Excel storage upload failed — no fallback. "
                    "Excel will be unavailable for this search."
                )
                ctx.excel_base64 = None
                ctx.download_url = None
                ctx.excel_available = False
                ctx.upgrade_message = (
                    "Erro temporário ao gerar Excel. Tente novamente em alguns instantes."
                )
        else:
            logger.info("Excel generation skipped (not allowed for user's plan)")
            ctx.upgrade_message = "Exportar Excel disponível no plano Máquina (R$ 597/mês)."

        # Convert to LicitacaoItems
        ctx.licitacao_items = _convert_to_licitacao_items(ctx.licitacoes_filtradas)

        # STORY-256 AC13: Sanctions enrichment (opt-in)
        if ctx.request.check_sanctions and ctx.licitacao_items:
            await self._enrich_with_sanctions(ctx)

        new_quota_used = ctx.quota_info.quota_used if ctx.quota_info else 0
        quota_remaining = ctx.quota_info.quota_remaining if ctx.quota_info else 0

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
            source_stats=ctx.source_stats_data,
            hidden_by_min_match=ctx.hidden_by_min_match if ctx.custom_terms else None,
            filter_relaxed=ctx.filter_relaxed if ctx.custom_terms else None,
            ultima_atualizacao=datetime.now().isoformat() + "Z",
            is_partial=ctx.is_partial,
            data_sources=ctx.data_sources,
            degradation_reason=ctx.degradation_reason,
            failed_ufs=ctx.failed_ufs,
            succeeded_ufs=ctx.succeeded_ufs,
            total_ufs_requested=len(ctx.request.ufs),
            cached=getattr(ctx, 'cached', False),
            cached_at=getattr(ctx, 'cached_at', None),
        )

        logger.info(
            "Search completed successfully",
            extra={
                "total_raw": ctx.response.total_raw,
                "total_filtrado": ctx.response.total_filtrado,
                "valor_total": ctx.resumo.valor_total,
            },
        )

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
        from services.sanctions_service import SanctionsService, SanctionsSummary
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
                logger.info("[SANCTIONS] No valid CNPJs found in results, skipping")
                return

            unique_cnpjs = list(cnpj_map.keys())
            logger.info(f"[SANCTIONS] Checking {len(unique_cnpjs)} unique CNPJs from {len(ctx.licitacao_items)} results")

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

            logger.info(
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
        # AC26: Emit structured log per search completion
        elapsed_ms = int((sync_time_module.time() - ctx.start_time) * 1000)

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
                else:
                    sources_succeeded.append(src_code)
        else:
            # PNCP-only path
            sources_attempted = ["PNCP"]
            if ctx.licitacoes_raw is not None:
                sources_succeeded = ["PNCP"]
            else:
                sources_failed_with_reason = [{"source": "PNCP", "reason": "unknown"}]

        is_partial = len(sources_failed_with_reason) > 0 and len(sources_succeeded) > 0

        logger.info(json.dumps({
            "event": "search_complete",
            "search_id": ctx.request.search_id or "no_id",
            "sources_attempted": sources_attempted,
            "sources_succeeded": sources_succeeded,
            "sources_failed": [s["source"] for s in sources_failed_with_reason],
            "cache_hit": getattr(ctx, 'cached', False),
            "circuit_breaker_state": "degraded" if get_circuit_breaker().is_degraded else "healthy",
            "total_results": len(ctx.licitacoes_raw) if ctx.licitacoes_raw else 0,
            "total_filtered": len(ctx.licitacoes_filtradas) if ctx.licitacoes_filtradas else 0,
            "ufs_requested": len(ctx.request.ufs),
            "ufs_succeeded": len(ctx.succeeded_ufs) if ctx.succeeded_ufs else 0,
            "ufs_failed": len(ctx.failed_ufs) if ctx.failed_ufs else 0,
            "failed_ufs": ctx.failed_ufs or [],
            "is_partial": ctx.is_partial,
            "latency_ms": elapsed_ms,
        }))

        # If response was already built (e.g., empty results early return in stage_generate)
        if ctx.response is not None and not ctx.licitacoes_filtradas:
            # Save session even for zero results
            if ctx.user:
                try:
                    ctx.session_id = quota.save_search_session(
                        user_id=ctx.user["id"],
                        sectors=[ctx.request.setor_id],
                        ufs=ctx.request.ufs,
                        data_inicial=ctx.request.data_inicial,
                        data_final=ctx.request.data_final,
                        custom_keywords=ctx.custom_terms if ctx.custom_terms else None,
                        total_raw=len(ctx.licitacoes_raw),
                        total_filtered=0,
                        valor_total=0.0,
                        resumo_executivo=ctx.resumo.resumo_executivo if ctx.resumo else None,
                        destaques=[],
                    )
                    logger.info(f"Search session saved (0 results): {ctx.session_id[:8]}*** for user {mask_user_id(ctx.user['id'])}")
                except Exception as e:
                    logger.error(
                        f"Failed to save search session for user {mask_user_id(ctx.user['id'])}: {type(e).__name__}: {e}",
                        exc_info=True,
                    )
            return ctx.response

        # Save session for non-empty results
        if ctx.user:
            try:
                ctx.session_id = quota.save_search_session(
                    user_id=ctx.user["id"],
                    sectors=[ctx.request.setor_id],
                    ufs=ctx.request.ufs,
                    data_inicial=ctx.request.data_inicial,
                    data_final=ctx.request.data_final,
                    custom_keywords=ctx.custom_terms if ctx.custom_terms else None,
                    total_raw=len(ctx.licitacoes_raw),
                    total_filtered=len(ctx.licitacoes_filtradas),
                    valor_total=ctx.resumo.valor_total if ctx.resumo else 0.0,
                    resumo_executivo=ctx.resumo.resumo_executivo if ctx.resumo else None,
                    destaques=ctx.resumo.destaques if ctx.resumo else None,
                )
                logger.info(f"Search session saved: {ctx.session_id[:8]}*** for user {mask_user_id(ctx.user['id'])}")
            except Exception as e:
                logger.error(
                    f"Failed to save search session for user {mask_user_id(ctx.user['id'])}: {type(e).__name__}: {e}",
                    exc_info=True,
                )

        return ctx.response
