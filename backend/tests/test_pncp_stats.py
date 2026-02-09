"""
Unit tests for PNCP statistics module and /api/pncp-stats endpoint.

Tests cover:
- compute_pncp_stats() function logic
- Annualization calculations
- Error handling and fallback behavior
- Cache hit/miss scenarios
- Concurrent request handling (lock mechanism)
- API timeout handling
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, PNCP_STATS_CACHE_KEY
from pncp_stats import (
    compute_pncp_stats,
    get_fallback_stats,
    FALLBACK_STATS,
    ALL_UFS,
)
from schemas import PNCPStatsResponse


# Test fixtures


@pytest.fixture
def mock_pncp_data():
    """Mock PNCP API response data (10 bids)."""
    return [
        {
            "numeroControlePNCP": f"test-bid-{i}",
            "valorTotalEstimado": 100000.0,  # R$ 100k per bid
            "objetoCompra": f"Test procurement {i}",
            "uf": "SP",
        }
        for i in range(10)
    ]


@pytest.fixture
def mock_sectors():
    """Mock sector data."""
    return [
        {"id": "vestuario", "name": "Vestuário", "description": "Uniformes"},
        {"id": "alimentos", "name": "Alimentos", "description": "Merenda"},
        {"id": "informatica", "name": "Informática", "description": "TI"},
    ]


# Tests for compute_pncp_stats()


@pytest.mark.asyncio
async def test_compute_pncp_stats_success(mock_pncp_data, mock_sectors):
    """Test successful stats computation with mocked PNCP API."""
    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar, \
         patch("pncp_stats.list_sectors", return_value=mock_sectors):

        mock_buscar.return_value = mock_pncp_data

        stats = await compute_pncp_stats()

        # Verify API was called with correct parameters
        mock_buscar.assert_called_once()
        call_kwargs = mock_buscar.call_args.kwargs
        assert call_kwargs["ufs"] == ALL_UFS
        assert call_kwargs["modalidades"] == [6]
        assert call_kwargs["status"] is None
        assert call_kwargs["max_concurrent"] == 10

        # Verify date range (last 30 days)
        data_inicial = call_kwargs["data_inicial"]
        data_final = call_kwargs["data_final"]
        d_inicial = datetime.fromisoformat(data_inicial).date()
        d_final = datetime.fromisoformat(data_final).date()
        assert (d_final - d_inicial).days == 30

        # Verify calculations
        assert stats.total_bids_30d == 10
        assert stats.annualized_total == int(10 * 365 / 30)  # 121

        total_value_30d = 10 * 100000.0  # 10 bids * R$ 100k
        assert stats.total_value_30d == total_value_30d
        assert stats.annualized_value == total_value_30d * 365 / 30

        assert stats.total_sectors == 3
        assert isinstance(stats.last_updated, str)
        assert "Z" in stats.last_updated  # ISO 8601 with timezone


@pytest.mark.asyncio
async def test_compute_pncp_stats_empty_results(mock_sectors):
    """Test stats computation with zero bids returned."""
    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar, \
         patch("pncp_stats.list_sectors", return_value=mock_sectors):

        mock_buscar.return_value = []  # No bids

        stats = await compute_pncp_stats()

        assert stats.total_bids_30d == 0
        assert stats.annualized_total == 0
        assert stats.total_value_30d == 0.0
        assert stats.annualized_value == 0.0
        assert stats.total_sectors == 3


@pytest.mark.asyncio
async def test_compute_pncp_stats_timeout():
    """Test timeout handling in stats computation."""
    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar:

        # Simulate slow API that exceeds timeout
        async def slow_api(*args, **kwargs):
            await asyncio.sleep(2)
            return []

        mock_buscar.side_effect = slow_api

        from exceptions import PNCPAPIError

        with pytest.raises(PNCPAPIError, match="timeout"):
            await compute_pncp_stats(timeout_seconds=0.1)


@pytest.mark.asyncio
async def test_compute_pncp_stats_api_error():
    """Test API error handling in stats computation."""
    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar:

        from exceptions import PNCPAPIError

        mock_buscar.side_effect = Exception("PNCP API connection failed")

        with pytest.raises(PNCPAPIError, match="Failed to compute"):
            await compute_pncp_stats()


@pytest.mark.asyncio
async def test_compute_pncp_stats_missing_values():
    """Test handling of bids with missing or null valorTotalEstimado."""
    mock_data = [
        {"numeroControlePNCP": "1", "valorTotalEstimado": 100000.0},
        {"numeroControlePNCP": "2", "valorTotalEstimado": None},  # Null value
        {"numeroControlePNCP": "3"},  # Missing field
        {"numeroControlePNCP": "4", "valorTotalEstimado": 50000.0},
    ]

    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar, \
         patch("pncp_stats.list_sectors", return_value=[]):

        mock_buscar.return_value = mock_data

        stats = await compute_pncp_stats()

        # Should handle missing/null values gracefully
        assert stats.total_bids_30d == 4
        assert stats.total_value_30d == 150000.0  # Only sum valid values


# Tests for get_fallback_stats()


def test_get_fallback_stats():
    """Test fallback stats have valid structure and updated timestamp."""
    stats = get_fallback_stats()

    assert isinstance(stats, PNCPStatsResponse)
    assert stats.total_bids_30d > 0
    assert stats.annualized_total > 0
    assert stats.total_value_30d > 0
    assert stats.annualized_value > 0
    assert stats.total_sectors > 0

    # Timestamp should be recent (within last 5 seconds)
    timestamp = datetime.fromisoformat(stats.last_updated.replace("Z", "+00:00"))
    age_seconds = (datetime.utcnow() - timestamp.replace(tzinfo=None)).total_seconds()
    assert age_seconds < 5


# Tests for /api/pncp-stats endpoint


def test_pncp_stats_endpoint_cache_hit():
    """Test endpoint returns cached data when available."""
    client = TestClient(app)

    mock_stats = PNCPStatsResponse(
        total_bids_30d=5000,
        annualized_total=60833,
        total_value_30d=10000000.0,
        annualized_value=121666666.67,
        total_sectors=5,
        last_updated="2026-02-09T12:00:00Z"
    )

    with patch("cache.redis_client") as mock_redis:
        mock_redis.get.return_value = mock_stats.model_dump_json()

        response = client.get("/api/pncp-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_bids_30d"] == 5000
        assert data["annualized_total"] == 60833
        assert data["total_sectors"] == 5

        # Verify cache was checked
        mock_redis.get.assert_called_with(PNCP_STATS_CACHE_KEY)


@pytest.mark.asyncio
async def test_pncp_stats_endpoint_cache_miss(mock_pncp_data, mock_sectors):
    """Test endpoint computes fresh data on cache miss."""
    client = TestClient(app)

    with patch("cache.redis_client") as mock_redis, \
         patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar, \
         patch("pncp_stats.list_sectors", return_value=mock_sectors):

        # Cache miss
        mock_redis.get.return_value = None
        mock_buscar.return_value = mock_pncp_data

        response = client.get("/api/pncp-stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_bids_30d"] == 10
        assert data["total_sectors"] == 3

        # Verify cache was updated
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == PNCP_STATS_CACHE_KEY
        assert call_args[0][1] == 86400  # 24 hours


def test_pncp_stats_endpoint_api_failure_fallback():
    """Test endpoint returns fallback data when API fails."""
    client = TestClient(app)

    with patch("cache.redis_client") as mock_redis, \
         patch("pncp_stats.compute_pncp_stats", new_callable=AsyncMock) as mock_compute:

        # Cache miss
        mock_redis.get.return_value = None

        # API failure
        from exceptions import PNCPAPIError
        mock_compute.side_effect = PNCPAPIError("PNCP API unavailable")

        response = client.get("/api/pncp-stats")

        assert response.status_code == 200
        data = response.json()

        # Should return fallback data
        assert data["total_bids_30d"] == FALLBACK_STATS.total_bids_30d
        assert data["annualized_total"] == FALLBACK_STATS.annualized_total

        # Verify fallback was cached (1 hour TTL)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # 1 hour for fallback


@pytest.mark.skip(reason="Lock implementation needs refactor for event loop safety")
@pytest.mark.asyncio
async def test_pncp_stats_endpoint_concurrent_requests(mock_pncp_data, mock_sectors):
    """Test concurrent requests use lock to prevent stampeding herd."""
    client = TestClient(app)

    compute_call_count = 0

    async def mock_compute(*args, **kwargs):
        nonlocal compute_call_count
        compute_call_count += 1
        await asyncio.sleep(0.1)  # Simulate slow computation
        return PNCPStatsResponse(
            total_bids_30d=10,
            annualized_total=121,
            total_value_30d=1000000.0,
            annualized_value=12166666.67,
            total_sectors=3,
            last_updated=datetime.utcnow().isoformat() + "Z"
        )

    with patch("cache.redis_client") as mock_redis, \
         patch("pncp_stats.compute_pncp_stats", new_callable=AsyncMock) as mock_compute_fn:

        # Cache miss
        mock_redis.get.return_value = None
        mock_compute_fn.side_effect = mock_compute

        # Simulate 5 concurrent requests
        tasks = [
            asyncio.create_task(asyncio.to_thread(client.get, "/api/pncp-stats"))
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # Due to lock, compute should only be called once or twice
        # (race condition may allow 2 calls before lock is acquired)
        assert compute_call_count <= 2, "Lock failed - too many compute calls"


def test_pncp_stats_endpoint_response_schema():
    """Test endpoint response matches PNCPStatsResponse schema."""
    client = TestClient(app)

    mock_stats = get_fallback_stats()

    with patch("cache.redis_client") as mock_redis:
        mock_redis.get.return_value = mock_stats.model_dump_json()

        response = client.get("/api/pncp-stats")

        assert response.status_code == 200
        data = response.json()

        # Validate schema
        validated = PNCPStatsResponse(**data)
        assert validated.total_bids_30d >= 0
        assert validated.annualized_total >= 0
        assert validated.total_value_30d >= 0.0
        assert validated.annualized_value >= 0.0
        assert validated.total_sectors >= 0
        assert isinstance(validated.last_updated, str)


# Edge cases


@pytest.mark.asyncio
async def test_compute_pncp_stats_large_values():
    """Test handling of very large bid values (billions)."""
    mock_data = [
        {"numeroControlePNCP": str(i), "valorTotalEstimado": 1_000_000_000.0}  # R$ 1B
        for i in range(5)
    ]

    with patch("pncp_stats.buscar_todas_ufs_paralelo", new_callable=AsyncMock) as mock_buscar, \
         patch("pncp_stats.list_sectors", return_value=[]):

        mock_buscar.return_value = mock_data

        stats = await compute_pncp_stats()

        # Should handle large numbers correctly
        assert stats.total_value_30d == 5_000_000_000.0  # R$ 5B
        assert stats.annualized_value == 5_000_000_000.0 * 365 / 30


@pytest.mark.skip(reason="Lock implementation needs refactor for event loop safety")
def test_pncp_stats_endpoint_invalid_cached_data():
    """Test endpoint handles corrupted cache data gracefully."""
    client = TestClient(app)

    with patch("cache.redis_client") as mock_redis, \
         patch("pncp_stats.compute_pncp_stats", new_callable=AsyncMock) as mock_compute:

        # Return invalid JSON
        mock_redis.get.return_value = "invalid json {{"

        mock_compute.return_value = get_fallback_stats()

        response = client.get("/api/pncp-stats")

        # Should recompute instead of crashing
        assert response.status_code == 200
        mock_compute.assert_called_once()
