"""
Search Router — Main procurement search endpoint (POST /buscar).

DEBT-115: Decomposed from 2177 LOC monolith into focused modules:
- routes/search_sse.py: SSE progress stream (GET /buscar-progress/{id})
- routes/search_state.py: Background results, async search, persistence
- routes/search_status.py: Status, results, retry, cancel endpoints
- routes/search.py (this file): POST /buscar orchestration + backward-compat re-exports

STORY-216: buscar_licitacoes() decomposed into SearchPipeline (search_pipeline.py).
This module is now a thin wrapper that delegates to the pipeline.

GTM-RESILIENCE-A04: Cache-first progressive delivery.
When cache exists, returns immediately and spawns background live fetch.
"""

import asyncio
import os
import time as sync_time
import uuid as _uuid

import sentry_sdk

from types import SimpleNamespace
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from starlette.responses import StreamingResponse, JSONResponse as StarletteJSONResponse

# === Module-level imports preserved for test mock compatibility (AC11) ===
# Tests use @patch("routes.search.X") to mock these names.
# The thin wrapper passes them to SearchPipeline as deps.
from config import ENABLE_NEW_PRICING
from schemas import BuscaRequest, BuscaResponse, SearchErrorCode, SearchStatusResponse
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
from rate_limiter import (
    rate_limiter,
    require_rate_limit,
    acquire_sse_connection,
    release_sse_connection,
    SEARCH_RATE_LIMIT_PER_MINUTE,
    SSE_RECONNECT_RATE_LIMIT,
    SSE_RECONNECT_WINDOW_SECONDS,
    _flexible_limiter,
)
from progress import create_tracker, get_tracker, remove_tracker, get_replay_events, is_search_terminal
from redis_pool import get_redis_pool, get_sse_redis_pool
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

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["search"])

# SYS-011 / DEBT-015: delegate to the project-wide helper; keep local name for
# backward compatibility with tests that patch "routes.search._build_error_detail".
from error_response import build_error_detail as _build_error_detail  # noqa: E402

# Helper functions moved to search_pipeline.py (STORY-216 AC6)
# Re-exported for any external callers (backward compat)
from search_pipeline import _build_pncp_link, _calcular_urgencia, _calcular_dias_restantes, _convert_to_licitacao_items  # noqa: F401, E402

# ---------------------------------------------------------------------------
# DEBT-115: Include sub-routers for decomposed endpoints
# ---------------------------------------------------------------------------
from routes.search_sse import router as _sse_router  # noqa: E402
from routes.search_status import router as _status_router  # noqa: E402

router.include_router(_sse_router)
router.include_router(_status_router)

# ---------------------------------------------------------------------------
# DEBT-115: Re-export all symbols from sub-modules for backward compatibility.
# Tests and other modules import these from routes.search — keep working.
# ---------------------------------------------------------------------------
from routes.search_sse import (  # noqa: F401, E402
    _SSE_HEARTBEAT_INTERVAL,
    _SSE_WAIT_HEARTBEAT_EVERY,
    _SSE_POLL_INTERVAL,
    _SSE_POLLS_PER_HEARTBEAT,
    buscar_progress_stream,
)

from routes.search_state import (  # noqa: F401, E402
    _background_results,
    _RESULTS_TTL,
    _active_background_tasks,
    _MAX_BACKGROUND_TASKS,
    _MAX_BACKGROUND_RESULTS,
    _RESULTS_REDIS_PREFIX,
    get_background_results_count,
    _cleanup_stale_results,
    store_background_results,
    _persist_results_to_redis,
    _persist_results_to_supabase,
    _safe_persist_results,
    _persist_done_callback,
    _get_results_from_supabase,
    _get_results_from_redis,
    get_background_results,
    get_background_results_async,
    _update_session_on_error,
    _update_session_on_complete,
    _apply_trial_paywall,
    _execute_background_fetch,
    _run_async_search,
    _ASYNC_SEARCH_TIMEOUT,
)

from routes.search_status import (  # noqa: F401, E402
    search_status_endpoint,
    search_timeline_endpoint,
    get_search_results,
    get_search_results_v1,
    get_zero_match_results_endpoint,
    regenerate_excel_endpoint,
    retry_search,
    cancel_search,
)


def get_correlation_id() -> str | None:
    """CRIT-050 AC9: Extract correlation ID from middleware ContextVar.

    Eliminates repeated try/except + import pattern across error handlers.
    Returns None if unavailable (middleware not loaded, outside request context).
    """
    try:
        from middleware import correlation_id_var
        corr_id = correlation_id_var.get("-")
        return None if corr_id == "-" else corr_id
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main search endpoint
# ---------------------------------------------------------------------------

