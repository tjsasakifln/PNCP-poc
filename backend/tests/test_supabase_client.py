"""Tests for supabase_client.py — circuit breaker, client management, sb_execute.

Wave 0 Safety Net: Covers SupabaseCircuitBreaker state transitions,
sliding window, cooldown, trial calls, _is_schema_error, sb_execute.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from supabase_client import (
    SupabaseCircuitBreaker,
    CircuitBreakerOpenError,
    _is_schema_error,
)


# ──────────────────────────────────────────────────────────────────────
# SupabaseCircuitBreaker — State Transitions
# ──────────────────────────────────────────────────────────────────────

class TestCircuitBreakerStates:
    """Tests for CB state machine transitions."""

    @pytest.mark.timeout(30)
    def test_initial_state_closed(self):
        cb = SupabaseCircuitBreaker()
        assert cb.state == "CLOSED"

    @pytest.mark.timeout(30)
    def test_closed_to_open_on_failures(self):
        """50% failure rate in 10-window should open the CB."""
        cb = SupabaseCircuitBreaker(window_size=10, failure_rate_threshold=0.5)
        # Fill window with 10 failures
        for _ in range(10):
            cb._record_failure()
        assert cb.state == "OPEN"

    @pytest.mark.timeout(30)
    def test_mixed_results_below_threshold(self):
        """40% failure rate should not open CB (threshold=50%)."""
        cb = SupabaseCircuitBreaker(window_size=10, failure_rate_threshold=0.5)
        for _ in range(6):
            cb._record_success()
        for _ in range(4):
            cb._record_failure()
        assert cb.state == "CLOSED"

    @pytest.mark.timeout(30)
    def test_open_to_half_open_after_cooldown(self):
        """After cooldown expires, OPEN -> HALF_OPEN."""
        cb = SupabaseCircuitBreaker(
            window_size=4, failure_rate_threshold=0.5, cooldown_seconds=0.1
        )
        for _ in range(4):
            cb._record_failure()
        assert cb.state == "OPEN"
        time.sleep(0.15)
        assert cb.state == "HALF_OPEN"

    @pytest.mark.timeout(30)
    def test_half_open_to_closed_after_trial_successes(self):
        """3 trial successes in HALF_OPEN -> CLOSED."""
        cb = SupabaseCircuitBreaker(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=3,
        )
        for _ in range(4):
            cb._record_failure()
        assert cb.state == "OPEN"
        time.sleep(0.1)
        assert cb.state == "HALF_OPEN"

        cb._record_success()
        cb._record_success()
        assert cb.state == "HALF_OPEN"  # Not yet
        cb._record_success()
        assert cb.state == "CLOSED"

    @pytest.mark.timeout(30)
    def test_half_open_to_open_on_failure(self):
        """A failure in HALF_OPEN -> OPEN."""
        cb = SupabaseCircuitBreaker(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=3,
        )
        for _ in range(4):
            cb._record_failure()
        time.sleep(0.1)
        assert cb.state == "HALF_OPEN"
        cb._record_failure()
        assert cb.state == "OPEN"

    @pytest.mark.timeout(30)
    def test_reset(self):
        cb = SupabaseCircuitBreaker(window_size=4, failure_rate_threshold=0.5)
        for _ in range(4):
            cb._record_failure()
        assert cb.state == "OPEN"
        cb.reset()
        assert cb.state == "CLOSED"


# ──────────────────────────────────────────────────────────────────────
# SupabaseCircuitBreaker — call_sync
# ──────────────────────────────────────────────────────────────────────

class TestCircuitBreakerCallSync:
    """Tests for synchronous call execution with CB."""

    @pytest.mark.timeout(30)
    def test_call_sync_success(self):
        cb = SupabaseCircuitBreaker()
        result = cb.call_sync(lambda: 42)
        assert result == 42

    @pytest.mark.timeout(30)
    def test_call_sync_failure_recorded(self):
        cb = SupabaseCircuitBreaker()
        with pytest.raises(ValueError):
            cb.call_sync(lambda: (_ for _ in ()).throw(ValueError("test")))

    @pytest.mark.timeout(30)
    def test_call_sync_open_raises(self):
        cb = SupabaseCircuitBreaker(window_size=2, failure_rate_threshold=0.5)
        for _ in range(2):
            cb._record_failure()
        with pytest.raises(CircuitBreakerOpenError):
            cb.call_sync(lambda: 42)


# ──────────────────────────────────────────────────────────────────────
# SupabaseCircuitBreaker — call_async
# ──────────────────────────────────────────────────────────────────────

class TestCircuitBreakerCallAsync:
    """Tests for async call execution with CB."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    async def test_call_async_success(self):
        cb = SupabaseCircuitBreaker()

        async def ok():
            return 42

        result = await cb.call_async(ok())
        assert result == 42

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    async def test_call_async_failure(self):
        cb = SupabaseCircuitBreaker()

        async def fail():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await cb.call_async(fail())

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    async def test_call_async_open_raises(self):
        cb = SupabaseCircuitBreaker(window_size=2, failure_rate_threshold=0.5)
        for _ in range(2):
            cb._record_failure()

        async def ok():
            return 42

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call_async(ok())


