"""STORY-252: PNCP Resilience & Multi-Source Tests.

Covers the 8 mandatory unit tests defined in the acceptance criteria:

Track 2 — PNCP Client Hardening:
  1. Per-modality timeout does not cancel other modalities (AC6)
  2. Circuit breaker activates after N timeouts (AC8)
  3. Health canary failure → PNCP skipped (AC10/AC11)
  4. Retry happens 1x before skip on modality timeout (AC9)

Track 3 — Multi-Source Orchestration:
  5. Health registry persists status between calls (AC12)
  6. Failover increases timeout of alternatives (AC13)
  7. ComprasGov last-resort fallback works (AC15)
  8. ConsolidationResult includes source_results detail (AC16)

Track 4 — Schema:
  9. BuscaResponse includes is_partial, data_sources, degradation_reason (AC18-20)
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest


# ============================================================================
# Track 2: PNCP Client Hardening Tests
# ============================================================================


class TestPerModalityTimeout:
    """AC6: Per-modality timeout does not cancel other modalities."""

    @pytest.mark.asyncio
    async def test_timeout_one_modality_does_not_block_others(self):
        """If modality 4 times out, modalities 5, 6, 7 still execute."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        async with AsyncPNCPClient(max_concurrent=10) as client:
            call_count = {"total": 0}

            # Patch _fetch_single_modality to simulate timeout on mod 4 only
            original = client._fetch_single_modality

            async def mock_fetch_single(uf, data_inicial, data_final, modalidade, **kw):
                call_count["total"] += 1
                if modalidade == 4:
                    # Simulate a very slow fetch that will exceed timeout
                    await asyncio.sleep(100)
                    return []
                # Other modalities return instantly
                return [{"codigoCompra": f"{uf}-{modalidade}-001", "uf": uf}]

            with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
                # Use a short per-modality timeout for testing
                with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.1):
                    with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                        results = await client._fetch_uf_all_pages(
                            uf="SP",
                            data_inicial="2026-01-01",
                            data_final="2026-01-15",
                            modalidades=[4, 5, 6, 7],
                        )

            # Modalities 5, 6, 7 should have returned results despite mod 4 timeout
            assert len(results) == 3
            mods_in_results = {r["codigoCompra"].split("-")[1] for r in results}
            assert "5" in mods_in_results
            assert "6" in mods_in_results
            assert "7" in mods_in_results

        _circuit_breaker.reset()


