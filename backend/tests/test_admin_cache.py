"""Tests for admin cache endpoints (GTM-RESILIENCE-B05 AC3-AC8, AC10)."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient

from main import app
from auth import require_auth
from admin import require_admin


# --- Fixtures ---


@pytest.fixture
def admin_user():
    return {"id": "admin-001", "email": "admin@test.com", "role": "admin"}


@pytest.fixture
def normal_user():
    return {"id": "user-001", "email": "user@test.com", "role": "user"}


@pytest.fixture
def client_as_admin(admin_user):
    """TestClient with admin auth override."""
    app.dependency_overrides[require_auth] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def client_as_user(normal_user):
    """TestClient with non-admin auth override."""
    app.dependency_overrides[require_auth] = lambda: normal_user

    async def deny_admin(user=None):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not admin")

    app.dependency_overrides[require_admin] = deny_admin
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def client_no_auth():
    """TestClient without auth."""
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin, None)
    return TestClient(app)


# --- AC3: GET /v1/admin/cache/metrics ---


class TestCacheMetricsEndpoint:
    """AC3: Cache metrics endpoint returns expected fields."""

    def test_returns_all_metric_fields(self, client_as_admin):
        mock_metrics = {
            "hit_rate_24h": 0.73,
            "miss_rate_24h": 0.27,
            "stale_served_24h": 15,
            "fresh_served_24h": 42,
            "total_entries": 87,
            "priority_distribution": {"hot": 12, "warm": 35, "cold": 40},
            "age_distribution": {"0-1h": 15, "1-6h": 30, "6-12h": 25, "12-24h": 17},
            "degraded_keys": 3,
            "avg_fetch_duration_ms": 4500,
            "top_keys": [],
        }

        with patch("search_cache.get_cache_metrics", new_callable=AsyncMock, return_value=mock_metrics):
            response = client_as_admin.get("/v1/admin/cache/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["hit_rate_24h"] == 0.73
        assert data["miss_rate_24h"] == 0.27
        assert data["total_entries"] == 87
        assert data["priority_distribution"]["hot"] == 12
        assert data["age_distribution"]["0-1h"] == 15
        assert data["degraded_keys"] == 3
        assert data["avg_fetch_duration_ms"] == 4500


class TestCacheMetricsCalculation:
    """AC4/AC10: Hit rate and age distribution calculations."""

    @pytest.mark.asyncio
    async def test_hit_rate_from_counters(self):
        """AC4: Hit rate calculated from counter data."""
        from search_cache import get_cache_metrics

        mock_cache = MagicMock()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        def mock_get(key):
            counters = {
                f"cache_counter:hits:{today}": "7",
                f"cache_counter:misses:{today}": "3",
                f"cache_counter:stale_served:{today}": "2",
                f"cache_counter:fresh_served:{today}": "5",
            }
            return counters.get(key)

        mock_cache.get = mock_get

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])

        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            with patch("supabase_client.get_supabase", return_value=mock_sb):
                metrics = await get_cache_metrics()

        assert metrics["hit_rate_24h"] == 0.7
        assert metrics["miss_rate_24h"] == 0.3

    @pytest.mark.asyncio
    async def test_age_distribution_buckets(self):
        """AC10: Age distribution has correct bucket counts."""
        from search_cache import get_cache_metrics

        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        now = datetime.now(timezone.utc)
        rows = [
            {"params_hash": "a1", "priority": "hot", "fetched_at": (now - timedelta(minutes=30)).isoformat(), "access_count": 5, "fail_streak": 0, "degraded_until": None, "fetch_duration_ms": 1000},
            {"params_hash": "a2", "priority": "warm", "fetched_at": (now - timedelta(hours=3)).isoformat(), "access_count": 2, "fail_streak": 0, "degraded_until": None, "fetch_duration_ms": 2000},
            {"params_hash": "a3", "priority": "cold", "fetched_at": (now - timedelta(hours=8)).isoformat(), "access_count": 1, "fail_streak": 0, "degraded_until": None, "fetch_duration_ms": 3000},
            {"params_hash": "a4", "priority": "cold", "fetched_at": (now - timedelta(hours=15)).isoformat(), "access_count": 0, "fail_streak": 0, "degraded_until": None, "fetch_duration_ms": 5000},
        ]

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=rows)

        with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
            with patch("supabase_client.get_supabase", return_value=mock_sb):
                metrics = await get_cache_metrics()

        assert metrics["age_distribution"]["0-1h"] == 1
        assert metrics["age_distribution"]["1-6h"] == 1
        assert metrics["age_distribution"]["6-12h"] == 1
        assert metrics["age_distribution"]["12-24h"] == 1


# --- AC5: DELETE /v1/admin/cache/{params_hash} ---


class TestCacheInvalidation:
    """AC5: Single cache entry invalidation."""

    def test_invalidate_specific_entry(self, client_as_admin):
        mock_result = {"deleted_levels": ["supabase", "redis", "local"]}

        with patch("search_cache.invalidate_cache_entry", new_callable=AsyncMock, return_value=mock_result):
            response = client_as_admin.delete("/v1/admin/cache/abcdef1234567890")

        assert response.status_code == 200
        data = response.json()
        assert "supabase" in data["deleted_levels"]
        assert "redis" in data["deleted_levels"]
        assert "local" in data["deleted_levels"]

    def test_invalid_hash_format_returns_400(self, client_as_admin):
        response = client_as_admin.delete("/v1/admin/cache/NOT-HEX!!")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalidate_clears_all_levels(self):
        """AC5: Entry removed from Supabase, Redis, and local."""
        from search_cache import invalidate_cache_entry

        mock_sb = MagicMock()
        mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

        mock_cache = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
                with patch("search_cache.LOCAL_CACHE_DIR") as mock_dir:
                    mock_file = MagicMock()
                    mock_file.exists.return_value = True
                    mock_dir.__truediv__ = MagicMock(return_value=mock_file)

                    result = await invalidate_cache_entry("abc123def456")

        assert "supabase" in result["deleted_levels"]
        assert "redis" in result["deleted_levels"]
        assert "local" in result["deleted_levels"]


# --- AC6: DELETE /v1/admin/cache (all) ---


class TestCacheBulkInvalidation:
    """AC6: Bulk cache invalidation with confirmation header."""

    def test_without_confirm_header_returns_400(self, client_as_admin):
        response = client_as_admin.delete("/v1/admin/cache")
        assert response.status_code == 400
        assert "X-Confirm" in response.json()["detail"]

    def test_with_confirm_header_succeeds(self, client_as_admin):
        mock_result = {"deleted_counts": {"supabase": 10, "redis": 5, "local": 3}}

        with patch("search_cache.invalidate_all_cache", new_callable=AsyncMock, return_value=mock_result):
            response = client_as_admin.delete(
                "/v1/admin/cache",
                headers={"X-Confirm": "delete-all"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_counts"]["supabase"] == 10


# --- AC7: GET /v1/admin/cache/{params_hash} (inspection) ---


class TestCacheInspection:
    """AC7: Cache entry inspection endpoint."""

    def test_inspect_existing_entry(self, client_as_admin):
        mock_entry = {
            "params_hash": "abc123",
            "user_id": "u1",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
            "results_count": 15,
            "sources": ["pncp", "pcp"],
            "fetched_at": "2026-02-19T10:00:00+00:00",
            "created_at": "2026-02-19T10:00:00+00:00",
            "priority": "hot",
            "access_count": 47,
            "last_accessed_at": "2026-02-19T14:00:00+00:00",
            "fail_streak": 0,
            "degraded_until": None,
            "coverage": {"ufs_requested": ["SP"], "ufs_processed": ["SP"]},
            "fetch_duration_ms": 3200,
            "last_success_at": "2026-02-19T10:00:00+00:00",
            "last_attempt_at": "2026-02-19T10:00:00+00:00",
            "age_hours": 4.0,
            "cache_status": "fresh",
        }

        with patch("search_cache.inspect_cache_entry", new_callable=AsyncMock, return_value=mock_entry):
            response = client_as_admin.get("/v1/admin/cache/abc123def456")

        assert response.status_code == 200
        data = response.json()
        assert data["params_hash"] == "abc123"
        assert data["priority"] == "hot"
        assert data["access_count"] == 47
        assert data["cache_status"] == "fresh"
        assert data["results_count"] == 15
        assert data["sources"] == ["pncp", "pcp"]
        assert data["coverage"] is not None

    def test_inspect_nonexistent_returns_404(self, client_as_admin):
        with patch("search_cache.inspect_cache_entry", new_callable=AsyncMock, return_value=None):
            response = client_as_admin.get("/v1/admin/cache/0000000000000000")

        assert response.status_code == 404


# --- AC8: Admin-only protection ---


class TestAdminOnlyProtection:
    """AC8: All cache admin endpoints require admin role."""

    def test_metrics_requires_admin(self, client_as_user):
        response = client_as_user.get("/v1/admin/cache/metrics")
        assert response.status_code == 403

    def test_inspect_requires_admin(self, client_as_user):
        response = client_as_user.get("/v1/admin/cache/abc123def456")
        assert response.status_code == 403

    def test_invalidate_requires_admin(self, client_as_user):
        response = client_as_user.delete("/v1/admin/cache/abc123def456")
        assert response.status_code == 403

    def test_invalidate_all_requires_admin(self, client_as_user):
        response = client_as_user.delete(
            "/v1/admin/cache",
            headers={"X-Confirm": "delete-all"},
        )
        assert response.status_code == 403

    def test_no_auth_returns_401(self, client_no_auth):
        response = client_no_auth.get("/v1/admin/cache/metrics")
        assert response.status_code in (401, 403)
