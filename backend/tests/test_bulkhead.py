"""STORY-296 + HARDEN-015: Tests for per-source bulkhead pattern.

Tests cover:
- AC1: Per-source semaphore concurrency limits
- AC2: Connection pool isolation (httpx.Limits)
- AC3: Per-source configurable timeouts
- AC4: PNCP exhaustion does NOT block PCP/ComprasGov
- AC5: Prometheus metrics per source
- AC6: Health endpoint per-source bulkhead status
- AC7: Existing tests continue passing (validated by CI)

HARDEN-015 additions:
- AC1: Bulkhead.execute() divides timeout 50% acquire / 50% execution
- AC2: BulkheadAcquireTimeoutError for acquire timeout
- AC3: UF marked as skipped (not error) when acquire timeout
- AC4: Metric smartlic_bulkhead_acquire_timeout_total
- AC5: 27 UFs with bulkhead size=5 scenario
"""

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from bulkhead import (
    BulkheadAcquireTimeoutError,
    SourceBulkhead,
    get_bulkhead,
    register_bulkhead,
    get_all_bulkheads,
    reset_registry,
    initialize_bulkheads,
)


# ============================================================================
# AC1: Per-source semaphore concurrency limits
# ============================================================================


class TestSourceBulkheadSemaphore:
    """Verify that the semaphore correctly limits concurrency."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """At most max_concurrent coroutines run simultaneously."""
        bh = SourceBulkhead("TEST", max_concurrent=2, timeout=10.0)
        running = []
        max_running = 0
        barrier = asyncio.Event()

        async def work():
            nonlocal max_running
            running.append(1)
            current = len(running)
            if current > max_running:
                max_running = current
            await barrier.wait()
            running.pop()

        # Launch 5 tasks through bulkhead with concurrency=2
        tasks = [asyncio.create_task(bh.execute(work())) for _ in range(5)]

        # Let tasks settle — only 2 should be running
        await asyncio.sleep(0.05)
        assert len(running) == 2
        assert max_running == 2

        # Release all
        barrier.set()
        await asyncio.gather(*tasks)
        assert len(running) == 0

    @pytest.mark.asyncio
    async def test_active_counter_tracks_correctly(self):
        """active property tracks in-flight operations."""
        bh = SourceBulkhead("TEST", max_concurrent=3, timeout=10.0)
        barrier = asyncio.Event()

        async def work():
            await barrier.wait()

        assert bh.active == 0
        tasks = [asyncio.create_task(bh.execute(work())) for _ in range(2)]
        await asyncio.sleep(0.02)
        assert bh.active == 2
        assert bh.available == 1

        barrier.set()
        await asyncio.gather(*tasks)
        assert bh.active == 0
        assert bh.available == 3

    @pytest.mark.asyncio
    async def test_pncp_concurrency_limit_5(self):
        """PNCP bulkhead defaults to max_concurrent=5."""
        bulkheads = initialize_bulkheads()
        assert bulkheads["PNCP"].max_concurrent == 5

    @pytest.mark.asyncio
    async def test_pcp_concurrency_limit_3(self):
        """PCP bulkhead defaults to max_concurrent=3."""
        bulkheads = initialize_bulkheads()
        assert bulkheads["PORTAL_COMPRAS"].max_concurrent == 3

    @pytest.mark.asyncio
    async def test_comprasgov_concurrency_limit_3(self):
        """ComprasGov bulkhead defaults to max_concurrent=3."""
        bulkheads = initialize_bulkheads()
        assert bulkheads["COMPRAS_GOV"].max_concurrent == 3


# ============================================================================
# AC3: Per-source configurable timeouts
# ============================================================================


class TestConfigurableTimeouts:
    """Verify timeouts are configurable via env vars."""

    def test_default_timeouts(self):
        bulkheads = initialize_bulkheads()
        assert bulkheads["PNCP"].timeout == 80.0
        assert bulkheads["PORTAL_COMPRAS"].timeout == 30.0
        assert bulkheads["COMPRAS_GOV"].timeout == 30.0

    @patch.dict("os.environ", {
        "PNCP_SOURCE_TIMEOUT": "120",
        "PCP_SOURCE_TIMEOUT": "45",
        "COMPRASGOV_SOURCE_TIMEOUT": "60",
    })
    def test_custom_timeouts_from_env(self):
        """Env vars override default timeouts."""
        # Reload config values
        import importlib
        import config
        importlib.reload(config)
        try:
            reset_registry()
            bulkheads = initialize_bulkheads()
            assert bulkheads["PNCP"].timeout == 120.0
            assert bulkheads["PORTAL_COMPRAS"].timeout == 45.0
            assert bulkheads["COMPRAS_GOV"].timeout == 60.0
        finally:
            importlib.reload(config)

    @patch.dict("os.environ", {
        "PNCP_BULKHEAD_CONCURRENCY": "10",
        "PCP_BULKHEAD_CONCURRENCY": "5",
        "COMPRASGOV_BULKHEAD_CONCURRENCY": "7",
    })
    def test_custom_concurrency_from_env(self):
        """Env vars override default concurrency."""
        import importlib
        import config
        importlib.reload(config)
        try:
            reset_registry()
            bulkheads = initialize_bulkheads()
            assert bulkheads["PNCP"].max_concurrent == 10
            assert bulkheads["PORTAL_COMPRAS"].max_concurrent == 5
            assert bulkheads["COMPRAS_GOV"].max_concurrent == 7
        finally:
            importlib.reload(config)


# ============================================================================
# AC4: PNCP exhaustion does NOT block PCP/ComprasGov
# ============================================================================


class TestBulkheadIsolation:
    """Core isolation test: failure/saturation in one source doesn't affect others."""

    @pytest.mark.asyncio
    async def test_pncp_exhaustion_does_not_block_pcp(self):
        """When PNCP's semaphore is fully occupied, PCP operations proceed immediately."""
        pncp_bh = SourceBulkhead("PNCP", max_concurrent=2, timeout=10.0)
        pcp_bh = SourceBulkhead("PORTAL_COMPRAS", max_concurrent=2, timeout=10.0)

        pncp_barrier = asyncio.Event()
        pcp_completed = asyncio.Event()

        async def pncp_slow_work():
            await pncp_barrier.wait()

        async def pcp_fast_work():
            pcp_completed.set()
            return "pcp_done"

        # Saturate PNCP with 2 tasks (fills semaphore)
        pncp_tasks = [
            asyncio.create_task(pncp_bh.execute(pncp_slow_work()))
            for _ in range(2)
        ]
        await asyncio.sleep(0.02)
        assert pncp_bh.is_exhausted

        # PCP should work immediately despite PNCP being full
        result = await asyncio.wait_for(
            pcp_bh.execute(pcp_fast_work()),
            timeout=1.0,
        )
        assert result == "pcp_done"
        assert pcp_completed.is_set()

        # Cleanup
        pncp_barrier.set()
        await asyncio.gather(*pncp_tasks)

    @pytest.mark.asyncio
    async def test_pncp_exhaustion_does_not_block_comprasgov(self):
        """When PNCP's semaphore is fully occupied, ComprasGov proceeds immediately."""
        pncp_bh = SourceBulkhead("PNCP", max_concurrent=1, timeout=10.0)
        cg_bh = SourceBulkhead("COMPRAS_GOV", max_concurrent=2, timeout=10.0)

        pncp_barrier = asyncio.Event()

        async def pncp_slow():
            await pncp_barrier.wait()

        async def cg_fast():
            return "cg_done"

        # Fill PNCP
        pncp_task = asyncio.create_task(pncp_bh.execute(pncp_slow()))
        await asyncio.sleep(0.02)
        assert pncp_bh.is_exhausted

        # ComprasGov still works
        result = await asyncio.wait_for(
            cg_bh.execute(cg_fast()),
            timeout=1.0,
        )
        assert result == "cg_done"

        pncp_barrier.set()
        await pncp_task

    @pytest.mark.asyncio
    async def test_all_three_sources_run_in_parallel(self):
        """All three sources can run concurrently without blocking each other."""
        pncp_bh = SourceBulkhead("PNCP", max_concurrent=5, timeout=10.0)
        pcp_bh = SourceBulkhead("PORTAL_COMPRAS", max_concurrent=3, timeout=10.0)
        cg_bh = SourceBulkhead("COMPRAS_GOV", max_concurrent=3, timeout=10.0)

        results = []

        async def work(name):
            results.append(f"{name}_start")
            await asyncio.sleep(0.01)
            results.append(f"{name}_end")
            return name

        tasks = [
            asyncio.create_task(pncp_bh.execute(work("pncp"))),
            asyncio.create_task(pcp_bh.execute(work("pcp"))),
            asyncio.create_task(cg_bh.execute(work("cg"))),
        ]
        outcomes = await asyncio.gather(*tasks)

        assert set(outcomes) == {"pncp", "pcp", "cg"}
        # All three should have started before any completed
        starts = [r for r in results if r.endswith("_start")]
        ends = [r for r in results if r.endswith("_end")]
        # With asyncio.sleep(0.01), starts should interleave with ends
        assert len(starts) == 3
        assert len(ends) == 3

    @pytest.mark.asyncio
    async def test_queued_tasks_execute_when_slot_frees(self):
        """When a slot frees up, queued tasks proceed."""
        bh = SourceBulkhead("TEST", max_concurrent=1, timeout=10.0)
        order = []

        async def work(name):
            order.append(f"{name}_start")
            await asyncio.sleep(0.01)
            order.append(f"{name}_end")
            return name

        t1 = asyncio.create_task(bh.execute(work("first")))
        await asyncio.sleep(0.005)
        t2 = asyncio.create_task(bh.execute(work("second")))

        await asyncio.gather(t1, t2)
        assert order == ["first_start", "first_end", "second_start", "second_end"]

    @pytest.mark.asyncio
    async def test_exception_in_task_releases_semaphore(self):
        """If the wrapped coroutine raises, the semaphore slot is released."""
        bh = SourceBulkhead("TEST", max_concurrent=1, timeout=10.0)

        async def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await bh.execute(failing())

        assert bh.active == 0
        assert bh.available == 1

        # Should be able to use the slot again
        async def ok():
            return "ok"

        result = await bh.execute(ok())
        assert result == "ok"


