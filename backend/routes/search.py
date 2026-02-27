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
)
from progress import create_tracker, get_tracker, remove_tracker
from redis_pool import get_redis_pool
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

# CRIT-012 AC2: Heartbeat interval reduced from 30s to 15s
_SSE_HEARTBEAT_INTERVAL = 15.0
_SSE_WAIT_HEARTBEAT_EVERY = 10  # Every 10 iterations of 0.5s = 5s

# CRIT-026-ROOT: Polled XREAD constants (replacing XREAD BLOCK).
# Non-blocking XREAD polls every _SSE_POLL_INTERVAL seconds.
# Heartbeat SSE comment sent every _SSE_POLLS_PER_HEARTBEAT empty polls.
_SSE_POLL_INTERVAL = 1.0   # seconds between non-blocking polls
_SSE_POLLS_PER_HEARTBEAT = 15  # heartbeat every ~15s (15 polls * 1s)


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
# A-04 + STORY-294: Background fetch results (in-memory L1 + Redis L2)
# ---------------------------------------------------------------------------
_background_results: Dict[str, Dict[str, Any]] = {}
_RESULTS_TTL = 600  # 10 minutes (in-memory)
_active_background_tasks: Dict[str, asyncio.Task] = {}
_MAX_BACKGROUND_TASKS = 5  # Budget: max concurrent background fetches

# STORY-294 AC2: Redis key prefix and TTL for cross-worker result sharing
_RESULTS_REDIS_PREFIX = "smartlic:results:"


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
    """Store results in in-memory L1 cache."""
    _background_results[search_id] = {
        "response": response,
        "stored_at": sync_time.time(),
    }


async def _persist_results_to_redis(search_id: str, response: Any) -> None:
    """STORY-294 AC2: Persist results to Redis for cross-worker access.

    Stores as JSON string with TTL from config.RESULTS_REDIS_TTL (30min default).
    Fire-and-forget: errors are logged and metriced, never raised.
    """
    import json as _json

    redis = await get_redis_pool()
    if not redis:
        return

    try:
        from config import RESULTS_REDIS_TTL
        key = f"{_RESULTS_REDIS_PREFIX}{search_id}"

        # Serialize: BuscaResponse → dict → JSON
        if hasattr(response, "model_dump"):
            data = response.model_dump(mode="json")
        elif hasattr(response, "dict"):
            data = response.dict()
        elif isinstance(response, dict):
            data = response
        else:
            logger.warning(f"STORY-294: Cannot serialize response type {type(response)}")
            return

        await redis.setex(key, RESULTS_REDIS_TTL, _json.dumps(data, default=str))
        logger.debug(f"STORY-294: Results stored in Redis: {key} (TTL={RESULTS_REDIS_TTL}s)")

    except Exception as e:
        from metrics import STATE_STORE_ERRORS
        STATE_STORE_ERRORS.labels(store="results", operation="write").inc()
        logger.warning(f"STORY-294: Failed to persist results to Redis: {e}")


async def _get_results_from_redis(search_id: str) -> Optional[Dict[str, Any]]:
    """STORY-294 AC5: Read results from Redis (cross-worker)."""
    import json as _json

    redis = await get_redis_pool()
    if not redis:
        return None

    try:
        key = f"{_RESULTS_REDIS_PREFIX}{search_id}"
        data = await redis.get(key)
        if data:
            logger.debug(f"STORY-294: Results retrieved from Redis: {key}")
            return _json.loads(data)
    except Exception as e:
        from metrics import STATE_STORE_ERRORS
        STATE_STORE_ERRORS.labels(store="results", operation="read").inc()
        logger.warning(f"STORY-294: Failed to read results from Redis: {e}")

    return None


def get_background_results(search_id: str) -> Optional[BuscaResponse]:
    """Retrieve background fetch results from in-memory L1 cache.

    For cross-worker access, use get_background_results_async() which checks Redis.
    """
    entry = _background_results.get(search_id)
    if entry and sync_time.time() - entry["stored_at"] < _RESULTS_TTL:
        return entry["response"]
    return None


