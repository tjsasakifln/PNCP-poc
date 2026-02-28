"""
STORY-266 AC16-AC20: Tests for trial reminder email templates and cron job.

AC16: Test each template renders correctly with proper content.
AC18: Test check_trial_reminders() identifies users at each milestone.
AC19: Test idempotency — running job twice doesn't send duplicate emails.
AC20: Test with zero usage (stats all zeros — message adapts).
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

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
        assert "397" in html

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
# CRIT-044 AC11: Verify legacy cron job is removed
# ============================================================================

class TestLegacyCronRemoved:
    """CRIT-044 AC11: Verify legacy STORY-266 trial reminder system is fully removed."""

    def test_check_trial_reminders_removed(self):
        """AC11: check_trial_reminders() no longer exists in cron_jobs."""
        import cron_jobs
        assert not hasattr(cron_jobs, "check_trial_reminders"), \
            "Legacy check_trial_reminders() should have been removed (CRIT-044 AC1)"

    def test_trial_email_milestones_removed(self):
        """AC11: TRIAL_EMAIL_MILESTONES dict no longer exists in cron_jobs."""
        import cron_jobs
        assert not hasattr(cron_jobs, "TRIAL_EMAIL_MILESTONES"), \
            "Legacy TRIAL_EMAIL_MILESTONES should have been removed (CRIT-044 AC2)"

    def test_start_trial_reminder_task_removed(self):
        """AC11: start_trial_reminder_task() no longer exists in cron_jobs."""
        import cron_jobs
        assert not hasattr(cron_jobs, "start_trial_reminder_task"), \
            "Legacy start_trial_reminder_task() should have been removed (CRIT-044 AC1)"

    def test_new_system_still_exists(self):
        """AC3: STORY-310 trial sequence system is still active."""
        import cron_jobs
        assert hasattr(cron_jobs, "start_trial_sequence_task"), \
            "STORY-310 start_trial_sequence_task() must remain (CRIT-044 AC3)"

    def test_new_system_respects_feature_flag(self):
        """AC7: STORY-310 process_trial_emails respects TRIAL_EMAILS_ENABLED."""
        from services.trial_email_sequence import process_trial_emails
        import inspect
        source = inspect.getsource(process_trial_emails)
        assert "TRIAL_EMAILS_ENABLED" in source, \
            "process_trial_emails must check TRIAL_EMAILS_ENABLED flag (CRIT-044 AC7)"

    def test_new_system_checks_marketing_emails_enabled(self):
        """AC9/AC10: STORY-310 checks marketing_emails_enabled for skip/send."""
        from services.trial_email_sequence import process_trial_emails
        import inspect
        source = inspect.getsource(process_trial_emails)
        assert "marketing_emails_enabled" in source, \
            "process_trial_emails must check marketing_emails_enabled (CRIT-044 AC9/AC10)"
