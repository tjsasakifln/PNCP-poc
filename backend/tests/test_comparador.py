"""Tests for comparador routes."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

import routes.comparador as _mod_comparador

# Patch target: datalake_query module (imported locally inside route function)
DL_PATCH = "datalake_query.query_datalake"
SB_PATCH = "routes.comparador.get_supabase"


@pytest.fixture(autouse=True)
def _clear_cache():
    _mod_comparador._comparador_cache.clear()
    yield
    _mod_comparador._comparador_cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


# Mock datalake results
MOCK_RESULTS = [
    {
        "pncp_id": "test-001",
        "titulo": "Pregão Eletrônico para serviços de engenharia",
        "orgao": "Prefeitura de Campinas",
        "valor_estimado": 500000.0,
        "uf": "SP",
        "municipio": "Campinas",
        "modalidade": "Pregão Eletrônico",
        "data_publicacao": "2026-04-01",
        "data_abertura": "2026-04-15",
        "link_pncp": "https://pncp.gov.br/test-001",
    },
    {
        "pncp_id": "test-002",
        "titulo": "Concorrência para fornecimento de equipamentos de TI",
        "orgao": "Governo do Estado de SP",
        "valor_estimado": 1200000.0,
        "uf": "SP",
        "municipio": "São Paulo",
        "modalidade": "Concorrência",
        "data_publicacao": "2026-04-02",
        "data_abertura": "2026-04-20",
        "link_pncp": "https://pncp.gov.br/test-002",
    },
    {
        "pncp_id": "test-003",
        "titulo": "Pregão para aquisição de material de escritório",
        "orgao": "Câmara Municipal de Santos",
        "valor_estimado": 80000.0,
        "uf": "SP",
        "municipio": "Santos",
        "modalidade": "Pregão Eletrônico",
        "data_publicacao": "2026-04-03",
        "data_abertura": None,
        "link_pncp": "",
    },
]


class TestBuscarEndpoint:
    def test_buscar_returns_results(self, client):
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = MOCK_RESULTS
            response = client.get("/v1/comparador/buscar?q=engenharia")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "engenharia"
        assert isinstance(data["bids"], list)
        assert data["total"] == len(data["bids"])
        assert len(data["bids"]) > 0
        # Verify bid fields are populated
        bid = data["bids"][0]
        assert "pncp_id" in bid
        assert "titulo" in bid
        assert "orgao" in bid
        assert "uf" in bid

    def test_buscar_requires_query(self, client):
        response = client.get("/v1/comparador/buscar")
        assert response.status_code == 422

    def test_buscar_query_too_short(self, client):
        response = client.get("/v1/comparador/buscar?q=ab")
        assert response.status_code == 422

    def test_buscar_invalid_uf(self, client):
        response = client.get("/v1/comparador/buscar?q=engenharia&uf=XX")
        assert response.status_code == 404
        assert "UF" in response.json()["detail"]

    def test_buscar_valid_uf(self, client):
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = MOCK_RESULTS
            response = client.get("/v1/comparador/buscar?q=engenharia&uf=SP")
        assert response.status_code == 200
        data = response.json()
        assert data["uf"] == "SP"

    def test_buscar_empty_results(self, client):
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = []
            response = client.get("/v1/comparador/buscar?q=termomuitoraro")
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0

    def test_buscar_datalake_error_returns_empty(self, client):
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.side_effect = Exception("Supabase timeout")
            response = client.get("/v1/comparador/buscar?q=engenharia")
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0

    def test_buscar_limits_to_10_results(self, client):
        many_results = [
            {**MOCK_RESULTS[0], "pncp_id": f"test-{i:03d}", "data_publicacao": f"2026-04-{i:02d}"}
            for i in range(1, 20)
        ]
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = many_results
            response = client.get("/v1/comparador/buscar?q=engenharia")
        assert response.status_code == 200
        data = response.json()
        assert len(data["bids"]) <= 10

    def test_buscar_uses_cache(self, client):
        with patch(DL_PATCH, new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = MOCK_RESULTS
            # First request
            r1 = client.get("/v1/comparador/buscar?q=engenharia")
            # Second request should hit cache
            r2 = client.get("/v1/comparador/buscar?q=engenharia")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # query_datalake should only be called once
        assert mock_dl.call_count == 1


class TestBidsEndpoint:
    def _make_supabase_mock(self, rows):
        mock_sb = MagicMock()
        mock_result = MagicMock()
        mock_result.data = rows
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_result
        return mock_sb

    def test_bids_by_ids(self, client):
        mock_sb = self._make_supabase_mock(MOCK_RESULTS[:2])
        with patch(SB_PATCH, return_value=mock_sb):
            response = client.get("/v1/comparador/bids?ids=test-001,test-002")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["bids"]) == 2
        pncp_ids = {b["pncp_id"] for b in data["bids"]}
        assert "test-001" in pncp_ids
        assert "test-002" in pncp_ids

    def test_bids_max_5(self, client):
        response = client.get("/v1/comparador/bids?ids=a,b,c,d,e,f")
        assert response.status_code == 400
        assert "5" in response.json()["detail"]

    def test_bids_empty_ids(self, client):
        response = client.get("/v1/comparador/bids?ids=,,,")
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0

    def test_bids_not_found_returns_empty(self, client):
        mock_sb = self._make_supabase_mock([])
        with patch(SB_PATCH, return_value=mock_sb):
            response = client.get("/v1/comparador/bids?ids=nonexistent-id")
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0

    def test_bids_supabase_error_returns_empty(self, client):
        with patch(SB_PATCH, side_effect=Exception("DB error")):
            response = client.get("/v1/comparador/bids?ids=test-001")
        assert response.status_code == 200
        data = response.json()
        assert data["bids"] == []
        assert data["total"] == 0

    def test_bids_uses_cache(self, client):
        mock_sb = self._make_supabase_mock(MOCK_RESULTS[:1])
        with patch(SB_PATCH, return_value=mock_sb) as mock_get:
            r1 = client.get("/v1/comparador/bids?ids=test-001")
            r2 = client.get("/v1/comparador/bids?ids=test-001")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # get_supabase should only be called once (second hit is cached)
        assert mock_get.call_count == 1

    def test_bids_single_id(self, client):
        mock_sb = self._make_supabase_mock([MOCK_RESULTS[0]])
        with patch(SB_PATCH, return_value=mock_sb):
            response = client.get("/v1/comparador/bids?ids=test-001")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["bids"][0]["pncp_id"] == "test-001"
