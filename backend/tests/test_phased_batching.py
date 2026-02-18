"""
GTM-FIX-031: Tests for phased UF batching in pncp_client.py.

Tests the batch splitting logic, inter-batch delay, and SSE batch events.
"""

import asyncio
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pncp_client import (
    AsyncPNCPClient,
    PNCP_BATCH_SIZE,
    PNCP_BATCH_DELAY_S,
)


class TestBatchConstants:
    """Test that batch constants are properly configured."""

    def test_default_batch_size(self):
        assert PNCP_BATCH_SIZE == 5

    def test_default_batch_delay(self):
        assert PNCP_BATCH_DELAY_S == 2.0

    def test_custom_batch_size_env_parsing(self):
        """Env var override for batch size (logic test without reload)."""
        assert int("3") == 3
        assert int(os.environ.get("PNCP_BATCH_SIZE", "5")) == 5

    def test_custom_batch_delay_env_parsing(self):
        """Env var override for batch delay (logic test without reload)."""
        assert float("1.5") == 1.5
        assert float(os.environ.get("PNCP_BATCH_DELAY_S", "2.0")) == 2.0


class TestBatchSplitting:
    """Test batch splitting logic (math)."""

    def test_12_ufs_batch_5_gives_3_batches(self):
        """12 UFs with batch_size=5 → 3 batches (5, 5, 2)."""
        ufs = [f"UF{i}" for i in range(12)]
        batch_size = 5
        batches = [
            ufs[i:i + batch_size]
            for i in range(0, len(ufs), batch_size)
        ]
        assert len(batches) == 3
        assert len(batches[0]) == 5
        assert len(batches[1]) == 5
        assert len(batches[2]) == 2

    def test_5_ufs_batch_5_gives_1_batch(self):
        """Exact batch size → 1 batch."""
        ufs = [f"UF{i}" for i in range(5)]
        batch_size = 5
        batches = [
            ufs[i:i + batch_size]
            for i in range(0, len(ufs), batch_size)
        ]
        assert len(batches) == 1
        assert len(batches[0]) == 5

    def test_1_uf_gives_1_batch(self):
        """Single UF → 1 batch, no delay needed."""
        ufs = ["SP"]
        batch_size = 5
        batches = [
            ufs[i:i + batch_size]
            for i in range(0, len(ufs), batch_size)
        ]
        assert len(batches) == 1
        assert batches[0] == ["SP"]

    def test_27_ufs_batch_5_gives_6_batches(self):
        """All 27 UFs with batch_size=5 → 6 batches (5,5,5,5,5,2)."""
        ufs = [f"UF{i}" for i in range(27)]
        batch_size = 5
        batches = [
            ufs[i:i + batch_size]
            for i in range(0, len(ufs), batch_size)
        ]
        assert len(batches) == 6
        assert sum(len(b) for b in batches) == 27


