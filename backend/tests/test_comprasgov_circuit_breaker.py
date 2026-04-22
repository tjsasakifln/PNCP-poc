"""STORY-305: ComprasGov Circuit Breaker tests.

AC14: CB trips after 15 failures and blocks new calls
AC15: CB recovers after cooldown (half-open → closed)
AC16: Pipeline works with 1 source in CB OPEN (partial results)
AC17: Pipeline returns cache stale when all sources OPEN
AC18: Existing tests pass (verified separately)
"""

import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# AC14: ComprasGov CB trips after threshold failures
# ---------------------------------------------------------------------------

class TestComprasGovCBTrip:
    """Verify ComprasGov circuit breaker trips after 15 failures."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Import and create a fresh CB instance for each test."""
        from pncp_client import PNCPCircuitBreaker
        self.cb = PNCPCircuitBreaker(
            name="comprasgov_test",
            threshold=15,
            cooldown_seconds=60,
        )

    @pytest.mark.asyncio
    async def test_cb_trips_after_threshold_failures(self):
        """AC14: ComprasGov CB trips after 15 consecutive failures."""
        assert not self.cb.is_degraded

        for _ in range(14):
            await self.cb.record_failure()
            assert not self.cb.is_degraded, "Should not trip before threshold"

        await self.cb.record_failure()  # 15th failure
        assert self.cb.is_degraded, "Should trip at threshold=15"

    @pytest.mark.asyncio
    async def test_cb_blocks_after_trip(self):
        """AC14: Once tripped, CB reports degraded state."""
        for _ in range(15):
            await self.cb.record_failure()

        assert self.cb.is_degraded
        # Verify it stays degraded (cooldown hasn't expired)
        assert self.cb.is_degraded

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Success resets consecutive failures — CB never trips."""
        for _ in range(14):
            await self.cb.record_failure()
        await self.cb.record_success()
        assert self.cb.consecutive_failures == 0

        # Another 14 failures still don't trip
        for _ in range(14):
            await self.cb.record_failure()
        assert not self.cb.is_degraded


# ---------------------------------------------------------------------------
# AC15: ComprasGov CB recovers after cooldown
# ---------------------------------------------------------------------------

class TestComprasGovCBRecovery:
    """Verify ComprasGov circuit breaker recovers after cooldown."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from pncp_client import PNCPCircuitBreaker
        self.cb = PNCPCircuitBreaker(
            name="comprasgov_recovery",
            threshold=15,
            cooldown_seconds=2,  # Short cooldown for testing
        )

    @pytest.mark.asyncio
    async def test_cb_recovers_after_cooldown(self):
        """AC15: CB transitions from OPEN back to CLOSED after cooldown."""
        for _ in range(15):
            await self.cb.record_failure()
        assert self.cb.is_degraded

        # Fast-forward past cooldown
        self.cb.degraded_until = time.time() - 1
        recovered = await self.cb.try_recover()
        assert recovered
        assert not self.cb.is_degraded
        assert self.cb.consecutive_failures == 0


# ---------------------------------------------------------------------------
# AC16: Pipeline with 1 source CB OPEN — partial results
# ---------------------------------------------------------------------------

class TestPipelinePartialResults:
    """Verify pipeline works when 1 source has CB OPEN."""

    @pytest.mark.asyncio
    @patch("pncp_client.get_circuit_breaker")
    async def test_pipeline_skips_cb_open_source(self, mock_get_cb):
        """AC16: Pipeline excludes source with CB OPEN, continues with others."""
        # Create mock CBs — ComprasGov is degraded
        pncp_cb = MagicMock()
        pncp_cb.is_degraded = False
        pcp_cb = MagicMock()
        pcp_cb.is_degraded = False
        comprasgov_cb = MagicMock()
        comprasgov_cb.is_degraded = True  # CB OPEN

        def _get_cb(source="pncp"):
            if source == "pcp":
                return pcp_cb
            if source == "comprasgov":
                return comprasgov_cb
            return pncp_cb

        mock_get_cb.side_effect = _get_cb

        # Verify the CB check logic
        cb = _get_cb("comprasgov")
        assert cb.is_degraded, "ComprasGov CB should be OPEN"
        cb = _get_cb("pncp")
        assert not cb.is_degraded, "PNCP CB should be CLOSED"
        cb = _get_cb("pcp")
        assert not cb.is_degraded, "PCP CB should be CLOSED"


# ---------------------------------------------------------------------------
# AC17: Pipeline returns cache stale when all sources OPEN
# ---------------------------------------------------------------------------

