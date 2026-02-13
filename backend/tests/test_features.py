"""Tests for features API multi-layer plan fallback (STORY-223 Track 2).

Tests AC6-AC11: Align /api/features/me with multi-layer plan fallback strategy.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from routes.features import fetch_features_from_db, UserFeaturesResponse


class TestFeaturesFallbackAC6AC7:
    """Test multi-layer fallback in fetch_features_from_db (AC6-AC7)."""

    @patch("supabase_client.get_supabase")
    def test_ac8_active_subscription_returns_correct_plan(self, mock_get_supabase):
        """AC8: Active subscription → correct plan features."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock active subscription
        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "plan_id": "maquina",
                "billing_period": "monthly",
                "expires_at": future_date,
            }
        ]

        # Mock plan_features result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"feature_key": "excel_export", "enabled": True, "metadata": None},
            {"feature_key": "advanced_filters", "enabled": True, "metadata": None},
        ]

        result = fetch_features_from_db("user-123")

        assert result.plan_id == "maquina"
        assert result.billing_period == "monthly"
        assert len(result.features) == 2
        assert result.features[0].key == "excel_export"
        assert result.features[0].enabled is True

    @patch("supabase_client.get_supabase")
    def test_ac9_expired_subscription_within_grace_returns_plan(self, mock_get_supabase):
        """AC9: Expired subscription within grace period → correct plan features (not free_trial)."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock no active subscription
        mock_table_chain_active = mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute
        mock_table_chain_active.return_value.data = []

        # Mock grace-period subscription (expired 2 days ago, within 3-day grace)
        expired_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        mock_table_chain_grace = mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute
        mock_table_chain_grace.return_value.data = [
            {
                "plan_id": "consultor_agil",
                "billing_period": "monthly",
                "expires_at": expired_date,
            }
        ]

        # Mock plan_features result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"feature_key": "basic_search", "enabled": True, "metadata": None},
        ]

        result = fetch_features_from_db("user-123")

        assert result.plan_id == "consultor_agil"
        assert result.billing_period == "monthly"
        assert len(result.features) == 1
        assert result.features[0].key == "basic_search"

    @patch("routes.features.get_plan_from_profile")
    @patch("supabase_client.get_supabase")
    def test_ac10_expired_subscription_and_valid_profile_plan(self, mock_get_supabase, mock_get_plan_from_profile):
        """AC10: Expired subscription + valid profile plan → profile plan features."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock no active subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock no grace-period subscription (expired > 3 days ago)
        mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock profiles.plan_type fallback
        mock_get_plan_from_profile.return_value = "maquina"

        # Mock plan_features result for maquina
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"feature_key": "excel_export", "enabled": True, "metadata": None},
        ]

        result = fetch_features_from_db("user-456")

        assert result.plan_id == "maquina"
        assert result.billing_period == "monthly"  # Default for profile fallback
        assert len(result.features) == 1
        mock_get_plan_from_profile.assert_called_once_with("user-456", mock_sb)

    @patch("routes.features.get_plan_from_profile")
    @patch("supabase_client.get_supabase")
    def test_ac11_no_subscription_no_profile_returns_free_trial(self, mock_get_supabase, mock_get_plan_from_profile):
        """AC11: No subscription + no profile plan → free_trial."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock no active subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock no grace-period subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock no profile plan (returns None or free_trial)
        mock_get_plan_from_profile.return_value = None

        # Mock plan_features result for free_trial (empty or none)
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = fetch_features_from_db("user-789")

        assert result.plan_id == "free_trial"
        assert result.billing_period == "monthly"
        assert len(result.features) == 0

    @patch("routes.features.get_plan_from_profile")
    @patch("supabase_client.get_supabase")
    def test_database_error_falls_back_to_profile(self, mock_get_supabase, mock_get_plan_from_profile):
        """Database error during subscription lookup should use profile fallback."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock database error
        mock_sb.table.return_value.select.side_effect = Exception("DB connection timeout")

        # Mock profiles.plan_type fallback
        mock_get_plan_from_profile.return_value = "consultor_agil"

        # Mock plan_features result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"feature_key": "basic_search", "enabled": True, "metadata": None},
        ]

        result = fetch_features_from_db("user-error")

        assert result.plan_id == "consultor_agil"
        mock_get_plan_from_profile.assert_called_once()


class TestFeaturesGracePeriodAC7:
    """Test grace period (3 days) is respected in features endpoint (AC7)."""

    @patch("quota.SUBSCRIPTION_GRACE_DAYS", 3)
    @patch("supabase_client.get_supabase")
    def test_grace_period_boundary_exactly_3_days(self, mock_get_supabase):
        """Subscription expired exactly 3 days ago should still be used."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock no active subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock subscription expired exactly 3 days ago
        expired_date = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "plan_id": "sala_guerra",
                "billing_period": "yearly",
                "expires_at": expired_date,
            }
        ]

        # Mock plan_features
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = fetch_features_from_db("user-boundary")

        assert result.plan_id == "sala_guerra"
        assert result.billing_period == "yearly"

    @patch("routes.features.get_plan_from_profile")
    @patch("routes.features.SUBSCRIPTION_GRACE_DAYS", 3)
    @patch("supabase_client.get_supabase")
    def test_expired_beyond_grace_uses_profile(self, mock_get_supabase, mock_get_plan_from_profile):
        """Subscription expired > 3 days ago should fall back to profile."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock no active subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock no grace-period subscription (expired 4 days ago, beyond 3-day grace)
        mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        # Mock profile fallback
        mock_get_plan_from_profile.return_value = "maquina"

        # Mock plan_features
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = fetch_features_from_db("user-expired-beyond")

        assert result.plan_id == "maquina"
        mock_get_plan_from_profile.assert_called_once()
