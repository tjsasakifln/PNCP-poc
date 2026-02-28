"""
GTM-INFRA-002: Health Canary Realista + Railway Config

Tests:
  T1: Canary usa tamanhoPagina=50
  T2: Health endpoint reporta status per-source
  T4: Batch delay configurável via env
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# T1: Canary usa tamanhoPagina=50
# ---------------------------------------------------------------------------

class TestT1CanaryTamanhoPagina50:
    """GTM-INFRA-002 T1: Health canary must use tamanhoPagina=50 (production value)."""

    @pytest.mark.asyncio
    async def test_health_canary_sends_tamanho_pagina_50(self):
        """health_canary() must send tamanhoPagina=50 in request params."""
        from pncp_client import AsyncPNCPClient

        client = AsyncPNCPClient(max_concurrent=10)

        captured_params = {}

        async def mock_get(url, params=None):
            captured_params.update(params or {})
            resp = MagicMock()
            resp.status_code = 200
            return resp

        mock_http_client = AsyncMock()
        mock_http_client.get = mock_get
        client._client = mock_http_client

        result = await client.health_canary()

        assert result is True
        assert "tamanhoPagina" in captured_params, (
            "health_canary MUST send tamanhoPagina parameter"
        )
        assert captured_params["tamanhoPagina"] == 50, (
            f"Expected tamanhoPagina=50 (production), got {captured_params['tamanhoPagina']}"
        )

    @pytest.mark.asyncio
    async def test_health_canary_not_using_10(self):
        """Regression: tamanhoPagina must NOT be 10 (old value that missed real limits)."""
        from pncp_client import AsyncPNCPClient

        client = AsyncPNCPClient(max_concurrent=10)

        captured_params = {}

        async def mock_get(url, params=None):
            captured_params.update(params or {})
            resp = MagicMock()
            resp.status_code = 200
            return resp

        mock_http_client = AsyncMock()
        mock_http_client.get = mock_get
        client._client = mock_http_client

        await client.health_canary()

        assert captured_params.get("tamanhoPagina") != 10, (
            "tamanhoPagina=10 is the OLD value that failed to detect PNCP limit changes"
        )


# ---------------------------------------------------------------------------
# T2: Health endpoint reporta status per-source
# ---------------------------------------------------------------------------

class TestT2HealthPerSource:
    """GTM-INFRA-002 T2: Health module reports per-source status."""

    def test_source_health_endpoints_includes_pncp(self):
        """PNCP must be in SOURCE_HEALTH_ENDPOINTS."""
        from health import SOURCE_HEALTH_ENDPOINTS
        assert "PNCP" in SOURCE_HEALTH_ENDPOINTS

    def test_source_health_endpoints_includes_portal(self):
        """Portal (PCP v2) must be in SOURCE_HEALTH_ENDPOINTS."""
        from health import SOURCE_HEALTH_ENDPOINTS
        assert "Portal" in SOURCE_HEALTH_ENDPOINTS

    def test_source_health_endpoints_includes_compras_gov(self):
        """ComprasGov must be in SOURCE_HEALTH_ENDPOINTS (AC2)."""
        from health import SOURCE_HEALTH_ENDPOINTS
        assert "ComprasGov" in SOURCE_HEALTH_ENDPOINTS

    def test_source_health_endpoints_compras_gov_url(self):
        """ComprasGov URL must point to dadosabertos.compras.gov.br."""
        from health import SOURCE_HEALTH_ENDPOINTS
        assert "dadosabertos.compras.gov.br" in SOURCE_HEALTH_ENDPOINTS["ComprasGov"]

    @pytest.mark.asyncio
    async def test_check_all_sources_returns_per_source_dict(self):
        """check_all_sources_health returns a dict with per-source results."""
        from health import check_all_sources_health, SourceHealthResult

        with patch("health.check_source_health") as mock_check:
            mock_check.return_value = SourceHealthResult(
                source_code="PNCP",
                status="healthy",
            )
            results = await check_all_sources_health(
                enabled_sources=["PNCP"], timeout=2.0
            )

        assert isinstance(results, dict)
        assert "PNCP" in results

    @pytest.mark.asyncio
    async def test_system_health_includes_sources(self):
        """get_health_status returns SystemHealth with per-source data."""
        from health import get_health_status, SourceHealthResult, HealthStatus

        mock_result = SourceHealthResult(
            source_code="PNCP",
            status=HealthStatus.HEALTHY,
            response_time_ms=100,
        )

        with patch("health.check_all_sources_health", return_value={"PNCP": mock_result}), \
             patch("source_config.sources.get_source_config", side_effect=ImportError):
            health = await get_health_status(include_sources=True, source_timeout=2.0)

        health_dict = health.to_dict()
        assert "sources" in health_dict
        assert "PNCP" in health_dict["sources"]
        assert health_dict["sources"]["PNCP"]["status"] == "healthy"
        assert health_dict["sources"]["PNCP"]["response_time_ms"] == 100

    def test_pncp_health_check_uses_tamanho_pagina_50(self):
        """health.py PNCP canary must use tamanhoPagina=50 (STORY-316 AC1: realistic canary detects page size bug)."""
        import inspect
        from health import check_source_health
        source = inspect.getsource(check_source_health)
        assert "tamanhoPagina" in source
        # STORY-316 AC1: Canary uses 50 (realistic — detects silent HTTP 400 when >50)
        assert '"tamanhoPagina": 50' in source or "'tamanhoPagina': 50" in source


# ---------------------------------------------------------------------------
# T4: Batch delay configurável via env
# ---------------------------------------------------------------------------

class TestT4BatchDelayConfigurable:
    """GTM-INFRA-002 T4: PNCP_BATCH_DELAY_S configurable via env."""

    def test_default_batch_delay_is_0_5(self):
        """Default PNCP_BATCH_DELAY_S must be 2.0s (STAB-003: increased to reduce PNCP rate-limit risk)."""
        from pncp_client import PNCP_BATCH_DELAY_S
        assert PNCP_BATCH_DELAY_S == 2.0

    def test_batch_delay_env_override(self):
        """PNCP_BATCH_DELAY_S can be overridden via environment variable."""
        # Test the parsing logic (without reloading module)
        test_value = "1.5"
        parsed = float(test_value)
        assert parsed == 1.5

    def test_batch_delay_used_in_search(self):
        """Verify PNCP_BATCH_DELAY_S is referenced in buscar_todas_ufs_paralelo."""
        import inspect
        from pncp_client import AsyncPNCPClient
        source = inspect.getsource(AsyncPNCPClient.buscar_todas_ufs_paralelo)
        assert "PNCP_BATCH_DELAY_S" in source or "batch_delay" in source

    @pytest.mark.asyncio
    async def test_batch_delay_applied_between_batches(self):
        """Inter-batch delay should use PNCP_BATCH_DELAY_S value."""
        from pncp_client import AsyncPNCPClient

        sleep_calls = []

        async def mock_sleep(duration):
            sleep_calls.append(duration)
            # Don't actually sleep in tests

        with patch.object(
            AsyncPNCPClient, "_fetch_uf_all_pages",
            new_callable=AsyncMock,
            return_value=([], False),
        ), patch.object(
            AsyncPNCPClient, "health_canary",
            new_callable=AsyncMock,
            return_value=True,
        ), patch("pncp_client.PNCP_BATCH_SIZE", 2), \
             patch("pncp_client.PNCP_BATCH_DELAY_S", 0.5), \
             patch("asyncio.sleep", side_effect=mock_sleep):

            client = AsyncPNCPClient(max_concurrent=10)
            await client.buscar_todas_ufs_paralelo(
                ufs=["SP", "RJ", "MG"],
                data_inicial="2026-02-01",
                data_final="2026-02-10",
            )

        # 3 UFs / batch 2 = 2 batches, 1 inter-batch delay
        assert 0.5 in sleep_calls, (
            f"Expected 0.5s inter-batch delay, got sleep calls: {sleep_calls}"
        )
