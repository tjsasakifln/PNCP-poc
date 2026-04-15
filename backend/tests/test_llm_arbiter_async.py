"""STORY-4.1 (TD-SYS-014) — tests for the async runtime primitives."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_semaphore_returns_loop_scoped_instance():
    """Re-entering a fresh loop rebuilds the semaphore (no 'Future attached to different loop')."""

    from llm_arbiter.async_runtime import _get_semaphore, reset_semaphore

    reset_semaphore()
    sem1 = _get_semaphore()
    sem2 = _get_semaphore()
    assert sem1 is sem2  # same loop → same instance

    # Cross-loop: invoke the helper from a fresh loop and assert we got a new one.
    reset_semaphore()
    result: list = []

    def _run_in_fresh_loop():
        async def _go():
            result.append(_get_semaphore())
        asyncio.run(_go())

    import threading

    thread = threading.Thread(target=_run_in_fresh_loop)
    thread.start()
    thread.join()
    assert result, "helper did not run"
    # Different loop → different semaphore
    assert result[0] is not sem1


@pytest.mark.asyncio
async def test_bounded_respects_max_concurrent(monkeypatch):
    """No more than LLM_MAX_CONCURRENT coroutines run inside _bounded at once."""

    import llm_arbiter.async_runtime as ar

    monkeypatch.setattr("config.LLM_MAX_CONCURRENT", 3, raising=False)
    ar.reset_semaphore()

    in_flight = 0
    peak = 0
    lock = asyncio.Lock()

    async def _work():
        nonlocal in_flight, peak
        async with ar._bounded("test"):
            async with lock:
                in_flight += 1
                peak = max(peak, in_flight)
            await asyncio.sleep(0.05)
            async with lock:
                in_flight -= 1

    await asyncio.gather(*[_work() for _ in range(20)])
    assert peak <= 3, f"peak concurrency {peak} exceeded LLM_MAX_CONCURRENT=3"


@pytest.mark.asyncio
async def test_gather_classifications_preserves_order_and_progress():
    """Results come back in input order; on_progress fires once per completion."""

    from llm_arbiter.async_runtime import gather_classifications, reset_semaphore

    reset_semaphore()
    calls: list = []

    def _classify(item):
        return item * 2

    results = await gather_classifications(
        _classify,
        [1, 2, 3, 4, 5],
        call_type="test",
        on_progress=lambda done, total, phase: calls.append((done, total, phase)),
    )
    assert results == [2, 4, 6, 8, 10]
    assert len(calls) == 5
    assert calls[-1][0] == 5
    assert all(phase == "llm_classify" for _, _, phase in calls)


@pytest.mark.asyncio
async def test_run_bounded_in_thread_executes_sync_fn():
    """run_bounded_in_thread invokes the sync function and returns its value."""

    from llm_arbiter.async_runtime import reset_semaphore, run_bounded_in_thread

    reset_semaphore()
    result = await run_bounded_in_thread(lambda x: x + 1, 41, call_type="test")
    assert result == 42


def test_get_async_client_is_lazy_and_cached():
    """_get_async_client is lazy and returns the same instance on re-entry."""

    import llm_arbiter.async_runtime as ar

    ar._async_client = None
    with patch("openai.AsyncOpenAI") as FakeClient:
        FakeClient.return_value = MagicMock(name="AsyncOpenAIInstance")
        client1 = ar._get_async_client()
        client2 = ar._get_async_client()
    assert client1 is client2
    # First call imports AsyncOpenAI, second returns cache — one constructor call.
    FakeClient.assert_called_once()
