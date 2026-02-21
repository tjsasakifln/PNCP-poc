"""
Search Router - Main procurement search endpoint and SSE progress tracking.

This router handles the core search functionality:
- POST /buscar: Main search orchestration via SearchPipeline (7-stage pipeline)
- GET /buscar-progress/{search_id}: SSE stream for real-time progress updates
- GET /buscar-results/{search_id}: Fetch results of an in-progress/completed background search (A-04 AC5)

STORY-216: buscar_licitacoes() decomposed into SearchPipeline (search_pipeline.py).
This module is now a thin wrapper that delegates to the pipeline.

GTM-RESILIENCE-A04: Cache-first progressive delivery.
When cache exists, returns immediately and spawns background live fetch.
"""

import asyncio
import time as sync_time

from types import SimpleNamespace
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from starlette.responses import StreamingResponse

# === Module-level imports preserved for test mock compatibility (AC11) ===
# Tests use @patch("routes.search.X") to mock these names.
# The thin wrapper passes them to SearchPipeline as deps.
from config import ENABLE_NEW_PRICING
from schemas import BuscaRequest, BuscaResponse, SearchErrorCode
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
from auth import require_auth
from authorization import check_user_roles
from rate_limiter import rate_limiter
from progress import create_tracker, get_tracker, remove_tracker, subscribe_to_events
from log_sanitizer import get_sanitized_logger
from search_pipeline import SearchPipeline
from search_context import SearchContext
from search_state_manager import (
    create_state_machine,
    get_state_machine,
    remove_state_machine,
    get_search_status,
    get_timeline,
    get_current_state,
)
from models.search_state import SearchState

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["search"])


