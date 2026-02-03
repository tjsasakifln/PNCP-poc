"""Tests for quota management module (quota.py).

Tests search credit checking, decrementing, and search session saving.
Covers all plan types: free tier, credit packs, unlimited subscriptions.
Uses mocked Supabase client to avoid external API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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


class TestCheckQuotaFreeTier:
    """Test suite for check_quota with free tier users (no subscription)."""

    @pytest.fixture
    def mock_supabase_no_subscription(self):
        """Create mock Supabase client with no active subscription."""
        mock = Mock()

        # No active subscription
        subscription_result = Mock()
        subscription_result.data = []
        mock.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        return mock

    def test_free_tier_with_searches_remaining(self):
        """Should return allowed=True for free tier user with searches remaining."""
        from quota import check_quota

        mock_supabase = Mock()

        # No active subscription
        subscription_result = Mock()
        subscription_result.data = []

        # Chain for subscription query
        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 1 search session used (2 remaining out of 3)
        session_result = Mock()
        session_result.count = 1
        mock_table.select.return_value.eq.return_value.execute.return_value = session_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["plan_id"] == "free"
        assert result["credits_remaining"] == 2  # 3 - 1 used
        assert result["subscription_id"] is None

    def test_free_tier_with_zero_searches_used(self):
        """Should return 3 credits for free tier user with no searches."""
        from quota import check_quota

        mock_supabase = Mock()

        # No active subscription
        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 0 search sessions used
        session_result = Mock()
        session_result.count = 0
        mock_table.select.return_value.eq.return_value.execute.return_value = session_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["credits_remaining"] == 3

    def test_free_tier_exhausted_raises_error(self):
        """Should raise QuotaExceededError when free tier searches exhausted."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        # No active subscription
        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 3 search sessions used (exhausted)
        session_result = Mock()
        session_result.count = 3
        mock_table.select.return_value.eq.return_value.execute.return_value = session_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError) as exc_info:
                check_quota("user-123")

        assert "3 buscas gratuitas" in str(exc_info.value)
        assert "plano" in str(exc_info.value).lower()

    def test_free_tier_more_than_three_searches(self):
        """Should return 0 credits when more than 3 free searches used."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = []

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        # 5 search sessions used (edge case)
        session_result = Mock()
        session_result.count = 5
        mock_table.select.return_value.eq.return_value.execute.return_value = session_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError):
                check_quota("user-123")


class TestCheckQuotaCreditPacks:
    """Test suite for check_quota with credit-based plans (packs)."""

    def test_pack_with_credits_remaining(self):
        """Should return allowed=True for pack user with credits."""
        from quota import check_quota

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-123",
            "plan_id": "pack_10",
            "credits_remaining": 7,
            "expires_at": None,  # Packs don't expire by time
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["plan_id"] == "pack_10"
        assert result["credits_remaining"] == 7
        assert result["subscription_id"] == "sub-123"

    def test_pack_with_one_credit_remaining(self):
        """Should return allowed=True for pack user with exactly 1 credit."""
        from quota import check_quota

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-456",
            "plan_id": "pack_5",
            "credits_remaining": 1,
            "expires_at": None,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["credits_remaining"] == 1

    def test_pack_with_zero_credits_raises_error(self):
        """Should raise QuotaExceededError when pack credits exhausted."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-789",
            "plan_id": "pack_10",
            "credits_remaining": 0,
            "expires_at": None,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError) as exc_info:
                check_quota("user-123")

        assert "buscas acabaram" in str(exc_info.value)
        assert "pacote" in str(exc_info.value).lower()


