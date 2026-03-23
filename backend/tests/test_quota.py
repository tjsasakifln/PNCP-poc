"""Tests for quota management module (quota.py).

Tests search credit checking, decrementing, and search session saving.
Covers all plan types: free_trial, consultor_agil, maquina, sala_guerra.
Uses mocked Supabase client to avoid external API calls.

Updated for STORY-165: New pricing model with capabilities system.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta


class TestQuotaExceededError:
    """Test suite for QuotaExceededError exception."""

    def test_quota_exceeded_error_is_exception(self):
        """QuotaExceededError should be a proper Exception subclass."""
        from quota import QuotaExceededError

        assert issubclass(QuotaExceededError, Exception)

    def test_quota_exceeded_error_message(self):
        """QuotaExceededError should preserve error message."""
        from quota import QuotaExceededError

        error = QuotaExceededError("Custom quota message")
        assert str(error) == "Custom quota message"


class TestPlanCapabilities:
    """Test suite for plan capabilities definitions (STORY-165)."""

    def test_all_plans_are_defined(self):
        """All four pricing tiers should be defined."""
        from quota import PLAN_CAPABILITIES

        expected_plans = ["free_trial", "consultor_agil", "maquina", "sala_guerra"]
        assert all(plan in PLAN_CAPABILITIES for plan in expected_plans)

    def test_free_trial_capabilities(self):
        """STORY-264 AC1-AC3: FREE Trial should have full product capabilities."""
        from quota import PLAN_CAPABILITIES

        caps = PLAN_CAPABILITIES["free_trial"]
        assert caps["max_history_days"] == 365  # GTM-003: 1 year
        assert caps["allow_excel"] is True  # GTM-003: Full product
        assert caps["allow_pipeline"] is True  # GTM-003: Full product
        assert caps["max_requests_per_month"] == 1000  # STORY-264 AC1: Full access
        assert caps["max_requests_per_min"] == 2  # STORY-264 AC2: Anti-abuse kept
        assert caps["max_summary_tokens"] == 10000  # GTM-003: Full AI
        assert caps["priority"] == "normal"  # GTM-003: Normal speed

    def test_consultor_agil_capabilities(self):
        """Consultor Ágil should have 30-day history, no Excel."""
        from quota import PLAN_CAPABILITIES

        caps = PLAN_CAPABILITIES["consultor_agil"]
        assert caps["max_history_days"] == 30
        assert caps["allow_excel"] is False
        assert caps["max_requests_per_month"] == 50
        assert caps["max_requests_per_min"] == 10
        assert caps["max_summary_tokens"] == 200
        assert caps["priority"] == "normal"

    def test_maquina_capabilities(self):
        """Máquina should have 1-year history, Excel enabled."""
        from quota import PLAN_CAPABILITIES

        caps = PLAN_CAPABILITIES["maquina"]
        assert caps["max_history_days"] == 365
        assert caps["allow_excel"] is True
        assert caps["max_requests_per_month"] == 300
        assert caps["max_requests_per_min"] == 30
        assert caps["max_summary_tokens"] == 500
        assert caps["priority"] == "high"

    def test_sala_guerra_capabilities(self):
        """Sala de Guerra should have 5-year history, max capabilities."""
        from quota import PLAN_CAPABILITIES

        caps = PLAN_CAPABILITIES["sala_guerra"]
        assert caps["max_history_days"] == 1825  # 5 years
        assert caps["allow_excel"] is True
        assert caps["max_requests_per_month"] == 1000
        assert caps["max_requests_per_min"] == 60
        assert caps["max_summary_tokens"] == 10000
        assert caps["priority"] == "critical"

    def test_plan_names_are_defined(self):
        """All plan display names should be defined."""
        from quota import PLAN_NAMES

        assert PLAN_NAMES["free_trial"] == "FREE Trial"
        assert PLAN_NAMES["consultor_agil"] == "Consultor Ágil (legacy)"
        assert PLAN_NAMES["maquina"] == "Máquina (legacy)"
        assert PLAN_NAMES["sala_guerra"] == "Sala de Guerra (legacy)"
        assert PLAN_NAMES["smartlic_pro"] == "SmartLic Pro"

    def test_upgrade_suggestions_are_valid(self):
        """Upgrade suggestions should point to valid plans."""
        from quota import UPGRADE_SUGGESTIONS, PLAN_CAPABILITIES

        for feature, suggestions in UPGRADE_SUGGESTIONS.items():
            for from_plan, to_plan in suggestions.items():
                assert to_plan in PLAN_CAPABILITIES, f"Invalid upgrade: {from_plan} → {to_plan}"


class TestQuotaInfo:
    """Test suite for QuotaInfo Pydantic model."""

    def test_quota_info_creation(self):
        """QuotaInfo should be created with all required fields."""
        from quota import QuotaInfo

        info = QuotaInfo(
            allowed=True,
            plan_id="maquina",
            plan_name="Máquina",
            capabilities={"max_history_days": 365, "allow_excel": True},
            quota_used=10,
            quota_remaining=290,
            quota_reset_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            trial_expires_at=None,
            error_message=None,
        )

        assert info.allowed is True
        assert info.plan_id == "maquina"
        assert info.quota_remaining == 290

    def test_quota_info_with_error(self):
        """QuotaInfo should capture error messages for denied access."""
        from quota import QuotaInfo

        info = QuotaInfo(
            allowed=False,
            plan_id="consultor_agil",
            plan_name="Consultor Ágil",
            capabilities={},
            quota_used=50,
            quota_remaining=0,
            quota_reset_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            error_message="Você atingiu 50 análises este mês.",
        )

        assert info.allowed is False
        assert "50 análises" in info.error_message


class TestCheckQuotaFreeTrial:
    """Test suite for check_quota with free trial users (no subscription)."""

    def test_free_trial_with_searches_remaining(self):
        """Should return allowed=True for free trial user with quota remaining."""
        from quota import check_quota

        mock_supabase = Mock()

        # No active subscription → defaults to free_trial
        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # Monthly quota: 1 search used (virtually unlimited for free trial)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 1}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "free_trial"
        assert result.plan_name == "FREE Trial"
        assert result.quota_remaining > 0

    def test_free_trial_with_zero_searches_used(self):
        """Should return full quota for free trial user with no searches."""
        from quota import check_quota, PLAN_CAPABILITIES

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # No monthly quota record = 0 searches
        monthly_result = Mock()
        monthly_result.data = []
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.quota_used == 0
        # STORY-264: Free trial has full access (1000 searches same as smartlic_pro)
        assert result.quota_remaining == PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"]
        assert result.quota_remaining == 1000

    def test_free_trial_capabilities_applied(self):
        """GTM-003: Free trial should have full product capabilities."""
        from quota import check_quota

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        monthly_result = Mock()
        monthly_result.data = []
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.capabilities["max_history_days"] == 365
        assert result.capabilities["allow_excel"] is True
        assert result.capabilities["max_summary_tokens"] == 10000


class TestFreeTrialFullAccess:
    """STORY-264: Verify free trial has full access (1000 searches)."""

    def test_trial_with_50_searches_not_blocked(self):
        """STORY-264 AC12: Trial user with 50 searches is NOT blocked (regression guard)."""
        from quota import check_quota

        mock_supabase = Mock()

        # No active subscription → defaults to free_trial
        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 50 searches used (old limit was 3 — must NOT block now)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 50}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "free_trial"
        assert result.quota_used == 50
        assert result.quota_remaining == 950  # 1000 - 50

    def test_expired_trial_still_blocks(self):
        """STORY-264 AC13: Expired trial blocks regardless of remaining searches."""
        from quota import check_quota

        mock_supabase = Mock()

        # Active subscription with plan_id=free_trial but EXPIRED
        past_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-trial",
            "plan_id": "free_trial",
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # Only 1 search used (plenty remaining under 1000 limit)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 1}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is False
        assert "expir" in (result.error_message or "").lower() or "trial" in (result.error_message or "").lower()


class TestCheckQuotaPaidPlans:
    """Test suite for check_quota with paid plan subscribers."""

    def setup_method(self):
        """Clear plan capabilities cache to prevent test pollution."""
        from quota import clear_plan_capabilities_cache
        clear_plan_capabilities_cache()

    def test_consultor_agil_with_quota_remaining(self):
        """Should return allowed=True for Consultor Ágil with quota remaining."""
        from quota import check_quota

        mock_supabase = Mock()

        # Active subscription
        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-123",
            "plan_id": "consultor_agil",
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 23 searches used (27 remaining from 50)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 23}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "consultor_agil"
        assert result.plan_name == "Consultor Ágil (legacy)"
        assert result.quota_used == 23
        assert result.quota_remaining == 27
        assert result.capabilities["max_history_days"] == 30
        assert result.capabilities["allow_excel"] is False

    def test_maquina_has_excel_enabled(self):
        """Máquina plan should have Excel export enabled."""
        from quota import check_quota

        mock_supabase = Mock()

        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-456",
            "plan_id": "maquina",
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 100}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "maquina"
        assert result.capabilities["allow_excel"] is True
        assert result.capabilities["max_history_days"] == 365

    def test_sala_guerra_has_max_capabilities(self):
        """Sala de Guerra should have maximum capabilities."""
        from quota import check_quota

        mock_supabase = Mock()

        future_date = (datetime.now(timezone.utc) + timedelta(days=300)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-789",
            "plan_id": "sala_guerra",
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 500}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is True
        assert result.plan_id == "sala_guerra"
        assert result.capabilities["max_history_days"] == 1825
        assert result.capabilities["allow_excel"] is True
        assert result.capabilities["max_summary_tokens"] == 10000
        assert result.quota_remaining == 500


class TestCheckQuotaExhausted:
    """Test suite for check_quota when quota is exhausted."""

    def setup_method(self):
        """Clear plan capabilities cache to prevent test pollution."""
        from quota import clear_plan_capabilities_cache
        clear_plan_capabilities_cache()

    def test_quota_exhausted_returns_not_allowed(self):
        """Should return allowed=False when monthly quota exhausted."""
        from quota import check_quota

        mock_supabase = Mock()

        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-123",
            "plan_id": "consultor_agil",
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 50 searches used (quota exhausted for consultor_agil)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 50}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is False
        assert result.quota_remaining == 0
        assert "50 análises este mês" in result.error_message

    def test_quota_exhausted_includes_reset_date(self):
        """Exhausted quota error should include reset date."""
        from quota import check_quota

        mock_supabase = Mock()

        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-123",
            "plan_id": "maquina",
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 300 searches used (quota exhausted for maquina)
        monthly_result = Mock()
        monthly_result.data = [{"searches_count": 300}]
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is False
        assert result.quota_reset_date is not None
        assert "renova em" in result.error_message


class TestCheckQuotaExpiredSubscriptions:
    """Test suite for check_quota with expired subscriptions."""

    def test_expired_subscription_returns_not_allowed(self):
        """Should return allowed=False for expired subscription."""
        from quota import check_quota

        mock_supabase = Mock()

        # Past expiry date (must exceed SUBSCRIPTION_GRACE_DAYS=7)
        past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-expired",
            "plan_id": "consultor_agil",
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        monthly_result = Mock()
        monthly_result.data = []
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result.allowed is False
        assert "expir" in result.error_message.lower()  # matches 'expirou' or 'expirado'

    def test_handles_utc_z_suffix_in_expires_at(self):
        """Should handle ISO date with Z suffix (UTC indicator)."""
        from quota import check_quota

        mock_supabase = Mock()

        # Date with Z suffix (common in Supabase)
        past_date = "2020-01-01T00:00:00Z"
        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-z",
            "plan_id": "maquina",
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        monthly_result = Mock()
        monthly_result.data = []
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = monthly_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        # Should parse date correctly and return not allowed (expired)
        assert result.allowed is False


class TestCheckAndIncrementQuotaAtomic:
    """Test suite for check_and_increment_quota_atomic (STORY-223 AC20)."""

    @patch("supabase_client.get_supabase")
    def test_ac20_fallback_path_increments_quota_without_race(self, mock_get_supabase):
        """AC20: Fallback path (no RPC) correctly increments quota without race conditions."""
        from quota import check_and_increment_quota_atomic

        mock_sb = Mock()
        mock_get_supabase.return_value = mock_sb

        # Mock RPC failure (function not available)
        mock_sb.rpc.return_value.execute.side_effect = Exception("function check_and_increment_quota does not exist")

        # Mock fallback: get_monthly_quota_used returns 5
        with patch("quota.get_monthly_quota_used", return_value=5):
            # Mock fallback: increment_monthly_quota returns 6
            with patch("quota.increment_monthly_quota", return_value=6):
                allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is True
        assert new_count == 6
        assert remaining == 44  # 50 - 6

    @patch("supabase_client.get_supabase")
    def test_fallback_path_blocks_when_at_limit(self, mock_get_supabase):
        """Fallback path should block when quota is at limit."""
        from quota import check_and_increment_quota_atomic

        mock_sb = Mock()
        mock_get_supabase.return_value = mock_sb

        # Mock RPC failure
        mock_sb.rpc.return_value.execute.side_effect = Exception("RPC not available")

        # Mock fallback: already at quota limit
        with patch("quota.get_monthly_quota_used", return_value=50):
            allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is False
        assert new_count == 50
        assert remaining == 0

    @patch("supabase_client.get_supabase")
    def test_rpc_path_atomic_increment(self, mock_get_supabase):
        """RPC path should atomically check and increment."""
        from quota import check_and_increment_quota_atomic

        mock_sb = Mock()
        mock_get_supabase.return_value = mock_sb

        # Mock successful RPC call
        mock_sb.rpc.return_value.execute.return_value.data = [
            {"allowed": True, "new_count": 11, "quota_remaining": 39}
        ]

        allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is True
        assert new_count == 11
        assert remaining == 39

        # Verify RPC was called with correct function name
        mock_sb.rpc.assert_called_once()
        call_args = mock_sb.rpc.call_args
        assert call_args[0][0] == "check_and_increment_quota"

    @patch("supabase_client.get_supabase")
    def test_rpc_path_blocks_at_limit(self, mock_get_supabase):
        """RPC path should block when at limit."""
        from quota import check_and_increment_quota_atomic

        mock_sb = Mock()
        mock_get_supabase.return_value = mock_sb

        # Mock RPC returning blocked result
        mock_sb.rpc.return_value.execute.return_value.data = [
            {"allowed": False, "new_count": 50, "quota_remaining": 0}
        ]

        allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is False
        assert new_count == 50
        assert remaining == 0


class TestMonthlyQuotaFunctions:
    """Test suite for monthly quota tracking functions (STORY-165)."""

    def test_get_current_month_key_format(self):
        """Month key should be in YYYY-MM format."""
        from quota import get_current_month_key

        key = get_current_month_key()
        assert len(key) == 7
        assert key[4] == "-"
        assert key[:4].isdigit()
        assert key[5:].isdigit()

    def test_get_quota_reset_date_is_first_of_next_month(self):
        """Reset date should be first of next month."""
        from quota import get_quota_reset_date

        reset = get_quota_reset_date()
        assert reset.day == 1
        assert reset.tzinfo == timezone.utc

    def test_get_monthly_quota_used_returns_zero_for_no_record(self):
        """Should return 0 if no monthly quota record exists."""
        from quota import get_monthly_quota_used

        mock_supabase = Mock()

        # Empty result
        result = Mock()
        result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            count = get_monthly_quota_used("user-123")

        assert count == 0

    def test_get_monthly_quota_used_returns_count(self):
        """Should return actual count from database."""
        from quota import get_monthly_quota_used

        mock_supabase = Mock()

        result = Mock()
        result.data = [{"searches_count": 42}]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            count = get_monthly_quota_used("user-123")

        assert count == 42


class TestSaveSearchSession:
    """Test suite for save_search_session function."""

    @pytest.fixture
    def valid_session_data(self):
        """Create valid session data for testing."""
        return {
            "user_id": "user-123",
            "sectors": ["uniformes", "alimentacao"],
            "ufs": ["SP", "RJ"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
            "custom_keywords": ["jaleco", "avental"],
            "total_raw": 100,
            "total_filtered": 25,
            "valor_total": 1500000.50,
            "resumo_executivo": "Encontradas 25 oportunidades relevantes.",
            "destaques": ["SP: R$ 500k", "RJ: R$ 1M"],
        }

    @pytest.fixture
    def mock_supabase_with_profile(self):
        """Create mock Supabase client that confirms profile exists."""
        mock_supabase = Mock()

        # Mock profile check - profile exists
        profile_result = Mock()
        profile_result.data = [{"id": "user-123"}]

        # Mock insert result for sessions
        insert_result = Mock()
        insert_result.data = [{"id": "session-uuid-123"}]

        # Configure table mock to handle both profiles and search_sessions
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table
        return mock_supabase

    async def test_saves_session_and_returns_id(self, valid_session_data, mock_supabase_with_profile):
        """Should save session and return the generated ID."""
        from quota import save_search_session

        with patch("supabase_client.get_supabase", return_value=mock_supabase_with_profile):
            result = await save_search_session(**valid_session_data)

        assert result == "session-uuid-123"

    async def test_saves_all_fields_correctly(self, valid_session_data, mock_supabase_with_profile):
        """Should save all session fields to database."""
        from quota import save_search_session

        with patch("supabase_client.get_supabase", return_value=mock_supabase_with_profile):
            await save_search_session(**valid_session_data)

        # Verify all fields were passed to insert
        mock_table = mock_supabase_with_profile.table.return_value
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["user_id"] == "user-123"
        assert call_args["sectors"] == sorted(["uniformes", "alimentacao"])
        assert call_args["ufs"] == sorted(["SP", "RJ"])
        assert call_args["data_inicial"] == "2025-01-01"
        assert call_args["data_final"] == "2025-01-31"
        assert call_args["custom_keywords"] == ["jaleco", "avental"]
        assert call_args["total_raw"] == 100
        assert call_args["total_filtered"] == 25
        assert call_args["valor_total"] == 1500000.50
        assert call_args["resumo_executivo"] == "Encontradas 25 oportunidades relevantes."
        assert call_args["destaques"] == ["SP: R$ 500k", "RJ: R$ 1M"]

    async def test_saves_session_without_optional_fields(self):
        """Should save session with None for optional fields."""
        from quota import save_search_session

        mock_supabase = Mock()

        # Mock profile check - profile exists
        profile_result = Mock()
        profile_result.data = [{"id": "user-456"}]

        insert_result = Mock()
        insert_result.data = [{"id": "session-minimal"}]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = await save_search_session(
                user_id="user-456",
                sectors=["uniformes"],
                ufs=["SP"],
                data_inicial="2025-01-01",
                data_final="2025-01-07",
                custom_keywords=None,
                total_raw=50,
                total_filtered=10,
                valor_total=100000.0,
                resumo_executivo=None,
                destaques=None,
            )

        assert result == "session-minimal"

        call_args = mock_table.insert.call_args[0][0]
        assert call_args["custom_keywords"] is None
        assert call_args["resumo_executivo"] is None
        assert call_args["destaques"] is None

    async def test_converts_valor_total_to_float(self):
        """Should convert valor_total to float."""
        from quota import save_search_session
        from decimal import Decimal

        mock_supabase = Mock()

        # Mock profile check - profile exists
        profile_result = Mock()
        profile_result.data = [{"id": "user-123"}]

        insert_result = Mock()
        insert_result.data = [{"id": "session-id"}]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            await save_search_session(
                user_id="user-123",
                sectors=["uniformes"],
                ufs=["SP"],
                data_inicial="2025-01-01",
                data_final="2025-01-07",
                custom_keywords=None,
                total_raw=10,
                total_filtered=5,
                valor_total=Decimal("123456.78"),  # Decimal input
                resumo_executivo=None,
                destaques=None,
            )

        call_args = mock_table.insert.call_args[0][0]
        assert isinstance(call_args["valor_total"], float)
        assert call_args["valor_total"] == 123456.78

    async def test_logs_saved_session_info(self, valid_session_data, mock_supabase_with_profile, caplog):
        """Should log info message when session is saved."""
        from quota import save_search_session
        import logging

        # Override the insert result for this test
        mock_table = mock_supabase_with_profile.table.return_value
        mock_table.insert.return_value.execute.return_value.data = [{"id": "session-logged"}]

        with patch("supabase_client.get_supabase", return_value=mock_supabase_with_profile):
            with caplog.at_level(logging.INFO):
                await save_search_session(**valid_session_data)

        # SECURITY (Issue #168): Log format changed to sanitize user IDs and session IDs
        # Format: "Saved search session session-***" for user user***"
        assert any("saved search session" in record.message.lower() for record in caplog.records)
        # Session ID is masked (first 8 chars + ***)
        assert any("session-***" in record.message for record in caplog.records)
        # User ID is masked via mask_user_id() function
        assert any("user***" in record.message for record in caplog.records)

    async def test_inserts_into_search_sessions_table(self, valid_session_data, mock_supabase_with_profile):
        """Should insert into the search_sessions table."""
        from quota import save_search_session

        with patch("supabase_client.get_supabase", return_value=mock_supabase_with_profile):
            await save_search_session(**valid_session_data)

        # The table should be called with "profiles" first (to check) and then "search_sessions" (to insert)
        calls = mock_supabase_with_profile.table.call_args_list
        table_names = [call[0][0] for call in calls]
        assert "profiles" in table_names
        assert "search_sessions" in table_names


class TestDebtDB022IncrementQuotaLastResort:
    """DEBT-DB-022: Verify last-resort fallback does NOT perform non-atomic upsert.

    When both RPC functions (increment_quota_atomic and increment_quota_fallback_atomic)
    are unavailable, the code should return the current count without mutating data,
    rather than performing a non-atomic upsert that could reset the count to 1.
    """

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", return_value=7)
    def test_last_resort_returns_current_count_without_upsert(
        self, mock_get_used, mock_get_sb, caplog
    ):
        """When both RPCs fail, should return current count and log warning."""
        import logging
        from quota import increment_monthly_quota

        mock_sb = Mock()
        mock_get_sb.return_value = mock_sb

        # Both RPC calls raise exceptions (functions not deployed)
        mock_sb.rpc.side_effect = Exception("RPC not available")

        with caplog.at_level(logging.WARNING):
            result = increment_monthly_quota("user-123", max_quota=100)

        # Should return current count from get_monthly_quota_used
        assert result == 7
        mock_get_used.assert_called_once_with("user-123")

        # Should NOT have called .table().upsert() — the old non-atomic path
        mock_sb.table.assert_not_called()

        # Should have logged a warning about all methods failing
        assert any("All atomic quota increment methods failed" in r.message for r in caplog.records)

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", side_effect=Exception("DB down"))
    def test_last_resort_returns_zero_on_total_failure(
        self, mock_get_used, mock_get_sb
    ):
        """When RPCs fail AND get_monthly_quota_used fails, should return 0 (fail-open)."""
        from quota import increment_monthly_quota

        mock_sb = Mock()
        mock_get_sb.return_value = mock_sb
        mock_sb.rpc.side_effect = Exception("RPC not available")

        result = increment_monthly_quota("user-456", max_quota=100)

        # Fail-open: return 0 rather than blocking user
        assert result == 0


class TestPlanStatusCacheBounded:
    """DEBT-323: Verify _plan_status_cache enforces maxsize eviction."""

    def test_cache_evicts_oldest_when_full(self):
        """Insert more than maxsize entries; oldest should be evicted."""
        from quota import (
            _plan_status_cache,
            _plan_status_cache_lock,
            _cache_plan_status,
            _get_cached_plan_status,
            PLAN_STATUS_CACHE_MAXSIZE,
        )

        # Clear cache before test
        with _plan_status_cache_lock:
            _plan_status_cache.clear()

        try:
            # Insert maxsize + 50 entries
            for i in range(PLAN_STATUS_CACHE_MAXSIZE + 50):
                _cache_plan_status(f"user-{i}", "smartlic_pro")

            # Cache should be bounded
            assert len(_plan_status_cache) == PLAN_STATUS_CACHE_MAXSIZE

            # Oldest entries (0..49) should have been evicted
            assert _get_cached_plan_status("user-0") is None
            assert _get_cached_plan_status("user-49") is None

            # Newest entries should still be present
            last_idx = PLAN_STATUS_CACHE_MAXSIZE + 49
            assert _get_cached_plan_status(f"user-{last_idx}") == "smartlic_pro"
        finally:
            # Clean up
            with _plan_status_cache_lock:
                _plan_status_cache.clear()

    def test_cache_update_existing_key_does_not_grow(self):
        """Updating an existing key should not increase cache size."""
        from quota import (
            _plan_status_cache,
            _plan_status_cache_lock,
            _cache_plan_status,
            _get_cached_plan_status,
        )

        with _plan_status_cache_lock:
            _plan_status_cache.clear()

        try:
            _cache_plan_status("user-A", "free_trial")
            _cache_plan_status("user-B", "free_trial")
            assert len(_plan_status_cache) == 2

            # Update existing key
            _cache_plan_status("user-A", "smartlic_pro")
            assert len(_plan_status_cache) == 2
            assert _get_cached_plan_status("user-A") == "smartlic_pro"
        finally:
            with _plan_status_cache_lock:
                _plan_status_cache.clear()
