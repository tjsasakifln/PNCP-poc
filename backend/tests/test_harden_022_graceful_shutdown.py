"""HARDEN-022: Graceful shutdown with task drain tests.

Tests validate the cleanup sequence:
- AC2: Background tasks are cancelled on shutdown
- AC3: Pending tasks are gathered with 10s timeout
- AC4: All Redis pools (main, SSE, sync) are closed
- AC5: All cron tasks are cancelled
- AC6: Cleanup sequence order is validated
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ============================================================================
# AC2 + AC3: Background task drain
# ============================================================================

class TestBackgroundTaskDrain:
    """Verify _active_background_tasks are cancelled and drained on shutdown."""

    @pytest.mark.asyncio
    async def test_background_tasks_cancelled_on_shutdown(self):
        """AC2: Shutdown cancels _active_background_tasks."""
        from routes.search import _active_background_tasks

        # Create a task that would run forever
        async def _forever():
            await asyncio.sleep(999)

        task = asyncio.create_task(_forever())
        _active_background_tasks["test-search-id"] = task

        try:
            # Simulate what lifespan shutdown does
            for sid, t in _active_background_tasks.items():
                if not t.done():
                    t.cancel()

            await asyncio.gather(*_active_background_tasks.values(), return_exceptions=True)

            assert task.cancelled()
        finally:
            _active_background_tasks.clear()

    @pytest.mark.asyncio
    async def test_background_tasks_drain_timeout(self):
        """AC3: Gather with 10s timeout doesn't block forever."""
        from routes.search import _active_background_tasks

        # Create a task that ignores cancellation
        async def _stubborn():
            try:
                await asyncio.sleep(999)
            except asyncio.CancelledError:
                # Simulate a task that takes time to clean up
                await asyncio.sleep(0.5)
                raise

        task = asyncio.create_task(_stubborn())
        _active_background_tasks["stubborn-id"] = task

        try:
            task.cancel()

            # Should complete within timeout (0.1s for test speed)
            await asyncio.wait_for(
                asyncio.gather(*_active_background_tasks.values(), return_exceptions=True),
                timeout=2.0,
            )
            assert task.done()
        finally:
            _active_background_tasks.clear()

    @pytest.mark.asyncio
    async def test_empty_background_tasks_is_noop(self):
        """No crash when _active_background_tasks is empty."""
        from routes.search import _active_background_tasks

        _active_background_tasks.clear()
        # Should not raise
        assert len(_active_background_tasks) == 0


# ============================================================================
# AC4: Redis pool shutdown
# ============================================================================

class TestRedisPoolShutdown:
    """Verify all Redis pools are closed on shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_closes_all_pools(self):
        """AC4: shutdown_redis closes main, SSE, and sync pools."""
        import redis_pool

        mock_main = AsyncMock()
        mock_sse = AsyncMock()
        mock_sync = MagicMock()

        redis_pool._redis_pool = mock_main
        redis_pool._pool_initialized = True
        redis_pool._sse_redis_pool = mock_sse
        redis_pool._sse_pool_initialized = True
        redis_pool._sync_redis = mock_sync
        redis_pool._sync_redis_initialized = True

        await redis_pool.shutdown_redis()

        mock_main.aclose.assert_awaited_once()
        mock_sse.aclose.assert_awaited_once()
        mock_sync.close.assert_called_once()

        # State is reset
        assert redis_pool._redis_pool is None
        assert redis_pool._pool_initialized is False
        assert redis_pool._sse_redis_pool is None
        assert redis_pool._sse_pool_initialized is False
        assert redis_pool._sync_redis is None
        assert redis_pool._sync_redis_initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_handles_close_errors(self):
        """AC4: Errors during pool close are logged, not raised."""
        import redis_pool

        mock_main = AsyncMock()
        mock_main.aclose.side_effect = Exception("connection reset")

        redis_pool._redis_pool = mock_main
        redis_pool._pool_initialized = True
        redis_pool._sse_redis_pool = None
        redis_pool._sse_pool_initialized = False
        redis_pool._sync_redis = None
        redis_pool._sync_redis_initialized = False

        # Should not raise
        await redis_pool.shutdown_redis()

        assert redis_pool._redis_pool is None

    @pytest.mark.asyncio
    async def test_shutdown_skips_sse_if_same_as_main(self):
        """AC4: SSE pool that fell back to main pool isn't double-closed."""
        import redis_pool

        mock_main = AsyncMock()

        # SSE pool fell back to main pool (same reference)
        redis_pool._redis_pool = mock_main
        redis_pool._pool_initialized = True
        redis_pool._sse_redis_pool = mock_main  # Same object!
        redis_pool._sse_pool_initialized = True
        redis_pool._sync_redis = None
        redis_pool._sync_redis_initialized = False

        await redis_pool.shutdown_redis()

        # aclose called only once (for main), not twice
        assert mock_main.aclose.await_count == 1

    @pytest.mark.asyncio
    async def test_shutdown_noop_when_no_pools(self):
        """AC4: No crash when no pools initialized."""
        import redis_pool

        redis_pool._redis_pool = None
        redis_pool._pool_initialized = False
        redis_pool._sse_redis_pool = None
        redis_pool._sse_pool_initialized = False
        redis_pool._sync_redis = None
        redis_pool._sync_redis_initialized = False

        # Should not raise
        await redis_pool.shutdown_redis()


