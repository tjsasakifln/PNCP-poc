"""
DEBT-115 AC7: Search status, results, retry, and cancel endpoints.

Extracted from routes/search.py to reduce module complexity.
Contains GET /search/{id}/status, GET /buscar-results/{id}, GET /search/{id}/results,
GET /search/{id}/zero-match, POST /search/{id}/regenerate-excel,
GET /search/{id}/timeline, POST /search/{id}/retry, POST /search/{id}/cancel.
"""

import asyncio
import time as sync_time

from fastapi import APIRouter, HTTPException, Depends
from starlette.responses import JSONResponse as StarletteJSONResponse

from auth import require_auth
from excel import create_excel
from log_sanitizer import get_sanitized_logger
from progress import get_tracker, remove_tracker
from rate_limiter import require_rate_limit
from schemas import BuscaResponse, SearchStatusResponse
from search_state_manager import (
    get_search_status,
    get_state_machine,
    get_timeline,
    remove_state_machine,
)

from routes.search_state import (
    get_background_results,
    get_background_results_async,
)

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["search"])


# ---------------------------------------------------------------------------
# CRIT-003 AC11: Search status polling endpoint
# ---------------------------------------------------------------------------

@router.get("/search/{search_id}/status", response_model=SearchStatusResponse)
async def search_status_endpoint(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """GTM-STAB-009 AC3: Enriched status response for polling.

    LIGHTWEIGHT (<50ms): Reads from in-memory progress tracker + state machine.
    Falls back to DB-based get_search_status only if in-memory state is unavailable.

    Called by frontend when SSE disconnects (AC12) or for async polling.
    """
    # --- Fast path: in-memory state (no DB hit) ---
    tracker = await get_tracker(search_id)
    state_machine = get_state_machine(search_id)

    if tracker or state_machine:
        # Determine status from state machine
        if state_machine and state_machine.current_state:
            state_val = state_machine.current_state.value
            # Map state machine states to simplified status strings
            status_map = {
                "created": "running",
                "validating": "running",
                "fetching": "running",
                "filtering": "running",
                "enriching": "running",
                "generating": "running",
                "persisting": "running",
                "completed": "completed",
                "failed": "failed",
                "rate_limited": "failed",
                "timed_out": "timeout",
            }
            status = status_map.get(state_val, "running")
        else:
            status = "running"

        # Progress from tracker
        progress_pct = 0
        ufs_completed: list[str] = []
        ufs_pending: list[str] = []
        if tracker:
            # Estimate progress from tracker's internal counters
            if tracker._is_complete:
                progress_pct = 100
            elif tracker.uf_count > 0:
                progress_pct = min(95, 10 + int((tracker._ufs_completed / tracker.uf_count) * 85))
            else:
                progress_pct = 0

        # Elapsed time
        elapsed_s = 0.0
        created_at_str = None
        if tracker:
            elapsed_s = round(sync_time.time() - tracker.created_at, 1)
            from datetime import datetime, timezone
            created_at_str = datetime.fromtimestamp(tracker.created_at, tz=timezone.utc).isoformat()

        # Results count (from background results store if completed)
        results_count = 0
        results_url = None
        if status == "completed":
            bg_result = get_background_results(search_id)
            if bg_result:
                results_count = getattr(bg_result, "total_filtrado", 0)
            results_url = f"/v1/search/{search_id}/results"

        # STORY-364 AC1: Include Excel status from job result
        excel_url = None
        excel_status_val = None
        from job_queue import get_job_result
        excel_result = await get_job_result(search_id, "excel_result")
        if excel_result:
            excel_url = excel_result.get("download_url")
            excel_status_val = excel_result.get("excel_status")

        return SearchStatusResponse(
            search_id=search_id,
            status=status,
            progress_pct=progress_pct,
            ufs_completed=ufs_completed,
            ufs_pending=ufs_pending,
            results_count=results_count,
            results_url=results_url,
            elapsed_s=elapsed_s,
            created_at=created_at_str,
            excel_url=excel_url,
            excel_status=excel_status_val,
        )

    # --- Slow path: fall back to DB-based status (backward compat) ---
    db_status = await get_search_status(search_id)
    if db_status is None:
        raise HTTPException(status_code=404, detail="Search not found")

    # Map DB status to enriched response
    raw_status = db_status.get("status", "running")
    status_map_db = {
        "created": "running",
        "processing": "running",
        "completed": "completed",
        "failed": "failed",
        "timed_out": "timeout",
    }
    mapped_status = status_map_db.get(raw_status, "running")

    elapsed_ms = db_status.get("elapsed_ms")
    elapsed_s = round(elapsed_ms / 1000.0, 1) if elapsed_ms else 0.0

    results_url = None
    results_count = 0
    if mapped_status == "completed":
        results_url = f"/v1/search/{search_id}/results"

    # STORY-364 AC1: Include Excel status from job result (slow path)
    excel_url_db = None
    excel_status_db = None
    from job_queue import get_job_result as _get_job_result
    excel_result_db = await _get_job_result(search_id, "excel_result")
    if excel_result_db:
        excel_url_db = excel_result_db.get("download_url")
        excel_status_db = excel_result_db.get("excel_status")

    return SearchStatusResponse(
        search_id=search_id,
        status=mapped_status,
        progress_pct=db_status.get("progress", 0),
        ufs_completed=[],
        ufs_pending=[],
        results_count=results_count,
        results_url=results_url,
        elapsed_s=elapsed_s,
        created_at=db_status.get("started_at"),
        excel_url=excel_url_db,
        excel_status=excel_status_db,
    )


# ---------------------------------------------------------------------------
# CRIT-003 AC7: Search timeline endpoint
# ---------------------------------------------------------------------------

@router.get("/search/{search_id}/timeline")
async def search_timeline_endpoint(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """AC7: Return all state transitions for audit trail."""
    timeline = await get_timeline(search_id)
    return {"search_id": search_id, "transitions": timeline}


# ---------------------------------------------------------------------------
# A-04 AC5: Background fetch results endpoint
# ---------------------------------------------------------------------------

@router.get("/buscar-results/{search_id}")
async def get_search_results(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """Return results of a background fetch or async search.

    A-04 AC5: Called by frontend when user clicks "Atualizar resultados" banner.
    GTM-ARCH-001 AC3: Also serves results from ARQ Worker (via Redis).
    Returns 404 if search_id not found or expired.
    """
    result = await get_background_results_async(search_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Resultados não encontrados ou expirados. Execute uma nova análise.",
        )
    return result


# ---------------------------------------------------------------------------
# GTM-STAB-009 AC4: Canonical results endpoint for async search
# ---------------------------------------------------------------------------

@router.get("/search/{search_id}/results")
async def get_search_results_v1(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """GTM-STAB-009 AC4: Return results of async search.

    - 200 with BuscaResponse when results are ready
    - 202 with status when still processing
    - 404 when search_id not found or expired
    """
    result = await get_background_results_async(search_id)
    if result is not None:
        # STORY-364 AC2: Merge Excel job result if not already in response
        if isinstance(result, dict) and not result.get("download_url"):
            from job_queue import get_job_result as _gjr
            _excel = await _gjr(search_id, "excel_result")
            if _excel and _excel.get("download_url"):
                result["download_url"] = _excel["download_url"]
                result["excel_status"] = _excel.get("excel_status", "ready")

        return StarletteJSONResponse(
            content=result if isinstance(result, dict) else result,
            headers={"Cache-Control": "max-age=300"},
        )

    # Not ready yet — check if search is still processing
    status = await get_search_status(search_id)
    if status is not None:
        return StarletteJSONResponse(
            status_code=202,
            content={
                "search_id": search_id,
                "status": status.get("status", "processing"),
                "progress": status.get("progress", 0),
                "message": "Busca em andamento. Tente novamente em alguns segundos.",
            },
            headers={"Cache-Control": "no-cache"},
        )

    raise HTTPException(
        status_code=404,
        detail="Resultados não encontrados ou expirados. Execute uma nova análise.",
    )


# ---------------------------------------------------------------------------
# CRIT-059 AC4: Fetch zero-match classification results
# ---------------------------------------------------------------------------

@router.get("/search/{search_id}/zero-match")
async def get_zero_match_results_endpoint(
    search_id: str,
    user: dict = Depends(require_auth),
    _rl=Depends(require_rate_limit(10, 60)),  # 10 req/min per user
):
    """Return items approved by background zero-match LLM classification.

    - 200: Results ready (may be empty list if none approved)
    - 404: Job not yet completed or results expired
    """
    from job_queue import get_zero_match_results

    results = await get_zero_match_results(search_id)
    if results is None:
        raise HTTPException(
            status_code=404,
            detail="Resultados de classificação ainda não disponíveis.",
        )

    return {"search_id": search_id, "results": results, "count": len(results)}


# ---------------------------------------------------------------------------
# STORY-364 AC7-AC8: Regenerate Excel from stored results
# ---------------------------------------------------------------------------

@router.post("/search/{search_id}/regenerate-excel")
async def regenerate_excel_endpoint(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """STORY-364 AC7-AC8: Regenerate Excel from stored results without re-running search.

    - 202: Excel generation job enqueued
    - 404: Results not found or expired
    """
    result = await get_background_results_async(search_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Resultados não encontrados ou expirados. Execute uma nova análise.",
        )

    # Extract licitacoes from stored result
    if isinstance(result, dict):
        licitacoes = result.get("licitacoes", [])
    elif hasattr(result, "licitacoes"):
        licitacoes = result.licitacoes
    else:
        licitacoes = []

    if not licitacoes:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma licitação nos resultados armazenados.",
        )

    from job_queue import enqueue_job, is_queue_available

    if await is_queue_available():
        await enqueue_job(
            "excel_generation_job",
            search_id=search_id,
            licitacoes=licitacoes,
            allow_excel=True,
        )
        return StarletteJSONResponse(
            status_code=202,
            content={
                "message": "Gerando Excel...",
                "search_id": search_id,
                "excel_status": "processing",
            },
        )

    # Inline fallback when ARQ unavailable
    try:
        excel_buffer = create_excel(licitacoes)
        excel_bytes = excel_buffer.read()
        from storage import upload_excel
        storage_result = upload_excel(excel_bytes, search_id)
        if storage_result:
            download_url = storage_result["signed_url"]
            from job_queue import persist_job_result
            await persist_job_result(
                search_id, "excel_result",
                {"excel_status": "ready", "download_url": download_url},
            )
            return {
                "excel_status": "ready",
                "download_url": download_url,
                "search_id": search_id,
            }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f"[Regenerate Excel] Inline generation failed: {e}", exc_info=True,
        )

    raise HTTPException(
        status_code=500,
        detail="Erro ao gerar Excel. Tente novamente.",
    )


# ---------------------------------------------------------------------------
# CRIT-006 AC4-5: Retry search with only missing/failed UFs
# ---------------------------------------------------------------------------

@router.post("/search/{search_id}/retry")
async def retry_search(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """CRIT-006 AC4-5: Retry search with only missing/failed UFs."""
    from database import get_db as _get_db
    from supabase_client import sb_execute

    db = _get_db()
    try:
        session_result = await sb_execute(
            db.table("search_sessions")
            .select("failed_ufs, ufs, status")
            .eq("id", search_id)
            .eq("user_id", user["id"])
            .single()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Search session not found")

    session_data = session_result.data if session_result and session_result.data else None
    if not session_data:
        raise HTTPException(status_code=404, detail="Search session not found")

    failed_ufs = session_data.get("failed_ufs") or []
    all_ufs = session_data.get("ufs") or []
    succeeded_ufs = [uf for uf in all_ufs if uf not in failed_ufs]

    return {
        "search_id": search_id,
        "retry_ufs": failed_ufs,
        "preserved_ufs": succeeded_ufs,
        "status": "retry_available" if failed_ufs else "no_retry_needed",
    }


# ---------------------------------------------------------------------------
# CRIT-006 AC16-17: Cancel an in-progress search
# ---------------------------------------------------------------------------

@router.post("/search/{search_id}/cancel")
async def cancel_search(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """CRIT-006 AC16-17: Cancel an in-progress search."""
    # Try to update state machine
    try:
        machine = get_state_machine(search_id)
        if machine and not machine.is_terminal:
            await machine.fail("Cancelled by user", error_code="cancelled")
            remove_state_machine(search_id)
    except Exception as e:
        logger.warning(f"Failed to update state machine on cancel: {e}")

    # Remove tracker to stop SSE
    tracker = await get_tracker(search_id)
    if tracker:
        await tracker.emit_error("Busca cancelada pelo usuario")
        await remove_tracker(search_id)

    # Update session in DB
    try:
        from datetime import datetime, timezone
        from quota import update_search_session_status
        await update_search_session_status(
            search_id,
            status="cancelled",
            error_code="cancelled",
            error_message="Cancelled by user",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.warning(f"Failed to update session on cancel: {e}")

    return {"status": "cancelled", "search_id": search_id}
