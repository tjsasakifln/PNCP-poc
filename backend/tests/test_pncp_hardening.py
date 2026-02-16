"""Unit tests for PNCP client hardening (STORY-252 Track 2).

Tests cover:
- AC6: Per-modality timeout (15s default, configurable)
- AC7: Reduced per-UF timeout (90s -> 30s)
- AC8: Explicit circuit breaker (5 consecutive failures -> 5min degraded)
- AC9: Retry on timeout (1 retry with 3s backoff)
- AC10: PNCP health canary before full search
- AC11: Logging on health canary failure
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pncp_client import (
    AsyncPNCPClient,
    ParallelFetchResult,
    PNCPCircuitBreaker,
    PNCPDegradedError,
    _circuit_breaker,
    get_circuit_breaker,
    PNCP_TIMEOUT_PER_MODALITY,
    PNCP_MODALITY_RETRY_BACKOFF,
)
from exceptions import PNCPAPIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pncp_response(data=None, paginas_restantes=0, total_registros=0):
    """Create a mock PNCP API response dict."""
    items = data or []
    return {
        "data": items,
        "totalRegistros": total_registros or len(items),
        "totalPaginas": 1,
        "paginaAtual": 1,
        "paginasRestantes": paginas_restantes,
    }


def _make_item(item_id: str, uf: str = "SP"):
    """Create a minimal PNCP procurement item for testing."""
    return {
        "numeroControlePNCP": item_id,
        "objetoCompra": f"Test item {item_id}",
        "valorTotalEstimado": 100000,
        "orgaoEntidade": {"razaoSocial": "Test Org"},
        "unidadeOrgao": {"ufSigla": uf, "municipioNome": "Test City", "nomeUnidade": "Unit"},
    }


# ---------------------------------------------------------------------------
# AC8: PNCPCircuitBreaker Tests
# ---------------------------------------------------------------------------

class TestPNCPCircuitBreaker:
    """Test circuit breaker behavior (STORY-252 AC8)."""

    def setup_method(self):
        """Create a fresh circuit breaker for each test."""
        self.cb = PNCPCircuitBreaker(threshold=5, cooldown_seconds=300)

    @pytest.mark.asyncio
    async def test_initial_state_is_healthy(self):
        """Circuit breaker starts in healthy (non-degraded) state."""
        assert self.cb.is_degraded is False
        assert self.cb.consecutive_failures == 0
        assert self.cb.degraded_until is None

    @pytest.mark.asyncio
    async def test_failures_below_threshold_dont_trip(self):
        """Failures below threshold do not trip the breaker."""
        for _ in range(4):  # threshold is 5
            await self.cb.record_failure()

        assert self.cb.consecutive_failures == 4
        assert self.cb.is_degraded is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_at_threshold(self):
        """Circuit breaker trips after exactly threshold failures."""
        for _ in range(5):
            await self.cb.record_failure()

        assert self.cb.consecutive_failures == 5
        assert self.cb.is_degraded is True
        assert self.cb.degraded_until is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_above_threshold(self):
        """Additional failures after tripping don't cause errors."""
        for _ in range(7):
            await self.cb.record_failure()

        assert self.cb.consecutive_failures == 7
        assert self.cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_success_resets_counter(self):
        """A successful request resets the failure counter."""
        for _ in range(3):
            await self.cb.record_failure()
        assert self.cb.consecutive_failures == 3

        await self.cb.record_success()
        assert self.cb.consecutive_failures == 0
        assert self.cb.is_degraded is False

    @pytest.mark.asyncio
    async def test_success_after_trip_resets_counter_but_stays_degraded(self):
        """Success resets counter but degraded_until persists until cooldown."""
        for _ in range(5):
            await self.cb.record_failure()
        assert self.cb.is_degraded is True

        await self.cb.record_success()
        assert self.cb.consecutive_failures == 0
        # Still degraded because degraded_until hasn't expired
        assert self.cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_cooldown_expires_resets_degraded(self):
        """After cooldown period expires, circuit breaker resets automatically."""
        for _ in range(5):
            await self.cb.record_failure()
        assert self.cb.is_degraded is True

        # Simulate cooldown expiry by setting degraded_until to the past
        self.cb.degraded_until = time.time() - 1

        # After STORY-257A, is_degraded is read-only — must call try_recover()
        await self.cb.try_recover()

        assert self.cb.is_degraded is False
        assert self.cb.consecutive_failures == 0
        assert self.cb.degraded_until is None

    def test_manual_reset(self):
        """Manual reset clears all state."""
        self.cb.consecutive_failures = 10
        self.cb.degraded_until = time.time() + 9999

        self.cb.reset()

        assert self.cb.consecutive_failures == 0
        assert self.cb.degraded_until is None
        assert self.cb.is_degraded is False

    @pytest.mark.asyncio
    async def test_custom_threshold_and_cooldown(self):
        """Custom threshold and cooldown values work correctly."""
        cb = PNCPCircuitBreaker(threshold=2, cooldown_seconds=10)

        await cb.record_failure()
        assert cb.is_degraded is False

        await cb.record_failure()
        assert cb.is_degraded is True
        assert cb.cooldown_seconds == 10


