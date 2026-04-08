"""Tests for GET /v1/sitemap/cnpjs endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear sitemap cache before each test."""
    from routes.sitemap_cnpjs import _sitemap_cache
    _sitemap_cache.clear()
    yield
    _sitemap_cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


def _mock_supabase_with_data(rows: list[dict]):
    """Build a mock get_supabase that returns given rows."""
    mock_sb = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = rows
    mock_sb.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.neq.return_value.limit.return_value.execute.return_value = mock_resp
    return mock_sb


class TestSitemapCnpjs:
    """Tests for /v1/sitemap/cnpjs."""

    @patch("supabase_client.get_supabase")
    def test_returns_cnpjs_with_min_bids(self, mock_get_sb, client):
        """Only CNPJs with ≥3 bids are returned."""
        rows = [
            {"orgao_cnpj": "11111111000100"},  # 1 bid
            {"orgao_cnpj": "22222222000200"},  # 3 bids
            {"orgao_cnpj": "22222222000200"},
            {"orgao_cnpj": "22222222000200"},
            {"orgao_cnpj": "33333333000300"},  # 5 bids
            {"orgao_cnpj": "33333333000300"},
            {"orgao_cnpj": "33333333000300"},
            {"orgao_cnpj": "33333333000300"},
            {"orgao_cnpj": "33333333000300"},
        ]
        mock_get_sb.return_value = _mock_supabase_with_data(rows)

        resp = client.get("/v1/sitemap/cnpjs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        # Sorted by count desc — 33... (5) before 22... (3)
        assert data["cnpjs"][0] == "33333333000300"
        assert data["cnpjs"][1] == "22222222000200"
        assert "11111111000100" not in data["cnpjs"]

    @patch("supabase_client.get_supabase")
    def test_empty_datalake(self, mock_get_sb, client):
        """Returns empty list when datalake has no data."""
        mock_get_sb.return_value = _mock_supabase_with_data([])

        resp = client.get("/v1/sitemap/cnpjs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cnpjs"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_filters_invalid_cnpjs(self, mock_get_sb, client):
        """Skips null, empty, and too-short CNPJ values."""
        rows = [
            {"orgao_cnpj": ""},
            {"orgao_cnpj": None},
            {"orgao_cnpj": "123"},  # too short
            {"orgao_cnpj": "44444444000400"},
            {"orgao_cnpj": "44444444000400"},
            {"orgao_cnpj": "44444444000400"},
        ]
        mock_get_sb.return_value = _mock_supabase_with_data(rows)

        resp = client.get("/v1/sitemap/cnpjs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["cnpjs"] == ["44444444000400"]

    @patch("supabase_client.get_supabase")
    def test_cache_serves_second_request(self, mock_get_sb, client):
        """Second request hits cache, not Supabase."""
        rows = [
            {"orgao_cnpj": "55555555000500"},
            {"orgao_cnpj": "55555555000500"},
            {"orgao_cnpj": "55555555000500"},
        ]
        mock_get_sb.return_value = _mock_supabase_with_data(rows)

        resp1 = client.get("/v1/sitemap/cnpjs")
        assert resp1.status_code == 200

        resp2 = client.get("/v1/sitemap/cnpjs")
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()

        # Supabase called only once (second request served from cache)
        assert mock_get_sb.call_count == 1

    @patch("supabase_client.get_supabase")
    def test_graceful_failure(self, mock_get_sb, client):
        """Returns empty response on Supabase error instead of 500."""
        mock_get_sb.side_effect = Exception("connection failed")

        resp = client.get("/v1/sitemap/cnpjs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cnpjs"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_response_schema(self, mock_get_sb, client):
        """Response has required fields with correct types."""
        rows = [{"orgao_cnpj": "66666666000600"}] * 4
        mock_get_sb.return_value = _mock_supabase_with_data(rows)

        resp = client.get("/v1/sitemap/cnpjs")
        data = resp.json()
        assert isinstance(data["cnpjs"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["updated_at"], str)

    @patch("supabase_client.get_supabase")
    def test_max_5000_cnpjs(self, mock_get_sb, client):
        """Respects _MAX_CNPJS limit."""
        # Generate 6000 unique CNPJs with 3 bids each
        rows = []
        for i in range(6000):
            cnpj = f"{i:014d}"
            rows.extend([{"orgao_cnpj": cnpj}] * 3)
        mock_get_sb.return_value = _mock_supabase_with_data(rows)

        resp = client.get("/v1/sitemap/cnpjs")
        data = resp.json()
        assert data["total"] <= 5000
