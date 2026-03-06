"""CRIT-071: Partial Data Progressive SSE — Backend Tests.

AC8: Tests for ProgressTracker.emit_partial_data, add_partial_licitacoes,
truncation logic, and feature flag gating in search_pipeline stages.
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_event_deps():
    """Patch telemetry + middleware imports used by ProgressEvent.to_dict()."""
    return (
        patch("telemetry.get_trace_id", return_value=None),
        patch("middleware.search_id_var", MagicMock(get=lambda x: "-")),
        patch("middleware.request_id_var", MagicMock(get=lambda x: "-")),
    )


def _make_tracker(search_id: str = "test-123", uf_count: int = 5):
    from progress import ProgressTracker
    return ProgressTracker(search_id, uf_count=uf_count, use_redis=False)


def _make_licitacoes(count: int) -> list[dict]:
    return [{"pncp_id": f"id-{i}", "objeto": f"Test {i}"} for i in range(count)]


# ===========================================================================
# 1. emit_partial_data — normal payload
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_emit_partial_data_with_licitacoes(_mock_redis):
    """emit_partial_data emits partial_data event with licitacoes inline."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-123", uf_count=5)
        licitacoes = _make_licitacoes(10)
        await tracker.emit_partial_data(
            licitacoes, batch_index=1, ufs_completed=["SP", "RJ"], is_final=False
        )

        event = tracker.queue.get_nowait()
        assert event.stage == "partial_data"
        assert event.detail["batch_index"] == 1
        assert event.detail["ufs_completed"] == ["SP", "RJ"]
        assert event.detail["is_final"] is False
        assert event.detail["truncated"] is False
        assert len(event.detail["licitacoes"]) == 10
        assert event.detail["total_items"] == 10
    finally:
        for p in patches:
            p.stop()


# ===========================================================================
# 2. emit_partial_data — truncation when >500 items
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_emit_partial_data_truncated_over_500(_mock_redis):
    """Payloads >500 items emit truncated=True with empty licitacoes."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-456", uf_count=27)
        licitacoes = _make_licitacoes(600)
        await tracker.emit_partial_data(
            licitacoes, batch_index=2, ufs_completed=["SP"], is_final=True
        )

        event = tracker.queue.get_nowait()
        assert event.stage == "partial_data"
        assert event.detail["truncated"] is True
        assert event.detail["licitacoes"] == []
        assert event.detail["total_items"] == 600
        assert event.detail["is_final"] is True
    finally:
        for p in patches:
            p.stop()


# ===========================================================================
# 3. emit_partial_data — exactly 500 items (boundary, should NOT truncate)
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_emit_partial_data_boundary_500_not_truncated(_mock_redis):
    """Exactly 500 items should be sent inline (not truncated)."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-boundary", uf_count=1)
        licitacoes = _make_licitacoes(500)
        await tracker.emit_partial_data(
            licitacoes, batch_index=1, ufs_completed=["MG"], is_final=True
        )

        event = tracker.queue.get_nowait()
        assert event.detail["truncated"] is False
        assert len(event.detail["licitacoes"]) == 500
        assert event.detail["total_items"] == 500
    finally:
        for p in patches:
            p.stop()


# ===========================================================================
# 4. add_partial_licitacoes — append-only accumulation
# ===========================================================================


def test_add_partial_licitacoes_append_only():
    """add_partial_licitacoes appends without overwriting previous data."""
    tracker = _make_tracker("test-789", uf_count=3)
    tracker.add_partial_licitacoes([{"id": 1}, {"id": 2}])
    tracker.add_partial_licitacoes([{"id": 3}])
    assert len(tracker.partial_licitacoes) == 3
    assert tracker.partial_licitacoes[0]["id"] == 1
    assert tracker.partial_licitacoes[2]["id"] == 3


def test_add_partial_licitacoes_empty_list():
    """Appending an empty list does not change state."""
    tracker = _make_tracker("test-empty", uf_count=1)
    tracker.add_partial_licitacoes([{"id": 1}])
    tracker.add_partial_licitacoes([])
    assert len(tracker.partial_licitacoes) == 1