class TestCircuitBreakerSingleton:
    """Test module-level circuit breaker singleton."""

    def setup_method(self):
        """Reset the global circuit breaker before each test."""
        _circuit_breaker.reset()

    def test_get_circuit_breaker_returns_singleton(self):
        """get_circuit_breaker() returns the same instance."""
        cb1 = get_circuit_breaker()
        cb2 = get_circuit_breaker()
        assert cb1 is cb2
        assert cb1 is _circuit_breaker


# ---------------------------------------------------------------------------
# AC6: Per-modality timeout tests
# ---------------------------------------------------------------------------

class TestPerModalityTimeout:
    """Test that each modality has independent timeout (STORY-252 AC6)."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_slow_modality_doesnt_block_others(self):
        """If modality 4 hangs, modalities 5, 6, 7 should still return results."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()  # dummy — we'll mock _fetch_single_modality

        items_mod5 = [_make_item("ID-5-1"), _make_item("ID-5-2")]
        items_mod6 = [_make_item("ID-6-1")]
        items_mod7 = [_make_item("ID-7-1"), _make_item("ID-7-2"), _make_item("ID-7-3")]

        call_count = 0

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            nonlocal call_count
            call_count += 1
            if modalidade == 4:
                # Simulate a hang that exceeds the per-modality timeout
                await asyncio.sleep(999)
                return []  # never reached
            elif modalidade == 5:
                return items_mod5
            elif modalidade == 6:
                return items_mod6
            elif modalidade == 7:
                return items_mod7
            return []

        with patch.object(
            client, "_fetch_single_modality", side_effect=mock_fetch_single
        ), patch.object(
            type(client), "_fetch_modality_with_timeout",
            # We need the real method but with a short timeout for testing
            wraps=None,
        ):
            # Use the real _fetch_modality_with_timeout but patch the timeout
            # to be very short for the test

            async def fast_timeout_method(self_inner, uf, data_inicial, data_final,
                                           modalidade, status=None, max_pages=500):
                """Same as real method but with 0.1s timeout for fast tests."""
                for attempt in range(2):
                    try:
                        result = await asyncio.wait_for(
                            self_inner._fetch_single_modality(
                                uf=uf,
                                data_inicial=data_inicial,
                                data_final=data_final,
                                modalidade=modalidade,
                                status=status,
                                max_pages=max_pages,
                            ),
                            timeout=0.1,  # fast timeout for tests
                        )
                        return result
                    except asyncio.TimeoutError:
                        await _circuit_breaker.record_failure()
                        if attempt == 0:
                            await asyncio.sleep(0.01)  # fast backoff for tests
                return []

            with patch.object(
                AsyncPNCPClient, "_fetch_modality_with_timeout", fast_timeout_method
            ):
                result = await client._fetch_uf_all_pages(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidades=[4, 5, 6, 7],
                )

        # Modality 4 timed out, but 5, 6, 7 should have returned items
        # The items are normalized by _normalize_item which adds codigoCompra
        result_ids = {
            item.get("codigoCompra") or item.get("numeroControlePNCP")
            for item in result
        }

        assert "ID-5-1" in result_ids
        assert "ID-5-2" in result_ids
        assert "ID-6-1" in result_ids
        assert "ID-7-1" in result_ids
        assert "ID-7-2" in result_ids
        assert "ID-7-3" in result_ids
        # Total: 6 items from modalities 5+6+7
        assert len(result) == 6


