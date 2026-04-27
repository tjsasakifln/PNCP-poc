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


# Sample datalake-format results for mocking (flat fields, compatible with helpers)
MOCK_PNCP_RESULTS = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoFormatted": "2026-02-28",
        "nomeOrgao": "Secretaria de Segurança Pública",
        "municipio": "São Paulo",
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 1,
        "dataPublicacaoFormatted": "2026-02-27",
        "nomeOrgao": "Polícia Militar do Estado de SP",
        "municipio": "São Paulo",
    },
    {
        "objetoCompra": "Roupas profissionais para servidores",
        "uf": "RJ",
        "valorTotalEstimado": 80000.0,
        "codigoModalidadeContratacao": 7,
        "dataPublicacaoFormatted": "2026-02-26",
        "nomeOrgao": "Prefeitura Municipal do Rio",
        "municipio": "Rio de Janeiro",
    },
]


def _mock_dl(results=None):
    """Return AsyncMock for datalake_query.query_datalake."""
    return AsyncMock(return_value=results if results is not None else [])


# ---------------------------------------------------------------------------
# Endpoint 1: GET /v1/blog/stats/setor/{setor_id}
# ---------------------------------------------------------------------------

class TestSectorBlogStats:
    def test_sector_stats_success(self, client):
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_RESULTS)):
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
        """Second call should hit cache (no datalake query)."""
        mock_dl = _mock_dl()
        with patch("datalake_query.query_datalake", mock_dl):
            res1 = client.get("/v1/blog/stats/setor/vestuario")
            assert res1.status_code == 200

            res2 = client.get("/v1/blog/stats/setor/vestuario")
            assert res2.status_code == 200
            assert res2.json() == res1.json()

            # query_datalake should only be called once (cache hit on second call)
            assert mock_dl.call_count == 1

    def test_sector_stats_not_found(self, client):
        res = client.get("/v1/blog/stats/setor/nonexistent")
        assert res.status_code == 404

    def test_sector_stats_slug_format(self, client):
        """Accept slug with hyphens (e.g., manutencao-predial)."""
        with patch("datalake_query.query_datalake", _mock_dl()):
            res = client.get("/v1/blog/stats/setor/manutencao-predial")
            assert res.status_code == 200
            assert res.json()["sector_id"] == "manutencao_predial"

    def test_sector_stats_no_auth_required(self, client):
        """Endpoint should be public (no auth header needed)."""
        with patch("datalake_query.query_datalake", _mock_dl()):
            res = client.get("/v1/blog/stats/setor/alimentos")
            assert res.status_code == 200

    def test_sector_stats_trend_structure(self, client):
        with patch("datalake_query.query_datalake", _mock_dl()):
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
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_RESULTS)):
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
        with patch("datalake_query.query_datalake", _mock_dl()):
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
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_RESULTS)):
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
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_RESULTS[:2])):
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
        mock_dl = _mock_dl()
        with patch("datalake_query.query_datalake", mock_dl):
            res1 = client.get("/v1/blog/stats/cidade/curitiba")
            res2 = client.get("/v1/blog/stats/cidade/curitiba")
            assert res1.status_code == 200
            assert res2.json() == res1.json()
            assert mock_dl.call_count == 1

    def test_cidade_stats_accent_insensitive_match(self, client):
        """CRIT-SEO-011: slug 'sao-paulo' DEVE bater com item_city 'São Paulo' (acento).

        Regressão histórica: antes do fix, get_cidade_stats usava apenas .lower()
        sem _strip_accents(), causando `"sao paulo" in "são paulo"` = False e
        retornando total_editais=0 para TODAS as cidades com acento no nome
        (São Paulo, São Luís, Brasília, Goiânia, etc — ~70% das cidades BR).
        """
        # Fabricar resultado DataLake onde item_city TEM acento (como PNCP armazena)
        items_with_accent = [
            {
                "numeroControlePNCP": "TEST-001",
                "orgaoEntidade": {"municipioNome": "São Paulo", "ufSigla": "SP"},
                "valorTotalEstimado": 100000.0,
                "objetoCompra": "Teste de normalização de acento",
                "dataPublicacaoPncp": "2026-04-20",
            },
            {
                "numeroControlePNCP": "TEST-002",
                "orgaoEntidade": {"municipioNome": "São Paulo", "ufSigla": "SP"},
                "valorTotalEstimado": 50000.0,
                "objetoCompra": "Segundo teste",
                "dataPublicacaoPncp": "2026-04-20",
            },
        ]
        with patch("datalake_query.query_datalake", _mock_dl(items_with_accent)):
            # Slug sem acento (como vem do frontend)
            res = client.get("/v1/blog/stats/cidade/sao-paulo")
            assert res.status_code == 200
            data = res.json()
            # Antes do fix: total_editais=0. Após fix: 2 (ambos items batem via ASCII)
            assert data["total_editais"] == 2, (
                f"Esperado 2 editais (ambos itens têm 'São Paulo' com acento); "
                f"recebido {data['total_editais']}. Bug CRIT-SEO-011 voltou?"
            )
            assert data["avg_value"] == 75000.0  # (100k + 50k) / 2

    def test_cidade_stats_brasilia_accent_fix(self, client):
        """CRIT-SEO-011: Brasília (com acento) — outra cidade afetada pelo bug."""
        items = [
            {
                "numeroControlePNCP": "TEST-BSB-001",
                "orgaoEntidade": {"municipioNome": "Brasília", "ufSigla": "DF"},
                "valorTotalEstimado": 200000.0,
                "objetoCompra": "Teste Brasília",
                "dataPublicacaoPncp": "2026-04-20",
            },
        ]
        with patch("datalake_query.query_datalake", _mock_dl(items)):
            res = client.get("/v1/blog/stats/cidade/brasilia")
            assert res.status_code == 200
            data = res.json()
            assert data["total_editais"] == 1
            assert data["uf"] == "DF"

    def test_cidade_stats_no_accent_city_still_works(self, client):
        """Regressão reversa: cidades sem acento (ex: Curitiba) continuam funcionando."""
        items = [
            {
                "numeroControlePNCP": "TEST-CWB-001",
                "orgaoEntidade": {"municipioNome": "Curitiba", "ufSigla": "PR"},
                "valorTotalEstimado": 75000.0,
                "objetoCompra": "Teste Curitiba",
                "dataPublicacaoPncp": "2026-04-20",
            },
        ]
        with patch("datalake_query.query_datalake", _mock_dl(items)):
            res = client.get("/v1/blog/stats/cidade/curitiba")
            assert res.status_code == 200
            data = res.json()
            assert data["total_editais"] == 1


