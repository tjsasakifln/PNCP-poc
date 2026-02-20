"""CRIT-003: Explicit state machine for search lifecycle.

Defines the SearchState enum with valid transitions and a validator
that rejects invalid state changes with CRITICAL logging.

AC1: State machine with deterministic transitions.
AC3: Invalid transitions rejected with CRITICAL log.
AC4: Each state carries metadata (timestamp, duration, details).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SearchState(str, Enum):
    """Explicit search lifecycle states.

    AC1: Every search follows a deterministic path through these states.
    Terminal states: COMPLETED, FAILED, RATE_LIMITED, TIMED_OUT.
    """

    CREATED = "created"
    VALIDATING = "validating"
    FETCHING = "fetching"
    FILTERING = "filtering"
    ENRICHING = "enriching"
    GENERATING = "generating"
    PERSISTING = "persisting"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    TIMED_OUT = "timed_out"


# AC1: Valid transitions map — only these are allowed
VALID_TRANSITIONS: Dict[SearchState, set[SearchState]] = {
    SearchState.CREATED: {SearchState.VALIDATING, SearchState.FAILED},
    SearchState.VALIDATING: {SearchState.FETCHING, SearchState.FAILED, SearchState.RATE_LIMITED},
    SearchState.FETCHING: {SearchState.FILTERING, SearchState.FAILED, SearchState.TIMED_OUT},
    SearchState.FILTERING: {SearchState.ENRICHING, SearchState.FAILED},
    SearchState.ENRICHING: {SearchState.GENERATING, SearchState.FAILED},
    SearchState.GENERATING: {SearchState.PERSISTING, SearchState.FAILED},
    SearchState.PERSISTING: {SearchState.COMPLETED, SearchState.FAILED},
    # Terminal states have no valid outgoing transitions
    SearchState.COMPLETED: set(),
    SearchState.FAILED: set(),
    SearchState.RATE_LIMITED: set(),
    SearchState.TIMED_OUT: set(),
}

# States that represent a terminal condition
TERMINAL_STATES = {
    SearchState.COMPLETED,
    SearchState.FAILED,
    SearchState.RATE_LIMITED,
    SearchState.TIMED_OUT,
}

# Map pipeline stage names to SearchState for convenience
STAGE_TO_STATE: Dict[str, SearchState] = {
    "validate": SearchState.VALIDATING,
    "prepare": SearchState.VALIDATING,  # prepare is part of validation phase
    "execute": SearchState.FETCHING,
    "fetch": SearchState.FETCHING,
    "filter": SearchState.FILTERING,
    "enrich": SearchState.ENRICHING,
    "generate": SearchState.GENERATING,
    "persist": SearchState.PERSISTING,
}


@dataclass
class StateTransition:
    """AC4: Each transition carries metadata."""

    search_id: str
    from_state: Optional[SearchState]
    to_state: SearchState
    stage: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    duration_since_previous: Optional[float] = None


def validate_transition(
    from_state: Optional[SearchState],
    to_state: SearchState,
) -> bool:
    """AC3: Validate that a state transition is allowed.

    Returns True if valid, False and logs CRITICAL if invalid.
    """
    # Initial transition (None -> CREATED) is always valid
    if from_state is None:
        if to_state == SearchState.CREATED:
            return True
        logger.critical(
            f"CRIT-003: Invalid initial state: expected CREATED, got {to_state.value}"
        )
        return False

    # Check valid transitions map
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    if to_state in valid_targets:
        return True

    logger.critical(
        f"CRIT-003: Invalid state transition: {from_state.value} -> {to_state.value}. "
        f"Valid targets from {from_state.value}: {[s.value for s in valid_targets]}"
    )
    return False


def is_terminal(state: SearchState) -> bool:
    """Check if a state is terminal (no valid outgoing transitions)."""
    return state in TERMINAL_STATES
