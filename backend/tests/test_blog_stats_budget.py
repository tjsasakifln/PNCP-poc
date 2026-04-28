"""Hotfix Stage 3 incident 2026-04-27: blog_stats budget + negative cache.

Stage 3 wedge: ``_compute_contratos_stats`` ran sync ``.execute()`` inside an
async handler. A 30s ``ilike`` on ``municipio`` blocked the only event loop
worker, ``/health/live`` (pure-async) also stalled, Railway proxy returned
502 to every probe.

Fix wraps the query in ``asyncio.to_thread`` + ``asyncio.wait_for(10s)`` and
caches the failure path under ``_NEGATIVE_CACHE_TTL_SECONDS`` (5min) instead
of the success TTL (6h) so the next Googlebot wave can probe again without a
day-long stale empty response.

These tests cover the two safety properties:
  1. Timeout/exception path returns the empty-shape fallback (200 OK, not 502)
     and caches it under the short TTL.
  2. Subsequent requests hit the in-memory cache and never re-query the DB.
"""

import asyncio
import time

import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_blog_cache():
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    yield
    _blog_cache.clear()


def _slow_sync_execute(*_args, **_kwargs):
    """Simulate the wedge: blocking call that exceeds the 10s budget."""
    time.sleep(15)
    raise AssertionError("budget should have fired before this returns")


class TestContratosBudget:
    def test_timeout_returns_fallback_and_caches_negative_ttl(self, client):
        """When the query exceeds _CONTRATOS_QUERY_BUDGET_S, handler must return
        the empty-shape fallback (200 OK) and store it under the negative TTL."""
        from routes import blog_stats as bs

        with patch.object(
            bs,
            "_query_contratos_sync",
            side_effect=_slow_sync_execute,
        ):
            # Patch budget down to keep test fast — fix still proves the
            # to_thread + wait_for wrapper short-circuits the slow path.
            with patch.object(bs, "_CONTRATOS_QUERY_BUDGET_S", 0.1):
                resp = client.get("/v1/blog/stats/contratos/informatica")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        # Empty-shape fallback, success-path keys present so Pydantic validates
        assert data["sector_id"] == "informatica"
        assert data["total_contracts"] == 0
        assert data["top_orgaos"] == []
        assert data["top_fornecedores"] == []

        # Cache stored under negative TTL (5min, not 6h)
        cache_key = "contratos_setor:informatica"
        assert cache_key in bs._blog_cache
        _data, _ts, ttl = bs._blog_cache[cache_key]
        assert ttl == bs._NEGATIVE_CACHE_TTL_SECONDS
        assert ttl < bs._CACHE_TTL_SECONDS

    def test_cache_hit_skips_db_query(self, client):
        """Pre-populated cache must be served without invoking the DB query."""
        from routes import blog_stats as bs

        cache_key = "contratos_setor:informatica"
        bs._cache_set(
            cache_key,
            {
                "sector_id": "informatica",
                "sector_name": "Informática",
                "total_contracts": 42,
                "total_value": 100000.0,
                "avg_value": 2380.95,
                "top_orgaos": [],
                "top_fornecedores": [],
                "monthly_trend": [],
                "by_uf": [],
                "last_updated": "2026-04-27T00:00:00+00:00",
                "n_unique_orgaos": 0,
                "n_unique_fornecedores": 0,
                "sample_contracts": [],
            },
            ttl=bs._CACHE_TTL_SECONDS,
        )

        with patch.object(bs, "_query_contratos_sync") as mock_query:
            resp = client.get("/v1/blog/stats/contratos/informatica")

        assert resp.status_code == 200
        assert resp.json()["total_contracts"] == 42
        # Critical: DB query MUST NOT have been called — cache served the response
        mock_query.assert_not_called()


class TestComputeContratosStatsAsync:
    """Direct unit tests on the async helper — independent of FastAPI routing."""

    def test_timeout_returns_partial_true(self):
        from routes import blog_stats as bs

        with patch.object(bs, "_query_contratos_sync", side_effect=_slow_sync_execute):
            with patch.object(bs, "_CONTRATOS_QUERY_BUDGET_S", 0.1):
                data, partial = asyncio.run(bs._compute_contratos_stats())

        assert partial is True
        assert data["total_contracts"] == 0
        assert data["sample_contracts"] == []

    def test_db_exception_returns_partial_true(self):
        from routes import blog_stats as bs

        with patch.object(
            bs,
            "_query_contratos_sync",
            side_effect=RuntimeError("supabase pool exhausted"),
        ):
            data, partial = asyncio.run(bs._compute_contratos_stats())

        assert partial is True
        assert data["total_contracts"] == 0

    def test_success_returns_partial_false(self):
        from routes import blog_stats as bs

        rows = [
            {
                "ni_fornecedor": "11111111000100",
                "nome_fornecedor": "TechCorp",
                "orgao_cnpj": "99999999000100",
                "orgao_nome": "Min Educacao",
                "valor_global": 100000.0,
                "data_assinatura": "2026-03-20",
                "objeto_contrato": "fornecimento de computadores",
                "uf": "SP",
            },
        ]
        with patch.object(bs, "_query_contratos_sync", return_value=rows):
            data, partial = asyncio.run(bs._compute_contratos_stats())

        assert partial is False
        # Aggregation produced something
        assert "top_orgaos" in data
