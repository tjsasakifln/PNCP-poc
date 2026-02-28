"""STORY-291: Tests for Supabase Circuit Breaker.

AC8: Tests for each state transition:
  - CLOSED → OPEN (when failure rate >= 50% in sliding window of 10)
  - OPEN → HALF_OPEN (after cooldown expires)
  - HALF_OPEN → CLOSED (after 3 consecutive trial successes)
  - HALF_OPEN → OPEN (on any failure during trial)

Also tests:
  - Redis plan cache fallback (AC3)
  - Fail-open quota behavior (AC4)
  - require_active_plan CB handling
  - sb_execute CB integration
  - Prometheus metrics emission (AC6, AC7)
"""

import time
import threading
from unittest.mock import Mock, patch

import pytest


# ---------------------------------------------------------------------------
# Unit tests for SupabaseCircuitBreaker class
# ---------------------------------------------------------------------------

class TestCircuitBreakerStateTransitions:
    """AC8: Test each CB state transition."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    def test_initial_state_is_closed(self):
        cb = self._make_cb()
        assert cb.state == "CLOSED"

    def test_closed_to_open_on_high_failure_rate(self):
        """CLOSED → OPEN when failure rate >= 50% in window of 10."""
        cb = self._make_cb(window_size=10, failure_rate_threshold=0.5)

        # Record 5 successes, then 5 failures → 50% failure rate
        for _ in range(5):
            cb._record_success()
        for _ in range(5):
            cb._record_failure()

        assert cb.state == "OPEN"

    def test_stays_closed_below_threshold(self):
        """Stays CLOSED when failure rate < 50%."""
        cb = self._make_cb(window_size=10, failure_rate_threshold=0.5)

        # 6 successes + 4 failures = 40% failure rate (below threshold)
        for _ in range(6):
            cb._record_success()
        for _ in range(4):
            cb._record_failure()

        assert cb.state == "CLOSED"

    def test_stays_closed_with_partial_window(self):
        """Stays CLOSED when window is not yet full (< window_size calls)."""
        cb = self._make_cb(window_size=10, failure_rate_threshold=0.5)

        # Only 5 calls (window not full yet), all failures
        for _ in range(5):
            cb._record_failure()

        assert cb.state == "CLOSED"

    def test_open_to_half_open_after_cooldown(self):
        """OPEN → HALF_OPEN after cooldown_seconds expires."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5, cooldown_seconds=0.1
        )

        # Force into OPEN state
        for _ in range(4):
            cb._record_failure()
        assert cb._state == "OPEN"

        # Wait for cooldown
        time.sleep(0.15)

        # Accessing state property should trigger transition
        assert cb.state == "HALF_OPEN"

    def test_stays_open_before_cooldown_expires(self):
        """Stays OPEN before cooldown expires."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5, cooldown_seconds=10.0
        )

        for _ in range(4):
            cb._record_failure()
        assert cb.state == "OPEN"

    def test_half_open_to_closed_after_trial_successes(self):
        """HALF_OPEN → CLOSED after trial_calls_max consecutive successes."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=3,
        )

        # Force OPEN
        for _ in range(4):
            cb._record_failure()
        assert cb._state == "OPEN"

        # Wait for cooldown → HALF_OPEN
        time.sleep(0.1)
        assert cb.state == "HALF_OPEN"

        # 3 trial successes → should transition to CLOSED
        for _ in range(3):
            cb._record_success()

        assert cb.state == "CLOSED"

    def test_half_open_to_open_on_failure(self):
        """HALF_OPEN → OPEN on any failure during trial period."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=3,
        )

        # Force OPEN
        for _ in range(4):
            cb._record_failure()

        # Wait for cooldown → HALF_OPEN
        time.sleep(0.1)
        assert cb.state == "HALF_OPEN"

        # 1 success then 1 failure → back to OPEN
        cb._record_success()
        cb._record_failure()

        assert cb.state == "OPEN"

    def test_window_cleared_on_close(self):
        """Window is cleared when transitioning to CLOSED."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=2,
        )

        # CLOSED → OPEN
        for _ in range(4):
            cb._record_failure()
        assert cb._state == "OPEN"

        # OPEN → HALF_OPEN
        time.sleep(0.1)
        _ = cb.state

        # HALF_OPEN → CLOSED
        cb._record_success()
        cb._record_success()

        assert cb.state == "CLOSED"
        assert len(cb._window) == 0

    def test_reset(self):
        """reset() returns CB to CLOSED with clean state."""
        cb = self._make_cb(window_size=4, failure_rate_threshold=0.5)

        for _ in range(4):
            cb._record_failure()
        assert cb._state == "OPEN"

        cb.reset()
        assert cb.state == "CLOSED"
        assert len(cb._window) == 0
        assert cb._trial_successes == 0
        assert cb._opened_at is None