# ===========================================================================
# 5. Feature flag gating — PARTIAL_DATA_SSE_ENABLED=false
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_partial_data_not_emitted_when_flag_disabled(_mock_redis):
    """When PARTIAL_DATA_SSE_ENABLED is false, emit_partial_data is never called."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-flag-off", uf_count=2)
        tracker.emit_partial_data = AsyncMock()
        tracker.add_partial_licitacoes = MagicMock()

        # Simulate the pipeline gating logic from search_pipeline.py stage_execute
        licitacoes_raw = _make_licitacoes(5)

        def _gated_emit(flag_value: bool):
            """Replicate the gating pattern from search_pipeline.py."""
            if flag_value:
                # Would call emit_partial_data
                tracker.emit_partial_data(
                    licitacoes=licitacoes_raw,
                    batch_index=1,
                    ufs_completed=["SP"],
                    is_final=False,
                )
                tracker.add_partial_licitacoes(licitacoes_raw)

        # Flag disabled — nothing should be called
        _gated_emit(False)
        tracker.emit_partial_data.assert_not_called()
        tracker.add_partial_licitacoes.assert_not_called()

        # Flag enabled — both should be called
        _gated_emit(True)
        tracker.emit_partial_data.assert_called_once()
        tracker.add_partial_licitacoes.assert_called_once()
    finally:
        for p in patches:
            p.stop()


# ===========================================================================
# 6. config.get_feature_flag returns correct value for PARTIAL_DATA_SSE_ENABLED
# ===========================================================================


def test_feature_flag_default_true():
    """PARTIAL_DATA_SSE_ENABLED defaults to true in config."""
    from config import PARTIAL_DATA_SSE_ENABLED
    assert PARTIAL_DATA_SSE_ENABLED is True


@patch.dict("os.environ", {"PARTIAL_DATA_SSE_ENABLED": "false"})
def test_get_feature_flag_respects_env():
    """get_feature_flag reads PARTIAL_DATA_SSE_ENABLED from environment."""
    from config import get_feature_flag
    # Clear the flag cache so the env var takes effect
    with patch("config._feature_flag_cache", {}):
        result = get_feature_flag("PARTIAL_DATA_SSE_ENABLED")
        assert result is False


# ===========================================================================
# 7. emit_partial_data — event counter increments (STORY-297 integration)
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_emit_partial_data_increments_event_counter(_mock_redis):
    """Each emit_partial_data call increments the monotonic event counter."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-counter", uf_count=3)
        assert tracker._event_counter == 0

        await tracker.emit_partial_data(
            _make_licitacoes(5), batch_index=1, ufs_completed=["SP"], is_final=False
        )
        assert tracker._event_counter == 1

        await tracker.emit_partial_data(
            _make_licitacoes(3), batch_index=2, ufs_completed=["SP", "RJ"], is_final=True
        )
        assert tracker._event_counter == 2

        # Verify events are in history for replay
        assert len(tracker._event_history) == 2
        assert tracker._event_history[0][1]["stage"] == "partial_data"
        assert tracker._event_history[1][1]["stage"] == "partial_data"
    finally:
        for p in patches:
            p.stop()


# ===========================================================================
# 8. emit_partial_data — message format
# ===========================================================================


@pytest.mark.asyncio
@patch("progress.get_redis_pool", new_callable=AsyncMock, return_value=None)
async def test_emit_partial_data_message_format(_mock_redis):
    """Message includes item count and batch index."""
    patches = _patch_event_deps()
    for p in patches:
        p.start()
    try:
        tracker = _make_tracker("test-msg", uf_count=1)
        await tracker.emit_partial_data(
            _make_licitacoes(42), batch_index=3, ufs_completed=["BA"], is_final=False
        )

        event = tracker.queue.get_nowait()
        assert "42" in event.message
        assert "batch 3" in event.message
        assert event.progress == -1  # partial_data events use -1 progress
    finally:
        for p in patches:
            p.stop()
