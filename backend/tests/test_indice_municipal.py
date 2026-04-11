"""Tests for STORY-435: Índice Municipal de Transparência em Compras Públicas.

Tests cover:
- GET /v1/indice-municipal (ranking nacional/UF)
- GET /v1/indice-municipal/periodos
- GET /v1/indice-municipal/{municipio_slug} (individual)
- Score calculation logic in services/indice_municipal
- Cache behavior
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from routes.indice_municipal import _route_cache
from services.indice_municipal import _svc_cache, _compute_scores, _periodo_to_dates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clear_caches():
    _route_cache.clear()
    _svc_cache.clear()
    yield
    _route_cache.clear()
    _svc_cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


# Supabase mock helper
def _make_supabase_mock(rows: list[dict]):
    """Returns a mock Supabase client whose .table().select()...execute() returns rows."""
    mock_resp = MagicMock()
    mock_resp.data = rows

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.gte.return_value = mock_query
    mock_query.lte.return_value = mock_query
    mock_query.ilike.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.execute.return_value = mock_resp

    mock_sb = MagicMock()
    mock_sb.table.return_value = mock_query
    return mock_sb


SAMPLE_ROWS_NACIONAL = [
    {
        "municipio_nome": "São Paulo",
        "municipio_ibge_code": "3550308",
        "uf": "SP",
        "periodo": "2026-Q1",
        "score_total": 78.5,
        "score_volume_publicacao": 18.0,
        "score_eficiencia_temporal": 15.5,
        "score_diversidade_mercado": 16.0,
        "score_transparencia_digital": 17.0,
        "score_consistencia": 12.0,
        "total_editais": 450,
        "ranking_nacional": 1,
        "ranking_uf": 1,
        "percentil": 98,
        "calculado_em": "2026-04-11T12:00:00+00:00",
    },
    {
        "municipio_nome": "Campinas",
        "municipio_ibge_code": "3509502",
        "uf": "SP",
        "periodo": "2026-Q1",
        "score_total": 65.2,
        "score_volume_publicacao": 14.0,
        "score_eficiencia_temporal": 12.0,
        "score_diversidade_mercado": 13.2,
        "score_transparencia_digital": 14.0,
        "score_consistencia": 12.0,
        "total_editais": 180,
        "ranking_nacional": 2,
        "ranking_uf": 2,
        "percentil": 90,
        "calculado_em": "2026-04-11T12:00:00+00:00",
    },
]

SAMPLE_ROW_MUNICIPIO = SAMPLE_ROWS_NACIONAL[0]


# ---------------------------------------------------------------------------
# Tests: GET /v1/indice-municipal (ranking)
# ---------------------------------------------------------------------------

class TestRankingEndpoint:
    def test_ranking_returns_list(self, client):
        mock_sb = _make_supabase_mock(SAMPLE_ROWS_NACIONAL)
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal?periodo=2026-Q1")

        assert resp.status_code == 200
        data = resp.json()
        assert "resultados" in data
        assert len(data["resultados"]) == 2
        assert data["resultados"][0]["municipio_nome"] == "São Paulo"
        assert data["resultados"][0]["municipio_slug"] == "sao-paulo-sp"
        assert data["periodo"] == "2026-Q1"
        assert data["fonte"] == "PNCP via SmartLic Observatório"

    def test_ranking_filters_by_uf(self, client):
        mock_sb = _make_supabase_mock([SAMPLE_ROWS_NACIONAL[0]])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal?periodo=2026-Q1&uf=SP")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["resultados"]) == 1
        assert data["resultados"][0]["uf"] == "SP"

    def test_ranking_invalid_uf(self, client):
        resp = client.get("/v1/indice-municipal?uf=XX")
        assert resp.status_code == 400

    def test_ranking_invalid_periodo_format(self, client):
        resp = client.get("/v1/indice-municipal?periodo=2026-X1")
        assert resp.status_code == 422  # FastAPI validation

    def test_ranking_cors_header(self, client):
        mock_sb = _make_supabase_mock([])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal?periodo=2026-Q1")
        assert resp.headers.get("access-control-allow-origin") == "*"

    def test_ranking_supabase_error_returns_empty(self, client):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("Supabase unreachable")
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal?periodo=2026-Q1")
        assert resp.status_code == 200
        assert resp.json()["resultados"] == []


# ---------------------------------------------------------------------------
# Tests: GET /v1/indice-municipal/periodos
# ---------------------------------------------------------------------------

class TestPeriodosEndpoint:
    def test_periodos_returns_list(self, client):
        mock_sb = _make_supabase_mock([{"periodo": "2026-Q1"}])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal/periodos")

        assert resp.status_code == 200
        data = resp.json()
        assert "periodos" in data
        assert isinstance(data["periodos"], list)

    def test_periodos_fallback_when_empty(self, client):
        mock_sb = _make_supabase_mock([])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal/periodos")

        assert resp.status_code == 200
        data = resp.json()
        # When DB empty, returns default current period
        assert len(data["periodos"]) >= 1


# ---------------------------------------------------------------------------
# Tests: GET /v1/indice-municipal/{municipio_slug}
# ---------------------------------------------------------------------------

class TestMunicipioEndpoint:
    def test_individual_returns_data(self, client):
        mock_sb = _make_supabase_mock([SAMPLE_ROW_MUNICIPIO])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal/sao-paulo-sp?periodo=2026-Q1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["municipio_nome"] == "São Paulo"
        assert data["uf"] == "SP"
        assert data["score_total"] == 78.5

    def test_individual_404_when_not_found(self, client):
        mock_sb = _make_supabase_mock([])
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            resp = client.get("/v1/indice-municipal/nao-existe-sp?periodo=2026-Q1")

        assert resp.status_code == 404

    def test_individual_invalid_slug_format(self, client):
        resp = client.get("/v1/indice-municipal/municipio-sem-uf")
        assert resp.status_code == 400

    def test_individual_invalid_uf_in_slug(self, client):
        resp = client.get("/v1/indice-municipal/sao-paulo-xx")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Tests: Score calculation (unit tests for services/indice_municipal.py)
# ---------------------------------------------------------------------------

class TestScoreCalculation:
    def test_periodo_to_dates_q1(self):
        start, end = _periodo_to_dates("2026-Q1")
        assert start == "2026-01-01"
        assert end == "2026-03-31"

    def test_periodo_to_dates_q2(self):
        start, end = _periodo_to_dates("2026-Q2")
        assert start == "2026-04-01"
        assert end == "2026-06-30"

    def test_periodo_to_dates_q4(self):
        start, end = _periodo_to_dates("2026-Q4")
        assert start == "2026-10-01"
        assert end == "2026-12-31"

    def test_periodo_to_dates_invalid(self):
        with pytest.raises(ValueError):
            _periodo_to_dates("2026-X1")

    def test_compute_scores_pregao_eletronico(self):
        # 10 editais, todos pregão eletrônico (cod 6) = score_transparencia_digital = 20
        rows = [
            {
                "modalidade_id": 6,
                "data_publicacao_pncp": "2026-01-15",
                "data_encerramento_proposta": "2026-01-20",  # 5 dias → ≤8 → 20pts eficiência
                "valor_estimado": 100_000,
                "cnpj_contratado": f"cnpj{i:014d}",
            }
            for i in range(10)
        ]
        scores = _compute_scores(rows, "2026-Q1")
        assert scores["transparencia_digital"] == 20.0
        assert scores["eficiencia_temporal"] == 20.0  # avg_delta=5 ≤ 8

    def test_compute_scores_minimum_editais(self):
        # 10 editais únicos = diversidade máxima
        rows = [
            {
                "modalidade_id": 8,  # Dispensa
                "data_publicacao_pncp": "2026-01-15",
                "data_encerramento_proposta": "2026-02-15",  # 31 dias → score_et=0
                "valor_estimado": 50_000,
                "cnpj_contratado": f"{i:014d}",  # todos únicos
            }
            for i in range(10)
        ]
        scores = _compute_scores(rows, "2026-Q1")
        assert scores["transparencia_digital"] == 0.0  # 0% pregão eletrônico
        assert scores["eficiencia_temporal"] == 0.0    # 31 dias ≥ 30
        assert scores["diversidade_mercado"] > 0       # 10 CNPJs únicos / 10 = 1.0 → 20pts
        total = sum(scores.values())
        assert 0 <= total <= 100

    def test_compute_scores_sum_within_range(self):
        """Score total sempre entre 0 e 100."""
        rows = [
            {
                "modalidade_id": 6,
                "data_publicacao_pncp": f"2026-0{(i % 3) + 1}-01",
                "data_encerramento_proposta": f"2026-0{(i % 3) + 1}-10",
                "valor_estimado": 100_000 * (i + 1),
                "cnpj_contratado": f"{i:014d}",
            }
            for i in range(15)
        ]
        scores = _compute_scores(rows, "2026-Q1")
        total = sum(scores.values())
        assert 0 <= total <= 100
        for nome, val in scores.items():
            assert 0 <= val <= 20, f"{nome}={val} fora do range 0-20"

    @pytest.mark.asyncio
    async def test_calcular_indice_municipio_insufficient_editais(self):
        """Município com < 10 editais retorna None."""
        from services.indice_municipal import calcular_indice_municipio

        mock_resp = MagicMock()
        mock_resp.data = [{"id": "x"}] * 5  # só 5 editais → abaixo do mínimo

        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_resp

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_query

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await calcular_indice_municipio("Município Pequeno", "SC", "2026-Q1")

        assert result is None

    @pytest.mark.asyncio
    async def test_calcular_indice_municipio_uses_cache(self):
        """Segundo request ao mesmo município usa cache e não bate Supabase."""
        from services.indice_municipal import calcular_indice_municipio

        raw_rows = [
            {
                "id": f"row-{i}",
                "modalidade_id": 6,
                "data_publicacao_pncp": "2026-01-15",
                "data_encerramento_proposta": "2026-01-20",
                "valor_estimado": 100_000,
                "cnpj_contratado": f"{i:014d}",
                "municipio": "São Paulo",
                "uf": "SP",
            }
            for i in range(15)
        ]

        mock_resp = MagicMock()
        mock_resp.data = raw_rows

        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = mock_resp

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_query

        with patch("supabase_client.get_supabase", return_value=mock_sb) as mock_get_sb:
            r1 = await calcular_indice_municipio("São Paulo", "SP", "2026-Q1")
            r2 = await calcular_indice_municipio("São Paulo", "SP", "2026-Q1")

        assert r1 is not None
        assert r2 is not None
        assert r1 == r2
        # Supabase deve ter sido chamado apenas 1 vez (segundo request usa cache)
        assert mock_get_sb.call_count == 1