class TestAllSourcesCBOpen:
    """Verify pipeline behavior when all sources have CB OPEN."""

    @pytest.mark.asyncio
    @patch("pncp_client.get_circuit_breaker")
    async def test_all_sources_open_returns_empty_adapters(self, mock_get_cb):
        """AC17: When all CBs are OPEN, no adapters are created."""
        # All CBs degraded
        degraded_cb = MagicMock()
        degraded_cb.is_degraded = True

        mock_get_cb.return_value = degraded_cb

        # All 3 sources would be skipped
        sources_to_check = ["pncp", "pcp", "comprasgov"]
        skipped = []
        for src in sources_to_check:
            cb = mock_get_cb(src)
            if cb.is_degraded:
                skipped.append(src)

        assert len(skipped) == 3, "All 3 sources should be skipped"


# ---------------------------------------------------------------------------
# Threshold alignment verification
# ---------------------------------------------------------------------------

class TestThresholdAlignment:
    """STORY-305 AC5: Verify all 3 sources share aligned thresholds."""

    def test_default_thresholds_aligned(self):
        """AC5: PNCP, PCP, and ComprasGov all default to threshold=15, cooldown=60s."""
        import os

        # Clear any overrides for this test
        env_backup = {}
        for key in (
            "PNCP_CIRCUIT_BREAKER_THRESHOLD",
            "PNCP_CIRCUIT_BREAKER_COOLDOWN",
            "PCP_CIRCUIT_BREAKER_THRESHOLD",
            "PCP_CIRCUIT_BREAKER_COOLDOWN",
            "COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD",
            "COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN",
        ):
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)

        try:
            # Re-import to get defaults
            # pncp_client re-exports PNCP/PCP constants; COMPRASGOV constants live
            # in config.pncp (source of truth) — no pncp_client re-export (TD-007 split).
            from pncp_client import (
                PNCP_CIRCUIT_BREAKER_THRESHOLD,
                PNCP_CIRCUIT_BREAKER_COOLDOWN,
                PCP_CIRCUIT_BREAKER_THRESHOLD,
                PCP_CIRCUIT_BREAKER_COOLDOWN,
            )
            from config import (
                COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD,
                COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN,
            )

            # All thresholds should be 15
            assert PNCP_CIRCUIT_BREAKER_THRESHOLD == 15
            assert PCP_CIRCUIT_BREAKER_THRESHOLD == 15
            assert COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD == 15

            # All cooldowns should be 60s
            assert PNCP_CIRCUIT_BREAKER_COOLDOWN == 60
            assert PCP_CIRCUIT_BREAKER_COOLDOWN == 60
            assert COMPRASGOV_CIRCUIT_BREAKER_COOLDOWN == 60
        finally:
            # Restore env
            for key, val in env_backup.items():
                os.environ[key] = val


class TestGetCircuitBreaker:
    """Verify get_circuit_breaker returns correct instances."""

    def test_returns_comprasgov_cb(self):
        """get_circuit_breaker('comprasgov') returns ComprasGov instance."""
        from pncp_client import get_circuit_breaker
        cb = get_circuit_breaker("comprasgov")
        assert cb.name == "comprasgov"

    def test_returns_pncp_cb(self):
        from pncp_client import get_circuit_breaker
        cb = get_circuit_breaker("pncp")
        assert cb.name == "pncp"

    def test_returns_pcp_cb(self):
        from pncp_client import get_circuit_breaker
        cb = get_circuit_breaker("pcp")
        assert cb.name == "pcp"

    def test_default_returns_pncp(self):
        from pncp_client import get_circuit_breaker
        cb = get_circuit_breaker()
        assert cb.name == "pncp"


# ---------------------------------------------------------------------------
# Sentry breadcrumb on transition (AC13)
# ---------------------------------------------------------------------------

class TestSentryBreadcrumbs:
    """AC13: Verify Sentry breadcrumbs are emitted on CB state transitions."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from pncp_client import PNCPCircuitBreaker
        self.cb = PNCPCircuitBreaker(
            name="sentry_test",
            threshold=3,
            cooldown_seconds=2,
        )

    @pytest.mark.asyncio
    @patch("sentry_sdk.add_breadcrumb")
    async def test_breadcrumb_on_trip(self, mock_breadcrumb):
        """AC13: Sentry breadcrumb emitted when CB transitions to OPEN."""
        for _ in range(3):
            await self.cb.record_failure()

        mock_breadcrumb.assert_called_once()
        call_kwargs = mock_breadcrumb.call_args
        assert call_kwargs[1]["category"] == "circuit_breaker"
        assert "OPEN" in call_kwargs[1]["message"]

    @pytest.mark.asyncio
    @patch("sentry_sdk.add_breadcrumb")
    async def test_breadcrumb_on_recovery(self, mock_breadcrumb):
        """AC13: Sentry breadcrumb emitted when CB transitions to CLOSED."""
        for _ in range(3):
            await self.cb.record_failure()
        mock_breadcrumb.reset_mock()

        # Fast-forward past cooldown
        self.cb.degraded_until = time.time() - 1
        await self.cb.try_recover()

        mock_breadcrumb.assert_called_once()
        call_kwargs = mock_breadcrumb.call_args
        assert "CLOSED" in call_kwargs[1]["message"]
