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
from unittest.mock import AsyncMock, patch

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
        """AC2: Test emit() publishes to Redis Stream when use_redis=True."""
        mock_redis_client = AsyncMock()
        mock_redis_client.xadd = AsyncMock(return_value="1-0")
        mock_redis_client.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = ProgressTracker(
                search_id="test-redis-123", uf_count=3, use_redis=True
            )

            await tracker.emit(stage="fetching", progress=30, message="Fetching...")

            # Check local queue
            assert tracker.queue.qsize() == 1

            # Check Redis XADD was called (STORY-276)
            mock_redis_client.xadd.assert_called_once()
            call_args = mock_redis_client.xadd.call_args
            stream_key = call_args[0][0]
            fields = call_args[0][1]

            assert stream_key == "smartlic:progress:test-redis-123:stream"
            assert fields["stage"] == "fetching"
            assert fields["progress"] == "30"
            assert fields["message"] == "Fetching..."
            assert "detail_json" in fields

            # Non-terminal event should NOT set EXPIRE on stream key
            # STORY-297: Replay list EXPIRE is always called, but stream EXPIRE only on terminal
            stream_expire_calls = [
                c for c in mock_redis_client.expire.call_args_list
                if c[0][0].endswith(":stream")
            ]
            assert len(stream_expire_calls) == 0

    @pytest.mark.asyncio
    async def test_emit_redis_publish_failure_graceful(self):
        """AC2: Test emit() handles Redis Stream failure gracefully."""
        mock_redis_client = AsyncMock()
        mock_redis_client.xadd = AsyncMock(
            side_effect=Exception("Redis connection lost")
        )

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = ProgressTracker(
                search_id="test-fail-123", uf_count=2, use_redis=True
            )

            # Should not raise exception
            await tracker.emit(stage="fetching", progress=0, message="Testing")

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
            assert call_args[0][0] == "smartlic:progress:search-redis-001"
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
        await create_tracker(search_id="search-003", uf_count=1)
        assert "search-003" in _active_trackers

        await remove_tracker("search-003")

        assert "search-003" not in _active_trackers

    @pytest.mark.asyncio
    async def test_remove_tracker_from_redis(self):
        """AC4: Test remove_tracker() cleans up Redis state (metadata + stream)."""
        mock_redis_client = AsyncMock()
        mock_redis_client.delete = AsyncMock()
        mock_redis_client.hset = AsyncMock()
        mock_redis_client.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool, \
             patch("progress.is_redis_available", new_callable=AsyncMock) as mock_available:
            mock_pool.return_value = mock_redis_client
            mock_available.return_value = True

            await create_tracker(search_id="search-redis-003", uf_count=2)
            await remove_tracker("search-redis-003")

            # STORY-276: Check Redis delete was called for BOTH metadata and stream keys
            mock_redis_client.delete.assert_called_once_with(
                "smartlic:progress:search-redis-003",
                "smartlic:progress:search-redis-003:stream",
            )

    @pytest.mark.asyncio
    async def test_remove_tracker_handles_redis_failure(self, mock_redis):
        """AC4: Test remove_tracker() handles Redis deletion failure gracefully."""
        mock_redis_client = AsyncMock()
        mock_redis_client.delete = AsyncMock(side_effect=Exception("Redis error"))

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            await create_tracker(search_id="search-004", uf_count=1)

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
        await create_tracker("search-removed", uf_count=2)
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