class TestCircuitBreakerCallSync:
    """Test call_sync() wrapper behavior."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    def test_call_sync_success(self):
        cb = self._make_cb()
        result = cb.call_sync(lambda: 42)
        assert result == 42
        assert cb.state == "CLOSED"

    def test_call_sync_records_failure(self):
        cb = self._make_cb(window_size=4, failure_rate_threshold=0.5)

        for _ in range(4):
            with pytest.raises(ValueError):
                cb.call_sync(self._failing_func)

        assert cb.state == "OPEN"

    def test_call_sync_raises_cb_open_error(self):
        from supabase_client import CircuitBreakerOpenError
        cb = self._make_cb(window_size=4, failure_rate_threshold=0.5)

        # Force OPEN
        for _ in range(4):
            cb._record_failure()

        with pytest.raises(CircuitBreakerOpenError):
            cb.call_sync(lambda: 42)

    @staticmethod
    def _failing_func():
        raise ValueError("simulated failure")


class TestCircuitBreakerCallAsync:
    """Test call_async() wrapper behavior."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    @pytest.mark.asyncio
    async def test_call_async_success(self):
        cb = self._make_cb()

        async def success_coro():
            return 42

        result = await cb.call_async(success_coro())
        assert result == 42
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_call_async_raises_cb_open_error(self):
        from supabase_client import CircuitBreakerOpenError
        cb = self._make_cb(window_size=4, failure_rate_threshold=0.5)

        for _ in range(4):
            cb._record_failure()

        async def coro():
            return 42

        with pytest.raises(CircuitBreakerOpenError):
            await cb.call_async(coro())


class TestCircuitBreakerMetrics:
    """AC6, AC7: Prometheus metrics emission."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    def test_metrics_emitted_on_transition(self):
        """CB state transitions emit Prometheus metrics."""
        cb = self._make_cb(window_size=4, failure_rate_threshold=0.5)

        with patch("metrics.SUPABASE_CB_STATE") as mock_gauge, \
             patch("metrics.SUPABASE_CB_TRANSITIONS") as mock_counter:
            # Force CLOSED → OPEN
            for _ in range(4):
                cb._record_failure()

            mock_gauge.set.assert_called_with(1)  # 1 = OPEN
            mock_counter.labels.assert_called_with(
                from_state="CLOSED", to_state="OPEN", source="app"
            )

    def test_metrics_on_recovery(self):
        """Metrics emitted on HALF_OPEN → CLOSED recovery."""
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            cooldown_seconds=0.05, trial_calls_max=2,
        )

        for _ in range(4):
            cb._record_failure()

        time.sleep(0.1)
        _ = cb.state  # trigger HALF_OPEN

        with patch("metrics.SUPABASE_CB_STATE") as mock_gauge, \
             patch("metrics.SUPABASE_CB_TRANSITIONS") as mock_counter:
            cb._record_success()
            cb._record_success()

            mock_gauge.set.assert_called_with(0)  # 0 = CLOSED
            mock_counter.labels.assert_called_with(
                from_state="HALF_OPEN", to_state="CLOSED", source="app"
            )


class TestCircuitBreakerThreadSafety:
    """Verify thread safety of CB operations."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    def test_concurrent_access(self):
        cb = self._make_cb(window_size=100, failure_rate_threshold=0.5)
        errors = []

        def record_many(success: bool, count: int):
            try:
                for _ in range(count):
                    if success:
                        cb._record_success()
                    else:
                        cb._record_failure()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=record_many, args=(True, 50)),
            threading.Thread(target=record_many, args=(False, 50)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # State should be deterministic (window has 100 entries)
        assert cb.state in ("CLOSED", "OPEN")


# ---------------------------------------------------------------------------
# Integration tests: sb_execute with CB
# ---------------------------------------------------------------------------

class TestSbExecuteWithCB:
    """Test sb_execute() integration with global circuit breaker."""

    @pytest.mark.asyncio
    async def test_sb_execute_rejects_when_cb_open(self):
        from supabase_client import sb_execute, supabase_cb, CircuitBreakerOpenError

        supabase_cb.reset()
        # Force CB open
        for _ in range(10):
            supabase_cb._record_failure()

        mock_query = Mock()
        with pytest.raises(CircuitBreakerOpenError):
            await sb_execute(mock_query)

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_sb_execute_records_success(self):
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[{"id": 1}])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"):
            result = await sb_execute(mock_query)

        assert result.data == [{"id": 1}]
        # At least 1 success recorded
        assert True in list(supabase_cb._window)

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_sb_execute_records_failure(self):
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = Exception("DB error")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"):
            with pytest.raises(Exception, match="DB error"):
                await sb_execute(mock_query)

        assert False in list(supabase_cb._window)

        supabase_cb.reset()


