"""GTM-FIX-004: Tests for PNCP truncation detection and propagation.

Verifies that when max_pages is hit during a search, the is_truncated flag
and truncated_ufs list are correctly propagated from _fetch_single_modality
through to the BuscaResponse.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from pncp_client import AsyncPNCPClient, ParallelFetchResult, _circuit_breaker


def _make_pncp_response(data, paginas_restantes=0, total_registros=None):
    """Helper to create a mock PNCP API response."""
    if total_registros is None:
        total_registros = len(data)
    return {
        "data": data,
        "totalRegistros": total_registros,
        "totalPaginas": 1,
        "paginasRestantes": paginas_restantes,
    }


def _make_item(item_id):
    """Helper to create a minimal PNCP item dict."""
    return {
        "numeroControlePNCP": item_id,
        "codigoCompra": item_id,
        "objetoCompra": f"Test object {item_id}",
        "valorTotalEstimado": 100000,
        "unidadeOrgao": {"ufSigla": "SP", "municipioNome": "Sao Paulo"},
        "orgaoEntidade": {"razaoSocial": "Test Org"},
    }


class TestFetchSingleModalityTruncation:
    """AC2: _fetch_single_modality returns was_truncated=True when max_pages hit."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_not_truncated_when_all_pages_fetched(self):
        """Normal completion: was_truncated is False."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        async def mock_fetch_page(*args, **kwargs):
            return _make_pncp_response(
                data=[_make_item("ITEM-1")],
                paginas_restantes=0,
            )

        with patch.object(client, "_fetch_page_async", side_effect=mock_fetch_page):
            items, was_truncated = await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                modalidade=6,
                max_pages=500,
            )

        assert len(items) == 1
        assert was_truncated is False

    @pytest.mark.asyncio
    async def test_truncated_when_max_pages_reached(self):
        """When max_pages is reached with remaining pages, was_truncated is True."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        page_count = 0

        async def mock_fetch_page(*args, **kwargs):
            nonlocal page_count
            page_count += 1
            return _make_pncp_response(
                data=[_make_item(f"ITEM-{page_count}")],
                paginas_restantes=100,  # Always more pages
                total_registros=1000,
            )

        with patch.object(client, "_fetch_page_async", side_effect=mock_fetch_page):
            items, was_truncated = await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-31",
                modalidade=6,
                max_pages=3,  # Low limit for test
            )

        assert len(items) == 3
        assert was_truncated is True
        assert page_count == 3


class TestFetchUfAllPagesTruncation:
    """_fetch_uf_all_pages aggregates truncation from modalities."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_uf_truncated_when_any_modality_truncated(self):
        """If any modality is truncated, the UF is marked as truncated."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            if modalidade == 6:
                return [_make_item(f"MOD6-1")], True  # Truncated
            return [_make_item(f"MOD{modalidade}-1")], False

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 5.0), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                items, was_truncated = await client._fetch_uf_all_pages(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidades=[5, 6, 7],
                )

        assert len(items) == 3
        assert was_truncated is True

    @pytest.mark.asyncio
    async def test_uf_not_truncated_when_no_modality_truncated(self):
        """If no modality is truncated, the UF is not marked as truncated."""
        client = AsyncPNCPClient(max_concurrent=10)
        client._semaphore = asyncio.Semaphore(10)
        client._client = MagicMock()

        async def mock_fetch_single(uf, data_inicial, data_final, modalidade,
                                     status=None, max_pages=500):
            return [_make_item(f"MOD{modalidade}-1")], False

        with patch.object(client, "_fetch_single_modality", side_effect=mock_fetch_single):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 5.0), \
                 patch("pncp_client.PNCP_MODALITY_RETRY_BACKOFF", 0.01):
                items, was_truncated = await client._fetch_uf_all_pages(
                    uf="SP",
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                    modalidades=[5, 6, 7],
                )

        assert len(items) == 3
        assert was_truncated is False


class TestBuscarTodasUfsTruncation:
    """buscar_todas_ufs_paralelo collects truncated_ufs in ParallelFetchResult."""

    def setup_method(self):
        _circuit_breaker.reset()

    @pytest.mark.asyncio
    async def test_truncated_ufs_populated(self):
        """ParallelFetchResult.truncated_ufs lists UFs that were truncated."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_uf(uf, data_inicial, data_final, modalidades,
                                     status=None, max_pages=500):
                if uf == "SP":
                    return [_make_item("SP-1")], True  # Truncated
                return [_make_item(f"{uf}-1")], False

            with patch.object(client, "health_canary", return_value=True), \
                 patch.object(client, "_fetch_uf_all_pages", side_effect=mock_fetch_uf):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

        assert isinstance(result, ParallelFetchResult)
        assert len(result.items) == 2
        assert result.truncated_ufs == ["SP"]
        assert "SP" in result.succeeded_ufs
        assert "RJ" in result.succeeded_ufs

    @pytest.mark.asyncio
    async def test_no_truncated_ufs_when_none_truncated(self):
        """ParallelFetchResult.truncated_ufs is empty when nothing truncated."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_uf(uf, data_inicial, data_final, modalidades,
                                     status=None, max_pages=500):
                return [_make_item(f"{uf}-1")], False

            with patch.object(client, "health_canary", return_value=True), \
                 patch.object(client, "_fetch_uf_all_pages", side_effect=mock_fetch_uf):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

        assert isinstance(result, ParallelFetchResult)
        assert result.truncated_ufs == []

    @pytest.mark.asyncio
    async def test_multiple_truncated_ufs(self):
        """When multiple UFs are truncated, all are listed."""
        async with AsyncPNCPClient(max_concurrent=10) as client:
            async def mock_fetch_uf(uf, data_inicial, data_final, modalidades,
                                     status=None, max_pages=500):
                if uf in ("SP", "MG"):
                    return [_make_item(f"{uf}-1")], True
                return [_make_item(f"{uf}-1")], False

            with patch.object(client, "health_canary", return_value=True), \
                 patch.object(client, "_fetch_uf_all_pages", side_effect=mock_fetch_uf):
                result = await client.buscar_todas_ufs_paralelo(
                    ufs=["SP", "RJ", "MG"],
                    data_inicial="2026-01-01",
                    data_final="2026-01-31",
                )

        assert isinstance(result, ParallelFetchResult)
        assert set(result.truncated_ufs) == {"SP", "MG"}


class TestParallelFetchResultDataclass:
    """AC1: ParallelFetchResult includes truncated_ufs field."""

    def test_default_truncated_ufs_is_empty(self):
        """Default truncated_ufs is an empty list."""
        result = ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=[])
        assert result.truncated_ufs == []

    def test_truncated_ufs_can_be_set(self):
        """truncated_ufs can be populated."""
        result = ParallelFetchResult(
            items=[{"id": 1}],
            succeeded_ufs=["SP"],
            failed_ufs=[],
            truncated_ufs=["SP"],
        )
        assert result.truncated_ufs == ["SP"]
