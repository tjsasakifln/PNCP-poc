"""STORY-431 AC9: Tests for Observatory public endpoint.

CIG-BE-story-drift-observatorio: the route added a historical code path
(`_query_historical_sync` via `asyncio.to_thread`) for months > 30 days old
whose raw bids may be soft-deleted by the purge job. Tests mock *both*
data paths via the `mock_datalake` fixture so they are stable regardless
of how far in the past the requested month is relative to today's clock.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_DATALAKE_RESULTS = [
    {
        "uf": "SP", "valorTotalEstimado": 500000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoFormatted": "2026-03-10",
        "objetoCompra": "Aquisição de material de limpeza",
    },
    {
        "uf": "RJ", "valorTotalEstimado": 300000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoFormatted": "2026-03-15",
        "objetoCompra": "Prestação de serviços de informática",
    },
    {
        "uf": "SP", "valorTotalEstimado": 1200000.0,
        "codigoModalidadeContratacao": 8,
        "dataPublicacaoFormatted": "2026-03-20",
        "objetoCompra": "Compra de equipamentos médicos",
    },
    {
        "uf": "MG", "valorTotalEstimado": 0.0,
        "codigoModalidadeContratacao": 4,
        "dataPublicacaoFormatted": "2026-03-05",
        "objetoCompra": "Obra de reforma",
    },
] * 5  # 20 total results


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_datalake():
    """Mock both data paths (live datalake + historical sync) with the same
    canned results, so test behaviour is independent of today's date.
    """
    with patch(
        "datalake_query.query_datalake",
        new_callable=AsyncMock,
        return_value=MOCK_DATALAKE_RESULTS,
    ) as live, patch(
        "routes.observatorio._query_historical_sync",
        return_value=MOCK_DATALAKE_RESULTS,
    ) as historical:
        yield live, historical


@pytest.fixture
def mock_datalake_empty():
    """Same as mock_datalake but returns an empty list from both paths."""
    with patch(
        "datalake_query.query_datalake", new_callable=AsyncMock, return_value=[]
    ) as live, patch(
        "routes.observatorio._query_historical_sync", return_value=[]
    ) as historical:
        yield live, historical


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestObservatorioEndpoint:
    """STORY-431: Observatory relatorio endpoint."""

    def setup_method(self):
        """Clear Observatory cache between tests to avoid pollution."""
        from routes import observatorio
        observatorio._obs_cache.clear()

    def test_get_relatorio_200_no_auth(self, mock_datalake, client):
        """AC endpoint retorna 200 sem autenticação."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        assert resp.status_code == 200

    def test_get_relatorio_structure(self, mock_datalake, client):
        """Resposta contém todos os campos obrigatórios."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        data = resp.json()
        assert data["mes"] == 3
        assert data["ano"] == 2026
        assert data["mes_nome"] == "março"
        assert data["total_editais"] == 20
        assert "valor_total" in data
        assert "valor_medio" in data
        assert "top_ufs" in data
        assert "modalidades" in data
        assert "gerado_em" in data
        assert "fonte" in data
        assert "license" in data

    def test_top_ufs_sorted_desc(self, mock_datalake, client):
        """top_ufs ordenadas por volume decrescente."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        data = resp.json()
        ufs = data["top_ufs"]
        assert len(ufs) > 0
        # SP aparece mais (10x) vs RJ (5x) vs MG (5x)
        assert ufs[0]["uf"] == "SP"
        totals = [u["total"] for u in ufs]
        assert totals == sorted(totals, reverse=True)

    def test_modalidade_distribution(self, mock_datalake, client):
        """modalidades inclui pregão eletrônico (id=6)."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        data = resp.json()
        modalidade_ids = [m["modalidade_id"] for m in data["modalidades"]]
        assert 6 in modalidade_ids

    def test_pct_sum_approximately_100(self, mock_datalake, client):
        """Soma dos percentuais de modalidades é ~100%."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        data = resp.json()
        total_pct = sum(m["pct"] for m in data["modalidades"])
        assert abs(total_pct - 100.0) < 2.0  # tolerância para arredondamento

    def test_empty_datalake_returns_zeros(self, mock_datalake_empty, client):
        """Datalake vazio retorna 200 com zeros (não 500)."""
        resp = client.get("/v1/observatorio/relatorio/3/2026")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_editais"] == 0
        assert data["valor_total"] == 0.0

    def test_invalid_mes_returns_422(self, client):
        """Mês inválido (0 ou 13) retorna 422."""
        resp = client.get("/v1/observatorio/relatorio/0/2026")
        assert resp.status_code == 422
        resp2 = client.get("/v1/observatorio/relatorio/13/2026")
        assert resp2.status_code == 422

    def test_invalid_ano_returns_422(self, client):
        """Ano inválido retorna 422."""
        resp = client.get("/v1/observatorio/relatorio/3/2023")
        assert resp.status_code == 422

    def test_csv_endpoint_200(self, mock_datalake, client):
        """Endpoint CSV retorna 200 com content-type text/csv."""
        # Prime cache
        client.get("/v1/observatorio/relatorio/3/2026")
        resp = client.get("/v1/observatorio/relatorio/3/2026/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_csv_has_source_attribution(self, mock_datalake, client):
        """CSV inclui header com atribuição de fonte (CC BY 4.0)."""
        client.get("/v1/observatorio/relatorio/3/2026")
        resp = client.get("/v1/observatorio/relatorio/3/2026/csv")
        content = resp.content.decode("utf-8-sig")
        assert "SmartLic" in content
        assert "PNCP" in content
