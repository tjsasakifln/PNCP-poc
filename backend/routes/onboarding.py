"""
Onboarding Router - First automatic analysis after onboarding completion.

GTM-004: Executes first search based on user profile to deliver
immediate value (time-to-first-value < 5 minutes).
"""

import asyncio
import logging
import time as sync_time
import uuid
from datetime import date, timedelta
from types import SimpleNamespace

from fastapi import APIRouter, HTTPException, Depends

from schemas import BuscaRequest, BuscaResponse, FirstAnalysisRequest, FirstAnalysisResponse
from auth import require_auth
from config import ENABLE_NEW_PRICING
from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
from exceptions import PNCPAPIError, PNCPRateLimitError
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
from progress import create_tracker, remove_tracker
from log_sanitizer import mask_user_id, get_sanitized_logger
from search_pipeline import SearchPipeline
from search_context import SearchContext
from utils.cnae_mapping import map_cnae_to_setor, get_setor_name

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["onboarding"])


@router.post("/first-analysis", response_model=FirstAnalysisResponse)
async def first_analysis(
    request: FirstAnalysisRequest,
    user: dict = Depends(require_auth),
):
    """
    Execute first automatic analysis based on onboarding profile.

    GTM-004 AC1-4: Maps CNAE to sector, builds BuscaRequest automatically,
    executes search in background, and returns search_id for SSE tracking.
    """
    user_id = user.get("id", "unknown")
    search_id = str(uuid.uuid4())

    # AC1: Map CNAE to sector
    setor_id = map_cnae_to_setor(request.cnae)
    setor_name = get_setor_name(setor_id)

    logger.info(
        f"First analysis for {mask_user_id(user_id)}: "
        f"CNAE={request.cnae} → setor={setor_id}, "
        f"UFs={request.ufs}"
    )

    # AC2: Build BuscaRequest from profile
    today = date.today()
    data_final = today.isoformat()
    data_inicial = (today - timedelta(days=30)).isoformat()

    busca_request = BuscaRequest(
        ufs=request.ufs,
        data_inicial=data_inicial,
        data_final=data_final,
        setor_id=setor_id,
        modo_busca="publicacao",
        search_id=search_id,
        valor_minimo=float(request.faixa_valor_min) if request.faixa_valor_min else None,
        valor_maximo=float(request.faixa_valor_max) if request.faixa_valor_max else None,
    )

    # AC3: Create SSE tracker and launch search in background
    tracker = await create_tracker(search_id, len(request.ufs))
    await tracker.emit("connecting", 3, "Iniciando primeira análise...")

    # Launch search pipeline in background task
    asyncio.create_task(
        _run_first_analysis_pipeline(busca_request, user, tracker, search_id)
    )

    # Build user-friendly message
    uf_list = ", ".join(request.ufs[:5])
    if len(request.ufs) > 5:
        uf_list += f" e mais {len(request.ufs) - 5}"

    return FirstAnalysisResponse(
        search_id=search_id,
        status="in_progress",
        message=f"Analisando oportunidades de {setor_name} em {uf_list}...",
        setor_id=setor_id,
    )


async def _run_first_analysis_pipeline(
    request: BuscaRequest,
    user: dict,
    tracker,
    search_id: str,
):
    """Run the search pipeline as a background task for first analysis."""
    deps = SimpleNamespace(
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

    pipeline = SearchPipeline(deps)
    ctx = SearchContext(
        request=request,
        user=user,
        tracker=tracker,
        start_time=sync_time.time(),
    )

    try:
        await pipeline.run(ctx)
        await tracker.emit_complete()
    except (PNCPRateLimitError, PNCPAPIError) as e:
        logger.error(f"First analysis pipeline error: {e}")
        await tracker.emit_error(f"Fontes de dados temporariamente indisponíveis: {e}")
    except Exception:
        logger.exception("First analysis pipeline unexpected error")
        await tracker.emit_error("Erro interno. Tente novamente em alguns instantes.")
    finally:
        await remove_tracker(search_id)
