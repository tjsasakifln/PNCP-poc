"""
Search Router - Main procurement search endpoint and SSE progress tracking.

This router handles the core search functionality:
- POST /buscar: Main search orchestration (fetch → filter → LLM → Excel)
- GET /buscar-progress/{search_id}: SSE stream for real-time progress updates

Extracted from main.py as part of modular routing architecture.
"""

import asyncio
import base64
import logging
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import StreamingResponse

from config import ENABLE_NEW_PRICING
from schemas import BuscaRequest, BuscaResponse, FilterStats, ResumoLicitacoes, LicitacaoItem
from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import (
    remove_stopwords,
    aplicar_todos_filtros,
    match_keywords,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    validate_terms,
)
from status_inference import enriquecer_com_status_inferido
from utils.ordenacao import ordenar_licitacoes
from excel import create_excel
from storage import upload_excel
from llm import gerar_resumo, gerar_resumo_fallback
from sectors import get_sector, list_sectors
from auth import require_auth
from authorization import _check_user_roles, _get_admin_ids, _get_master_quota_info
from log_sanitizer import mask_user_id, log_user_action
from rate_limiter import rate_limiter
from progress import create_tracker, get_tracker, remove_tracker, subscribe_to_events

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


def _build_pncp_link(lic: dict) -> str:
    """
    Build PNCP link from bid data.

    Priority: linkSistemaOrigem > linkProcessoEletronico > constructed URL from numeroControlePNCP
    """
    link = lic.get("linkSistemaOrigem") or lic.get("linkProcessoEletronico")

    if not link:
        numero_controle = lic.get("numeroControlePNCP", "")
        if numero_controle:
            try:
                # Parse: "67366310000103-1-000189/2025" -> cnpj=67366310000103, ano=2025, seq=189
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
    """
    Convert raw bid dictionaries to LicitacaoItem objects for frontend display.
    """
    items = []
    for lic in licitacoes:
        try:
            data_enc = lic.get("dataEncerramentoProposta", "")[:10] if lic.get("dataEncerramentoProposta") else None
            dias_rest = _calcular_dias_restantes(data_enc)
            item = LicitacaoItem(
                pncp_id=lic.get("codigoCompra", lic.get("numeroControlePNCP", "")),
                objeto=lic.get("objetoCompra", "")[:500],  # Truncate long descriptions
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


@router.get("/buscar-progress/{search_id}")
async def buscar_progress_stream(
    search_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    """
    SSE endpoint for real-time search progress updates.

    The client opens this connection simultaneously with POST /buscar,
    using the same search_id to correlate progress events.

    Events:
        - connecting (5%): Initial setup
        - fetching (10-55%): Per-UF progress with uf_index/uf_total
        - filtering (60-70%): Filter application
        - llm (75-90%): LLM summary generation
        - excel (92-98%): Excel report generation
        - complete (100%): Search finished
        - error: Search failed
    """
    import asyncio as _asyncio
    import json as _json

    async def event_generator():
        # Wait up to 30s for the tracker to be created by POST /buscar
        tracker = None
        for _ in range(60):  # 60 * 0.5s = 30s
            tracker = await get_tracker(search_id)
            if tracker:
                break
            await _asyncio.sleep(0.5)

        if not tracker:
            yield f"data: {_json.dumps({'stage': 'error', 'progress': -1, 'message': 'Search not found'})}\n\n"
            return

        # Try Redis pub/sub first, fallback to in-memory queue
        pubsub = await subscribe_to_events(search_id)

        if pubsub:
            # Redis mode: Stream from pub/sub channel
            logger.debug(f"SSE using Redis pub/sub for {search_id}")
            try:
                while True:
                    try:
                        message = await _asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=30.0)
                        if message and message["type"] == "message":
                            # Redis returns JSON string, parse it
                            event_data = _json.loads(message["data"])
                            yield f"data: {_json.dumps(event_data)}\n\n"

                            if event_data.get("stage") in ("complete", "error"):
                                break

                    except _asyncio.TimeoutError:
                        # Heartbeat to keep connection alive
                        yield ": heartbeat\n\n"

                    except _asyncio.CancelledError:
                        break

            finally:
                await pubsub.unsubscribe()
                await pubsub.close()

        else:
            # In-memory mode: Stream from local queue
            logger.debug(f"SSE using in-memory queue for {search_id}")
            while True:
                try:
                    event = await _asyncio.wait_for(tracker.queue.get(), timeout=30.0)
                    yield f"data: {_json.dumps(event.to_dict())}\n\n"

                    if event.stage in ("complete", "error"):
                        break

                except _asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield ": heartbeat\n\n"

                except _asyncio.CancelledError:
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(
    request: BuscaRequest,
    user: dict = Depends(require_auth),
):
    """
    Main search endpoint - orchestrates the complete pipeline.

    Workflow:
        1. Fetch bids from PNCP API (with automatic pagination)
        2. Apply sequential filters (UF, value, keywords, status)
        3. Generate executive summary via GPT-4.1-nano (with fallback)
        4. Create formatted Excel report
        5. Return summary + base64-encoded Excel

    Args:
        request: BuscaRequest with ufs, data_inicial, data_final

    Returns:
        BuscaResponse with resumo, excel_base64, total_raw, total_filtrado

    Raises:
        HTTPException 502: PNCP API error (network, timeout, invalid response)
        HTTPException 503: PNCP rate limit exceeded (retry after N seconds)
        HTTPException 500: Internal server error (unexpected failure)

    Example:
        >>> request = BuscaRequest(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2025-01-01",
        ...     data_final="2025-01-31"
        ... )
        >>> response = await buscar_licitacoes(request)
        >>> response.total_filtrado
        15
    """
    import time as sync_time
    from datetime import timezone

    start_time = sync_time.time()

    # SSE Progress Tracking: Create tracker if search_id provided
    tracker = None
    if request.search_id:
        tracker = await create_tracker(request.search_id, len(request.ufs))
        await tracker.emit("connecting", 3, "Iniciando busca...")

    logger.info(
        "Starting procurement search",
        extra={
            "ufs": request.ufs,
            "data_inicial": request.data_inicial,
            "data_final": request.data_final,
            "setor_id": request.setor_id,
            "status": request.status.value if request.status else None,
            "modalidades": request.modalidades,
            "valor_minimo": request.valor_minimo,
            "valor_maximo": request.valor_maximo,
            "esferas": [e.value for e in request.esferas] if request.esferas else None,
            "municipios": request.municipios,
            "ordenacao": request.ordenacao,
        },
    )

    # FEATURE FLAG: New Pricing Model (STORY-165)
    from quota import check_quota, QuotaInfo, PLAN_CAPABILITIES, get_plan_from_profile, PLAN_NAMES

    # ADMIN/MASTER BYPASS: Get highest tier automatically (no quota/rate limits)
    is_admin, is_master = _check_user_roles(user["id"])
    # Also check env var for admin override
    if user["id"].lower() in _get_admin_ids():
        is_admin = True
        is_master = True

    # -----------------------------------------------------------------
    # RATE LIMITING CHECK (per-minute, plan-based)
    # Must happen BEFORE quota check to prevent abuse
    # Admins/masters bypass rate limiting
    # -----------------------------------------------------------------
    if not (is_admin or is_master):
        # Get user's plan to determine rate limit
        # Quick check to get max_requests_per_min without full quota check
        try:
            quick_quota = check_quota(user["id"])
            max_rpm = quick_quota.capabilities.get("max_requests_per_min", 10)
        except Exception as e:
            logger.warning(f"Failed to get rate limit for user {mask_user_id(user['id'])}: {e}")
            # Fallback to conservative limit (consultor_agil level)
            max_rpm = 10

        rate_allowed, retry_after = rate_limiter.check_rate_limit(user["id"], max_rpm)

        if not rate_allowed:
            logger.warning(
                f"Rate limit exceeded for user {mask_user_id(user['id'])}: "
                f"{max_rpm} req/min limit, retry after {retry_after}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Limite de requisições excedido ({max_rpm}/min). Aguarde {retry_after} segundos.",
                headers={"Retry-After": str(retry_after)},
            )

        logger.debug(f"Rate limit check passed for user {mask_user_id(user['id'])}: {max_rpm} req/min")

    if is_admin or is_master:
        role = "ADMIN" if is_admin else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(user['id'])} - bypassing quota check")
        quota_info = _get_master_quota_info(is_admin=is_admin)
    elif ENABLE_NEW_PRICING:
        logger.debug("New pricing enabled, checking quota and plan capabilities")
        try:
            # HOTFIX 2026-02-10: Use atomic check-and-increment to prevent race conditions
            # Issue #189: TOCTOU vulnerability fix
            from quota import check_quota, check_and_increment_quota_atomic

            quota_info = check_quota(user["id"])

            # Pre-check trial expiration and quota availability
            if not quota_info.allowed:
                # Quota exhausted or trial expired
                raise HTTPException(status_code=403, detail=quota_info.error_message)

            # ATOMIC: Check and increment quota BEFORE search execution
            # This prevents race condition where multiple concurrent requests
            # could exceed the quota limit
            allowed, new_quota_used, quota_remaining_after = check_and_increment_quota_atomic(
                user["id"],
                quota_info.capabilities["max_requests_per_month"]
            )

            if not allowed:
                # Quota was exhausted atomically (another request consumed last credit)
                raise HTTPException(
                    status_code=429,
                    detail=f"Limite de {quota_info.capabilities['max_requests_per_month']} buscas mensais atingido. Renova em {quota_info.quota_reset_date.strftime('%d/%m/%Y')}."
                )

            # Update quota_info with atomic values for response
            quota_info.quota_used = new_quota_used
            quota_info.quota_remaining = quota_remaining_after
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except RuntimeError as e:
            # Configuration error (missing env vars) - fail fast
            logger.error(f"Supabase configuration error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
            )
        except Exception as e:
            # Unexpected error - log but continue with safe fallback (user already authenticated)
            logger.warning(f"Quota check failed (continuing with fallback): {e}")
            # RESILIENCE: Use profile's plan_type instead of hardcoded free_trial
            fallback_plan = get_plan_from_profile(user["id"]) or "free_trial"
            fallback_caps = PLAN_CAPABILITIES.get(fallback_plan, PLAN_CAPABILITIES["free_trial"])
            fallback_name = PLAN_NAMES.get(fallback_plan, "FREE Trial") if fallback_plan != "free_trial" else "FREE Trial"
            if fallback_plan != "free_trial":
                logger.warning(
                    f"PLAN FALLBACK for user {mask_user_id(user['id'])}: "
                    f"subscription check failed, using profiles.plan_type='{fallback_plan}'"
                )
            quota_info = QuotaInfo(
                allowed=True,
                plan_id=fallback_plan,
                plan_name=fallback_name,
                capabilities=fallback_caps,
                quota_used=0,
                quota_remaining=999999,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=None,
                error_message=None,
            )
    else:
        # OLD BEHAVIOR: No quota/plan enforcement
        logger.debug("New pricing disabled, using legacy behavior (no quota limits)")
        quota_info = QuotaInfo(
            allowed=True,
            plan_id="legacy",
            plan_name="Legacy",
            capabilities=PLAN_CAPABILITIES["free_trial"],  # Use free_trial capabilities as base
            quota_used=0,
            quota_remaining=999999,
            quota_reset_date=datetime.now(timezone.utc),
            trial_expires_at=None,
            error_message=None,
        )

    # ==========================================================================
    # DATE RANGE: No restrictions - users can search any period
    # ==========================================================================
    # HOTFIX 2026-02-10: Removed date_range validation that was blocking paying users.
    # Essential validations (data_inicial <= data_final) are handled by Pydantic
    # in schemas.py BuscaRequest.validate_dates_and_values()
    #
    # Previously blocked users with 400 errors for searches > max_history_days.
    # Now unlimited date ranges allowed per user requirement.

    try:
        # Load sector configuration
        try:
            sector = get_sector(request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Using sector: {sector.name} ({len(sector.keywords)} keywords)")

        # Determine keywords: custom terms REPLACE sector keywords (mutually exclusive)
        # STORY-178 AC1: Use intelligent term parser with comma/phrase support
        from term_parser import parse_search_terms
        from relevance import calculate_min_matches

        custom_terms: list[str] = []
        stopwords_removed: list[str] = []  # kept for backward compat in response
        min_match_floor_value: int | None = None

        if request.termos_busca and request.termos_busca.strip():
            # STEP 1: Parse terms (comma-delimited phrases + stopword removal)
            parsed_terms = parse_search_terms(request.termos_busca)

            # STEP 2: CRITICAL - Validate terms with robust logic
            # This eliminates the bug where terms appear in BOTH "used" and "ignored"
            validated = validate_terms(parsed_terms)

            if not validated['valid']:
                # ALL terms rejected - return helpful error
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Nenhum termo válido para busca",
                        "termos_ignorados": validated['ignored'],
                        "motivos_ignorados": validated['reasons'],
                        "sugestao": "Use termos mais específicos (mínimo 4 caracteres, evite palavras comuns como 'de', 'da', etc.)"
                    }
                )

            # Use only VALIDATED terms for search
            custom_terms = validated['valid']
            stopwords_removed = validated['ignored']  # For response transparency

            logger.info(
                f"Term validation: {len(custom_terms)} valid, {len(stopwords_removed)} ignored. "
                f"Valid={custom_terms}, Ignored={list(validated['reasons'].keys())}"
            )

            # Calculate min_match_floor for custom terms (AC2.2)
            if custom_terms and not request.show_all_matches:
                min_match_floor_value = calculate_min_matches(len(custom_terms))
                logger.info(
                    f"Min match floor: {min_match_floor_value} "
                    f"(total_terms={len(custom_terms)})"
                )

        if custom_terms:
            active_keywords = set(custom_terms)
            logger.info(f"Using {len(custom_terms)} custom search terms: {custom_terms}")
        else:
            active_keywords = set(sector.keywords)
            logger.info(f"Using sector keywords ({len(active_keywords)} terms)")

        # SSE: Sector ready, starting fetch
        if tracker:
            await tracker.emit("connecting", 8, f"Setor '{sector.name}' configurado, conectando ao PNCP...")

        # Step 1: Fetch from procurement sources
        # FEATURE FLAG: Multi-source consolidation (STORY-177)
        enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
        source_stats_data = None  # Will be populated if multi-source is active

        # Use parallel fetching for multiple UFs to improve performance
        use_parallel = len(request.ufs) > 1

        # Get status value for PNCP API query
        status_value = request.status.value if request.status else None

        # Get modalidades to fetch (defaults to [6] if not specified)
        modalidades_to_fetch = request.modalidades if request.modalidades else None

        # SSE: Starting fetch
        if tracker:
            msg = f"Iniciando busca em {len(request.ufs)} estados..."
            if enable_multi_source:
                msg += " (multi-fonte ativo)"
            await tracker.emit("fetching", 10, msg)

        # Build per-UF progress callback for SSE
        uf_progress_callback = None
        if tracker:
            async def uf_progress_callback(uf: str, items_count: int):
                await tracker.emit_uf_complete(uf, items_count)

        # Global fetch timeout: 4 minutes max for the entire fetch phase
        FETCH_TIMEOUT = 4 * 60  # seconds

        if enable_multi_source:
            # === MULTI-SOURCE PATH (STORY-177) ===
            logger.info("Multi-source fetch enabled, using ConsolidationService")
            from consolidation import ConsolidationService
            from clients.compras_gov_client import ComprasGovAdapter
            from clients.portal_compras_client import PortalComprasAdapter
            from source_config.sources import get_source_config

            source_config = get_source_config()
            adapters = {}

            # Always include PNCP via legacy wrapper
            from clients.base import SourceAdapter, SourceMetadata, SourceStatus, SourceCapability, UnifiedProcurement
            class _PNCPLegacyAdapter(SourceAdapter):
                """Wraps existing PNCPClient as a SourceAdapter for consolidation."""
                _meta = SourceMetadata(
                    name="PNCP", code="PNCP",
                    base_url="https://pncp.gov.br/api/consulta/v1",
                    capabilities={SourceCapability.PAGINATION, SourceCapability.DATE_RANGE, SourceCapability.FILTER_BY_UF},
                    rate_limit_rps=10.0, priority=1,
                )
                @property
                def metadata(self): return self._meta
                async def health_check(self): return SourceStatus.AVAILABLE
                async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
                    _ufs = list(ufs) if ufs else request.ufs
                    if len(_ufs) > 1:
                        results = await buscar_todas_ufs_paralelo(
                            ufs=_ufs, data_inicial=data_inicial, data_final=data_final,
                            modalidades=modalidades_to_fetch, status=status_value,
                            max_concurrent=10, on_uf_complete=uf_progress_callback,
                        )
                    else:
                        client = PNCPClient()
                        results = list(client.fetch_all(
                            data_inicial=data_inicial, data_final=data_final,
                            ufs=_ufs, modalidades=modalidades_to_fetch,
                        ))
                    for item in results:
                        yield UnifiedProcurement(
                            source_id=item.get("codigoCompra", ""),
                            source_name="PNCP",
                            objeto=item.get("objetoCompra", ""),
                            valor_estimado=item.get("valorTotalEstimado", 0) or 0,
                            orgao=item.get("nomeOrgao", ""),
                            cnpj_orgao=item.get("cnpjOrgao", ""),
                            uf=item.get("uf", ""),
                            municipio=item.get("municipio", ""),
                            numero_edital=item.get("numeroEdital", ""),
                            modalidade=item.get("modalidadeNome", ""),
                            situacao=item.get("situacaoCompraNome", ""),
                            link_edital=item.get("linkSistemaOrigem", ""),
                            link_portal=item.get("linkProcessoEletronico", ""),
                            raw_data=item,
                        )
                def normalize(self, raw_record): pass

            if source_config.pncp.enabled:
                adapters["PNCP"] = _PNCPLegacyAdapter()

            if source_config.compras_gov.enabled:
                adapters["COMPRAS_GOV"] = ComprasGovAdapter(
                    timeout=source_config.compras_gov.timeout
                )

            if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
                adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                    api_key=source_config.portal.credentials.api_key,
                    timeout=source_config.portal.timeout,
                )

            consolidation_svc = ConsolidationService(
                adapters=adapters,
                timeout_per_source=source_config.consolidation.timeout_per_source,
                timeout_global=source_config.consolidation.timeout_global,
                fail_on_all_errors=source_config.consolidation.fail_on_all_errors,
            )

            # SSE callback for source completion
            source_complete_cb = None
            if tracker:
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
                    timeout=FETCH_TIMEOUT,
                )
                licitacoes_raw = consolidation_result.records
                source_stats_data = [
                    {
                        "source_code": sr.source_code,
                        "record_count": sr.record_count,
                        "duration_ms": sr.duration_ms,
                        "error": sr.error,
                        "status": sr.status,
                    }
                    for sr in consolidation_result.source_results
                ]
                logger.info(
                    f"Multi-source fetch: {consolidation_result.total_before_dedup} raw → "
                    f"{consolidation_result.total_after_dedup} deduped "
                    f"({consolidation_result.duplicates_removed} dupes removed)"
                )
            except asyncio.TimeoutError:
                logger.error(f"Multi-source fetch timed out after {FETCH_TIMEOUT}s")
                if tracker:
                    await tracker.emit_error("Busca expirou por tempo")
                    await remove_tracker(request.search_id)
                raise HTTPException(
                    status_code=504,
                    detail=(
                        f"A busca excedeu o tempo limite de {FETCH_TIMEOUT // 60} minutos. "
                        f"Tente com menos estados ou um período menor."
                    ),
                )
            finally:
                await consolidation_svc.close()
        else:
            # === PNCP-ONLY PATH (default, original behavior) ===
            logger.info(f"Fetching bids from PNCP API for {len(request.ufs)} UFs")

            async def _do_fetch() -> list:
                if use_parallel:
                    logger.info(f"Using parallel fetch for {len(request.ufs)} UFs (max_concurrent=10)")
                    try:
                        return await buscar_todas_ufs_paralelo(
                            ufs=request.ufs,
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            modalidades=modalidades_to_fetch,
                            status=status_value,
                            max_concurrent=10,
                            on_uf_complete=uf_progress_callback,
                        )
                    except Exception as e:
                        logger.warning(f"Parallel fetch failed, falling back to sequential: {e}")
                        client = PNCPClient()
                        return list(
                            client.fetch_all(
                                data_inicial=request.data_inicial,
                                data_final=request.data_final,
                                ufs=request.ufs,
                                modalidades=modalidades_to_fetch,
                            )
                        )
                else:
                    client = PNCPClient()
                    return list(
                        client.fetch_all(
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            ufs=request.ufs,
                            modalidades=modalidades_to_fetch,
                        )
                    )

            try:
                licitacoes_raw = await asyncio.wait_for(_do_fetch(), timeout=FETCH_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"PNCP fetch timed out after {FETCH_TIMEOUT}s for {len(request.ufs)} UFs")
                if tracker:
                    await tracker.emit_error("Busca expirou por tempo")
                    await remove_tracker(request.search_id)
                raise HTTPException(
                    status_code=504,
                    detail=(
                        f"A busca excedeu o tempo limite de {FETCH_TIMEOUT // 60} minutos. "
                        f"Tente com menos estados ou um período menor."
                    ),
                )

        fetch_elapsed = sync_time.time() - start_time
        logger.info(f"Fetched {len(licitacoes_raw)} raw bids in {fetch_elapsed:.2f}s")

        # SSE: Fetch complete
        if tracker:
            await tracker.emit("fetching", 55, f"Busca concluida: {len(licitacoes_raw)} licitacoes encontradas", total_raw=len(licitacoes_raw))

        # Step 2: Enrich with inferred status (before filtering)
        # IMPORTANTE: A API PNCP não retorna status padronizado, então inferimos
        # baseado em datas (abertura, encerramento) e valores (homologado)
        logger.info("Enriching bids with inferred status...")
        enriquecer_com_status_inferido(licitacoes_raw)
        logger.info(f"Status inference complete for {len(licitacoes_raw)} bids")

        # SSE: Starting filtering
        if tracker:
            await tracker.emit("filtering", 60, f"Aplicando filtros em {len(licitacoes_raw)} licitacoes...")

        # Step 3: Apply ALL filters (fail-fast sequential)
        # Filter order (optimized for performance):
        # 1. UF (O(1) - already filtered at API level for parallel, but verify)
        # 2. Status (if specified)
        # 3. Esfera (if specified)
        # 4. Modalidade (if specified - may be filtered at API level)
        # 5. Município (if specified)
        # 6. Valor (if specified)
        # 7. Keywords (regex - most expensive)

        # Extract filter parameters from request
        esferas_values = [e.value for e in request.esferas] if request.esferas else None
        status_filter = request.status.value if request.status else "todos"

        logger.info(
            f"Applying filters: status={status_filter}, modalidades={request.modalidades}, "
            f"valor=[{request.valor_minimo}, {request.valor_maximo}], esferas={esferas_values}, "
            f"municipios={len(request.municipios) if request.municipios else 0}"
        )

        # Use the comprehensive filter function that applies all filters in order
        # AC3.1: Re-enable sector exclusions when custom terms + sector selected
        # AC3.2: No exclusions when custom terms without sector (generic/default)
        # AC3.3: User-provided exclusion_terms override sector exclusions
        if request.exclusion_terms:
            active_exclusions = set(request.exclusion_terms)
            active_context_required = None
        elif custom_terms and request.setor_id and request.setor_id != "vestuario":
            # AC3.1: Sector selected with custom terms — re-enable sector safety nets
            active_exclusions = sector.exclusions
            active_context_required = sector.context_required_keywords
        elif not custom_terms:
            # Sector-only mode: full exclusions (existing behavior)
            active_exclusions = sector.exclusions
            active_context_required = sector.context_required_keywords
        else:
            # AC3.2: Custom terms without specific sector — no exclusions
            active_exclusions = set()
            active_context_required = None

        licitacoes_filtradas, stats = aplicar_todos_filtros(
            licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            status=status_filter,
            modalidades=request.modalidades,
            valor_min=request.valor_minimo,
            valor_max=request.valor_maximo,
            esferas=esferas_values,
            municipios=request.municipios,
            keywords=active_keywords,
            exclusions=active_exclusions,
            context_required=active_context_required,
            min_match_floor=min_match_floor_value,
        )

        # AC2.3: Degradation — if min_match_floor produced 0 results, relax to 1
        hidden_by_min_match = stats.get("rejeitadas_min_match", 0)
        filter_relaxed = False

        if (
            custom_terms
            and min_match_floor_value is not None
            and min_match_floor_value > 1
            and len(licitacoes_filtradas) == 0
            and hidden_by_min_match > 0
        ):
            logger.warning(
                f"Min match floor relaxed from {min_match_floor_value} to 1 — "
                f"zero results with strict filter"
            )
            filter_relaxed = True
            # Re-run filter without min_match_floor
            licitacoes_filtradas, stats = aplicar_todos_filtros(
                licitacoes_raw,
                ufs_selecionadas=set(request.ufs),
                status=status_filter,
                modalidades=request.modalidades,
                valor_min=request.valor_minimo,
                valor_max=request.valor_maximo,
                esferas=esferas_values,
                municipios=request.municipios,
                keywords=active_keywords,
                exclusions=active_exclusions,
                context_required=active_context_required,
                min_match_floor=None,  # Relaxed — no minimum
            )
            hidden_by_min_match = 0  # All results now shown

        # STORY-178: Compute relevance scores for each bid when custom terms active
        if custom_terms and licitacoes_filtradas:
            from relevance import score_relevance, count_phrase_matches
            for lic in licitacoes_filtradas:
                matched_terms = lic.get("_matched_terms", [])
                phrase_count = count_phrase_matches(matched_terms)
                lic["_relevance_score"] = score_relevance(
                    len(matched_terms), len(custom_terms), phrase_count
                )

        # Detailed logging for debugging and monitoring
        logger.info(
            f"Filtering complete: {len(licitacoes_filtradas)}/{len(licitacoes_raw)} bids passed"
        )
        # Use .get() with defaults for robustness (e.g., in tests with mocked stats)
        if stats:
            logger.info(f"  - Total processadas: {stats.get('total', len(licitacoes_raw))}")
            logger.info(f"  - Aprovadas: {stats.get('aprovadas', len(licitacoes_filtradas))}")
            logger.info(f"  - Rejeitadas (UF): {stats.get('rejeitadas_uf', 0)}")
            logger.info(f"  - Rejeitadas (Status): {stats.get('rejeitadas_status', 0)}")
            logger.info(f"  - Rejeitadas (Esfera): {stats.get('rejeitadas_esfera', 0)}")
            logger.info(f"  - Rejeitadas (Modalidade): {stats.get('rejeitadas_modalidade', 0)}")
            logger.info(f"  - Rejeitadas (Município): {stats.get('rejeitadas_municipio', 0)}")
            logger.info(f"  - Rejeitadas (Valor): {stats.get('rejeitadas_valor', 0)}")
            logger.info(f"  - Rejeitadas (Keyword): {stats.get('rejeitadas_keyword', 0)}")
            logger.info(f"  - Rejeitadas (Min Match): {stats.get('rejeitadas_min_match', 0)}")
            logger.info(f"  - Rejeitadas (Outros): {stats.get('rejeitadas_outros', 0)}")

        # Diagnostic: sample of keyword-rejected items for debugging
        if stats.get('rejeitadas_keyword', 0) > 0:
            keyword_rejected_sample = []
            for lic in licitacoes_raw[:200]:
                obj = lic.get("objetoCompra", "")
                matched, _ = match_keywords(obj, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
                if not matched:
                    keyword_rejected_sample.append(obj[:120])
                    if len(keyword_rejected_sample) >= 3:
                        break
            if keyword_rejected_sample:
                logger.debug(f"  - Sample keyword-rejected objects: {keyword_rejected_sample}")

        # SSE: Filtering complete
        if tracker:
            await tracker.emit("filtering", 70, f"Filtragem concluida: {len(licitacoes_filtradas)} resultados", total_filtered=len(licitacoes_filtradas))

        # Build filter stats for frontend
        fs = FilterStats(
            rejeitadas_uf=stats.get("rejeitadas_uf", 0),
            rejeitadas_valor=stats.get("rejeitadas_valor", 0),
            rejeitadas_keyword=stats.get("rejeitadas_keyword", 0),
            rejeitadas_min_match=stats.get("rejeitadas_min_match", 0),
            rejeitadas_prazo=stats.get("rejeitadas_prazo", 0),
            rejeitadas_outros=stats.get("rejeitadas_outros", 0),
        )

        # Early return if no results passed filters — skip LLM and Excel
        if not licitacoes_filtradas:
            logger.info("No bids passed filters — skipping LLM and Excel generation")
            if tracker:
                await tracker.emit_complete()
                await remove_tracker(request.search_id)
            resumo = ResumoLicitacoes(
                resumo_executivo=(
                    f"Nenhuma licitação de {sector.name.lower()} encontrada "
                    f"nos estados selecionados para o período informado."
                ),
                total_oportunidades=0,
                valor_total=0.0,
                destaques=[],
                alerta_urgencia=None,
            )

            # Quota already incremented atomically at request start (check_and_increment_quota_atomic)
            # Use values from quota_info which were updated after atomic increment
            new_quota_used = quota_info.quota_used if quota_info else 0
            quota_remaining = quota_info.quota_remaining if quota_info else 0

            response = BuscaResponse(
                resumo=resumo,
                licitacoes=[],  # Empty list for zero results
                excel_base64=None if not quota_info or not quota_info.capabilities["allow_excel"] else "",
                excel_available=quota_info.capabilities["allow_excel"] if quota_info else False,
                quota_used=new_quota_used,
                quota_remaining=quota_remaining,
                total_raw=len(licitacoes_raw),
                total_filtrado=0,
                filter_stats=fs,
                termos_utilizados=custom_terms if custom_terms else None,
                stopwords_removidas=stopwords_removed if stopwords_removed else None,
                upgrade_message="Exportar Excel disponível no plano Máquina (R$ 597/mês)." if quota_info and not quota_info.capabilities["allow_excel"] else None,
                source_stats=source_stats_data,
                hidden_by_min_match=hidden_by_min_match if custom_terms else None,
                filter_relaxed=filter_relaxed if custom_terms else None,
            )
            logger.info(
                "Search completed with 0 results",
                extra={"total_raw": len(licitacoes_raw), "total_filtrado": 0},
            )

            # Save session even for zero results (for history tracking)
            if user:
                try:
                    from quota import save_search_session
                    session_id = save_search_session(
                        user_id=user["id"],
                        sectors=[request.setor_id],
                        ufs=request.ufs,
                        data_inicial=request.data_inicial,
                        data_final=request.data_final,
                        custom_keywords=custom_terms if custom_terms else None,
                        total_raw=len(licitacoes_raw),
                        total_filtered=0,
                        valor_total=0.0,
                        resumo_executivo=resumo.resumo_executivo,
                        destaques=[],
                    )
                    logger.info(f"Search session saved (0 results): {session_id[:8]}*** for user {mask_user_id(user['id'])}")
                except Exception as e:
                    logger.error(
                        f"Failed to save search session for user {mask_user_id(user['id'])}: {type(e).__name__}: {e}",
                        exc_info=True,
                    )

            return response

        # Step 2.5: Apply sorting/ordering
        # Sort results before LLM summary and Excel generation so order is consistent
        logger.info(f"Applying sorting: ordenacao='{request.ordenacao}'")
        licitacoes_filtradas = ordenar_licitacoes(
            licitacoes_filtradas,
            ordenacao=request.ordenacao,
            termos_busca=custom_terms if custom_terms else list(active_keywords)[:10],  # Use first 10 keywords for relevance
        )

        filter_elapsed = sync_time.time() - start_time
        logger.info(
            f"Filtering and sorting complete in {filter_elapsed:.2f}s: "
            f"{len(licitacoes_filtradas)} results ordered by '{request.ordenacao}'"
        )

        # SSE: Starting LLM
        if tracker:
            await tracker.emit("llm", 75, "Gerando resumo executivo com IA...")

        # Step 3: Generate executive summary via LLM (with automatic fallback)
        logger.info("Generating executive summary")
        try:
            resumo = gerar_resumo(licitacoes_filtradas, sector_name=sector.name)
            logger.info("LLM summary generated successfully")
        except Exception as e:
            logger.warning(
                f"LLM generation failed, using fallback mechanism: {e}",
                exc_info=True,
            )
            resumo = gerar_resumo_fallback(licitacoes_filtradas, sector_name=sector.name)
            logger.info("Fallback summary generated successfully")

        # CRITICAL: Override LLM-generated counts with actual computed values.
        # The LLM may hallucinate total_oportunidades (often returning 0),
        # which causes the frontend to show "no results found".
        actual_total = len(licitacoes_filtradas)
        actual_valor = sum(
            lic.get("valorTotalEstimado", 0) or 0 for lic in licitacoes_filtradas
        )
        if resumo.total_oportunidades != actual_total:
            logger.warning(
                f"LLM returned total_oportunidades={resumo.total_oportunidades}, "
                f"overriding with actual count={actual_total}"
            )
        resumo.total_oportunidades = actual_total
        resumo.valor_total = actual_valor

        # SSE: LLM done, starting Excel
        if tracker:
            await tracker.emit("excel", 92, "Gerando planilha Excel...")

        # Step 4: Generate Excel report (conditional based on plan)
        excel_base64 = None
        download_url = None
        excel_available = quota_info.capabilities["allow_excel"] if quota_info else False
        upgrade_message = None

        if excel_available:
            logger.info("Generating Excel report")
            excel_buffer = create_excel(licitacoes_filtradas)
            excel_bytes = excel_buffer.read()

            # Try to upload to object storage (Supabase Storage)
            storage_result = upload_excel(excel_bytes, request.search_id)

            if storage_result:
                # Storage upload succeeded - use signed URL
                download_url = storage_result["signed_url"]
                logger.info(
                    f"Excel uploaded to storage: {storage_result['file_path']} "
                    f"(signed URL valid for {storage_result['expires_in']}s)"
                )
                # Don't send base64 if we have a download URL (saves bandwidth)
                excel_base64 = None
            else:
                # Storage upload failed - fallback to base64
                logger.warning("Storage upload failed, falling back to base64 encoding")
                excel_base64 = base64.b64encode(excel_bytes).decode("utf-8")
                logger.info(f"Excel report encoded as base64 ({len(excel_base64)} chars)")
        else:
            logger.info("Excel generation skipped (not allowed for user's plan)")
            upgrade_message = "Exportar Excel disponível no plano Máquina (R$ 597/mês)."

        # Quota already incremented atomically at request start (check_and_increment_quota_atomic)
        # Use values from quota_info which were updated after atomic increment
        new_quota_used = quota_info.quota_used if quota_info else 0
        quota_remaining = quota_info.quota_remaining if quota_info else 0

        # Step 5: Return response with individual bid items for preview
        licitacao_items = _convert_to_licitacao_items(licitacoes_filtradas)

        response = BuscaResponse(
            resumo=resumo,
            licitacoes=licitacao_items,  # Individual bids for frontend display
            excel_base64=excel_base64,
            download_url=download_url,
            excel_available=excel_available,
            quota_used=new_quota_used,
            quota_remaining=quota_remaining,
            total_raw=len(licitacoes_raw),
            total_filtrado=len(licitacoes_filtradas),
            filter_stats=fs,
            termos_utilizados=custom_terms if custom_terms else None,
            stopwords_removidas=stopwords_removed if stopwords_removed else None,
            upgrade_message=upgrade_message,
            source_stats=source_stats_data,
            hidden_by_min_match=hidden_by_min_match if custom_terms else None,
            filter_relaxed=filter_relaxed if custom_terms else None,
            ultima_atualizacao=datetime.now().isoformat() + "Z",
        )

        logger.info(
            "Search completed successfully",
            extra={
                "total_raw": response.total_raw,
                "total_filtrado": response.total_filtrado,
                "valor_total": resumo.valor_total,
            },
        )

        # Save session to history (for /historico page)
        # This must happen BEFORE returning the response
        if user:
            try:
                from quota import save_search_session
                session_id = save_search_session(
                    user_id=user["id"],
                    sectors=[request.setor_id],
                    ufs=request.ufs,
                    data_inicial=request.data_inicial,
                    data_final=request.data_final,
                    custom_keywords=custom_terms if custom_terms else None,
                    total_raw=len(licitacoes_raw),
                    total_filtered=len(licitacoes_filtradas),
                    valor_total=resumo.valor_total,
                    resumo_executivo=resumo.resumo_executivo,
                    destaques=resumo.destaques,
                )
                logger.info(f"Search session saved: {session_id[:8]}*** for user {mask_user_id(user['id'])}")
            except Exception as e:
                # Log detailed error but don't fail the search request
                logger.error(
                    f"Failed to save search session for user {mask_user_id(user['id'])}: {type(e).__name__}: {e}",
                    exc_info=True,
                )

        # SSE: Search complete
        if tracker:
            await tracker.emit_complete()
            await remove_tracker(request.search_id)

        return response

    except PNCPRateLimitError as e:
        if tracker:
            await tracker.emit_error(f"PNCP rate limit: {e}")
            await remove_tracker(request.search_id)
        logger.error(f"PNCP rate limit exceeded: {e}", exc_info=True)
        # Extract Retry-After header if available
        retry_after = getattr(e, "retry_after", 60)  # Default 60s if not provided
        raise HTTPException(
            status_code=503,
            detail=(
                f"O PNCP está limitando requisições. "
                f"Aguarde {retry_after} segundos e tente novamente."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    except PNCPAPIError as e:
        if tracker:
            await tracker.emit_error(f"PNCP API error: {e}")
            await remove_tracker(request.search_id)
        logger.error(f"PNCP API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=(
                "O Portal Nacional de Contratações (PNCP) está temporariamente "
                "indisponível ou retornou um erro. Tente novamente em alguns "
                "instantes ou reduza o número de estados selecionados."
            ),
        )

    except Exception:
        if tracker:
            await tracker.emit_error("Erro interno do servidor")
            await remove_tracker(request.search_id)
        logger.exception("Internal server error during procurement search")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor. Tente novamente em alguns instantes.",
        )
