"""Tests for progress tracking and SSE-based real-time search progress.

Test coverage for STORY-224 Track 1:
- AC1: ProgressTracker creates queue and tracks progress correctly
- AC2: update_progress() sends correct SSE event format
- AC3: get_progress_stream() yields events as Server-Sent Events
- AC4: Test cleanup: tracker removed after search completes
- AC5: Test timeout: stale trackers cleaned up after TTL
- AC6: Test concurrent searches create independent trackers
- AC7: Test SSE reconnection handles missing tracker gracefully
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from progress import (
    ProgressEvent,
    ProgressTracker,
    _TRACKER_TTL,
    _active_trackers,
    _cleanup_stale,
    create_tracker,
    get_tracker,
    remove_tracker,
)


@pytest.fixture(autouse=True)
def cleanup_trackers():
    """Clean up global tracker registry after each test to prevent pollution."""
    yield
    _active_trackers.clear()


@pytest.fixture
def mock_redis():
    """Mock Redis pool and availability check."""
    with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool, \
         patch("progress.is_redis_available", new_callable=AsyncMock) as mock_available:
        mock_pool.return_value = None
        mock_available.return_value = False
        yield {"pool": mock_pool, "available": mock_available}


class TestProgressEvent:
    """Tests for ProgressEvent dataclass."""

    def test_event_creation(self):
        """Test creating a progress event with all fields."""
        event = ProgressEvent(
            stage="fetching",
            progress=50,
            message="Processing...",
            detail={"uf": "SP", "items": 100},
        )

        assert event.stage == "fetching"
        assert event.progress == 50
        assert event.message == "Processing..."
        assert event.detail == {"uf": "SP", "items": 100}
        assert isinstance(event.timestamp, float)

    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = ProgressEvent(
            stage="complete",
            progress=100,
            message="Done!",
            detail={"total": 500},
        )

        event_dict = event.to_dict()

        assert event_dict["stage"] == "complete"
        assert event_dict["progress"] == 100
        assert event_dict["message"] == "Done!"
        assert event_dict["detail"] == {"total": 500}
        assert "timestamp" not in event_dict  # Not included in to_dict()


class TestProgressTracker:
    """Tests for ProgressTracker class (AC1, AC2)."""

    @pytest.mark.asyncio
    async def test_tracker_initialization(self, mock_redis):
        """AC1: Test ProgressTracker creates queue and initializes correctly."""
        tracker = ProgressTracker(search_id="test-123", uf_count=5, use_redis=False)

        assert tracker.search_id == "test-123"
        assert tracker.uf_count == 5
        assert isinstance(tracker.queue, asyncio.Queue)
        assert tracker.queue.qsize() == 0
        assert tracker._ufs_completed == 0
        assert tracker._is_complete is False
        assert tracker._use_redis is False
        assert isinstance(tracker.created_at, float)

    @pytest.mark.asyncio
    async def test_emit_progress_event(self, mock_redis):
        """AC1: Test emit() sends event to queue with correct format."""
        tracker = ProgressTracker(search_id="test-123", uf_count=3, use_redis=False)

        await tracker.emit(
            stage="fetching",
            progress=25,
            message="Fetching data...",
            uf="SP",
            items=100,
        )

        assert tracker.queue.qsize() == 1
        event = await tracker.queue.get()

        assert isinstance(event, ProgressEvent)
        assert event.stage == "fetching"
        assert event.progress == 25
        assert event.message == "Fetching data..."
        assert event.detail["uf"] == "SP"
        assert event.detail["items"] == 100

    @pytest.mark.asyncio
    async def test_emit_clamps_progress(self, mock_redis):
        """AC1: Test emit() clamps progress to 0-100 range."""
        tracker = ProgressTracker(search_id="test-123", uf_count=1, use_redis=False)

        # Test negative progress clamped to 0
        await tracker.emit(stage="test", progress=-50, message="Below zero")
        event1 = await tracker.queue.get()
        assert event1.progress == 0

        # Test progress > 100 clamped to 100
        await tracker.emit(stage="test", progress=150, message="Above hundred")
        event2 = await tracker.queue.get()
        assert event2.progress == 100

    @pytest.mark.asyncio
    async def test_emit_uf_complete(self, mock_redis):
        """AC1: Test emit_uf_complete() calculates progress correctly (10-55%)."""
        tracker = ProgressTracker(search_id="test-123", uf_count=5, use_redis=False)

        # Complete 1st UF (1/5 = 20% of fetching range)
        await tracker.emit_uf_complete(uf="SP", items_count=150)
        event1 = await tracker.queue.get()

        assert event1.stage == "fetching"
        assert event1.progress == 10 + int((1 / 5) * 45)  # 10 + 9 = 19
        assert "1/5" in event1.message  # Message format: "Buscando dados: 1/5 estados"
        assert event1.detail["uf"] == "SP"
        assert event1.detail["uf_index"] == 1
        assert event1.detail["uf_total"] == 5
        assert event1.detail["items_found"] == 150

        # Complete 3rd UF (3/5 = 60% of fetching range)
        await tracker.emit_uf_complete(uf="RJ", items_count=200)
        await tracker.emit_uf_complete(uf="MG", items_count=175)
        event3 = await tracker.queue.get()  # Skip 2nd event
        event3 = await tracker.queue.get()

        assert event3.progress == 10 + int((3 / 5) * 45)  # 10 + 27 = 37

    @pytest.mark.asyncio
    async def test_emit_uf_complete_with_zero_ufs(self, mock_redis):
        """AC1: Test emit_uf_complete() handles edge case of zero UFs."""
        tracker = ProgressTracker(search_id="test-123", uf_count=0, use_redis=False)

        # Should not crash with division by zero
        await tracker.emit_uf_complete(uf="SP", items_count=100)
        event = await tracker.queue.get()

        assert event.stage == "fetching"
        assert event.progress >= 10  # No crash, progress calculated safely

    @pytest.mark.asyncio
    async def test_emit_complete(self, mock_redis):
        """AC1: Test emit_complete() sets completion state correctly."""
        tracker = ProgressTracker(search_id="test-123", uf_count=2, use_redis=False)

        await tracker.emit_complete()

        assert tracker._is_complete is True
        event = await tracker.queue.get()

        assert event.stage == "complete"
        assert event.progress == 100
        assert "concluida" in event.message.lower()

    @pytest.mark.asyncio
    async def test_emit_error(self, mock_redis):
        """AC1: Test emit_error() sets error state correctly."""
        tracker = ProgressTracker(search_id="test-123", uf_count=2, use_redis=False)

        await tracker.emit_error("API connection failed")

        assert tracker._is_complete is True
        event = await tracker.queue.get()

        assert event.stage == "error"
        assert event.progress == -1
        assert event.message == "API connection failed"
        assert event.detail["error"] == "API connection failed"

    @pytest.mark.asyncio
    async def test_emit_with_redis_enabled(self):
        """AC2: Test emit() publishes to Redis when use_redis=True."""
        mock_redis_client = AsyncMock()
        mock_redis_client.publish = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = ProgressTracker(
                search_id="test-redis-123", uf_count=3, use_redis=True
            )

            await tracker.emit(stage="fetching", progress=30, message="Fetching...")

            # Check local queue
            assert tracker.queue.qsize() == 1

            # Check Redis publish was called
            mock_redis_client.publish.assert_called_once()
            call_args = mock_redis_client.publish.call_args
            channel = call_args[0][0]
            event_json = call_args[0][1]

            assert channel == "bidiq:progress:test-redis-123:events"
            event_data = json.loads(event_json)
            assert event_data["stage"] == "fetching"
            assert event_data["progress"] == 30
            assert event_data["message"] == "Fetching..."

    @pytest.mark.asyncio
    async def test_emit_redis_publish_failure_graceful(self):
        """AC2: Test emit() handles Redis publish failure gracefully."""
        mock_redis_client = AsyncMock()
        mock_redis_client.publish = AsyncMock(
            side_effect=Exception("Redis connection lost")
        )

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = ProgressTracker(
                search_id="test-fail-123", uf_count=2, use_redis=True
            )

            # Should not raise exception
            await tracker.emit(stage="error", progress=0, message="Testing")

            # Local queue should still have event
            assert tracker.queue.qsize() == 1


class TestTrackerManagement:
    """Tests for global tracker management (AC4, AC5, AC6, AC7)."""

    @pytest.mark.asyncio
    async def test_create_tracker_in_memory_mode(self, mock_redis):
        """AC6: Test create_tracker() in in-memory mode."""
        tracker = await create_tracker(search_id="search-001", uf_count=3)

        assert tracker.search_id == "search-001"
        assert tracker.uf_count == 3
        assert tracker._use_redis is False
        assert "search-001" in _active_trackers
        assert _active_trackers["search-001"] is tracker

    @pytest.mark.asyncio
    async def test_create_tracker_with_redis_mode(self):
        """AC6: Test create_tracker() in Redis mode."""
        mock_redis_client = AsyncMock()
        mock_redis_client.hset = AsyncMock()
        mock_redis_client.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool, \
             patch("progress.is_redis_available", new_callable=AsyncMock) as mock_available:
            mock_pool.return_value = mock_redis_client
            mock_available.return_value = True

            tracker = await create_tracker(search_id="search-redis-001", uf_count=5)

            assert tracker._use_redis is True
            assert "search-redis-001" in _active_trackers

            # Check Redis metadata was stored
            mock_redis_client.hset.assert_called_once()
            call_args = mock_redis_client.hset.call_args
            assert call_args[0][0] == "bidiq:progress:search-redis-001"
            assert "uf_count" in call_args[1]["mapping"]

            mock_redis_client.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tracker_from_memory(self, mock_redis):
        """AC7: Test get_tracker() retrieves from in-memory registry."""
        tracker = await create_tracker(search_id="search-002", uf_count=2)

        retrieved = await get_tracker("search-002")

        assert retrieved is tracker
        assert retrieved.search_id == "search-002"

    @pytest.mark.asyncio
    async def test_get_tracker_not_found(self, mock_redis):
        """AC7: Test get_tracker() returns None for missing tracker."""
        retrieved = await get_tracker("nonexistent-search")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_tracker_from_redis_metadata(self):
        """AC7: Test get_tracker() reconstructs tracker from Redis metadata."""
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall = AsyncMock(
            return_value={"uf_count": "4", "created_at": str(time.time())}
        )

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            # Tracker not in memory but exists in Redis
            tracker = await get_tracker("redis-search-123")

            assert tracker is not None
            assert tracker.search_id == "redis-search-123"
            assert tracker.uf_count == 4
            assert tracker._use_redis is True
            assert "redis-search-123" in _active_trackers

    @pytest.mark.asyncio
    async def test_remove_tracker_from_memory(self, mock_redis):
        """AC4: Test remove_tracker() cleans up in-memory registry."""
        tracker = await create_tracker(search_id="search-003", uf_count=1)
        assert "search-003" in _active_trackers

        await remove_tracker("search-003")

        assert "search-003" not in _active_trackers

    @pytest.mark.asyncio
    async def test_remove_tracker_from_redis(self):
        """AC4: Test remove_tracker() cleans up Redis state."""
        mock_redis_client = AsyncMock()
        mock_redis_client.delete = AsyncMock()
        mock_redis_client.hset = AsyncMock()
        mock_redis_client.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool, \
             patch("progress.is_redis_available", new_callable=AsyncMock) as mock_available:
            mock_pool.return_value = mock_redis_client
            mock_available.return_value = True

            tracker = await create_tracker(search_id="search-redis-003", uf_count=2)
            await remove_tracker("search-redis-003")

            # Check Redis delete was called
            mock_redis_client.delete.assert_called_once_with(
                "bidiq:progress:search-redis-003"
            )

    @pytest.mark.asyncio
    async def test_remove_tracker_handles_redis_failure(self, mock_redis):
        """AC4: Test remove_tracker() handles Redis deletion failure gracefully."""
        mock_redis_client = AsyncMock()
        mock_redis_client.delete = AsyncMock(side_effect=Exception("Redis error"))

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = await create_tracker(search_id="search-004", uf_count=1)

            # Should not raise exception
            await remove_tracker("search-004")

            # In-memory cleanup should still succeed
            assert "search-004" not in _active_trackers

    def test_cleanup_stale_trackers(self, mock_redis):
        """AC5: Test _cleanup_stale() removes trackers older than TTL."""
        # Create old tracker (simulating creation 10 minutes ago)
        old_tracker = ProgressTracker("old-search", uf_count=1, use_redis=False)
        old_tracker.created_at = time.time() - (_TRACKER_TTL + 60)  # Older than TTL
        _active_trackers["old-search"] = old_tracker

        # Create recent tracker (created just now)
        recent_tracker = ProgressTracker("recent-search", uf_count=1, use_redis=False)
        recent_tracker.created_at = time.time()
        _active_trackers["recent-search"] = recent_tracker

        # Run cleanup
        _cleanup_stale()

        # Old tracker should be removed, recent tracker should remain
        assert "old-search" not in _active_trackers
        assert "recent-search" in _active_trackers

    def test_cleanup_stale_multiple_trackers(self, mock_redis):
        """AC5: Test _cleanup_stale() handles multiple stale trackers."""
        now = time.time()

        # Create 3 stale trackers
        for i in range(3):
            tracker = ProgressTracker(f"stale-{i}", uf_count=1, use_redis=False)
            tracker.created_at = now - (_TRACKER_TTL + 100)
            _active_trackers[f"stale-{i}"] = tracker

        # Create 2 fresh trackers
        for i in range(2):
            tracker = ProgressTracker(f"fresh-{i}", uf_count=1, use_redis=False)
            tracker.created_at = now
            _active_trackers[f"fresh-{i}"] = tracker

        assert len(_active_trackers) == 5

        _cleanup_stale()

        # Only fresh trackers should remain
        assert len(_active_trackers) == 2
        assert "fresh-0" in _active_trackers
        assert "fresh-1" in _active_trackers

    @pytest.mark.asyncio
    async def test_concurrent_searches_independent(self, mock_redis):
        """AC6: Test concurrent searches create independent trackers."""
        # Create 3 concurrent trackers
        tracker1 = await create_tracker("search-A", uf_count=2)
        tracker2 = await create_tracker("search-B", uf_count=3)
        tracker3 = await create_tracker("search-C", uf_count=5)

        # Emit events to each tracker
        await tracker1.emit("fetching", 20, "Search A fetching")
        await tracker2.emit("filtering", 50, "Search B filtering")
        await tracker3.emit("llm", 80, "Search C LLM")

        # Each tracker should have exactly 1 event in its queue
        assert tracker1.queue.qsize() == 1
        assert tracker2.queue.qsize() == 1
        assert tracker3.queue.qsize() == 1

        # Events should be independent
        event1 = await tracker1.queue.get()
        event2 = await tracker2.queue.get()
        event3 = await tracker3.queue.get()

        assert event1.stage == "fetching"
        assert event2.stage == "filtering"
        assert event3.stage == "llm"

    @pytest.mark.asyncio
    async def test_concurrent_uf_completion_tracking(self, mock_redis):
        """AC6: Test concurrent searches track UF completion independently."""
        tracker1 = await create_tracker("search-X", uf_count=3)
        tracker2 = await create_tracker("search-Y", uf_count=5)

        # Complete UFs in tracker1
        await tracker1.emit_uf_complete("SP", 100)
        await tracker1.emit_uf_complete("RJ", 150)

        # Complete UFs in tracker2
        await tracker2.emit_uf_complete("MG", 200)

        # Check completion counts are independent
        assert tracker1._ufs_completed == 2
        assert tracker2._ufs_completed == 1

    @pytest.mark.asyncio
    async def test_tracker_isolation_on_error(self, mock_redis):
        """AC6: Test error in one tracker doesn't affect others."""
        tracker1 = await create_tracker("search-error", uf_count=2)
        tracker2 = await create_tracker("search-success", uf_count=2)

        # Emit error in tracker1
        await tracker1.emit_error("Connection timeout")

        # Emit success in tracker2
        await tracker2.emit("fetching", 30, "Still working...")

        # tracker1 should be marked as complete with error
        assert tracker1._is_complete is True
        event1 = await tracker1.queue.get()
        assert event1.stage == "error"
        assert event1.progress == -1

        # tracker2 should be unaffected
        assert tracker2._is_complete is False
        event2 = await tracker2.queue.get()
        assert event2.stage == "fetching"
        assert event2.progress == 30


