"""HARDEN-003: Tests for bounded asyncio.Queue in ProgressTracker.

AC1: maxsize=500
AC2: Drop-oldest backpressure when queue is full
AC3: SSE_QUEUE_DROPS metric increments on drop
AC4: Unit test validates behavior with queue full
"""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from progress import ProgressTracker


@pytest.fixture
def tracker():
    """Create a ProgressTracker with small maxsize for testing."""
    t = ProgressTracker(search_id="test-harden-003", uf_count=5)
    return t


@pytest.fixture
def small_tracker():
    """Create a ProgressTracker with maxsize=3 for fast fill testing."""
    t = ProgressTracker(search_id="test-small", uf_count=1)
    t.queue = asyncio.Queue(maxsize=3)
    return t


class TestQueueBounded:
    """AC1: Queue has maxsize=500."""

    def test_queue_has_maxsize(self, tracker):
        assert tracker.queue.maxsize == 500

    def test_queue_starts_empty(self, tracker):
        assert tracker.queue.empty()

    @pytest.mark.asyncio
    async def test_queue_accepts_events_up_to_maxsize(self, small_tracker):
        """Queue should accept events without blocking up to maxsize."""
        with patch("progress.get_redis_pool", return_value=None):
            for i in range(3):
                await small_tracker.emit("fetching", i * 10, f"msg {i}")
            assert small_tracker.queue.qsize() == 3


class TestDropOldest:
    """AC2: Drop-oldest when queue is full."""

    @pytest.mark.asyncio
    async def test_drop_oldest_when_full(self, small_tracker):
        """When queue is full, oldest event should be dropped to make room."""
        with patch("progress.get_redis_pool", return_value=None):
            # Fill queue
            await small_tracker.emit("fetching", 10, "first")
            await small_tracker.emit("fetching", 20, "second")
            await small_tracker.emit("fetching", 30, "third")
            assert small_tracker.queue.full()

            # This should drop "first" and add "fourth"
            await small_tracker.emit("fetching", 40, "fourth")

            assert small_tracker.queue.qsize() == 3
            # Drain and verify oldest was dropped
            events = []
            while not small_tracker.queue.empty():
                events.append(small_tracker.queue.get_nowait())
            messages = [e.message for e in events]
            assert messages == ["second", "third", "fourth"]

    @pytest.mark.asyncio
    async def test_no_drop_when_not_full(self, small_tracker):
        """No events should be dropped when queue has room."""
        with patch("progress.get_redis_pool", return_value=None):
            await small_tracker.emit("fetching", 10, "first")
            await small_tracker.emit("fetching", 20, "second")

            assert small_tracker.queue.qsize() == 2
            events = []
            while not small_tracker.queue.empty():
                events.append(small_tracker.queue.get_nowait())
            messages = [e.message for e in events]
            assert messages == ["first", "second"]

    @pytest.mark.asyncio
    async def test_multiple_drops_in_sequence(self, small_tracker):
        """Multiple overflows should each drop the oldest."""
        with patch("progress.get_redis_pool", return_value=None):
            for i in range(6):
                await small_tracker.emit("fetching", i * 10, f"msg-{i}")

            assert small_tracker.queue.qsize() == 3
            events = []
            while not small_tracker.queue.empty():
                events.append(small_tracker.queue.get_nowait())
            messages = [e.message for e in events]
            assert messages == ["msg-3", "msg-4", "msg-5"]


class TestDropMetric:
    """AC3: SSE_QUEUE_DROPS metric increments on drop."""

    @pytest.mark.asyncio
    async def test_metric_incremented_on_drop(self, small_tracker):
        """SSE_QUEUE_DROPS.inc() should be called when an event is dropped."""
        with patch("progress.get_redis_pool", return_value=None):
            mock_metric = MagicMock()
            with patch("metrics.SSE_QUEUE_DROPS", mock_metric):
                # Fill queue
                for i in range(3):
                    await small_tracker.emit("fetching", i * 10, f"msg-{i}")

                mock_metric.inc.assert_not_called()

                # Trigger drop
                await small_tracker.emit("fetching", 40, "overflow")
                mock_metric.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_metric_not_incremented_without_drop(self, small_tracker):
        """SSE_QUEUE_DROPS should not be called when queue has room."""
        with patch("progress.get_redis_pool", return_value=None):
            mock_metric = MagicMock()
            with patch("metrics.SSE_QUEUE_DROPS", mock_metric):
                await small_tracker.emit("fetching", 10, "msg")
                mock_metric.inc.assert_not_called()

    @pytest.mark.asyncio
    async def test_metric_count_matches_drops(self, small_tracker):
        """Metric should be incremented once per drop."""
        with patch("progress.get_redis_pool", return_value=None):
            mock_metric = MagicMock()
            with patch("metrics.SSE_QUEUE_DROPS", mock_metric):
                # Fill + 3 overflows
                for i in range(6):
                    await small_tracker.emit("fetching", i * 10, f"msg-{i}")

                assert mock_metric.inc.call_count == 3


class TestEventHistoryIntegrity:
    """Verify event_history still works correctly with bounded queue."""

    @pytest.mark.asyncio
    async def test_event_history_contains_all_events(self, small_tracker):
        """Event history should contain ALL events, even dropped ones."""
        with patch("progress.get_redis_pool", return_value=None):
            for i in range(6):
                await small_tracker.emit("fetching", i * 10, f"msg-{i}")

            # History keeps all (up to _REPLAY_MAX_EVENTS)
            assert len(small_tracker._event_history) == 6

    @pytest.mark.asyncio
    async def test_event_counter_increments_regardless(self, small_tracker):
        """Event counter should increment for every event, even dropped ones."""
        with patch("progress.get_redis_pool", return_value=None):
            for i in range(6):
                await small_tracker.emit("fetching", i * 10, f"msg-{i}")

            assert small_tracker._event_counter == 6