# ============================================================================
# AC5: Prometheus metrics per source
# ============================================================================


class TestBulkheadMetrics:
    """Verify Prometheus metrics emission."""

    @pytest.mark.asyncio
    async def test_active_requests_gauge_set_on_execute(self):
        """SOURCE_ACTIVE_REQUESTS gauge is set during execution."""
        bh = SourceBulkhead("TEST_SRC", max_concurrent=5, timeout=10.0)

        with patch("bulkhead.SOURCE_ACTIVE_REQUESTS") as mock_gauge:
            mock_labeled = MagicMock()
            mock_gauge.labels.return_value = mock_labeled

            async def work():
                await asyncio.sleep(0.01)
                return "done"

            await bh.execute(work())

            # Should have been called with source="TEST_SRC"
            mock_gauge.labels.assert_called_with(source="TEST_SRC")
            # Should set(1) on entry and set(0) on exit
            calls = mock_labeled.set.call_args_list
            assert len(calls) >= 2
            assert calls[0].args[0] == 1  # enter
            assert calls[-1].args[0] == 0  # exit

    @pytest.mark.asyncio
    async def test_pool_exhausted_counter_incremented(self):
        """SOURCE_POOL_EXHAUSTED counter is incremented when semaphore is full."""
        bh = SourceBulkhead("TEST_SRC", max_concurrent=1, timeout=10.0)
        barrier = asyncio.Event()

        with patch("bulkhead.SOURCE_POOL_EXHAUSTED") as mock_counter:
            mock_labeled = MagicMock()
            mock_counter.labels.return_value = mock_labeled

            async def slow():
                await barrier.wait()

            # Fill the semaphore
            t1 = asyncio.create_task(bh.execute(slow()))
            await asyncio.sleep(0.02)

            # This task should trigger exhausted counter
            async def quick():
                return "ok"

            t2 = asyncio.create_task(bh.execute(quick()))
            await asyncio.sleep(0.02)

            # Release
            barrier.set()
            await asyncio.gather(t1, t2)

            mock_counter.labels.assert_called_with(source="TEST_SRC")
            mock_labeled.inc.assert_called_once()


