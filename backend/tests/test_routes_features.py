"""Tests for routes.features — GET /api/features/me endpoint.

STORY-224 Track 4 (AC26): Feature flags route coverage with Redis caching.
"""

import json
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from auth import require_auth
from routes.features import router


MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}


def _create_client():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    return TestClient(app)


def _mock_sb():
    """Build a fluent-chainable Supabase mock."""
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.eq.return_value = sb
    sb.gte.return_value = sb
    sb.order.return_value = sb
    sb.limit.return_value = sb
    sb.single.return_value = sb
    sb.execute.return_value = Mock(data=[])
    return sb


# ============================================================================
# GET /api/features/me
# ============================================================================

class TestGetMyFeatures:

    @patch("routes.features.redis_cache")
    def test_cache_hit_returns_cached_data(self, mock_redis):
        """When Redis has cached data, return it directly without DB query."""
        cached_response = {
            "features": [
                {"key": "excel_export", "enabled": True, "metadata": None},
                {"key": "ai_summary", "enabled": True, "metadata": {"max_tokens": 500}},
            ],
            "plan_id": "consultor_agil",
            "billing_period": "monthly",
            "cached_at": "2026-02-01T10:00:00+00:00",
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_response))

        client = _create_client()
        resp = client.get("/api/features/me")

        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"] == "consultor_agil"
        assert len(body["features"]) == 2
        assert body["cached_at"] == "2026-02-01T10:00:00+00:00"
        # Should not call setex since it was a cache hit
        mock_redis.setex.assert_not_called()

    @patch("routes.features.redis_cache")
    @patch("routes.features.fetch_features_from_db")
    def test_cache_miss_fetches_from_db(self, mock_fetch_db, mock_redis):
        """When Redis returns None, fetch from DB and cache."""
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        from routes.features import UserFeaturesResponse, FeatureInfo
        db_response = UserFeaturesResponse(
            features=[
                FeatureInfo(key="excel_export", enabled=True, metadata=None),
            ],
            plan_id="consultor_agil",
            billing_period="monthly",
            cached_at=None,
        )
        mock_fetch_db.return_value = db_response

        client = _create_client()
        resp = client.get("/api/features/me")

        assert resp.status_code == 200
        body = resp.json()
        assert body["plan_id"] == "consultor_agil"
        assert len(body["features"]) == 1
        # cached_at should be set after cache write
        assert body["cached_at"] is not None
        # Should write to cache
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "features:user-123-uuid"
        assert call_args[0][1] == 300  # 5-minute TTL

    @patch("routes.features.redis_cache")
    @patch("routes.features.fetch_features_from_db")
    def test_cache_read_failure_falls_through_to_db(self, mock_fetch_db, mock_redis):
        """If Redis get() raises, should still fetch from DB."""
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection refused"))
        mock_redis.setex = AsyncMock()

        from routes.features import UserFeaturesResponse
        mock_fetch_db.return_value = UserFeaturesResponse(
            features=[],
            plan_id="free_trial",
            billing_period="monthly",
            cached_at=None,
        )

        client = _create_client()
        resp = client.get("/api/features/me")

        assert resp.status_code == 200
        assert resp.json()["plan_id"] == "free_trial"
        mock_fetch_db.assert_called_once()

    @patch("routes.features.redis_cache")
    @patch("routes.features.fetch_features_from_db")
    def test_cache_write_failure_non_critical(self, mock_fetch_db, mock_redis):
        """If Redis setex() raises, endpoint should still succeed."""
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis write failed"))

        from routes.features import UserFeaturesResponse
        mock_fetch_db.return_value = UserFeaturesResponse(
            features=[],
            plan_id="free_trial",
            billing_period="monthly",
            cached_at=None,
        )

        client = _create_client()
        resp = client.get("/api/features/me")

        assert resp.status_code == 200  # Should not fail


# ============================================================================
# fetch_features_from_db — multi-layer fallback tests
# ============================================================================