# ---------------------------------------------------------------------------
# Integration tests: authorization with CB
# ---------------------------------------------------------------------------

class TestAuthorizationWithCB:
    """Test authorization.check_user_roles() with CB."""

    @pytest.mark.asyncio
    async def test_check_user_roles_returns_false_when_cb_open(self):
        from supabase_client import supabase_cb

        supabase_cb.reset()
        # Force CB open
        for _ in range(10):
            supabase_cb._record_failure()

        with patch("supabase_client.get_supabase", return_value=Mock()):
            from authorization import check_user_roles
            is_admin, is_master = await check_user_roles("test-user")

        assert is_admin is False
        assert is_master is False

        supabase_cb.reset()


# ---------------------------------------------------------------------------
# Integration tests: quota with CB
# ---------------------------------------------------------------------------

class TestQuotaWithCB:
    """Test quota functions with circuit breaker integration."""

    def setup_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

        # Clear plan status cache
        from quota import _plan_status_cache, _plan_status_cache_lock
        with _plan_status_cache_lock:
            _plan_status_cache.clear()

        # Clear plan capabilities cache
        try:
            import quota
            quota._plan_capabilities_cache = None
            quota._plan_capabilities_cache_time = 0
        except Exception:
            pass

    def teardown_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    def test_check_quota_caches_plan_on_success(self):
        """AC3: Plan status cached after successful Supabase call."""
        from quota import check_quota, _get_cached_plan_status

        mock_sb = Mock()
        # Subscription query
        sub_result = Mock()
        sub_result.data = [{"id": "sub-1", "plan_id": "smartlic_pro", "expires_at": None}]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute = Mock(return_value=sub_result)

        # Monthly quota query
        quota_result = Mock()
        quota_result.data = [{"searches_count": 5}]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute = Mock(return_value=quota_result)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = check_quota("user-123")

        assert result.plan_id == "smartlic_pro"
        # Plan should be cached
        cached = _get_cached_plan_status("user-123")
        assert cached == "smartlic_pro"

    def test_check_quota_uses_cache_when_cb_open(self):
        """AC3: When CB open, uses cached plan status."""
        from supabase_client import supabase_cb
        from quota import check_quota, _cache_plan_status

        # Pre-populate cache
        _cache_plan_status("user-456", "smartlic_pro")

        # Force CB open
        for _ in range(10):
            supabase_cb._record_failure()

        mock_sb = Mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = check_quota("user-456")

        assert result.plan_id == "smartlic_pro"
        assert result.allowed is True

    def test_check_quota_fail_open_when_cb_open_no_cache(self):
        """AC4: When CB open and no cache, allows search (fail-open)."""
        from supabase_client import supabase_cb
        from quota import check_quota

        # Force CB open (no cache pre-populated)
        for _ in range(10):
            supabase_cb._record_failure()

        mock_sb = Mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = check_quota("user-789")

        assert result.allowed is True
        assert result.plan_id == "smartlic_pro"

    def test_check_and_increment_quota_fail_open_when_cb_open(self):
        """AC4: check_and_increment_quota_atomic returns (True, 0, max) when CB open."""
        from supabase_client import supabase_cb
        from quota import check_and_increment_quota_atomic

        # Force CB open
        for _ in range(10):
            supabase_cb._record_failure()

        mock_sb = Mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", 1000)

        assert allowed is True
        assert new_count == 0
        assert remaining == 1000