def _build_error_detail(
    message: str,
    error_code: SearchErrorCode,
    search_id: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    """CRIT-009 AC1: Build structured error response body for /buscar errors.

    Returns a dict suitable for HTTPException detail parameter.
    Never exposes stack traces or internal information.
    """
    from datetime import datetime, timezone
    return {
        "detail": message,
        "error_code": error_code.value,
        "search_id": search_id,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _update_session_on_error(
    session_id: str,
    start_time: float,
    status: str,
    error_code: str,
    error_message: str,
    pipeline_stage: str | None = None,
    response_state: str | None = None,
) -> None:
    """CRIT-002 AC12: Fire-and-forget session status update on error.

    Called via asyncio.create_task() from exception handlers.
    Never raises — logs errors silently.
    """
    try:
        from datetime import datetime, timezone
        from quota import update_search_session_status
        elapsed_ms = int((sync_time.time() - start_time) * 1000)
        await update_search_session_status(
            session_id,
            status=status,
            error_code=error_code,
            error_message=error_message,
            pipeline_stage=pipeline_stage,
            response_state=response_state,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error(f"CRIT-002: Failed to update session on error: {e}")


# Helper functions moved to search_pipeline.py (STORY-216 AC6)
# Re-exported for any external callers (backward compat)
from search_pipeline import _build_pncp_link, _calcular_urgencia, _calcular_dias_restantes, _convert_to_licitacao_items  # noqa: F401, E402


# ---------------------------------------------------------------------------
# A-04: In-memory store for background fetch results
# ---------------------------------------------------------------------------
_background_results: Dict[str, Dict[str, Any]] = {}
_RESULTS_TTL = 600  # 10 minutes
_active_background_tasks: Dict[str, asyncio.Task] = {}
_MAX_BACKGROUND_TASKS = 5  # Budget: max concurrent background fetches


def _cleanup_stale_results() -> None:
    """Remove background results older than TTL."""
    now = sync_time.time()
    stale = [sid for sid, entry in _background_results.items()
             if now - entry.get("stored_at", 0) > _RESULTS_TTL]
    for sid in stale:
        _background_results.pop(sid, None)
    # Also clean up completed tasks
    done = [sid for sid, task in _active_background_tasks.items() if task.done()]
    for sid in done:
        _active_background_tasks.pop(sid, None)


def store_background_results(search_id: str, response: BuscaResponse) -> None:
    """Store results from a completed background fetch."""
    _background_results[search_id] = {
        "response": response,
        "stored_at": sync_time.time(),
    }


def get_background_results(search_id: str) -> Optional[BuscaResponse]:
    """Retrieve background fetch results if available and not expired."""
    entry = _background_results.get(search_id)
    if entry and sync_time.time() - entry["stored_at"] < _RESULTS_TTL:
        return entry["response"]
    return None


# ---------------------------------------------------------------------------
# SSE Progress Stream
# ---------------------------------------------------------------------------

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
        - partial_results: Non-terminal — intermediate results during background fetch (A-04)
        - refresh_available (100%): Background fetch complete, new data available (A-04)
        - error: Search failed
    """
    import asyncio as _asyncio
    import json as _json

    # CRIT-005 AC28-29: Wait for tracker, then check DB — return 404 before SSE if not found
    tracker = None
    for _ in range(60):  # 60 * 0.5s = 30s
        tracker = await get_tracker(search_id)
        if tracker:
            break
        await _asyncio.sleep(0.5)

    db_state = None
    if not tracker:
        # AC9: On reconnection, try to get current state from DB
        try:
            db_state = await get_current_state(search_id)
        except Exception:
            db_state = None

        if not db_state:
            # CRIT-005 AC28: Return 404 when search_id doesn't exist at all
            raise HTTPException(status_code=404, detail="Search not found")

    async def event_generator():
        nonlocal tracker, db_state

        if not tracker and db_state:
            # AC9: Emit current state from DB for reconnection
            state_val = db_state.get("to_state", "error")
            from search_state_manager import _estimate_progress
            progress = _estimate_progress(state_val)
            yield f"data: {_json.dumps({'stage': state_val, 'progress': progress, 'message': f'Estado atual: {state_val}'})}\n\n"
            # If terminal, we're done
            if state_val in ("completed", "failed", "timed_out", "rate_limited"):
                return
            # Otherwise fall through to wait for more events — but we have no tracker
            # so we can't stream further. Just return.
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

                            if event_data.get("stage") in ("complete", "degraded", "error", "refresh_available"):
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

                    if event.stage in ("complete", "degraded", "error", "refresh_available"):
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


# ---------------------------------------------------------------------------
# CRIT-003 AC11: Search status polling endpoint
# ---------------------------------------------------------------------------

@router.get("/v1/search/{search_id}/status")
async def search_status_endpoint(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """AC11: Return current search state for polling fallback.

    Called by frontend when SSE disconnects (AC12).
    Response format matches AC11 specification.
    """
    status = await get_search_status(search_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Search not found")
    return status


# ---------------------------------------------------------------------------
# CRIT-003 AC7: Search timeline endpoint
# ---------------------------------------------------------------------------

@router.get("/v1/search/{search_id}/timeline")
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
    """Return results of a background fetch for cache-first progressive delivery.

    A-04 AC5: Called by frontend when user clicks "Atualizar resultados" banner.
    Returns 404 if search_id not found or expired (10min TTL).
    """
    result = get_background_results(search_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Resultados não encontrados ou expirados. Execute uma nova busca.",
        )
    return result


# ---------------------------------------------------------------------------
# A-04: Background live fetch task
# ---------------------------------------------------------------------------

async def _execute_background_fetch(
    search_id: str,
    request: BuscaRequest,
    user: dict,
    deps: SimpleNamespace,
    cached_response: BuscaResponse,
) -> None:
    """A-04 AC2/AC11: Execute full live fetch in background after cache-first response.

    - Runs full pipeline (validate → prepare → execute → filter → enrich → generate → persist)
    - Emits partial_results SSE events per UF batch (debounced every 3 UFs)
    - Emits refresh_available when complete with diff summary
    - Has its own timeout (FETCH_TIMEOUT) and is cancellable on shutdown
    - Max 1 task per search_id
    """
    import os

    FETCH_TIMEOUT = int(os.environ.get("SEARCH_FETCH_TIMEOUT", str(6 * 60)))  # 6 minutes

    tracker = await get_tracker(search_id)

    try:
        # Force fresh fetch — bypass cache
        original_force_fresh = request.force_fresh
        request.force_fresh = True

        pipeline = SearchPipeline(deps)
        ctx = SearchContext(
            request=request,
            user=user,
            tracker=tracker,
            start_time=sync_time.time(),
        )

        # Run full pipeline with timeout
        response = await asyncio.wait_for(
            pipeline.run(ctx),
            timeout=FETCH_TIMEOUT,
        )

        # Restore original flag
        request.force_fresh = original_force_fresh

        # Store results for /buscar-results/{search_id}
        store_background_results(search_id, response)

        # Calculate diff summary for refresh_available event
        cached_ids = set()
        if cached_response.licitacoes:
            for lic in cached_response.licitacoes:
                lid = getattr(lic, "pncp_id", None) or getattr(lic, "source_id", None)
                if lid:
                    cached_ids.add(lid)

        live_ids = set()
        if response.licitacoes:
            for lic in response.licitacoes:
                lid = getattr(lic, "pncp_id", None) or getattr(lic, "source_id", None)
                if lid:
                    live_ids.add(lid)

        new_count = len(live_ids - cached_ids)
        removed_count = len(cached_ids - live_ids)
        updated_count = len(live_ids & cached_ids)

        # Emit refresh_available (terminal SSE event)
        if tracker:
            await tracker.emit_refresh_available(
                total_live=response.total_filtrado,
                total_cached=cached_response.total_filtrado,
                new_count=new_count,
                updated_count=updated_count,
                removed_count=removed_count,
            )

        logger.info(
            f"A-04: Background fetch complete for {search_id}: "
            f"{response.total_filtrado} live results "
            f"(+{new_count} new, ~{updated_count} updated, -{removed_count} removed)"
        )

    except asyncio.TimeoutError:
        logger.warning(f"A-04: Background fetch timed out for {search_id} after {FETCH_TIMEOUT}s")
        if tracker:
            await tracker.emit_error("Background fetch timed out")
    except asyncio.CancelledError:
        logger.info(f"A-04: Background fetch cancelled for {search_id} (shutdown)")
        raise  # Re-raise for proper cleanup
    except Exception as e:
        logger.warning(f"A-04: Background fetch failed for {search_id}: {type(e).__name__}: {e}")
        if tracker:
            await tracker.emit_error(f"Background fetch failed: {type(e).__name__}")
    finally:
        # Cleanup: remove tracker after background task finishes
        # (only if we still own it — don't remove if already removed)
        if search_id in _active_background_tasks:
            _active_background_tasks.pop(search_id, None)
        await remove_tracker(search_id)


# ---------------------------------------------------------------------------
# Main search endpoint
# ---------------------------------------------------------------------------

@router.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(
    request: BuscaRequest,
    http_response: Response,  # CRIT-005 AC1-2: Injected for response headers
    user: dict = Depends(require_auth),
):
    """
    Main search endpoint — thin wrapper that delegates to SearchPipeline.

    GTM-RESILIENCE-A04: Cache-first progressive delivery.
    When cache exists for this search, returns cached data immediately with
    `live_fetch_in_progress=True` and dispatches background live fetch.
    When no cache, runs synchronous pipeline as before (AC10).

    The wrapper handles:
    - Cache-first check and immediate response (A-04 AC1)
    - Background task dispatch (A-04 AC2)
    - SSE tracker lifecycle (create, cleanup on error)
    - Exception mapping (PNCPRateLimitError → 503, PNCPAPIError → 502, etc.)
    - Dependency injection (passing module-level names for test mock compatibility)
    """
    # SSE Progress Tracking
    # CRIT-011 AC4: Auto-generate search_id if not provided by client
    if not request.search_id:
        import uuid
        request.search_id = str(uuid.uuid4())

    # CRIT-004 AC7: Set search_id in ContextVar for end-to-end log correlation
    tracker = None
    state_machine = None
    from middleware import search_id_var
    search_id_var.set(request.search_id)
    tracker = await create_tracker(request.search_id, len(request.ufs))
    await tracker.emit("connecting", 3, "Iniciando busca...")
    # CRIT-003 AC2: Create state machine for deterministic lifecycle tracking
    state_machine = await create_state_machine(request.search_id)

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

    # -----------------------------------------------------------------------
    # A-04 AC1: Cache-first — check cascade before running full pipeline
    # -----------------------------------------------------------------------
    if not request.force_fresh and request.search_id:
        try:
            from search_cache import get_from_cache_cascade
            from search_pipeline import _build_cache_params

            cache_params = _build_cache_params(request)
            stale_cache = None

            if user and user.get("id"):
                stale_cache = await get_from_cache_cascade(
                    user_id=user["id"],
                    params=cache_params,
                )

            if stale_cache and stale_cache.get("results"):
                logger.info(
                    f"A-04: Cache-first hit for {request.search_id} "
                    f"({stale_cache.get('cache_age_hours', '?')}h old, "
                    f"level={stale_cache.get('cache_level', 'unknown')})"
                )

                # Build immediate response from cache
                # We need to run validate+prepare+filter+generate on cached data
                # But for speed, we return raw cached results with minimal processing
                pipeline = SearchPipeline(deps)
                ctx = SearchContext(
                    request=request,
                    user=user,
                    tracker=None,  # Don't emit progress for cache-first
                    start_time=sync_time.time(),
                )

                # Stage 1+2: Validate and prepare (needed for quota, sector, keywords)
                await pipeline.stage_validate(ctx)
                await pipeline.stage_prepare(ctx)

                # Populate context from cache
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
                ctx.response_state = "cached"

                # Run filter + enrich + generate on cached data
                await pipeline.stage_filter(ctx)
                await pipeline.stage_enrich(ctx)
                await pipeline.stage_generate(ctx)

                # Set live_fetch_in_progress on response
                if ctx.response:
                    ctx.response.live_fetch_in_progress = True

                response = await pipeline.stage_persist(ctx)
                if response:
                    response.live_fetch_in_progress = True

                # A-04 AC2: Dispatch background live fetch
                _cleanup_stale_results()
                active_count = len(_active_background_tasks)
                if active_count < _MAX_BACKGROUND_TASKS and request.search_id not in _active_background_tasks:
                    task = asyncio.create_task(
                        _execute_background_fetch(
                            search_id=request.search_id,
                            request=request,
                            user=user,
                            deps=deps,
                            cached_response=response,
                        )
                    )
                    _active_background_tasks[request.search_id] = task
                    logger.debug(f"A-04: Background fetch task dispatched for {request.search_id}")
                else:
                    # Budget exceeded or duplicate — emit degraded instead
                    logger.warning(
                        f"A-04: Background fetch skipped for {request.search_id} "
                        f"(active={active_count}, max={_MAX_BACKGROUND_TASKS})"
                    )
                    if tracker:
                        from search_pipeline import _build_degraded_detail
                        await tracker.emit_degraded("source_failure", _build_degraded_detail(ctx))
                        await remove_tracker(request.search_id)

                # CRIT-005 AC1-2: Observability headers (cache-first path)
                http_response.headers["X-Response-State"] = ctx.response_state or "live"
                http_response.headers["X-Cache-Level"] = ctx.cache_level or "none"
                return response

        except Exception as cache_err:
            # Cache-first failed — fall through to synchronous path
            logger.debug(f"A-04: Cache-first check failed (falling through to sync): {cache_err}")

    # -----------------------------------------------------------------------
    # AC10: No cache — synchronous pipeline (unchanged flow)
    # -----------------------------------------------------------------------
    pipeline = SearchPipeline(deps)
    ctx = SearchContext(
        request=request,
        user=user,
        tracker=tracker,
        start_time=sync_time.time(),
    )

    try:
        response = await pipeline.run(ctx)

        # SSE: Emit terminal event based on response_state (A-02 AC3-AC5)
        if tracker:
            if ctx.response_state in ("cached", "degraded") or (ctx.is_partial and ctx.response_state == "live"):
                from search_pipeline import _build_degraded_detail
                if ctx.response_state == "cached":
                    reason = "timeout" if "expirou" in (ctx.degradation_reason or "") else "source_failure"
                elif ctx.is_partial and ctx.response_state == "live":
                    reason = "partial"
                else:
                    reason = "source_failure"
                await tracker.emit_degraded(reason, _build_degraded_detail(ctx))
            elif ctx.response_state == "empty_failure":
                await tracker.emit_error(
                    ctx.degradation_guidance or "Fontes temporariamente indisponíveis"
                )
            else:
                await tracker.emit_complete()
            await remove_tracker(request.search_id)

        # CRIT-003: Clean up state machine on success (state already set to COMPLETED by pipeline)
        if state_machine:
            remove_state_machine(request.search_id)

        # CRIT-005 AC1-2: Observability headers (synchronous path)
        http_response.headers["X-Response-State"] = ctx.response_state or "live"
        http_response.headers["X-Cache-Level"] = ctx.cache_level or "none"
        return response

    except PNCPRateLimitError as e:
        # CRIT-003: Transition state machine on rate limit
        if state_machine:
            await state_machine.rate_limited(retry_after=getattr(e, "retry_after", 60))
            remove_state_machine(request.search_id)
        # CRIT-002 AC12: Update session status on error
        if ctx.session_id:
            retry_after = getattr(e, "retry_after", 60)
            import asyncio as _aio
            _aio.create_task(
                _update_session_on_error(
                    ctx.session_id, ctx.start_time,
                    status="failed", error_code="sources_unavailable",
                    error_message=f"PNCP rate limit: retry after {retry_after}s",
                    pipeline_stage=None, response_state=None,
                )
            )
        if tracker:
            await tracker.emit_error(f"PNCP rate limit: {e}")
            await remove_tracker(request.search_id)
        logger.warning(f"PNCP rate limit exceeded: {type(e).__name__}: {e}")
        retry_after = getattr(e, "retry_after", 60)
        # CRIT-009 AC3: Structured error response
        corr_id = getattr(getattr(http_response, '_request', None), 'state', SimpleNamespace()).correlation_id if hasattr(http_response, '_request') else None
        try:
            from middleware import correlation_id_var
            corr_id = correlation_id_var.get("-")
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail=_build_error_detail(
                f"As fontes de dados estão temporariamente limitando consultas. "
                f"Aguarde {retry_after} segundos e tente novamente.",
                SearchErrorCode.RATE_LIMIT,
                search_id=request.search_id,
                correlation_id=corr_id if corr_id != "-" else None,
            ),
            headers={"Retry-After": str(retry_after)},
        )

    except PNCPAPIError as e:
        # CRIT-003: Transition state machine on API error
        if state_machine:
            await state_machine.fail(str(e)[:300], error_code="sources_unavailable")
            remove_state_machine(request.search_id)
        # CRIT-002 AC12: Update session status on error
        if ctx.session_id:
            import asyncio as _aio
            _aio.create_task(
                _update_session_on_error(
                    ctx.session_id, ctx.start_time,
                    status="failed", error_code="sources_unavailable",
                    error_message=str(e)[:500],
                    pipeline_stage=None, response_state=None,
                )
            )
        if tracker:
            await tracker.emit_error(f"PNCP API error: {e}")
            await remove_tracker(request.search_id)
        logger.error(f"PNCP API error: {e}", exc_info=True)
        # CRIT-009 AC3: Structured error response
        corr_id = None
        try:
            from middleware import correlation_id_var
            corr_id = correlation_id_var.get("-")
            if corr_id == "-":
                corr_id = None
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=_build_error_detail(
                "Nossas fontes de dados estão temporariamente indisponíveis. "
                "Tente novamente em alguns instantes ou reduza o número "
                "de estados selecionados.",
                SearchErrorCode.SOURCE_UNAVAILABLE,
                search_id=request.search_id,
                correlation_id=corr_id,
            ),
        )

    except HTTPException as exc:
        # CRIT-003: Transition state machine on HTTP error
        if state_machine:
            if exc.status_code == 504:
                await state_machine.timeout()
            else:
                await state_machine.fail(f"HTTP {exc.status_code}: {exc.detail}"[:300])
            remove_state_machine(request.search_id)
        # CRIT-002 AC12: Update session status on error
        if ctx.session_id:
            import asyncio as _aio
            _aio.create_task(
                _update_session_on_error(
                    ctx.session_id, ctx.start_time,
                    status="failed" if exc.status_code != 504 else "timed_out",
                    error_code="timeout" if exc.status_code == 504 else "unknown",
                    error_message=f"HTTP {exc.status_code}: {exc.detail}"[:500],
                    pipeline_stage=None, response_state=None,
                )
            )
        if tracker:
            await tracker.emit_error("Erro no processamento")
            await remove_tracker(request.search_id)
        # CRIT-009 AC3: Enrich HTTPException with structured error if not already structured
        if isinstance(exc.detail, str):
            corr_id = None
            try:
                from middleware import correlation_id_var
                corr_id = correlation_id_var.get("-")
                if corr_id == "-":
                    corr_id = None
            except Exception:
                pass
            # Map HTTP status to error code
            if exc.status_code == 504:
                err_code = SearchErrorCode.TIMEOUT
            elif exc.status_code == 403:
                err_code = SearchErrorCode.QUOTA_EXCEEDED
            elif exc.status_code == 429:
                err_code = SearchErrorCode.RATE_LIMIT
            elif exc.status_code == 422 or exc.status_code == 400:
                err_code = SearchErrorCode.VALIDATION_ERROR
            else:
                err_code = SearchErrorCode.INTERNAL_ERROR
            exc.detail = _build_error_detail(
                exc.detail,
                err_code,
                search_id=request.search_id,
                correlation_id=corr_id,
            )
        raise

    except Exception as e:
        # CRIT-003: Transition state machine on unexpected error
        if state_machine:
            await state_machine.fail(f"{type(e).__name__}: {str(e)[:200]}", error_code="unknown")
            remove_state_machine(request.search_id)
        # CRIT-002 AC12: Update session status on error
        if ctx.session_id:
            import asyncio as _aio
            _aio.create_task(
                _update_session_on_error(
                    ctx.session_id, ctx.start_time,
                    status="failed", error_code="unknown",
                    error_message=f"{type(e).__name__}: {str(e)[:300]}",
                    pipeline_stage=None, response_state=None,
                )
            )
        if tracker:
            await tracker.emit_error("Erro interno do servidor")
            await remove_tracker(request.search_id)
        logger.exception("Internal server error during procurement search")
        # CRIT-009 AC3: Structured error response — never expose stack traces
        corr_id = None
        try:
            from middleware import correlation_id_var
            corr_id = correlation_id_var.get("-")
            if corr_id == "-":
                corr_id = None
        except Exception:
            pass
        # Determine error_code based on exception type
        if isinstance(e, asyncio.TimeoutError):
            err_code = SearchErrorCode.TIMEOUT
            err_msg = "A busca excedeu o tempo limite. Tente com menos estados ou um período menor."
            status_code = 504
        else:
            err_code = SearchErrorCode.INTERNAL_ERROR
            err_msg = "Erro interno do servidor. Tente novamente em alguns instantes."
            status_code = 500
        raise HTTPException(
            status_code=status_code,
            detail=_build_error_detail(
                err_msg,
                err_code,
                search_id=request.search_id,
                correlation_id=corr_id,
            ),
        )



# ---------------------------------------------------------------------------
# CRIT-006 AC4-5: Retry search with only missing/failed UFs
# ---------------------------------------------------------------------------

@router.post("/v1/search/{search_id}/retry")
async def retry_search(
    search_id: str,
    user: dict = Depends(require_auth),
):
    """CRIT-006 AC4-5: Retry search with only missing/failed UFs."""
    from database import get_db as _get_db

    db = _get_db()
    try:
        session_result = (
            db.table("search_sessions")
            .select("failed_ufs, ufs, status")
            .eq("id", search_id)
            .eq("user_id", user["id"])
            .single()
            .execute()
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

@router.post("/v1/search/{search_id}/cancel")
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
