"""Tests for STORY-SEO-017: /v1/sitemap/licitacoes-do-dia-indexable endpoint."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_cache():
    from routes.sitemap_licitacoes_do_dia import _cache
    _cache.clear()
    yield
    _cache.clear()


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


def _mock_supabase_paginated(rows: list[dict]):
    """Mock paginated select(data_publicacao) — first call returns rows, second empty."""
    mock_sb = MagicMock()

    def _make_resp(data):
        r = MagicMock()
        r.data = data
        return r

    # Build chain: sb.table().select().eq().gte().not_.is_().range().execute()
    # 1st page returns all rows; subsequent pages return empty (loop break)
    pages = [rows, []]
    page_iter = iter(pages)

    def _execute_side_effect(*args, **kwargs):
        try:
            return _make_resp(next(page_iter))
        except StopIteration:
            return _make_resp([])

    chain = (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .gte.return_value
        .not_.is_.return_value
        .range.return_value
    )
    chain.execute.side_effect = _execute_side_effect
    return mock_sb


class TestSitemapLicitacoesDoDiaIndexable:
    @patch("supabase_client.get_supabase")
    def test_filters_dates_below_5_bids(self, mock_get_sb, client):
        """Datas com <5 bids filtradas; somente >=5 retornadas."""
        rows = (
            [{"data_publicacao": "2026-04-23T10:00:00"}] * 7
            + [{"data_publicacao": "2026-04-22T10:00:00"}] * 4
            + [{"data_publicacao": "2026-04-21T10:00:00"}] * 5
        )
        mock_get_sb.return_value = _mock_supabase_paginated(rows)

        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        assert resp.status_code == 200
        data = resp.json()
        assert "2026-04-23" in data["dates"]  # 7 bids
        assert "2026-04-21" in data["dates"]  # 5 bids (boundary)
        assert "2026-04-22" not in data["dates"]  # 4 bids (excluded)

    @patch("supabase_client.get_supabase")
    def test_dates_sorted_desc(self, mock_get_sb, client):
        rows = (
            [{"data_publicacao": "2026-04-15"}] * 6
            + [{"data_publicacao": "2026-04-23"}] * 6
            + [{"data_publicacao": "2026-04-19"}] * 6
        )
        mock_get_sb.return_value = _mock_supabase_paginated(rows)

        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        data = resp.json()
        assert data["dates"] == ["2026-04-23", "2026-04-19", "2026-04-15"]

    @patch("supabase_client.get_supabase")
    def test_empty_datalake(self, mock_get_sb, client):
        mock_get_sb.return_value = _mock_supabase_paginated([])

        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dates"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_graceful_failure(self, mock_get_sb, client):
        mock_get_sb.side_effect = Exception("Supabase down")

        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["dates"] == []
        assert data["total"] == 0

    @patch("supabase_client.get_supabase")
    def test_response_schema(self, mock_get_sb, client):
        mock_get_sb.return_value = _mock_supabase_paginated(
            [{"data_publicacao": "2026-04-20"}] * 5
        )
        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        data = resp.json()
        assert isinstance(data["dates"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["updated_at"], str)

    @patch("supabase_client.get_supabase")
    def test_cache_serves_second_request(self, mock_get_sb, client):
        rows = [{"data_publicacao": "2026-04-22"}] * 6
        mock_get_sb.return_value = _mock_supabase_paginated(rows)

        resp1 = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        assert resp1.status_code == 200

        mock_get_sb.reset_mock()
        resp2 = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        assert resp2.status_code == 200
        assert resp2.json() == resp1.json()
        mock_get_sb.assert_not_called()

    @patch("supabase_client.get_supabase")
    def test_skips_invalid_dates(self, mock_get_sb, client):
        """Datas malformadas ou null sao ignoradas."""
        rows = (
            [{"data_publicacao": "2026-04-22"}] * 5
            + [{"data_publicacao": None}] * 3
            + [{"data_publicacao": "invalid"}] * 3
            + [{"data_publicacao": ""}] * 3
        )
        mock_get_sb.return_value = _mock_supabase_paginated(rows)

        resp = client.get("/v1/sitemap/licitacoes-do-dia-indexable")
        data = resp.json()
        assert data["dates"] == ["2026-04-22"]
