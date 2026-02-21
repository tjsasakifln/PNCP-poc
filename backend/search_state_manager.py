"""CRIT-003: Search state manager — transition helpers and DB persistence.

Provides fire-and-forget state transition recording and query helpers.
All DB writes are non-blocking (asyncio.create_task) to avoid adding
latency to the pipeline.

AC2: Every transition persisted to DB.
AC5-AC6: Fire-and-forget INSERT to search_state_transitions.
AC7: Timeline query for /v1/search/{search_id}/timeline.
AC23: Structured logging on every transition.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from models.search_state import (
    SearchState,
    StateTransition,
    TERMINAL_STATES,
    validate_transition,
)

logger = logging.getLogger(__name__)


class SearchStateMachine:
    """Manages the state lifecycle of a single search execution.

    Thread-safe within a single asyncio event loop (one per search).
    """

    def __init__(self, search_id: str):
        self.search_id = search_id
        self._current_state: Optional[SearchState] = None
        self._last_transition_time: float = time.time()
        self._transitions: List[StateTransition] = []

    @property
    def current_state(self) -> Optional[SearchState]:
        return self._current_state

    @property
    def is_terminal(self) -> bool:
        return self._current_state in TERMINAL_STATES

    async def transition_to(
        self,
        to_state: SearchState,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Attempt a state transition. Returns True if successful.

        AC2: Persists to DB via fire-and-forget.
        AC3: Rejects invalid transitions with CRITICAL log.
        AC4: Carries metadata (timestamp, duration, details).
        AC23: Structured log on every transition.
        """
        if not validate_transition(self._current_state, to_state):
            return False

        now = time.time()
        duration_ms = int((now - self._last_transition_time) * 1000)

        transition = StateTransition(
            search_id=self.search_id,
            from_state=self._current_state,
            to_state=to_state,
            stage=stage,
            details=details or {},
            timestamp=now,
            duration_since_previous=duration_ms if self._current_state else None,
        )

        self._transitions.append(transition)
        prev_state = self._current_state
        self._current_state = to_state
        self._last_transition_time = now

        # AC23: Structured logging
        logger.info(
            f"CRIT-003: State transition: "
            f"{prev_state.value if prev_state else 'None'} -> {to_state.value}",
            extra={
                "search_id": self.search_id,
                "from_state": prev_state.value if prev_state else None,
                "to_state": to_state.value,
                "stage": stage,
                "duration_ms": duration_ms if prev_state else None,
            },
        )

        # AC22: Record time spent in previous state
        if prev_state and duration_ms is not None:
            try:
                from metrics import STATE_DURATION
                STATE_DURATION.labels(state=prev_state.value).observe(duration_ms / 1000.0)
            except Exception:
                pass

        # AC6: Fire-and-forget DB write
        asyncio.create_task(_persist_transition(transition))

        # Also update search_sessions.status and pipeline_stage
        asyncio.create_task(
            _update_session_state(self.search_id, to_state, stage)
        )

        return True

    async def fail(
        self,
        error_message: str,
        error_code: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> bool:
        """Transition to FAILED state with error details."""
        return await self.transition_to(
            SearchState.FAILED,
            stage=stage,
            details={"error_message": error_message, "error_code": error_code},
        )

    async def timeout(self, stage: Optional[str] = None) -> bool:
        """Transition to TIMED_OUT state."""
        return await self.transition_to(
            SearchState.TIMED_OUT,
            stage=stage,
            details={"reason": "Pipeline timeout exceeded"},
        )

    async def rate_limited(self, retry_after: int = 60) -> bool:
        """Transition to RATE_LIMITED state."""
        return await self.transition_to(
            SearchState.RATE_LIMITED,
            stage="validate",
            details={"retry_after": retry_after},
        )


# ---------------------------------------------------------------------------
# DB Persistence (fire-and-forget)
# ---------------------------------------------------------------------------

async def _persist_transition(transition: StateTransition) -> None:
    """AC6: Insert transition record into search_state_transitions table.

    Fire-and-forget — never raises, logs errors silently.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        row = {
            "search_id": transition.search_id,
            "from_state": transition.from_state.value if transition.from_state else None,
            "to_state": transition.to_state.value,
            "stage": transition.stage,
            "details": transition.details,
            "duration_since_previous_ms": (
                int(transition.duration_since_previous)
                if transition.duration_since_previous is not None
                else None
            ),
        }

        sb.table("search_state_transitions").insert(row).execute()
    except Exception as e:
        logger.warning(f"CRIT-003: Failed to persist state transition: {e}")


async def _update_session_state(
    search_id: str,
    state: SearchState,
    stage: Optional[str] = None,
) -> None:
    """Update search_sessions.status and pipeline_stage to match state machine.

    Maps SearchState to session status values (CRIT-002 schema).
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Map state machine states to session status values
        status_map = {
            SearchState.CREATED: "created",
            SearchState.VALIDATING: "processing",
            SearchState.FETCHING: "processing",
            SearchState.FILTERING: "processing",
            SearchState.ENRICHING: "processing",
            SearchState.GENERATING: "processing",
            SearchState.PERSISTING: "processing",
            SearchState.COMPLETED: "completed",
            SearchState.FAILED: "failed",
            SearchState.RATE_LIMITED: "failed",
            SearchState.TIMED_OUT: "timed_out",
        }

        update_data: Dict[str, Any] = {
            "status": status_map.get(state, "processing"),
        }
        if stage:
            update_data["pipeline_stage"] = stage

        if state in TERMINAL_STATES:
            from datetime import datetime, timezone
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()

        (
            sb.table("search_sessions")
            .update(update_data)
            .eq("search_id", search_id)
            .execute()
        )
    except Exception as e:
        logger.warning(f"CRIT-003: Failed to update session state: {e}")


# ---------------------------------------------------------------------------
# Query Helpers
# ---------------------------------------------------------------------------

async def get_timeline(search_id: str) -> List[Dict[str, Any]]:
    """AC7: Return all transitions for a search_id, ordered chronologically."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        result = (
            sb.table("search_state_transitions")
            .select("*")
            .eq("search_id", search_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning(f"CRIT-003: Failed to get timeline for {search_id}: {e}")
        return []


async def get_current_state(search_id: str) -> Optional[Dict[str, Any]]:
    """Get the current (latest) state for a search from the DB.

    AC9: Used by SSE reconnection to derive current state from persistent storage.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        result = (
            sb.table("search_state_transitions")
            .select("*")
            .eq("search_id", search_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.warning(f"CRIT-003: Failed to get current state for {search_id}: {e}")
        return None


async def get_search_status(search_id: str) -> Optional[Dict[str, Any]]:
    """AC11: Build status response for polling endpoint.

    Combines search_sessions data with latest state transition.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Get session data
        session_result = (
            sb.table("search_sessions")
            .select("*")
            .eq("search_id", search_id)
            .limit(1)
            .execute()
        )

        if not session_result.data:
            return None

        session = session_result.data[0]

        # Get latest transition for detail
        latest_state = await get_current_state(search_id)

        # Calculate elapsed time
        started_at = session.get("started_at")
        elapsed_ms = None
        if started_at:
            from datetime import datetime, timezone
            try:
                start_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                elapsed_ms = int((datetime.now(timezone.utc) - start_dt).total_seconds() * 1000)
            except (ValueError, TypeError):
                pass

        return {
            "search_id": search_id,
            "status": latest_state["to_state"] if latest_state else session.get("status", "unknown"),
            "progress": _estimate_progress(latest_state["to_state"] if latest_state else session.get("status")),
            "stage": session.get("pipeline_stage"),
            "started_at": started_at,
            "elapsed_ms": elapsed_ms,
            "ufs_completed": session.get("ufs_completed"),
            "ufs_total": session.get("ufs_total"),
            "ufs_failed": session.get("ufs_failed"),
            "llm_status": session.get("llm_status", "pending"),
            "excel_status": session.get("excel_status", "pending"),
            "error_message": session.get("error_message"),
            "error_code": session.get("error_code"),
        }
    except Exception as e:
        logger.warning(f"CRIT-003: Failed to get search status for {search_id}: {e}")
        return None


def _estimate_progress(state: Optional[str]) -> int:
    """Estimate progress percentage from state name."""
    progress_map = {
        "created": 0,
        "validating": 5,
        "fetching": 30,
        "filtering": 60,
        "enriching": 70,
        "generating": 85,
        "persisting": 95,
        "completed": 100,
        "failed": -1,
        "rate_limited": -1,
        "timed_out": -1,
    }
    return progress_map.get(state or "", 0)


# ---------------------------------------------------------------------------
# Startup Recovery (AC16-AC18)
# ---------------------------------------------------------------------------

async def recover_stale_searches(max_age_minutes: int = 10) -> int:
    """AC16-AC18: On server startup, mark stale processing searches.

    - Searches processing > max_age_minutes: mark as timed_out (AC17)
    - Searches processing < max_age_minutes: mark as failed with retry message (AC18)

    CRIT-011 AC6: Handles missing search_id column gracefully (backward compat).

    Returns number of recovered sessions.
    """
    try:
        from supabase_client import get_supabase
        from datetime import datetime, timezone, timedelta
        sb = get_supabase()

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=max_age_minutes)

        # CRIT-011 AC6: Try with all columns first, fall back gracefully
        # Production search_sessions may lack: search_id, status, started_at
        has_search_id_column = True
        try:
            result = (
                sb.table("search_sessions")
                .select("id, search_id, status, started_at")
                .in_("status", ["created", "processing"])
                .execute()
            )
        except Exception as col_err:
            err_str = str(col_err)
            if "42703" in err_str:
                # One or more columns don't exist — try minimal query
                logger.warning(
                    "Startup recovery: required columns missing (%s), "
                    "attempting created_at-based recovery",
                    err_str[:120],
                )
                has_search_id_column = False
                try:
                    # Fallback: use only columns we know exist (id, created_at)
                    result = (
                        sb.table("search_sessions")
                        .select("id, created_at")
                        .lt("created_at", cutoff.isoformat())
                        .execute()
                    )
                except Exception:
                    logger.warning(
                        "Startup recovery: fallback query also failed, "
                        "skipping recovery (apply CRIT-011 migration)"
                    )
                    return 0
            else:
                raise

        if not result.data:
            logger.info("Startup recovery: no stale searches found")
            return 0

        timed_out_count = 0
        failed_count = 0

        for session in result.data:
            # Use started_at if available, otherwise created_at
            time_str = session.get("started_at") or session.get("created_at")
            if not time_str:
                continue

            try:
                session_time = datetime.fromisoformat(
                    time_str.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                continue

            session_id = session["id"]

            # Build update dict — only include columns that exist
            if session_time < cutoff:
                # AC17: Old search — timed_out
                update_data: dict = {}
                # Only set status/error columns if they exist (may not in production)
                try:
                    sb.table("search_sessions").update({
                        "status": "timed_out",
                        "error_message": "Server restart during processing",
                        "error_code": "timeout",
                        "completed_at": now.isoformat(),
                    }).eq("id", session_id).execute()
                except Exception:
                    # Columns may not exist — just delete the stale session
                    try:
                        sb.table("search_sessions").delete().eq("id", session_id).execute()
                    except Exception:
                        pass
                timed_out_count += 1

                sid = session.get("search_id") if has_search_id_column else None
                if sid:
                    await _persist_transition(StateTransition(
                        search_id=sid,
                        from_state=SearchState.FETCHING,
                        to_state=SearchState.TIMED_OUT,
                        stage="recovery",
                        details={"reason": "Server restart during processing"},
                    ))
            else:
                # AC18: Recent search — failed with retry
                try:
                    sb.table("search_sessions").update({
                        "status": "failed",
                        "error_message": "Server restart — retry recommended",
                        "error_code": "server_restart",
                        "completed_at": now.isoformat(),
                    }).eq("id", session_id).execute()
                except Exception:
                    pass  # Columns may not exist — leave session as-is
                failed_count += 1

                sid = session.get("search_id") if has_search_id_column else None
                if sid:
                    await _persist_transition(StateTransition(
                        search_id=sid,
                        from_state=SearchState.FETCHING,
                        to_state=SearchState.FAILED,
                        stage="recovery",
                        details={"reason": "Server restart — retry recommended"},
                    ))

        total = timed_out_count + failed_count
        if total > 0:
            logger.info(
                f"Startup recovery: marked {total} stale sessions "
                f"({timed_out_count} timed_out, {failed_count} failed)"
            )
        else:
            logger.info("Startup recovery: no stale searches found")
        return total

    except Exception as e:
        err_str = str(e)
        if "42703" in err_str:
            logger.warning(
                "Startup recovery skipped: missing columns in search_sessions (%s)",
                err_str[:120],
            )
        else:
            logger.error(f"Startup recovery error: {e}", exc_info=True)
        return 0


# ---------------------------------------------------------------------------
# Active state machine registry (in-memory)
# ---------------------------------------------------------------------------

_active_machines: Dict[str, SearchStateMachine] = {}


async def create_state_machine(search_id: str) -> SearchStateMachine:
    """Create and register a state machine for a search."""
    machine = SearchStateMachine(search_id)
    await machine.transition_to(SearchState.CREATED, stage="init")
    _active_machines[search_id] = machine
    return machine


def get_state_machine(search_id: str) -> Optional[SearchStateMachine]:
    """Get an active state machine by search_id."""
    return _active_machines.get(search_id)


def remove_state_machine(search_id: str) -> None:
    """Remove a state machine after search completes."""
    _active_machines.pop(search_id, None)