# ---------------------------------------------------------------------------
# AC9: Retry on timeout (1 retry with 3s backoff)
# ---------------------------------------------------------------------------

class TestModalityRetry:
    """Test per-modality retry on timeout (STORY-252 AC9)."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """If first attempt times out, retry should succeed."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        attempt_count = 0

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                # First attempt: hang forever (will timeout)
                await asyncio.sleep(999)
                return []
            else:
                # Second attempt: succeed immediately
                return [_make_item("RETRY-OK")]

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            # Use short timeouts for testing
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.1), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                result = await client._fetch_modality_with_timeout(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidade=6,
                )

        assert attempt_count == 2
        assert len(result) == 1
        assert result[0]["numeroControlePNCP"] == "RETRY-OK"

    @pytest.mark.asyncio
    async def test_both_attempts_timeout_returns_empty(self):
        """If both attempts timeout, returns empty list."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        attempt_count = 0

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            nonlocal attempt_count
            attempt_count += 1
            await asyncio.sleep(999)  # always hang
            return []

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.1), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                result = await client._fetch_modality_with_timeout(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidade=6,
                )

        assert attempt_count == 2
        assert result == []

    @pytest.mark.asyncio
    async def test_circuit_breaker_records_failures_on_timeout(self):
        """Each timeout attempt records a failure in the circuit breaker."""
        _circuit_breaker.reset()
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        async def mock_fetch_single(*args, **kwargs):
            await asyncio.sleep(999)
            return []

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.1), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                await client._fetch_modality_with_timeout(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidade=6,
                )

        # 2 timeout attempts = 2 recorded failures
        assert _circuit_breaker.consecutive_failures == 2


# ---------------------------------------------------------------------------
# AC8 (continued): Circuit breaker activates after N timeouts
# ---------------------------------------------------------------------------

class TestCircuitBreakerActivation:
    """Test circuit breaker activation during actual modality fetches."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_after_multiple_modality_timeouts(self):
        """Circuit breaker trips after 5 consecutive timeout failures."""
        cb = PNCPCircuitBreaker(threshold=5, cooldown_seconds=300)

        # Record 5 failures
        for _ in range(5):
            await cb.record_failure()

        assert cb.is_degraded is True

    @pytest.mark.asyncio
    async def test_degraded_uf_fetch_returns_empty(self):
        """When circuit breaker is degraded, _fetch_uf_all_pages returns empty."""
        _circuit_breaker.degraded_until = time.time() + 300
        _circuit_breaker.consecutive_failures = 5

        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        result = await client._fetch_uf_all_pages(
            uf="SP",
            data_inicial="2026-01-01",
            data_final="2026-01-31",
            modalidades=[4, 5, 6, 7],
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self):
        """Successful modality fetch resets the circuit breaker counter."""
        _circuit_breaker.consecutive_failures = 3

        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        async def mock_fetch_page(*args, **kwargs):
            return _make_pncp_response(data=[_make_item("OK-1")], paginas_restantes=0)

        with patch.object(client, "_fetch_page_async", side_effect=mock_fetch_page):
            result = await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                modalidade=6,
            )

        assert len(result) == 1
        assert _circuit_breaker.consecutive_failures == 0


