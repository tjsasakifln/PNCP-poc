"""Tests for SEO Onda 2: /v1/sitemap/orgaos endpoint."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_cache():
    """Clear sitemap_orgaos cache between tests."""
    from routes.sitemap_orgaos import _sitemap_cache
    _sitemap_cache.clear()
    yield
    _sitemap_cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


def _mock_supabase_response(data: list[dict]):
    """Legacy table-query mock (kept for other tests in this file that
    coincidentally pass because the RPC primary path returns a MagicMock,
    fails the `isinstance(..., list)` check, and emits an empty orgao_list).
    New/fixed tests should prefer `_mock_rpc_response`.
    """
    mock_sb = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = data
    mock_sb.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.neq.return_value.limit.return_value.execute.return_value = mock_resp
    return mock_sb


def _mock_rpc_response(cnpjs: list[str]):
    """Mock sb.rpc('get_sitemap_orgaos_json', ...).execute() returning a list
    of CNPJ strings (the RPC `RETURNS json` scalar already does server-side
    GROUP BY + length≥11 + is_active + not-null filtering; see migration
    20260408200000_sitemap_rpc_json.sql).
    """
    mock_sb = MagicMock()
    mock_resp = MagicMock()
    mock_resp.data = cnpjs
    mock_sb.rpc.return_value.execute.return_value = mock_resp
    return mock_sb


class TestSitemapOrgaos:
    """Tests for GET /v1/sitemap/orgaos."""

    @patch("supabase_client.get_supabase")
    def test_returns_orgaos_with_min_5_bids(self, mock_get_sb, client):
        """Órgãos filtered + ordered by bid_count server-side.

        BTS-011 cluster 5: the ≥5-bid filter + aggregation live in the
        `get_sitemap_orgaos_json` RPC (SQL GROUP BY … HAVING-like semantics
        via ORDER BY bid_count DESC + LIMIT). Python route just receives the
        final list. Mocking the RPC directly matches the primary code path
        (`sb.rpc(...).execute()` in `routes/sitemap_orgaos.py::_fetch_top_orgaos`).
        """
        # RPC already applied server-side filtering (≥5 bids, length≥11, not-null)
        # Return sorted by bid_count desc: 33... (10 bids), 11... (5 bids)
        mock_get_sb.return_value = _mock_rpc_response(["33333333000300", "11111111000100"])

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert "33333333000300" in data["orgaos"]  # 10 bids
        assert "11111111000100" in data["orgaos"]  # 5 bids
        assert "22222222000200" not in data["orgaos"]  # 4 bids (excluded by RPC)
        assert data["total"] == 2

    @patch("supabase_client.get_supabase")
    def test_empty_datalake(self, mock_get_sb, client):
        """Empty datalake returns empty list, not error."""
        mock_get_sb.return_value = _mock_supabase_response([])

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgaos"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_filters_invalid_cnpjs(self, mock_get_sb, client):
        """Null, empty, and short CNPJs are filtered out server-side.

        BTS-011 cluster 5: invalid-CNPJ filtering (`length >= 11`, not null,
        not empty) lives in the RPC SQL. The Python layer also guards with
        `isinstance(c, str) and len(c) >= 11` to short-circuit malformed
        payloads before they hit the response model. Mock the RPC to return
        only the valid entry (what the SQL would have emitted).
        """
        mock_get_sb.return_value = _mock_rpc_response(["44444444000400"])

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgaos"] == ["44444444000400"]
        assert data["total"] == 1

    @patch("supabase_client.get_supabase")
    def test_cache_serves_second_request(self, mock_get_sb, client):
        """Second request should be served from cache (no DB call)."""
        rows = [{"orgao_cnpj": "55555555000500"}] * 8
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp1 = client.get("/v1/sitemap/orgaos")
        assert resp1.status_code == 200

        # Reset mock — second call should NOT hit DB
        mock_get_sb.reset_mock()
        resp2 = client.get("/v1/sitemap/orgaos")
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()
        mock_get_sb.assert_not_called()

    @patch("supabase_client.get_supabase")
    def test_graceful_failure(self, mock_get_sb, client):
        """Supabase error returns empty list, not 500."""
        mock_get_sb.side_effect = Exception("Connection refused")

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert data["orgaos"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_response_schema(self, mock_get_sb, client):
        """Response must have orgaos, total, updated_at fields."""
        rows = [{"orgao_cnpj": "66666666000600"}] * 7
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["orgaos"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["updated_at"], str)

    @patch("supabase_client.get_supabase")
    def test_max_2000_orgaos(self, mock_get_sb, client):
        """Should return at most 2000 órgãos."""
        # Create 2500 distinct CNPJs each with 5 bids
        rows = []
        for i in range(2500):
            cnpj = f"{i:014d}"
            rows.extend([{"orgao_cnpj": cnpj}] * 5)
        mock_get_sb.return_value = _mock_supabase_response(rows)

        resp = client.get("/v1/sitemap/orgaos")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["orgaos"]) <= 2000
        assert data["total"] <= 2000
