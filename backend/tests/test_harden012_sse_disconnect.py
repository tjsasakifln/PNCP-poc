"""
HARDEN-012: SSE Client Disconnect Detection via request.is_disconnected()

Tests that event_generator checks request.is_disconnected() each iteration
and performs proper cleanup (release_sse_connection + metric increment).
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(*, disconnected_after: int = 0):
    """Create a mock Request that returns disconnected=True after N calls."""
    call_count = 0

    async def _is_disconnected():
        nonlocal call_count
        call_count += 1
        return call_count > disconnected_after

    req = AsyncMock()
    req.is_disconnected = _is_disconnected
    req.headers = MagicMock()
    req.headers.get = MagicMock(return_value=None)
    req.query_params = MagicMock()
    req.query_params.get = MagicMock(return_value=None)
    return req


async def _collect_sse_events(gen, max_events=50):
    """Drain an async generator, collecting yielded strings."""
    events = []
    count = 0
    async for chunk in gen:
        events.append(chunk)
        count += 1
        if count >= max_events:
            break
    return events


def _base_patches():
    """Return common patches needed by all tests."""
    return [
        patch("routes.search.is_search_terminal", new_callable=AsyncMock, return_value=None),
        patch("routes.search.get_replay_events", new_callable=AsyncMock, return_value=[]),
        patch("routes.search.acquire_sse_connection", new_callable=AsyncMock, return_value=True),
        patch("metrics.SSE_CONNECTIONS_TOTAL", MagicMock()),
        patch("metrics.SSE_DISCONNECTS_TOTAL", MagicMock()),
        patch("metrics.SSE_CONNECTION_ERRORS", MagicMock()),
    ]


# ---------------------------------------------------------------------------
# AC1 + AC2 + AC3 + AC4: Disconnect during wait-for-tracker phase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_during_wait_phase():
    """Client disconnects while waiting for tracker → generator exits cleanly."""
    request = _make_request(disconnected_after=0)  # Immediate disconnect

    patches = _base_patches() + [
        patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=None),
        patch("routes.search.release_sse_connection", new_callable=AsyncMock),
    ]

    for p in patches:
        p.start()

    try:
        import metrics
        mock_metric = metrics.SSE_DISCONNECTS_TOTAL
        mock_release = None

        # Get the mock_release from the active patches
        import routes.search as search_mod
        mock_release = search_mod.release_sse_connection

        from routes.search import buscar_progress_stream
        response = await buscar_progress_stream(
            search_id="test-disconnect-wait",
            request=request,
            user={"id": "test-user-id", "sub": "test-user-id"},
        )

        events = await _collect_sse_events(response.body_iterator)

        # AC1+AC2: No data events should be yielded (immediate disconnect)
        data_events = [e for e in events if "data:" in e]
        assert len(data_events) == 0, f"Expected no data events on immediate disconnect, got {data_events}"

        # AC3: release_sse_connection called via finally
        mock_release.assert_awaited_once_with("test-user-id")

        # AC4: Disconnect metric incremented
        mock_metric.inc.assert_called()
    finally:
        for p in patches:
            p.stop()


# ---------------------------------------------------------------------------
# AC1 + AC4: Disconnect during Redis Streams polling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_during_redis_streaming():
    """Client disconnects during Redis XREAD polling → generator exits cleanly."""
    request = _make_request(disconnected_after=1)  # 1st check OK (wait), 2nd triggers (redis loop)

    mock_tracker = MagicMock()
    mock_tracker._use_redis = True
    mock_tracker.queue = asyncio.Queue()

    mock_redis = AsyncMock()
    mock_redis.xread = AsyncMock(return_value=[])

    patches = _base_patches() + [
        patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        patch("routes.search.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("routes.search.release_sse_connection", new_callable=AsyncMock),
    ]

    for p in patches:
        p.start()

    try:
        import metrics
        mock_metric = metrics.SSE_DISCONNECTS_TOTAL
        import routes.search as search_mod
        mock_release = search_mod.release_sse_connection

        from routes.search import buscar_progress_stream
        response = await buscar_progress_stream(
            search_id="test-disconnect-redis",
            request=request,
            user={"id": "test-user-id", "sub": "test-user-id"},
        )

        events = await _collect_sse_events(response.body_iterator)

        data_events = [e for e in events if "data:" in e]
        assert len(data_events) == 0, f"Expected no data events, got {data_events}"

        mock_release.assert_awaited_once_with("test-user-id")
        mock_metric.inc.assert_called()
    finally:
        for p in patches:
            p.stop()


# ---------------------------------------------------------------------------
# AC1 + AC4: Disconnect during in-memory queue mode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_during_inmemory_queue():
    """Client disconnects during in-memory queue polling → generator exits cleanly."""
    request = _make_request(disconnected_after=1)  # 1st OK (wait), 2nd triggers (queue loop)

    mock_tracker = MagicMock()
    mock_tracker._use_redis = False
    mock_tracker.queue = asyncio.Queue()

    patches = _base_patches() + [
        patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        patch("routes.search.release_sse_connection", new_callable=AsyncMock),
        patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01),
    ]

    for p in patches:
        p.start()

    try:
        import metrics
        mock_metric = metrics.SSE_DISCONNECTS_TOTAL
        import routes.search as search_mod
        mock_release = search_mod.release_sse_connection

        from routes.search import buscar_progress_stream
        response = await buscar_progress_stream(
            search_id="test-disconnect-queue",
            request=request,
            user={"id": "test-user-id", "sub": "test-user-id"},
        )

        events = await _collect_sse_events(response.body_iterator)

        data_events = [e for e in events if "data:" in e]
        assert len(data_events) == 0, f"Expected no data events, got {data_events}"

        mock_release.assert_awaited_once_with("test-user-id")
        mock_metric.inc.assert_called()
    finally:
        for p in patches:
            p.stop()


# ---------------------------------------------------------------------------
# AC5: Disconnect during Supabase fallback polling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_disconnect_during_supabase_fallback():
    """Client disconnects during Supabase fallback → generator exits cleanly."""
    request = _make_request(disconnected_after=2)  # wait=1, redis=1 (triggers timeout), supabase=1 (disconnect)

    mock_tracker = MagicMock()
    mock_tracker._use_redis = True
    mock_tracker.queue = asyncio.Queue()

    mock_redis = AsyncMock()
    mock_redis.xread = AsyncMock(side_effect=TimeoutError("redis timeout"))

    patches = _base_patches() + [
        patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        patch("routes.search.get_sse_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("routes.search.get_search_status", new_callable=AsyncMock, return_value=None),
        patch("routes.search.release_sse_connection", new_callable=AsyncMock),
    ]

    for p in patches:
        p.start()

    try:
        import metrics
        mock_metric = metrics.SSE_DISCONNECTS_TOTAL
        import routes.search as search_mod
        mock_release = search_mod.release_sse_connection

        from routes.search import buscar_progress_stream
        response = await buscar_progress_stream(
            search_id="test-disconnect-supabase",
            request=request,
            user={"id": "test-user-id", "sub": "test-user-id"},
        )

        events = await _collect_sse_events(response.body_iterator)

        mock_release.assert_awaited_once_with("test-user-id")
        mock_metric.inc.assert_called()
    finally:
        for p in patches:
            p.stop()


# ---------------------------------------------------------------------------
# Negative test: No disconnect → normal flow continues
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_disconnect_normal_flow():
    """When client stays connected, events flow normally until terminal."""
    request = _make_request(disconnected_after=999)

    mock_tracker = MagicMock()
    mock_tracker._use_redis = False
    mock_tracker.queue = asyncio.Queue()

    mock_event = MagicMock()
    mock_event.stage = "complete"
    mock_event.to_dict.return_value = {"stage": "complete", "progress": 100, "message": "Done"}
    await mock_tracker.queue.put(mock_event)

    patches = _base_patches() + [
        patch("routes.search.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        patch("routes.search.release_sse_connection", new_callable=AsyncMock),
        patch("routes.search._SSE_HEARTBEAT_INTERVAL", 0.01),
    ]

    for p in patches:
        p.start()

    try:
        import metrics
        mock_metric = metrics.SSE_DISCONNECTS_TOTAL
        import routes.search as search_mod
        mock_release = search_mod.release_sse_connection

        from routes.search import buscar_progress_stream
        response = await buscar_progress_stream(
            search_id="test-no-disconnect",
            request=request,
            user={"id": "test-user-id", "sub": "test-user-id"},
        )

        events = await _collect_sse_events(response.body_iterator)

        data_events = [e for e in events if "data:" in e]
        assert len(data_events) >= 1, f"Expected data events, got {events}"
        assert "complete" in data_events[-1]

        # Disconnect metric should NOT have been called
        mock_metric.inc.assert_not_called()

        mock_release.assert_awaited_once_with("test-user-id")
    finally:
        for p in patches:
            p.stop()
