"""CRIT-046: Tests for Supabase connection pool exhaustion fix.

AC1: Prometheus gauge `smartlic_supabase_pool_active_connections`
AC2: Log pool size when > 80% utilization
AC3: httpx pool configured with max_connections=50, max_keepalive=20
AC4: Explicit timeout=30s/connect=10s
AC5: ConnectionError retry (1 retry, 1s delay)
AC6: Existing tests pass without regression (full suite)
"""

import asyncio
from unittest.mock import Mock, patch

import pytest


# ---------------------------------------------------------------------------
# AC1: Pool active connections gauge
# ---------------------------------------------------------------------------

class TestPoolActiveMetric:
    """AC1: Prometheus gauge tracks active sb_execute connections."""

    @pytest.mark.asyncio
    async def test_sb_execute_increments_and_decrements_gauge(self):
        """Gauge increments on entry and decrements on exit."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[{"id": 1}])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge, \
             patch("metrics.SUPABASE_RETRY_TOTAL"):
            await sb_execute(mock_query)

        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_sb_execute_decrements_gauge_on_error(self):
        """Gauge decrements even when query fails (via finally)."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = ValueError("DB error")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge, \
             patch("metrics.SUPABASE_RETRY_TOTAL"):
            with pytest.raises(ValueError, match="DB error"):
                await sb_execute(mock_query)

        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_sb_execute_direct_tracks_gauge(self):
        """sb_execute_direct also increments/decrements the gauge."""
        from supabase_client import sb_execute_direct

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge:
            await sb_execute_direct(mock_query)

        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()

    @pytest.mark.asyncio
    async def test_sb_execute_direct_decrements_gauge_on_error(self):
        """sb_execute_direct decrements gauge even on failure."""
        from supabase_client import sb_execute_direct

        mock_query = Mock()
        mock_query.execute.side_effect = ConnectionError("timeout")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge:
            with pytest.raises(ConnectionError):
                await sb_execute_direct(mock_query)

        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()


# ---------------------------------------------------------------------------
# AC2: High-water pool utilization logging
# ---------------------------------------------------------------------------

class TestPoolHighWaterLogging:
    """AC2: Log when pool > 80% utilization."""

    @pytest.mark.asyncio
    async def test_logs_warning_when_pool_above_80_percent(self):
        """Warning logged when active connections > 80% of max."""
        import supabase_client
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[])

        # Simulate high pool usage by setting _pool_active_count to 40
        # (80% of 50 = 40, we need > 40 to trigger)
        original_count = supabase_client._pool_active_count
        supabase_client._pool_active_count = 40  # Will become 41 after inc

        try:
            with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
                 patch("metrics.SUPABASE_POOL_ACTIVE"), \
                 patch("metrics.SUPABASE_RETRY_TOTAL"), \
                 patch.object(supabase_client.logger, "warning") as mock_warn:
                await sb_execute(mock_query)

            # Check that the high-water warning was logged
            pool_warnings = [
                call for call in mock_warn.call_args_list
                if "80%" in str(call) and "CRIT-046" in str(call)
            ]
            assert len(pool_warnings) >= 1, "Expected high-water pool warning"
        finally:
            supabase_client._pool_active_count = original_count
            supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_no_warning_when_pool_below_80_percent(self):
        """No warning when active connections <= 80% of max."""
        import supabase_client
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[])

        # Pool at 0 — well below 80%
        original_count = supabase_client._pool_active_count
        supabase_client._pool_active_count = 0

        try:
            with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
                 patch("metrics.SUPABASE_POOL_ACTIVE"), \
                 patch("metrics.SUPABASE_RETRY_TOTAL"), \
                 patch.object(supabase_client.logger, "warning") as mock_warn:
                await sb_execute(mock_query)

            pool_warnings = [
                call for call in mock_warn.call_args_list
                if "80%" in str(call) and "CRIT-046" in str(call)
            ]
            assert len(pool_warnings) == 0, "Unexpected high-water warning"
        finally:
            supabase_client._pool_active_count = original_count
            supabase_cb.reset()


# ---------------------------------------------------------------------------
# AC3/AC4: httpx pool configuration
# ---------------------------------------------------------------------------