# ---------------------------------------------------------------------------
# STORY-SEO-012: UF_CITIES expansion (16 → 27 UFs, 12 capitals unblocked)
# ---------------------------------------------------------------------------

# All 27 Brazilian state capitals + their slug forms (slug → expected_uf)
_CAPITALS_27 = [
    ("rio-branco", "AC"), ("maceio", "AL"), ("manaus", "AM"), ("macapa", "AP"),
    ("salvador", "BA"), ("fortaleza", "CE"), ("brasilia", "DF"), ("vitoria", "ES"),
    ("goiania", "GO"), ("sao-luis", "MA"), ("belo-horizonte", "MG"),
    ("campo-grande", "MS"), ("cuiaba", "MT"), ("belem", "PA"), ("joao-pessoa", "PB"),
    ("recife", "PE"), ("teresina", "PI"), ("curitiba", "PR"), ("rio-de-janeiro", "RJ"),
    ("natal", "RN"), ("porto-velho", "RO"), ("boa-vista", "RR"), ("porto-alegre", "RS"),
    ("florianopolis", "SC"), ("aracaju", "SE"), ("sao-paulo", "SP"), ("palmas", "TO"),
]

# 12 capitals previously returning 404 (story scope)
_CAPITALS_PREVIOUSLY_404 = [
    "maceio", "joao-pessoa", "aracaju", "teresina", "rio-branco", "porto-velho",
    "boa-vista", "macapa", "palmas", "cuiaba", "campo-grande", "natal",
]