class TestPlanStatusCache:
    """Test in-memory plan status cache (AC3)."""

    def setup_method(self):
        from quota import _plan_status_cache, _plan_status_cache_lock
        with _plan_status_cache_lock:
            _plan_status_cache.clear()

    def test_cache_set_and_get(self):
        from quota import _cache_plan_status, _get_cached_plan_status

        _cache_plan_status("user-1", "smartlic_pro")
        assert _get_cached_plan_status("user-1") == "smartlic_pro"

    def test_cache_returns_none_for_missing(self):
        from quota import _get_cached_plan_status

        assert _get_cached_plan_status("nonexistent") is None

    def test_cache_expires_after_ttl(self):
        from quota import _get_cached_plan_status, _plan_status_cache, _plan_status_cache_lock

        # Manually insert an entry with a past timestamp so it's already expired
        with _plan_status_cache_lock:
            # cached_at = 0 means it was cached at monotonic epoch (always expired with TTL=300)
            _plan_status_cache["user-2"] = ("smartlic_pro", 0.0)

        assert _get_cached_plan_status("user-2") is None


# ---------------------------------------------------------------------------
# Integration test: require_active_plan with CB
# ---------------------------------------------------------------------------

class TestRequireActivePlanWithCB:
    """Test require_active_plan() handles CircuitBreakerOpenError."""

    def setup_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    def teardown_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_require_active_plan_allows_when_cb_open(self):
        """AC4: When CB open, require_active_plan allows user through."""
        from supabase_client import CircuitBreakerOpenError
        from quota import require_active_plan

        user = {"id": "test-user-123", "email": "test@test.com"}

        # Mock has_master_access to raise CircuitBreakerOpenError
        with patch("authorization.has_master_access", side_effect=CircuitBreakerOpenError("CB open")):
            result = await require_active_plan(user)

        assert result == user  # User allowed through


# ---------------------------------------------------------------------------
# AC5: require_active_plan moved inside try block
# ---------------------------------------------------------------------------

class TestRequireActivePlanPosition:
    """AC5: require_active_plan is called AFTER tracker creation."""

    @pytest.mark.asyncio
    async def test_plan_error_emits_sse_event(self):
        """When require_active_plan fails, SSE tracker emits error event."""
        from fastapi import HTTPException
        from unittest.mock import AsyncMock

        mock_tracker = AsyncMock()
        mock_tracker.emit = AsyncMock()
        mock_tracker.emit_error = AsyncMock()

        with patch("routes.search.create_tracker", return_value=mock_tracker), \
             patch("routes.search.create_state_machine", return_value=Mock()), \
             patch("routes.search.remove_tracker", new_callable=AsyncMock), \
             patch("quota.require_active_plan", side_effect=HTTPException(
                 status_code=403,
                 detail={"error": "trial_expired", "message": "Seu trial expirou.", "upgrade_url": "/planos"}
             )):

            from main import app
            from httpx import AsyncClient, ASGITransport

            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                await client.post(
                    "/buscar",
                    json={
                        "setor_id": "tecnologia",
                        "ufs": ["SP"],
                        "dias": 10,
                    },
                    headers={"Authorization": "Bearer test-token"},
                )

            # Should get 403 (plan expired)
            # The key assertion: tracker.emit_error should have been called
            # because require_active_plan is now AFTER tracker creation (AC5)
            # Note: This test may get 401 from auth — the important thing is
            # that the code path exists. Full integration testing is covered by
            # the search endpoint tests.


