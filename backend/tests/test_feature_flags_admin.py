"""Tests for CROSS-003: Feature Flags Runtime Admin API.

Tests the /admin/feature-flags endpoints for listing, updating,
and reloading feature flags at runtime.

Uses standalone FastAPI app (not main.app) to avoid lifespan signal issues.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

ADMIN_UUID = "550e8400-e29b-41d4-a716-446655440000"
ADMIN_USER = {"id": ADMIN_UUID, "email": "admin@test.com", "role": "authenticated"}


@pytest.fixture
def client():
    """Create test client with admin auth override using standalone app."""
    from routes.feature_flags import router
    from admin import require_admin

    app = FastAPI()
    app.include_router(router)

    async def mock_require_admin():
        return ADMIN_USER

    app.dependency_overrides[require_admin] = mock_require_admin

    return TestClient(app)


@pytest.fixture
def unauth_client():
    """Create test client without auth overrides."""
    from routes.feature_flags import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear runtime overrides and TTL cache before each test.

    BTS-011 cluster 7: `_feature_flag_cache` is module-level state in
    `config.features` that persists across tests. Without explicit
    teardown, `test_update_flag_clears_ttl_cache` fails in batch because
    prior tests (or prior runs via `get_feature_flag()`) leave cache
    entries that the seed line then overwrites, and the endpoint's
    `del` happens — but a collateral read by `_resolve_flag_value` or
    a concurrent test may re-populate the entry between PATCH return
    and the final assertion. Clearing on setup+teardown eliminates the
    cross-test contamination.
    """
    from routes.feature_flags import _runtime_overrides
    from config.features import _feature_flag_cache

    _runtime_overrides.clear()
    _feature_flag_cache.clear()
    yield
    _runtime_overrides.clear()
    _feature_flag_cache.clear()


class TestListFeatureFlags:
    """GET /admin/feature-flags"""

    @patch("redis_pool.is_redis_available", new_callable=AsyncMock, return_value=False)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_list_returns_all_flags(self, mock_redis_override, mock_redis, client):
        """Should return all registered feature flags."""
        resp = client.get("/admin/feature-flags")
        assert resp.status_code == 200
        data = resp.json()
        assert "flags" in data
        assert "total" in data
        assert data["total"] > 0
        assert data["redis_available"] is False

        # Verify structure of each flag
        for flag in data["flags"]:
            assert "name" in flag
            assert "value" in flag
            assert "source" in flag
            assert "description" in flag
            assert "env_var" in flag
            assert "default" in flag
            assert flag["source"] in ("redis", "memory", "env", "default")

    @patch("redis_pool.is_redis_available", new_callable=AsyncMock, return_value=False)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_list_contains_known_flags(self, mock_redis_override, mock_redis, client):
        """Should include well-known flags like LLM_ARBITER_ENABLED."""
        resp = client.get("/admin/feature-flags")
        assert resp.status_code == 200
        flag_names = [f["name"] for f in resp.json()["flags"]]
        assert "LLM_ARBITER_ENABLED" in flag_names
        assert "TRIAL_PAYWALL_ENABLED" in flag_names

    @patch("redis_pool.is_redis_available", new_callable=AsyncMock, return_value=False)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_list_flags_sorted(self, mock_redis_override, mock_redis, client):
        """Flags should be returned in alphabetical order."""
        resp = client.get("/admin/feature-flags")
        assert resp.status_code == 200
        names = [f["name"] for f in resp.json()["flags"]]
        assert names == sorted(names)

    @patch("redis_pool.is_redis_available", new_callable=AsyncMock, return_value=False)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_list_flags_have_descriptions(self, mock_redis_override, mock_redis, client):
        """Most flags should have non-empty descriptions."""
        resp = client.get("/admin/feature-flags")
        assert resp.status_code == 200
        flags_with_desc = [f for f in resp.json()["flags"] if f["description"]]
        # At least 80% of flags should have descriptions
        assert len(flags_with_desc) > resp.json()["total"] * 0.8


class TestUpdateFeatureFlag:
    """PATCH /admin/feature-flags/{flag_name}"""

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_update_flag_success(self, mock_get, mock_set, client):
        """Should update a flag and return previous/new values."""
        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "LLM_ARBITER_ENABLED"
        assert data["value"] is False
        assert data["source"] == "redis"
        assert "previous_value" in data
        assert "previous_source" in data

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=False)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_update_flag_redis_unavailable_falls_back_to_memory(self, mock_get, mock_set, client):
        """When Redis is unavailable, should fall back to in-memory storage."""
        # BTS-010a: FILTER_DEBUG_MODE was removed from _FEATURE_FLAG_REGISTRY;
        # use DIGEST_ENABLED (ops-toggle, still in registry) as replacement fixture.
        resp = client.patch(
            "/admin/feature-flags/DIGEST_ENABLED",
            json={"value": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "memory"
        assert data["value"] is True

    def test_update_nonexistent_flag_returns_404(self, client):
        """Should return 404 for unknown flag names."""
        resp = client.patch(
            "/admin/feature-flags/TOTALLY_FAKE_FLAG",
            json={"value": True},
        )
        assert resp.status_code == 404
        assert "not found in registry" in resp.json()["detail"]

    def test_update_flag_invalid_body(self, client):
        """Should return 422 for missing value field."""
        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={},
        )
        assert resp.status_code == 422

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_update_flag_invalidates_ttl_cache(self, mock_get, mock_set, client):
        """BTS-013: After an admin update, subsequent reads must return the new value.

        Test the observable invariant (subsequent get_feature_flag() reads),
        not the internal cache state. BTS-013 made _runtime_overrides
        authoritative in config/features — so the admin toggle takes effect
        immediately regardless of what the TTL cache happens to contain.
        """
        from config.features import _feature_flag_cache, get_feature_flag
        import time

        # Seed the cache with OLD value (True) — establishes that even a
        # pre-populated stale cache entry must not shadow the new override.
        _feature_flag_cache["LLM_ARBITER_ENABLED"] = (True, time.time())

        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": False},
        )
        assert resp.status_code == 200

        # Observable invariant: next read returns the NEW value (False),
        # because runtime_overrides is authoritative over TTL cache.
        assert get_feature_flag("LLM_ARBITER_ENABLED") is False, (
            "get_feature_flag returned stale True after admin update to False"
        )

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_update_flag_stores_in_memory(self, mock_get, mock_set, client):
        """After update, in-memory override should be set."""
        # BTS-010a: FILTER_DEBUG_MODE was removed from _FEATURE_FLAG_REGISTRY;
        # use DIGEST_ENABLED (ops-toggle, still in registry) as replacement fixture.
        from routes.feature_flags import _runtime_overrides

        resp = client.patch(
            "/admin/feature-flags/DIGEST_ENABLED",
            json={"value": True},
        )
        assert resp.status_code == 200
        assert _runtime_overrides.get("DIGEST_ENABLED") is True

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    def test_update_flag_toggle_off_and_on(self, mock_get, mock_set, client):
        """Should be able to toggle a flag off then on."""
        # Toggle off
        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": False},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] is False

        # Toggle on
        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": True},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] is True


