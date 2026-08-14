"""CONV-005b-1: Tests for digital_products schema, endpoint, and Stripe sync.

Tests:
- Migration SQL exists and has expected structure
- GET /v1/products returns correct structure
- GET /v1/products handles empty DB gracefully
- GET /v1/products uses cache on repeat calls
- Response schema matches DigitalProductOut
- Stripe sync script structure (importable)
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_PRODUCTS = [
    {
        "sku": "relatorio-oportunidade",
        "name": "Relatorio de Oportunidade Setorial",
        "description": "Analise completa de oportunidades em um setor especifico",
        "price_brl": 4700,
        "preview_config": {"max_free_items": 3, "blurred_items": 3},
        "delivery_config": {"type": "pdf", "template": "relatorio-oportunidade"},
    },
    {
        "sku": "fornecedores-vencedores",
        "name": "Fornecedores Vencedores",
        "description": "Lista detalhada de fornecedores",
        "price_brl": 6700,
        "preview_config": {"max_free_items": 3, "blurred_items": 5},
        "delivery_config": {"type": "pdf", "template": "fornecedores-vencedores"},
    },
]


@pytest.fixture
def client():
    """FastAPI test client with products router."""
    from fastapi import FastAPI
    from routes.products import router

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MIGRATION_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "supabase", "migrations")
)


def _find_migration_file() -> str | None:
    """Find the digital_products migration file."""
    for f in os.listdir(_MIGRATION_DIR):
        if "digital_products" in f and f.endswith(".sql") and "down" not in f:
            return os.path.join(_MIGRATION_DIR, f)
    return None


def _read_migration_content() -> str:
    """Read the digital_products migration content."""
    path = _find_migration_file()
    assert path is not None, "Migration file not found"
    with open(path) as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Migration tests
# ---------------------------------------------------------------------------


class TestMigration:
    """Verify migration files exist and have expected structure."""

    def test_migration_file_exists(self):
        """Verify the migration SQL file exists."""
        assert _find_migration_file() is not None, (
            "Migration file for digital_products not found in supabase/migrations/"
        )

    def test_migration_down_file_exists(self):
        """Verify the paired .down.sql file exists."""
        down_file = None
        for f in os.listdir(_MIGRATION_DIR):
            if "digital_products" in f and f.endswith(".down.sql"):
                down_file = f
                break
        assert down_file is not None, (
            "Migration .down.sql file for digital_products not found"
        )

    def test_migration_has_create_table(self):
        """Migration must contain CREATE TABLE digital_products."""
        content = _read_migration_content()
        assert "CREATE TABLE digital_products" in content

    def test_migration_has_seed_data(self):
        """Migration must contain INSERT for the 5 seed products."""
        content = _read_migration_content()
        assert "relatorio-oportunidade" in content
        assert "fornecedores-vencedores" in content
        assert "orgaos-compradores" in content
        assert "subcontratacao-map" in content
        assert "alerta-semanal" in content

    def test_migration_has_rls(self):
        """Migration must enable RLS and create policies."""
        content = _read_migration_content()
        assert "ENABLE ROW LEVEL SECURITY" in content
        assert "GRANT SELECT ON digital_products" in content

    def test_migration_has_stripe_columns(self):
        """Migration must include stripe_product_id and stripe_price_id columns."""
        content = _read_migration_content()
        assert "stripe_product_id" in content
        assert "stripe_price_id" in content


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestListProducts:
    """GET /v1/products behavior."""

    @patch("supabase_client.get_supabase")
    @patch("routes.products._get_cached_products", new_callable=AsyncMock)
    def test_returns_products_list(self, mock_cache, mock_get_supabase, client):
        """Should return a list of active products."""
        mock_cache.return_value = None

        mock_sb = MagicMock()
        mock_query = MagicMock()
        mock_sb.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=MOCK_PRODUCTS)
        mock_get_supabase.return_value = mock_sb

        resp = client.get("/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert "products" in data
        assert len(data["products"]) == 2
        assert data["products"][0]["sku"] == "relatorio-oportunidade"
        assert data["products"][0]["price_brl"] == 4700

    @patch("supabase_client.get_supabase")
    @patch("routes.products._get_cached_products", new_callable=AsyncMock)
    def test_returns_correct_schema(self, mock_cache, mock_get_supabase, client):
        """Response fields must match DigitalProductOut."""
        mock_cache.return_value = None

        mock_sb = MagicMock()
        mock_query = MagicMock()
        mock_sb.table.return_value = mock_query
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=MOCK_PRODUCTS)
        mock_get_supabase.return_value = mock_sb

        resp = client.get("/v1/products")
        data = resp.json()
        product = data["products"][0]
        assert "sku" in product
        assert "name" in product
        assert "price_brl" in product
        assert "preview_config" in product
        assert "delivery_config" in product
        assert "id" not in product  # should not expose internal ID
        assert "stripe_product_id" not in product  # should not expose Stripe IDs

    @patch("routes.products._get_cached_products", new_callable=AsyncMock)
    @patch("routes.products._set_cached_products", new_callable=AsyncMock)
    def test_empty_response_when_no_products(
        self, mock_set_cache, mock_get_cache, client
    ):
        """Should return empty products list when DB has no data."""
        mock_get_cache.return_value = None

        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            resp = client.get("/v1/products")
            assert resp.status_code == 200
            data = resp.json()
            assert data["products"] == []

    @patch("routes.products._get_cached_products", new_callable=AsyncMock)
    def test_uses_cache_when_available(self, mock_cache, client):
        """Should return cached data without hitting Supabase."""
        cached_data = {
            "products": [
                {
                    "sku": "cached-product",
                    "name": "Cached",
                    "description": "From cache",
                    "price_brl": 9999,
                    "preview_config": {},
                    "delivery_config": {},
                }
            ]
        }
        mock_cache.return_value = cached_data

        resp = client.get("/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert data["products"][0]["sku"] == "cached-product"
        assert data["products"][0]["price_brl"] == 9999
