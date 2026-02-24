"""
STORY-266 AC16-AC20: Tests for trial reminder email templates and cron job.

AC16: Test each template renders correctly with proper content.
AC18: Test check_trial_reminders() identifies users at each milestone.
AC19: Test idempotency — running job twice doesn't send duplicate emails.
AC20: Test with zero usage (stats all zeros — message adapts).
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta

# ============================================================================
# AC16: Template rendering tests
# ============================================================================

from templates.emails.trial import (
    render_trial_midpoint_email,
    render_trial_expiring_email,
    render_trial_last_day_email,
    render_trial_expired_email,
    _format_brl,
)


class TestFormatBrl:
    """Test Brazilian Real formatting helper."""

    def test_millions(self):
        assert "M" in _format_brl(2_500_000)
        assert "2.5M" in _format_brl(2_500_000)

    def test_thousands(self):
        assert "k" in _format_brl(150_000)
        assert "150k" in _format_brl(150_000)

    def test_small_value(self):
        result = _format_brl(500)
        assert "500" in result
        assert "R$" in result

    def test_zero(self):
        result = _format_brl(0)
        assert "R$" in result


class TestTrialMidpointEmail:
    """AC1/AC16: Day 3 midpoint template."""

    def test_renders_without_error(self):
        html = render_trial_midpoint_email("João", {
            "searches_count": 5,
            "opportunities_found": 42,
            "total_value_estimated": 1_500_000,
            "pipeline_items_count": 3,
        })
        assert "<!DOCTYPE html>" in html

    def test_contains_user_name(self):
        html = render_trial_midpoint_email("Maria Silva", {
            "searches_count": 3,
            "opportunities_found": 10,
            "total_value_estimated": 500_000,
        })
        assert "Maria Silva" in html

    def test_contains_cta_link_buscar(self):
        html = render_trial_midpoint_email("Test", {
            "searches_count": 1,
            "opportunities_found": 5,
            "total_value_estimated": 100_000,
        })
        assert "/buscar" in html
        assert "Continuar descobrindo oportunidades" in html

    def test_shows_stats_when_used(self):
        html = render_trial_midpoint_email("Test", {
            "searches_count": 5,
            "opportunities_found": 42,
            "total_value_estimated": 1_500_000,
        })
        assert "42" in html
        assert "5" in html
        assert "1.5M" in html

    def test_celebratory_tone(self):
        html = render_trial_midpoint_email("Test", {
            "searches_count": 3,
            "opportunities_found": 10,
            "total_value_estimated": 200_000,
        })
        assert "descobrindo" in html.lower() or "analisou" in html.lower()

    def test_zero_usage_adapts_message(self):
        """AC20: Zero usage shows adapted copy."""
        html = render_trial_midpoint_email("Test", {
            "searches_count": 0,
            "opportunities_found": 0,
            "total_value_estimated": 0,
        })
        assert "ainda tem" in html.lower() or "descobrir" in html.lower()
        assert "primeira busca" in html.lower()

    def test_empty_stats_dict(self):
        """AC20: Empty stats dict doesn't crash."""
        html = render_trial_midpoint_email("Test", {})
        assert "<!DOCTYPE html>" in html


class TestTrialExpiringEmail:
    """AC2/AC16: Day 5 expiring template."""

    def test_renders_without_error(self):
        html = render_trial_expiring_email("João", 2, {
            "searches_count": 10,
            "opportunities_found": 50,
            "total_value_estimated": 3_000_000,
            "pipeline_items_count": 5,
        })
        assert "<!DOCTYPE html>" in html

    def test_contains_days_remaining(self):
        html = render_trial_expiring_email("Test", 2, {})
        assert "2 dias" in html

    def test_contains_cta_link_planos(self):
        html = render_trial_expiring_email("Test", 2, {})
        assert "/planos" in html
        assert "Garantir acesso contínuo" in html

    def test_shows_pipeline_count(self):
        html = render_trial_expiring_email("Test", 2, {
            "searches_count": 5,
            "opportunities_found": 20,
            "total_value_estimated": 500_000,
            "pipeline_items_count": 7,
        })
        assert "7" in html  # pipeline items

    def test_informative_tone(self):
        html = render_trial_expiring_email("Test", 2, {})
        assert "chegando ao fim" in html.lower() or "expir" in html.lower()