# ============================================================================
# Registry tests
# ============================================================================


class TestBulkheadRegistry:
    """Test the global bulkhead registry."""

    def test_register_and_get(self):
        bh = SourceBulkhead("MY_SOURCE", max_concurrent=5, timeout=30.0)
        register_bulkhead(bh)
        assert get_bulkhead("MY_SOURCE") is bh

    def test_get_nonexistent_returns_none(self):
        assert get_bulkhead("NONEXISTENT") is None

    def test_get_all_bulkheads(self):
        bh1 = SourceBulkhead("SRC1", max_concurrent=3, timeout=10.0)
        bh2 = SourceBulkhead("SRC2", max_concurrent=5, timeout=20.0)
        register_bulkhead(bh1)
        register_bulkhead(bh2)
        all_bh = get_all_bulkheads()
        assert len(all_bh) == 2
        assert "SRC1" in all_bh
        assert "SRC2" in all_bh

    def test_reset_clears_registry(self):
        register_bulkhead(SourceBulkhead("X", 1, 1.0))
        assert get_bulkhead("X") is not None
        reset_registry()
        assert get_bulkhead("X") is None

    def test_initialize_bulkheads_creates_three(self):
        bulkheads = initialize_bulkheads()
        assert "PNCP" in bulkheads
        assert "PORTAL_COMPRAS" in bulkheads
        assert "COMPRAS_GOV" in bulkheads
        # Also registered in global
        assert get_bulkhead("PNCP") is bulkheads["PNCP"]

    def test_initialize_bulkheads_idempotent(self):
        initialize_bulkheads()
        initialize_bulkheads()
        # Second call overwrites; registry still has 3
        assert len(get_all_bulkheads()) == 3


