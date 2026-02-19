"""Tests for circuit breaker log hygiene (GTM-RESILIENCE-E02 AC2/AC6/AC7).

Validates:
  - Circuit breaker does NOT emit per-failure debug logs
  - Circuit breaker DOES emit trip warning and recovery info
  - Error scenario total log count is within budget
"""

import asyncio
import logging
import pytest
from unittest.mock import patch

from pncp_client import PNCPCircuitBreaker


@pytest.mark.asyncio
class TestCircuitBreakerLogHygiene:
    """AC2: Circuit breaker logs only on state transitions."""

    async def test_no_per_failure_debug_logs(self, caplog):
        """AC2: record_failure() does not emit debug logs for each failure."""
        cb = PNCPCircuitBreaker(name="test", threshold=5, cooldown_seconds=10)

        with caplog.at_level(logging.DEBUG):
            for _ in range(4):
                await cb.record_failure()

        # No debug logs about individual failure increments
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        failure_debugs = [r for r in debug_records if "failure #" in r.message]
        assert len(failure_debugs) == 0, (
            f"Expected 0 per-failure debug logs, got {len(failure_debugs)}: "
            f"{[r.message for r in failure_debugs]}"
        )

    async def test_no_per_success_debug_logs(self, caplog):
        """AC2: record_success() does not emit debug logs for reset."""
        cb = PNCPCircuitBreaker(name="test", threshold=5, cooldown_seconds=10)

        # Accumulate some failures then succeed
        for _ in range(3):
            await cb.record_failure()

        with caplog.at_level(logging.DEBUG):
            await cb.record_success()

        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        reset_debugs = [r for r in debug_records if "resetting counter" in r.message]
        assert len(reset_debugs) == 0, (
            f"Expected 0 reset debug logs, got {len(reset_debugs)}: "
            f"{[r.message for r in reset_debugs]}"
        )

    async def test_trip_emits_warning(self, caplog):
        """AC2: Trip event still emits WARNING log."""
        cb = PNCPCircuitBreaker(name="test_trip", threshold=3, cooldown_seconds=10)

        with caplog.at_level(logging.WARNING):
            for _ in range(3):
                await cb.record_failure()

        trip_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "TRIPPED" in r.message
        ]
        assert len(trip_warnings) == 1
        assert "test_trip" in trip_warnings[0].message
        assert "3" in trip_warnings[0].message  # failure count

    async def test_recovery_emits_info(self, caplog):
        """AC2: Recovery event still emits INFO log."""
        cb = PNCPCircuitBreaker(name="test_recovery", threshold=2, cooldown_seconds=0)

        # Trip the breaker
        for _ in range(2):
            await cb.record_failure()

        # Wait for cooldown (0 seconds)
        await asyncio.sleep(0.01)

        with caplog.at_level(logging.INFO):
            recovered = await cb.try_recover()

        assert recovered is True
        recovery_infos = [
            r for r in caplog.records
            if r.levelno == logging.INFO and "cooldown expired" in r.message
        ]
        assert len(recovery_infos) == 1
        assert "test_recovery" in recovery_infos[0].message


@pytest.mark.asyncio
class TestErrorScenarioLogBudget:
    """AC7: Error scenario log count within budget."""

    async def test_trip_cycle_log_count(self, caplog):
        """AC7: 3 failures (trip) + recovery produces ≤5 log lines (INFO+WARNING+ERROR).

        Expected: 1 WARNING (trip) + 1 INFO (recovery) = 2 lines total.
        Budget: ≤5 lines.
        """
        cb = PNCPCircuitBreaker(name="budget_test", threshold=3, cooldown_seconds=60)

        with caplog.at_level(logging.INFO):
            # 3 failures to trip (stays degraded with 60s cooldown)
            for _ in range(3):
                await cb.record_failure()

            # Manually expire cooldown for recovery test
            cb.degraded_until = 0  # Force expired

            # Recovery
            await cb.try_recover()

            # Success resets counter
            await cb.record_success()

        # Count INFO + WARNING + ERROR logs
        significant_records = [
            r for r in caplog.records
            if r.levelno >= logging.INFO
        ]

        assert len(significant_records) <= 5, (
            f"Expected ≤5 log lines for full trip+recovery cycle, got {len(significant_records)}: "
            f"{[(r.levelname, r.message) for r in significant_records]}"
        )

        # Verify we have at least the essential logs
        trip_logs = [r for r in significant_records if "TRIPPED" in r.message]
        recovery_logs = [r for r in significant_records if "cooldown expired" in r.message]
        assert len(trip_logs) == 1, "Should have exactly 1 trip log"
        assert len(recovery_logs) == 1, "Should have exactly 1 recovery log"

    async def test_intermittent_errors_minimal_logs(self, caplog):
        """AC7: Intermittent failures (fail-succeed-fail) produce minimal logs."""
        cb = PNCPCircuitBreaker(name="intermittent", threshold=5, cooldown_seconds=10)

        with caplog.at_level(logging.INFO):
            # Simulate intermittent: 2 failures, 1 success, 2 failures
            await cb.record_failure()
            await cb.record_failure()
            await cb.record_success()
            await cb.record_failure()
            await cb.record_failure()

        # No trip (never reached threshold due to reset), so 0 logs
        significant_records = [
            r for r in caplog.records
            if r.levelno >= logging.INFO
        ]
        assert len(significant_records) == 0, (
            f"Expected 0 log lines for sub-threshold intermittent errors, got {len(significant_records)}: "
            f"{[(r.levelname, r.message) for r in significant_records]}"
        )