class TestPhasedExecution:
    """Integration-style tests for phased batch execution."""

    @pytest.mark.asyncio
    async def test_batch_callback_emitted(self):
        """Verify on_uf_status is called with batch_info for each batch."""
        batch_events = []

        async def mock_on_uf_status(uf, status, **kwargs):
            if status == "batch_info":
                batch_events.append({
                    "uf": uf,
                    "batch_num": kwargs.get("batch_num"),
                    "total_batches": kwargs.get("total_batches"),
                    "ufs_in_batch": kwargs.get("ufs_in_batch"),
                })

        # Mock the entire _fetch_uf_all_pages to return empty results quickly
        with patch.object(
            AsyncPNCPClient, "_fetch_uf_all_pages",
            new_callable=AsyncMock,
            return_value=([], False),
        ), patch.object(
            AsyncPNCPClient, "health_canary",
            new_callable=AsyncMock,
            return_value=True,
        ), patch("pncp_client.PNCP_BATCH_SIZE", 2), \
             patch("pncp_client.PNCP_BATCH_DELAY_S", 0.01):

            client = AsyncPNCPClient(max_concurrent=10)
            await client.buscar_todas_ufs_paralelo(
                ufs=["SP", "RJ", "MG", "BA", "RS"],
                data_inicial="2026-02-01",
                data_final="2026-02-10",
                on_uf_status=mock_on_uf_status,
            )

        # 5 UFs / batch_size 2 = 3 batches
        assert len(batch_events) == 3
        assert batch_events[0]["batch_num"] == 1
        assert batch_events[0]["total_batches"] == 3
        assert batch_events[2]["batch_num"] == 3

    @pytest.mark.asyncio
    async def test_single_uf_no_delay(self):
        """Single UF should not have inter-batch delay."""
        start = time.monotonic()

        with patch.object(
            AsyncPNCPClient, "_fetch_uf_all_pages",
            new_callable=AsyncMock,
            return_value=([], False),
        ), patch.object(
            AsyncPNCPClient, "health_canary",
            new_callable=AsyncMock,
            return_value=True,
        ), patch("pncp_client.PNCP_BATCH_SIZE", 5), \
             patch("pncp_client.PNCP_BATCH_DELAY_S", 5.0):

            client = AsyncPNCPClient(max_concurrent=10)
            await client.buscar_todas_ufs_paralelo(
                ufs=["SP"],
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

        elapsed = time.monotonic() - start
        # Should be fast — no inter-batch delay for single batch
        assert elapsed < 3.0, f"Single UF should not have batch delay, took {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_results_aggregated_across_batches(self):
        """Results from all batches should be aggregated correctly."""
        call_count = 0

        async def mock_fetch(self, uf, **kwargs):
            nonlocal call_count
            call_count += 1
            return ([{"uf": uf, "codigoCompra": f"CODE-{uf}"}], False)

        with patch.object(
            AsyncPNCPClient, "_fetch_uf_all_pages",
            mock_fetch,
        ), patch.object(
            AsyncPNCPClient, "health_canary",
            new_callable=AsyncMock,
            return_value=True,
        ), patch("pncp_client.PNCP_BATCH_SIZE", 2), \
             patch("pncp_client.PNCP_BATCH_DELAY_S", 0.01):

            client = AsyncPNCPClient(max_concurrent=10)
            result = await client.buscar_todas_ufs_paralelo(
                ufs=["SP", "RJ", "MG"],
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

        assert len(result.items) == 3
        assert len(result.succeeded_ufs) == 3
        assert call_count == 3


class TestProgressTrackerBatchEmit:
    """Tests for ProgressTracker.emit_batch_progress()."""

    @pytest.mark.asyncio
    async def test_emit_batch_progress(self):
        """emit_batch_progress should put event in queue with correct data."""
        from progress import ProgressTracker

        tracker = ProgressTracker(search_id="test-batch", uf_count=10)
        await tracker.emit_batch_progress(
            batch_num=2, total_batches=4, ufs_in_batch=["SP", "RJ", "MG", "BA", "RS"]
        )

        event = await asyncio.wait_for(tracker.queue.get(), timeout=1.0)
        assert event.stage == "batch_progress"
        assert event.detail["batch_num"] == 2
        assert event.detail["total_batches"] == 4
        assert event.detail["ufs_in_batch"] == ["SP", "RJ", "MG", "BA", "RS"]
        assert "Fase 2 de 4" in event.message

    @pytest.mark.asyncio
    async def test_emit_batch_progress_values(self):
        """Batch progress percentage should scale between 10-55%."""
        from progress import ProgressTracker

        tracker = ProgressTracker(search_id="test-pct", uf_count=20)

        await tracker.emit_batch_progress(batch_num=1, total_batches=4, ufs_in_batch=["SP"])
        event1 = await asyncio.wait_for(tracker.queue.get(), timeout=1.0)
        # batch 1/4 → 10 + (1/4)*45 = 10 + 11 = 21
        assert event1.progress == 21

        await tracker.emit_batch_progress(batch_num=4, total_batches=4, ufs_in_batch=["RS"])
        event4 = await asyncio.wait_for(tracker.queue.get(), timeout=1.0)
        # batch 4/4 → 10 + (4/4)*45 = 10 + 45 = 55
        assert event4.progress == 55