# ============================================================================
# Status/health serialization
# ============================================================================


class TestBulkheadStatus:
    """Test status() and to_dict() methods."""

    def test_status_healthy_when_idle(self):
        bh = SourceBulkhead("TEST", max_concurrent=5, timeout=10.0)
        assert bh.status() == "healthy"

    @pytest.mark.asyncio
    async def test_status_degraded_at_80_percent(self):
        bh = SourceBulkhead("TEST", max_concurrent=5, timeout=10.0)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        # Fill 4 out of 5 slots (80%)
        tasks = [asyncio.create_task(bh.execute(hold())) for _ in range(4)]
        await asyncio.sleep(0.02)
        assert bh.status() == "degraded"

        barrier.set()
        await asyncio.gather(*tasks)

    @pytest.mark.asyncio
    async def test_status_exhausted_at_100_percent(self):
        bh = SourceBulkhead("TEST", max_concurrent=2, timeout=10.0)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        tasks = [asyncio.create_task(bh.execute(hold())) for _ in range(2)]
        await asyncio.sleep(0.02)
        assert bh.status() == "exhausted"
        assert bh.is_exhausted

        barrier.set()
        await asyncio.gather(*tasks)

    def test_to_dict_contains_required_fields(self):
        bh = SourceBulkhead("PNCP", max_concurrent=5, timeout=80.0)
        d = bh.to_dict()
        assert d["max_concurrent"] == 5
        assert d["active"] == 0
        assert d["available"] == 5
        assert d["timeout"] == 80.0
        assert d["status"] == "healthy"
        assert d["exhausted_count"] == 0

    def test_repr(self):
        bh = SourceBulkhead("PNCP", max_concurrent=5, timeout=80.0)
        assert "PNCP" in repr(bh)
        assert "0/5" in repr(bh)


# ============================================================================
# Integration with ConsolidationService
# ============================================================================


