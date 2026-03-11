"""
DEBT-115 AC5: SSE Progress Stream endpoint.

Extracted from routes/search.py to reduce module complexity.
Contains the GET /buscar-progress/{search_id} SSE endpoint.
"""

import asyncio
import json as _json
import os
import uuid as _uuid

import sentry_sdk

from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import StreamingResponse

from auth import require_auth
from log_sanitizer import get_sanitized_logger
from progress import create_tracker, get_tracker, remove_tracker, get_replay_events, is_search_terminal
from rate_limiter import (
    require_rate_limit,
    acquire_sse_connection,
    release_sse_connection,
    SSE_RECONNECT_RATE_LIMIT,
    SSE_RECONNECT_WINDOW_SECONDS,
    _flexible_limiter,
)
from redis_pool import get_redis_pool, get_sse_redis_pool
from search_state_manager import (
    get_search_status,
    get_current_state,
    get_state_machine,
)

logger = get_sanitized_logger(__name__)

router = APIRouter(tags=["search"])

# CRIT-012 AC2: Heartbeat interval reduced from 30s to 15s
# STORY-365 AC5: Configurable via SSE_HEARTBEAT_INTERVAL_S env var
_SSE_HEARTBEAT_INTERVAL = float(os.environ.get("SSE_HEARTBEAT_INTERVAL_S", "15"))
_SSE_WAIT_HEARTBEAT_EVERY = 10  # Every 10 iterations of 0.5s = 5s

