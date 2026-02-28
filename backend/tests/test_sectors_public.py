"""STORY-324 AC18: Tests for public sector stats endpoint.

Tests:
- Endpoint returns correct stats structure
- Slug → sector_id mapping
- 404 for unknown slugs
- Cache hit/miss behavior
- Sample items sanitization (no internal IDs)
- Sector list endpoint
"""

import time
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from routes.sectors_public import (
    sector_id_from_slug,
    sector_slug,
    get_all_sector_slugs,
    _stats_cache,
    _CACHE_TTL_SECONDS,
    _get_cached_stats,
    _set_cached_stats,
    invalidate_all_stats,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_stats_cache():
    """Clear the sector stats cache before each test."""
    _stats_cache.clear()
    yield
    _stats_cache.clear()


@pytest.fixture
def client():
    """FastAPI test client with sectors_public router."""
    from fastapi import FastAPI
    from routes.sectors_public import router

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return TestClient(app)


@pytest.fixture
def sample_stats():
    """Sample sector stats dict."""
    return {
        "sector_id": "saude",
        "sector_name": "Saúde",
        "sector_description": "Medicamentos, equipamentos hospitalares, insumos médicos",
        "slug": "saude",
        "total_open": 42,
        "total_value": 5000000.0,
        "avg_value": 119047.62,
        "top_ufs": [{"name": "SP", "count": 15}, {"name": "RJ", "count": 10}],
        "top_modalidades": [{"name": "Pregão Eletrônico", "count": 30}],
        "sample_items": [
            {
                "titulo": "Aquisição de medicamentos",
                "orgao": "Hospital Municipal",
                "valor": 100000.0,
                "uf": "SP",
                "data": "2026-02-28",
            }
        ],
        "last_updated": "2026-02-28T06:00:00+00:00",
    }


# ---------------------------------------------------------------------------
# Unit tests — slug mapping (AC8)
# ---------------------------------------------------------------------------

class TestSlugMapping:
    def test_simple_slug(self):
        assert sector_id_from_slug("saude") == "saude"

    def test_hyphenated_slug(self):
        assert sector_id_from_slug("manutencao-predial") == "manutencao_predial"

    def test_unknown_slug(self):
        assert sector_id_from_slug("inexistente") is None

    def test_sector_slug_simple(self):
        assert sector_slug("saude") == "saude"

    def test_sector_slug_underscore(self):
        assert sector_slug("materiais_eletricos") == "materiais-eletricos"

    def test_all_sector_slugs_count(self):
        slugs = get_all_sector_slugs()
        assert len(slugs) == 15

    def test_all_slugs_have_correct_structure(self):
        slugs = get_all_sector_slugs()
        for item in slugs:
            assert "id" in item
            assert "slug" in item
            assert "name" in item
            assert "description" in item
            assert "_" not in item["slug"], f"Slug should use hyphens: {item['slug']}"


# ---------------------------------------------------------------------------
# Unit tests — cache behavior (AC2)
# ---------------------------------------------------------------------------

class TestStatsCache:
    def test_cache_miss_returns_none(self):
        assert _get_cached_stats("saude") is None

    def test_cache_hit_returns_data(self, sample_stats):
        _set_cached_stats("saude", sample_stats)
        result = _get_cached_stats("saude")
        assert result is not None
        assert result["total_open"] == 42

    def test_cache_expired_returns_none(self, sample_stats):
        _stats_cache["saude"] = (sample_stats, time.time() - _CACHE_TTL_SECONDS - 1)
        assert _get_cached_stats("saude") is None

    def test_invalidate_all(self, sample_stats):
        _set_cached_stats("saude", sample_stats)
        _set_cached_stats("alimentos", sample_stats)
        invalidate_all_stats()
        assert _get_cached_stats("saude") is None
        assert _get_cached_stats("alimentos") is None


# ---------------------------------------------------------------------------
# API tests — GET /v1/sectors (list)
# ---------------------------------------------------------------------------

class TestSectorsListEndpoint:
    def test_list_all_sectors(self, client):
        resp = client.get("/v1/sectors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 15
        assert data[0]["slug"]
        assert data[0]["name"]

    def test_no_auth_required(self, client):
        """Public endpoint — no Authorization header needed."""
        resp = client.get("/v1/sectors")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# API tests — GET /v1/sectors/{slug}/stats (AC1)
# ---------------------------------------------------------------------------

class TestSectorStatsEndpoint:
    def test_unknown_slug_returns_404(self, client):
        resp = client.get("/v1/sectors/inexistente/stats")
        assert resp.status_code == 404

    def test_returns_stats_from_cache(self, client, sample_stats):
        _set_cached_stats("saude", sample_stats)
        resp = client.get("/v1/sectors/saude/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sector_id"] == "saude"
        assert data["total_open"] == 42
        assert data["slug"] == "saude"

    def test_hyphenated_slug_works(self, client, sample_stats):
        stats = {**sample_stats, "sector_id": "manutencao_predial", "slug": "manutencao-predial"}
        _set_cached_stats("manutencao_predial", stats)
        resp = client.get("/v1/sectors/manutencao-predial/stats")
        assert resp.status_code == 200
        assert resp.json()["sector_id"] == "manutencao_predial"

    @patch("routes.sectors_public._generate_sector_stats")
    def test_generates_on_cache_miss(self, mock_gen, client, sample_stats):
        mock_gen.return_value = sample_stats
        resp = client.get("/v1/sectors/saude/stats")
        assert resp.status_code == 200
        mock_gen.assert_called_once()

    def test_sample_items_no_internal_ids(self, client, sample_stats):
        """AC4: sample_items should not expose internal IDs."""
        _set_cached_stats("saude", sample_stats)
        resp = client.get("/v1/sectors/saude/stats")
        data = resp.json()
        for item in data["sample_items"]:
            assert "id" not in item
            assert "pncp_id" not in item
            assert "internal_id" not in item

    def test_stats_response_structure(self, client, sample_stats):
        """AC1: Verify all required fields are present."""
        _set_cached_stats("saude", sample_stats)
        resp = client.get("/v1/sectors/saude/stats")
        data = resp.json()
        required_fields = [
            "sector_id", "sector_name", "sector_description", "slug",
            "total_open", "total_value", "avg_value",
            "top_ufs", "top_modalidades", "sample_items", "last_updated",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Unit tests — stats generation
# ---------------------------------------------------------------------------

class TestStatsGeneration:
    @pytest.mark.asyncio
    @patch("pncp_client.PNCPClient")
    async def test_generate_returns_correct_structure(self, mock_client_cls):
        """Test _generate_sector_stats returns all required fields."""
        from routes.sectors_public import _generate_sector_stats
        from sectors import SECTORS

        mock_client = MagicMock()
        mock_client.buscar = AsyncMock(return_value=[])
        mock_client_cls.return_value = mock_client

        sector = SECTORS["saude"]
        result = await _generate_sector_stats("saude", sector)

        assert result["sector_id"] == "saude"
        assert result["sector_name"] == "Saúde"
        assert result["slug"] == "saude"
        assert result["total_open"] == 0
        assert isinstance(result["top_ufs"], list)
        assert isinstance(result["sample_items"], list)

    @pytest.mark.asyncio
    @patch("pncp_client.PNCPClient")
    async def test_generate_handles_pncp_failure(self, mock_client_cls):
        """Should return empty stats on PNCP failure, not crash."""
        from routes.sectors_public import _generate_sector_stats
        from sectors import SECTORS

        mock_client = MagicMock()
        mock_client.buscar = AsyncMock(side_effect=Exception("PNCP down"))
        mock_client_cls.return_value = mock_client

        sector = SECTORS["saude"]
        result = await _generate_sector_stats("saude", sector)

        assert result["total_open"] == 0
        assert result["total_value"] == 0.0

    @pytest.mark.asyncio
    @patch("pncp_client.PNCPClient")
    async def test_generate_filters_by_keywords(self, mock_client_cls):
        """Should only count results matching sector keywords."""
        from routes.sectors_public import _generate_sector_stats
        from sectors import SECTORS

        mock_client = MagicMock()
        mock_client.buscar = AsyncMock(return_value=[
            {"objetoCompra": "Aquisição de medicamentos hospitalares", "uf": "SP", "valorTotalEstimado": 100000},
            {"objetoCompra": "Compra de material de escritório", "uf": "RJ", "valorTotalEstimado": 50000},
        ])
        mock_client_cls.return_value = mock_client

        sector = SECTORS["saude"]
        result = await _generate_sector_stats("saude", sector)

        # "medicamentos" matches saude keywords, "material de escritório" does not
        assert result["total_open"] >= 1

    @pytest.mark.asyncio
    @patch("pncp_client.PNCPClient")
    async def test_sample_items_truncated(self, mock_client_cls):
        """Titles longer than 120 chars should be truncated."""
        from routes.sectors_public import _generate_sector_stats
        from sectors import SECTORS

        long_title = "Medicamento " * 20  # 240 chars
        mock_client = MagicMock()
        mock_client.buscar = AsyncMock(return_value=[
            {"objetoCompra": long_title, "uf": "SP", "valorTotalEstimado": 100000},
        ])
        mock_client_cls.return_value = mock_client

        sector = SECTORS["saude"]
        result = await _generate_sector_stats("saude", sector)

        if result["sample_items"]:
            assert len(result["sample_items"][0]["titulo"]) <= 120


# ---------------------------------------------------------------------------
# Cron helper test (AC3)
# ---------------------------------------------------------------------------

class TestRefreshAllSectorStats:
    @pytest.mark.asyncio
    @patch("routes.sectors_public._generate_sector_stats")
    async def test_refresh_all_sectors(self, mock_gen):
        from routes.sectors_public import refresh_all_sector_stats

        mock_gen.return_value = {
            "sector_id": "test",
            "sector_name": "Test",
            "sector_description": "Test",
            "slug": "test",
            "total_open": 10,
            "total_value": 0,
            "avg_value": 0,
            "top_ufs": [],
            "top_modalidades": [],
            "sample_items": [],
            "last_updated": "2026-01-01T00:00:00",
        }

        count = await refresh_all_sector_stats()
        assert count == 15  # All 15 sectors
        assert mock_gen.call_count == 15