class TestHarden017PartialDataReplay:
    """HARDEN-017: partial_data events excluded from replay history."""

    @pytest.mark.asyncio
    async def test_partial_data_excluded_from_event_history(self, mock_redis):
        """AC2/AC4: partial_data events must NOT appear in _event_history."""
        tracker = ProgressTracker("test-h017", uf_count=3, use_redis=False)

        # Emit a normal event, then partial_data, then another normal event
        await tracker.emit("fetching", 20, "Fetching...")
        await tracker.emit_partial_data(
            licitacoes=[{"id": "1", "titulo": "x" * 5000}],
            batch_index=1,
            ufs_completed=["SP"],
            is_final=False,
        )
        await tracker.emit("filtering", 60, "Filtering...")

        # All 3 events should be in queue (AC3: real-time SSE works)
        assert tracker.queue.qsize() == 3

        # But only 2 events in replay history (partial_data excluded)
        assert len(tracker._event_history) == 2
        stages_in_history = [data["stage"] for _, data in tracker._event_history]
        assert "partial_data" not in stages_in_history
        assert "fetching" in stages_in_history
        assert "filtering" in stages_in_history

    @pytest.mark.asyncio
    async def test_partial_data_not_in_get_events_after(self, mock_redis):
        """AC4: get_events_after() never returns partial_data."""
        tracker = ProgressTracker("test-h017-replay", uf_count=2, use_redis=False)

        await tracker.emit("connecting", 5, "Connecting...")
        await tracker.emit_partial_data(
            licitacoes=[{"id": "big"}],
            batch_index=1,
            ufs_completed=["RJ"],
        )
        await tracker.emit_complete()

        replayed = tracker.get_events_after(0)
        replayed_stages = [data["stage"] for _, data in replayed]
        assert "partial_data" not in replayed_stages
        assert "connecting" in replayed_stages
        assert "complete" in replayed_stages

    @pytest.mark.asyncio
    async def test_replay_max_events_is_200(self, mock_redis):
        """AC1: _REPLAY_MAX_EVENTS must be 200."""
        from progress import _REPLAY_MAX_EVENTS
        assert _REPLAY_MAX_EVENTS == 200

    @pytest.mark.asyncio
    async def test_partial_data_still_emitted_via_queue(self, mock_redis):
        """AC3: partial_data events must still reach the queue for real-time SSE."""
        tracker = ProgressTracker("test-h017-queue", uf_count=1, use_redis=False)

        await tracker.emit_partial_data(
            licitacoes=[{"id": "1"}, {"id": "2"}],
            batch_index=1,
            ufs_completed=["SP"],
            is_final=True,
        )

        assert tracker.queue.qsize() == 1
        event = await tracker.queue.get()
        assert event.stage == "partial_data"
        assert event.detail["total_items"] == 2


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


class TestEmitDegraded:
    """Tests for emit_degraded() method - degraded state handling."""

    @pytest.mark.asyncio
    async def test_emit_degraded_sets_complete_and_stage(self, mock_redis):
        """AC11: emit_degraded() sets stage=degraded, progress=100, _is_complete=True."""
        tracker = ProgressTracker(search_id="test-degraded", uf_count=3, use_redis=False)

        await tracker.emit_degraded(
            reason="timeout",
            detail={"cache_age_hours": 2.3}
        )

        # Check completion state
        assert tracker._is_complete is True

        # Check event
        event = await tracker.queue.get()
        assert event.stage == "degraded"
        assert event.progress == 100
        assert event.detail["reason"] == "timeout"
        assert event.detail["cache_age_hours"] == 2.3

    @pytest.mark.asyncio
    async def test_emit_degraded_message_with_cache_age(self, mock_redis):
        """Test degraded message contains cache age when provided."""
        tracker = ProgressTracker(search_id="test-cache-age", uf_count=2, use_redis=False)

        await tracker.emit_degraded(
            reason="timeout",
            detail={"cache_age_hours": 2.3}
        )

        event = await tracker.queue.get()
        assert "2h atrás" in event.message.lower()

    @pytest.mark.asyncio
    async def test_emit_degraded_message_partial(self, mock_redis):
        """Test degraded message shows partial coverage when reason=partial."""
        tracker = ProgressTracker(search_id="test-partial", uf_count=5, use_redis=False)

        await tracker.emit_degraded(
            reason="partial",
            detail={"coverage_pct": 78}
        )

        event = await tracker.queue.get()
        assert "parciais" in event.message.lower() or "parcial" in event.message.lower()
        assert "78%" in event.message

    @pytest.mark.asyncio
    async def test_emit_degraded_publishes_to_redis(self):
        """Test emit_degraded() publishes to Redis Stream when use_redis=True."""
        mock_redis_client = AsyncMock()
        mock_redis_client.xadd = AsyncMock(return_value="1-0")
        mock_redis_client.expire = AsyncMock()

        with patch("progress.get_redis_pool", new_callable=AsyncMock) as mock_pool:
            mock_pool.return_value = mock_redis_client

            tracker = ProgressTracker(
                search_id="test-degraded-redis", uf_count=3, use_redis=True
            )

            await tracker.emit_degraded(
                reason="timeout",
                detail={"cache_age_hours": 1.5}
            )

            # Check local queue
            assert tracker.queue.qsize() == 1

            # STORY-276: Check Redis XADD was called
            mock_redis_client.xadd.assert_called_once()
            call_args = mock_redis_client.xadd.call_args
            stream_key = call_args[0][0]
            fields = call_args[0][1]

            assert stream_key == "smartlic:progress:test-degraded-redis:stream"
            assert fields["stage"] == "degraded"
            assert fields["progress"] == "100"
            detail = json.loads(fields["detail_json"])
            assert detail["reason"] == "timeout"
            assert detail["cache_age_hours"] == 1.5

            # Terminal event should set EXPIRE on stream key
            # STORY-297: Also sets EXPIRE on replay list, so expect 2 calls
            stream_expire_calls = [
                c for c in mock_redis_client.expire.call_args_list
                if c[0][0].endswith(":stream")
            ]
            assert len(stream_expire_calls) == 1