class TestReloadFeatureFlags:
    """POST /admin/feature-flags/reload"""

    @patch("routes.feature_flags._redis_clear_all_overrides", new_callable=AsyncMock, return_value=3)
    def test_reload_clears_overrides(self, mock_clear, client):
        """Should clear all overrides and return current values."""
        from routes.feature_flags import _runtime_overrides
        _runtime_overrides["LLM_ARBITER_ENABLED"] = False
        # FILTER_DEBUG_MODE was removed from _FEATURE_FLAG_REGISTRY (BTS-010a);
        # use DIGEST_ENABLED as the second override fixture.
        _runtime_overrides["DIGEST_ENABLED"] = True

        resp = client.post("/admin/feature-flags/reload")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["overrides_cleared"] == 5  # 3 from Redis + 2 from memory
        assert "flags" in data
        assert isinstance(data["flags"], dict)
        assert len(data["flags"]) > 0

        # Memory overrides should be cleared
        assert len(_runtime_overrides) == 0

    @patch("routes.feature_flags._redis_clear_all_overrides", new_callable=AsyncMock, return_value=0)
    def test_reload_with_no_overrides(self, mock_clear, client):
        """Should succeed even when no overrides exist."""
        resp = client.post("/admin/feature-flags/reload")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["overrides_cleared"] == 0

    @patch("routes.feature_flags._redis_clear_all_overrides", new_callable=AsyncMock, return_value=0)
    def test_reload_returns_all_registry_flags(self, mock_clear, client):
        """Should return all flags from the registry after reload."""
        from config.features import _FEATURE_FLAG_REGISTRY

        resp = client.post("/admin/feature-flags/reload")
        assert resp.status_code == 200
        data = resp.json()
        # All registry flags should be in the response
        for flag_name in _FEATURE_FLAG_REGISTRY:
            assert flag_name in data["flags"]


class TestUpdateFeatureFlagAudit:
    """AC3 — STORY-5.2: PATCH must emit persistent audit_logger event."""

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    @patch("routes.feature_flags.audit_logger")
    def test_update_feature_flag_logs_audit_event(self, mock_audit_logger, mock_get, mock_set, client):
        """PATCH should call audit_logger.log with event_type=admin.feature_flag_change."""
        mock_audit_logger.log = AsyncMock()

        resp = client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": False},
        )
        assert resp.status_code == 200

        mock_audit_logger.log.assert_called_once()
        call_kwargs = mock_audit_logger.log.call_args
        assert call_kwargs.kwargs["event_type"] == "admin.feature_flag_change"
        assert call_kwargs.kwargs["actor_id"] == ADMIN_UUID
        assert call_kwargs.kwargs["target_id"] == "LLM_ARBITER_ENABLED"
        details = call_kwargs.kwargs["details"]
        assert details["flag_name"] == "LLM_ARBITER_ENABLED"
        assert details["new_value"] == "False"

    @patch("routes.feature_flags._redis_set_override", new_callable=AsyncMock, return_value=True)
    @patch("routes.feature_flags._redis_get_override", new_callable=AsyncMock, return_value=None)
    @patch("routes.feature_flags.audit_logger")
    def test_audit_event_not_logged_for_invalid_flag(self, mock_audit_logger, mock_get, mock_set, client):
        """PATCH with non-existent flag returns 404 and does NOT call audit_logger."""
        mock_audit_logger.log = AsyncMock()

        resp = client.patch(
            "/admin/feature-flags/TOTALLY_FAKE_FLAG_XYZ",
            json={"value": True},
        )
        assert resp.status_code == 404
        mock_audit_logger.log.assert_not_called()


class TestFeatureFlagsSecurity:
    """Test admin-only access control."""

    def test_list_requires_admin(self, unauth_client):
        """Should return 401 without authentication."""
        resp = unauth_client.get("/admin/feature-flags")
        assert resp.status_code in (401, 403)

    def test_update_requires_admin(self, unauth_client):
        """Should return 401 without authentication."""
        resp = unauth_client.patch(
            "/admin/feature-flags/LLM_ARBITER_ENABLED",
            json={"value": False},
        )
        assert resp.status_code in (401, 403)

    def test_reload_requires_admin(self, unauth_client):
        """Should return 401 without authentication."""
        resp = unauth_client.post("/admin/feature-flags/reload")
        assert resp.status_code in (401, 403)