# CRIT-026-ROOT: Polled XREAD constants (replacing XREAD BLOCK).
# Non-blocking XREAD polls every _SSE_POLL_INTERVAL seconds.
# Heartbeat SSE comment sent every _SSE_POLLS_PER_HEARTBEAT empty polls.
_SSE_POLL_INTERVAL = 1.0   # seconds between non-blocking polls
_SSE_POLLS_PER_HEARTBEAT = 15  # heartbeat every ~15s (15 polls * 1s)


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
    # STORY-299 AC2: Track total SSE connection attempts for SLI
    try:
        from metrics import SSE_CONNECTIONS_TOTAL
        SSE_CONNECTIONS_TOTAL.inc()
    except Exception as e:
        logger.debug(f"SSE metrics unavailable: {e}")

    # HARDEN-020 AC1+AC2: Rate limit SSE reconnections (10/60s per user)
    user_id = user.get("id", "unknown")
    allowed, retry_after = await _flexible_limiter.check_rate_limit(
        f"sse_reconnect:user:{user_id}",
        SSE_RECONNECT_RATE_LIMIT,
        SSE_RECONNECT_WINDOW_SECONDS,
    )
    if not allowed:
        logger.warning(
            "HARDEN-020: SSE reconnect rate limit exceeded user_id=%s retry_after=%ds",
            user_id,
            retry_after,
        )
        raise HTTPException(
            status_code=429,
            detail={
                "detail": f"Limite de reconexões SSE excedido. Tente novamente em {retry_after} segundos.",
                "retry_after_seconds": retry_after,
                "correlation_id": str(_uuid.uuid4()),
            },
            headers={"Retry-After": str(retry_after)},
        )

    # GTM-GO-002 AC6: Enforce SSE connection limit per user
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

    # STORY-297 AC3: Read Last-Event-ID for reconnection replay
    last_event_id_raw = request.headers.get("Last-Event-ID") or request.query_params.get("last_event_id")
    last_event_id: int = 0
    if last_event_id_raw:
        try:
            last_event_id = int(last_event_id_raw)
        except (ValueError, TypeError):
            last_event_id = 0
        logger.debug(f"STORY-297: SSE reconnect for {search_id} with Last-Event-ID={last_event_id}")

    async def event_generator():
        # GTM-GO-002 AC6: Release SSE slot when generator finishes
        heartbeat_count = 0
        # STORY-297: Track event IDs for SSE id: field
        _sse_event_counter = last_event_id
        try:
            # STORY-297 AC3+AC4: Replay events after Last-Event-ID on reconnection
            if last_event_id > 0:
                # AC4: If search already completed, replay + send terminal immediately
                terminal_event = await is_search_terminal(search_id)
                if terminal_event:
                    replay_events = await get_replay_events(search_id, last_event_id)
                    for eid, edata in replay_events:
                        yield f"id: {eid}\ndata: {_json.dumps(edata)}\n\n"
                    # If terminal wasn't in replay (already seen), send it now
                    if not replay_events or replay_events[-1][1].get("stage") != terminal_event.get("stage"):
                        # Generate a synthetic ID beyond replay
                        final_id = replay_events[-1][0] + 1 if replay_events else last_event_id + 1
                        yield f"id: {final_id}\ndata: {_json.dumps(terminal_event)}\n\n"
                    logger.debug(
                        f"STORY-297 AC4: Replayed {len(replay_events) if replay_events else 0} events "
                        f"+ terminal for completed search {search_id}"
                    )
                    return

                # AC3: Search still in progress — replay missed events then continue streaming
                replay_events = await get_replay_events(search_id, last_event_id)
                if replay_events:
                    for eid, edata in replay_events:
                        _sse_event_counter = eid
                        yield f"id: {eid}\ndata: {_json.dumps(edata)}\n\n"
                    logger.debug(
                        f"STORY-297 AC3: Replayed {len(replay_events)} events for {search_id} "
                        f"(after ID {last_event_id})"
                    )
                    # Check if replay included terminal event
                    if replay_events[-1][1].get("stage") in (
                        "complete", "degraded", "error", "refresh_available", "search_complete", "shutdown",
                    ):
                        return

            # CRIT-012 AC1: Wait for tracker with SSE keepalive comments every 5s
            # Moved inside generator so heartbeats flow before first real event
            tracker = None
            for i in range(60):  # 60 * 0.5s = 30s
                # HARDEN-012 AC1: Check if client disconnected
                if await request.is_disconnected():
                    from metrics import SSE_DISCONNECTS_TOTAL
                    SSE_DISCONNECTS_TOTAL.inc()
                    logger.debug(f"HARDEN-012: Client disconnected during wait phase for {search_id}")
                    return
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
                await asyncio.sleep(0.5)

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
                _sse_event_counter += 1
                yield f"id: {_sse_event_counter}\ndata: {_json.dumps({'stage': state_val, 'progress': progress, 'message': f'Estado atual: {state_val}'})}\n\n"
                # If terminal, we're done
                if state_val in ("completed", "failed", "timed_out", "rate_limited"):
                    return
                # Otherwise fall through to wait for more events — but we have no tracker
                # so we can't stream further. Just return.
                return

            # STORY-276: Try Redis Streams first, fallback to in-memory queue
            _use_streams = tracker._use_redis
            _redis = None
            _supabase_fallback = False  # CRIT-048 AC4: track Redis timeout for Supabase polling fallback
            if _use_streams:
                # CRIT-048 AC5: Use SSE-specific Redis pool with 60s socket timeout
                _redis = await get_sse_redis_pool()
                if not _redis:
                    _use_streams = False
                    logger.warning(
                        f"Redis unavailable for SSE {search_id}, falling back to queue"
                    )

            if _use_streams:
                # CRIT-026-ROOT: Non-blocking polled XREAD replaces XREAD BLOCK.
                _stream_key = f"smartlic:progress:{search_id}:stream"
                _last_id = "0"  # AC2: id=0 reads ALL history since beginning
                _polls_since_heartbeat = 0
                _consecutive_errors = 0
                _MAX_CONSECUTIVE_ERRORS = 5  # circuit breaker for Redis failures
                logger.debug(f"SSE using Redis Streams (polled) for {search_id}")

                while True:
                    # HARDEN-012 AC1: Check if client disconnected
                    if await request.is_disconnected():
                        from metrics import SSE_DISCONNECTS_TOTAL
                        SSE_DISCONNECTS_TOTAL.inc()
                        logger.debug(f"HARDEN-012: Client disconnected during Redis streaming for {search_id}")
                        return

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
                            await asyncio.sleep(_SSE_POLL_INTERVAL)
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

                                # STORY-297 AC1: Include SSE event id
                                _sse_event_counter += 1
                                yield f"id: {_sse_event_counter}\ndata: {_json.dumps(event_data)}\n\n"

                                if fields["stage"] in (
                                    "complete", "degraded", "error",
                                    "refresh_available", "search_complete", "shutdown",
                                ):
                                    return

                    except asyncio.CancelledError:
                        from metrics import SSE_CONNECTION_ERRORS
                        SSE_CONNECTION_ERRORS.labels(
                            error_type="cancelled", phase="streaming"
                        ).inc()
                        break

                    except (TimeoutError, ConnectionError) as redis_timeout_err:
                        # CRIT-048 AC3: Redis timeout/connection error
                        from metrics import SSE_CONNECTION_ERRORS
                        SSE_CONNECTION_ERRORS.labels(
                            error_type="redis_timeout", phase="streaming"
                        ).inc()
                        logger.error(
                            f"CRIT-048 AC3: Redis timeout for SSE {search_id}: "
                            f"{type(redis_timeout_err).__name__}: {redis_timeout_err}"
                        )
                        # Emit non-terminal informational event before switching transport
                        _sse_event_counter += 1
                        yield (
                            f"id: {_sse_event_counter}\n"
                            f"data: {_json.dumps({'stage': 'connecting', 'progress': -1, 'message': 'Reconectando ao servidor de progresso...'})}\n\n"
                        )
                        _supabase_fallback = True
                        _use_streams = False
                        break

                    except Exception as redis_err:
                        # CRIT-026-ROOT: Circuit breaker for transient Redis errors.
                        _consecutive_errors += 1
                        logger.warning(
                            f"CRIT-026: Redis read error #{_consecutive_errors} "
                            f"for {search_id}: {type(redis_err).__name__}: {redis_err}"
                        )
                        if _consecutive_errors >= _MAX_CONSECUTIVE_ERRORS:
                            logger.error(
                                f"CRIT-026: Circuit breaker open for {search_id} "
                                f"after {_consecutive_errors} consecutive Redis errors, "
                                f"falling back to Supabase polling"
                            )
                            # CRIT-048 AC4: Fall through to Supabase polling
                            _use_streams = False
                            _supabase_fallback = True
                            break
                        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                        _backoff = min(2 ** (_consecutive_errors - 1), 16)
                        await asyncio.sleep(_backoff)

            # CRIT-048 AC4: Supabase polling fallback when Redis is unavailable
            if _supabase_fallback:
                logger.info(f"CRIT-048 AC4: Supabase polling fallback for {search_id}")
                _last_polled_state = None
                _max_polls = 60  # 60 * 5s = 5 minutes max
                for _poll_idx in range(_max_polls):
                    # HARDEN-012 AC1: Check if client disconnected
                    if await request.is_disconnected():
                        from metrics import SSE_DISCONNECTS_TOTAL
                        SSE_DISCONNECTS_TOTAL.inc()
                        logger.debug(f"HARDEN-012: Client disconnected during Supabase fallback for {search_id}")
                        return

                    try:
                        _sb_status = await get_search_status(search_id)
                        if _sb_status:
                            _current_status = _sb_status.get("status", "unknown")
                            if _current_status != _last_polled_state:
                                _last_polled_state = _current_status
                                # Map DB states to SSE stages
                                _stage = _current_status
                                if _current_status == "completed":
                                    _stage = "complete"
                                elif _current_status in ("failed", "timed_out", "rate_limited"):
                                    _stage = "error"
                                _sse_event_counter += 1
                                yield (
                                    f"id: {_sse_event_counter}\n"
                                    f"data: {_json.dumps({'stage': _stage, 'progress': _sb_status.get('progress', 0), 'message': f'Acompanhamento: {_current_status}', 'detail': {'transport': 'supabase_fallback'}})}\n\n"
                                )
                                if _stage in (
                                    "complete", "error", "degraded",
                                    "refresh_available", "search_complete", "shutdown",
                                ):
                                    return
                    except Exception as _sb_err:
                        logger.warning(
                            f"CRIT-048: Supabase poll error for {search_id}: {_sb_err}"
                        )
                    heartbeat_count += 1
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(5.0)
                # Max polls exhausted — emit terminal error
                _sse_event_counter += 1
                yield (
                    f"id: {_sse_event_counter}\n"
                    f"data: {_json.dumps({'stage': 'error', 'progress': -1, 'message': 'Timeout no acompanhamento da busca'})}\n\n"
                )

            elif not _use_streams:
                # AC3: In-memory mode — fallback asyncio.Queue (no Redis)
                logger.debug(f"SSE using in-memory queue for {search_id}")
                while True:
                    # HARDEN-012 AC1: Check if client disconnected
                    if await request.is_disconnected():
                        from metrics import SSE_DISCONNECTS_TOTAL
                        SSE_DISCONNECTS_TOTAL.inc()
                        logger.debug(f"HARDEN-012: Client disconnected during in-memory streaming for {search_id}")
                        break

                    try:
                        # CRIT-012 AC2: Heartbeat interval as timeout
                        event = await asyncio.wait_for(
                            tracker.queue.get(),
                            timeout=_SSE_HEARTBEAT_INTERVAL,
                        )
                        # STORY-297 AC1: Include SSE event id
                        _sse_event_counter += 1
                        yield f"id: {_sse_event_counter}\ndata: {_json.dumps(event.to_dict())}\n\n"

                        if event.stage in (
                            "complete", "degraded", "error",
                            "refresh_available", "search_complete", "shutdown",
                        ):
                            break

                    except asyncio.TimeoutError:
                        heartbeat_count += 1
                        yield ": heartbeat\n\n"
                        logger.debug(
                            f"CRIT-012: Heartbeat #{heartbeat_count} "
                            f"for {search_id} (in-memory)"
                        )

                    except asyncio.CancelledError:
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
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