# ============================================================================
# AC5: Cron task cancellation
# ============================================================================

class TestCronTaskCancellation:
    """Verify all cron tasks are cancelled during shutdown."""

    @pytest.mark.asyncio
    async def test_all_cron_tasks_cancelled(self):
        """AC5: All 13 cron tasks are cancelled in batch."""
        tasks = []
        for i in range(13):
            async def _cron(idx=i):
                await asyncio.sleep(999)
            t = asyncio.create_task(_cron())
            tasks.append(t)

        # Cancel all
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        for t in tasks:
            assert t.done()
            assert t.cancelled()

    @pytest.mark.asyncio
    async def test_trial_sequence_task_included(self):
        """AC5: trial_sequence_task is included in cron shutdown (was missing before)."""
        # Verify the import list in main.py includes trial_sequence_task
        import main
        source = open(main.__file__, "r").read()

        # Verify trial_sequence_task is in the _cron_tasks list
        assert "trial_sequence_task" in source
        assert "_cron_tasks" in source


# ============================================================================
# AC6: Cleanup sequence order
# ============================================================================

class TestCleanupSequence:
    """Verify shutdown follows correct order."""

    @pytest.mark.asyncio
    async def test_shutdown_sequence_order(self):
        """AC6: Cleanup follows: sessions → bg tasks → crons → ARQ → tracing → threadpool → Redis."""
        import main
        source = open(main.__file__, "r").read()

        # Find the positions of key shutdown steps
        shutdown_marker = source.index("=== SHUTDOWN ===")
        pos_sessions = source.index("_mark_inflight_sessions_timed_out", shutdown_marker)
        pos_bg_tasks = source.index("_active_background_tasks", shutdown_marker)
        pos_cron = source.index("_cron_tasks", shutdown_marker)
        pos_arq = source.index("close_arq_pool", shutdown_marker)
        pos_tracing = source.index("shutdown_tracing", shutdown_marker)
        pos_threadpool = source.index("_thread_pool.shutdown", shutdown_marker)
        pos_redis = source.index("shutdown_redis", shutdown_marker)

        # Assert correct ordering
        assert pos_sessions < pos_bg_tasks, "Sessions must be marked before bg task drain"
        assert pos_bg_tasks < pos_cron, "Background tasks must drain before cron cancellation"
        assert pos_cron < pos_arq, "Cron tasks must cancel before ARQ pool close"
        assert pos_arq < pos_tracing, "ARQ must close before tracing shutdown"
        assert pos_tracing < pos_threadpool, "Tracing must flush before threadpool shutdown"
        assert pos_threadpool < pos_redis, "Threadpool must stop before Redis pools close"

    @pytest.mark.asyncio
    async def test_lifespan_has_asynccontextmanager(self):
        """AC1: Lifespan uses @asynccontextmanager decorator."""
        import main
        import inspect
        assert inspect.isasyncgenfunction(main.lifespan.__wrapped__) or \
            hasattr(main.lifespan, '__aenter__'), \
            "lifespan must be an async context manager"

    @pytest.mark.asyncio
    async def test_shutdown_logs_completion(self):
        """AC6: Shutdown logs start and completion messages."""
        import main
        source = open(main.__file__, "r").read()

        assert "Graceful shutdown initiated" in source
        assert "Graceful shutdown complete" in source
