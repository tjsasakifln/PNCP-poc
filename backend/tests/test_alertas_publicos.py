"""Tests for S3: alertas_publicos endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from startup.app_factory import create_app
import routes.alertas_publicos as _mod_alertas

# Patch target: datalake_query module (imported locally inside route function)
DL_PATCH = "datalake_query.query_datalake"


@pytest.fixture(autouse=True)
def _clear_cache():
    _mod_alertas._alertas_cache.clear()
    yield
    _mod_alertas._alertas_cache.clear()


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


MOCK_DATALAKE_RESULTS = [
    {
        "titulo": "Pregão para serviço de manutenção predial",
        "objeto": "Contratação de empresa para manutenção predial",
        "orgao": "Prefeitura Municipal de São Paulo",
        "valor_estimado": 150000.0,
        "uf": "SP",
        "municipio": "São Paulo",
        "modalidade": "Pregão Eletrônico",
        "data_publicacao": "2026-04-07",
        "data_abertura": "2026-04-14",
        "link_pncp": "https://pncp.gov.br/app/editais/123",
        "pncp_id": "pncp-123",
    },
    {
        "titulo": "Aquisição de material de escritório",
        "objeto": "Material de escritório variado",
        "orgao": "Governo do Estado de SP",
        "valor_estimado": 50000.0,
        "uf": "SP",
        "municipio": "São Paulo",
        "modalidade": "Dispensa",
        "data_publicacao": "2026-04-06",
        "data_abertura": None,
        "link_pncp": "",
        "pncp_id": "pncp-456",
    },
]


class TestAlertasPublicos:
    """Test GET /v1/alertas/{setor_id}/uf/{uf}."""

    @patch(DL_PATCH, new_callable=AsyncMock)
    def test_valid_sector_uf(self, mock_dl, client):
        mock_dl.return_value = MOCK_DATALAKE_RESULTS
        res = client.get("/v1/alertas/manutencao_predial/uf/SP")
        assert res.status_code == 200
        data = res.json()
        assert data["sector_id"] == "manutencao_predial"
        assert data["uf"] == "SP"
        assert isinstance(data["bids"], list)
        assert data["total"] >= 0

    @patch(DL_PATCH, new_callable=AsyncMock)
    def test_slug_format_sector(self, mock_dl, client):
        """Accept slug format (hyphens) for sector_id."""
        mock_dl.return_value = MOCK_DATALAKE_RESULTS
        res = client.get("/v1/alertas/manutencao-predial/uf/SP")
        assert res.status_code == 200
        assert res.json()["sector_id"] == "manutencao_predial"

    def test_invalid_sector(self, client):
        res = client.get("/v1/alertas/inexistente/uf/SP")
        assert res.status_code == 404

    def test_invalid_uf(self, client):
        res = client.get("/v1/alertas/manutencao_predial/uf/XX")
        assert res.status_code == 404

    @patch(DL_PATCH, new_callable=AsyncMock)
    def test_empty_results(self, mock_dl, client):
        mock_dl.return_value = []
        res = client.get("/v1/alertas/manutencao_predial/uf/AC")
        assert res.status_code == 200
        data = res.json()
        assert data["bids"] == []
        assert data["total"] == 0

    @patch(DL_PATCH, new_callable=AsyncMock)
    def test_uf_case_insensitive(self, mock_dl, client):
        mock_dl.return_value = []
        res = client.get("/v1/alertas/manutencao_predial/uf/sp")
        assert res.status_code == 200
        assert res.json()["uf"] == "SP"

    @patch(DL_PATCH, new_callable=AsyncMock)
    def test_datalake_failure_returns_empty(self, mock_dl, client):
        mock_dl.side_effect = Exception("Supabase timeout")
        res = client.get("/v1/alertas/manutencao_predial/uf/SP")
        assert res.status_code == 200
        assert res.json()["bids"] == []
