"""HARDEN-005 AC5: Tests for _safe_persist_results retry + metric + done_callback."""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


@pytest.mark.asyncio
async def test_safe_persist_succeeds_first_attempt():
    """AC1: Wrapper calls _persist_results_to_supabase and returns on success."""
    from routes.search import _safe_persist_results

    with patch(
        "routes.search_state._persist_results_to_supabase", new_callable=AsyncMock
    ) as mock_persist:
        await _safe_persist_results("sid-1", "uid-1", {"data": 1})

    mock_persist.assert_awaited_once_with("sid-1", "uid-1", {"data": 1})


@pytest.mark.asyncio
async def test_safe_persist_retries_on_failure():
    """AC1: Retries up to 3 times with exponential backoff."""
    from routes.search import _safe_persist_results

    mock_persist = AsyncMock(
        side_effect=[Exception("fail-1"), Exception("fail-2"), None]
    )

    with (
        patch("routes.search_state._persist_results_to_supabase", mock_persist),
        patch("routes.search_state.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        patch("routes.search_state.sentry_sdk") as mock_sentry,
    ):
        await _safe_persist_results("sid-2", "uid-2", {"data": 2})

    assert mock_persist.await_count == 3
    # Exponential backoff: 2^0=1s, 2^1=2s
    mock_sleep.assert_any_await(1)
    mock_sleep.assert_any_await(2)
    mock_sentry.capture_exception.assert_not_called()


@pytest.mark.asyncio
async def test_safe_persist_sentry_on_final_failure():
    """AC2: sentry_sdk.capture_exception() called on final failure."""
    from routes.search import _safe_persist_results

    final_exc = Exception("permanent-failure")
    mock_persist = AsyncMock(
        side_effect=[Exception("fail-1"), Exception("fail-2"), final_exc]
    )

    with (
        patch("routes.search_state._persist_results_to_supabase", mock_persist),
        patch("routes.search_state.asyncio.sleep", new_callable=AsyncMock),
        patch("routes.search_state.sentry_sdk") as mock_sentry,
        patch("routes.search_state.PERSIST_FAILURES", create=True) as mock_metric,
    ):
        # Need to patch the import inside the function
        with patch("metrics.PERSIST_FAILURES", mock_metric):
            await _safe_persist_results("sid-3", "uid-3", {"data": 3})

    mock_sentry.capture_exception.assert_called_once_with(final_exc)


@pytest.mark.asyncio
async def test_safe_persist_metric_on_final_failure():
    """AC3: PERSIST_FAILURES counter incremented on final failure."""
    from routes.search import _safe_persist_results

    mock_persist = AsyncMock(side_effect=Exception("always-fail"))
    mock_metric = MagicMock()
    mock_labels = MagicMock()
    mock_metric.labels.return_value = mock_labels

    with (
        patch("routes.search_state._persist_results_to_supabase", mock_persist),
        patch("routes.search_state.asyncio.sleep", new_callable=AsyncMock),
        patch("routes.search_state.sentry_sdk"),
        patch("metrics.PERSIST_FAILURES", mock_metric),
    ):
        await _safe_persist_results("sid-4", "uid-4", {"data": 4})

    mock_metric.labels.assert_called_with(store="supabase")
    mock_labels.inc.assert_called_once()


def test_persist_done_callback_captures_exception():
    """AC4: done_callback captures exceptions from fire-and-forget tasks."""
    from routes.search import _persist_done_callback

    mock_task = MagicMock(spec=asyncio.Task)
    exc = RuntimeError("task-boom")
    mock_task.cancelled.return_value = False
    mock_task.exception.return_value = exc

    with patch("routes.search_state.sentry_sdk") as mock_sentry:
        _persist_done_callback(mock_task)

    mock_sentry.capture_exception.assert_called_once_with(exc)


def test_persist_done_callback_ignores_cancelled():
    """AC4: done_callback does nothing for cancelled tasks."""
    from routes.search import _persist_done_callback

    mock_task = MagicMock(spec=asyncio.Task)
    mock_task.cancelled.return_value = True

    with patch("routes.search_state.sentry_sdk") as mock_sentry:
        _persist_done_callback(mock_task)

    mock_sentry.capture_exception.assert_not_called()


def test_persist_done_callback_no_exception():
    """AC4: done_callback does nothing when task completes successfully."""
    from routes.search import _persist_done_callback

    mock_task = MagicMock(spec=asyncio.Task)
    mock_task.cancelled.return_value = False
    mock_task.exception.return_value = None

    with patch("routes.search_state.sentry_sdk") as mock_sentry:
        _persist_done_callback(mock_task)

    mock_sentry.capture_exception.assert_not_called()


@pytest.mark.asyncio
async def test_safe_persist_no_retry_on_first_success():
    """AC1: No sleep/retry if first attempt succeeds."""
    from routes.search import _safe_persist_results

    with (
        patch(
            "routes.search_state._persist_results_to_supabase", new_callable=AsyncMock
        ) as mock_persist,
        patch("routes.search_state.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await _safe_persist_results("sid-5", "uid-5", {"data": 5})

    mock_persist.assert_awaited_once()
    mock_sleep.assert_not_awaited()