@router.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(
    request: BuscaRequest,
    raw_request: Request,  # GTM-STAB-009 AC6: For X-Sync header inspection
    http_response: Response,  # CRIT-005 AC1-2: Injected for response headers
    user: dict = Depends(require_auth),
    _rl=Depends(require_rate_limit(SEARCH_RATE_LIMIT_PER_MINUTE, 60)),  # GTM-GO-002 AC1
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

    STORY-291 AC5: require_active_plan() moved INSIDE try block, AFTER tracker
    creation. Previously, when it failed the frontend was left in limbo — POST
    failed but SSE was waiting for a tracker that never existed.
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

    # GTM-STAB-008 AC6: Sentry context tags for triaging
    _search_start = sync_time.time()
    _search_mode = "terms" if request.termos_busca else "sector"
    sentry_sdk.set_tag("search_mode", _search_mode)
    sentry_sdk.set_tag("uf_count", len(request.ufs))
    if not request.termos_busca:
        sentry_sdk.set_tag("setor", request.setor_id)

    tracker = await create_tracker(request.search_id, len(request.ufs))
    await tracker.emit("connecting", 3, "Iniciando análise...")

    # STORY-291 AC5: Block expired trials AFTER tracker creation so SSE
    # can emit an error event instead of leaving frontend in limbo.
    from quota import require_active_plan
    try:
        await require_active_plan(user)
    except HTTPException as plan_err:
        await tracker.emit_error(
            plan_err.detail.get("message", str(plan_err.detail))
            if isinstance(plan_err.detail, dict)
            else str(plan_err.detail)
        )
        await remove_tracker(request.search_id)
        raise
    # CRIT-003 AC2: Create state machine for deterministic lifecycle tracking
    # DEBT-009 DB-007: Pass user_id for direct column in search_state_transitions
    state_machine = await create_state_machine(request.search_id, user_id=user.get("id"))

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
    # STORY-363: Async search — ARQ Worker (primary) with in-process fallback
    # -----------------------------------------------------------------------
    from config import get_feature_flag

    # AC14: X-Sync header forces synchronous mode (backward compat)
    force_sync = (
        raw_request.headers.get("x-sync", "").lower() == "true"
        or raw_request.query_params.get("sync", "").lower() == "true"
    )

    # CRIT-072: ASYNC_SEARCH_DEFAULT=True makes 202 the default mode.
    # Falls back to sync via X-Sync header, ?sync=true, or ASYNC_SEARCH_DEFAULT=False.
    from config import ASYNC_SEARCH_DEFAULT
    _async_enabled = ASYNC_SEARCH_DEFAULT or get_feature_flag("SEARCH_ASYNC_ENABLED")
    if _async_enabled and not force_sync:
        logger.info(f"CRIT-072: Async mode — dispatching to ARQ Worker for {request.search_id}")

        # Consume quota in POST before dispatching (prevents wasted work)
        # PHASE-0: 15s timeout prevents Supabase latency from blocking POST response
        _QUOTA_CHECK_TIMEOUT = 15  # seconds
        try:
            async def _do_quota_check():
                import quota as _quota
                from authorization import get_admin_ids as _get_admin_ids

                _is_admin = user["id"].lower() in _get_admin_ids()
                _is_master = False
                if not _is_admin:
                    _is_admin, _is_master = await check_user_roles(user["id"])

                if not (_is_admin or _is_master):
                    _quota_info = await asyncio.to_thread(_quota.check_quota, user["id"])
                    if not _quota_info.allowed:
                        if tracker:
                            await tracker.emit_error(_quota_info.error_message)
                            await remove_tracker(request.search_id)
                        raise HTTPException(status_code=403, detail=_quota_info.error_message)

                    # CRIT-050 AC7: Safe .get() access on capabilities dict
                    _max_monthly = _quota_info.capabilities.get("max_requests_per_month", 1000)
                    _allowed, _new_used, _remaining = await asyncio.to_thread(
                        _quota.check_and_increment_quota_atomic,
                        user["id"],
                        _max_monthly,
                    )
                    if not _allowed:
                        if tracker:
                            await tracker.emit_error("Suas análises acabaram.")
                            await remove_tracker(request.search_id)
                        raise HTTPException(
                            status_code=403,
                            detail=(
                                f"Limite de {_max_monthly} "
                                f"análises mensais atingido."
                            ),
                        )

            await asyncio.wait_for(_do_quota_check(), timeout=_QUOTA_CHECK_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(
                f"PHASE-0: Quota check timed out after {_QUOTA_CHECK_TIMEOUT}s for "
                f"{request.search_id} — proceeding with async dispatch (allow-through)"
            )
        except HTTPException:
            raise
        except Exception as quota_err:
            logger.warning(f"STORY-363: Quota check failed, falling through to sync: {quota_err}")
            # Fall through to sync/cache-first path below
            force_sync = True

        if not force_sync:
            # STORY-363 AC14: Check concurrent search limit per user
            from job_queue import acquire_search_slot, enqueue_job, is_queue_available
            _slot_acquired = await acquire_search_slot(user["id"], request.search_id)
            if not _slot_acquired:
                from config import MAX_CONCURRENT_SEARCHES
                await tracker.emit_error(
                    f"Limite de {MAX_CONCURRENT_SEARCHES} análises simultâneas atingido. "
                    f"Aguarde uma análise terminar."
                )
                await remove_tracker(request.search_id)
                raise HTTPException(
                    status_code=429,
                    detail=f"Limite de {MAX_CONCURRENT_SEARCHES} análises simultâneas atingido.",
                )

            # STORY-363 AC2: Try ARQ Worker first (true decoupling from HTTP)
            _arq_dispatched = False
            if await is_queue_available():
                from datetime import datetime, timezone as _tz
                _job = await enqueue_job(
                    "search_job",
                    request.search_id,
                    request.model_dump(mode="json"),
                    user,
                    _job_id=f"search:{request.search_id}",
                    _queued_at=datetime.now(_tz.utc).isoformat(),
                )
                if _job is not None:
                    _arq_dispatched = True
                    logger.info(
                        f"STORY-363 AC2: Search job enqueued to ARQ Worker for "
                        f"{request.search_id} (job_id={_job.job_id})"
                    )

            if not _arq_dispatched:
                # Fallback: asyncio.create_task in-process (STORY-292 behavior)
                logger.warning(
                    f"STORY-363: ARQ unavailable — falling back to in-process task for "
                    f"{request.search_id}"
                )
                task = asyncio.create_task(
                    _run_async_search(
                        search_id=request.search_id,
                        request=request,
                        user=user,
                        deps=deps,
                        tracker=tracker,
                        state_machine=state_machine,
                    )
                )
                _active_background_tasks[request.search_id] = task

            # CRIT-072 AC1+AC9: Return 202 Accepted in <2s with Location header
            from metrics import SEARCH_MODE_TOTAL
            SEARCH_MODE_TOTAL.labels(mode="async").inc()
            num_ufs = len(request.ufs) if request.ufs else 1
            status_url = f"/v1/search/{request.search_id}/status"
            results_url = f"/v1/search/{request.search_id}/results"
            logger.info(f"CRIT-072: Returning 202 for {request.search_id} (arq={_arq_dispatched})")
            return StarletteJSONResponse(
                status_code=202,
                content={
                    "search_id": request.search_id,
                    "status": "queued",
                    "status_url": status_url,
                    "results_url": results_url,
                    "progress_url": f"/buscar-progress/{request.search_id}",
                    "estimated_duration_s": min(15 + num_ufs * 8, 120),
                },
                headers={"Location": status_url},
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

                # STORY-320 AC3: Apply trial paywall truncation (cache-first path)
                response = _apply_trial_paywall(response, user)

                # CRIT-005 AC1-2: Observability headers (cache-first path)
                http_response.headers["X-Response-State"] = ctx.response_state or "live"
                http_response.headers["X-Cache-Level"] = ctx.cache_level or "none"
                # GTM-STAB-008 AC6: elapsed_s tag (cache-first path)
                sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
                return response

        except Exception as cache_err:
            # Cache-first failed — fall through to synchronous path
            logger.debug(f"A-04: Cache-first check failed (falling through to sync): {cache_err}")

    # -----------------------------------------------------------------------
    # AC10: No cache — synchronous pipeline (unchanged flow)
    # CRIT-072 AC9: Count sync mode searches
    # -----------------------------------------------------------------------
    from metrics import SEARCH_MODE_TOTAL
    SEARCH_MODE_TOTAL.labels(mode="sync").inc()
    pipeline = SearchPipeline(deps)
    ctx = SearchContext(
        request=request,
        user=user,
        tracker=tracker,
        start_time=sync_time.time(),
    )

    try:
        response = await pipeline.run(ctx)

        # STORY-320 AC3: Apply trial paywall truncation (sync path)
        response = _apply_trial_paywall(response, user)

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
        # GTM-STAB-008 AC6: elapsed_s tag (synchronous path)
        sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
        return response

    except PNCPRateLimitError as e:
        # GTM-STAB-008 AC6: elapsed_s tag on rate limit error
        sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
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
        # CRIT-009 AC3 + CRIT-050 AC9: Structured error response
        raise HTTPException(
            status_code=503,
            detail=_build_error_detail(
                f"As fontes de dados estão temporariamente limitando consultas. "
                f"Aguarde {retry_after} segundos e tente novamente.",
                SearchErrorCode.RATE_LIMIT,
                search_id=request.search_id,
                correlation_id=get_correlation_id(),
            ),
            headers={"Retry-After": str(retry_after)},
        )

    except PNCPAPIError as e:
        # GTM-STAB-008 AC6: elapsed_s tag on API error
        sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
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
        # CRIT-009 AC3 + CRIT-050 AC9: Structured error response
        raise HTTPException(
            status_code=502,
            detail=_build_error_detail(
                "Nossas fontes de dados estão temporariamente indisponíveis. "
                "Tente novamente em alguns instantes ou reduza o número "
                "de estados selecionados.",
                SearchErrorCode.SOURCE_UNAVAILABLE,
                search_id=request.search_id,
                correlation_id=get_correlation_id(),
            ),
        )

    except HTTPException as exc:
        # GTM-STAB-008 AC6: elapsed_s tag on HTTP error
        sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
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
        # CRIT-009 AC3 + CRIT-050 AC9: Enrich HTTPException with structured error if not already structured
        if isinstance(exc.detail, str):
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
                correlation_id=get_correlation_id(),
            )
        raise

    except Exception as e:
        # GTM-STAB-008 AC6: elapsed_s tag on error path
        sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
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

        # GTM-STAB-004 AC6: If partial results were collected before failure, return
        # them as HTTP 200 with is_partial=True instead of raising HTTP 5xx.
        if ctx.response and getattr(ctx.response, "licitacoes", None):
            logger.warning(
                f"STAB-004: Exception after partial results — returning {len(ctx.response.licitacoes)} "
                f"results as partial (error: {type(e).__name__}: {e})"
            )
            if tracker:
                from search_pipeline import _build_degraded_detail
                await tracker.emit_degraded("source_failure", _build_degraded_detail(ctx))
                await remove_tracker(request.search_id)
            ctx.response.is_partial = True
            ctx.response.degradation_reason = (
                ctx.response.degradation_reason
                or f"Resultado parcial — erro interno: {type(e).__name__}"
            )
            http_response.headers["X-Response-State"] = "degraded"
            http_response.headers["X-Cache-Level"] = ctx.cache_level or "none"
            return ctx.response
        elif ctx.licitacoes_filtradas:
            # Pipeline generated filtered results but stage_generate/persist failed;
            # build a minimal partial response so the user gets something useful.
            logger.warning(
                f"STAB-004: Exception with {len(ctx.licitacoes_filtradas)} filtered results — "
                f"building minimal partial response (error: {type(e).__name__}: {e})"
            )
            if tracker:
                from search_pipeline import _build_degraded_detail
                await tracker.emit_degraded("source_failure", _build_degraded_detail(ctx))
                await remove_tracker(request.search_id)
            from search_pipeline import _convert_to_licitacao_items
            from llm import gerar_resumo_fallback
            items = _convert_to_licitacao_items(ctx.licitacoes_filtradas)
            _fb_resumo = gerar_resumo_fallback(ctx.licitacoes_filtradas)
            _qi = ctx.quota_info
            partial_response = BuscaResponse(
                licitacoes=items,
                resumo=_fb_resumo,
                excel_available=ctx.excel_available,
                quota_used=_qi.quota_used if _qi else 0,
                quota_remaining=_qi.quota_remaining if _qi else 999,
                total_raw=len(ctx.licitacoes_raw),
                total_filtrado=len(ctx.licitacoes_filtradas),
                is_partial=True,
                degradation_reason=f"Resultado parcial — erro interno: {type(e).__name__}",
            )
            http_response.headers["X-Response-State"] = "degraded"
            http_response.headers["X-Cache-Level"] = ctx.cache_level or "none"
            return partial_response

        if tracker:
            await tracker.emit_error("Erro interno do servidor")
            await remove_tracker(request.search_id)
        logger.exception("Internal server error during procurement search")
        # CRIT-009 AC3 + CRIT-050 AC9: Structured error response — never expose stack traces
        # Determine error_code based on exception type
        if isinstance(e, asyncio.TimeoutError):
            err_code = SearchErrorCode.TIMEOUT
            err_msg = "A análise excedeu o tempo limite. Tente com menos estados ou um período menor."
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
                correlation_id=get_correlation_id(),
            ),
        )