# ---------------------------------------------------------------------------
# AC10/AC11: Health Canary Tests
# ---------------------------------------------------------------------------

class TestHealthCanary:
    """Test PNCP health canary (STORY-252 AC10/AC11)."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_health_canary_success(self):
        """Health canary returns True on 200 response."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is True
        assert _circuit_breaker.is_degraded is False

    @pytest.mark.asyncio
    async def test_health_canary_success_204(self):
        """Health canary returns True on 204 (no content) response."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_response = MagicMock()
        mock_response.status_code = 204

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is True
        assert _circuit_breaker.is_degraded is False

    @pytest.mark.asyncio
    async def test_health_canary_failure_timeout_sets_degraded(self):
        """Health canary failure due to timeout trips the circuit breaker."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is False
        # After STORY-257A threshold=8, 1 failure doesn't trip
        assert _circuit_breaker.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_health_canary_failure_http_error_sets_degraded(self):
        """Health canary failure due to HTTP error trips the circuit breaker."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            side_effect=httpx.ConnectError("connection refused")
        )
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is False
        # After STORY-257A threshold=8, 1 failure doesn't trip
        assert _circuit_breaker.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_health_canary_failure_500_sets_degraded(self):
        """Health canary failure due to 500 status trips the circuit breaker."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is False
        # After STORY-257A threshold=8, 1 failure doesn't trip
        assert _circuit_breaker.consecutive_failures > 0

    @pytest.mark.asyncio
    async def test_health_canary_failure_logs_warning(self, caplog):
        """Health canary failure logs a warning message (AC11)."""
        client = AsyncPNCPClient(max_concurrent=10)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        client._client = mock_http_client

        with caplog.at_level("WARNING"):
            await client.health_canary()

        # AC11: Check for the specific warning message
        assert any(
            "PNCP health check failed" in record.message
            for record in caplog.records
        )
        assert any(
            "skipping PNCP for this search" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_health_canary_not_initialized_raises(self):
        """Health canary raises RuntimeError if client not initialized."""
        client = AsyncPNCPClient(max_concurrent=10)
        # _client is None (no async context manager)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.health_canary()


# ---------------------------------------------------------------------------
# AC10 integration: buscar_todas_ufs_paralelo skips on canary failure
# ---------------------------------------------------------------------------

class TestBuscarComHealthCanary:
    """Test that buscar_todas_ufs_paralelo respects health canary result."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_canary_failure_skips_pncp(self):
        """When health canary fails, buscar_todas_ufs_paralelo returns empty."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            with patch.object(client, "health_canary", return_value=False):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

        # After STORY-257A, returns ParallelFetchResult
        assert isinstance(result, ParallelFetchResult)
        assert result.items == []

    @pytest.mark.asyncio
    async def test_canary_success_proceeds_with_search(self):
        """When health canary succeeds, search proceeds normally."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_uf(*args, **kwargs):
                return [_make_item("FOUND-1")]

            with patch.object(client, "health_canary", return_value=True), \
                 patch.object(client, "_fetch_uf_all_pages", side_effect=mock_fetch_uf):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

        # After STORY-257A, returns ParallelFetchResult
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_already_degraded_skips(self):
        """When circuit breaker already degraded, skips without canary check."""
        _circuit_breaker.degraded_until = time.time() + 300
        _circuit_breaker.consecutive_failures = 8  # Updated threshold

        async with AsyncPNCPClient(max_concurrent=10) as client:
            # health_canary should NOT be called
            canary_mock = AsyncMock(return_value=True)
            with patch.object(client, "health_canary", canary_mock):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

            canary_mock.assert_not_called()

        # After STORY-257A, returns ParallelFetchResult when degraded (tries with reduced concurrency)
        assert isinstance(result, ParallelFetchResult)


# ---------------------------------------------------------------------------
# AC7: Per-UF timeout reduced to 30s
# ---------------------------------------------------------------------------

class TestPerUFTimeout:
    """Test that per-UF timeout is 30s (STORY-252 AC7)."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_per_uf_timeout_is_30s(self):
        """Verify the per-UF timeout value in buscar_todas_ufs_paralelo is 30s."""
        # We verify by checking the timeout passed to asyncio.wait_for
        async with AsyncPNCPClient(max_concurrent=10) as client:
            timeout_seen = None

            original_wait_for = asyncio.wait_for

            async def capture_timeout(coro, *, timeout=None):
                nonlocal timeout_seen
                if timeout_seen is None and timeout is not None:
                    # Skip the health canary wait_for (5s) and capture the UF one
                    if timeout != 5.0:
                        timeout_seen = timeout
                return await original_wait_for(coro, timeout=timeout)

            with patch.object(client, "health_canary", return_value=True), \
                 patch.object(
                     client, "_fetch_uf_all_pages",
                     side_effect=lambda **kw: asyncio.coroutine(lambda: [])(),
                 ), \
                 patch("pncp_client.asyncio.wait_for", side_effect=capture_timeout):
                await client.buscar_todas_ufs_paralelo(
                    ufs=["SP"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

            # The per-UF timeout should be 30s (AC7)
            assert timeout_seen == 30


# ---------------------------------------------------------------------------
# Integration-style test: end-to-end modality parallelism
# ---------------------------------------------------------------------------

class TestModalityParallelism:
    """Test that modalities run in parallel within _fetch_uf_all_pages."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_modalities_run_in_parallel(self):
        """All modalities should start approximately simultaneously."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        start_times = {}

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            start_times[modalidade] = asyncio.get_running_loop().time()
            await asyncio.sleep(0.05)  # simulate small work
            return [_make_item(f"MOD-{modalidade}-1")]

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 5.0), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                result = await client._fetch_uf_all_pages(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidades=[4, 5, 6, 7],
                )

        # All 4 modalities should have returned items
        assert len(result) == 4

        # Start times should be within 50ms of each other (parallel, not sequential)
        times = list(start_times.values())
        assert len(times) == 4
        time_spread = max(times) - min(times)
        assert time_spread < 0.1, (
            f"Modalities started {time_spread:.3f}s apart — "
            f"expected parallel execution"
        )


# ---------------------------------------------------------------------------
# PNCPDegradedError
# ---------------------------------------------------------------------------

class TestPNCPDegradedError:
    """Test the PNCPDegradedError exception."""

    def test_is_subclass_of_pncp_api_error(self):
        assert issubclass(PNCPDegradedError, PNCPAPIError)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(PNCPDegradedError):
            raise PNCPDegradedError("PNCP is degraded")

    def test_caught_by_pncp_api_error_handler(self):
        with pytest.raises(PNCPAPIError):
            raise PNCPDegradedError("PNCP is degraded")


# ---------------------------------------------------------------------------
# Environment variable configuration
# ---------------------------------------------------------------------------

class TestEnvironmentConfiguration:
    """Test that module-level constants read from environment variables."""

    def test_default_per_modality_timeout(self):
        """Default per-modality timeout is 15s."""
        assert PNCP_TIMEOUT_PER_MODALITY == 15.0

    def test_default_modality_retry_backoff(self):
        """Default modality retry backoff is 3s."""
        assert PNCP_MODALITY_RETRY_BACKOFF == 3.0

    def test_circuit_breaker_default_threshold(self):
        """Default circuit breaker threshold is 8."""
        cb = PNCPCircuitBreaker()
        assert cb.threshold == 8

    def test_circuit_breaker_default_cooldown(self):
        """Default circuit breaker cooldown is 120s (2 minutes)."""
        cb = PNCPCircuitBreaker()
        assert cb.cooldown_seconds == 120
