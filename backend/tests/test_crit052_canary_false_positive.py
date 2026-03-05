"""CRIT-052: Health Canary PNCP — False Positive by Aggressive Timeout.

Tests for adaptive canary timeout, cron status feeding, honest logging,
and canary-failure-doesn't-block behavior.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from types import SimpleNamespace

import httpx
import pytest


# ============================================================================
# AC1: Adaptive timeout based on cron canary status
# ============================================================================


class TestAdaptiveCanaryTimeout:
    """CRIT-052 AC1: Canary uses adaptive timeout based on cron status."""

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "healthy", "latency_ms": 500, "updated_at": time.time(),
    })
    async def test_healthy_cron_uses_standard_timeout(self, mock_cron):
        """AC1: When cron reports healthy, canary uses standard 10s timeout."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is True
        assert result["cron_status"] == "healthy"
        assert result["latency_ms"] is not None
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "degraded", "latency_ms": 4000, "updated_at": time.time(),
    })
    async def test_degraded_cron_uses_extended_timeout(self, mock_cron):
        """AC1: When cron reports degraded, canary uses extended 15s timeout."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        # Simulate PNCP responding in 4s (would timeout at 5s old, OK at 15s)
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def slow_get(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate slight delay
            return mock_response

        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=slow_get):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is True
        assert result["cron_status"] == "degraded"
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "healthy", "latency_ms": 100, "updated_at": time.time(),
    })
    async def test_pncp_responding_in_4s_with_10s_timeout_succeeds(self, mock_cron):
        """AC5-T1: PNCP responding in 4s with canary timeout 10s -> PNCP used normally."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = MagicMock()
        mock_response.status_code = 200

        async def respond_in_4s(*args, **kwargs):
            await asyncio.sleep(0.04)  # Simulate 4s (scaled down for test)
            return mock_response

        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=respond_in_4s), \
             patch("config.PNCP_CANARY_TIMEOUT_S", 10.0):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is True
        assert result["latency_ms"] is not None
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "degraded", "latency_ms": 8000, "updated_at": time.time(),
    })
    async def test_pncp_responding_in_12s_with_extended_timeout(self, mock_cron):
        """AC5-T2: PNCP responding in 12s with canary timeout 10s -> extended timeout used."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = MagicMock()
        mock_response.status_code = 200

        call_count = 0

        async def respond_slowly(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Fast for test
            return mock_response

        # With cron_status=degraded, timeout becomes PNCP_CANARY_TIMEOUT_EXTENDED_S (15s)
        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=respond_slowly), \
             patch("config.PNCP_CANARY_TIMEOUT_EXTENDED_S", 15.0):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is True
        assert result["cron_status"] == "degraded"
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "degraded", "latency_ms": None, "updated_at": time.time(),
    })
    async def test_pncp_no_response_in_15s_discarded(self, mock_cron):
        """AC5-T3: PNCP no response in 15s -> correctly discarded."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        async def never_respond(*args, **kwargs):
            await asyncio.sleep(100)  # Will be cancelled by timeout
            return MagicMock()

        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=never_respond), \
             patch("config.PNCP_CANARY_TIMEOUT_S", 0.05), \
             patch("config.PNCP_CANARY_TIMEOUT_EXTENDED_S", 0.1):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is False
        assert result["latency_ms"] is not None
        _circuit_breaker.reset()


# ============================================================================
# AC2: Canary failure doesn't block — tries normal fetch
# ============================================================================