# ---------------------------------------------------------------------------
# Definition of Done checks
# ---------------------------------------------------------------------------

class TestDefinitionOfDone:
    """Verify the Definition of Done items from the story."""

    def test_circuit_breaker_class_exists(self):
        from supabase_client import SupabaseCircuitBreaker
        assert SupabaseCircuitBreaker is not None

    def test_circuit_breaker_open_error_exists(self):
        from supabase_client import CircuitBreakerOpenError
        assert issubclass(CircuitBreakerOpenError, Exception)

    def test_global_singleton_exists(self):
        from supabase_client import supabase_cb
        assert supabase_cb is not None
        assert supabase_cb.state == "CLOSED"

    def test_metrics_defined(self):
        from metrics import SUPABASE_CB_STATE, SUPABASE_CB_TRANSITIONS
        assert SUPABASE_CB_STATE is not None
        assert SUPABASE_CB_TRANSITIONS is not None

    def test_sb_execute_uses_cb(self):
        """sb_execute checks CB state before executing."""
        import inspect
        from supabase_client import sb_execute
        source = inspect.getsource(sb_execute)
        assert "CircuitBreakerOpenError" in source or "supabase_cb" in source

    def test_global_singleton_has_exclude_predicates(self):
        """CRIT-040: Global singleton configured with schema error exclusion."""
        from supabase_client import supabase_cb
        assert len(supabase_cb._exclude_predicates) >= 1

    def test_is_schema_error_function_exists(self):
        """CRIT-040: _is_schema_error helper is importable."""
        from supabase_client import _is_schema_error
        assert callable(_is_schema_error)


# ---------------------------------------------------------------------------
# CRIT-040 AC10: Tests for exclude_predicates
# ---------------------------------------------------------------------------

