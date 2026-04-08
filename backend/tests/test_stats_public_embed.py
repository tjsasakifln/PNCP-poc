"""S9: Tests for stats_public embed/badge/schema formats."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.fixture
def mock_datalake():
    """Mock datalake query to return sample data."""
    sample = [
        {
            "objeto": "Aquisição de computadores",
            "valorTotalEstimado": 150000.0,
            "uf": "SP",
            "codigoModalidadeContratacao": 5,
        },
        {
            "objeto": "Manutenção predial",
            "valorTotalEstimado": 80000.0,
            "uf": "RJ",
            "codigoModalidadeContratacao": 8,
        },
    ]
    with patch("datalake_query.query_datalake", new_callable=AsyncMock, return_value=sample):
        # Clear the in-memory cache so _generate_stats runs fresh
        from routes.stats_public import _stats_cache
        _stats_cache.clear()
        yield


@pytest.mark.asyncio
async def test_stats_public_json_includes_data_download(mock_datalake):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/stats/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "data_download" in data
    assert data["data_download"]["@type"] == "DataDownload"
    assert data["data_download"]["encodingFormat"] == "application/json"


@pytest.mark.asyncio
async def test_stats_public_format_embed(mock_datalake):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/stats/public?format=embed")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    body = resp.text
    assert "smartlic.tech/estatisticas" in body
    assert "sl-embed" in body


@pytest.mark.asyncio
async def test_stats_public_format_badge(mock_datalake):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/stats/public?format=badge")
    assert resp.status_code == 200
    assert "image/svg+xml" in resp.headers.get("content-type", "")
    body = resp.text
    assert "<svg" in body
    assert "SmartLic" in body


@pytest.mark.asyncio
async def test_stats_public_default_is_json(mock_datalake):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/v1/stats/public")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    assert "updated_at" in data