class TestConsolidationBulkheadIntegration:
    """Test that ConsolidationService correctly uses bulkheads."""

    @pytest.mark.asyncio
    async def test_consolidation_wraps_fetch_with_bulkhead(self):
        """ConsolidationService uses bulkhead.execute() for source fetches."""
        from consolidation import ConsolidationService

        # Create a mock adapter
        mock_adapter = MagicMock()
        mock_adapter.code = "TEST_SOURCE"
        mock_adapter.metadata = MagicMock()
        mock_adapter.metadata.priority = 1
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        # fetch() yields one record
        from clients.base import UnifiedProcurement
        record = UnifiedProcurement(
            source_id="test-1",
            source_name="TEST_SOURCE",
            dedup_key="test-1",
            objeto="Test procurement",
            orgao="Test Org",
            uf="SP",
            valor_estimado=1000.0,
        )

        async def mock_fetch(*args, **kwargs):
            yield record

        mock_adapter.fetch = mock_fetch

        # Create bulkhead and spy on execute
        bulkhead = SourceBulkhead("TEST_SOURCE", max_concurrent=2, timeout=30.0)
        original_execute = bulkhead.execute

        execute_called = False

        async def spy_execute(coro):
            nonlocal execute_called
            execute_called = True
            return await original_execute(coro)

        bulkhead.execute = spy_execute

        svc = ConsolidationService(
            adapters={"TEST_SOURCE": mock_adapter},
            timeout_per_source=10,
            timeout_global=30,
            bulkheads={"TEST_SOURCE": bulkhead},
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-10")
        assert execute_called
        assert result.total_after_dedup >= 1

    @pytest.mark.asyncio
    async def test_consolidation_without_bulkhead_still_works(self):
        """ConsolidationService works normally when no bulkhead is provided."""
        from consolidation import ConsolidationService

        mock_adapter = MagicMock()
        mock_adapter.code = "NO_BH"
        mock_adapter.metadata = MagicMock()
        mock_adapter.metadata.priority = 1
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        async def mock_fetch(*args, **kwargs):
            return
            yield  # Make it an async generator

        mock_adapter.fetch = mock_fetch

        svc = ConsolidationService(
            adapters={"NO_BH": mock_adapter},
            timeout_per_source=10,
            timeout_global=30,
            # No bulkheads provided
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-10")
        # Should complete without error
        assert result.total_after_dedup == 0

    @pytest.mark.asyncio
    async def test_consolidation_bulkhead_from_registry(self):
        """ConsolidationService falls back to global registry for bulkheads."""
        from consolidation import ConsolidationService

        # Register a bulkhead in global registry
        bulkhead = SourceBulkhead("REGISTRY_SRC", max_concurrent=3, timeout=10.0)
        register_bulkhead(bulkhead)

        mock_adapter = MagicMock()
        mock_adapter.code = "REGISTRY_SRC"
        mock_adapter.metadata = MagicMock()
        mock_adapter.metadata.priority = 1
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        async def mock_fetch(*args, **kwargs):
            return
            yield

        mock_adapter.fetch = mock_fetch

        svc = ConsolidationService(
            adapters={"REGISTRY_SRC": mock_adapter},
            timeout_per_source=10,
            timeout_global=30,
            # No explicit bulkheads — should use registry
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-10")
        assert result is not None


# ============================================================================
# AC6: Health endpoint per-source status
# ============================================================================


class TestHealthEndpointBulkheadStatus:
    """Verify that health endpoint includes bulkhead data."""

    def test_bulkhead_to_dict_for_health_endpoint(self):
        """AC6: Bulkhead status is serializable for health endpoint."""
        bh = SourceBulkhead("PNCP", max_concurrent=5, timeout=80.0)
        status = bh.to_dict()

        # Required fields per AC6
        assert "status" in status
        assert status["status"] in ("healthy", "degraded", "exhausted")
        assert "max_concurrent" in status
        assert "active" in status
        assert "available" in status

    def test_all_bulkheads_status(self):
        """All three sources are serializable."""
        bulkheads = initialize_bulkheads()
        for name, bh in bulkheads.items():
            d = bh.to_dict()
            assert d["status"] == "healthy"
            assert d["active"] == 0


# ============================================================================
# HARDEN-015: Bulkhead Semaphore Acquire Timeout
# ============================================================================


class TestBulkheadAcquireTimeout:
    """HARDEN-015: Bulkhead acquire timeout splits timeout 50/50."""

    @pytest.mark.asyncio
    async def test_ac1_timeout_split_50_50(self):
        """AC1: 50% of timeout goes to acquire, 50% to execution."""
        bh = SourceBulkhead("TEST", max_concurrent=1, timeout=2.0)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        # Fill the single slot
        t1 = asyncio.create_task(bh.execute(hold()))
        await asyncio.sleep(0.02)

        # Second task should fail to acquire within 1.0s (50% of 2.0)
        start = asyncio.get_event_loop().time()
        with pytest.raises(BulkheadAcquireTimeoutError):
            await bh.execute(asyncio.sleep(0))
        elapsed = asyncio.get_event_loop().time() - start
        # Should have waited ~1.0s (50% of 2.0), not 2.0s
        assert 0.8 <= elapsed <= 1.5, f"Expected ~1.0s acquire budget, got {elapsed:.2f}s"

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_ac2_bulkhead_acquire_timeout_error(self):
        """AC2: BulkheadAcquireTimeoutError raised when acquire times out."""
        bh = SourceBulkhead("PNCP", max_concurrent=1, timeout=0.2)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        t1 = asyncio.create_task(bh.execute(hold()))
        await asyncio.sleep(0.02)

        with pytest.raises(BulkheadAcquireTimeoutError) as exc_info:
            await bh.execute(asyncio.sleep(0))

        assert exc_info.value.source == "PNCP"
        assert exc_info.value.timeout == 0.1  # 50% of 0.2
        assert "PNCP" in str(exc_info.value)

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_ac2_semaphore_not_leaked_on_acquire_timeout(self):
        """AC2: After acquire timeout, semaphore is not corrupted."""
        bh = SourceBulkhead("TEST", max_concurrent=1, timeout=0.1)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        t1 = asyncio.create_task(bh.execute(hold()))
        await asyncio.sleep(0.02)

        # This should timeout on acquire
        with pytest.raises(BulkheadAcquireTimeoutError):
            await bh.execute(asyncio.sleep(0))

        # Release the slot
        barrier.set()
        await t1

        # Bulkhead should be usable again
        async def quick():
            return "ok"

        result = await bh.execute(quick())
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_ac3_consolidation_skipped_status(self):
        """AC3: UF marked as 'skipped' (not 'error') on acquire timeout."""
        from consolidation import ConsolidationService, AllSourcesFailedError

        mock_adapter = MagicMock()
        mock_adapter.code = "PNCP"
        mock_adapter.metadata = MagicMock()
        mock_adapter.metadata.priority = 1
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        async def mock_fetch(*args, **kwargs):
            return
            yield

        mock_adapter.fetch = mock_fetch

        # Create a bulkhead with tiny timeout that will fail on acquire
        bulkhead = SourceBulkhead("PNCP", max_concurrent=1, timeout=0.1)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        # Fill the single slot
        t1 = asyncio.create_task(bulkhead.execute(hold()))
        await asyncio.sleep(0.02)

        svc = ConsolidationService(
            adapters={"PNCP": mock_adapter},
            timeout_per_source=10,
            timeout_global=30,
            bulkheads={"PNCP": bulkhead},
        )

        # When all sources are skipped (no data), AllSourcesFailedError is raised
        # but the source_errors should contain the acquire timeout message
        with pytest.raises(AllSourcesFailedError) as exc_info:
            await svc.fetch_all("2026-01-01", "2026-01-10")

        # Verify the error mentions acquire timeout (not generic error)
        assert "acquire timeout" in str(exc_info.value).lower()

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_ac3_skipped_status_in_wrap_source(self):
        """AC3: _wrap_source_inner returns status='skipped' on acquire timeout."""
        from consolidation import ConsolidationService

        mock_adapter = MagicMock()
        mock_adapter.code = "PNCP"
        mock_adapter.metadata = MagicMock()
        mock_adapter.metadata.priority = 1
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        async def mock_fetch(*args, **kwargs):
            return
            yield

        mock_adapter.fetch = mock_fetch

        bulkhead = SourceBulkhead("PNCP", max_concurrent=1, timeout=0.1)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        t1 = asyncio.create_task(bulkhead.execute(hold()))
        await asyncio.sleep(0.02)

        svc = ConsolidationService(
            adapters={"PNCP": mock_adapter},
            timeout_per_source=10,
            timeout_global=30,
            bulkheads={"PNCP": bulkhead},
        )

        import time
        result = await svc._wrap_source_inner(
            "PNCP", mock_adapter, "2026-01-01", "2026-01-10", None,
            10.0, time.time(), [], MagicMock(),
        )

        assert result["status"] == "skipped"
        assert result["code"] == "PNCP"
        assert "acquire timeout" in result["error"].lower()
        assert result["records"] == []

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_ac4_metric_incremented(self):
        """AC4: smartlic_bulkhead_acquire_timeout_total incremented on acquire timeout."""
        bh = SourceBulkhead("PNCP", max_concurrent=1, timeout=0.1)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        t1 = asyncio.create_task(bh.execute(hold()))
        await asyncio.sleep(0.02)

        with patch("bulkhead.BULKHEAD_ACQUIRE_TIMEOUT") as mock_counter:
            mock_labeled = MagicMock()
            mock_counter.labels.return_value = mock_labeled

            with pytest.raises(BulkheadAcquireTimeoutError):
                await bh.execute(asyncio.sleep(0))

            mock_counter.labels.assert_called_with(source="PNCP")
            mock_labeled.inc.assert_called_once()

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_ac5_27_ufs_bulkhead_size_5(self):
        """AC5: 27 UFs competing for bulkhead size=5 — some skip, some succeed."""
        bh = SourceBulkhead("PNCP", max_concurrent=5, timeout=0.5)
        results = {"completed": 0, "skipped": 0}

        async def uf_work(uf_name):
            """Simulate UF fetch that takes 0.3s."""
            await asyncio.sleep(0.3)
            return uf_name

        async def try_uf(uf_name):
            try:
                result = await bh.execute(uf_work(uf_name))
                results["completed"] += 1
                return ("success", result)
            except BulkheadAcquireTimeoutError:
                results["skipped"] += 1
                return ("skipped", uf_name)

        ufs = [f"UF-{i:02d}" for i in range(27)]
        tasks = [asyncio.create_task(try_uf(uf)) for uf in ufs]
        outcomes = await asyncio.gather(*tasks)  # noqa: F841

        # With 5 slots, 0.5s total timeout (0.25s acquire budget), 0.3s work:
        # First 5 start immediately, next batch waits ~0.3s for slots.
        # Some later UFs will timeout on acquire.
        assert results["completed"] > 0, "Some UFs should complete"
        assert results["skipped"] > 0, "Some UFs should be skipped due to acquire timeout"
        assert results["completed"] + results["skipped"] == 27

        # Verify bulkhead is clean after all tasks complete
        assert bh.active == 0

    @pytest.mark.asyncio
    async def test_timeout_override_parameter(self):
        """execute() accepts optional timeout override."""
        bh = SourceBulkhead("TEST", max_concurrent=1, timeout=10.0)
        barrier = asyncio.Event()

        async def hold():
            await barrier.wait()

        t1 = asyncio.create_task(bh.execute(hold()))
        await asyncio.sleep(0.02)

        # Override with tiny timeout — should fail fast
        with pytest.raises(BulkheadAcquireTimeoutError):
            await bh.execute(asyncio.sleep(0), timeout=0.1)

        barrier.set()
        await t1

    @pytest.mark.asyncio
    async def test_successful_acquire_no_error(self):
        """When slot is available, no acquire timeout even with short timeout."""
        bh = SourceBulkhead("TEST", max_concurrent=5, timeout=0.5)

        async def quick():
            return "ok"

        # Slot is available — should succeed immediately
        result = await bh.execute(quick())
        assert result == "ok"
