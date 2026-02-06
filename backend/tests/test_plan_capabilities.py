"""Tests for plan capabilities system (STORY-165)."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from quota import (
    PLAN_CAPABILITIES,
    PLAN_NAMES,
    PLAN_PRICES,
    UPGRADE_SUGGESTIONS,
    PlanPriority,
    QuotaInfo,
    check_quota,
    get_current_month_key,
    get_quota_reset_date,
    get_monthly_quota_used,
    increment_monthly_quota,
)


class TestPlanCapabilities:
    """Test PLAN_CAPABILITIES constants."""

    def test_all_plans_have_required_fields(self):
        """All 4 plans must have all required capability fields."""
        required_fields = {
            "max_history_days",
            "allow_excel",
            "max_requests_per_month",
            "max_requests_per_min",
            "max_summary_tokens",
            "priority",
        }

        for plan_id, caps in PLAN_CAPABILITIES.items():
            assert set(caps.keys()) == required_fields, f"{plan_id} missing fields"

    def test_max_history_days_progression(self):
        """History days should progress: FREE < Consultor < Máquina < Sala."""
        assert PLAN_CAPABILITIES["free_trial"]["max_history_days"] == 7
        assert PLAN_CAPABILITIES["consultor_agil"]["max_history_days"] == 30
        assert PLAN_CAPABILITIES["maquina"]["max_history_days"] == 365
        assert PLAN_CAPABILITIES["sala_guerra"]["max_history_days"] == 1825

    def test_excel_only_allowed_for_premium_plans(self):
        """Excel export only available for Máquina and Sala de Guerra."""
        assert PLAN_CAPABILITIES["free_trial"]["allow_excel"] is False
        assert PLAN_CAPABILITIES["consultor_agil"]["allow_excel"] is False
        assert PLAN_CAPABILITIES["maquina"]["allow_excel"] is True
        assert PLAN_CAPABILITIES["sala_guerra"]["allow_excel"] is True

    def test_quota_limits_make_sense(self):
        """Monthly quotas should be reasonable and progressive."""
        # FREE trial should have limited quota (3 free searches)
        assert PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"] == 3

        # Paid plans should progress
        consultor = PLAN_CAPABILITIES["consultor_agil"]["max_requests_per_month"]
        maquina = PLAN_CAPABILITIES["maquina"]["max_requests_per_month"]
        sala = PLAN_CAPABILITIES["sala_guerra"]["max_requests_per_month"]

        assert consultor < maquina < sala
        assert consultor == 50
        assert maquina == 300
        assert sala == 1000

    def test_rate_limits_progressive(self):
        """Rate limits should increase with plan tier."""
        free = PLAN_CAPABILITIES["free_trial"]["max_requests_per_min"]
        consultor = PLAN_CAPABILITIES["consultor_agil"]["max_requests_per_min"]
        maquina = PLAN_CAPABILITIES["maquina"]["max_requests_per_min"]
        sala = PLAN_CAPABILITIES["sala_guerra"]["max_requests_per_min"]

        assert free < consultor < maquina < sala
        assert free == 2
        assert consultor == 10
        assert maquina == 30
        assert sala == 60

    def test_priority_levels_valid(self):
        """All priorities should be valid PlanPriority enum values."""
        valid_priorities = {p.value for p in PlanPriority}

        for plan_id, caps in PLAN_CAPABILITIES.items():
            assert caps["priority"] in valid_priorities, f"{plan_id} has invalid priority"

    def test_plan_names_exist_for_all_plans(self):
        """PLAN_NAMES should have entries for all plan IDs."""
        assert set(PLAN_NAMES.keys()) == set(PLAN_CAPABILITIES.keys())

    def test_plan_prices_exist_for_paid_plans(self):
        """PLAN_PRICES should have prices for all paid plans."""
        paid_plans = {"consultor_agil", "maquina", "sala_guerra"}
        assert set(PLAN_PRICES.keys()) == paid_plans

    def test_upgrade_suggestions_valid(self):
        """Upgrade suggestions should only point to valid plan IDs."""
        valid_plan_ids = set(PLAN_CAPABILITIES.keys())

        for category, suggestions in UPGRADE_SUGGESTIONS.items():
            for from_plan, to_plan in suggestions.items():
                assert from_plan in valid_plan_ids, f"Invalid source plan: {from_plan}"
                assert to_plan in valid_plan_ids, f"Invalid target plan: {to_plan}"


class TestMonthlyQuotaHelpers:
    """Test quota tracking helper functions."""

    def test_get_current_month_key_format(self):
        """Month key should be in YYYY-MM format."""
        key = get_current_month_key()
        assert len(key) == 7
        assert key[4] == "-"

        # Parse to validate format
        year, month = key.split("-")
        assert len(year) == 4
        assert len(month) == 2
        assert 1 <= int(month) <= 12

    def test_get_quota_reset_date(self):
        """Reset date should be 1st of next month."""
        reset_date = get_quota_reset_date()

        assert reset_date.day == 1
        assert reset_date.hour == 0
        assert reset_date.minute == 0
        assert reset_date.second == 0
        assert reset_date.tzinfo == timezone.utc

        # Should be in the future
        assert reset_date > datetime.now(timezone.utc)

    def test_get_quota_reset_date_handles_december(self):
        """Reset date should roll over to next year if current month is December."""
        with patch("quota.datetime") as mock_datetime:
            # Mock current date as December 15, 2025
            mock_datetime.utcnow.return_value = datetime(2025, 12, 15)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            reset_date = get_quota_reset_date()

            assert reset_date.year == 2026
            assert reset_date.month == 1
            assert reset_date.day == 1


class TestGetMonthlyQuotaUsed:
    """Test get_monthly_quota_used function."""

    @patch("supabase_client.get_supabase")
    def test_returns_zero_when_no_record_exists(self, mock_get_supabase):
        """Should return 0 if no quota record for current month."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock empty result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

        result = get_monthly_quota_used("user-123")

        assert result == 0

    @patch("supabase_client.get_supabase")
    def test_returns_searches_count_when_record_exists(self, mock_get_supabase):
        """Should return searches_count from database."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock quota record
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {"searches_count": 23}
        ]

        result = get_monthly_quota_used("user-123")

        assert result == 23

    @patch("supabase_client.get_supabase")
    def test_fails_open_on_database_error(self, mock_get_supabase):
        """Should return 0 on database errors (fail open)."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock database error
        mock_sb.table.return_value.select.return_value.eq.side_effect = Exception("DB error")

        result = get_monthly_quota_used("user-123")

        assert result == 0  # Fail open