class TestTrialLastDayEmail:
    """AC3/AC16: Day 6 last day template."""

    def test_renders_without_error(self):
        html = render_trial_last_day_email("João", {
            "searches_count": 15,
            "opportunities_found": 80,
            "total_value_estimated": 5_000_000,
            "pipeline_items_count": 10,
        })
        assert "<!DOCTYPE html>" in html

    def test_contains_urgency_message(self):
        html = render_trial_last_day_email("Test", {})
        assert "Amanhã" in html
        assert "último dia" in html.lower()

    def test_contains_cta_link_planos(self):
        html = render_trial_last_day_email("Test", {})
        assert "/planos" in html

    def test_contains_price(self):
        """AC3: Includes SmartLic Pro price."""
        html = render_trial_last_day_email("Test", {})
        assert "1.999" in html

    def test_contains_annual_discount_mention(self):
        """AC3: Mentions annual discount alternative."""
        html = render_trial_last_day_email("Test", {})
        assert "anual" in html.lower()

    def test_high_urgency_styling(self):
        """AC3: Uses red/urgent styling."""
        html = render_trial_last_day_email("Test", {})
        assert "#d32f2f" in html  # red color


class TestTrialExpiredEmail:
    """AC4/AC16: Day 8 expired template."""

    def test_renders_without_error(self):
        html = render_trial_expired_email("João", {
            "searches_count": 10,
            "opportunities_found": 30,
            "total_value_estimated": 2_000_000,
            "pipeline_items_count": 5,
        })
        assert "<!DOCTYPE html>" in html

    def test_contains_cta_link_planos(self):
        html = render_trial_expired_email("Test", {})
        assert "/planos" in html
        assert "Reativar acesso" in html

    def test_mentions_data_saved(self):
        """AC4: Mentions data saved for 30 days."""
        html = render_trial_expired_email("Test", {})
        assert "30 dias" in html

    def test_reengagement_tone(self):
        html = render_trial_expired_email("Test", {
            "opportunities_found": 15,
            "pipeline_items_count": 3,
        })
        assert "esperando" in html.lower()

    def test_uses_pipeline_count_when_available(self):
        html = render_trial_expired_email("Test", {
            "opportunities_found": 30,
            "pipeline_items_count": 5,
        })
        assert "5 oportunidades" in html

    def test_uses_opportunities_count_when_no_pipeline(self):
        html = render_trial_expired_email("Test", {
            "opportunities_found": 30,
            "pipeline_items_count": 0,
        })
        assert "30 oportunidades" in html

    def test_zero_usage_adapts_message(self):
        """AC20: Zero usage shows generic reengagement."""
        html = render_trial_expired_email("Test", {
            "searches_count": 0,
            "opportunities_found": 0,
            "total_value_estimated": 0,
            "pipeline_items_count": 0,
        })
        assert "continuam surgindo" in html.lower()

    def test_empty_stats(self):
        """AC20: Empty stats doesn't crash."""
        html = render_trial_expired_email("Test", {})
        assert "<!DOCTYPE html>" in html


# ============================================================================
# AC18-AC19: Cron job tests
# ============================================================================