async def get_background_results_async(search_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve search results: in-memory L1 → Redis L2 → ARQ Worker results.

    STORY-294 AC5: Cross-worker result retrieval via Redis.
    GTM-ARCH-001: Also checks ARQ Worker results as last resort.
    """
    # L1: Check in-memory first (same worker — fast path)
    sync_result = get_background_results(search_id)
    if sync_result:
        return sync_result

    # L2: Check Redis (cross-worker — STORY-294)
    redis_result = await _get_results_from_redis(search_id)
    if redis_result:
        return redis_result

    # L3: Check ARQ Worker results (job_queue)
    from job_queue import get_job_result
    arq_result = await get_job_result(search_id, "search_result")
    if arq_result:
        return arq_result

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

    GTM-GO-002 AC6: Max 3 simultaneous SSE connections per user.

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

    # GTM-GO-002 AC6: Enforce SSE connection limit per user
    user_id = user.get("id", "unknown")
    if not await acquire_sse_connection(user_id):
        raise HTTPException(
            status_code=429,
            detail={
                "detail": "Limite de conexões SSE excedido. Feche outras abas antes de abrir uma nova.",
                "retry_after_seconds": 5,
                "correlation_id": str(_uuid.uuid4()),
            },
            headers={"Retry-After": "5"},
        )

    async def event_generator():
        # GTM-GO-002 AC6: Release SSE slot when generator finishes
        heartbeat_count = 0
        try:
            # CRIT-012 AC1: Wait for tracker with SSE keepalive comments every 5s
            # Moved inside generator so heartbeats flow before first real event
            tracker = None
            for i in range(60):  # 60 * 0.5s = 30s
                tracker = await get_tracker(search_id)
                if tracker:
                    break
                # CRIT-012 AC1: Emit SSE comment every 5s to keep connection alive
                if i > 0 and i % _SSE_WAIT_HEARTBEAT_EVERY == 0:
                    heartbeat_count += 1
                    yield ": waiting\n\n"
                    # CRIT-012 AC3: Telemetry logging
                    logger.debug(
                        f"CRIT-012: Wait heartbeat #{heartbeat_count} for {search_id} "
                        f"(elapsed={i * 0.5:.1f}s)"
                    )
                await _asyncio.sleep(0.5)

            # CRIT-005 AC28-29: Check DB state if no tracker found
            db_state = None
            if not tracker:
                try:
                    db_state = await get_current_state(search_id)
                except Exception:
                    db_state = None

                if not db_state:
                    # CRIT-012: Emit error event (can't use HTTP 404 — headers already sent)
                    from metrics import SSE_CONNECTION_ERRORS
                    SSE_CONNECTION_ERRORS.labels(error_type="tracker_not_found", phase="wait").inc()
                    yield f'data: {_json.dumps({"stage": "error", "progress": -1, "message": "Search not found"})}\n\n'
                    return

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

            # STORY-276: Try Redis Streams first, fallback to in-memory queue
            _use_streams = tracker._use_redis
            _redis = None
            if _use_streams:
                _redis = await get_redis_pool()
                if not _redis:
                    _use_streams = False
                    logger.warning(
                        f"Redis unavailable for SSE {search_id}, falling back to queue"
                    )

            if _use_streams:
                # CRIT-026-ROOT: Non-blocking polled XREAD replaces XREAD BLOCK.
                #
                # WHY: redis-py applies socket_timeout (global) to the ENTIRE
                # XREAD BLOCK response wait. With socket_timeout=5s and block=15s,
                # the socket layer kills the connection after 5s — BEFORE the
                # 15s block timeout completes. This is a KNOWN BUG in redis-py:
                #   - https://github.com/redis/redis-py/issues/2807
                #   - https://github.com/redis/redis-py/issues/3454
                #   - https://github.com/redis/redis-py/issues/2663
                #
                # SOLUTION: Use non-blocking XREAD (no BLOCK param) + asyncio.sleep
                # polling. This completely sidesteps the socket_timeout conflict
                # AND avoids connection pool corruption from stuck blocking reads
                # (redis-py #2663). 1s poll interval is negligible latency for
                # SSE progress updates.
                #
                # Preserves STORY-276 at-least-once delivery guarantee: XREAD
                # with last_id still replays all entries from any point.
                _stream_key = f"smartlic:progress:{search_id}:stream"
                _last_id = "0"  # AC2: id=0 reads ALL history since beginning
                _polls_since_heartbeat = 0
                _consecutive_errors = 0
                _MAX_CONSECUTIVE_ERRORS = 5  # circuit breaker for Redis failures
                logger.debug(f"SSE using Redis Streams (polled) for {search_id}")

                while True:
                    try:
                        # Non-blocking XREAD — returns immediately with data or empty
                        result = await _redis.xread(
                            {_stream_key: _last_id},
                            count=100,
                        )
                        _consecutive_errors = 0  # reset on success

                        if not result:
                            # No new data — poll again after sleep
                            _polls_since_heartbeat += 1
                            if _polls_since_heartbeat >= _SSE_POLLS_PER_HEARTBEAT:
                                heartbeat_count += 1
                                yield ": heartbeat\n\n"
                                logger.debug(
                                    f"CRIT-012: Heartbeat #{heartbeat_count} "
                                    f"for {search_id} (streams-polled)"
                                )
                                _polls_since_heartbeat = 0
                            await _asyncio.sleep(_SSE_POLL_INTERVAL)
                            continue

                        # AC2: Process entries, updating last_id for subsequent reads
                        _polls_since_heartbeat = 0  # reset on data received
                        for _stream_name, entries in result:
                            for entry_id, fields in entries:
                                _last_id = entry_id
                                event_data = {
                                    "stage": fields["stage"],
                                    "progress": int(fields["progress"]),
                                    "message": fields["message"],
                                }
                                detail_json = fields.get("detail_json", "{}")
                                if detail_json and detail_json != "{}":
                                    event_data["detail"] = _json.loads(detail_json)
                                # Preserve correlation fields
                                for _extra in ("trace_id", "search_id", "request_id"):
                                    if _extra in fields:
                                        event_data[_extra] = fields[_extra]

                                yield f"data: {_json.dumps(event_data)}\n\n"

                                if fields["stage"] in (
                                    "complete", "degraded", "error",
                                    "refresh_available", "search_complete",
                                ):
                                    return

                    except _asyncio.CancelledError:
                        from metrics import SSE_CONNECTION_ERRORS
                        SSE_CONNECTION_ERRORS.labels(
                            error_type="cancelled", phase="streaming"
                        ).inc()
                        break

                    except Exception as redis_err:
                        # CRIT-026-ROOT: Circuit breaker for transient Redis errors.
                        # Instead of crashing the SSE generator on first error,
                        # retry up to _MAX_CONSECUTIVE_ERRORS times with backoff.
                        _consecutive_errors += 1
                        logger.warning(
                            f"CRIT-026: Redis read error #{_consecutive_errors} "
                            f"for {search_id}: {type(redis_err).__name__}: {redis_err}"
                        )
                        if _consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                            logger.error(
                                f"CRIT-026: Circuit breaker open for {search_id} "
                                f"after {_consecutive_errors} consecutive Redis errors, "
                                f"falling back to in-memory queue"
                            )
                            # Fall through to in-memory mode
                            _use_streams = False
                            break
                        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                        _backoff = min(2 ** (_consecutive_errors - 1), 16)
                        await _asyncio.sleep(_backoff)

            if not _use_streams:
                # AC3: In-memory mode — fallback asyncio.Queue (no Redis)
                # Also entered when CRIT-026-ROOT circuit breaker opens mid-stream.
                logger.debug(f"SSE using in-memory queue for {search_id}")
                while True:
                    try:
                        # CRIT-012 AC2: Heartbeat interval as timeout
                        event = await _asyncio.wait_for(
                            tracker.queue.get(),
                            timeout=_SSE_HEARTBEAT_INTERVAL,
                        )
                        yield f"data: {_json.dumps(event.to_dict())}\n\n"

                        if event.stage in (
                            "complete", "degraded", "error",
                            "refresh_available", "search_complete",
                        ):
                            break

                    except _asyncio.TimeoutError:
                        heartbeat_count += 1
                        yield ": heartbeat\n\n"
                        logger.debug(
                            f"CRIT-012: Heartbeat #{heartbeat_count} "
                            f"for {search_id} (in-memory)"
                        )

                    except _asyncio.CancelledError:
                        from metrics import SSE_CONNECTION_ERRORS
                        SSE_CONNECTION_ERRORS.labels(
                            error_type="cancelled", phase="streaming"
                        ).inc()
                        break
        except Exception as gen_exc:
            # CRIT-026 AC8: Log when SSE generator finishes abruptly (unexpected exception)
            from metrics import SSE_CONNECTION_ERRORS, WORKER_TIMEOUT
            SSE_CONNECTION_ERRORS.labels(error_type="generator_abrupt", phase="streaming").inc()
            WORKER_TIMEOUT.labels(reason="sse_generator_exception").inc()
            logger.error(
                f"CRIT-026: SSE generator abrupt finish for {search_id}: "
                f"{type(gen_exc).__name__}: {gen_exc}"
            )
        finally:
            # CRIT-026 AC8: Log SSE generator lifecycle completion
            logger.debug(
                f"CRIT-026: SSE generator finished for {search_id} "
                f"(heartbeats={heartbeat_count})"
            )
            await release_sse_connection(user_id)

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

@router.get("/v1/search/{search_id}/status", response_model=SearchStatusResponse)
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
    )


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
    """Return results of a background fetch or async search.

    A-04 AC5: Called by frontend when user clicks "Atualizar resultados" banner.
    GTM-ARCH-001 AC3: Also serves results from ARQ Worker (via Redis).
    Returns 404 if search_id not found or expired.
    """
    result = await get_background_results_async(search_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Resultados não encontrados ou expirados. Execute uma nova busca.",
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
        detail="Resultados não encontrados ou expirados. Execute uma nova busca.",
    )


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
        await _persist_results_to_redis(search_id, response)

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
# STORY-292 AC3: Async search via asyncio.create_task (replaces ARQ worker)
# ---------------------------------------------------------------------------

_ASYNC_SEARCH_TIMEOUT = 120  # AC9: Hard limit in seconds


async def _run_async_search(
    search_id: str,
    request: "BuscaRequest",
    user: dict,
    deps: "SimpleNamespace",
    tracker,
    state_machine,
) -> None:
    """STORY-292 AC3: Execute search pipeline as background task.

    Runs the full 7-stage SearchPipeline via asyncio.create_task() in the
    same worker process (no ARQ dependency).  Results are persisted to
    in-memory L1, Redis L2, and Supabase session update for retrieval via
    GET /buscar-results/{search_id}.

    AC7: On failure, state transitions to 'failed' and SSE emits error.
    AC9: 120s hard timeout with cleanup.
    """
    _start = sync_time.time()
    try:
        pipeline = SearchPipeline(deps)
        ctx = SearchContext(
            request=request,
            user=user,
            tracker=tracker,
            start_time=_start,
            quota_pre_consumed=True,  # Quota already consumed in POST
        )

        # AC9: 120s hard limit
        response = await asyncio.wait_for(
            pipeline.run(ctx),
            timeout=_ASYNC_SEARCH_TIMEOUT,
        )

        # Persist results: L1 (memory) + L2 (Redis) + L3 (Supabase session update)
        store_background_results(search_id, response)
        await _persist_results_to_redis(search_id, response)
        asyncio.create_task(_update_session_on_complete(search_id, user.get("id"), response))

        # Emit terminal SSE event
        if tracker:
            await tracker.emit_search_complete(search_id, response.total_filtrado)

        # CRIT-003: Complete state machine
        if state_machine:
            try:
                await state_machine.complete()
            except Exception:
                pass

        elapsed = round(sync_time.time() - _start, 1)
        logger.info(
            f"STORY-292: Async search completed for {search_id} in {elapsed}s "
            f"({response.total_filtrado} results)"
        )

    except asyncio.TimeoutError:
        elapsed = round(sync_time.time() - _start, 1)
        logger.error(f"STORY-292: Search timed out after {elapsed}s: {search_id}")
        sentry_sdk.capture_message(
            f"Async search timeout: {search_id}",
            level="warning",
        )
        if tracker:
            await tracker.emit_error(
                "Busca excedeu o tempo limite de 120 segundos. "
                "Tente com menos estados ou um período menor."
            )
        if state_machine:
            try:
                await state_machine.timeout()
            except Exception:
                pass

    except asyncio.CancelledError:
        logger.info(f"STORY-292: Async search cancelled for {search_id} (shutdown)")
        raise

    except Exception as e:
        elapsed = round(sync_time.time() - _start, 1)
        logger.error(
            f"STORY-292: Async search failed for {search_id} after {elapsed}s: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        sentry_sdk.capture_exception(e)
        if tracker:
            await tracker.emit_error(f"Erro no processamento: {type(e).__name__}")
        if state_machine:
            try:
                await state_machine.fail(
                    f"{type(e).__name__}: {str(e)[:200]}",
                    error_code="pipeline_error",
                )
            except Exception:
                pass

    finally:
        await remove_tracker(search_id)
        _active_background_tasks.pop(search_id, None)
        if state_machine:
            remove_state_machine(search_id)


async def _update_session_on_complete(
    search_id: str,
    user_id: str | None,
    response: Any,
) -> None:
    """STORY-292 AC6: Update search session with result metadata on completion.

    Fire-and-forget: errors are logged, never raised.
    """
    if not user_id:
        return
    try:
        from supabase_client import get_supabase, sb_execute
        from datetime import datetime, timezone

        db = get_supabase()
        if not db:
            return

        await sb_execute(
            db.table("search_sessions")
            .update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("search_id", search_id)
            .eq("user_id", user_id)
        )
    except Exception as e:
        logger.debug(f"STORY-292: Session update on complete failed (non-fatal): {e}")


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
    await tracker.emit("connecting", 3, "Iniciando busca...")

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
    # STORY-292: Async search — create_task in-process, return 202
    # -----------------------------------------------------------------------
    from config import get_feature_flag

    # AC14: X-Sync header forces synchronous mode (backward compat)
    force_sync = (
        raw_request.headers.get("x-sync", "").lower() == "true"
        or raw_request.query_params.get("sync", "").lower() == "true"
    )

    if get_feature_flag("SEARCH_ASYNC_ENABLED") and not force_sync:
        logger.info(f"STORY-292: Async mode — dispatching background task for {request.search_id}")

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

                    _allowed, _new_used, _remaining = await asyncio.to_thread(
                        _quota.check_and_increment_quota_atomic,
                        user["id"],
                        _quota_info.capabilities["max_requests_per_month"],
                    )
                    if not _allowed:
                        if tracker:
                            await tracker.emit_error("Suas buscas acabaram.")
                            await remove_tracker(request.search_id)
                        raise HTTPException(
                            status_code=403,
                            detail=(
                                f"Limite de {_quota_info.capabilities['max_requests_per_month']} "
                                f"buscas mensais atingido."
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
            logger.warning(f"STORY-292: Quota check failed, falling through to sync: {quota_err}")
            # Fall through to sync/cache-first path below
            force_sync = True

        if not force_sync:
            # AC3: Dispatch pipeline as asyncio.create_task (no ARQ dependency)
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

            # AC1+AC2: Return 202 Accepted with Location header
            num_ufs = len(request.ufs) if request.ufs else 1
            status_url = f"/v1/search/{request.search_id}/status"
            logger.info(f"STORY-292: Background task dispatched for {request.search_id} — returning 202")
            return StarletteJSONResponse(
                status_code=202,
                content={
                    "search_id": request.search_id,
                    "status": "queued",
                    "status_url": status_url,
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
                # GTM-STAB-008 AC6: elapsed_s tag (cache-first path)
                sentry_sdk.set_tag("elapsed_s", round(sync_time.time() - _search_start, 1))
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
            items = _convert_to_licitacao_items(ctx.licitacoes_filtradas)
            partial_response = BuscaResponse(
                licitacoes=items,
                total_encontrado=len(ctx.licitacoes_filtradas),
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