class TestStorySEO012CapitalsExpansion:
    """STORY-SEO-012: validate UF_CITIES covers all 27 Brazilian capitals.

    Closes 12-capital gap that returned 404 before this story (Maceió, João
    Pessoa, Aracaju, Teresina, Rio Branco, Porto Velho, Boa Vista, Macapá,
    Palmas, Cuiabá, Campo Grande, Natal).
    """

    def test_uf_cities_dict_has_27_entries(self):
        """AC3: structural — UF_CITIES must cover all 27 Brazilian UFs."""
        from routes.blog_stats import UF_CITIES, ALL_UFS

        assert len(UF_CITIES) == 27, (
            f"Expected 27 UFs, got {len(UF_CITIES)}: missing "
            f"{set(ALL_UFS) - set(UF_CITIES.keys())}"
        )
        assert set(UF_CITIES.keys()) == set(ALL_UFS), (
            f"UF_CITIES keys must equal ALL_UFS. "
            f"Missing: {set(ALL_UFS) - set(UF_CITIES.keys())}, "
            f"Extra: {set(UF_CITIES.keys()) - set(ALL_UFS)}"
        )
        # Each UF must have at least the capital (≥1 city)
        for uf, cities in UF_CITIES.items():
            assert len(cities) >= 1, f"UF {uf} has no cities listed"

    @pytest.mark.parametrize("slug,expected_uf", _CAPITALS_27)
    def test_all_27_state_capitals_return_200(self, client, slug, expected_uf):
        """AC2: All 27 state capitals must return HTTP 200 (not 404).

        With mocked DataLake (empty results), total_editais=0 is acceptable;
        the assertion is that the slug resolves to a UF and the endpoint
        returns 200, not 404.
        """
        with patch("datalake_query.query_datalake", _mock_dl([])):
            res = client.get(f"/v1/blog/stats/cidade/{slug}")
            assert res.status_code == 200, (
                f"Capital '{slug}' returned {res.status_code} (expected 200). "
                f"UF_CITIES likely missing entry for {expected_uf}."
            )
            data = res.json()
            assert data["uf"] == expected_uf, (
                f"Capital '{slug}' resolved to UF '{data['uf']}', "
                f"expected '{expected_uf}'"
            )

    @pytest.mark.parametrize("slug", _CAPITALS_PREVIOUSLY_404)
    def test_cidade_stats_newly_added_capitals_work(self, client, slug):
        """AC6: 12 capitals that returned 404 before STORY-SEO-012 must now return 200.

        Regression guard for the specific scope of this story.
        """
        with patch("datalake_query.query_datalake", _mock_dl([])):
            res = client.get(f"/v1/blog/stats/cidade/{slug}")
            assert res.status_code == 200, (
                f"REGRESSION: capital '{slug}' returned {res.status_code} "
                f"(was 404 before STORY-SEO-012; must be 200 now). "
                f"Check UF_CITIES dict in backend/routes/blog_stats.py."
            )

    def test_uf_cities_each_uf_has_capital(self):
        """Sanity: each UF entry must include its actual capital as the first city."""
        from routes.blog_stats import UF_CITIES

        # UF -> expected capital (display name with accents)
        capitals = {
            "AC": "Rio Branco", "AL": "Maceió", "AM": "Manaus", "AP": "Macapá",
            "BA": "Salvador", "CE": "Fortaleza", "DF": "Brasília", "ES": "Vitória",
            "GO": "Goiânia", "MA": "São Luís", "MG": "Belo Horizonte",
            "MS": "Campo Grande", "MT": "Cuiabá", "PA": "Belém", "PB": "João Pessoa",
            "PE": "Recife", "PI": "Teresina", "PR": "Curitiba", "RJ": "Rio de Janeiro",
            "RN": "Natal", "RO": "Porto Velho", "RR": "Boa Vista", "RS": "Porto Alegre",
            "SC": "Florianópolis", "SE": "Aracaju", "SP": "São Paulo", "TO": "Palmas",
        }
        for uf, expected_capital in capitals.items():
            assert expected_capital in UF_CITIES[uf], (
                f"UF {uf}: capital '{expected_capital}' not in cities list "
                f"{UF_CITIES[uf]}"
            )