class TestCheckTrialReminders:
    """AC18: Test cron job logic for identifying milestone users."""

    @pytest.mark.asyncio
    async def test_disabled_flag_skips(self):
        """AC10: When TRIAL_EMAILS_ENABLED=false, does nothing."""
        with patch("config.TRIAL_EMAILS_ENABLED", False):
            from cron_jobs import check_trial_reminders
            result = await check_trial_reminders()
            assert result.get("disabled") is True
            assert result["sent"] == 0

    @pytest.mark.asyncio
    async def test_sends_midpoint_email(self):
        """AC18: Correctly identifies day-3 users and sends midpoint email."""
        from cron_jobs import check_trial_reminders

        now = datetime.now(timezone.utc)

        mock_sb = MagicMock()
        # Mock profiles query — return one user at day 3
        profiles_chain = MagicMock()
        profiles_chain.select.return_value = profiles_chain
        profiles_chain.eq.return_value = profiles_chain
        profiles_chain.gte.return_value = profiles_chain
        profiles_chain.lt.return_value = profiles_chain

        # Only return data for first milestone (day 3)
        call_count = [0]

        def profiles_execute():
            call_count[0] += 1
            if call_count[0] == 1:  # First call is for day 3
                return MagicMock(data=[{
                    "id": "user-123-uuid-mock-abcdef123456",
                    "email": "test@example.com",
                    "full_name": "Test User",
                }])
            return MagicMock(data=[])

        profiles_chain.execute.side_effect = profiles_execute

        # Mock trial_email_log check — not yet sent
        log_check_chain = MagicMock()
        log_check_chain.select.return_value = log_check_chain
        log_check_chain.eq.return_value = log_check_chain
        log_check_chain.limit.return_value = log_check_chain
        log_check_chain.execute.return_value = MagicMock(data=[])

        # Mock log insert
        log_insert_chain = MagicMock()
        log_insert_chain.insert.return_value = log_insert_chain
        log_insert_chain.execute.return_value = MagicMock(data=[{"id": "log-1"}])

        # Track which table is requested
        table_call_count = [0]

        def table_side_effect(name):
            if name == "profiles":
                return profiles_chain
            elif name == "trial_email_log":
                table_call_count[0] += 1
                # First calls are checks (select), later is insert
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.limit.return_value = chain
                chain.execute.return_value = MagicMock(data=[])
                chain.insert.return_value = chain
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        mock_stats = MagicMock()
        mock_stats.model_dump.return_value = {
            "searches_count": 5,
            "opportunities_found": 20,
            "total_value_estimated": 500_000,
            "pipeline_items_count": 2,
            "sectors_searched": ["vestuario"],
        }

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("services.trial_stats.get_trial_usage_stats", return_value=mock_stats), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT") as mock_metric:

            result = await check_trial_reminders()

            assert result["sent"] >= 1
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_idempotency_skips_already_sent(self):
        """AC19: Running job twice doesn't send duplicate emails."""
        from cron_jobs import check_trial_reminders

        mock_sb = MagicMock()

        profiles_chain = MagicMock()
        profiles_chain.select.return_value = profiles_chain
        profiles_chain.eq.return_value = profiles_chain
        profiles_chain.gte.return_value = profiles_chain
        profiles_chain.lt.return_value = profiles_chain

        call_count = [0]

        def profiles_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(data=[{
                    "id": "user-456-uuid-mock-abcdef789012",
                    "email": "dup@example.com",
                    "full_name": "Dup User",
                }])
            return MagicMock(data=[])

        profiles_chain.execute.side_effect = profiles_execute

        def table_side_effect(name):
            if name == "profiles":
                return profiles_chain
            elif name == "trial_email_log":
                # Return existing log entry = already sent!
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.limit.return_value = chain
                chain.execute.return_value = MagicMock(data=[{"id": "existing-log"}])
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await check_trial_reminders()

            assert result["skipped"] >= 1
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_users_at_milestone(self):
        """AC18: No users at any milestone = zero sent."""
        from cron_jobs import check_trial_reminders

        mock_sb = MagicMock()
        empty_chain = MagicMock()
        empty_chain.select.return_value = empty_chain
        empty_chain.eq.return_value = empty_chain
        empty_chain.gte.return_value = empty_chain
        empty_chain.lt.return_value = empty_chain
        empty_chain.execute.return_value = MagicMock(data=[])

        mock_sb.table.return_value = empty_chain

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await check_trial_reminders()
            assert result["sent"] == 0
            assert result["errors"] == 0