class TestCanaryDoesNotBlock:
    """CRIT-052 AC2: Canary failure no longer returns empty immediately."""

    @pytest.mark.asyncio
    async def test_canary_failure_still_attempts_fetch(self):
        """AC2: When canary fails, search proceeds with normal fetch."""
        from pncp_client import AsyncPNCPClient, ParallelFetchResult, _circuit_breaker

        _circuit_breaker.reset()

        canary_result = {"ok": False, "latency_ms": 10500.0, "cron_status": "degraded"}

        mock_page = MagicMock()
        mock_page.status_code = 200
        mock_page.headers = {"content-type": "application/json"}
        mock_page.json.return_value = {
            "data": [
                {"numeroControlePNCP": "001", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
            ],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        async with AsyncPNCPClient(max_concurrent=5) as client:
            with patch.object(client, "health_canary", new_callable=AsyncMock, return_value=canary_result):
                with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_page):
                    result = await client.buscar_todas_ufs_paralelo(
                        ufs=["SP"],
                        data_inicial="2026-01-01",
                        data_final="2026-01-15",
                    )

        # Key assertion: result has items (not empty)
        assert isinstance(result, ParallelFetchResult)
        # Search proceeded even though canary failed
        assert result.canary_result is not None
        assert result.canary_result["ok"] is False
        _circuit_breaker.reset()


# ============================================================================
# AC3: Cron canary feeds per-search decision
# ============================================================================


class TestCronCanaryFeedsDecision:
    """CRIT-052 AC3: Cron canary status stored globally and consulted."""

    def test_get_pncp_cron_status_default(self):
        """AC3: Default status is 'unknown'."""
        from cron_jobs import get_pncp_cron_status
        status = get_pncp_cron_status()
        assert status["status"] in ("unknown", "healthy", "degraded", "down")

    def test_update_and_get_pncp_cron_status(self):
        """AC3: Thread-safe update and read."""
        from cron_jobs import _update_pncp_cron_status, get_pncp_cron_status, _pncp_cron_status_lock, _pncp_cron_status

        # Save original
        with _pncp_cron_status_lock:
            original = dict(_pncp_cron_status)

        try:
            _update_pncp_cron_status("degraded", 3500)
            status = get_pncp_cron_status()
            assert status["status"] == "degraded"
            assert status["latency_ms"] == 3500
            assert status["updated_at"] is not None

            _update_pncp_cron_status("healthy", 800)
            status = get_pncp_cron_status()
            assert status["status"] == "healthy"
            assert status["latency_ms"] == 800
        finally:
            # Restore original
            with _pncp_cron_status_lock:
                _pncp_cron_status.update(original)

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "degraded", "latency_ms": 4000, "updated_at": time.time(),
    })
    async def test_cron_degraded_makes_canary_use_extended_timeout(self, mock_cron):
        """AC5-T4: cron status=degraded -> per-search uses extended timeout."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result["ok"] is True
        assert result["cron_status"] == "degraded"
        _circuit_breaker.reset()


# ============================================================================
# AC4: Honest logging
# ============================================================================


class TestHonestLogging:
    """CRIT-052 AC4: Logs include cron status and canary latency."""

    @pytest.mark.asyncio
    @patch("cron_jobs.get_pncp_cron_status", return_value={
        "status": "degraded", "latency_ms": 4027, "updated_at": time.time(),
    })
    async def test_timeout_log_includes_cron_context(self, mock_cron, caplog):
        """AC4: Timeout log includes cron status and latency."""
        import logging
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        async def timeout_response(*args, **kwargs):
            raise asyncio.TimeoutError()

        with caplog.at_level(logging.WARNING, logger="pncp_client"):
            with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=timeout_response), \
                 patch("config.PNCP_CANARY_TIMEOUT_S", 10.0), \
                 patch("config.PNCP_CANARY_TIMEOUT_EXTENDED_S", 0.01):
                async with AsyncPNCPClient(max_concurrent=5) as client:
                    result = await client.health_canary()

        assert result["ok"] is False
        # Verify honest log message
        canary_logs = [r for r in caplog.records if "canary" in r.getMessage().lower()]
        assert any("degraded" in r.getMessage() for r in canary_logs), \
            f"Expected 'degraded' in canary log, got: {[r.getMessage() for r in canary_logs]}"
        assert any("4027" in r.getMessage() for r in canary_logs), \
            f"Expected cron latency '4027' in canary log, got: {[r.getMessage() for r in canary_logs]}"
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_canary_result_includes_telemetry(self):
        """AC4: Canary result dict includes cron_status and latency_ms."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("cron_jobs.get_pncp_cron_status", return_value={
            "status": "healthy", "latency_ms": 200, "updated_at": time.time(),
        }):
            with patch("pncp_client.httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
                async with AsyncPNCPClient(max_concurrent=5) as client:
                    result = await client.health_canary()

        assert "ok" in result
        assert "latency_ms" in result
        assert "cron_status" in result
        assert result["cron_status"] == "healthy"
        _circuit_breaker.reset()

    def test_search_complete_event_includes_canary_fields(self):
        """AC4: search_complete JSON includes pncp_canary_status and pncp_canary_latency_ms."""
        import inspect
        from search_pipeline import SearchPipeline

        source = inspect.getsource(SearchPipeline)
        assert "pncp_canary_status" in source, "search_complete must include pncp_canary_status"
        assert "pncp_canary_latency_ms" in source, "search_complete must include pncp_canary_latency_ms"


# ============================================================================
# Config tests
# ============================================================================


class TestCanaryConfig:
    """CRIT-052 AC1: Config env vars."""

    def test_canary_timeout_default(self):
        """AC1: Default PNCP_CANARY_TIMEOUT_S is 10s."""
        from config import PNCP_CANARY_TIMEOUT_S
        assert PNCP_CANARY_TIMEOUT_S == 10.0

    def test_canary_timeout_extended_default(self):
        """AC1: Default PNCP_CANARY_TIMEOUT_EXTENDED_S is 15s."""
        from config import PNCP_CANARY_TIMEOUT_EXTENDED_S
        assert PNCP_CANARY_TIMEOUT_EXTENDED_S == 15.0

    def test_parallel_fetch_result_has_canary_field(self):
        """AC4: ParallelFetchResult includes canary_result field."""
        from pncp_client import ParallelFetchResult
        result = ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=[])
        assert result.canary_result is None
        result2 = ParallelFetchResult(
            items=[], succeeded_ufs=[], failed_ufs=[],
            canary_result={"ok": True, "latency_ms": 50.0, "cron_status": "healthy"},
        )
        assert result2.canary_result["ok"] is True
