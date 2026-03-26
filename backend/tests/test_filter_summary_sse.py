"""STORY-327 AC5+AC6: Tests for filter_summary SSE event.

AC5: Backend emits filter_summary event with breakdown after filtering.
AC6: Integration test: 100 raw → 15 filtered → verify counters.
"""

import json

import pytest

from progress import (
    ProgressTracker,
    _active_trackers,
)


@pytest.fixture(autouse=True)
def cleanup_trackers():
    """Clean up global tracker registry after each test."""
    yield
    _active_trackers.clear()


class TestEmitFilterSummary:
    """AC5: emit_filter_summary() emits correct SSE event."""

    @pytest.mark.asyncio
    async def test_emits_filter_summary_event(self):
        """filter_summary event contains total_raw, total_filtered, rejection breakdown."""
        tracker = ProgressTracker("test-fs-001", uf_count=3, use_redis=False)

        await tracker.emit_filter_summary(
            total_raw=100,
            total_filtered=15,
            rejected_keyword=50,
            rejected_value=30,
            rejected_llm=5,
        )

        event = await tracker.queue.get()
        assert event.stage == "filter_summary"
        assert event.progress == 70
        assert "15 relevantes de 100 analisadas" in event.message
        assert event.detail["total_raw"] == 100
        assert event.detail["total_filtered"] == 15
        assert event.detail["rejected_keyword"] == 50
        assert event.detail["rejected_value"] == 30
        assert event.detail["rejected_llm"] == 5

    @pytest.mark.asyncio
    async def test_emits_with_filter_stats_dict(self):
        """filter_stats dict adds rejection details to event."""
        tracker = ProgressTracker("test-fs-002", uf_count=1, use_redis=False)
        stats = {
            "rejeitadas_uf": 10,
            "rejeitadas_status": 5,
            "rejeitadas_outros": 3,
            "rejeitadas_keyword": 20,
            "rejeitadas_valor": 12,
        }

        await tracker.emit_filter_summary(
            total_raw=50,
            total_filtered=0,
            rejected_keyword=20,
            rejected_value=12,
            filter_stats=stats,
        )

        event = await tracker.queue.get()
        assert event.detail["rejected_uf"] == 10
        assert event.detail["rejected_status"] == 5
        assert event.detail["rejected_outros"] == 3

    @pytest.mark.asyncio
    async def test_emits_without_filter_stats(self):
        """Works when filter_stats is None (defaults to 0)."""
        tracker = ProgressTracker("test-fs-003", uf_count=1, use_redis=False)

        await tracker.emit_filter_summary(
            total_raw=80,
            total_filtered=25,
        )

        event = await tracker.queue.get()
        assert event.detail["total_raw"] == 80
        assert event.detail["total_filtered"] == 25
        assert event.detail["rejected_keyword"] == 0
        assert event.detail["rejected_value"] == 0

    @pytest.mark.asyncio
    async def test_zero_filtered_results(self):
        """When 0 results pass filtering, message still includes counts."""
        tracker = ProgressTracker("test-fs-004", uf_count=5, use_redis=False)

        await tracker.emit_filter_summary(
            total_raw=200,
            total_filtered=0,
            rejected_keyword=180,
            rejected_value=20,
        )

        event = await tracker.queue.get()
        assert event.detail["total_raw"] == 200
        assert event.detail["total_filtered"] == 0
        assert "0 relevantes de 200 analisadas" in event.message

    @pytest.mark.asyncio
    async def test_event_serialization(self):
        """filter_summary event serializes correctly via to_dict()."""
        tracker = ProgressTracker("test-fs-005", uf_count=1, use_redis=False)

        await tracker.emit_filter_summary(
            total_raw=100,
            total_filtered=15,
            rejected_keyword=50,
            rejected_value=30,
            rejected_llm=5,
        )

        event = await tracker.queue.get()
        d = event.to_dict()
        assert d["stage"] == "filter_summary"
        assert d["progress"] == 70
        assert d["detail"]["total_raw"] == 100
        assert d["detail"]["total_filtered"] == 15
        # Verify it's JSON-serializable
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["detail"]["rejected_keyword"] == 50

    @pytest.mark.asyncio
    async def test_is_not_terminal(self):
        """filter_summary is NOT a terminal event — stream continues after."""
        tracker = ProgressTracker("test-fs-006", uf_count=1, use_redis=False)

        await tracker.emit_filter_summary(total_raw=10, total_filtered=5)

        assert not tracker._is_complete, "filter_summary should not mark tracker as complete"

    @pytest.mark.asyncio
    async def test_event_counter_increments(self):
        """filter_summary event gets a monotonic event ID for replay."""
        tracker = ProgressTracker("test-fs-007", uf_count=1, use_redis=False)

        # Emit some events before filter_summary
        await tracker.emit("fetching", 30, "Buscando...")
        counter_before = tracker._event_counter

        await tracker.emit_filter_summary(total_raw=100, total_filtered=15)

        assert tracker._event_counter == counter_before + 1

    @pytest.mark.asyncio
    async def test_event_stored_in_history(self):
        """filter_summary event is stored in _event_history for replay."""
        tracker = ProgressTracker("test-fs-008", uf_count=1, use_redis=False)

        await tracker.emit_filter_summary(total_raw=100, total_filtered=15)

        assert len(tracker._event_history) == 1
        eid, data = tracker._event_history[0]
        assert data["stage"] == "filter_summary"
        assert data["detail"]["total_raw"] == 100


