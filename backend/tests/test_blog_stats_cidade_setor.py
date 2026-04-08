"""Tests for city × sector cross-reference blog stats endpoint."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)

MOCK_ITEMS = [
    {
        "objetoCompra": "Aquisição de computadores e periféricos",
        "orgaoEntidade": {"razaoSocial": "Prefeitura de São Paulo", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoPncp": "2026-04-01",
        "uf": "SP",
    },
    {
        "objetoCompra": "Fornecimento de servidores de rede",
        "orgaoEntidade": {"razaoSocial": "Secretaria de Educação SP", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoPncp": "2026-04-02",
        "uf": "SP",
    },
    {
        "objetoCompra": "Manutenção de equipamentos de TI",
        "orgaoEntidade": {"razaoSocial": "INSS Regional", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 80000.0,
        "codigoModalidadeContratacao": 8,
        "dataPublicacaoPncp": "2026-04-03",
        "uf": "SP",
    },
    {
        "objetoCompra": "Notebooks para secretaria de saúde",
        "orgaoEntidade": {"razaoSocial": "Prefeitura de São Paulo", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 200000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoPncp": "2026-04-04",
        "uf": "SP",
    },
    {
        "objetoCompra": "Switches e roteadores corporativos",
        "orgaoEntidade": {"razaoSocial": "Tribunal Regional", "municipioNome": "São Paulo"},
        "valorTotalEstimado": 300000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoPncp": "2026-04-05",
        "uf": "SP",
    },
    {
        "objetoCompra": "Impressoras multifuncionais",
        "orgaoEntidade": {"razaoSocial": "Prefeitura de Campinas", "municipioNome": "Campinas"},
        "valorTotalEstimado": 50000.0,
        "codigoModalidadeContratacao": 6,
        "dataPublicacaoPncp": "2026-04-01",
        "uf": "SP",
    },
]


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_stats_success(mock_query):
    """Returns stats filtered by both city and sector."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = MOCK_ITEMS
    resp = client.get("/v1/blog/stats/cidade/sao-paulo/setor/informatica")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cidade"] == "Sao Paulo"
    assert data["uf"] == "SP"
    assert data["sector_id"] == "informatica"
    assert data["total_editais"] == 5  # excludes Campinas item
    assert data["has_sufficient_data"] is True
    assert len(data["orgaos_frequentes"]) <= 5
    assert len(data["top_oportunidades"]) <= 5


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_insufficient_data(mock_query):
    """has_sufficient_data=False when <5 results."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = MOCK_ITEMS[:2]  # Only 2 items for São Paulo
    resp = client.get("/v1/blog/stats/cidade/sao-paulo/setor/informatica")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_sufficient_data"] is False
    assert data["total_editais"] == 2


def test_cidade_setor_unknown_city():
    """Returns 404 for unknown city."""
    resp = client.get("/v1/blog/stats/cidade/cidade-inexistente/setor/informatica")
    assert resp.status_code == 404


def test_cidade_setor_unknown_sector():
    """Returns 404 for unknown sector."""
    resp = client.get("/v1/blog/stats/cidade/sao-paulo/setor/setor-inexistente")
    assert resp.status_code == 404


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_empty_results(mock_query):
    """Returns zeros when no results match."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = []
    resp = client.get("/v1/blog/stats/cidade/manaus/setor/vestuario")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_editais"] == 0
    assert data["has_sufficient_data"] is False
    assert data["avg_value"] == 0.0


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_cache_hit(mock_query):
    """Second call uses cache, not PNCP."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = MOCK_ITEMS
    resp1 = client.get("/v1/blog/stats/cidade/curitiba/setor/engenharia")
    resp2 = client.get("/v1/blog/stats/cidade/curitiba/setor/engenharia")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert mock_query.call_count == 1  # Only called once


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_value_ranges(mock_query):
    """Value range min/max computed correctly."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = MOCK_ITEMS
    resp = client.get("/v1/blog/stats/cidade/sao-paulo/setor/informatica")
    data = resp.json()
    assert data["value_range_min"] == 80000.0
    assert data["value_range_max"] == 300000.0
    assert data["avg_value"] > 0


@patch("routes.blog_stats._query_pncp_for_sector", new_callable=AsyncMock)
def test_cidade_setor_top_modalidades(mock_query):
    """Top modalidades aggregated correctly."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    mock_query.return_value = MOCK_ITEMS
    resp = client.get("/v1/blog/stats/cidade/sao-paulo/setor/informatica")
    data = resp.json()
    mods = data["top_modalidades"]
    assert len(mods) > 0
    # Pregão Eletrônico should be most common (4 items with code 6)
    assert mods[0]["count"] >= 3