class TestHttpxPoolConfiguration:
    """AC3/AC4: Test _configure_httpx_pool configures limits and timeouts."""

    def test_configure_httpx_pool_sets_limits(self):
        """Pool configured with the production defaults from supabase_client (DEBT-018)."""
        import httpx
        from supabase_client import (
            _configure_httpx_pool,
            _POOL_MAX_CONNECTIONS,
            _POOL_MAX_KEEPALIVE,
        )

        # Create a mock supabase client with a real httpx session
        mock_client = Mock()
        mock_client.postgrest = Mock()
        mock_client.postgrest.session = httpx.Client(
            base_url="https://test.supabase.co/rest/v1",
            headers={"apikey": "test-key"},
        )

        _configure_httpx_pool(mock_client)

        new_session = mock_client.postgrest.session
        assert isinstance(new_session, httpx.Client)

        # Verify the transport has the correct limits matching module constants
        # (env-tunable via SUPABASE_POOL_MAX_CONNECTIONS / SUPABASE_POOL_MAX_KEEPALIVE).
        transport = new_session._transport
        assert transport._pool._max_connections == _POOL_MAX_CONNECTIONS
        assert transport._pool._max_keepalive_connections == _POOL_MAX_KEEPALIVE

    def test_configure_httpx_pool_sets_timeout(self):
        """Timeout configured as 30s total, 10s connect."""
        import httpx
        from supabase_client import _configure_httpx_pool

        mock_client = Mock()
        mock_client.postgrest = Mock()
        mock_client.postgrest.session = httpx.Client(
            base_url="https://test.supabase.co/rest/v1",
        )

        _configure_httpx_pool(mock_client)

        new_session = mock_client.postgrest.session
        timeout = new_session.timeout
        assert timeout.connect == 10.0
        # The default timeout (read/write/pool) should be 30.0
        assert timeout.read == 30.0

    def test_configure_httpx_pool_preserves_headers(self):
        """Custom headers from original session are preserved."""
        import httpx
        from supabase_client import _configure_httpx_pool

        mock_client = Mock()
        mock_client.postgrest = Mock()
        mock_client.postgrest.session = httpx.Client(
            base_url="https://test.supabase.co/rest/v1",
            headers={"apikey": "my-key", "Authorization": "Bearer token"},
        )

        _configure_httpx_pool(mock_client)

        new_session = mock_client.postgrest.session
        assert new_session.headers.get("apikey") == "my-key"
        assert new_session.headers.get("Authorization") == "Bearer token"

    def test_configure_httpx_pool_closes_old_session(self):
        """Old session is closed to release resources."""
        import httpx
        from supabase_client import _configure_httpx_pool

        mock_client = Mock()
        mock_client.postgrest = Mock()
        old_session = httpx.Client(
            base_url="https://test.supabase.co/rest/v1",
        )
        mock_client.postgrest.session = old_session

        _configure_httpx_pool(mock_client)

        # Old session should be closed (is_closed property)
        assert old_session.is_closed

    def test_configure_httpx_pool_graceful_on_error(self):
        """If configuration fails, logs warning but doesn't crash."""
        from supabase_client import _configure_httpx_pool

        mock_client = Mock()
        mock_client.postgrest = Mock()
        # session that raises on .base_url access
        mock_client.postgrest.session = Mock()
        mock_client.postgrest.session.base_url = None  # Will cause httpx.Client() to fail

        # Should not raise — logs warning
        _configure_httpx_pool(mock_client)


# ---------------------------------------------------------------------------
# AC5: ConnectionError retry
# ---------------------------------------------------------------------------

class TestConnectionErrorRetry:
    """AC5: ConnectionError retried once with 1s delay."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """ConnectionError on first try, success on retry."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        # First call raises ConnectionError, second succeeds
        mock_query.execute.side_effect = [
            ConnectionError("Too many connections"),
            Mock(data=[{"id": 1}]),
        ]

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL") as mock_retry, \
             patch("supabase_client._RETRY_DELAY_S", 0.01):  # Fast test
            result = await sb_execute(mock_query)

        assert result.data == [{"id": 1}]
        assert mock_query.execute.call_count == 2

        # Retry metrics recorded
        mock_retry.labels.assert_any_call(outcome="attempt")
        mock_retry.labels.assert_any_call(outcome="success")

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_retry_fails_on_second_attempt(self):
        """ConnectionError on both tries — raises after retry."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = ConnectionError("Pool exhausted")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL") as mock_retry, \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            with pytest.raises(ConnectionError, match="Pool exhausted"):
                await sb_execute(mock_query)

        assert mock_query.execute.call_count == 2

        mock_retry.labels.assert_any_call(outcome="attempt")
        mock_retry.labels.assert_any_call(outcome="failure")

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_non_connection_error_not_retried(self):
        """Non-ConnectionError exceptions are NOT retried."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = ValueError("Bad query")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"):
            with pytest.raises(ValueError, match="Bad query"):
                await sb_execute(mock_query)

        # Only 1 call — no retry for ValueError
        assert mock_query.execute.call_count == 1

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_retry_records_cb_success_on_recovery(self):
        """Successful retry records success in circuit breaker."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = [
            ConnectionError("Transient failure"),
            Mock(data=[]),
        ]

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"), \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            await sb_execute(mock_query)

        # CB should have a success recorded (not a failure)
        assert True in list(supabase_cb._window)

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_retry_records_cb_failure_on_exhaustion(self):
        """Failed retry records failure in circuit breaker."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = ConnectionError("Persistent failure")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"), \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            with pytest.raises(ConnectionError):
                await sb_execute(mock_query)

        # CB should have a failure recorded
        assert False in list(supabase_cb._window)

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_retry_different_error_on_second_attempt(self):
        """ConnectionError first, different error on retry — different error raised."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = [
            ConnectionError("Too many connections"),
            TimeoutError("Read timeout"),
        ]

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"), \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            with pytest.raises(TimeoutError, match="Read timeout"):
                await sb_execute(mock_query)

        assert mock_query.execute.call_count == 2

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_gauge_decremented_after_retry_success(self):
        """Pool gauge decremented in finally block after successful retry."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = [
            ConnectionError("Transient"),
            Mock(data=[]),
        ]

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge, \
             patch("metrics.SUPABASE_RETRY_TOTAL"), \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            await sb_execute(mock_query)

        # Gauge should be balanced: 1 inc, 1 dec
        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_gauge_decremented_after_retry_failure(self):
        """Pool gauge decremented in finally block after failed retry."""
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()

        mock_query = Mock()
        mock_query.execute.side_effect = ConnectionError("Persistent")

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE") as mock_gauge, \
             patch("metrics.SUPABASE_RETRY_TOTAL"), \
             patch("supabase_client._RETRY_DELAY_S", 0.01):
            with pytest.raises(ConnectionError):
                await sb_execute(mock_query)

        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()

        supabase_cb.reset()


