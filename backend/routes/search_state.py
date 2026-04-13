"""
DEBT-115 AC6: Search state management — background results, async search, persistence.

Extracted from routes/search.py to reduce module complexity.
Contains background results storage, persistence helpers, async search execution,
and trial paywall logic.
"""

import asyncio
import time as sync_time
from typing import Any, Dict, Optional

import sentry_sdk

from types import SimpleNamespace

from log_sanitizer import get_sanitized_logger
from progress import get_tracker, remove_tracker
from redis_pool import get_redis_pool
from schemas import BuscaRequest, BuscaResponse
from search_context import SearchContext
from search_pipeline import SearchPipeline
from search_state_manager import (
    remove_state_machine,
)

logger = get_sanitized_logger(__name__)


# ---------------------------------------------------------------------------
# A-04 + STORY-294: Background fetch results (in-memory L1 + Redis L2)
# ---------------------------------------------------------------------------
_background_results: Dict[str, Dict[str, Any]] = {}
_RESULTS_TTL = 3600  # 1 hour (in-memory) — STORY-362 AC1
_active_background_tasks: Dict[str, asyncio.Task] = {}
_MAX_BACKGROUND_TASKS = 5  # Budget: max concurrent background fetches
_MAX_BACKGROUND_RESULTS = 200  # HARDEN-013 AC1: cap in-memory results dict

# STORY-294 AC2: Redis key prefix and TTL for cross-worker result sharing
_RESULTS_REDIS_PREFIX = "smartlic:results:"


def get_background_results_count() -> int:
    """HARDEN-024 AC5: Return number of background results in memory."""
    return len(_background_results)


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
    """Store results in in-memory L1 cache.

    HARDEN-013: Evicts oldest entries when dict exceeds _MAX_BACKGROUND_RESULTS.
    """
    # HARDEN-013 AC2: evict oldest entries when at capacity
    if len(_background_results) >= _MAX_BACKGROUND_RESULTS and search_id not in _background_results:
        oldest_id = min(_background_results, key=lambda k: _background_results[k].get("stored_at", 0))
        _background_results.pop(oldest_id, None)
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


async def _persist_results_to_supabase(
    search_id: str, user_id: str, response: Any
) -> None:
    """STORY-362 AC5: Persist results to Supabase L3 for long-term access.

    Fire-and-forget: errors are logged, never raised.
    Uses service_role so RLS INSERT is allowed.
    """
    import json as _json
    from datetime import datetime, timezone, timedelta

    try:
        from supabase_client import get_supabase, sb_execute
        from config import RESULTS_SUPABASE_TTL_HOURS

        db = get_supabase()
        if not db:
            return

        # Serialize response
        if hasattr(response, "model_dump"):
            data = response.model_dump(mode="json")
        elif hasattr(response, "dict"):
            data = response.dict()
        elif isinstance(response, dict):
            data = response
        else:
            return

        sector = data.get("setor", "")
        ufs = data.get("ufs", [])
        total_filtered = data.get("total_filtrado", 0)
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=RESULTS_SUPABASE_TTL_HOURS)
        ).isoformat()

        await sb_execute(
            db.table("search_results_store").upsert({
                "search_id": search_id,
                "user_id": user_id,
                "results": _json.loads(_json.dumps(data, default=str)),
                "sector": sector,
                "ufs": ufs,
                "total_filtered": total_filtered,
                "expires_at": expires_at,
            })
        )
        logger.debug(f"STORY-362: Results persisted to Supabase L3: {search_id}")

    except Exception as e:
        logger.warning(f"STORY-362: Failed to persist results to Supabase L3: {e}")


async def _safe_persist_results(search_id: str, user_id: str, response: Any) -> None:
    """HARDEN-005 AC1/AC2/AC3: Retry wrapper for _persist_results_to_supabase.

    Retries up to 3 times with exponential backoff. On final failure,
    captures exception to Sentry and increments persist_failures metric.
    """
    from metrics import PERSIST_FAILURES

    for attempt in range(3):
        try:
            await _persist_results_to_supabase(search_id, user_id, response)
            return
        except Exception as e:
            if attempt == 2:
                sentry_sdk.capture_exception(e)
                PERSIST_FAILURES.labels(store="supabase").inc()
                logger.error(
                    f"HARDEN-005: Persist failed after 3 attempts for {search_id}: {e}"
                )
            else:
                await asyncio.sleep(2 ** attempt)


def _persist_done_callback(task: asyncio.Task) -> None:
    """HARDEN-005 AC4: Capture unhandled exceptions from fire-and-forget tasks."""
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        sentry_sdk.capture_exception(exc)
        logger.error(f"HARDEN-005: Unhandled exception in persist task: {exc}")