# ──────────────────────────────────────────────────────────────────────
# Sliding Window Behavior
# ──────────────────────────────────────────────────────────────────────

class TestSlidingWindow:
    """Tests for the sliding window failure counting."""

    @pytest.mark.timeout(30)
    def test_window_evicts_old_entries(self):
        """When window is full, oldest entry is evicted."""
        cb = SupabaseCircuitBreaker(window_size=4, failure_rate_threshold=0.5)
        # 4 failures -> open
        for _ in range(4):
            cb._record_failure()
        assert cb.state == "OPEN"

        # Reset and verify clean state
        cb.reset()
        # 3 successes + 1 failure = 25% failure rate in 4-window -> stays CLOSED
        for _ in range(3):
            cb._record_success()
        cb._record_failure()
        assert cb.state == "CLOSED"  # 1/4 = 25% < 50%

    @pytest.mark.timeout(30)
    def test_window_requires_full_before_opening(self):
        """CB needs a full window before calculating failure rate."""
        cb = SupabaseCircuitBreaker(window_size=10, failure_rate_threshold=0.5)
        for _ in range(5):
            cb._record_failure()
        # Only 5 entries in 10-window -> shouldn't open
        assert cb.state == "CLOSED"


# ──────────────────────────────────────────────────────────────────────
# Exclude Predicates (CRIT-040)
# ──────────────────────────────────────────────────────────────────────

class TestExcludePredicates:
    """Tests for exclude predicates preventing certain errors from counting."""

    @pytest.mark.timeout(30)
    def test_excluded_error_not_counted(self):
        def is_schema(e):
            return "schema" in str(e)

        cb = SupabaseCircuitBreaker(
            window_size=4, failure_rate_threshold=0.5,
            exclude_predicates=[is_schema],
        )
        for _ in range(10):
            cb._record_failure(Exception("schema error PGRST205"))
        # Excluded errors should not count -> CB stays closed
        assert cb.state == "CLOSED"

    @pytest.mark.timeout(30)
    def test_non_excluded_error_counted(self):
        def is_schema(e):
            return "schema" in str(e)

        cb = SupabaseCircuitBreaker(
            window_size=4, failure_rate_threshold=0.5,
            exclude_predicates=[is_schema],
        )
        for _ in range(4):
            cb._record_failure(Exception("connection timeout"))
        assert cb.state == "OPEN"


# ──────────────────────────────────────────────────────────────────────
# _is_schema_error
# ──────────────────────────────────────────────────────────────────────

class TestIsSchemaError:
    """Tests for schema error detection."""

    @pytest.mark.timeout(30)
    def test_pgrst205(self):
        assert _is_schema_error(Exception("PGRST205: relation not found")) is True

    @pytest.mark.timeout(30)
    def test_pgrst204(self):
        assert _is_schema_error(Exception("PGRST204: column not found")) is True

    @pytest.mark.timeout(30)
    def test_pg_42703(self):
        assert _is_schema_error(Exception("42703: undefined column")) is True

    @pytest.mark.timeout(30)
    def test_pg_42P01(self):
        assert _is_schema_error(Exception("42P01: undefined table")) is True

    @pytest.mark.timeout(30)
    def test_non_schema_error(self):
        assert _is_schema_error(Exception("connection refused")) is False

    @pytest.mark.timeout(30)
    def test_empty_message(self):
        assert _is_schema_error(Exception("")) is False


# ──────────────────────────────────────────────────────────────────────
# Thread Safety
# ──────────────────────────────────────────────────────────────────────

class TestThreadSafety:
    """Tests for concurrent access to the circuit breaker."""

    @pytest.mark.timeout(30)
    def test_concurrent_failures(self):
        cb = SupabaseCircuitBreaker(window_size=100, failure_rate_threshold=0.5)
        errors = []

        def record_many():
            try:
                for _ in range(50):
                    cb._record_failure()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0
        # Should be OPEN after 200 failures in a 100-window
        assert cb.state == "OPEN"
