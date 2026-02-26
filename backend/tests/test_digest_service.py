"""Tests for STORY-278 AC2: Digest Service.

Tests build_digest_for_user(), get_digest_eligible_users(), mark_digest_sent(),
_is_digest_due(), and _query_recent_opportunities().
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace


# ============================================================================
# _is_digest_due() tests
# ============================================================================

class TestIsDigestDue:
    """Test the _is_digest_due helper function."""

    def test_disabled_prefs_not_due(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"enabled": False, "frequency": "daily"}) is False

    def test_off_frequency_not_due(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"enabled": True, "frequency": "off"}) is False

    def test_never_sent_is_due(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"enabled": True, "frequency": "daily", "last_digest_sent_at": None}) is True

    def test_daily_recently_sent_not_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(hours=5)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "daily", "last_digest_sent_at": recent}) is False

    def test_daily_old_sent_is_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        old = (now - timedelta(hours=25)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "daily", "last_digest_sent_at": old}) is True

    def test_twice_weekly_3_days_ago_is_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=4)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "twice_weekly", "last_digest_sent_at": old}) is True

    def test_twice_weekly_1_day_ago_not_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=1)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "twice_weekly", "last_digest_sent_at": recent}) is False

    def test_weekly_7_days_ago_is_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=7)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "weekly", "last_digest_sent_at": old}) is True

    def test_weekly_2_days_ago_not_due(self):
        from services.digest_service import _is_digest_due
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(days=2)).isoformat()
        assert _is_digest_due({"enabled": True, "frequency": "weekly", "last_digest_sent_at": recent}) is False

    def test_invalid_timestamp_is_due(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"enabled": True, "frequency": "daily", "last_digest_sent_at": "invalid"}) is True

    def test_missing_enabled_defaults_true(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"frequency": "daily", "last_digest_sent_at": None}) is True

    def test_unknown_frequency_not_due(self):
        from services.digest_service import _is_digest_due
        assert _is_digest_due({"enabled": True, "frequency": "hourly", "last_digest_sent_at": None}) is False


# ============================================================================
# build_digest_for_user() tests
# ============================================================================

class TestBuildDigestForUser:
    """Test digest building for a single user."""

    @pytest.mark.asyncio
    async def test_returns_none_when_not_due(self):
        from services.digest_service import build_digest_for_user

        mock_db = MagicMock()
        # Alert prefs: recently sent, not due
        now = datetime.now(timezone.utc)
        recent = (now - timedelta(hours=2)).isoformat()

        prefs_result = MagicMock()
        prefs_result.data = {
            "frequency": "daily",
            "enabled": True,
            "last_digest_sent_at": recent,
        }

        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = prefs_result

        result = await build_digest_for_user("user-123", db=mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_profile(self):
        from services.digest_service import build_digest_for_user

        mock_db = MagicMock()

        # Alert prefs: due (never sent)
        prefs_result = MagicMock()
        prefs_result.data = {
            "frequency": "daily",
            "enabled": True,
            "last_digest_sent_at": None,
        }

        # Profile: None
        profile_result = MagicMock()
        profile_result.data = {}

        call_count = [0]
        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "alert_preferences":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = prefs_result
            elif name == "profiles":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.side_effect = Exception("no row")
            elif name == "search_results_cache":
                cache_result = MagicMock()
                cache_result.data = []
                mock_table.select.return_value.order.return_value.limit.return_value.execute.return_value = cache_result
                mock_table.select.return_value.order.return_value.limit.return_value.gte.return_value.execute.return_value = cache_result
            return mock_table

        mock_db.table.side_effect = table_side_effect

        result = await build_digest_for_user("user-123", db=mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_builds_digest_with_opportunities(self):
        from services.digest_service import build_digest_for_user

        mock_db = MagicMock()

        # Alert prefs: due
        prefs_result = MagicMock()
        prefs_result.data = {
            "frequency": "daily",
            "enabled": True,
            "last_digest_sent_at": None,
        }

        # Profile with context
        profile_result = MagicMock()
        profile_result.data = {
            "context_data": {
                "setor_id": "vestuario",
                "ufs_atuacao": ["SP", "RJ"],
            }
        }

        # Cache with results
        cache_result = MagicMock()
        cache_result.data = [
            {
                "results": [
                    {
                        "objetoCompra": "Uniformes escolares",
                        "nomeOrgao": "Prefeitura SP",
                        "valorTotalEstimado": 500000,
                        "uf": "SP",
                        "viability_score": 0.8,
                        "dataPublicacaoPncp": "2026-02-25",
                    },
                    {
                        "objetoCompra": "Camisetas",
                        "nomeOrgao": "Prefeitura RJ",
                        "valorTotalEstimado": 200000,
                        "uf": "RJ",
                        "viability_score": 0.5,
                    },
                ],
                "search_params": {"setor_id": "vestuario"},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

        # User data
        mock_user_data = MagicMock()
        mock_user_data.user.email = "test@example.com"

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "alert_preferences":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = prefs_result
            elif name == "profiles":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result
            elif name == "search_results_cache":
                mock_table.select.return_value.order.return_value.limit.return_value.gte.return_value.execute.return_value = cache_result
            return mock_table

        mock_db.table.side_effect = table_side_effect
        mock_db.auth.admin.get_user_by_id.return_value = mock_user_data

        result = await build_digest_for_user("user-123", db=mock_db, max_items=10)

        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["user_name"] == "test"
        assert len(result["opportunities"]) == 2
        assert result["stats"]["total_novas"] == 2
        assert result["stats"]["total_valor"] == 700000

    @pytest.mark.asyncio
    async def test_returns_none_when_no_email(self):
        from services.digest_service import build_digest_for_user

        mock_db = MagicMock()

        prefs_result = MagicMock()
        prefs_result.data = {
            "frequency": "daily", "enabled": True, "last_digest_sent_at": None,
        }

        profile_result = MagicMock()
        profile_result.data = {"context_data": {"setor_id": "software"}}

        cache_result = MagicMock()
        cache_result.data = []

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "alert_preferences":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = prefs_result
            elif name == "profiles":
                mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result
            elif name == "search_results_cache":
                mock_table.select.return_value.order.return_value.limit.return_value.gte.return_value.execute.return_value = cache_result
            return mock_table

        mock_db.table.side_effect = table_side_effect
        mock_db.auth.admin.get_user_by_id.side_effect = Exception("no user")

        result = await build_digest_for_user("user-123", db=mock_db)
        assert result is None


# ============================================================================
# get_digest_eligible_users() tests
# ============================================================================

class TestGetDigestEligibleUsers:

    @pytest.mark.asyncio
    async def test_returns_eligible_users(self):
        from services.digest_service import get_digest_eligible_users

        mock_db = MagicMock()
        result = MagicMock()
        result.data = [
            {"user_id": "u1", "frequency": "daily", "enabled": True, "last_digest_sent_at": None},
            {"user_id": "u2", "frequency": "daily", "enabled": True,
             "last_digest_sent_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()},
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = result

        eligible = await get_digest_eligible_users(mock_db)
        assert len(eligible) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        from services.digest_service import get_digest_eligible_users

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.side_effect = Exception("DB error")

        eligible = await get_digest_eligible_users(mock_db)
        assert eligible == []

    @pytest.mark.asyncio
    async def test_filters_not_due_users(self):
        from services.digest_service import get_digest_eligible_users

        mock_db = MagicMock()
        now = datetime.now(timezone.utc)
        result = MagicMock()
        result.data = [
            {"user_id": "u1", "frequency": "daily", "enabled": True, "last_digest_sent_at": None},
            {"user_id": "u2", "frequency": "daily", "enabled": True,
             "last_digest_sent_at": (now - timedelta(hours=2)).isoformat()},  # not due
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = result

        eligible = await get_digest_eligible_users(mock_db)
        assert len(eligible) == 1
        assert eligible[0]["user_id"] == "u1"


# ============================================================================
# mark_digest_sent() tests
# ============================================================================

class TestMarkDigestSent:

    @pytest.mark.asyncio
    async def test_updates_last_sent(self):
        from services.digest_service import mark_digest_sent

        mock_db = MagicMock()
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        await mark_digest_sent("user-123", db=mock_db)

        mock_db.table.assert_called_with("alert_preferences")
        mock_db.table.return_value.update.assert_called_once()
        call_args = mock_db.table.return_value.update.call_args[0][0]
        assert "last_digest_sent_at" in call_args

    @pytest.mark.asyncio
    async def test_handles_db_error_gracefully(self):
        from services.digest_service import mark_digest_sent

        mock_db = MagicMock()
        mock_db.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception("DB error")

        # Should not raise
        await mark_digest_sent("user-123", db=mock_db)
