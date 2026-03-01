"""Tests for MKT-002 AC1: Blog stats API endpoints.

Tests all 4 public endpoints:
- GET /v1/blog/stats/setor/{setor_id}
- GET /v1/blog/stats/setor/{setor_id}/uf/{uf}
- GET /v1/blog/stats/cidade/{cidade}
- GET /v1/blog/stats/panorama/{setor_id}
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_blog_cache():
    """Clear blog stats cache between tests."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    yield
    _blog_cache.clear()


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


# Sample PNCP results for mocking
MOCK_PNCP_RESULTS = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoPncp": "2026-02-28",
        "orgaoEntidade": {
            "razaoSocial": "Secretaria de Segurança Pública",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoPncp": "2026-02-27",
        "orgaoEntidade": {
            "razaoSocial": "Polícia Militar do Estado de SP",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Roupas profissionais para servidores",
        "uf": "RJ",
        "valorTotalEstimado": 80000.0,
        "codigoModalidadeContratacao": 7,
        "dataPublicacaoPncp": "2026-02-26",
        "orgaoEntidade": {
            "razaoSocial": "Prefeitura Municipal do Rio",
            "municipioNome": "Rio de Janeiro",
        },
    },
]


def _mock_pncp_buscar(uf, **kwargs):
    """Return filtered mock results by UF."""
    return [r for r in MOCK_PNCP_RESULTS if r["uf"] == uf]


# ---------------------------------------------------------------------------
# Endpoint 1: GET /v1/blog/stats/setor/{setor_id}
# ---------------------------------------------------------------------------

class TestSectorBlogStats:
    def test_sector_stats_success(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_pncp_buscar)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["sector_name"] == "Vestuário e Uniformes"
            assert data["total_editais"] >= 0
            assert "top_modalidades" in data
            assert "top_ufs" in data
            assert "trend_90d" in data
            assert "last_updated" in data
            assert data["value_range_min"] >= 0
            assert data["value_range_max"] >= 0
            assert data["avg_value"] >= 0

    def test_sector_stats_cached(self, client):
        """Second call should hit cache (no PNCP query)."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res1 = client.get("/v1/blog/stats/setor/vestuario")
            assert res1.status_code == 200

            res2 = client.get("/v1/blog/stats/setor/vestuario")
            assert res2.status_code == 200
            assert res2.json() == res1.json()

            # PNCPClient should only be instantiated once
            assert mock_cls.call_count == 1

    def test_sector_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/setor/nonexistent")
        assert res.status_code == 404

    def test_sector_stats_slug_format(self, client):
        """Accept slug with hyphens (e.g., manutencao-predial)."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/manutencao-predial")
            assert res.status_code == 200
            assert res.json()["sector_id"] == "manutencao_predial"

    def test_sector_stats_no_auth_required(self, client):
        """Endpoint should be public (no auth header needed)."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/alimentos")
            assert res.status_code == 200

    def test_sector_stats_trend_structure(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/informatica")
            data = res.json()
            assert len(data["trend_90d"]) == 3
            for point in data["trend_90d"]:
                assert "period" in point
                assert "count" in point
                assert "avg_value" in point


# ---------------------------------------------------------------------------
# Endpoint 2: GET /v1/blog/stats/setor/{setor_id}/uf/{uf}
# ---------------------------------------------------------------------------

class TestSectorUfStats:
    def test_sector_uf_stats_success(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_pncp_buscar)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["uf"] == "SP"
            assert data["total_editais"] >= 0
            assert data["avg_value"] >= 0
            assert "top_oportunidades" in data

    def test_sector_uf_stats_lowercase(self, client):
        """Accept lowercase UF."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/sp")
            assert res.status_code == 200
            assert res.json()["uf"] == "SP"

    def test_sector_uf_stats_invalid_uf(self, client):
        res = client.get("/v1/blog/stats/setor/vestuario/uf/XX")
        assert res.status_code == 404

    def test_sector_uf_stats_invalid_sector(self, client):
        res = client.get("/v1/blog/stats/setor/nonexistent/uf/SP")
        assert res.status_code == 404

    def test_sector_uf_top_oportunidades(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_pncp_buscar)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            data = res.json()
            for item in data["top_oportunidades"]:
                assert "titulo" in item
                assert "orgao" in item
                assert "uf" in item
                assert "data" in item


# ---------------------------------------------------------------------------
# Endpoint 3: GET /v1/blog/stats/cidade/{cidade}
# ---------------------------------------------------------------------------