# ---------------------------------------------------------------------------
# Endpoint 4: GET /v1/blog/stats/panorama/{setor_id}
# ---------------------------------------------------------------------------

class TestPanoramaStats:
    def test_panorama_stats_success(self, client):
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_RESULTS)):
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
        # BTS-010b: 'software' sector was split into software_desenvolvimento /
        # software_licencas; use the current canonical ID.
        with patch("datalake_query.query_datalake", _mock_dl()):
            res = client.get("/v1/blog/stats/panorama/software_desenvolvimento")
            data = res.json()
            for month in data["sazonalidade"]:
                assert "period" in month
                assert "count" in month
                assert "avg_value" in month

    def test_panorama_stats_no_auth(self, client):
        """Public endpoint — no auth required."""
        # BTS-010b: 'saude' was split into medicamentos / equipamentos_medicos /
        # insumos_hospitalares; use an existing health-adjacent ID.
        with patch("datalake_query.query_datalake", _mock_dl()):
            res = client.get("/v1/blog/stats/panorama/medicamentos")
            assert res.status_code == 200


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

class TestCacheInvalidation:
    def test_invalidate_blog_cache(self, client):
        from routes.blog_stats import invalidate_blog_cache, _blog_cache

        with patch("datalake_query.query_datalake", _mock_dl()):
            client.get("/v1/blog/stats/setor/vestuario")
            assert len(_blog_cache) > 0

            invalidate_blog_cache()
            assert len(_blog_cache) == 0


# ---------------------------------------------------------------------------
# MKT-003: Enhanced SectorUfStats fields
# ---------------------------------------------------------------------------

# Richer mock data for MKT-003 tests — two items with distinct modalities/values (datalake flat format)
MOCK_PNCP_UF_SP = [
    {
        "objetoCompra": "Aquisição de uniformes para equipe de segurança",
        "uf": "SP",
        "valorTotalEstimado": 150000.0,
        "codigoModalidadeContratacao": 1,  # Leilão - Eletrônico (Lei 14.133)
        "dataPublicacaoFormatted": "2026-02-28",
        "nomeOrgao": "Secretaria de Segurança Pública",
        "municipio": "São Paulo",
    },
    {
        "objetoCompra": "Fardamentos militares para batalhão de uniformes",
        "uf": "SP",
        "valorTotalEstimado": 250000.0,
        "codigoModalidadeContratacao": 7,  # Pregão - Presencial (Lei 14.133)
        "dataPublicacaoFormatted": "2026-02-27",
        "nomeOrgao": "Polícia Militar do Estado de SP",
        "municipio": "São Paulo",
    },
]


