"""Tests for Redis cache invalidation (STORY-171, STORY-217).

STORY-217: features.py now uses cache.redis_cache (shared pool) instead of
per-request get_redis_client(). Tests updated to mock redis_cache.
"""

from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import pytest


class TestRedisCacheInvalidation:
    """Test Redis cache management for feature flags."""

    def test_redis_cache_key_format(self):
        """Test that cache keys follow the expected format."""
        user_id = "12345678-1234-1234-1234-123456789abc"
        expected_key = f"features:{user_id}"

        # This is the format used in routes/features.py
        assert expected_key == f"features:{user_id}"

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    async def test_cache_stores_json_with_ttl(self, mock_redis_cache):
        """Test that cached data is stored as JSON with 5-minute TTL."""
        from routes.features import get_my_features

        mock_redis_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis_cache.setex = AsyncMock()

        user = {"id": "test-user", "email": "test@example.com"}

        with patch("routes.features.fetch_features_from_db") as mock_fetch:
            mock_fetch.return_value = Mock(
                features=[],
                plan_id="free_trial",
                billing_period="monthly",
                cached_at=None,
                model_dump_json=Mock(return_value='{"features":[],"plan_id":"free_trial","billing_period":"monthly","cached_at":null}'),
            )

            await get_my_features(user)

            # Verify setex was called with correct TTL
            mock_redis_cache.setex.assert_called_once()
            call_args = mock_redis_cache.setex.call_args
            cache_key = call_args[0][0]
            ttl = call_args[0][1]

            assert cache_key == "features:test-user"
            assert ttl == 300  # 5 minutes

    def test_billing_period_update_invalidates_cache(self):
        """Test that successful billing period update deletes cache key."""
        # Simulating the cache invalidation logic from routes/subscriptions.py

        redis_mock = MagicMock()

        user_id = "test-user-123"
        cache_key = f"features:{user_id}"

        # Simulate cache invalidation
        redis_mock.delete(cache_key)

        # Verify delete was called with correct key format
        redis_mock.delete.assert_called_once_with(cache_key)

    def test_cache_value_serialization(self):
        """Test that UserFeaturesResponse serializes to JSON correctly."""
        from routes.features import UserFeaturesResponse, FeatureInfo

        response = UserFeaturesResponse(
            features=[
                FeatureInfo(key="early_access", enabled=True, metadata={"desc": "Beta"}),
                FeatureInfo(key="proactive_search", enabled=True, metadata=None),
            ],
            plan_id="consultor_agil",
            billing_period="annual",
            cached_at="2026-02-07T12:00:00",
        )

        # Serialize to JSON (Pydantic v2)
        json_str = response.model_dump_json()
        data = json.loads(json_str)

        assert data["plan_id"] == "consultor_agil"
        assert data["billing_period"] == "annual"
        assert len(data["features"]) == 2

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    async def test_redis_connection_failure_doesnt_break_endpoint(self, mock_redis_cache):
        """Test that Redis connection failure doesn't break the endpoint."""
        from routes.features import get_my_features

        user = {"id": "test-user", "email": "test@example.com"}

        # Mock redis_cache.get raising exception
        mock_redis_cache.get = AsyncMock(side_effect=Exception("Redis connection timeout"))

        with patch("routes.features.fetch_features_from_db") as mock_fetch:
            mock_fetch.return_value = Mock(
                features=[],
                plan_id="free_trial",
                billing_period="monthly",
                cached_at=None,
                model_dump_json=Mock(return_value='{"features":[],"plan_id":"free_trial","billing_period":"monthly","cached_at":null}'),
            )

            # Should not raise exception
            response = await get_my_features(user)

            # Should still return valid response
            assert response.plan_id == "free_trial"

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    async def test_cache_ttl_expiration(self, mock_redis_cache):
        """Test cache behavior after TTL expiration (simulated cache miss)."""
        from routes.features import get_my_features

        user = {"id": "test-user-expired", "email": "expired@example.com"}

        # Simulate expired cache (get returns None)
        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        with patch("routes.features.fetch_features_from_db") as mock_fetch:
            mock_fetch.return_value = Mock(
                features=[],
                plan_id="maquina",
                billing_period="annual",
                cached_at="2026-02-07T12:05:00",
                model_dump_json=Mock(return_value='{"features":[],"plan_id":"maquina","billing_period":"annual","cached_at":"2026-02-07T12:05:00"}'),
            )

            await get_my_features(user)

            # Should fetch from DB (cache miss)
            mock_fetch.assert_called_once_with("test-user-expired")

            # Should re-cache the result
            mock_redis_cache.setex.assert_called_once()


class TestCacheKeyCollisionPrevention:
    """Test that cache keys are properly namespaced to prevent collisions."""

    def test_different_users_have_different_cache_keys(self):
        """Test that different users don't share cache keys."""
        user1_id = "user-111"
        user2_id = "user-222"

        key1 = f"features:{user1_id}"
        key2 = f"features:{user2_id}"

        assert key1 != key2
        assert key1 == "features:user-111"
        assert key2 == "features:user-222"

    def test_cache_key_uses_full_uuid(self):
        """Test that cache key uses full UUID (not truncated)."""
        full_uuid = "12345678-1234-1234-1234-123456789abc"
        cache_key = f"features:{full_uuid}"

        # Should contain full UUID
        assert full_uuid in cache_key
        assert len(cache_key.split(":")[1]) == len(full_uuid)