class TestIncrementMonthlyQuota:
    """Test increment_monthly_quota function.

    Updated for Issue #189: Now uses atomic RPC function with fallback.
    """

    @patch("supabase_client.get_supabase")
    def test_increments_existing_quota_via_rpc(self, mock_get_supabase):
        """Should increment quota via atomic RPC function."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock successful RPC call
        mock_sb.rpc.return_value.execute.return_value.data = [
            {"new_count": 24, "was_at_limit": False, "previous_count": 23}
        ]

        result = increment_monthly_quota("user-123")

        assert result == 24

        # Verify RPC was called with atomic function
        mock_sb.rpc.assert_called_once()
        call_args = mock_sb.rpc.call_args
        assert call_args[0][0] == "increment_quota_atomic"

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_fallback_increments_existing_quota(self, mock_get_used, mock_get_supabase):
        """Should increment quota via fallback when RPC unavailable."""
        # RPC fails (function not available)
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb
        mock_sb.rpc.return_value.execute.side_effect = Exception("function does not exist")

        # Fallback: first call returns 23 (before), second returns 24 (after increment)
        mock_get_used.side_effect = [23, 24]

        result = increment_monthly_quota("user-123")

        assert result == 24

        # Verify upsert was called as fallback
        mock_sb.table.return_value.upsert.assert_called_once()

    @patch("supabase_client.get_supabase")
    def test_creates_new_record_via_rpc(self, mock_get_supabase):
        """Should create new record with count=1 via atomic RPC."""
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock RPC returning first increment
        mock_sb.rpc.return_value.execute.return_value.data = [
            {"new_count": 1, "was_at_limit": False, "previous_count": 0}
        ]

        result = increment_monthly_quota("user-123")

        assert result == 1


class TestCheckQuota:
    """Test check_quota function."""

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_free_trial_user_within_trial_period(self, mock_get_used, mock_get_supabase):
        """FREE trial user within trial period and under quota should be allowed."""
        mock_get_used.return_value = 1  # Under 3-search limit
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock subscription with future expiry
        future_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "free_trial",
                "expires_at": future_date,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "free_trial"
        assert result.quota_used == 1
        assert result.quota_remaining == 2  # 3 - 1 = 2 remaining
        assert result.trial_expires_at is not None

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_trial_expired_blocks_user(self, mock_get_used, mock_get_supabase):
        """Expired trial should block user."""
        mock_get_used.return_value = 5
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock expired trial
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "free_trial",
                "expires_at": past_date,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is False
        assert "Trial expirado" in result.error_message

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_consultor_agil_within_quota(self, mock_get_used, mock_get_supabase):
        """Consultor Ágil user within quota should be allowed."""
        mock_get_used.return_value = 23  # Under 50 limit
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "consultor_agil",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "consultor_agil"
        assert result.quota_used == 23
        assert result.quota_remaining == 27  # 50 - 23

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_quota_exhausted_blocks_user(self, mock_get_used, mock_get_supabase):
        """User who exhausted monthly quota should be blocked."""
        mock_get_used.return_value = 50  # At limit
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "consultor_agil",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is False
        assert "Limite de 50 buscas mensais atingido" in result.error_message
        assert result.quota_remaining == 0

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_maquina_plan_has_excel_enabled(self, mock_get_used, mock_get_supabase):
        """Máquina plan should have allow_excel=True."""
        mock_get_used.return_value = 100
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "maquina",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is True
        assert result.capabilities["allow_excel"] is True
        assert result.capabilities["max_history_days"] == 365

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_sala_guerra_highest_limits(self, mock_get_used, mock_get_supabase):
        """Sala de Guerra should have highest limits."""
        mock_get_used.return_value = 500
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "sala_guerra",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.allowed is True
        assert result.capabilities["max_history_days"] == 1825  # 5 years
        assert result.capabilities["max_requests_per_month"] == 1000
        assert result.capabilities["max_requests_per_min"] == 60
        assert result.capabilities["max_summary_tokens"] == 1000

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_fails_open_on_database_error(self, mock_get_used, mock_get_supabase):
        """Should fail open with free_trial on database errors."""
        mock_get_used.return_value = 0
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock database error
        mock_sb.table.return_value.select.side_effect = Exception("DB error")

        result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "free_trial"

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_no_subscription_defaults_to_free_trial(self, mock_get_used, mock_get_supabase):
        """User with no subscription should default to free_trial."""
        mock_get_used.return_value = 0
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # Mock empty subscription result
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        result = check_quota("user-123")

        assert result.plan_id == "free_trial"
        assert result.allowed is True


class TestPlanNameMapping:
    """Test PLAN_NAMES constants for correct display names."""

    def test_free_trial_display_name(self):
        """FREE trial should display as 'FREE Trial'."""
        assert PLAN_NAMES["free_trial"] == "FREE Trial"

    def test_consultor_agil_display_name(self):
        """Consultor Agil should display with accent."""
        assert PLAN_NAMES["consultor_agil"] == "Consultor Ágil"

    def test_maquina_display_name(self):
        """Maquina should display as 'Máquina'."""
        assert PLAN_NAMES["maquina"] == "Máquina"

    def test_sala_guerra_display_name(self):
        """Sala de Guerra should display correctly."""
        assert PLAN_NAMES["sala_guerra"] == "Sala de Guerra"

    def test_plan_names_matches_capabilities_keys(self):
        """All capability plan IDs must have a display name."""
        capability_plan_ids = set(PLAN_CAPABILITIES.keys())
        name_plan_ids = set(PLAN_NAMES.keys())
        assert capability_plan_ids == name_plan_ids

    def test_plan_names_not_empty(self):
        """All plan display names must be non-empty."""
        for plan_id, name in PLAN_NAMES.items():
            assert name, f"Plan {plan_id} has empty display name"
            assert len(name) >= 3, f"Plan {plan_id} display name too short"


class TestPlanPricing:
    """Test PLAN_PRICES constants for correct pricing display."""

    def test_consultor_agil_price(self):
        """Consultor Agil should have correct price."""
        assert PLAN_PRICES["consultor_agil"] == "R$ 297/mês"

    def test_maquina_price(self):
        """Maquina should have correct price."""
        assert PLAN_PRICES["maquina"] == "R$ 597/mês"

    def test_sala_guerra_price(self):
        """Sala de Guerra should have correct price."""
        assert PLAN_PRICES["sala_guerra"] == "R$ 1.497/mês"

    def test_free_trial_has_no_price(self):
        """FREE trial should not be in pricing (it's free)."""
        assert "free_trial" not in PLAN_PRICES

    def test_all_paid_plans_have_prices(self):
        """All paid plans must have prices."""
        paid_plans = {"consultor_agil", "maquina", "sala_guerra"}
        assert set(PLAN_PRICES.keys()) == paid_plans

    def test_prices_contain_currency_symbol(self):
        """All prices should contain R$ currency symbol."""
        for plan_id, price in PLAN_PRICES.items():
            assert "R$" in price, f"Plan {plan_id} price missing currency symbol"

    def test_prices_contain_period(self):
        """All prices should indicate billing period."""
        for plan_id, price in PLAN_PRICES.items():
            assert "/mês" in price or "/ano" in price, f"Plan {plan_id} price missing period"


class TestQuotaInfoPlanName:
    """Test QuotaInfo returns correct plan_name field."""

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_quota_info_returns_correct_plan_name(self, mock_get_used, mock_get_supabase):
        """check_quota should return correctly formatted plan_name."""
        mock_get_used.return_value = 10
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "consultor_agil",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.plan_id == "consultor_agil"
        assert result.plan_name == "Consultor Ágil"

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_quota_info_maquina_plan_name(self, mock_get_used, mock_get_supabase):
        """check_quota should return 'Máquina' for maquina plan."""
        mock_get_used.return_value = 50
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "sub-123",
                "plan_id": "maquina",
                "expires_at": None,
            }
        ]

        result = check_quota("user-123")

        assert result.plan_id == "maquina"
        assert result.plan_name == "Máquina"

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used")
    def test_quota_info_defaults_to_free_trial_name(self, mock_get_used, mock_get_supabase):
        """check_quota should default to 'FREE Trial' name for unknown plans."""
        mock_get_used.return_value = 0
        mock_sb = MagicMock()
        mock_get_supabase.return_value = mock_sb

        # No subscription
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

        result = check_quota("user-123")

        assert result.plan_name == "FREE Trial"