class TestSectorUfStatsEnhanced:
    """MKT-003: Tests for enhanced SectorUfStats fields."""

    def test_sector_uf_stats_enhanced_fields(self, client):
        """Response includes value_range_min, value_range_max, top_modalidades, trend_90d with correct types."""
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_UF_SP)):
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
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_UF_SP)):
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

        with patch("datalake_query.query_datalake", _mock_dl(single_item)):
            res = client.get("/v1/blog/stats/setor/vestuario/uf/SP")
            assert res.status_code == 200

            data = res.json()
            assert data["value_range_min"] == data["value_range_max"]
            assert data["value_range_min"] == 150000.0

    def test_sector_uf_stats_modalities(self, client):
        """top_modalidades has entries with name (str) and count (int) structure."""
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_UF_SP)):
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
            # Code 1 = "Leilão - Eletrônico", Code 7 = "Pregão - Presencial" (Lei 14.133/2021)
            assert len(top_mods) == 2
            names = {e["name"] for e in top_mods}
            assert "Leilão - Eletrônico" in names
            assert "Pregão - Presencial" in names

    def test_sector_uf_stats_trend(self, client):
        """trend_90d has exactly 3 entries, each with period, count, avg_value."""
        with patch("datalake_query.query_datalake", _mock_dl(MOCK_PNCP_UF_SP)):
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
        """When datalake returns no results: value_range_min=0, top_modalidades=[], trend counts >= 1."""
        with patch("datalake_query.query_datalake", _mock_dl()):
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


def test_sector_uf_stats_most_recent_bid_date_present():
    """STORY-430 AC5: most_recent_bid_date é o max das datas disponíveis."""
    from routes.blog_stats import SectorUfStats
    # Testar que o campo existe no modelo
    stats = SectorUfStats(
        sector_id="tech",
        sector_name="Tecnologia",
        uf="SP",
        total_editais=5,
        avg_value=1000.0,
        top_oportunidades=[],
        last_updated="2026-04-12T00:00:00",
        most_recent_bid_date="2026-04-10",
    )
    assert stats.most_recent_bid_date == "2026-04-10"


def test_sector_uf_stats_most_recent_bid_date_optional():
    """STORY-430 AC5: most_recent_bid_date é None quando ausente."""
    from routes.blog_stats import SectorUfStats
    stats = SectorUfStats(
        sector_id="tech",
        sector_name="Tecnologia",
        uf="SP",
        total_editais=0,
        avg_value=0.0,
        top_oportunidades=[],
        last_updated="2026-04-12T00:00:00",
    )
    assert stats.most_recent_bid_date is None


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

    def test_sector_uf_contratos_db_failure_returns_empty(self, client):
        # Hotfix incident 2026-04-27: DB failure returns 200 + empty stats
        # (instead of 502) to prevent crawler retry storm that wedged backend.
        # Endpoint cache absorbs the empty response.
        mock_sb = MagicMock()
        mock_sb.table.side_effect = RuntimeError("connection refused")
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            # Unique slug to bypass cache from preceding tests in the class
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/AC")
            assert res.status_code == 200
            data = res.json()
            assert data["total_contracts"] == 0
            assert data["total_value"] == 0.0
            assert data["top_orgaos"] == []
            assert data["top_fornecedores"] == []


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

    def test_cidade_contratos_db_failure_returns_empty(self, client):
        # Hotfix incident 2026-04-27: DB failure returns 200 + empty stats
        # (instead of 502) to prevent crawler retry storm that wedged backend.
        mock_sb = MagicMock()
        mock_sb.table.side_effect = RuntimeError("db down")
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            # Unique slug to bypass cache from preceding tests in the class
            res = client.get("/v1/blog/stats/contratos/cidade/manaus")
            assert res.status_code == 200
            data = res.json()
            assert data["total_contracts"] == 0
            assert data["total_value"] == 0.0
            assert data["top_orgaos"] == []
            assert data["top_fornecedores"] == []


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


# ---------------------------------------------------------------------------
# SEO-475 — Enrichment fields: n_unique_orgaos, n_unique_fornecedores, sample_contracts
# ---------------------------------------------------------------------------

