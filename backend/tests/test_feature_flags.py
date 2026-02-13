"""Tests for feature flags API (STORY-171, STORY-217).

Tests GET /api/features/me endpoint with feature flag retrieval,
plan-based capabilities, and billing-period-specific features.

STORY-217: features.py now uses cache.redis_cache (shared pool) instead of
per-request get_redis_client(). Tests updated to mock redis_cache.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock


class TestFeatureFlagsAPI:
    """Test feature flags API endpoint."""

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_get_features_annual_consultor_agil(self, mock_supabase, mock_redis_cache):
        """Test feature retrieval for annual Consultor Agil subscriber."""
        from routes.features import get_my_features

        user = {"id": "test-user-123", "email": "test@example.com"}

        # Mock redis_cache (cache miss)
        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock user subscription (annual Consultor Agil)
        subscription_data = {
            "plan_id": "consultor_agil",
            "billing_period": "annual",
        }
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock plan features (annual gets early_access + proactive_search)
        features_data = [
            {"feature_key": "early_access", "enabled": True, "metadata": {"description": "Beta features"}},
            {"feature_key": "proactive_search", "enabled": True, "metadata": {"description": "Auto alerts"}},
        ]
        sb_mock.table("plan_features").select().eq().eq().eq().execute.return_value = Mock(
            data=features_data
        )

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "consultor_agil"
        assert response.billing_period == "annual"
        assert len(response.features) == 2
        assert any(f.key == "early_access" for f in response.features)
        assert any(f.key == "proactive_search" for f in response.features)

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_get_features_monthly_consultor_agil_no_annual_features(self, mock_supabase, mock_redis_cache):
        """Test that monthly subscribers don't get annual-exclusive features."""
        from routes.features import get_my_features

        user = {"id": "test-user-456", "email": "test2@example.com"}

        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock user subscription (monthly Consultor Agil)
        subscription_data = {
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
        }
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock plan features (monthly gets NO annual-exclusive features)
        sb_mock.table("plan_features").select().eq().eq().eq().execute.return_value = Mock(
            data=[]  # No features for monthly billing
        )

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "consultor_agil"
        assert response.billing_period == "monthly"
        assert len(response.features) == 0  # No annual features

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_get_features_sala_guerra_annual_includes_ai_analysis(self, mock_supabase, mock_redis_cache):
        """Test that annual Sala de Guerra gets AI edital analysis feature."""
        from routes.features import get_my_features

        user = {"id": "test-user-789", "email": "test3@example.com"}

        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock user subscription (annual Sala de Guerra)
        subscription_data = {
            "plan_id": "sala_guerra",
            "billing_period": "annual",
        }
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        # Mock plan features (annual Sala de Guerra gets 3 features)
        features_data = [
            {"feature_key": "early_access", "enabled": True, "metadata": {}},
            {"feature_key": "proactive_search", "enabled": True, "metadata": {}},
            {"feature_key": "ai_edital_analysis", "enabled": True, "metadata": {"description": "GPT-4 analysis"}},
        ]
        sb_mock.table("plan_features").select().eq().eq().eq().execute.return_value = Mock(
            data=features_data
        )

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "sala_guerra"
        assert len(response.features) == 3
        assert any(f.key == "ai_edital_analysis" for f in response.features)

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_get_features_no_active_subscription_defaults_to_free_trial(self, mock_supabase, mock_redis_cache):
        """Test that users with no active subscription default to free_trial."""
        from routes.features import get_my_features

        user = {"id": "test-user-new", "email": "new@example.com"}

        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        # Mock empty subscription result
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[]
        )

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "free_trial"
        assert response.billing_period == "monthly"
        assert len(response.features) == 0  # Free trial has no special features


class TestFeatureCacheRedis:
    """Test Redis caching for feature flags (STORY-217: shared pool)."""

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_cache_hit_returns_cached_features(self, mock_supabase, mock_redis_cache):
        """Test that cache hit returns cached data without DB query."""
        from routes.features import get_my_features
        import json

        user = {"id": "test-user-cached", "email": "cached@example.com"}

        # Cached data
        cached_response = {
            "features": [{"key": "early_access", "enabled": True, "metadata": None}],
            "plan_id": "consultor_agil",
            "billing_period": "annual",
            "cached_at": "2026-02-07T12:00:00",
        }
        mock_redis_cache.get = AsyncMock(return_value=json.dumps(cached_response))

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "consultor_agil"
        assert response.billing_period == "annual"
        assert len(response.features) == 1

        # DB should NOT be queried (cache hit)
        mock_supabase.assert_not_called()

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_cache_miss_queries_db_and_caches_result(self, mock_supabase, mock_redis_cache):
        """Test that cache miss queries DB and stores result in Redis."""
        from routes.features import get_my_features

        user = {"id": "test-user-uncached", "email": "uncached@example.com"}

        # Cache miss
        mock_redis_cache.get = AsyncMock(return_value=None)
        mock_redis_cache.setex = AsyncMock()

        # Mock Supabase
        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {"plan_id": "maquina", "billing_period": "annual"}
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        features_data = [{"feature_key": "early_access", "enabled": True, "metadata": {}}]
        sb_mock.table("plan_features").select().eq().eq().eq().execute.return_value = Mock(
            data=features_data
        )

        response = await get_my_features(user)

        # Assertions
        assert response.plan_id == "maquina"

        # redis_cache.setex should be called to cache the result
        mock_redis_cache.setex.assert_called_once()

        # Verify TTL is 300 seconds (5 minutes)
        call_args = mock_redis_cache.setex.call_args
        assert call_args[0][1] == 300  # TTL

    @pytest.mark.asyncio
    @patch("routes.features.redis_cache")
    @patch("supabase_client.get_supabase")
    async def test_redis_unavailable_falls_back_to_db(self, mock_supabase, mock_redis_cache):
        """Test graceful degradation when Redis cache raises exception."""
        from routes.features import get_my_features

        user = {"id": "test-user-redis-down", "email": "redis-down@example.com"}

        # Mock redis_cache.get raising exception (connection failure)
        mock_redis_cache.get = AsyncMock(side_effect=Exception("Redis connection failed"))
        mock_redis_cache.setex = AsyncMock(side_effect=Exception("Redis connection failed"))

        # Mock Supabase
        sb_mock = MagicMock()
        mock_supabase.return_value = sb_mock

        subscription_data = {"plan_id": "consultor_agil", "billing_period": "monthly"}
        sb_mock.table("user_subscriptions").select().eq().eq().order().limit().execute.return_value = Mock(
            data=[subscription_data]
        )

        sb_mock.table("plan_features").select().eq().eq().eq().execute.return_value = Mock(
            data=[]
        )

        response = await get_my_features(user)

        # Should still work (graceful degradation)
        assert response.plan_id == "consultor_agil"
        assert response.billing_period == "monthly"
