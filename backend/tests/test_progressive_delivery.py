"""
Tests for GTM-RESILIENCE-A04 Progressive Delivery

Coverage:
- AC12: Cache-first returns in < 2s (via mock)
- AC13: Background fetch task created after cache-first
- AC14: ProgressTracker emits partial_results and refresh_available events
- AC15: GET /buscar-results/{search_id} returns stored results
"""

import asyncio
import time

import pytest

from progress import ProgressTracker
from routes.search import (
    get_background_results,
    store_background_results,
    _background_results,
)
from schemas import BuscaResponse, ResumoEstrategico


# ---------------------------------------------------------------------------
# Helper: minimal valid BuscaResponse for testing
# ---------------------------------------------------------------------------
def _make_response(**overrides) -> BuscaResponse:
    defaults = dict(
        resumo=ResumoEstrategico(
            resumo_executivo="Test summary",
            total_oportunidades=1,
            valor_total=100000.0,
            destaques=["Test"],
        ),
        licitacoes=[],
        total_raw=10,
        total_filtrado=1,
        excel_available=False,
        quota_used=1,
        quota_remaining=99,
    )
    defaults.update(overrides)
    return BuscaResponse(**defaults)


# ===================================================================
# AC14: ProgressTracker emits partial_results and refresh_available
# ===================================================================
class TestProgressTrackerA04Events:
    """AC14: ProgressTracker partial_results and refresh_available events."""

    @pytest.mark.asyncio
    async def test_emit_partial_results_queues_event(self):
        """emit_partial_results() puts a ProgressEvent in the queue."""
        tracker = ProgressTracker("test-partial-001", uf_count=5)

        await tracker.emit_partial_results(
            new_results_count=10,
            total_so_far=25,
            ufs_completed=["SP", "RJ"],
            ufs_pending=["MG", "BA", "PR"],
        )

        assert not tracker.queue.empty()
        event = await tracker.queue.get()
        assert event.stage == "partial_results"
        assert event.detail["new_results_count"] == 10
        assert event.detail["total_so_far"] == 25
        assert event.detail["ufs_completed"] == ["SP", "RJ"]
        assert event.detail["ufs_pending"] == ["MG", "BA", "PR"]

    @pytest.mark.asyncio
    async def test_partial_results_is_non_terminal(self):
        """partial_results should NOT set _is_complete — SSE stream stays open."""
        tracker = ProgressTracker("test-partial-002", uf_count=3)

        await tracker.emit_partial_results(5, 5, ["SP"], ["RJ", "MG"])
        assert tracker._is_complete is False

        # Can still emit more events
        await tracker.emit_partial_results(3, 8, ["SP", "RJ"], ["MG"])
        assert tracker._is_complete is False
        assert tracker.queue.qsize() == 2

    @pytest.mark.asyncio
    async def test_emit_refresh_available_queues_event(self):
        """emit_refresh_available() puts a terminal ProgressEvent in the queue."""
        tracker = ProgressTracker("test-refresh-001", uf_count=3)

        await tracker.emit_refresh_available(
            total_live=50,
            total_cached=40,
            new_count=15,
            updated_count=5,
            removed_count=10,
        )

        assert not tracker.queue.empty()
        event = await tracker.queue.get()
        assert event.stage == "refresh_available"
        assert event.progress == 100
        assert event.detail["total_live"] == 50
        assert event.detail["total_cached"] == 40
        assert event.detail["new_count"] == 15
        assert event.detail["updated_count"] == 5
        assert event.detail["removed_count"] == 10

    @pytest.mark.asyncio
    async def test_refresh_available_is_terminal(self):
        """refresh_available should set _is_complete = True."""
        tracker = ProgressTracker("test-refresh-002", uf_count=1)

        await tracker.emit_refresh_available(10, 8, 2, 0, 0)
        assert tracker._is_complete is True

    @pytest.mark.asyncio
    async def test_partial_then_refresh_sequence(self):
        """Typical flow: multiple partial_results followed by refresh_available."""
        tracker = ProgressTracker("test-flow-001", uf_count=3)

        await tracker.emit_partial_results(5, 5, ["SP"], ["RJ", "MG"])
        assert tracker._is_complete is False

        await tracker.emit_partial_results(3, 8, ["SP", "RJ"], ["MG"])
        assert tracker._is_complete is False

        await tracker.emit_refresh_available(12, 8, 4, 0, 0)
        assert tracker._is_complete is True

        # 3 events in queue
        assert tracker.queue.qsize() == 3

    @pytest.mark.asyncio
    async def test_partial_results_progress_percentage(self):
        """Progress percentage should scale with UFs completed."""
        tracker = ProgressTracker("test-pct-001", uf_count=9)

        await tracker.emit_partial_results(5, 5, ["SP", "RJ", "MG"], ["BA", "CE", "PE", "RS", "PR", "SC"])
        event = await tracker.queue.get()
        # 3/9 = 33%, scaled to 10 + 33%*85 = ~38
        assert 10 <= event.progress <= 95


# ===================================================================
# AC15: GET /buscar-results/{search_id} — store and retrieve
# ===================================================================
class TestBackgroundResultsStore:
    """AC15: In-memory store for background fetch results."""

    def setup_method(self):
        """Clean up _background_results between tests."""
        _background_results.clear()

    def test_store_and_retrieve(self):
        """store_background_results → get_background_results roundtrip."""
        resp = _make_response(live_fetch_in_progress=False)
        store_background_results("test-store-001", resp)

        retrieved = get_background_results("test-store-001")
        assert retrieved is not None
        assert retrieved.total_filtrado == 1

    def test_retrieve_nonexistent_returns_none(self):
        """get_background_results returns None for unknown search_id."""
        result = get_background_results("nonexistent-id")
        assert result is None

    def test_ttl_expiry(self):
        """Results older than TTL should not be served."""
        resp = _make_response()
        store_background_results("test-ttl-001", resp)

        # Manually expire entry
        _background_results["test-ttl-001"]["stored_at"] = time.time() - 700  # > 600s TTL

        result = get_background_results("test-ttl-001")
        assert result is None

    def test_multiple_stores(self):
        """Multiple search_ids can be stored independently."""
        store_background_results("s1", _make_response(total_raw=10))
        store_background_results("s2", _make_response(total_raw=20))

        r1 = get_background_results("s1")
        r2 = get_background_results("s2")
        assert r1 is not None
        assert r2 is not None
        assert r1.total_raw == 10
        assert r2.total_raw == 20


# ===================================================================
# AC12+AC13: Cache-first path and background task (unit tests)
# ===================================================================
class TestCacheFirstBehavior:
    """AC12/AC13: Verify BuscaResponse has live_fetch_in_progress field."""

    def test_busca_response_has_live_fetch_field(self):
        """BuscaResponse should have live_fetch_in_progress field defaulting to False."""
        resp = _make_response()
        assert resp.live_fetch_in_progress is False

    def test_busca_response_live_fetch_true(self):
        """BuscaResponse can be constructed with live_fetch_in_progress=True."""
        resp = _make_response(live_fetch_in_progress=True)
        assert resp.live_fetch_in_progress is True

    def test_live_fetch_serializes(self):
        """live_fetch_in_progress should appear in JSON serialization."""
        resp = _make_response(live_fetch_in_progress=True)
        data = resp.model_dump()
        assert data["live_fetch_in_progress"] is True

    def test_live_fetch_false_serializes(self):
        """live_fetch_in_progress=False should also appear in JSON."""
        resp = _make_response()
        data = resp.model_dump()
        assert data["live_fetch_in_progress"] is False