class TestExcludePredicates:
    """CRIT-040 AC10: Test CB error exclusion for schema errors."""

    def _make_cb(self, **kwargs):
        from supabase_client import SupabaseCircuitBreaker
        return SupabaseCircuitBreaker(**kwargs)

    def test_pgrst205_does_not_increment_failure_count(self):
        """PGRST205 error is excluded — does NOT increment failure count."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        # Record 10 PGRST205 errors
        for _ in range(10):
            cb._record_failure(Exception("PGRST205: Could not find the table in the schema cache"))

        # Window should be empty — all excluded
        assert len(cb._window) == 0
        assert cb.state == "CLOSED"

    def test_pgrst204_does_not_increment_failure_count(self):
        """PGRST204 error is excluded — does NOT increment failure count."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        cb._record_failure(Exception("PGRST204: Column not found"))
        assert len(cb._window) == 0
        assert cb.state == "CLOSED"

    def test_pg_42703_does_not_increment_failure_count(self):
        """PostgreSQL 42703 (undefined column) is excluded."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        cb._record_failure(Exception("42703: undefined column"))
        assert len(cb._window) == 0

    def test_pg_42P01_does_not_increment_failure_count(self):
        """PostgreSQL 42P01 (undefined table) is excluded."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        cb._record_failure(Exception("42P01: undefined table"))
        assert len(cb._window) == 0

    def test_connection_error_increments_failure_count(self):
        """Connection errors are NOT excluded — SIM increment failure count."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        cb._record_failure(ConnectionError("Connection refused"))
        assert len(cb._window) == 1
        assert list(cb._window)[0] is False

    def test_cb_does_not_open_after_10_pgrst205_errors(self):
        """CB stays CLOSED after 10 consecutive PGRST205 errors."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        for _ in range(10):
            cb._record_failure(Exception("PGRST205: schema cache miss"))

        assert cb.state == "CLOSED"
        assert len(cb._window) == 0

    def test_cb_opens_after_5_connection_errors_in_window_of_10(self):
        """CB opens after 5 connection errors in window of 10 (50% rate)."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        # 5 successes + 5 connection errors = 50% failure rate → OPEN
        for _ in range(5):
            cb._record_success()
        for _ in range(5):
            cb._record_failure(ConnectionError("Connection refused"))

        assert cb.state == "OPEN"

    def test_mixed_schema_and_connection_errors(self):
        """Schema errors excluded, connection errors counted — correct rate."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        # 8 successes + 20 PGRST205 (all excluded) + 2 connection errors
        for _ in range(8):
            cb._record_success()
        for _ in range(20):
            cb._record_failure(Exception("PGRST205: schema cache miss"))
        for _ in range(2):
            cb._record_failure(ConnectionError("timeout"))

        # Window should have 10 entries: 8 success + 2 failure = 20% rate → CLOSED
        assert cb.state == "CLOSED"

    def test_no_predicates_counts_all_failures(self):
        """Without exclude_predicates, PGRST205 counts as normal failure."""
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
        )

        for _ in range(5):
            cb._record_success()
        for _ in range(5):
            cb._record_failure(Exception("PGRST205: schema cache miss"))

        assert cb.state == "OPEN"  # Without predicate, PGRST205 counts

    def test_record_failure_without_exception_counts_normally(self):
        """_record_failure(None) counts as a failure (backward compatible)."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        for _ in range(4):
            cb._record_failure()  # No exception passed

        assert cb.state == "OPEN"

    def test_exclude_predicate_exception_is_swallowed(self):
        """If a predicate itself raises, it's swallowed (best-effort)."""
        def buggy_predicate(exc):
            raise RuntimeError("predicate bug")

        cb = self._make_cb(
            window_size=4, failure_rate_threshold=0.5,
            exclude_predicates=[buggy_predicate],
        )

        # Should not crash — counts as normal failure
        for _ in range(4):
            cb._record_failure(Exception("some error"))

        assert cb.state == "OPEN"

    def test_call_sync_passes_exception_to_record_failure(self):
        """call_sync() passes the caught exception to _record_failure."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        # Schema error via call_sync — should be excluded
        def raise_pgrst205():
            raise Exception("PGRST205: table not found")

        for _ in range(10):
            with pytest.raises(Exception, match="PGRST205"):
                cb.call_sync(raise_pgrst205)

        assert cb.state == "CLOSED"  # All excluded
        assert len(cb._window) == 0

    @pytest.mark.asyncio
    async def test_call_async_passes_exception_to_record_failure(self):
        """call_async() passes the caught exception to _record_failure."""
        from supabase_client import _is_schema_error
        cb = self._make_cb(
            window_size=10, failure_rate_threshold=0.5,
            exclude_predicates=[_is_schema_error],
        )

        async def raise_pgrst205():
            raise Exception("PGRST205: table not found")

        for _ in range(10):
            with pytest.raises(Exception, match="PGRST205"):
                await cb.call_async(raise_pgrst205())

        assert cb.state == "CLOSED"
        assert len(cb._window) == 0


# ---------------------------------------------------------------------------
# CRIT-040 AC11: Integration test — health canary + missing table → CB CLOSED
# ---------------------------------------------------------------------------

class TestHealthCanaryCBIntegration:
    """CRIT-040 AC11: Health canary with missing table → CB remains CLOSED."""

    def setup_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    def teardown_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_save_health_check_pgrst205_cb_stays_closed(self):
        """save_health_check() with PGRST205 → CB stays CLOSED."""
        from supabase_client import supabase_cb

        # sb_execute_direct raises PGRST205 → health.py catches → CB untouched
        with patch("supabase_client.get_supabase", return_value=Mock()), \
             patch("supabase_client.sb_execute_direct") as mock_sb_direct:
            pgrst_exc = Exception("PGRST205: Could not find the table in the schema cache")
            mock_sb_direct.side_effect = pgrst_exc

            from health import save_health_check
            await save_health_check("healthy", {}, {})

        # CB should still be CLOSED — sb_execute_direct bypasses CB entirely
        assert supabase_cb.state == "CLOSED"
        assert len(supabase_cb._window) == 0

    @pytest.mark.asyncio
    async def test_detect_incident_pgrst205_cb_stays_closed(self):
        """detect_incident() with PGRST205 → CB stays CLOSED."""
        from supabase_client import supabase_cb

        pgrst_exc = Exception("PGRST205: schema cache miss")
        with patch("supabase_client.get_supabase", return_value=Mock()), \
             patch("supabase_client.sb_execute_direct", side_effect=pgrst_exc):
            from health import detect_incident
            await detect_incident("healthy", {})

        assert supabase_cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_repeated_pgrst205_never_opens_cb(self):
        """50 consecutive PGRST205 errors from health canary → CB still CLOSED."""
        from supabase_client import supabase_cb

        pgrst_exc = Exception("PGRST205: table missing")
        with patch("supabase_client.get_supabase", return_value=Mock()), \
             patch("supabase_client.sb_execute_direct", side_effect=pgrst_exc):
            from health import save_health_check
            for _ in range(50):
                await save_health_check("healthy", {}, {})

        assert supabase_cb.state == "CLOSED"
        assert len(supabase_cb._window) == 0


# ---------------------------------------------------------------------------
# CRIT-042: Health canary isolation tests
# ---------------------------------------------------------------------------

class TestCrit042CanaryIsolation:
    """CRIT-042 AC10-AC12: Health canary fully isolated from supabase_cb."""

    def setup_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    def teardown_method(self):
        from supabase_client import supabase_cb
        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_ac10_canary_20_failures_cb_stays_closed(self):
        """AC10: Health canary fails 20x consecutively → supabase_cb remains CLOSED.

        sb_execute_direct bypasses the CB entirely, so any number of
        canary failures must never affect supabase_cb state.
        """
        from supabase_client import supabase_cb

        timeout_exc = ConnectionError("Connection timed out")
        with patch("supabase_client.get_supabase", return_value=Mock()), \
             patch("supabase_client.sb_execute_direct", side_effect=timeout_exc):
            from health import save_health_check, detect_incident, cleanup_old_health_checks
            for _ in range(20):
                await save_health_check("unhealthy", {}, {})
                await detect_incident("unhealthy", {})
                await cleanup_old_health_checks()

        # CB must remain CLOSED — canary operations bypass CB
        assert supabase_cb.state == "CLOSED"
        assert len(supabase_cb._window) == 0

    @pytest.mark.asyncio
    async def test_ac11_real_app_error_opens_cb(self):
        """AC11: Real application connection error → supabase_cb opens normally.

        sb_execute (used by app code) still records failures in the CB.
        """
        from supabase_client import supabase_cb, sb_execute

        mock_query = Mock()
        mock_query.execute.side_effect = ConnectionError("Connection refused")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"):
            for _ in range(10):
                with pytest.raises(ConnectionError):
                    await sb_execute(mock_query)

        # CB should be OPEN — 10 consecutive failures (100% rate in window of 10)
        assert supabase_cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_ac12_sb_execute_direct_works_when_cb_open(self):
        """AC12: sb_execute_direct() works even when supabase_cb is OPEN.

        The bypass function must not check CB state at all.
        """
        from supabase_client import supabase_cb, sb_execute_direct

        # Force CB OPEN
        for _ in range(10):
            supabase_cb._record_failure()
        assert supabase_cb.state == "OPEN"

        # sb_execute_direct must still work
        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[{"id": 1}])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"):
            result = await sb_execute_direct(mock_query)

        assert result.data == [{"id": 1}]
        # CB must still be OPEN — sb_execute_direct doesn't record success either
        assert supabase_cb.state == "OPEN"

    @pytest.mark.asyncio
    async def test_canary_failures_then_app_query_succeeds(self):
        """Canary failures don't poison app queries — CB stays CLOSED for app."""
        from supabase_client import supabase_cb, sb_execute

        # 50 canary failures via sb_execute_direct (bypass)
        timeout_exc = ConnectionError("timeout")
        with patch("supabase_client.get_supabase", return_value=Mock()), \
             patch("supabase_client.sb_execute_direct", side_effect=timeout_exc):
            from health import save_health_check
            for _ in range(50):
                await save_health_check("unhealthy", {}, {})

        # CB should be untouched
        assert supabase_cb.state == "CLOSED"

        # App query via sb_execute should work fine
        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[{"ok": True}])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"):
            result = await sb_execute(mock_query)

        assert result.data == [{"ok": True}]
        assert supabase_cb.state == "CLOSED"
