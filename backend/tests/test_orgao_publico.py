"""Tests for SEO Onda 2: /v1/orgao/{cnpj}/stats endpoint."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear orgao_publico cache between tests."""
    from routes.orgao_publico import _orgao_cache
    _orgao_cache.clear()
    yield
    _orgao_cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


def _make_bid_row(
    orgao_razao_social: str = "PREFEITURA MUNICIPAL DE CURITIBA",
    esfera_id: str = "M",
    uf: str = "PR",
    municipio: str = "Curitiba",
    modalidade_nome: str = "Pregão Eletrônico",
    objeto_compra: str = "Aquisição de material de escritório",
    valor_total_estimado: float = 50000.0,
    data_publicacao: str | None = None,
) -> dict:
    if data_publicacao is None:
        data_publicacao = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "orgao_razao_social": orgao_razao_social,
        "esfera_id": esfera_id,
        "uf": uf,
        "municipio": municipio,
        "modalidade_nome": modalidade_nome,
        "objeto_compra": objeto_compra,
        "valor_total_estimado": valor_total_estimado,
        "data_publicacao": data_publicacao,
    }


def _mock_supabase_response(data: list[dict]):
    mock_sb = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = data
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .limit.return_value
        .execute
    ).return_value = mock_resp
    return mock_sb


VALID_CNPJ = "12345678000190"


class TestOrgaoPublico:
    """Tests for GET /v1/orgao/{cnpj}/stats."""

    @patch("supabase_client.get_supabase")
    def test_valid_cnpj_returns_stats(self, mock_get_sb, client):
        """Valid CNPJ with bids returns full stats response."""
        rows = [_make_bid_row() for _ in range(3)]
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nome"] == "PREFEITURA MUNICIPAL DE CURITIBA"
        assert data["cnpj"] == VALID_CNPJ
        assert data["esfera"] == "Municipal"
        assert data["uf"] == "PR"
        assert data["municipio"] == "Curitiba"
        assert data["total_licitacoes"] == 3
        assert data["valor_medio_estimado"] == 50000.0
        assert data["valor_total_estimado"] == 150000.0
        assert isinstance(data["top_modalidades"], list)
        assert isinstance(data["top_setores"], list)
        assert isinstance(data["ultimas_licitacoes"], list)
        assert data["aviso_legal"]

    def test_invalid_cnpj_returns_400(self, client):
        """Non-14-digit CNPJ returns 400."""
        resp = client.get("/v1/orgao/12345/stats")
        assert resp.status_code == 400

    @patch("supabase_client.get_supabase")
    def test_unknown_cnpj_returns_404(self, mock_get_sb, client):
        """CNPJ with zero bids returns 404."""
        mock_get_sb.return_value = _mock_supabase_response([])

        resp = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp.status_code == 404

    @patch("supabase_client.get_supabase")
    def test_response_schema(self, mock_get_sb, client):
        """All required fields present with correct types."""
        rows = [_make_bid_row()]
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp.status_code == 200
        data = resp.json()

        required_fields = {
            "nome": str, "cnpj": str, "esfera": str, "uf": str,
            "municipio": str, "total_licitacoes": int,
            "licitacoes_30d": int, "licitacoes_90d": int, "licitacoes_365d": int,
            "valor_medio_estimado": (int, float),
            "valor_total_estimado": (int, float),
            "top_modalidades": list, "top_setores": list,
            "ultimas_licitacoes": list, "aviso_legal": str,
        }
        for field, expected_type in required_fields.items():
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], expected_type), f"Wrong type for {field}"

    @patch("supabase_client.get_supabase")
    def test_cache_hit(self, mock_get_sb, client):
        """Second request served from cache — no DB call."""
        rows = [_make_bid_row()]
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp1 = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp1.status_code == 200

        mock_get_sb.reset_mock()
        resp2 = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()
        mock_get_sb.assert_not_called()

    @patch("supabase_client.get_supabase")
    def test_bid_count_windows(self, mock_get_sb, client):
        """Verify 30d/90d/365d counts are correctly computed."""
        now = datetime.now(timezone.utc)
        rows = [
            _make_bid_row(data_publicacao=(now - timedelta(days=5)).strftime("%Y-%m-%d")),   # Within 30d
            _make_bid_row(data_publicacao=(now - timedelta(days=60)).strftime("%Y-%m-%d")),  # Within 90d
            _make_bid_row(data_publicacao=(now - timedelta(days=200)).strftime("%Y-%m-%d")), # Within 365d
            _make_bid_row(data_publicacao=(now - timedelta(days=400)).strftime("%Y-%m-%d")), # Outside 365d
        ]
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["licitacoes_30d"] == 1
        assert data["licitacoes_90d"] == 2
        assert data["licitacoes_365d"] == 3
        assert data["total_licitacoes"] == 4

    @patch("supabase_client.get_supabase")
    def test_top_modalidades_aggregation(self, mock_get_sb, client):
        """Top modalidades sorted by count descending."""
        rows = [
            _make_bid_row(modalidade_nome="Pregão Eletrônico"),
            _make_bid_row(modalidade_nome="Pregão Eletrônico"),
            _make_bid_row(modalidade_nome="Pregão Eletrônico"),
            _make_bid_row(modalidade_nome="Dispensa"),
            _make_bid_row(modalidade_nome="Dispensa"),
            _make_bid_row(modalidade_nome="Concorrência"),
        ]
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get(f"/v1/orgao/{VALID_CNPJ}/stats")
        assert resp.status_code == 200
        data = resp.json()
        mods = data["top_modalidades"]
        assert len(mods) == 3
        assert mods[0]["nome"] == "Pregão Eletrônico"
        assert mods[0]["count"] == 3
        assert mods[1]["nome"] == "Dispensa"
        assert mods[1]["count"] == 2
