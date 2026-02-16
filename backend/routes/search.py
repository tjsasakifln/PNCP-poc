"""
Search Router - Main procurement search endpoint and SSE progress tracking.

This router handles the core search functionality:
- POST /buscar: Main search orchestration via SearchPipeline (7-stage pipeline)
- GET /buscar-progress/{search_id}: SSE stream for real-time progress updates

STORY-216: buscar_licitacoes() decomposed into SearchPipeline (search_pipeline.py).
This module is now a thin wrapper that delegates to the pipeline.
"""

import asyncio
import logging
import time as sync_time

from types import SimpleNamespace

from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import StreamingResponse

# === Module-level imports preserved for test mock compatibility (AC11) ===
# Tests use @patch("routes.search.X") to mock these names.
# The thin wrapper passes them to SearchPipeline as deps.
from config import ENABLE_NEW_PRICING
from schemas import BuscaRequest, BuscaResponse
from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import (
    aplicar_todos_filtros,
    filtrar_por_prazo_aberto,
    match_keywords,
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    validate_terms,
)
from excel import create_excel
from auth import require_auth
from authorization import check_user_roles
from rate_limiter import rate_limiter
from progress import create_tracker, get_tracker, remove_tracker, subscribe_to_events
from log_sanitizer import mask_user_id, get_sanitized_logger
from search_pipeline import SearchPipeline
from search_context import SearchContext

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["search"])


# Helper functions moved to search_pipeline.py (STORY-216 AC6)
# Re-exported for any external callers (backward compat)
from search_pipeline import _build_pncp_link, _calcular_urgencia, _calcular_dias_restantes, _convert_to_licitacao_items


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
    Main search endpoint — thin wrapper that delegates to SearchPipeline.

    STORY-216 AC5: buscar_licitacoes() is a thin wrapper that creates
    SearchPipeline and runs stages. All business logic lives in search_pipeline.py.

    The wrapper handles:
    - SSE tracker lifecycle (create, cleanup on error)
    - Exception mapping (PNCPRateLimitError → 503, PNCPAPIError → 502, etc.)
    - Dependency injection (passing module-level names for test mock compatibility)
    """
    # SSE Progress Tracking
    tracker = None
    if request.search_id:
        tracker = await create_tracker(request.search_id, len(request.ufs))
        await tracker.emit("connecting", 3, "Iniciando busca...")

    # Build deps namespace from module-level imports (preserves test mock paths)
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
        response = await pipeline.run(ctx)

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
        retry_after = getattr(e, "retry_after", 60)
        raise HTTPException(
            status_code=503,
            detail=(
                f"As fontes de dados estão temporariamente limitando consultas. "
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
                "Nossas fontes de dados estão temporariamente indisponíveis. "
                "Tente novamente em alguns instantes ou reduza o número "
                "de estados selecionados."
            ),
        )

    except HTTPException:
        if tracker:
            await tracker.emit_error("Erro no processamento")
            await remove_tracker(request.search_id)
        raise

    except Exception:
        if tracker:
            await tracker.emit_error("Erro interno do servidor")
            await remove_tracker(request.search_id)
        logger.exception("Internal server error during procurement search")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor. Tente novamente em alguns instantes.",
        )