class TestCircuitBreaker:
    """AC8: Circuit breaker activates after N consecutive timeouts."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_after_threshold(self):
        """After 5 consecutive failures, circuit breaker marks PNCP as degraded."""
        from pncp_client import PNCPCircuitBreaker

        cb = PNCPCircuitBreaker(threshold=5, cooldown_seconds=10)

        assert not cb.is_degraded

        for i in range(4):
            await cb.record_failure()
            assert not cb.is_degraded, f"Should not trip after {i + 1} failures"

        await cb.record_failure()  # 5th failure
        assert cb.is_degraded, "Should be degraded after 5 failures"
        assert cb.degraded_until is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self):
        """A successful request resets the failure counter."""
        from pncp_client import PNCPCircuitBreaker

        cb = PNCPCircuitBreaker(threshold=5, cooldown_seconds=10)

        # Accumulate 4 failures
        for _ in range(4):
            await cb.record_failure()

        # One success resets counter
        await cb.record_success()
        assert cb.consecutive_failures == 0

        # Need 5 more failures to trip (not just 1)
        await cb.record_failure()
        assert not cb.is_degraded

    @pytest.mark.asyncio
    async def test_circuit_breaker_auto_resets_after_cooldown(self):
        """Circuit breaker auto-resets after cooldown period expires."""
        from pncp_client import PNCPCircuitBreaker

        cb = PNCPCircuitBreaker(threshold=2, cooldown_seconds=1)

        await cb.record_failure()
        await cb.record_failure()
        assert cb.is_degraded

        # Wait for cooldown
        await asyncio.sleep(1.1)
        assert not cb.is_degraded, "Should reset after cooldown"
        assert cb.consecutive_failures == 0


class TestHealthCanary:
    """AC10/AC11: Health canary failure → PNCP skipped."""

    @pytest.mark.asyncio
    async def test_health_canary_failure_skips_pncp(self):
        """When health canary fails, buscar_todas_ufs_paralelo returns empty."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        async with AsyncPNCPClient(max_concurrent=10) as client:
            # Make the canary fail
            with patch.object(client, "health_canary", return_value=False):
                # Manually set circuit breaker to degraded (canary does this)
                _circuit_breaker.degraded_until = time.time() + 300
                _circuit_breaker.consecutive_failures = 5

                results = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-15",
                )

            assert results == []

        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_health_canary_success_proceeds(self):
        """When health canary succeeds, search proceeds normally."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "data": [
                {"numeroControlePNCP": "001", "unidadeOrgao": {"ufSigla": "SP", "municipioNome": ""}, "orgaoEntidade": {"razaoSocial": ""}},
            ],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "paginasRestantes": 0,
        }

        with patch("pncp_client.httpx.AsyncClient.get", return_value=mock_response):
            async with AsyncPNCPClient(max_concurrent=10) as client:
                results = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-15",
                )

        assert len(results) >= 1
        _circuit_breaker.reset()


class TestModalityRetry:
    """AC9: Retry happens 1x before skip on modality timeout."""

    @pytest.mark.asyncio
    async def test_modality_retries_once_on_timeout(self):
        """A timed-out modality retries once with backoff before giving up."""
        from pncp_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()
        call_count = 0

        async def slow_fetch(uf, data_inicial, data_final, modalidade, **kw):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(100)  # Will be interrupted by timeout
            return []

        async with AsyncPNCPClient(max_concurrent=10) as client:
            with patch.object(client, "_fetch_single_modality", side_effect=slow_fetch):
                with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 0.05):
                    with patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                        result = await client._fetch_modality_with_timeout(
                            uf="SP",
                            data_inicial="2026-01-01",
                            data_final="2026-01-15",
                            modalidade=6,
                        )

        # Should have been called exactly 2 times (initial + 1 retry)
        assert call_count == 2
        assert result == []

        _circuit_breaker.reset()


# ============================================================================
# Track 3: Multi-Source Orchestration Tests
# ============================================================================


class TestSourceHealthRegistry:
    """AC12: Health registry persists status between calls."""

    def test_registry_tracks_failures_and_degrades(self):
        """After 3 failures, status transitions to degraded."""
        from source_config.sources import SourceHealthRegistry

        registry = SourceHealthRegistry()

        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "healthy"  # 1 failure

        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "healthy"  # 2 failures

        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "degraded"  # 3 failures

    def test_registry_marks_down_after_5_failures(self):
        """After 5 failures, status transitions to down."""
        from source_config.sources import SourceHealthRegistry

        registry = SourceHealthRegistry()
        for _ in range(5):
            registry.record_failure("PNCP")

        assert registry.get_status("PNCP") == "down"

    def test_registry_resets_on_success(self):
        """A success resets status to healthy."""
        from source_config.sources import SourceHealthRegistry

        registry = SourceHealthRegistry()
        for _ in range(4):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "degraded"

        registry.record_success("PNCP")
        assert registry.get_status("PNCP") == "healthy"

    def test_registry_persists_between_calls(self):
        """Status persists within same registry instance."""
        from source_config.sources import SourceHealthRegistry

        registry = SourceHealthRegistry()

        registry.record_failure("Portal")
        registry.record_failure("Portal")
        registry.record_failure("Portal")
        # Status should persist
        assert registry.get_status("Portal") == "degraded"

        # Check different source is independent
        assert registry.get_status("PNCP") == "healthy"

    def test_registry_is_available(self):
        """is_available returns False only when down."""
        from source_config.sources import SourceHealthRegistry

        registry = SourceHealthRegistry()

        assert registry.is_available("PNCP") is True  # healthy

        for _ in range(3):
            registry.record_failure("PNCP")
        assert registry.is_available("PNCP") is True  # degraded but available

        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        assert registry.is_available("PNCP") is False  # down


class TestFailoverTimeoutIncrease:
    """AC13: Failover increases timeout when PNCP is degraded."""

    @pytest.mark.asyncio
    async def test_degraded_pncp_increases_alternative_timeouts(self):
        """When PNCP is degraded, alternative sources get 40s timeout (up from 25s)."""
        from consolidation import ConsolidationService
        from source_config.sources import source_health_registry

        # Mark PNCP as degraded
        source_health_registry.reset()
        for _ in range(4):
            source_health_registry.record_failure("PNCP")
        assert source_health_registry.get_status("PNCP") == "degraded"

        # Create mock adapters
        mock_pncp = _make_mock_adapter("PNCP", priority=1)
        mock_compras = _make_mock_adapter("COMPRAS_GOV", priority=4)

        svc = ConsolidationService(
            adapters={"PNCP": mock_pncp, "COMPRAS_GOV": mock_compras},
            timeout_per_source=25,
            timeout_global=60,
            fail_on_all_errors=False,
        )

        # Capture the effective timeout used
        original_wrap = svc._wrap_source
        captured_timeouts = {}

        async def patched_wrap(code, coro, timeout=None):
            captured_timeouts[code] = timeout
            return await original_wrap(code, coro, timeout)

        with patch.object(svc, "_wrap_source", side_effect=patched_wrap):
            await svc.fetch_all("2026-01-01", "2026-01-15")

        # COMPRAS_GOV should have gotten the failover timeout (40s)
        assert captured_timeouts.get("COMPRAS_GOV") == ConsolidationService.FAILOVER_TIMEOUT_PER_SOURCE

        source_health_registry.reset()


class TestComprasGovLastResort:
    """AC15: ComprasGov last-resort fallback when all primary sources fail."""

    @pytest.mark.asyncio
    async def test_fallback_fires_when_all_sources_fail(self):
        """When all primary sources fail, ComprasGov fallback is attempted."""
        from consolidation import ConsolidationService
        from source_config.sources import source_health_registry

        source_health_registry.reset()

        # Create failing primary adapter
        mock_pncp = _make_mock_adapter("PNCP", priority=1, should_fail=True)

        # Create working fallback
        mock_fallback = _make_mock_adapter("COMPRAS_GOV", priority=4, records=3)

        svc = ConsolidationService(
            adapters={"PNCP": mock_pncp},
            timeout_per_source=25,
            timeout_global=60,
            fail_on_all_errors=False,
            fallback_adapter=mock_fallback,
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-15")

        # Should have records from fallback
        assert result.total_after_dedup == 3
        # Check fallback source appears in source_results
        source_codes = [sr.source_code for sr in result.source_results]
        assert "COMPRAS_GOV" in source_codes

        source_health_registry.reset()

    @pytest.mark.asyncio
    async def test_fallback_not_attempted_if_data_exists(self):
        """Fallback is NOT attempted when primary sources return data."""
        from consolidation import ConsolidationService
        from source_config.sources import source_health_registry

        source_health_registry.reset()

        mock_pncp = _make_mock_adapter("PNCP", priority=1, records=5)
        mock_fallback = _make_mock_adapter("COMPRAS_GOV", priority=4, records=3)

        svc = ConsolidationService(
            adapters={"PNCP": mock_pncp},
            timeout_per_source=25,
            timeout_global=60,
            fail_on_all_errors=False,
            fallback_adapter=mock_fallback,
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-15")

        # Should have PNCP records, NOT fallback
        assert result.total_after_dedup == 5
        source_codes = [sr.source_code for sr in result.source_results]
        assert "PNCP" in source_codes
        assert "COMPRAS_GOV" not in source_codes

        source_health_registry.reset()


class TestConsolidationSourceResults:
    """AC16: ConsolidationResult includes source_results detail."""

    @pytest.mark.asyncio
    async def test_source_results_include_all_sources(self):
        """Result includes status for every source attempted."""
        from consolidation import ConsolidationService
        from source_config.sources import source_health_registry

        source_health_registry.reset()

        mock_pncp = _make_mock_adapter("PNCP", priority=1, records=5)
        mock_compras = _make_mock_adapter("COMPRAS_GOV", priority=4, should_fail=True)

        svc = ConsolidationService(
            adapters={"PNCP": mock_pncp, "COMPRAS_GOV": mock_compras},
            timeout_per_source=25,
            timeout_global=60,
            fail_on_all_errors=False,
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-15")

        # Both sources should be in source_results
        assert len(result.source_results) == 2

        pncp_sr = next(sr for sr in result.source_results if sr.source_code == "PNCP")
        compras_sr = next(sr for sr in result.source_results if sr.source_code == "COMPRAS_GOV")

        assert pncp_sr.status == "success"
        assert pncp_sr.record_count == 5
        assert pncp_sr.error is None

        assert compras_sr.status == "error"
        assert compras_sr.record_count == 0
        assert compras_sr.error is not None

        source_health_registry.reset()

    @pytest.mark.asyncio
    async def test_partial_results_marked_correctly(self):
        """is_partial=True and degradation_reason set when some sources fail."""
        from consolidation import ConsolidationService
        from source_config.sources import source_health_registry

        source_health_registry.reset()

        mock_pncp = _make_mock_adapter("PNCP", priority=1, records=3)
        mock_compras = _make_mock_adapter("COMPRAS_GOV", priority=4, should_fail=True)

        svc = ConsolidationService(
            adapters={"PNCP": mock_pncp, "COMPRAS_GOV": mock_compras},
            timeout_per_source=25,
            timeout_global=60,
            fail_on_all_errors=False,
        )

        result = await svc.fetch_all("2026-01-01", "2026-01-15")

        assert result.is_partial is True
        assert result.degradation_reason is not None
        assert "COMPRAS_GOV" in result.degradation_reason

        source_health_registry.reset()


# ============================================================================
# Track 4: Schema Tests
# ============================================================================


class TestBuscaResponseSchema:
    """AC18-AC20: BuscaResponse includes degradation fields."""

    def test_busca_response_has_is_partial(self):
        """AC18: BuscaResponse has is_partial field defaulting to False."""
        from schemas import BuscaResponse, ResumoEstrategico

        resp = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="Test",
                total_oportunidades=0,
                valor_total=0.0,
                destaques=[],
                recomendacoes=[],
                alertas_urgencia=[],
            ),
            excel_available=False,
            quota_used=0,
            quota_remaining=10,
            total_raw=0,
            total_filtrado=0,
        )
        assert resp.is_partial is False

    def test_busca_response_accepts_data_sources(self):
        """AC19: BuscaResponse accepts data_sources list."""
        from schemas import BuscaResponse, DataSourceStatus, ResumoEstrategico

        sources = [
            DataSourceStatus(source="PNCP", status="ok", records=10),
            DataSourceStatus(source="COMPRAS_GOV", status="timeout", records=0),
        ]
        resp = BuscaResponse(
            resumo=ResumoEstrategico(
                resumo_executivo="Test",
                total_oportunidades=10,
                valor_total=100000.0,
                destaques=[],
                recomendacoes=[],
                alertas_urgencia=[],
            ),
            excel_available=False,
            quota_used=1,
            quota_remaining=9,
            total_raw=100,
            total_filtrado=10,
            is_partial=True,
            data_sources=sources,
            degradation_reason="PNCP timeout",
        )
        assert resp.is_partial is True
        assert len(resp.data_sources) == 2
        assert resp.data_sources[0].source == "PNCP"
        assert resp.data_sources[1].status == "timeout"
        assert resp.degradation_reason == "PNCP timeout"

    def test_data_source_status_model(self):
        """AC16: DataSourceStatus model validates correctly."""
        from schemas import DataSourceStatus

        ds = DataSourceStatus(source="PNCP", status="ok", records=42)
        assert ds.source == "PNCP"
        assert ds.status == "ok"
        assert ds.records == 42

        ds_timeout = DataSourceStatus(source="ComprasGov", status="timeout")
        assert ds_timeout.records == 0


# ============================================================================
# Helpers
# ============================================================================


def _make_mock_adapter(code: str, priority: int = 1, records: int = 0, should_fail: bool = False):
    """Create a mock SourceAdapter for testing ConsolidationService."""
    from clients.base import SourceMetadata, SourceCapability, SourceStatus, UnifiedProcurement

    mock = AsyncMock()
    mock.code = code
    mock.metadata = SourceMetadata(
        name=f"Mock {code}",
        code=code,
        base_url="https://mock.test",
        capabilities={SourceCapability.PAGINATION},
        rate_limit_rps=10.0,
        priority=priority,
    )

    if should_fail:
        async def failing_fetch(*args, **kwargs):
            raise RuntimeError(f"Mock {code} failure")
            yield  # unreachable — makes this an async generator for async for
        mock.fetch = failing_fetch
    else:
        async def ok_fetch(*args, **kwargs):
            for i in range(records):
                yield UnifiedProcurement(
                    source_id=f"{code}-{i:03d}",
                    source_name=code,
                    objeto=f"Test procurement item {i}",
                    valor_estimado=10000.0 * (i + 1),
                    orgao=f"Test Org {code}",
                    uf="SP",
                )
        mock.fetch = ok_fetch

    mock.health_check = AsyncMock(return_value=SourceStatus.AVAILABLE)
    mock.close = AsyncMock()
    return mock
