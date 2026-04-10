"""STORY-416: Regression tests for the segregated Supabase circuit breakers.

The production incident on 2026-04-10 (19-24 events across pipeline,
analytics, sessions and trial emails) was amplified by a single global
``supabase_cb`` that tripped whenever one hot path got slow, starving
every other endpoint that shared the same ``sb_execute`` wrapper.

The fix introduces per-category circuit breakers (read/write/rpc) and a
hybrid trip mode: OPEN when either the sliding-window failure rate
exceeds the threshold **or** the consecutive-failure streak does.
Recovery drops ``trial_calls`` from 3 → 2 so a recovered upstream flows
again faster.

These tests exercise the CB in isolation — no Supabase, no FastAPI —
because the goal is to pin the state machine behaviour, not the
integration.
"""

from __future__ import annotations

import pytest

from supabase_client import (
    SupabaseCircuitBreaker,
    get_cb,
    read_cb,
    reset_all_circuit_breakers,
    rpc_cb,
    supabase_cb,
    write_cb,
)


@pytest.fixture(autouse=True)
def _reset_all_cbs() -> None:
    """Make sure global CB state does not leak between tests."""
    read_cb.reset()
    write_cb.reset()
    rpc_cb.reset()
    supabase_cb.reset()


# ---------------------------------------------------------------------------
# State machine — consecutive streak triggers OPEN independently of rate
# ---------------------------------------------------------------------------


def test_consecutive_streak_opens_before_window_fills() -> None:
    cb = SupabaseCircuitBreaker(
        window_size=10,
        failure_rate_threshold=0.9,  # intentionally high so rate never trips
        cooldown_seconds=60.0,
        trial_calls_max=2,
        consecutive_failures_threshold=3,
        name="test",
    )
    cb._record_failure(RuntimeError("boom"))
    cb._record_failure(RuntimeError("boom"))
    assert cb.state == "CLOSED", "streak should not trip before threshold"
    cb._record_failure(RuntimeError("boom"))
    assert cb.state == "OPEN", (
        "STORY-416: consecutive streak must open the CB on the Nth failure"
    )


def test_success_resets_streak_but_not_window() -> None:
    cb = SupabaseCircuitBreaker(
        window_size=10,
        failure_rate_threshold=0.99,
        cooldown_seconds=60.0,
        trial_calls_max=2,
        consecutive_failures_threshold=3,
        name="test",
    )
    cb._record_failure(RuntimeError("boom"))
    cb._record_failure(RuntimeError("boom"))
    cb._record_success()  # resets streak
    cb._record_failure(RuntimeError("boom"))
    cb._record_failure(RuntimeError("boom"))
    assert cb.state == "CLOSED", (
        "successes must reset the streak so only 2 consecutive fails do NOT trip"
    )


def test_rate_trip_still_works_when_streak_disabled() -> None:
    cb = SupabaseCircuitBreaker(
        window_size=4,
        failure_rate_threshold=0.5,
        cooldown_seconds=60.0,
        trial_calls_max=2,
        consecutive_failures_threshold=None,  # no streak — legacy mode
        name="test",
    )
    cb._record_success()
    cb._record_success()
    cb._record_failure(RuntimeError("boom"))
    cb._record_failure(RuntimeError("boom"))
    assert cb.state == "OPEN", "50% rate over full window must trip in legacy mode"


# ---------------------------------------------------------------------------
# Segregation — failures in one category must NOT open the others
# ---------------------------------------------------------------------------


def test_read_failures_do_not_open_write_cb() -> None:
    """This is the exact cascade mode from the 2026-04-10 incident."""
    # Force a streak on read_cb — 5 consecutive failures per config default.
    for _ in range(10):
        read_cb._record_failure(RuntimeError("read boom"))

    assert read_cb.state == "OPEN"
    assert write_cb.state == "CLOSED", (
        "STORY-416: read failures must not cascade into the write CB"
    )
    assert rpc_cb.state == "CLOSED", (
        "STORY-416: read failures must not cascade into the rpc CB either"
    )


def test_write_failures_do_not_open_read_cb() -> None:
    for _ in range(10):
        write_cb._record_failure(RuntimeError("write boom"))
    assert write_cb.state == "OPEN"
    assert read_cb.state == "CLOSED"
    assert rpc_cb.state == "CLOSED"


def test_get_cb_returns_segregated_instances() -> None:
    assert get_cb("read") is read_cb
    assert get_cb("write") is write_cb
    assert get_cb("rpc") is rpc_cb


def test_get_cb_unknown_category_falls_back_to_legacy() -> None:
    cb = get_cb("definitely-not-a-category")
    assert cb is supabase_cb


# ---------------------------------------------------------------------------
# Admin reset helper
# ---------------------------------------------------------------------------


def test_reset_all_circuit_breakers_returns_snapshot() -> None:
    # Trip read and write first — verify the reset reports their prior state.
    for _ in range(10):
        read_cb._record_failure(RuntimeError("boom"))
    for _ in range(10):
        write_cb._record_failure(RuntimeError("boom"))

    assert read_cb.state == "OPEN"
    assert write_cb.state == "OPEN"

    snapshot = reset_all_circuit_breakers()
    assert snapshot["read"] == "OPEN"
    assert snapshot["write"] == "OPEN"
    assert read_cb.state == "CLOSED"
    assert write_cb.state == "CLOSED"
    assert rpc_cb.state == "CLOSED"
    assert "legacy" in snapshot


# ---------------------------------------------------------------------------
# Schema errors still bypass the CB (CRIT-040 parity)
# ---------------------------------------------------------------------------


def test_schema_errors_still_excluded_on_segregated_cbs() -> None:
    """STORY-416 must not regress CRIT-040: schema errors never count."""
    for _ in range(10):
        read_cb._record_failure(Exception("PGRST205: schema cache miss"))
    assert read_cb.state == "CLOSED", (
        "Schema errors must continue to bypass the CB on all categories"
    )
