"""Tests for MKT-002 AC1: Blog stats API endpoints.

Tests all 4 public endpoints:
- GET /v1/blog/stats/setor/{setor_id}
- GET /v1/blog/stats/setor/{setor_id}/uf/{uf}
- GET /v1/blog/stats/cidade/{cidade}
- GET /v1/blog/stats/panorama/{setor_id}
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@pytest.fixture(autouse=True)
def _clear_blog_cache():
    """Clear blog stats cache between tests."""
    from routes.blog_stats import _blog_cache
    _blog_cache.clear()
    yield
    _blog_cache.clear()


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


# Sample PNCP results for mocking
MOCK_PNCP_RESULTS = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoPncp": "2026-02-28",
        "orgaoEntidade": {
            "razaoSocial": "Secretaria de Segurança Pública",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoPncp": "2026-02-27",
        "orgaoEntidade": {
            "razaoSocial": "Polícia Militar do Estado de SP",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Roupas profissionais para servidores",
        "uf": "RJ",
        "valorTotalEstimado": 80000.0,
        "codigoModalidadeContratacao": 7,
        "dataPublicacaoPncp": "2026-02-26",
        "orgaoEntidade": {
            "razaoSocial": "Prefeitura Municipal do Rio",
            "municipioNome": "Rio de Janeiro",
        },
    },
]


@dataclass
class MockParallelFetchResult:
    """Mock for pncp_client.ParallelFetchResult."""
    items: List[Dict[str, Any]] = field(default_factory=list)
    succeeded_ufs: List[str] = field(default_factory=list)
    failed_ufs: List[str] = field(default_factory=list)
    truncated_ufs: List[str] = field(default_factory=list)
    canary_result: Optional[Dict[str, Any]] = None


def _make_async_pncp_mock(buscar_return=None, buscar_side_effect=None):
    """Create a mock AsyncPNCPClient usable as async context manager.

    Args:
        buscar_return: Static return value for buscar_todas_ufs_paralelo
        buscar_side_effect: Side effect function for buscar_todas_ufs_paralelo
    """
    mock_client = MagicMock()

    if buscar_side_effect:
        mock_client.buscar_todas_ufs_paralelo = AsyncMock(side_effect=buscar_side_effect)
    elif buscar_return is not None:
        mock_client.buscar_todas_ufs_paralelo = AsyncMock(return_value=buscar_return)
    else:
        mock_client.buscar_todas_ufs_paralelo = AsyncMock(
            return_value=MockParallelFetchResult(items=[])
        )

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_cls, mock_client


def _mock_pncp_buscar(**kwargs):
    """Return all mock results wrapped in ParallelFetchResult."""
    return MockParallelFetchResult(
        items=MOCK_PNCP_RESULTS,
        succeeded_ufs=["SP", "RJ"],
    )


def _mock_pncp_buscar_empty(**kwargs):
    return MockParallelFetchResult(items=[])


# ---------------------------------------------------------------------------
# Endpoint 1: GET /v1/blog/stats/setor/{setor_id}
# ---------------------------------------------------------------------------

class TestSectorBlogStats:
    def test_sector_stats_success(self, client):
        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: _mock_pncp_buscar(**kw)
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["sector_name"] == "Vestuário e Uniformes"
            assert data["total_editais"] >= 0
            assert "top_modalidades" in data
            assert "top_ufs" in data
            assert "trend_90d" in data
            assert "last_updated" in data
            assert data["value_range_min"] >= 0
            assert data["value_range_max"] >= 0
            assert data["avg_value"] >= 0

    def test_sector_stats_cached(self, client):
        """Second call should hit cache (no PNCP query)."""
        mock_cls, mock_client = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: _mock_pncp_buscar_empty(**kw)
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res1 = client.get("/v1/blog/stats/setor/vestuario")
            assert res1.status_code == 200

            res2 = client.get("/v1/blog/stats/setor/vestuario")
            assert res2.status_code == 200
            assert res2.json() == res1.json()

            # AsyncPNCPClient should only be instantiated once
            assert mock_cls.call_count == 1

    def test_sector_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/setor/nonexistent")
        assert res.status_code == 404

    def test_sector_stats_slug_format(self, client):
        """Accept slug with hyphens (e.g., manutencao-predial)."""
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/manutencao-predial")
            assert res.status_code == 200
            assert res.json()["sector_id"] == "manutencao_predial"

    def test_sector_stats_no_auth_required(self, client):
        """Endpoint should be public (no auth header needed)."""
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/alimentos")
            assert res.status_code == 200

    def test_sector_stats_trend_structure(self, client):
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/informatica")
            data = res.json()
            assert len(data["trend_90d"]) == 3
            for point in data["trend_90d"]:
                assert "period" in point
                assert "count" in point
                assert "avg_value" in point


# ---------------------------------------------------------------------------
# Endpoint 2: GET /v1/blog/stats/setor/{setor_id}/uf/{uf}
# ---------------------------------------------------------------------------

class TestSectorUfStats:
    def test_sector_uf_stats_success(self, client):
        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: _mock_pncp_buscar(**kw)
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["uf"] == "SP"
            assert data["total_editais"] >= 0
            assert data["avg_value"] >= 0
            assert "top_oportunidades" in data

    def test_sector_uf_stats_lowercase(self, client):
        """Accept lowercase UF."""
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/sp")
            assert res.status_code == 200
            assert res.json()["uf"] == "SP"

    def test_sector_uf_stats_invalid_uf(self, client):
        res = client.get("/v1/blog/stats/setor/vestuario/uf/XX")
        assert res.status_code == 404

    def test_sector_uf_stats_invalid_sector(self, client):
        res = client.get("/v1/blog/stats/setor/nonexistent/uf/SP")
        assert res.status_code == 404

    def test_sector_uf_top_oportunidades(self, client):
        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: _mock_pncp_buscar(**kw)
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            data = res.json()
            for item in data["top_oportunidades"]:
                assert "titulo" in item
                assert "orgao" in item
                assert "uf" in item
                assert "data" in item


# ---------------------------------------------------------------------------
# Endpoint 3: GET /v1/blog/stats/cidade/{cidade}
# ---------------------------------------------------------------------------

class TestCidadeStats:
    def test_cidade_stats_success(self, client):
        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: MockParallelFetchResult(
                items=MOCK_PNCP_RESULTS[:2], succeeded_ufs=["SP"]
            )
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/cidade/são-paulo")
            assert res.status_code == 200

            data = res.json()
            assert data["cidade"] == "São Paulo"
            assert data["uf"] == "SP"
            assert "orgaos_frequentes" in data
            assert data["avg_value"] >= 0

    def test_cidade_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/cidade/atlantida")
        assert res.status_code == 404

    def test_cidade_stats_cached(self, client):
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res1 = client.get("/v1/blog/stats/cidade/curitiba")
            res2 = client.get("/v1/blog/stats/cidade/curitiba")
            assert res1.status_code == 200
            assert res2.json() == res1.json()
            assert mock_cls.call_count == 1


# ---------------------------------------------------------------------------
# Endpoint 4: GET /v1/blog/stats/panorama/{setor_id}
# ---------------------------------------------------------------------------

class TestPanoramaStats:
    def test_panorama_stats_success(self, client):
        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: _mock_pncp_buscar(**kw)
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/panorama/vestuario")
            assert res.status_code == 200

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["sector_name"] == "Vestuário e Uniformes"
            assert data["total_nacional"] >= 0
            assert data["total_value"] >= 0
            assert data["crescimento_estimado_pct"] > 0
            assert "sazonalidade" in data
            assert len(data["sazonalidade"]) == 12

    def test_panorama_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/panorama/nonexistent")
        assert res.status_code == 404

    def test_panorama_stats_sazonalidade_structure(self, client):
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/panorama/software")
            data = res.json()
            for month in data["sazonalidade"]:
                assert "period" in month
                assert "count" in month
                assert "avg_value" in month

    def test_panorama_stats_no_auth(self, client):
        """Public endpoint — no auth required."""
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/panorama/saude")
            assert res.status_code == 200


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

class TestCacheInvalidation:
    def test_invalidate_blog_cache(self, client):
        from routes.blog_stats import invalidate_blog_cache, _blog_cache

        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            client.get("/v1/blog/stats/setor/vestuario")
            assert len(_blog_cache) > 0

            invalidate_blog_cache()
            assert len(_blog_cache) == 0


# ---------------------------------------------------------------------------
# MKT-003: Enhanced SectorUfStats fields
# ---------------------------------------------------------------------------

# Richer mock data for MKT-003 tests — two items with distinct modalities/values
MOCK_PNCP_UF_SP = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,  # Pregão Eletrônico
        "dataPublicacaoPncp": "2026-02-28",
        "orgaoEntidade": {
            "razaoSocial": "Secretaria de Segurança Pública",
            "municipioNome": "São Paulo",
        },
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão de uniformes",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 7,  # Dispensa de Licitação
        "dataPublicacaoPncp": "2026-02-27",
        "orgaoEntidade": {
            "razaoSocial": "Polícia Militar do Estado de SP",
            "municipioNome": "São Paulo",
        },
    },
]


def _mock_sp_fetch(**kwargs):
    """Return SP items wrapped in ParallelFetchResult."""
    return MockParallelFetchResult(items=MOCK_PNCP_UF_SP, succeeded_ufs=["SP"])


class TestSectorUfStatsEnhanced:
    """MKT-003: Tests for enhanced SectorUfStats fields."""

    def test_sector_uf_stats_enhanced_fields(self, client):
        """Response includes value_range_min, value_range_max, top_modalidades, trend_90d with correct types."""
        mock_cls, _ = _make_async_pncp_mock(buscar_side_effect=lambda **kw: _mock_sp_fetch(**kw))
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()

            # Field presence
            assert "value_range_min" in data
            assert "value_range_max" in data
            assert "top_modalidades" in data
            assert "trend_90d" in data

            # Type checks
            assert isinstance(data["value_range_min"], (int, float))
            assert isinstance(data["value_range_max"], (int, float))
            assert isinstance(data["top_modalidades"], list)
            assert isinstance(data["trend_90d"], list)

    def test_sector_uf_stats_value_range(self, client):
        """With 2 items of different values, min < max (or equal if 1 item)."""
        mock_cls, _ = _make_async_pncp_mock(buscar_side_effect=lambda **kw: _mock_sp_fetch(**kw))
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            # Two SP items: 150_000 and 250_000
            assert data["value_range_min"] <= data["value_range_max"]
            # Specifically, min should be 150_000 and max should be 250_000
            assert data["value_range_min"] == 150000.0
            assert data["value_range_max"] == 250000.0

    def test_sector_uf_stats_value_range_single_item(self, client):
        """With exactly 1 valued item, min == max."""
        single_item = [MOCK_PNCP_UF_SP[0].copy()]  # only 150_000 item

        mock_cls, _ = _make_async_pncp_mock(
            buscar_side_effect=lambda **kw: MockParallelFetchResult(items=single_item, succeeded_ufs=["SP"])
        )
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            assert data["value_range_min"] == data["value_range_max"]
            assert data["value_range_min"] == 150000.0

    def test_sector_uf_stats_modalities(self, client):
        """top_modalidades has entries with name (str) and count (int) structure."""
        mock_cls, _ = _make_async_pncp_mock(buscar_side_effect=lambda **kw: _mock_sp_fetch(**kw))
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            top_mods = data["top_modalidades"]
            assert len(top_mods) >= 1

            for entry in top_mods:
                assert "name" in entry
                assert "count" in entry
                assert isinstance(entry["name"], str)
                assert isinstance(entry["count"], int)
                assert entry["count"] >= 1

            # Both mock items have distinct modalities (1 and 7), so 2 entries expected
            assert len(top_mods) == 2
            names = {e["name"] for e in top_mods}
            assert "Pregão Eletrônico" in names
            assert "Dispensa de Licitação" in names

    def test_sector_uf_stats_trend(self, client):
        """trend_90d has exactly 3 entries, each with period, count, avg_value."""
        mock_cls, _ = _make_async_pncp_mock(buscar_side_effect=lambda **kw: _mock_sp_fetch(**kw))
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            trend = data["trend_90d"]
            assert len(trend) == 3

            for point in trend:
                assert "period" in point
                assert "count" in point
                assert "avg_value" in point
                assert isinstance(point["period"], str)
                assert isinstance(point["count"], int)
                assert isinstance(point["avg_value"], (int, float))
                # Counts are positive (at least 1 due to max(1, ...) guard)
                assert point["count"] >= 1

            # Periods should be in ascending order (oldest to most recent)
            periods = [p["period"] for p in trend]
            assert periods == sorted(periods)

    def test_sector_uf_stats_empty_results(self, client):
        """When PNCP returns no results: value_range_min=0, top_modalidades=[], trend counts >= 1."""
        mock_cls, _ = _make_async_pncp_mock()
        with patch("pncp_client.AsyncPNCPClient", mock_cls):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()

            assert data["value_range_min"] == 0.0
            assert data["value_range_max"] == 0.0
            assert data["top_modalidades"] == []

            # trend_90d still has 3 entries (count >= 1 by _estimate_trend guard)
            trend = data["trend_90d"]
            assert len(trend) == 3
            for point in trend:
                assert point["count"] >= 1
                assert point["avg_value"] == 0.0


# ---------------------------------------------------------------------------
# Contratos endpoints (pncp_supplier_contracts fallback for zero-editais pages)
# ---------------------------------------------------------------------------

# Sample rows from pncp_supplier_contracts (uniform/vestuario sector keywords)
MOCK_CONTRACT_ROWS = [
    {
        "ni_fornecedor": "12345678000101",
        "nome_fornecedor": "Uniformes Brasil LTDA",
        "orgao_cnpj": "00000000000111",
        "orgao_nome": "Secretaria de Segurança Pública SP",
        "valor_global": 180000.00,
        "data_assinatura": "2026-01-15",
        "objeto_contrato": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "municipio": "São Paulo",
    },
    {
        "ni_fornecedor": "98765432000199",
        "nome_fornecedor": "Fardamentos Militares S.A.",
        "orgao_cnpj": "00000000000222",
        "orgao_nome": "Polícia Militar SP",
        "valor_global": 320000.00,
        "data_assinatura": "2026-02-03",
        "objeto_contrato": "Fardamentos militares para batalhão de choque",
        "uf": "SP",
        "municipio": "São Paulo",
    },
    {
        "ni_fornecedor": "12345678000101",
        "nome_fornecedor": "Uniformes Brasil LTDA",
        "orgao_cnpj": "00000000000333",
        "orgao_nome": "Prefeitura de Campinas",
        "valor_global": 95000.00,
        "data_assinatura": "2026-02-20",
        "objeto_contrato": "Uniformes escolares para rede municipal",
        "uf": "SP",
        "municipio": "Campinas",
    },
    {
        "ni_fornecedor": "55555555000155",
        "nome_fornecedor": "Confecções do Norte",
        "orgao_cnpj": "00000000000444",
        "orgao_nome": "Prefeitura de Manaus",
        "valor_global": 60000.00,
        "data_assinatura": "2026-01-08",
        "objeto_contrato": "Aquisição de uniformes para agentes de saúde",
        "uf": "AM",
        "municipio": "Manaus",
    },
    # Non-matching row (should be filtered out by sector keywords)
    {
        "ni_fornecedor": "99999999000199",
        "nome_fornecedor": "Papelaria Central",
        "orgao_cnpj": "00000000000555",
        "orgao_nome": "Secretaria de Educação SP",
        "valor_global": 25000.00,
        "data_assinatura": "2026-02-18",
        "objeto_contrato": "Aquisição de material de escritório e papelaria",
        "uf": "SP",
        "municipio": "São Paulo",
    },
]


class _ContractsQueryBuilder:
    """Chainable mock that mirrors supabase-py query builder for pncp_supplier_contracts.

    Captures invoked filter kwargs so tests can assert UF/municipio were applied.
    """
    def __init__(self, rows):
        self._rows = rows
        self.filters = {}

    def select(self, *_a, **_kw):
        return self

    def eq(self, key, value):
        self.filters[f"eq:{key}"] = value
        return self

    def ilike(self, key, pattern):
        self.filters[f"ilike:{key}"] = pattern
        return self

    def order(self, *_a, **_kw):
        return self

    def limit(self, *_a, **_kw):
        return self

    def execute(self):
        rows = list(self._rows)
        uf = self.filters.get("eq:uf")
        if uf is not None:
            rows = [r for r in rows if (r.get("uf") or "") == uf]
        municipio_ilike = self.filters.get("ilike:municipio")
        if municipio_ilike is not None:
            # strip the surrounding %…% wildcards, case-insensitive substring
            needle = municipio_ilike.strip("%").lower()
            rows = [r for r in rows if needle in (r.get("municipio") or "").lower()]
        resp = MagicMock()
        resp.data = rows
        return resp


def _make_contracts_supabase_mock(rows=None):
    """Return (mock_supabase, builder_ref) — builder_ref holds the last builder created."""
    rows = rows if rows is not None else MOCK_CONTRACT_ROWS
    builder_ref = {}

    def _table(name):
        assert name == "pncp_supplier_contracts", f"Unexpected table: {name}"
        builder = _ContractsQueryBuilder(rows)
        builder_ref["last"] = builder
        return builder

    mock_sb = MagicMock()
    mock_sb.table.side_effect = _table
    return mock_sb, builder_ref


class TestContratosSetorUfStats:
    """GET /v1/blog/stats/contratos/{setor_id}/uf/{uf}"""

    def test_sector_uf_contratos_success(self, client):
        mock_sb, builder_ref = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            assert res.status_code == 200

            # UF filter was applied at query level
            assert builder_ref["last"].filters.get("eq:uf") == "SP"
            assert builder_ref["last"].filters.get("eq:is_active") is True

            data = res.json()
            assert data["sector_id"] == "vestuario"
            assert data["sector_name"] == "Vestuário e Uniformes"
            assert data["uf"] == "SP"
            # 3 of 4 SP rows match sector keywords (uniformes/fardamentos), papelaria excluded
            assert data["total_contracts"] == 3
            assert data["total_value"] == round(180000.0 + 320000.0 + 95000.0, 2)
            assert data["avg_value"] > 0
            assert len(data["top_orgaos"]) >= 1
            assert len(data["top_fornecedores"]) >= 1
            assert len(data["monthly_trend"]) == 12
            # ContratosSetorUfStats doesn't include by_uf (single-UF scope)
            assert "by_uf" not in data

    def test_sector_uf_contratos_invalid_uf(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/XX")
            assert res.status_code == 404

    def test_sector_uf_contratos_invalid_sector(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/nonexistent/uf/SP")
            assert res.status_code == 404

    def test_sector_uf_contratos_cached(self, client):
        """Second call hits the cache — supabase should not be called twice."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb) as mock_fn:
            res1 = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            res2 = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            assert res1.status_code == 200
            assert res2.status_code == 200
            assert res1.json() == res2.json()
            assert mock_fn.call_count == 1

    def test_sector_uf_contratos_cache_key_distinct_per_uf(self, client):
        """Different UFs must use different cache keys (no cross-contamination)."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res_sp = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            res_am = client.get("/v1/blog/stats/contratos/vestuario/uf/AM")
            assert res_sp.status_code == 200
            assert res_am.status_code == 200
            assert res_sp.json()["total_contracts"] == 3  # SP matches
            assert res_am.json()["total_contracts"] == 1  # AM has 1 matching row

    def test_sector_uf_contratos_zero_matches(self, client):
        """Sector with no keyword matches returns zero but still 200."""
        mock_sb, _ = _make_contracts_supabase_mock(rows=[MOCK_CONTRACT_ROWS[4]])  # papelaria only
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            assert res.status_code == 200
            data = res.json()
            assert data["total_contracts"] == 0
            assert data["total_value"] == 0.0
            assert data["avg_value"] == 0.0
            assert data["top_orgaos"] == []
            assert data["top_fornecedores"] == []

    def test_sector_uf_contratos_db_failure_502(self, client):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = RuntimeError("connection refused")
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            assert res.status_code == 502


class TestContratosCidadeStats:
    """GET /v1/blog/stats/contratos/cidade/{cidade}"""

    def test_cidade_contratos_success(self, client):
        mock_sb, builder_ref = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/sao-paulo")
            assert res.status_code == 200

            # UF resolved + municipio ilike applied
            assert builder_ref["last"].filters.get("eq:uf") == "SP"
            assert builder_ref["last"].filters.get("ilike:municipio", "").startswith("%")

            data = res.json()
            assert data["cidade"] == "São Paulo"  # accented official name from _CITY_DISPLAY
            assert data["uf"] == "SP"
            # All São Paulo rows included (no sector filter): 3 rows match (uniforms + fardamentos + papelaria)
            # Campinas is filtered out by ilike
            assert data["total_contracts"] == 3
            assert "top_orgaos" in data
            assert "monthly_trend" in data
            assert len(data["monthly_trend"]) == 12

    def test_cidade_contratos_invalid_city(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/nonexistent-city")
            assert res.status_code == 404

    def test_cidade_contratos_db_failure_502(self, client):
        mock_sb = MagicMock()
        mock_sb.table.side_effect = RuntimeError("db down")
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/sao-paulo")
            assert res.status_code == 502


class TestContratosCidadeSetorStats:
    """GET /v1/blog/stats/contratos/cidade/{cidade}/setor/{setor_id}"""

    def test_cidade_setor_contratos_success(self, client):
        mock_sb, builder_ref = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/sao-paulo/setor/vestuario")
            assert res.status_code == 200

            # All 3 filters present: is_active + uf + municipio ilike
            filt = builder_ref["last"].filters
            assert filt.get("eq:is_active") is True
            assert filt.get("eq:uf") == "SP"
            assert "ilike:municipio" in filt

            data = res.json()
            assert data["cidade"] == "São Paulo"
            assert data["uf"] == "SP"
            assert data["sector_id"] == "vestuario"
            # Only uniforms/fardamentos rows that are in São Paulo (not Campinas) — 2 rows
            assert data["total_contracts"] == 2

    def test_cidade_setor_contratos_invalid_sector(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/sao-paulo/setor/nonexistent")
            assert res.status_code == 404

    def test_cidade_setor_contratos_invalid_city(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/nonexistent/setor/vestuario")
            assert res.status_code == 404

    def test_cidade_setor_contratos_cache_key_distinct(self, client):
        """Different city+sector combinations must not cross-contaminate cache."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res1 = client.get("/v1/blog/stats/contratos/cidade/sao-paulo/setor/vestuario")
            res2 = client.get("/v1/blog/stats/contratos/cidade/campinas/setor/vestuario")
            assert res1.status_code == 200
            assert res2.status_code == 200
            # SP: 2 São Paulo rows, Campinas: 1 (uniformes escolares)
            assert res1.json()["total_contracts"] == 2
            assert res2.json()["total_contracts"] == 1
