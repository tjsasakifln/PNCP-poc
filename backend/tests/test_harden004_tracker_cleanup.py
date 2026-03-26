"""HARDEN-004: Periodic tracker cleanup tests.

Tests AC1 (periodic loop), AC5 (metric), AC6 (unit validation).
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _clear_trackers():
    """Reset _active_trackers before each test."""
    from progress import _active_trackers
    _active_trackers.clear()
    yield
    _active_trackers.clear()


class TestCleanupStaleReturnsCount:
    """_cleanup_stale() must return int (number of cleaned trackers)."""

    def test_returns_zero_when_no_trackers(self):
        from progress import _cleanup_stale
        result = _cleanup_stale()
        assert result == 0

    def test_returns_zero_when_trackers_not_stale(self):
        from progress import _active_trackers, _cleanup_stale, ProgressTracker
        tracker = ProgressTracker("fresh-1", 3)
        tracker.created_at = time.time()  # just created
        _active_trackers["fresh-1"] = tracker
        result = _cleanup_stale()
        assert result == 0
        assert "fresh-1" in _active_trackers

    @patch("search_state_manager.get_state_machine", return_value=None)
    def test_returns_count_of_stale_trackers(self, _mock_sm):
        from progress import _active_trackers, _cleanup_stale, _TRACKER_TTL, ProgressTracker
        # Create two stale trackers
        for i in range(2):
            t = ProgressTracker(f"stale-{i}", 3)
            t.created_at = time.time() - _TRACKER_TTL - 100
            _active_trackers[f"stale-{i}"] = t
        result = _cleanup_stale()
        assert result == 2
        assert len(_active_trackers) == 0


class TestPeriodicTrackerCleanup:
    """AC1: _periodic_tracker_cleanup runs every _TRACKER_CLEANUP_INTERVAL seconds."""

    @pytest.mark.asyncio
    async def test_periodic_cleanup_calls_cleanup_stale(self):
        """Verify the loop runs and calls _cleanup_stale."""
        from progress import _periodic_tracker_cleanup

        call_count = 0

        def mock_cleanup():
            nonlocal call_count
            call_count += 1
            return 0

        with patch("progress._TRACKER_CLEANUP_INTERVAL", 0.01), \
             patch("progress._cleanup_stale", side_effect=mock_cleanup):
            task = asyncio.create_task(_periodic_tracker_cleanup())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_periodic_cleanup_removes_stale_trackers(self):
        """Stale trackers are actually removed by the periodic loop."""
        from progress import (
            _active_trackers,
            _periodic_tracker_cleanup,
            _TRACKER_TTL,
            ProgressTracker,
        )

        # Add a stale tracker
        t = ProgressTracker("stale-periodic", 3)
        t.created_at = time.time() - _TRACKER_TTL - 100
        _active_trackers["stale-periodic"] = t

        with patch("progress._TRACKER_CLEANUP_INTERVAL", 0.01), \
             patch("search_state_manager.get_state_machine", return_value=None):
            task = asyncio.create_task(_periodic_tracker_cleanup())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        assert "stale-periodic" not in _active_trackers

    @pytest.mark.asyncio
    async def test_periodic_cleanup_increments_metric(self):
        """AC5: TRACKER_CLEANUP_COUNT metric incremented when trackers cleaned."""
        from progress import (
            _active_trackers,
            _periodic_tracker_cleanup,
            _TRACKER_TTL,
            ProgressTracker,
        )

        mock_counter = MagicMock()

        # Add a stale tracker
        t = ProgressTracker("stale-metric", 3)
        t.created_at = time.time() - _TRACKER_TTL - 100
        _active_trackers["stale-metric"] = t

        with patch("progress._TRACKER_CLEANUP_INTERVAL", 0.01), \
             patch("search_state_manager.get_state_machine", return_value=None), \
             patch("metrics.TRACKER_CLEANUP_COUNT", mock_counter):
            task = asyncio.create_task(_periodic_tracker_cleanup())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        mock_counter.inc.assert_called_with(1)

    @pytest.mark.asyncio
    async def test_periodic_cleanup_survives_exception(self):
        """Exceptions in _cleanup_stale don't crash the loop."""
        from progress import _periodic_tracker_cleanup

        call_count = 0

        def failing_cleanup():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("simulated failure")
            return 0

        with patch("progress._TRACKER_CLEANUP_INTERVAL", 0.01), \
             patch("progress._cleanup_stale", side_effect=failing_cleanup):
            task = asyncio.create_task(_periodic_tracker_cleanup())
            await asyncio.sleep(0.08)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Loop survived the exception and ran at least twice
        assert call_count >= 2


class TestCleanupInterval:
    """AC1: Verify constant value."""

    def test_cleanup_interval_is_120(self):
        from progress import _TRACKER_CLEANUP_INTERVAL
        assert _TRACKER_CLEANUP_INTERVAL == 120
