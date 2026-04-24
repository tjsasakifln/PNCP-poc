"""STORY-SEO-015: Cache-Control headers em endpoints /v1/sitemap/*.

Valida que todos os 8 endpoints sitemap publicos respondem com Cache-Control
permitindo CDN/proxy/browser cachear por 6h fresh + 12h SWR + 24h stale-if-error.
"""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from startup.app_factory import create_app
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_all_caches():
    """Clear in-memory caches between tests to ensure handler runs."""
    try:
        from routes.sitemap_cnpjs import _sitemap_cache as c1, _fornecedores_sitemap_cache as c2
        c1.clear(); c2.clear()
    except Exception:
        pass
    try:
        from routes.sitemap_orgaos import _sitemap_cache as o1, _contratos_orgao_cache as o2
        o1.clear(); o2.clear()
    except Exception:
        pass
    try:
        from routes import sitemap_licitacoes
        sitemap_licitacoes._cache = None
    except Exception:
        pass
    try:
        from routes.sitemap_licitacoes_do_dia import _cache as l3
        l3.clear()
    except Exception:
        pass


EXPECTED_CC = "public, max-age=21600, stale-while-revalidate=43200, stale-if-error=86400"


@pytest.mark.parametrize(
    "endpoint,patch_target,return_value",
    [
        ("/v1/sitemap/cnpjs", "supabase_client.get_supabase", MagicMock()),
        ("/v1/sitemap/orgaos", "supabase_client.get_supabase", MagicMock()),
        ("/v1/sitemap/contratos-orgao-indexable", "supabase_client.get_supabase", MagicMock()),
        ("/v1/sitemap/fornecedores-cnpj", "supabase_client.get_supabase", MagicMock()),
        ("/v1/sitemap/licitacoes-do-dia-indexable", "supabase_client.get_supabase", MagicMock()),
    ],
)
def test_sitemap_endpoint_emits_cache_control(client, endpoint, patch_target, return_value):
    """STORY-SEO-015 AC2: cada endpoint sitemap emite Cache-Control configurado."""
    with patch(patch_target, return_value=return_value):
        resp = client.get(endpoint)
    assert resp.status_code == 200, f"{endpoint} failed: {resp.text[:200]}"
    cc = resp.headers.get("cache-control", "")
    assert cc == EXPECTED_CC, f"{endpoint} cache-control: {cc!r}"
    assert resp.headers.get("vary", "") == "Accept-Encoding"


def test_sitemap_municipios_emits_cache_control(client):
    """municipios usa cache + lista hardcoded (nao precisa mock supabase)."""
    resp = client.get("/v1/sitemap/municipios")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control", "") == EXPECTED_CC


def test_sitemap_itens_emits_cache_control(client):
    """itens usa cache + lista hardcoded (nao precisa mock supabase)."""
    resp = client.get("/v1/sitemap/itens")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control", "") == EXPECTED_CC


def test_sitemap_licitacoes_indexable_emits_cache_control(client):
    """licitacoes-indexable e o mais complexo (gather paralelo)."""
    with patch("routes.sitemap_licitacoes._compute_indexable_combos", return_value=[{"setor": "construcao", "uf": "SP"}]):
        resp = client.get("/v1/sitemap/licitacoes-indexable")
    assert resp.status_code == 200
    assert resp.headers.get("cache-control", "") == EXPECTED_CC


def test_cache_headers_constant_format():
    """Constante de header e estavel + tem fields esperados."""
    from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS
    cc = SITEMAP_CACHE_HEADERS["Cache-Control"]
    # 6h fresh
    assert "max-age=21600" in cc
    # 12h SWR
    assert "stale-while-revalidate=43200" in cc
    # 24h stale-if-error
    assert "stale-if-error=86400" in cc
    assert "public" in cc