class TestFilterSummaryIntegration:
    """AC6: Integration test — simulate 100 raw → 15 filtered pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_filter_summary(self):
        """Simulate complete pipeline: fetch → filter → filter_summary → complete.

        Verifies:
        1. fetching events emitted during UF fetch
        2. filtering event emitted before filter
        3. filter_summary event with correct 100 raw / 15 filtered
        4. complete event terminates stream
        """
        tracker = ProgressTracker("test-integration-001", uf_count=3, use_redis=False)

        # Stage 1: Fetching UFs
        await tracker.emit_uf_complete("SP", 50)
        await tracker.emit_uf_complete("RJ", 30)
        await tracker.emit_uf_complete("MG", 20)

        # Stage 2: Filtering starts
        await tracker.emit("filtering", 60, "Aplicando filtros em 100 licitacoes...")

        # Stage 3: Filter summary (100 raw, 15 pass)
        stats = {
            "rejeitadas_uf": 0,
            "rejeitadas_keyword": 60,
            "rejeitadas_valor": 20,
            "rejeitadas_status": 5,
            "rejeitadas_outros": 0,
        }
        await tracker.emit_filter_summary(
            total_raw=100,
            total_filtered=15,
            rejected_keyword=60,
            rejected_value=20,
            rejected_llm=0,
            filter_stats=stats,
        )

        # Stage 4: Complete
        await tracker.emit("filtering", 70, "Filtragem concluida: 15 resultados")
        await tracker.emit_complete()

        # Drain all events
        events = []
        while not tracker.queue.empty():
            events.append(await tracker.queue.get())

        # Verify event sequence
        stages = [e.stage for e in events]
        assert "fetching" in stages
        assert "filtering" in stages
        assert "filter_summary" in stages
        assert "complete" in stages

        # Find filter_summary event
        fs_event = next(e for e in events if e.stage == "filter_summary")
        assert fs_event.detail["total_raw"] == 100
        assert fs_event.detail["total_filtered"] == 15
        assert fs_event.detail["rejected_keyword"] == 60
        assert fs_event.detail["rejected_value"] == 20
        assert fs_event.detail["rejected_uf"] == 0
        assert fs_event.detail["rejected_status"] == 5

        # Verify complete is terminal
        complete_event = next(e for e in events if e.stage == "complete")
        assert complete_event.progress == 100

    @pytest.mark.asyncio
    async def test_pipeline_zero_filtered(self):
        """Pipeline with 0 filtered results out of 100 raw."""
        tracker = ProgressTracker("test-integration-002", uf_count=1, use_redis=False)

        await tracker.emit_uf_complete("SP", 100)
        await tracker.emit("filtering", 60, "Aplicando filtros em 100 licitacoes...")
        await tracker.emit_filter_summary(
            total_raw=100,
            total_filtered=0,
            rejected_keyword=80,
            rejected_value=20,
        )
        await tracker.emit_complete()

        events = []
        while not tracker.queue.empty():
            events.append(await tracker.queue.get())

        fs_event = next(e for e in events if e.stage == "filter_summary")
        assert fs_event.detail["total_raw"] == 100
        assert fs_event.detail["total_filtered"] == 0
        assert "0 relevantes de 100" in fs_event.message
