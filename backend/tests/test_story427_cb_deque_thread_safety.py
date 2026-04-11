"""STORY-427: Fix RuntimeError `deque mutated during iteration` no CB Supabase.

Tests confirm that concurrent calls to _record_failure and _record_success
do not raise RuntimeError, and that sb_execute wraps RuntimeError in
CircuitBreakerOpenError instead of leaking a 500.
"""

import threading
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Tests: _record_failure thread safety
# ---------------------------------------------------------------------------

@pytest.mark.timeout(15)
def test_cb_record_failure_no_runtime_error_under_load():
    """10 threads calling _record_failure simultaneously must not RuntimeError."""
    from supabase_client import SupabaseCircuitBreaker

    cb = SupabaseCircuitBreaker(
        window_size=10,
        failure_rate_threshold=0.7,
        consecutive_failures_threshold=5,
        cooldown_seconds=60.0,
        trial_calls_max=2,
        name="test_story427",
    )

    errors: list[Exception] = []

    def worker():
        for _ in range(50):
            try:
                cb._record_failure()
            except RuntimeError as e:
                errors.append(e)
            except Exception:
                pass  # CB open etc. — not the error we're testing

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, (
        f"RuntimeError raised {len(errors)} time(s) under concurrent _record_failure: {errors[0]}"
    )


@pytest.mark.timeout(15)
def test_cb_mixed_success_failure_no_runtime_error():
    """Interleaved _record_success + _record_failure from 10 threads must not RuntimeError."""
    from supabase_client import SupabaseCircuitBreaker

    cb = SupabaseCircuitBreaker(
        window_size=10,
        failure_rate_threshold=0.7,
        consecutive_failures_threshold=200,  # high — avoid OPEN during test
        cooldown_seconds=60.0,
        trial_calls_max=2,
        name="test_story427_mixed",
    )

    errors: list[Exception] = []

    def failure_worker():
        for _ in range(30):
            try:
                cb._record_failure()
            except RuntimeError as e:
                errors.append(e)
            except Exception:
                pass

    def success_worker():
        for _ in range(30):
            try:
                cb._record_success()
            except RuntimeError as e:
                errors.append(e)
            except Exception:
                pass

    threads = (
        [threading.Thread(target=failure_worker) for _ in range(5)]
        + [threading.Thread(target=success_worker) for _ in range(5)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, (
        f"RuntimeError raised {len(errors)} time(s) in mixed concurrent CB calls: {errors[0]}"
    )


@pytest.mark.timeout(15)
def test_cb_window_clear_during_iteration_no_error():
    """CLOSED->OPEN transition (window.clear) must not RuntimeError during concurrent failure."""
    from supabase_client import SupabaseCircuitBreaker

    cb = SupabaseCircuitBreaker(
        window_size=5,
        failure_rate_threshold=0.6,
        consecutive_failures_threshold=3,
        cooldown_seconds=1.0,
        trial_calls_max=2,
        name="test_story427_clear",
    )

    errors: list[Exception] = []

    def worker():
        for _ in range(20):
            try:
                cb._record_failure()
                cb._record_success()
            except RuntimeError as e:
                errors.append(e)
            except Exception:
                pass

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, (
        f"RuntimeError during window.clear/iteration race: {errors}"
    )


# ---------------------------------------------------------------------------
# Tests: sb_execute wraps RuntimeError as CircuitBreakerOpenError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_sb_execute_wraps_runtime_error_in_cb_open_error():
    """RuntimeError in sb_execute must be wrapped as CircuitBreakerOpenError."""
    from supabase_client import CircuitBreakerOpenError

    with patch("supabase_client.asyncio.to_thread", side_effect=RuntimeError("deque mutated during iteration")), \
         patch("supabase_client.supabase_cb") as mock_legacy_cb, \
         patch("supabase_client.get_cb") as mock_get_cb, \
         patch("metrics.SUPABASE_POOL_ACTIVE"), \
         patch("metrics.SUPABASE_EXECUTE_DURATION"), \
         patch("metrics.SUPABASE_RETRY_TOTAL"):
        mock_legacy_cb.state = "CLOSED"
        mock_category_cb = MagicMock()
        mock_category_cb.state = "CLOSED"
        mock_get_cb.return_value = mock_category_cb

        from supabase_client import sb_execute
        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            await sb_execute(MagicMock(), category="read")

        assert "Circuit breaker internal error" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_sb_execute_does_not_propagate_runtime_error_as_500():
    """RuntimeError in sb_execute must NOT propagate as a plain RuntimeError."""
    from supabase_client import CircuitBreakerOpenError

    with patch("supabase_client.asyncio.to_thread", side_effect=RuntimeError("deque mutated")), \
         patch("supabase_client.supabase_cb") as mock_legacy_cb, \
         patch("supabase_client.get_cb") as mock_get_cb, \
         patch("metrics.SUPABASE_POOL_ACTIVE"), \
         patch("metrics.SUPABASE_EXECUTE_DURATION"), \
         patch("metrics.SUPABASE_RETRY_TOTAL"):
        mock_legacy_cb.state = "CLOSED"
        mock_cb = MagicMock()
        mock_cb.state = "CLOSED"
        mock_get_cb.return_value = mock_cb

        from supabase_client import sb_execute
        # Must raise CircuitBreakerOpenError, NOT RuntimeError
        with pytest.raises(Exception) as exc_info:
            await sb_execute(MagicMock(), category="write")

        assert not isinstance(exc_info.value, RuntimeError), (
            "sb_execute must not leak RuntimeError to callers — "
            "it must be wrapped as CircuitBreakerOpenError"
        )
        assert isinstance(exc_info.value, CircuitBreakerOpenError)