class TestCheckQuotaUnlimited:
    """Test suite for check_quota with unlimited plans (monthly, annual, master)."""

    def test_unlimited_plan_monthly(self):
        """Should return allowed=True with None credits for monthly plan."""
        from quota import check_quota

        mock_supabase = Mock()

        # Future expiry date
        future_date = (datetime.now(timezone.utc) + timedelta(days=25)).isoformat()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-monthly",
            "plan_id": "monthly",
            "credits_remaining": None,  # Unlimited
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["plan_id"] == "monthly"
        assert result["credits_remaining"] is None
        assert result["subscription_id"] == "sub-monthly"

    def test_unlimited_plan_annual(self):
        """Should return allowed=True with None credits for annual plan."""
        from quota import check_quota

        mock_supabase = Mock()

        future_date = (datetime.now(timezone.utc) + timedelta(days=300)).isoformat()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-annual",
            "plan_id": "annual",
            "credits_remaining": None,
            "expires_at": future_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["plan_id"] == "annual"
        assert result["credits_remaining"] is None

    def test_unlimited_plan_master(self):
        """Should return allowed=True for master plan (no expiry)."""
        from quota import check_quota

        mock_supabase = Mock()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-master",
            "plan_id": "master",
            "credits_remaining": None,  # Unlimited
            "expires_at": None,  # Never expires
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = check_quota("user-123")

        assert result["allowed"] is True
        assert result["plan_id"] == "master"
        assert result["credits_remaining"] is None


class TestCheckQuotaExpiredSubscriptions:
    """Test suite for check_quota with expired subscriptions."""

    def test_expired_subscription_raises_error(self):
        """Should raise QuotaExceededError for expired subscription."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        # Past expiry date
        past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-expired",
            "plan_id": "monthly",
            "credits_remaining": None,
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError) as exc_info:
                check_quota("user-123")

        assert "expirou" in str(exc_info.value).lower()
        assert "renove" in str(exc_info.value).lower()

    def test_expired_subscription_is_deactivated(self):
        """Should deactivate expired subscription in database."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-to-deactivate",
            "plan_id": "monthly",
            "credits_remaining": None,
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result
        mock_update = Mock()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError):
                check_quota("user-123")

        # Verify deactivation was called
        mock_table.update.assert_called_with({"is_active": False})

    def test_expired_subscription_logs_info(self, caplog):
        """Should log info message when subscription expires."""
        from quota import check_quota, QuotaExceededError
        import logging

        mock_supabase = Mock()

        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-logged",
            "plan_id": "monthly",
            "credits_remaining": None,
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.INFO):
                with pytest.raises(QuotaExceededError):
                    check_quota("user-123")

        assert any("expired" in record.message.lower() for record in caplog.records)

    def test_handles_utc_z_suffix_in_expires_at(self):
        """Should handle ISO date with Z suffix (UTC indicator)."""
        from quota import check_quota, QuotaExceededError

        mock_supabase = Mock()

        # Date with Z suffix (common in Supabase)
        past_date = "2020-01-01T00:00:00Z"

        subscription_result = Mock()
        subscription_result.data = [{
            "id": "sub-z",
            "plan_id": "monthly",
            "credits_remaining": None,
            "expires_at": past_date,
        }]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = subscription_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with pytest.raises(QuotaExceededError):
                check_quota("user-123")


