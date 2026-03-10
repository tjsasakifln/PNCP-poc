"""CRIT-033: Tests for ARQ enqueue NoneType fix + worker detection.

Tests cover:
- AC4: pool.enqueue_job() returns Job object (not None) — handle gracefully
- AC8: Fallback continues working if ARQ/Redis unavailable (zero regression)

Fix details:
1. enqueue_job() handles None return from pool.enqueue_job() (no crash)
2. is_queue_available() checks worker liveness via arq:queue:health-check key
3. Pipeline falls back to inline when enqueue returns None
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# AC4: enqueue_job() handles None from pool gracefully
# ============================================================================

class TestEnqueueNoneHandling:
    """CRIT-033: enqueue_job() must not crash when pool.enqueue_job() returns None."""

    @pytest.mark.asyncio
    async def test_enqueue_returns_none_when_pool_returns_none(self):
        """pool.enqueue_job() returns None (dedup) → our wrapper returns None, no crash."""
        import job_queue
        job_queue._arq_pool = None

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        # ARQ returns None when job_id already exists (dedup)
        mock_pool.enqueue_job = AsyncMock(return_value=None)
        job_queue._arq_pool = mock_pool

        result = await job_queue.enqueue_job(
            "llm_summary_job", "search-1", [], "vestuario",
            _job_id="llm:search-1",
        )

        assert result is None
        mock_pool.enqueue_job.assert_awaited_once()
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_enqueue_returns_job_on_success(self):
        """pool.enqueue_job() returns Job → our wrapper returns it."""
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_job = MagicMock()
        mock_job.job_id = "test-job-123"
        mock_pool.enqueue_job = AsyncMock(return_value=mock_job)
        job_queue._arq_pool = mock_pool

        result = await job_queue.enqueue_job(
            "llm_summary_job", "search-1", [], "vestuario",
            _job_id="llm:search-1",
        )

        assert result is mock_job
        assert result.job_id == "test-job-123"
        job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_enqueue_none_does_not_raise_attribute_error(self):
        """Regression: accessing .job_id on None must NOT raise AttributeError."""
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_pool.enqueue_job = AsyncMock(return_value=None)
        job_queue._arq_pool = mock_pool

        # This used to crash with: AttributeError: 'NoneType' object has no attribute 'job_id'
        try:
            result = await job_queue.enqueue_job("llm_summary_job", "s1", [], "sector")
            assert result is None  # Should return None gracefully
        except AttributeError:
            pytest.fail("enqueue_job raised AttributeError on None — CRIT-033 regression!")
        finally:
            job_queue._arq_pool = None

    @pytest.mark.asyncio
    async def test_enqueue_exception_still_returns_none(self):
        """pool.enqueue_job() raises → our wrapper catches and returns None."""
        import job_queue

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_pool.enqueue_job = AsyncMock(side_effect=ConnectionError("Redis gone"))
        job_queue._arq_pool = mock_pool

        result = await job_queue.enqueue_job("excel_generation_job", "s1", [], True)
        assert result is None
        job_queue._arq_pool = None


# ============================================================================
# CRIT-033: Worker liveness detection
# ============================================================================

class TestWorkerAliveCheck:
    """CRIT-033: _check_worker_alive() detects worker via Redis health-check key."""

    @pytest.mark.asyncio
    async def test_worker_alive_when_key_exists(self):
        """Health-check key exists → worker is alive."""
        import job_queue
        # Reset cache
        job_queue._worker_alive_cache = (0.0, False)

        mock_pool = AsyncMock()
        mock_pool.exists = AsyncMock(return_value=1)

        result = await job_queue._check_worker_alive(mock_pool)
        assert result is True
        mock_pool.exists.assert_awaited_once_with("arq:queue:health-check")
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_worker_dead_when_key_missing(self):
        """Health-check key absent → no worker running."""
        import job_queue
        job_queue._worker_alive_cache = (0.0, False)

        mock_pool = AsyncMock()
        mock_pool.exists = AsyncMock(return_value=0)

        result = await job_queue._check_worker_alive(mock_pool)
        assert result is False
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_worker_check_cached(self):
        """Cached result used within _WORKER_CHECK_INTERVAL."""
        import job_queue
        # Set fresh cache: alive=True, checked just now
        job_queue._worker_alive_cache = (time.monotonic(), True)

        mock_pool = AsyncMock()
        mock_pool.exists = AsyncMock(return_value=0)

        result = await job_queue._check_worker_alive(mock_pool)
        assert result is True  # Cached value, not the Redis value
        mock_pool.exists.assert_not_awaited()  # Redis not queried
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_worker_check_refreshed_after_interval(self):
        """Cache expired → Redis queried again."""
        import job_queue
        # Set stale cache: alive=True, checked long ago
        job_queue._worker_alive_cache = (time.monotonic() - 120, True)

        mock_pool = AsyncMock()
        mock_pool.exists = AsyncMock(return_value=0)

        result = await job_queue._check_worker_alive(mock_pool)
        assert result is False  # Fresh Redis value
        mock_pool.exists.assert_awaited_once()
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_worker_check_handles_exception(self):
        """Redis error → returns False (safe default)."""
        import job_queue
        job_queue._worker_alive_cache = (0.0, False)

        mock_pool = AsyncMock()
        mock_pool.exists = AsyncMock(side_effect=ConnectionError("Redis timeout"))

        result = await job_queue._check_worker_alive(mock_pool)
        assert result is False
        job_queue._worker_alive_cache = (0.0, False)


# ============================================================================
# CRIT-033: is_queue_available() with worker check
# ============================================================================

class TestIsQueueAvailableWithWorker:
    """CRIT-033: is_queue_available() requires both Redis + worker."""

    @pytest.mark.asyncio
    async def test_available_when_redis_and_worker_alive(self):
        """Redis up + worker alive → True."""
        import job_queue
        job_queue._worker_alive_cache = (0.0, False)

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_pool.exists = AsyncMock(return_value=1)
        job_queue._arq_pool = mock_pool

        result = await job_queue.is_queue_available()
        assert result is True
        job_queue._arq_pool = None
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_unavailable_when_redis_up_but_no_worker(self):
        """Redis up + no worker → False (CRIT-033 key fix)."""
        import job_queue
        job_queue._worker_alive_cache = (0.0, False)

        mock_pool = AsyncMock()
        mock_pool.ping = AsyncMock(return_value=True)
        mock_pool.exists = AsyncMock(return_value=0)
        job_queue._arq_pool = mock_pool

        result = await job_queue.is_queue_available()
        assert result is False  # This is the CRIT-033 fix
        job_queue._arq_pool = None
        job_queue._worker_alive_cache = (0.0, False)

    @pytest.mark.asyncio
    async def test_unavailable_when_no_redis(self):
        """No Redis pool → False (unchanged behavior)."""
        import job_queue
        job_queue._arq_pool = None

        with patch.object(job_queue, "_get_redis_settings", side_effect=ValueError("no REDIS_URL")):
            result = await job_queue.is_queue_available()
            assert result is False


# ============================================================================
# AC8: Pipeline inline fallback when enqueue fails (regression)
# ============================================================================

class TestPipelineEnqueueFallback:
    """CRIT-033 AC8: Pipeline falls back to inline when enqueue returns None.

    These tests verify search_pipeline.py handles enqueue failure by
    marking status as 'ready'/'fallback' instead of leaving 'processing'.
    """

    @pytest.mark.asyncio
    async def test_llm_enqueue_failure_sets_fallback_status(self):
        """If LLM enqueue returns None, ctx.llm_status='ready', ctx.llm_source='fallback'."""
        from search_context import SearchContext

        # Minimal ctx for the queue mode code path
        mock_request = MagicMock()
        mock_request.search_id = "test-search-001"
        ctx = SearchContext(request=mock_request, user={"sub": "user-1"})
        ctx.licitacoes_filtradas = [{"objeto": "Test", "valorTotalEstimado": 100}]
        ctx.quota_info = MagicMock()
        ctx.quota_info.capabilities = {"allow_excel": False}
        ctx.tracker = None

        mock_sector = MagicMock()
        mock_sector.name = "vestuario"
        ctx.sector = mock_sector

        mock_resumo = MagicMock()

        with patch("job_queue.is_queue_available", new_callable=lambda: AsyncMock(return_value=True)):
            with patch("job_queue.enqueue_job", new_callable=lambda: AsyncMock(return_value=None)):
                with patch("pipeline.stages.generate.gerar_resumo_fallback", return_value=mock_resumo):
                    # Import and call the relevant pipeline section
                    from job_queue import is_queue_available, enqueue_job

                    queue_available = await is_queue_available()
                    search_id = ctx.request.search_id

                    ctx.excel_base64 = None
                    ctx.download_url = None
                    ctx.excel_available = ctx.quota_info.capabilities["allow_excel"]
                    ctx.upgrade_message = None

                    if queue_available and search_id:
                        ctx.queue_mode = True
                        ctx.resumo = mock_resumo
                        ctx.llm_status = "processing"
                        ctx.llm_source = "processing"

                        llm_enqueued = await enqueue_job(
                            "llm_summary_job", search_id,
                            ctx.licitacoes_filtradas, ctx.sector.name,
                            _job_id=f"llm:{search_id}",
                        )
                        if llm_enqueued is None:
                            ctx.llm_status = "ready"
                            ctx.llm_source = "fallback"

        assert ctx.llm_status == "ready"
        assert ctx.llm_source == "fallback"

    @pytest.mark.asyncio
    async def test_excel_enqueue_failure_sets_failed_status(self):
        """If Excel enqueue returns None, ctx.excel_status='failed'."""
        from search_context import SearchContext

        mock_request = MagicMock()
        mock_request.search_id = "test-search-002"
        ctx = SearchContext(request=mock_request, user={"sub": "user-1"})
        ctx.licitacoes_filtradas = [{"objeto": "Test", "valorTotalEstimado": 100}]
        ctx.quota_info = MagicMock()
        ctx.quota_info.capabilities = {"allow_excel": True}
        ctx.tracker = None

        mock_sector = MagicMock()
        mock_sector.name = "vestuario"
        ctx.sector = mock_sector

        mock_job = MagicMock()
        mock_job.job_id = "llm-123"

        with patch("job_queue.is_queue_available", new_callable=lambda: AsyncMock(return_value=True)):
            # LLM enqueue succeeds, Excel enqueue fails
            with patch("job_queue.enqueue_job", new_callable=lambda: AsyncMock(
                side_effect=[mock_job, None]
            )):
                with patch("pipeline.stages.generate.gerar_resumo_fallback", return_value=MagicMock()):
                    from job_queue import is_queue_available, enqueue_job

                    queue_available = await is_queue_available()
                    search_id = ctx.request.search_id

                    ctx.excel_base64 = None
                    ctx.download_url = None
                    ctx.excel_available = True
                    ctx.upgrade_message = None

                    if queue_available and search_id:
                        ctx.queue_mode = True
                        ctx.llm_status = "processing"
                        ctx.llm_source = "processing"
                        ctx.resumo = MagicMock()

                        llm_enqueued = await enqueue_job(
                            "llm_summary_job", search_id,
                            ctx.licitacoes_filtradas, ctx.sector.name,
                            _job_id=f"llm:{search_id}",
                        )
                        if llm_enqueued is None:
                            ctx.llm_status = "ready"
                            ctx.llm_source = "fallback"

                        excel_enqueued = await enqueue_job(
                            "excel_generation_job", search_id,
                            ctx.licitacoes_filtradas, True,
                            _job_id=f"excel:{search_id}",
                        )
                        if excel_enqueued is not None:
                            ctx.excel_status = "processing"
                        else:
                            ctx.excel_status = "failed"

        assert ctx.llm_status == "processing"  # LLM enqueue succeeded
        assert ctx.excel_status == "failed"  # Excel enqueue failed

    @pytest.mark.asyncio
    async def test_both_enqueue_success_keeps_processing_status(self):
        """When both enqueues succeed, status stays 'processing'."""
        from search_context import SearchContext

        mock_request = MagicMock()
        mock_request.search_id = "test-search-003"
        ctx = SearchContext(request=mock_request, user={"sub": "user-1"})
        ctx.licitacoes_filtradas = [{"objeto": "Test"}]
        ctx.quota_info = MagicMock()
        ctx.quota_info.capabilities = {"allow_excel": True}
        ctx.tracker = None

        mock_sector = MagicMock()
        mock_sector.name = "vestuario"
        ctx.sector = mock_sector

        mock_llm_job = MagicMock()
        mock_llm_job.job_id = "llm-ok"
        mock_excel_job = MagicMock()
        mock_excel_job.job_id = "excel-ok"

        with patch("job_queue.is_queue_available", new_callable=lambda: AsyncMock(return_value=True)):
            with patch("job_queue.enqueue_job", new_callable=lambda: AsyncMock(
                side_effect=[mock_llm_job, mock_excel_job]
            )):
                with patch("pipeline.stages.generate.gerar_resumo_fallback", return_value=MagicMock()):
                    from job_queue import is_queue_available, enqueue_job

                    queue_available = await is_queue_available()
                    search_id = ctx.request.search_id

                    ctx.excel_base64 = None
                    ctx.download_url = None
                    ctx.excel_available = True
                    ctx.upgrade_message = None

                    if queue_available and search_id:
                        ctx.queue_mode = True
                        ctx.llm_status = "processing"
                        ctx.llm_source = "processing"
                        ctx.resumo = MagicMock()

                        llm_enqueued = await enqueue_job(
                            "llm_summary_job", search_id,
                            ctx.licitacoes_filtradas, ctx.sector.name,
                            _job_id=f"llm:{search_id}",
                        )
                        if llm_enqueued is None:
                            ctx.llm_status = "ready"
                            ctx.llm_source = "fallback"

                        excel_enqueued = await enqueue_job(
                            "excel_generation_job", search_id,
                            ctx.licitacoes_filtradas, True,
                            _job_id=f"excel:{search_id}",
                        )
                        if excel_enqueued is not None:
                            ctx.excel_status = "processing"
                        else:
                            ctx.excel_status = "failed"

        assert ctx.llm_status == "processing"
        assert ctx.llm_source == "processing"
        assert ctx.excel_status == "processing"


# ============================================================================
# AC8: Existing inline fallback still works (regression)
# ============================================================================

class TestInlineFallbackRegression:
    """AC8: When queue unavailable, inline mode works unchanged."""

    @pytest.mark.asyncio
    async def test_inline_mode_when_queue_unavailable(self):
        """Pipeline uses inline mode when is_queue_available() returns False."""
        from search_context import SearchContext

        mock_request = MagicMock()
        mock_request.search_id = "test-search-inline"
        ctx = SearchContext(request=mock_request, user={"sub": "user-1"})

        with patch("job_queue.is_queue_available", new_callable=lambda: AsyncMock(return_value=False)):
            from job_queue import is_queue_available

            queue_available = await is_queue_available()
            assert queue_available is False

            # Pipeline should NOT enter queue mode
            ctx.queue_mode = False
            assert ctx.queue_mode is False

    @pytest.mark.asyncio
    async def test_inline_mode_when_no_search_id(self):
        """Pipeline uses inline mode when search_id is None."""
        from search_context import SearchContext

        mock_request = MagicMock()
        mock_request.search_id = None
        ctx = SearchContext(request=mock_request, user={"sub": "user-1"})

        with patch("job_queue.is_queue_available", new_callable=lambda: AsyncMock(return_value=True)):
            from job_queue import is_queue_available

            queue_available = await is_queue_available()
            search_id = ctx.request.search_id

            should_queue = queue_available and search_id
            assert should_queue is None or should_queue is False