async def _get_results_from_supabase(search_id: str) -> Optional[Dict[str, Any]]:
    """STORY-362 AC6: Read results from Supabase L3 (long-term persistence)."""
    from datetime import datetime, timezone

    try:
        from supabase_client import get_supabase, sb_execute

        db = get_supabase()
        if not db:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        result = await sb_execute(
            db.table("search_results_store")
            .select("results")
            .eq("search_id", search_id)
            .gt("expires_at", now_iso)
            .limit(1)
        )

        if result and result.data and len(result.data) > 0:
            logger.debug(f"STORY-362: Results retrieved from Supabase L3: {search_id}")
            return result.data[0]["results"]

    except Exception as e:
        logger.warning(f"STORY-362: Failed to read results from Supabase L3: {e}")

    return None


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
    """Retrieve search results: L1 (memory) → L2 (Redis) → ARQ → L3 (Supabase).

    STORY-294 AC5: Cross-worker result retrieval via Redis.
    STORY-362 AC6: Supabase L3 fallback for long-term persistence.
    """
    # L1: Check in-memory first (same worker — fast path)
    sync_result = get_background_results(search_id)
    if sync_result:
        return sync_result

    # L2: Check Redis (cross-worker — STORY-294)
    redis_result = await _get_results_from_redis(search_id)
    if redis_result:
        return redis_result

    # ARQ: Check ARQ Worker results (job_queue)
    from job_queue import get_job_result
    arq_result = await get_job_result(search_id, "search_result")
    if arq_result:
        return arq_result

    # L3: Check Supabase (long-term persistence — STORY-362 AC6)
    supabase_result = await _get_results_from_supabase(search_id)
    if supabase_result:
        return supabase_result

    return None


# ---------------------------------------------------------------------------
# Session update helpers
# ---------------------------------------------------------------------------

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
# Trial paywall
# ---------------------------------------------------------------------------

def _apply_trial_paywall(response: BuscaResponse, user: dict) -> BuscaResponse:
    """STORY-320 AC3: Truncate results for trial users in limited_access phase.

    If trial paywall is active and user is in limited_access phase:
    - Truncate licitacoes to TRIAL_PAYWALL_MAX_RESULTS
    - Set paywall_applied=True
    - Set total_before_paywall to original count
    """
    from config import get_feature_flag, TRIAL_PAYWALL_MAX_RESULTS
    from quota import get_trial_phase

    if not get_feature_flag("TRIAL_PAYWALL_ENABLED"):
        return response

    user_id = user.get("id")
    if not user_id:
        return response

    try:
        phase_info = get_trial_phase(user_id)
    except Exception as e:
        logger.warning(f"STORY-320: trial phase check failed, skipping paywall: {e}")
        return response

    if phase_info["phase"] != "limited_access":
        return response

    total_results = len(response.licitacoes)
    if total_results <= TRIAL_PAYWALL_MAX_RESULTS:
        return response

    response.total_before_paywall = total_results
    response.licitacoes = response.licitacoes[:TRIAL_PAYWALL_MAX_RESULTS]
    response.paywall_applied = True

    # Update summary count to reflect visible results
    response.resumo.total_oportunidades = TRIAL_PAYWALL_MAX_RESULTS
    logger.info(
        f"STORY-320: Paywall applied for user {user_id[:8]}... "
        f"({total_results} → {TRIAL_PAYWALL_MAX_RESULTS} results)"
    )

    return response


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
        # HARDEN-005: Retry-wrapped L3 persist with done_callback
        _persist_task = asyncio.create_task(_safe_persist_results(search_id, user.get("id", ""), response))
        _persist_task.add_done_callback(_persist_done_callback)

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

_ASYNC_SEARCH_TIMEOUT = 240  # AC9: Hard limit — raised from 120s to accommodate tamanhoPagina=50


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

        # STORY-320 AC3: Apply trial paywall truncation
        response = _apply_trial_paywall(response, user)

        # Persist results: L1 (memory) + L2 (Redis) + L3 (Supabase)
        store_background_results(search_id, response)
        await _persist_results_to_redis(search_id, response)
        # HARDEN-005: Retry-wrapped L3 persist with done_callback
        _persist_task = asyncio.create_task(_safe_persist_results(search_id, user.get("id", ""), response))
        _persist_task.add_done_callback(_persist_done_callback)
        asyncio.create_task(_update_session_on_complete(search_id, user.get("id"), response))

        # Emit terminal SSE event
        if tracker:
            await tracker.emit_search_complete(search_id, response.total_filtrado)

        # CRIT-003: Complete state machine
        if state_machine:
            try:
                await state_machine.complete()
            except Exception as e:
                logger.warning(f"State machine complete() failed: {e}")

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
                f"Busca excedeu o tempo limite de {_ASYNC_SEARCH_TIMEOUT} segundos. "
                "Tente novamente em alguns minutos."
            )
        if state_machine:
            try:
                await state_machine.timeout()
            except Exception as e:
                logger.warning(f"State machine timeout() failed: {e}")

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
            except Exception as sm_err:
                logger.warning(f"State machine fail() failed: {sm_err}")

    finally:
        # Release concurrent search slot to prevent slot leak (was missing — 3 crashes = user blocked 10min)
        try:
            from job_queue import release_search_slot
            user_id = user.get("id", "")
            if user_id:
                await release_search_slot(user_id, search_id)
        except Exception as slot_err:
            logger.debug(f"release_search_slot in finally failed (non-fatal): {slot_err}")
        await remove_tracker(search_id)
        _active_background_tasks.pop(search_id, None)
        if state_machine:
            remove_state_machine(search_id)