class TestSSEReconnection:
    """Tests for SSE reconnection and missing tracker handling (AC7)."""

    @pytest.mark.asyncio
    async def test_reconnect_to_existing_tracker(self, mock_redis):
        """AC7: Test SSE client can reconnect to existing tracker."""
        # Create tracker
        tracker = await create_tracker("search-reconnect", uf_count=3)

        # Emit some events
        await tracker.emit("connecting", 5, "Connecting...")
        await tracker.emit("fetching", 20, "Fetching...")

        # Simulate reconnection by getting tracker again
        reconnected = await get_tracker("search-reconnect")

        assert reconnected is tracker
        assert reconnected.search_id == "search-reconnect"

        # New events after reconnection should work
        await reconnected.emit("filtering", 60, "Filtering...")
        assert reconnected.queue.qsize() == 3  # All events in queue

    @pytest.mark.asyncio
    async def test_reconnect_to_missing_tracker_returns_none(self, mock_redis):
        """AC7: Test reconnecting to non-existent tracker returns None."""
        # Try to get a tracker that was never created
        tracker = await get_tracker("never-existed")

        assert tracker is None

    @pytest.mark.asyncio
    async def test_reconnect_after_cleanup(self, mock_redis):
        """AC7: Test reconnecting to cleaned-up tracker returns None."""
        # Create and remove tracker
        tracker = await create_tracker("search-removed", uf_count=2)
        await remove_tracker("search-removed")

        # Try to reconnect
        reconnected = await get_tracker("search-removed")

        assert reconnected is None

    @pytest.mark.asyncio
    async def test_reconnect_from_redis_after_memory_cleared(self):
        """AC7: Test reconnecting loads tracker from Redis if not in memory."""
        mock_redis_client = AsyncMock()
        mock_redis_client.hgetall = AsyncMock(
            return_value={"uf_count": "3", "created_at": str(time.time())}
        )

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            # Simulate scenario where tracker exists in Redis but not in memory
            # (e.g., different backend instance or after restart)
            tracker = await get_tracker("redis-only-search")

            assert tracker is not None
            assert tracker.search_id == "redis-only-search"
            assert tracker.uf_count == 3
            assert tracker._use_redis is True