class TestHarden019DbFallback:
    """HARDEN-019: Last-Event-ID fallback to DB state when Redis expired."""

    @pytest.mark.asyncio
    async def test_ac1_is_search_terminal_falls_back_to_db_when_redis_empty(self, mock_redis):
        """AC1: is_search_terminal() falls back to DB when Redis replay is empty."""
        from progress import is_search_terminal

        # No local tracker, no Redis data → should query DB
        mock_db_state = {
            "to_state": "completed",
            "details": {"reason": "all sources done"},
        }
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state) as mock_get:
            result = await is_search_terminal("expired-search-001")

            mock_get.assert_called_once_with("expired-search-001")
            assert result is not None
            assert result["stage"] == "complete"
            assert result["progress"] == 100
            assert result["detail"]["source"] == "db_fallback"
            assert result["detail"]["db_state"] == "completed"

    @pytest.mark.asyncio
    async def test_ac2_db_completed_maps_to_sse_complete(self, mock_redis):
        """AC2: DB state 'completed' maps to SSE stage 'complete'."""
        from progress import is_search_terminal

        mock_db_state = {"to_state": "completed", "details": {}}
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("db-completed-search")

            assert result["stage"] == "complete"
            assert result["progress"] == 100
            assert "concluida" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_ac2_db_failed_maps_to_sse_error(self, mock_redis):
        """AC2: DB state 'failed' maps to SSE stage 'error'."""
        from progress import is_search_terminal

        mock_db_state = {
            "to_state": "failed",
            "details": {"error_message": "Pipeline timeout exceeded"},
        }
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("db-failed-search")

            assert result["stage"] == "error"
            assert result["progress"] == -1
            assert "Pipeline timeout exceeded" in result["message"]

    @pytest.mark.asyncio
    async def test_ac2_db_timed_out_maps_to_sse_error(self, mock_redis):
        """AC2: DB state 'timed_out' maps to SSE stage 'error'."""
        from progress import is_search_terminal

        mock_db_state = {
            "to_state": "timed_out",
            "details": {"reason": "Pipeline timeout exceeded"},
        }
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("db-timeout-search")

            assert result["stage"] == "error"
            assert result["progress"] == -1
            assert result["detail"]["db_state"] == "timed_out"

    @pytest.mark.asyncio
    async def test_ac2_db_rate_limited_maps_to_sse_error(self, mock_redis):
        """AC2: DB state 'rate_limited' maps to SSE stage 'error'."""
        from progress import is_search_terminal

        mock_db_state = {"to_state": "rate_limited", "details": {"retry_after": 60}}
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("db-ratelimit-search")

            assert result["stage"] == "error"
            assert result["progress"] == -1
            assert result["detail"]["db_state"] == "rate_limited"

    @pytest.mark.asyncio
    async def test_ac3_synthetic_event_contains_db_data(self, mock_redis):
        """AC3: Client receives synthetic terminal event with DB details."""
        from progress import is_search_terminal

        mock_db_state = {
            "to_state": "completed",
            "details": {"total_results": 42, "sector": "construcao"},
        }
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("db-data-search")

            assert result["detail"]["source"] == "db_fallback"
            assert result["detail"]["total_results"] == 42
            assert result["detail"]["sector"] == "construcao"
            assert result["detail"]["db_state"] == "completed"

    @pytest.mark.asyncio
    async def test_ac4_redis_expired_db_complete_scenario(self):
        """AC4: Full scenario — Redis expired, DB shows completed."""
        from progress import is_search_terminal

        # Redis available but replay list empty (expired)
        mock_redis_client = AsyncMock()
        mock_redis_client.lrange = AsyncMock(return_value=[])

        mock_db_state = {
            "to_state": "completed",
            "details": {"reason": "all sources done"},
        }

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_client), \
             patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("redis-expired-search")

            # Redis was checked (lrange called)
            mock_redis_client.lrange.assert_called_once()
            # DB fallback was used
            assert result is not None
            assert result["stage"] == "complete"
            assert result["detail"]["source"] == "db_fallback"

    @pytest.mark.asyncio
    async def test_ac4_redis_expired_db_failed_scenario(self):
        """AC4: Full scenario — Redis expired, DB shows failed."""
        from progress import is_search_terminal

        mock_redis_client = AsyncMock()
        mock_redis_client.lrange = AsyncMock(return_value=[])

        mock_db_state = {
            "to_state": "failed",
            "details": {"error_message": "PNCP API down"},
        }

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_client), \
             patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("redis-expired-failed")

            assert result["stage"] == "error"
            assert "PNCP API down" in result["message"]

    @pytest.mark.asyncio
    async def test_db_non_terminal_state_returns_none(self, mock_redis):
        """DB state 'fetching' (non-terminal) should return None."""
        from progress import is_search_terminal

        mock_db_state = {"to_state": "fetching", "details": {}}
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("still-processing")

            assert result is None

    @pytest.mark.asyncio
    async def test_db_returns_none_when_no_state(self, mock_redis):
        """DB returns None (search_id not found) → is_search_terminal returns None."""
        from progress import is_search_terminal

        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=None):
            result = await is_search_terminal("unknown-search")

            assert result is None

    @pytest.mark.asyncio
    async def test_db_fallback_exception_returns_none(self, mock_redis):
        """DB query failure should not crash — returns None gracefully."""
        from progress import is_search_terminal

        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, side_effect=Exception("DB down")):
            result = await is_search_terminal("db-error-search")

            assert result is None

    @pytest.mark.asyncio
    async def test_ac5_local_tracker_still_takes_priority(self, mock_redis):
        """AC5: Local tracker with terminal event should NOT trigger DB fallback."""
        from progress import is_search_terminal

        # Create a tracker with a terminal event in history
        tracker = ProgressTracker("local-terminal", uf_count=1, use_redis=False)
        await tracker.emit_complete()
        _active_trackers["local-terminal"] = tracker

        with patch("search_state_manager.get_current_state", new_callable=AsyncMock) as mock_db:
            result = await is_search_terminal("local-terminal")

            # Should use local tracker, NOT call DB
            mock_db.assert_not_called()
            assert result is not None
            assert result["stage"] == "complete"

    @pytest.mark.asyncio
    async def test_ac5_redis_data_still_takes_priority(self):
        """AC5: Redis replay with terminal event should NOT trigger DB fallback."""
        from progress import is_search_terminal

        terminal_event = json.dumps({
            "id": 5,
            "data": {"stage": "complete", "progress": 100, "message": "Done", "detail": {}},
        })
        mock_redis_client = AsyncMock()
        mock_redis_client.lrange = AsyncMock(return_value=[terminal_event])

        with patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis_client), \
             patch("search_state_manager.get_current_state", new_callable=AsyncMock) as mock_db:
            result = await is_search_terminal("redis-terminal")

            mock_db.assert_not_called()
            assert result is not None
            assert result["stage"] == "complete"

    @pytest.mark.asyncio
    async def test_failed_with_empty_details_uses_fallback_message(self, mock_redis):
        """Error event with empty details uses fallback message."""
        from progress import is_search_terminal

        mock_db_state = {"to_state": "failed", "details": {}}
        with patch("search_state_manager.get_current_state", new_callable=AsyncMock, return_value=mock_db_state):
            result = await is_search_terminal("empty-details")

            assert result["stage"] == "error"
            assert "failed" in result["message"].lower()
