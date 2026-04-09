"""Tests for SEO Wave 2: contratos_publicos endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from main import app
    return TestClient(app)


def _mock_rows(n=5):
    """Generate mock pncp_supplier_contracts rows."""
    rows = []
    for i in range(n):
        rows.append({
            "ni_fornecedor": f"1234567800{i:04d}",
            "nome_fornecedor": f"Fornecedor {i}",
            "orgao_cnpj": f"9876543200{i:04d}",
            "orgao_nome": f"Orgao {i}",
            "valor_global": str((i + 1) * 10000.0),
            "data_assinatura": f"2026-03-{15 - i:02d}",
            "objeto_contrato": f"Aquisicao de uniformes e fardamentos item {i}",
        })
    return rows


# ---------------------------------------------------------------------------
# Contratos Stats
# ---------------------------------------------------------------------------

class TestContratosStats:
    @patch("routes.contratos_publicos.get_supabase", create=True)
    def test_contratos_stats_success(self, mock_get_sb, client):
        """GET /v1/contratos/{setor}/{uf}/stats returns 200 with valid data."""
        mock_sb = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = _mock_rows(5)
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_resp

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            # Clear cache to ensure fresh query
            from routes.contratos_publicos import _contratos_cache
            _contratos_cache.clear()

            resp = client.get("/v1/contratos/vestuario/sp/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["sector_id"] == "vestuario"
        assert data["uf"] == "SP"
        assert data["total_contracts"] == 5
        assert data["total_value"] > 0
        assert data["avg_value"] > 0
        assert len(data["top_orgaos"]) > 0
        assert len(data["top_fornecedores"]) > 0
        assert len(data["sample_contracts"]) > 0
        assert "aviso_legal" in data

    def test_contratos_stats_invalid_sector(self, client):
        """GET /v1/contratos/{setor}/{uf}/stats returns 404 for invalid sector."""
        resp = client.get("/v1/contratos/naoexiste/sp/stats")
        assert resp.status_code == 404

    def test_contratos_stats_invalid_uf(self, client):
        """GET /v1/contratos/{setor}/{uf}/stats returns 404 for invalid UF."""
        resp = client.get("/v1/contratos/vestuario/xx/stats")
        assert resp.status_code == 404

    @patch("routes.contratos_publicos.get_supabase", create=True)
    def test_contratos_stats_empty_results(self, mock_get_sb, client):
        """GET /v1/contratos/{setor}/{uf}/stats returns 200 with zero contracts when no keyword match."""
        mock_sb = MagicMock()
        mock_resp = MagicMock()
        # Rows that don't match vestuario keywords
        mock_resp.data = [{"objeto_contrato": "servico de TI", "ni_fornecedor": "123", "orgao_cnpj": "456",
                           "orgao_nome": "Org", "nome_fornecedor": "F", "valor_global": "100",
                           "data_assinatura": "2026-03-01"}]
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_resp

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            from routes.contratos_publicos import _contratos_cache
            _contratos_cache.clear()
            resp = client.get("/v1/contratos/vestuario/sp/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_contracts"] == 0

    def test_contratos_stats_cache_hit(self, client):
        """Second call should hit cache (no DB call)."""
        import time as _time
        from routes.contratos_publicos import _contratos_cache, _set_cached

        fake_data = {
            "sector_id": "vestuario", "sector_name": "Vestuario", "uf": "RJ",
            "total_contracts": 10, "total_value": 50000.0, "avg_value": 5000.0,
            "top_orgaos": [], "top_fornecedores": [], "monthly_trend": [],
            "sample_contracts": [], "last_updated": "2026-04-08T00:00:00Z",
            "aviso_legal": "test",
        }
        _set_cached(_contratos_cache, "contratos:vestuario:RJ", fake_data)

        resp = client.get("/v1/contratos/vestuario/rj/stats")
        assert resp.status_code == 200
        assert resp.json()["total_contracts"] == 10

        # Cleanup
        _contratos_cache.clear()

    def test_contratos_slug_with_hyphens(self, client):
        """Sector slugs with hyphens should be normalized to underscores."""
        from routes.contratos_publicos import _contratos_cache, _set_cached

        fake_data = {
            "sector_id": "manutencao_predial", "sector_name": "Manutencao Predial", "uf": "MG",
            "total_contracts": 3, "total_value": 9000.0, "avg_value": 3000.0,
            "top_orgaos": [], "top_fornecedores": [], "monthly_trend": [],
            "sample_contracts": [], "last_updated": "2026-04-08T00:00:00Z",
            "aviso_legal": "test",
        }
        _set_cached(_contratos_cache, "contratos:manutencao_predial:MG", fake_data)

        resp = client.get("/v1/contratos/manutencao-predial/mg/stats")
        assert resp.status_code == 200
        assert resp.json()["sector_id"] == "manutencao_predial"

        _contratos_cache.clear()


# ---------------------------------------------------------------------------
# Fornecedores Stats
# ---------------------------------------------------------------------------

class TestFornecedoresStats:
    @patch("routes.contratos_publicos.get_supabase", create=True)
    def test_fornecedores_stats_success(self, mock_get_sb, client):
        """GET /v1/fornecedores/{setor}/{uf}/stats returns 200."""
        mock_sb = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = _mock_rows(5)
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_resp

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            from routes.contratos_publicos import _fornecedores_cache
            _fornecedores_cache.clear()
            resp = client.get("/v1/fornecedores/vestuario/sp/stats")

        assert resp.status_code == 200
        data = resp.json()
        assert data["sector_id"] == "vestuario"
        assert data["uf"] == "SP"
        assert data["total_suppliers"] > 0
        assert len(data["supplier_ranking"]) > 0
        assert "aviso_legal" in data

    def test_fornecedores_stats_invalid_sector(self, client):
        """GET /v1/fornecedores/{setor}/{uf}/stats returns 404 for invalid sector."""
        resp = client.get("/v1/fornecedores/naoexiste/sp/stats")
        assert resp.status_code == 404

    def test_fornecedores_stats_invalid_uf(self, client):
        """GET /v1/fornecedores/{setor}/{uf}/stats returns 404 for invalid UF."""
        resp = client.get("/v1/fornecedores/vestuario/xx/stats")
        assert resp.status_code == 404

    def test_fornecedores_stats_cache_hit(self, client):
        """Second call should hit cache."""
        from routes.contratos_publicos import _fornecedores_cache, _set_cached

        fake_data = {
            "sector_id": "informatica", "sector_name": "Informatica", "uf": "PR",
            "total_suppliers": 20, "supplier_ranking": [],
            "top_orgaos_compradores": [],
            "last_updated": "2026-04-08T00:00:00Z",
            "aviso_legal": "test",
        }
        _set_cached(_fornecedores_cache, "fornecedores:informatica:PR", fake_data)

        resp = client.get("/v1/fornecedores/informatica/pr/stats")
        assert resp.status_code == 200
        assert resp.json()["total_suppliers"] == 20

        _fornecedores_cache.clear()