# ---------------------------------------------------------------------------
# AC6: Constants and configuration validation
# ---------------------------------------------------------------------------

class TestPoolConstants:
    """Verify CRIT-046 constants are correctly defined."""

    def test_pool_max_connections(self):
        """DEBT-018 lowered the default to 25 (env-tunable via SUPABASE_POOL_MAX_CONNECTIONS)."""
        from supabase_client import _POOL_MAX_CONNECTIONS
        assert _POOL_MAX_CONNECTIONS == 25

    def test_pool_max_keepalive(self):
        """DEBT-018 lowered the default to 10 (env-tunable via SUPABASE_POOL_MAX_KEEPALIVE)."""
        from supabase_client import _POOL_MAX_KEEPALIVE
        assert _POOL_MAX_KEEPALIVE == 10

    def test_pool_timeout(self):
        from supabase_client import _POOL_TIMEOUT
        assert _POOL_TIMEOUT == 30.0

    def test_pool_connect_timeout(self):
        from supabase_client import _POOL_CONNECT_TIMEOUT
        assert _POOL_CONNECT_TIMEOUT == 10.0

    def test_retry_delay(self):
        from supabase_client import _RETRY_DELAY_S
        assert _RETRY_DELAY_S == 1.0

    def test_high_water_ratio(self):
        from supabase_client import _POOL_HIGH_WATER_RATIO
        assert _POOL_HIGH_WATER_RATIO == 0.8

    def test_metrics_defined(self):
        from metrics import SUPABASE_POOL_ACTIVE, SUPABASE_RETRY_TOTAL
        assert SUPABASE_POOL_ACTIVE is not None
        assert SUPABASE_RETRY_TOTAL is not None

    def test_configure_httpx_pool_function_exists(self):
        from supabase_client import _configure_httpx_pool
        assert callable(_configure_httpx_pool)


# ---------------------------------------------------------------------------
# Integration: Pool counter thread-safety
# ---------------------------------------------------------------------------

class TestPoolCounterThreadSafety:
    """Verify _pool_active_count is correctly managed."""

    @pytest.mark.asyncio
    async def test_counter_balanced_after_concurrent_calls(self):
        """Counter returns to 0 after multiple concurrent sb_execute calls."""
        import supabase_client
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()
        supabase_client._pool_active_count = 0

        mock_query = Mock()
        mock_query.execute.return_value = Mock(data=[])

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"):
            # Run 10 concurrent sb_execute calls
            tasks = [sb_execute(mock_query) for _ in range(10)]
            await asyncio.gather(*tasks)

        assert supabase_client._pool_active_count == 0

        supabase_cb.reset()

    @pytest.mark.asyncio
    async def test_counter_balanced_after_mixed_success_and_failure(self):
        """Counter returns to 0 with mix of successes and failures."""
        import supabase_client
        from supabase_client import sb_execute, supabase_cb

        supabase_cb.reset()
        supabase_client._pool_active_count = 0

        call_count = 0

        def alternating_execute():
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise ValueError("Simulated error")
            return Mock(data=[])

        mock_query = Mock()
        mock_query.execute.side_effect = alternating_execute

        with patch("metrics.SUPABASE_EXECUTE_DURATION"), \
             patch("metrics.SUPABASE_POOL_ACTIVE"), \
             patch("metrics.SUPABASE_RETRY_TOTAL"):
            for _ in range(9):
                try:
                    await sb_execute(mock_query)
                except ValueError:
                    pass

        assert supabase_client._pool_active_count == 0

        supabase_cb.reset()