class TestContratosEnrichment:
    """AC1–AC11 for SEO-475: new enrichment fields on all contratos endpoints."""

    # AC1-3 / AC8-9: ContratosSetorUfStats has n_unique_orgaos, n_unique_fornecedores,
    # sample_contracts with correct semantics
    def test_setor_uf_has_enrichment_fields(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            assert res.status_code == 200
            data = res.json()
            assert "n_unique_orgaos" in data
            assert "n_unique_fornecedores" in data
            assert "sample_contracts" in data

    def test_setor_uf_n_unique_orgaos_count(self, client):
        """AC8: n_unique_orgaos = count of distinct orgao_cnpj in matched rows."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            # 3 SP rows matching vestuario: orgaos 111, 222, 333 → 3 unique
            assert data["n_unique_orgaos"] == 3

    def test_setor_uf_n_unique_fornecedores_count(self, client):
        """AC9: n_unique_fornecedores = count of distinct ni_fornecedor in matched rows."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            # 3 SP rows matching vestuario: fornecedores 12345678000101 (x2) + 98765432000199
            # → 2 unique fornecedores
            assert data["n_unique_fornecedores"] == 2

    def test_setor_uf_sample_contracts_structure(self, client):
        """AC6: sample_contracts items have exactly 5 required fields."""
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            assert len(data["sample_contracts"]) >= 1
            sample = data["sample_contracts"][0]
            assert set(sample.keys()) == {"objeto", "orgao", "fornecedor", "valor", "data_assinatura"}
            assert isinstance(sample["objeto"], str)
            assert isinstance(sample["orgao"], str)
            assert isinstance(sample["fornecedor"], str)
            assert sample["valor"] is None or isinstance(sample["valor"], (int, float))
            assert isinstance(sample["data_assinatura"], str)

    def test_setor_uf_sample_contracts_max_5(self, client):
        """AC7: sample_contracts is capped at 5 items."""
        # 7 matching rows to force the 5-cap
        many_rows = [
            {
                "ni_fornecedor": f"111111111{i:05d}",
                "nome_fornecedor": f"Fornecedor {i}",
                "orgao_cnpj": f"222222222{i:05d}",
                "orgao_nome": f"Órgão {i}",
                "valor_global": 50000.0 + i * 1000,
                "data_assinatura": f"2026-0{(i % 3) + 1}-{(i % 28) + 1:02d}",
                "objeto_contrato": f"Aquisição de uniformes lote {i}",
                "uf": "SP",
                "municipio": "São Paulo",
            }
            for i in range(7)
        ]
        mock_sb, _ = _make_contracts_supabase_mock(rows=many_rows)
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            assert len(data["sample_contracts"]) <= 5

    def test_setor_uf_sample_contracts_excludes_no_objeto(self, client):
        """AC7: rows with empty objeto_contrato are excluded from sample_contracts."""
        rows_with_empty_objeto = [
            {
                "ni_fornecedor": "11111111000111",
                "nome_fornecedor": "Forn A",
                "orgao_cnpj": "22222222000111",
                "orgao_nome": "Órgão A",
                "valor_global": 100000.0,
                "data_assinatura": "2026-03-01",
                "objeto_contrato": "",  # empty — should be excluded
                "uf": "SP",
                "municipio": "São Paulo",
            },
            MOCK_CONTRACT_ROWS[0],  # valid uniforms row with objeto
        ]
        mock_sb, _ = _make_contracts_supabase_mock(rows=rows_with_empty_objeto)
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            for sc in data["sample_contracts"]:
                assert sc["objeto"].strip() != ""

    def test_setor_uf_sample_contracts_excludes_zero_valor(self, client):
        """AC7: rows with valor_global == 0 are excluded from sample_contracts."""
        rows_with_zero_valor = [
            {
                "ni_fornecedor": "11111111000111",
                "nome_fornecedor": "Forn A",
                "orgao_cnpj": "22222222000111",
                "orgao_nome": "Órgão A",
                "valor_global": 0.0,  # zero — should be excluded
                "data_assinatura": "2026-03-01",
                "objeto_contrato": "Uniformes para agentes",
                "uf": "SP",
                "municipio": "São Paulo",
            },
        ]
        mock_sb, _ = _make_contracts_supabase_mock(rows=rows_with_zero_valor)
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            assert data["sample_contracts"] == []

    # AC4: ContratosCidadeStats has the enrichment fields
    def test_cidade_has_enrichment_fields(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/cidade/sao-paulo")
            assert res.status_code == 200
            data = res.json()
            assert "n_unique_orgaos" in data
            assert "n_unique_fornecedores" in data
            assert "sample_contracts" in data
            # São Paulo has 3 rows (org 111, 222, 555) and 3 distinct orgaos
            assert data["n_unique_orgaos"] >= 1
            assert data["n_unique_fornecedores"] >= 1

    # AC5: ContratosSetorStats (nacional) has the enrichment fields
    def test_setor_nacional_has_enrichment_fields(self, client):
        mock_sb, _ = _make_contracts_supabase_mock()
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario")
            assert res.status_code == 200
            data = res.json()
            assert "n_unique_orgaos" in data
            assert "n_unique_fornecedores" in data
            assert "sample_contracts" in data
            # 4 matching rows: 4 distinct orgaos (111, 222, 333, 444)
            assert data["n_unique_orgaos"] == 4
            # 3 distinct fornecedores (12345678000101 x2, 98765432000199, 55555555000155)
            assert data["n_unique_fornecedores"] == 3

    # AC11: backward compatibility — existing tests are unaffected (fields have defaults)
    def test_enrichment_fields_have_defaults(self):
        """AC11: Pydantic models accept missing enrichment fields via defaults."""
        from routes.blog_stats import ContratosSetorUfStats, ContratosCidadeStats, ContratosSetorStats

        # ContratosSetorUfStats without enrichment fields
        stats = ContratosSetorUfStats(
            sector_id="vestuario",
            sector_name="Vestuário",
            uf="SP",
            total_contracts=0,
            total_value=0.0,
            avg_value=0.0,
            top_orgaos=[],
            top_fornecedores=[],
            monthly_trend=[],
            last_updated="2026-04-13T00:00:00",
        )
        assert stats.n_unique_orgaos == 0
        assert stats.n_unique_fornecedores == 0
        assert stats.sample_contracts == []

        # ContratosCidadeStats without enrichment fields
        cidade_stats = ContratosCidadeStats(
            cidade="São Paulo",
            uf="SP",
            total_contracts=0,
            total_value=0.0,
            avg_value=0.0,
            top_orgaos=[],
            top_fornecedores=[],
            monthly_trend=[],
            last_updated="2026-04-13T00:00:00",
        )
        assert cidade_stats.n_unique_orgaos == 0
        assert cidade_stats.sample_contracts == []

        # ContratosSetorStats without enrichment fields
        setor_stats = ContratosSetorStats(
            sector_id="vestuario",
            sector_name="Vestuário",
            total_contracts=0,
            total_value=0.0,
            avg_value=0.0,
            top_orgaos=[],
            top_fornecedores=[],
            monthly_trend=[],
            by_uf=[],
            last_updated="2026-04-13T00:00:00",
        )
        assert setor_stats.n_unique_orgaos == 0
        assert setor_stats.sample_contracts == []

    def test_sample_contract_objeto_truncated_to_200(self, client):
        """AC7: objeto_contrato > 200 chars is truncated."""
        long_objeto = "A" * 300  # 300 chars
        rows = [{
            "ni_fornecedor": "11111111000111",
            "nome_fornecedor": "Forn A",
            "orgao_cnpj": "22222222000111",
            "orgao_nome": "Órgão A",
            "valor_global": 100000.0,
            "data_assinatura": "2026-03-01",
            "objeto_contrato": f"Uniformes {long_objeto}",
            "uf": "SP",
            "municipio": "São Paulo",
        }]
        mock_sb, _ = _make_contracts_supabase_mock(rows=rows)
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            res = client.get("/v1/blog/stats/contratos/vestuario/uf/SP")
            data = res.json()
            assert len(data["sample_contracts"]) == 1
            assert len(data["sample_contracts"][0]["objeto"]) <= 200
