"""STORY-282: PNCP Timeout Resilience — Tests for all 5 ACs.

AC1: Aggressive timeout reduction (connect=10s, read=15s, retries=1)
AC2: Page limit per modalidade (MAX_PAGES=5 → 250 items max)
AC3: Cache-first for user searches (serve stale, revalidate in background)
AC4: Warming pause during live search (already tested in test_cache_warming_noninterference)
AC5: PCP UF filter fix (skip records with empty UF when filter active)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# AC1: Aggressive Timeout Reduction
# ============================================================================

class TestAC1AggressiveTimeouts:
    """STORY-282 AC1: Verify reduced timeouts and retries."""

    def test_retry_config_defaults_reflect_story_282(self):
        """RetryConfig defaults: max_retries=1, timeout=15, connect=10."""
        from config import RetryConfig
        config = RetryConfig()
        assert config.max_retries == 1, "STORY-282 AC1: max_retries should be 1 (was 3)"
        assert config.timeout == 15, "STORY-282 AC1: timeout should be 15 (was 30)"
        assert config.connect_timeout == 10.0, "STORY-282 AC1: connect_timeout should be 10"
        assert config.read_timeout == 15.0, "STORY-282 AC1: read_timeout should be 15"

    def test_env_override_pncp_connect_timeout(self, monkeypatch):
        """PNCP_CONNECT_TIMEOUT env var overrides default.

        NOTE (STORY-BTS-011): RetryConfig is defined in config.pncp (not in the
        config package root). Reloading the package root does NOT re-evaluate
        submodule dataclass field defaults — we must reload config.pncp.
        """
        monkeypatch.setenv("PNCP_CONNECT_TIMEOUT", "5")
        monkeypatch.setenv("PNCP_READ_TIMEOUT", "8")
        monkeypatch.setenv("PNCP_MAX_RETRIES", "0")
        import importlib
        import config.pncp
        importlib.reload(config.pncp)
        try:
            c = config.pncp.RetryConfig()
            assert c.connect_timeout == 5.0
            assert c.read_timeout == 8.0
            assert c.max_retries == 0
        finally:
            # Restore defaults
            monkeypatch.delenv("PNCP_CONNECT_TIMEOUT", raising=False)
            monkeypatch.delenv("PNCP_READ_TIMEOUT", raising=False)
            monkeypatch.delenv("PNCP_MAX_RETRIES", raising=False)
            importlib.reload(config.pncp)

    def test_config_module_level_vars(self):
        """config.py exposes PNCP_CONNECT_TIMEOUT, PNCP_READ_TIMEOUT, PNCP_MAX_RETRIES."""
        from config import PNCP_CONNECT_TIMEOUT, PNCP_READ_TIMEOUT, PNCP_MAX_RETRIES
        assert PNCP_CONNECT_TIMEOUT == 10.0
        assert PNCP_READ_TIMEOUT == 15.0
        assert PNCP_MAX_RETRIES == 1

    @pytest.mark.asyncio
    async def test_async_client_uses_split_timeouts(self):
        """AsyncPNCPClient.__aenter__ creates httpx client with split connect/read timeouts."""
        from pncp_client import AsyncPNCPClient
        from config import RetryConfig

        config = RetryConfig()
        client = AsyncPNCPClient(config=config)

        async with client:
            # Verify the httpx client timeout configuration
            assert client._client is not None
            timeout = client._client.timeout
            assert timeout.connect == config.connect_timeout
            assert timeout.read == config.read_timeout


# ============================================================================
# AC2: Page Limit Per Modalidade
# ============================================================================

class TestAC2PageLimit:
    """STORY-282 AC2: Verify page limit per modality caps at PNCP_MAX_PAGES."""

    def test_config_pncp_max_pages_default(self):
        """PNCP_MAX_PAGES defaults to 20 (raised from 5 post-STORY-282 for better coverage)."""
        from config import PNCP_MAX_PAGES
        # Post-STORY-282 default: raised 5→20 because 50-items/page × 20 pages = 1000-item ceiling
        # provides enough coverage for high-volume UFs (SP/MG/RJ) without exceeding budget.
        assert PNCP_MAX_PAGES == 20

    def test_config_pncp_max_pages_env_override(self, monkeypatch):
        """PNCP_MAX_PAGES can be overridden via env.

        Reload target is config.pncp (module that reads the env), not the config package root.
        """
        monkeypatch.setenv("PNCP_MAX_PAGES", "10")
        import importlib
        import config.pncp
        importlib.reload(config.pncp)
        try:
            assert config.pncp.PNCP_MAX_PAGES == 10
        finally:
            monkeypatch.delenv("PNCP_MAX_PAGES", raising=False)
            importlib.reload(config.pncp)

    @pytest.mark.asyncio
    async def test_fetch_single_modality_respects_max_pages(self):
        """_fetch_single_modality stops after PNCP_MAX_PAGES pages."""
        from pncp_client import AsyncPNCPClient
        from config import RetryConfig

        config = RetryConfig()
        client = AsyncPNCPClient(config=config)

        pages_fetched = []

        async def mock_fetch_page(*args, **kwargs):
            pagina = kwargs.get("pagina", 1)
            pages_fetched.append(pagina)
            return {
                "data": [{"numeroControlePNCP": f"item-{pagina}-1"}],
                "totalRegistros": 500,
                "totalPaginas": 10,
                "paginasRestantes": 10 - pagina,
            }

        # Initialize client internals
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()  # Won't be used directly
        client._fetch_page_async = AsyncMock(side_effect=mock_fetch_page)

        # Mock circuit breaker
        with patch("pncp_client._circuit_breaker") as mock_cb:
            mock_cb.record_success = AsyncMock()
            mock_cb.record_failure = AsyncMock()

            items, was_truncated = await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                modalidade=6,
                max_pages=5,  # Explicit limit
            )

        assert len(pages_fetched) == 5, f"Should fetch exactly 5 pages, got {len(pages_fetched)}"
        assert was_truncated is True, "Should flag truncation when more pages remain"
        assert len(items) == 5, "Should have 5 items (1 per page)"

    @pytest.mark.asyncio
    async def test_fetch_single_modality_default_uses_config(self):
        """_fetch_single_modality uses PNCP_MAX_PAGES when max_pages=None."""
        from pncp_client import AsyncPNCPClient
        from config import RetryConfig

        config = RetryConfig()
        client = AsyncPNCPClient(config=config)

        pages_fetched = []

        async def mock_fetch_page(*args, **kwargs):
            pagina = kwargs.get("pagina", 1)
            pages_fetched.append(pagina)
            return {
                "data": [{"numeroControlePNCP": f"item-{pagina}-1"}],
                "totalRegistros": 100,
                "totalPaginas": 3,
                "paginasRestantes": max(0, 3 - pagina),
            }

        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()
        client._fetch_page_async = AsyncMock(side_effect=mock_fetch_page)

        with patch("pncp_client._circuit_breaker") as mock_cb:
            mock_cb.record_success = AsyncMock()
            mock_cb.record_failure = AsyncMock()

            # max_pages=None → should use PNCP_MAX_PAGES (default 5)
            items, was_truncated = await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                modalidade=6,
                max_pages=None,
            )

        # 3 pages total < 5 pages limit → no truncation
        assert len(pages_fetched) == 3
        assert was_truncated is False


# ============================================================================
# AC3: Cache-First for User Searches
# ============================================================================

class TestAC3CacheFirst:
    """STORY-282 AC3: Verify cache-first logic serves stale cache immediately."""

    def test_config_cache_first_fresh_timeout(self):
        """CACHE_FIRST_FRESH_TIMEOUT defaults to 60."""
        from config import CACHE_FIRST_FRESH_TIMEOUT
        assert CACHE_FIRST_FRESH_TIMEOUT == 60


# ============================================================================
# AC5: PCP UF Filter Fix
# ============================================================================

class TestAC5PCPUFFilter:
    """STORY-282 AC5: PCP should skip records with empty UF when UF filter is active."""

    @pytest.mark.asyncio
    async def test_pcp_skips_empty_uf_records(self):
        """Records with empty/missing UF are skipped when ufs filter is provided."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()

        # Mock response with records: one with UF, one without
        mock_response = {
            "result": [
                {
                    "codigoLicitacao": "101",
                    "resumo": "Uniforme escolar",
                    "unidadeCompradora": {"uf": "SP", "nomeUnidadeCompradora": "Prefeitura SP", "cidade": "São Paulo"},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
                {
                    "codigoLicitacao": "102",
                    "resumo": "Fardamento militar",
                    "unidadeCompradora": {"uf": "", "nomeUnidadeCompradora": "Orgao sem UF", "cidade": ""},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
                {
                    "codigoLicitacao": "103",
                    "resumo": "Material escritorio",
                    "unidadeCompradora": {"uf": "RJ", "nomeUnidadeCompradora": "Prefeitura RJ", "cidade": "Rio"},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
            ],
            "total": 3,
            "pageCount": 1,
            "nextPage": None,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        results = []
        async for record in adapter.fetch("2026-01-01", "2026-01-10", ufs={"SP"}):
            results.append(record)

        # Only SP record should pass — empty UF and RJ should be filtered out
        assert len(results) == 1
        assert results[0].uf == "SP"

    @pytest.mark.asyncio
    async def test_pcp_case_insensitive_uf_match(self):
        """UF matching should be case-insensitive."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()

        mock_response = {
            "result": [
                {
                    "codigoLicitacao": "201",
                    "resumo": "Teste",
                    "unidadeCompradora": {"uf": "sp", "nomeUnidadeCompradora": "Test", "cidade": "SP"},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
            ],
            "total": 1,
            "pageCount": 1,
            "nextPage": None,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        results = []
        async for record in adapter.fetch("2026-01-01", "2026-01-10", ufs={"SP"}):
            results.append(record)

        # Lowercase "sp" should match "SP" filter
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_pcp_no_uf_filter_passes_all(self):
        """When no ufs filter, all records pass (including empty UF)."""
        from clients.portal_compras_client import PortalComprasAdapter

        adapter = PortalComprasAdapter()

        mock_response = {
            "result": [
                {
                    "codigoLicitacao": "301",
                    "resumo": "Teste 1",
                    "unidadeCompradora": {"uf": "", "nomeUnidadeCompradora": "Test", "cidade": ""},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
                {
                    "codigoLicitacao": "302",
                    "resumo": "Teste 2",
                    "unidadeCompradora": {"uf": "MG", "nomeUnidadeCompradora": "Test", "cidade": "BH"},
                    "tipoLicitacao": {"modalidadeLicitacao": "Pregão"},
                    "statusProcessoPublico": {"descricao": "Aberto"},
                },
            ],
            "total": 2,
            "pageCount": 1,
            "nextPage": None,
        }

        adapter._request_with_retry = AsyncMock(return_value=mock_response)

        results = []
        async for record in adapter.fetch("2026-01-01", "2026-01-10", ufs=None):
            results.append(record)

        # All records should pass when no UF filter
        assert len(results) == 2


# ============================================================================
# Integration: Verify PNCP_MAX_PAGES propagates to buscar_todas_ufs_paralelo
# ============================================================================

class TestAC2Integration:
    """Verify PNCP_MAX_PAGES propagates through the call chain."""

    @pytest.mark.asyncio
    async def test_buscar_todas_ufs_uses_max_pages(self):
        """buscar_todas_ufs_paralelo passes PNCP_MAX_PAGES to _fetch_uf_all_pages."""
        from pncp_client import AsyncPNCPClient
        from config import RetryConfig

        config = RetryConfig()
        client = AsyncPNCPClient(config=config)

        # Track what max_pages was passed
        received_max_pages = []


        async def mock_fetch_uf(uf, data_inicial, data_final, modalidades, status=None, max_pages=None):
            received_max_pages.append(max_pages)
            return ([], False)

        client._fetch_uf_all_pages = mock_fetch_uf

        # Need to mock internals
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        with patch("pncp_client._circuit_breaker") as mock_cb:
            mock_cb.is_degraded = False
            mock_cb.try_recover = AsyncMock(return_value=True)
            mock_cb.record_success = AsyncMock()

            # Mock health canary to return True
            client.health_canary = AsyncMock(return_value={"ok": True, "latency_ms": 50.0, "cron_status": "healthy"})

            await client.buscar_todas_ufs_paralelo(
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-10",
            )

        # The max_pages passed to _fetch_uf_all_pages should be PNCP_MAX_PAGES (5)
        from config import PNCP_MAX_PAGES
        assert len(received_max_pages) == 1
        assert received_max_pages[0] == PNCP_MAX_PAGES