class TestFetchFeaturesFromDB:

    @patch("supabase_client.get_supabase")
    def test_active_subscription_primary_source(self, mock_get_sb):
        """Layer 1: Active subscription found — use its plan_id."""
        sb = _mock_sb()
        sub_data = [{"plan_id": "maquina", "billing_period": "annual", "expires_at": None}]
        features_data = [
            {"feature_key": "excel_export", "enabled": True, "metadata": None},
            {"feature_key": "unlimited_searches", "enabled": True, "metadata": None},
        ]
        sb.execute.side_effect = [
            Mock(data=sub_data),       # subscription query
            Mock(data=features_data),  # plan_features query
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "maquina"
        assert result.billing_period == "annual"
        assert len(result.features) == 2

    @patch("routes.features.get_plan_from_profile", return_value=None)
    @patch("supabase_client.get_supabase")
    def test_grace_period_fallback(self, mock_get_sb, mock_profile):
        """Layer 2: No active sub, but recently-expired sub within grace period."""
        sb = _mock_sb()
        # First query: no active subscription
        # Second query: grace period subscription found
        grace_sub = [{"plan_id": "consultor_agil", "billing_period": "monthly", "expires_at": "2026-02-10T00:00:00+00:00"}]
        features_data = [{"feature_key": "excel_export", "enabled": True, "metadata": None}]
        sb.execute.side_effect = [
            Mock(data=[]),          # no active sub
            Mock(data=grace_sub),   # grace period sub
            Mock(data=features_data),
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "consultor_agil"

    @patch("routes.features.get_plan_from_profile", return_value="maquina")
    @patch("supabase_client.get_supabase")
    def test_profile_fallback(self, mock_get_sb, mock_profile):
        """Layer 3: No active or grace sub — fall back to profiles.plan_type."""
        sb = _mock_sb()
        features_data = [{"feature_key": "excel_export", "enabled": True, "metadata": None}]
        sb.execute.side_effect = [
            Mock(data=[]),  # no active sub
            Mock(data=[]),  # no grace period sub
            Mock(data=features_data),
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "maquina"
        assert result.billing_period == "monthly"  # Default for profile fallback

    @patch("routes.features.get_plan_from_profile", return_value=None)
    @patch("supabase_client.get_supabase")
    def test_free_trial_last_resort(self, mock_get_sb, mock_profile):
        """Layer 4: Nothing found — defaults to free_trial."""
        sb = _mock_sb()
        features_data = []
        sb.execute.side_effect = [
            Mock(data=[]),  # no active sub
            Mock(data=[]),  # no grace period sub
            Mock(data=features_data),
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "free_trial"
        assert result.billing_period == "monthly"
        assert result.features == []

    @patch("routes.features.get_plan_from_profile", return_value="free_trial")
    @patch("supabase_client.get_supabase")
    def test_profile_free_trial_skipped_to_layer4(self, mock_get_sb, mock_profile):
        """Layer 3 returns 'free_trial' — skip it and fall through to Layer 4."""
        sb = _mock_sb()
        sb.execute.side_effect = [
            Mock(data=[]),  # no active sub
            Mock(data=[]),  # no grace period sub
            Mock(data=[]),  # no features for free_trial
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "free_trial"

    @patch("routes.features.get_plan_from_profile", return_value=None)
    @patch("supabase_client.get_supabase")
    def test_plan_features_query_failure_returns_empty(self, mock_get_sb, mock_profile):
        """If plan_features query fails, return empty features (fail safe)."""
        sb = _mock_sb()
        sub_data = [{"plan_id": "consultor_agil", "billing_period": "monthly", "expires_at": None}]
        sb.execute.side_effect = [
            Mock(data=sub_data),    # subscription found
            Exception("DB error"),  # plan_features query fails
        ]
        mock_get_sb.return_value = sb

        from routes.features import fetch_features_from_db
        result = fetch_features_from_db("user-123-uuid")

        assert result.plan_id == "consultor_agil"
        assert result.features == []