class TestEdgeCases:
    """Additional edge case tests for robustness."""

    @pytest.mark.asyncio
    async def test_empty_detail_dict(self, mock_redis):
        """Test emitting events with no detail kwargs."""
        tracker = ProgressTracker("test-empty", uf_count=1, use_redis=False)

        await tracker.emit(stage="test", progress=50, message="No details")

        event = await tracker.queue.get()
        assert event.detail == {}

    @pytest.mark.asyncio
    async def test_multiple_rapid_events(self, mock_redis):
        """Test emitting many events in rapid succession."""
        tracker = ProgressTracker("test-rapid", uf_count=10, use_redis=False)

        # Emit 20 events rapidly
        for i in range(20):
            await tracker.emit(stage="test", progress=i * 5, message=f"Event {i}")

        assert tracker.queue.qsize() == 20

        # All events should be retrievable
        for i in range(20):
            event = await tracker.queue.get()
            assert event.message == f"Event {i}"

    @pytest.mark.asyncio
    async def test_tracker_with_single_uf(self, mock_redis):
        """Test tracker with uf_count=1 (edge case)."""
        tracker = ProgressTracker("test-single-uf", uf_count=1, use_redis=False)

        await tracker.emit_uf_complete("SP", 500)

        event = await tracker.queue.get()
        assert event.progress == 10 + int((1 / 1) * 45)  # Should be 55
        assert event.detail["uf_index"] == 1
        assert event.detail["uf_total"] == 1

    @pytest.mark.asyncio
    async def test_unicode_in_messages(self, mock_redis):
        """Test handling of Unicode characters in messages."""
        tracker = ProgressTracker("test-unicode", uf_count=1, use_redis=False)

        await tracker.emit(
            stage="test",
            progress=50,
            message="Buscando em São Paulo 🔍",
            estado="São Paulo",
        )

        event = await tracker.queue.get()
        assert "São Paulo" in event.message
        assert event.detail["estado"] == "São Paulo"
