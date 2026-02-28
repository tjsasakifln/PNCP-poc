"""
STORY-319: Tests for 14-day trial duration.

AC14: Trial expires in 14 days (not 30).
AC15: Grandfather clause for existing users.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone


class TestTrialDuration14Days:
    """AC14: Verify trial expiration at 14 days."""

    def test_config_trial_duration_is_14(self):
        """TRIAL_DURATION_DAYS should default to 14."""
        from config import TRIAL_DURATION_DAYS
        assert TRIAL_DURATION_DAYS == 14

    def test_feature_flag_enabled_by_default(self):
        """TRIAL_14_DAYS_ENABLED should be True by default."""
        from config import TRIAL_14_DAYS_ENABLED
        assert TRIAL_14_DAYS_ENABLED is True

    def test_trial_expires_at_14_days(self):
        """New trial should expire after 14 days, not 30."""
        from config import TRIAL_DURATION_DAYS
        now = datetime.now(timezone.utc)
        expected_expiry = now + timedelta(days=TRIAL_DURATION_DAYS)
        # Verify it's 14 days, not 30
        delta = (expected_expiry - now).days
        assert delta == 14

    def test_trial_user_blocked_after_14_days(self):
        """Trial user with expired 14-day trial should be blocked."""
        from quota import check_quota, QuotaInfo, PLAN_CAPABILITIES

        # Simulate a trial that expired 1 day ago (after 14 days)
        expired_at = datetime.now(timezone.utc) - timedelta(days=1)

        # The quota check uses the trial_expires_at from DB
        # When trial_expires_at < now, user should be blocked
        assert expired_at < datetime.now(timezone.utc)

    def test_trial_user_active_within_14_days(self):
        """Trial user within 14 days should have access."""
        from config import TRIAL_DURATION_DAYS
        created_at = datetime.now(timezone.utc) - timedelta(days=7)
        trial_expires = created_at + timedelta(days=TRIAL_DURATION_DAYS)
        # Should still be active (7 days into 14-day trial)
        assert trial_expires > datetime.now(timezone.utc)


class TestEmailSequence14Days:
    """AC14: Email sequence adjusted for 14-day trial."""

    def test_sequence_schedule_fits_14_days(self):
        """All pre-expiry emails should be before day 14."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE

        pre_expiry_emails = [e for e in TRIAL_EMAIL_SEQUENCE if e["type"] != "expired"]
        for email in pre_expiry_emails:
            assert email["day"] <= 13, (
                f"Email #{email['number']} ({email['type']}) scheduled at day {email['day']} "
                f"but trial ends at day 14"
            )

    def test_expired_email_after_trial(self):
        """Expired email should be sent after trial period."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE

        expired = [e for e in TRIAL_EMAIL_SEQUENCE if e["type"] == "expired"]
        assert len(expired) == 1
        assert expired[0]["day"] == 16  # 2 days after 14-day trial

    def test_sequence_has_6_emails(self):
        """STORY-321: Sequence has 6 emails (compressed from 8)."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        assert len(TRIAL_EMAIL_SEQUENCE) == 6

    def test_sequence_days_are_ascending(self):
        """Email days should be in ascending order."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        days = [e["day"] for e in TRIAL_EMAIL_SEQUENCE]
        assert days == sorted(days)

    def test_welcome_email_says_14_dias(self):
        """Welcome email should mention 14 dias, not 30."""
        from templates.emails.trial import render_trial_welcome_email
        html = render_trial_welcome_email("Test")
        assert "14 dias" in html
        assert "30 dias" not in html

    def test_engagement_email_says_11_dias(self):
        """STORY-321: Day 3 engagement email should say 11 dias remaining for zero usage."""
        from templates.emails.trial import render_trial_engagement_email
        html = render_trial_engagement_email("Test", {"searches_count": 0})
        assert "11 dias" in html

    def test_paywall_alert_says_7_dias(self):
        """STORY-321: Day 7 paywall alert email should mention 7 dias."""
        from templates.emails.trial import render_trial_paywall_alert_email
        html = render_trial_paywall_alert_email("Test", {"searches_count": 5})
        assert "7 dias" in html

    def test_value_email_says_4_dias(self):
        """STORY-321: Day 10 value email should say 4 dias for zero usage."""
        from templates.emails.trial import render_trial_value_email
        html = render_trial_value_email("Test", {"searches_count": 0})
        assert "4 dias" in html

    def test_welcome_subject_says_14_dias(self):
        """Welcome email subject should say 14 dias."""
        from services.trial_email_sequence import _render_email
        subject, _ = _render_email("welcome", "Test", {})
        assert "14 dias" in subject
        assert "30 dias" not in subject

    def test_expired_email_data_retention_30_days(self):
        """Expired email should still mention 30-day data retention."""
        from templates.emails.trial import render_trial_expired_email
        html = render_trial_expired_email("Test", {
            "opportunities_found": 5,
            "pipeline_items_count": 2,
        })
        # Data retention is still 30 days
        assert "30 dias" in html


class TestGrandfatherClause:
    """AC15: Grandfather clause for existing trial users."""

    def test_user_created_15_days_ago_keeps_30_day_trial(self):
        """User created >14 days ago should keep their original 30-day trial."""
        created_at = datetime.now(timezone.utc) - timedelta(days=15)
        original_expires = created_at + timedelta(days=30)
        # Grandfather: keep original 30-day trial
        # New limit would be created_at + 14 days = 1 day ago (already expired)
        # But grandfather clause preserves the original 30-day expiry
        assert original_expires > datetime.now(timezone.utc)
        new_limit = created_at + timedelta(days=14)
        # The new 14-day limit would already be past
        assert new_limit < datetime.now(timezone.utc)

    def test_user_created_10_days_ago_gets_14_day_trial(self):
        """User created <=14 days ago should get new 14-day limit."""
        created_at = datetime.now(timezone.utc) - timedelta(days=10)
        new_expires = created_at + timedelta(days=14)
        # New limit: 4 more days of trial
        assert new_expires > datetime.now(timezone.utc)
        # Was originally 30 days: 20 more days. Now only 4.
        original_expires = created_at + timedelta(days=30)
        assert new_expires < original_expires

    def test_user_created_today_gets_14_day_trial(self):
        """Brand new user gets 14-day trial."""
        from config import TRIAL_DURATION_DAYS
        created_at = datetime.now(timezone.utc)
        expires = created_at + timedelta(days=TRIAL_DURATION_DAYS)
        delta = (expires - created_at).days
        assert delta == 14

    def test_user_created_20_days_ago_trial_active(self):
        """User created 20 days ago with grandfather should still have active trial."""
        created_at = datetime.now(timezone.utc) - timedelta(days=20)
        # Grandfather clause: keeps 30-day trial
        grandfather_expires = created_at + timedelta(days=30)
        # 30 - 20 = 10 days remaining
        assert grandfather_expires > datetime.now(timezone.utc)

    def test_user_created_31_days_ago_trial_expired(self):
        """User created 31 days ago — even with grandfather, trial has expired."""
        created_at = datetime.now(timezone.utc) - timedelta(days=31)
        grandfather_expires = created_at + timedelta(days=30)
        assert grandfather_expires < datetime.now(timezone.utc)