class TestDecrementCredits:
    """Test suite for decrement_credits function."""

    def test_does_not_decrement_for_free_tier(self):
        """Should not decrement when subscription_id is None (free tier)."""
        from quota import decrement_credits

        # Should not call Supabase at all
        with patch("supabase_client.get_supabase") as mock_get_supabase:
            decrement_credits(subscription_id=None, user_id="user-123")

        mock_get_supabase.assert_not_called()

    def test_decrements_credit_based_plan(self):
        """Should decrement credits for pack plans."""
        from quota import decrement_credits

        mock_supabase = Mock()

        # Current credits
        credits_result = Mock()
        credits_result.data = {"credits_remaining": 5}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = credits_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            decrement_credits(subscription_id="sub-123", user_id="user-123")

        # Verify update was called with decremented value
        mock_table.update.assert_called_once_with({"credits_remaining": 4})

    def test_does_not_decrement_unlimited_plan(self):
        """Should not decrement when credits_remaining is None (unlimited)."""
        from quota import decrement_credits

        mock_supabase = Mock()

        # Unlimited plan has None credits
        credits_result = Mock()
        credits_result.data = {"credits_remaining": None}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = credits_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            decrement_credits(subscription_id="sub-unlimited", user_id="user-123")

        # Verify update was NOT called
        mock_table.update.assert_not_called()

    def test_does_not_go_below_zero(self):
        """Should not decrement below zero credits."""
        from quota import decrement_credits

        mock_supabase = Mock()

        # Already at 0 credits
        credits_result = Mock()
        credits_result.data = {"credits_remaining": 0}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = credits_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            decrement_credits(subscription_id="sub-zero", user_id="user-123")

        # Should update with 0, not -1
        mock_table.update.assert_called_once_with({"credits_remaining": 0})

    def test_logs_decrement_info(self, caplog):
        """Should log info message when credits are decremented."""
        from quota import decrement_credits
        import logging

        mock_supabase = Mock()

        credits_result = Mock()
        credits_result.data = {"credits_remaining": 3}

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = credits_result
        mock_table.update.return_value.eq.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.INFO):
                decrement_credits(subscription_id="sub-log", user_id="user-123")

        assert any("decremented" in record.message.lower() for record in caplog.records)
        assert any("2 remaining" in record.message for record in caplog.records)

    def test_handles_no_result_data(self):
        """Should handle case when subscription not found."""
        from quota import decrement_credits

        mock_supabase = Mock()

        # No data returned
        credits_result = Mock()
        credits_result.data = None

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.single.return_value.execute.return_value = credits_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Should not raise, just do nothing
            decrement_credits(subscription_id="sub-missing", user_id="user-123")

        mock_table.update.assert_not_called()


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

    def test_saves_session_and_returns_id(self, valid_session_data):
        """Should save session and return the generated ID."""
        from quota import save_search_session

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-uuid-123"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(**valid_session_data)

        assert result == "session-uuid-123"

    def test_saves_all_fields_correctly(self, valid_session_data):
        """Should save all session fields to database."""
        from quota import save_search_session

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-id"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            save_search_session(**valid_session_data)

        # Verify all fields were passed to insert
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["user_id"] == "user-123"
        assert call_args["sectors"] == ["uniformes", "alimentacao"]
        assert call_args["ufs"] == ["SP", "RJ"]
        assert call_args["data_inicial"] == "2025-01-01"
        assert call_args["data_final"] == "2025-01-31"
        assert call_args["custom_keywords"] == ["jaleco", "avental"]
        assert call_args["total_raw"] == 100
        assert call_args["total_filtered"] == 25
        assert call_args["valor_total"] == 1500000.50
        assert call_args["resumo_executivo"] == "Encontradas 25 oportunidades relevantes."
        assert call_args["destaques"] == ["SP: R$ 500k", "RJ: R$ 1M"]

    def test_saves_session_without_optional_fields(self):
        """Should save session with None for optional fields."""
        from quota import save_search_session

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-minimal"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
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

    def test_converts_valor_total_to_float(self):
        """Should convert valor_total to float."""
        from quota import save_search_session
        from decimal import Decimal

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-id"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            save_search_session(
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

    def test_logs_saved_session_info(self, valid_session_data, caplog):
        """Should log info message when session is saved."""
        from quota import save_search_session
        import logging

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-logged"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            with caplog.at_level(logging.INFO):
                save_search_session(**valid_session_data)

        assert any("saved search session" in record.message.lower() for record in caplog.records)
        assert any("session-logged" in record.message for record in caplog.records)
        assert any("user-123" in record.message for record in caplog.records)

    def test_inserts_into_search_sessions_table(self, valid_session_data):
        """Should insert into the search_sessions table."""
        from quota import save_search_session

        mock_supabase = Mock()

        insert_result = Mock()
        insert_result.data = [{"id": "session-id"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            save_search_session(**valid_session_data)

        mock_supabase.table.assert_called_with("search_sessions")