class TestCidadeStats:
    def test_cidade_stats_success(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=MOCK_PNCP_RESULTS[:2])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/cidade/são-paulo")
            assert res.status_code == 200

            data = res.json()
            assert data["cidade"] == "São Paulo"
            assert data["uf"] == "SP"
            assert "orgaos_frequentes" in data
            assert data["avg_value"] >= 0

    def test_cidade_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/cidade/atlantida")
        assert res.status_code == 404

    def test_cidade_stats_cached(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res1 = client.get("/v1/blog/stats/cidade/curitiba")
            res2 = client.get("/v1/blog/stats/cidade/curitiba")
            assert res1.status_code == 200
            assert res2.json() == res1.json()
            assert mock_cls.call_count == 1


# ---------------------------------------------------------------------------
# Endpoint 4: GET /v1/blog/stats/panorama/{setor_id}
# ---------------------------------------------------------------------------

class TestPanoramaStats:
    def test_panorama_stats_success(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_pncp_buscar)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/panorama/vestuario")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["sector_name"] == "Vestuário e Uniformes"
            assert data["total_nacional"] >= 0
            assert data["total_value"] >= 0
            assert data["crescimento_estimado_pct"] > 0
            assert "sazonalidade" in data
            assert len(data["sazonalidade"]) == 12

    def test_panorama_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/panorama/nonexistent")
        assert res.status_code == 404

    def test_panorama_stats_sazonalidade_structure(self, client):
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/panorama/software")
            data = res.json()
            for month in data["sazonalidade"]:
                assert "period" in month
                assert "count" in month
                assert "avg_value" in month

    def test_panorama_stats_no_auth(self, client):
        """Public endpoint — no auth required."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/panorama/saude")
            assert res.status_code == 200


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

class TestCacheInvalidation:
    def test_invalidate_blog_cache(self, client):
        from routes.blog_stats import invalidate_blog_cache, _blog_cache

        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            client.get("/v1/blog/stats/setor/vestuario")
            assert len(_blog_cache) > 0

            invalidate_blog_cache()
            assert len(_blog_cache) == 0


# ---------------------------------------------------------------------------
# MKT-003: Enhanced SectorUfStats fields
# ---------------------------------------------------------------------------

# Richer mock data for MKT-003 tests — two items with distinct modalities/values
MOCK_PNCP_UF_SP = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,  # Pregão Eletrônico
        "dataPublicacaoPncp": "2026-02-28",
        "orgaoEntidade": {
            "razaoSocial": "Secretaria de Segurança Pública",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão de uniformes",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 7,  # Dispensa de Licitação
        "dataPublicacaoPncp": "2026-02-27",
        "orgaoEntidade": {
            "razaoSocial": "Polícia Militar do Estado de SP",
            "municipioNome": "São Paulo",
        },
    },
]


def _mock_sp_only(uf, **kwargs):
    """Return SP items only; empty for other UFs."""
    if uf == "SP":
        return MOCK_PNCP_UF_SP
    return []


class TestSectorUfStatsEnhanced:
    """MKT-003: Tests for enhanced SectorUfStats fields."""

    def test_sector_uf_stats_enhanced_fields(self, client):
        """Response includes value_range_min, value_range_max, top_modalidades, trend_90d with correct types."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_sp_only)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()

            # Field presence
            assert "value_range_min" in data
            assert "value_range_max" in data
            assert "top_modalidades" in data
            assert "trend_90d" in data

            # Type checks
            assert isinstance(data["value_range_min"], (int, float))
            assert isinstance(data["value_range_max"], (int, float))
            assert isinstance(data["top_modalidades"], list)
            assert isinstance(data["trend_90d"], list)

    def test_sector_uf_stats_value_range(self, client):
        """With 2 items of different values, min < max (or equal if 1 item)."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_sp_only)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            # Two SP items: 150_000 and 250_000
            assert data["value_range_min"] <= data["value_range_max"]
            # Specifically, min should be 150_000 and max should be 250_000
            assert data["value_range_min"] == 150000.0
            assert data["value_range_max"] == 250000.0

    def test_sector_uf_stats_value_range_single_item(self, client):
        """With exactly 1 valued item, min == max."""
        single_item = [MOCK_PNCP_UF_SP[0].copy()]  # only 150_000 item

        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=single_item)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            assert data["value_range_min"] == data["value_range_max"]
            assert data["value_range_min"] == 150000.0

    def test_sector_uf_stats_modalities(self, client):
        """top_modalidades has entries with name (str) and count (int) structure."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_sp_only)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            top_mods = data["top_modalidades"]
            assert len(top_mods) >= 1

            for entry in top_mods:
                assert "name" in entry
                assert "count" in entry
                assert isinstance(entry["name"], str)
                assert isinstance(entry["count"], int)
                assert entry["count"] >= 1

            # Both mock items have distinct modalities (1 and 7), so 2 entries expected
            assert len(top_mods) == 2
            names = {e["name"] for e in top_mods}
            assert "Pregão Eletrônico" in names
            assert "Dispensa de Licitação" in names

    def test_sector_uf_stats_trend(self, client):
        """trend_90d has exactly 3 entries, each with period, count, avg_value."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(side_effect=_mock_sp_only)
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            trend = data["trend_90d"]
            assert len(trend) == 3

            for point in trend:
                assert "period" in point
                assert "count" in point
                assert "avg_value" in point
                assert isinstance(point["period"], str)
                assert isinstance(point["count"], int)
                assert isinstance(point["avg_value"], (int, float))
                # Counts are positive (at least 1 due to max(1, ...) guard)
                assert point["count"] >= 1

            # Periods should be in ascending order (oldest to most recent)
            periods = [p["period"] for p in trend]
            assert periods == sorted(periods)

    def test_sector_uf_stats_empty_results(self, client):
        """When PNCP returns no results: value_range_min=0, top_modalidades=[], trend counts >= 1."""
        with patch("pncp_client.PNCPClient") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.buscar = AsyncMock(return_value=[])
            mock_cls.return_value = mock_instance

            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()

            assert data["value_range_min"] == 0.0
            assert data["value_range_max"] == 0.0
            assert data["top_modalidades"] == []

            # trend_90d still has 3 entries (count >= 1 by _estimate_trend guard)
            trend = data["trend_90d"]
            assert len(trend) == 3
            for point in trend:
                assert point["count"] >= 1
                assert point["avg_value"] == 0.0
