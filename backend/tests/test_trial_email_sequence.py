"""
STORY-321 AC17-AC20: Tests for trial email sequence — 6 emails.

AC17: Tests for each email (6 emails x scenarios).
AC18: Tests for cron job (scheduling, dedup, rate limit, skip converted).
AC19: Tests for stats query.
AC20: Zero regressions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone, timedelta


SAMPLE_STATS = {
    "searches_count": 12,
    "opportunities_found": 47,
    "total_value_estimated": 2_350_000,
    "pipeline_items_count": 8,
    "sectors_searched": ["software", "medicamentos", "construcao"],
}

ZERO_STATS = {
    "searches_count": 0,
    "opportunities_found": 0,
    "total_value_estimated": 0,
    "pipeline_items_count": 0,
    "sectors_searched": [],
}

UNSUB_URL = "https://api.smartlic.tech/v1/trial-emails/unsubscribe?user_id=test&token=abc"


# ============================================================================
# AC1: Sequence definition tests
# ============================================================================

class TestSequenceDefinition:
    """AC1: Verify the 6-email sequence structure."""

    def test_sequence_has_6_emails(self):
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        assert len(TRIAL_EMAIL_SEQUENCE) == 6

    def test_sequence_days(self):
        """AC1: Correct day schedule: 0, 3, 7, 10, 13, 16."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        days = [e["day"] for e in TRIAL_EMAIL_SEQUENCE]
        assert days == [0, 3, 7, 10, 13, 16]

    def test_sequence_types(self):
        """AC1: Correct email types."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        types = [e["type"] for e in TRIAL_EMAIL_SEQUENCE]
        assert types == ["welcome", "engagement", "paywall_alert", "value", "last_day", "expired"]

    def test_sequence_numbers(self):
        """AC1: Sequential numbering 1-6."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        numbers = [e["number"] for e in TRIAL_EMAIL_SEQUENCE]
        assert numbers == [1, 2, 3, 4, 5, 6]


# ============================================================================
# AC13/AC14: Coupon tests
# ============================================================================

class TestCoupon:
    """AC13/AC14: Stripe coupon logic."""

    def test_coupon_constant(self):
        from services.trial_email_sequence import TRIAL_COMEBACK_COUPON
        assert TRIAL_COMEBACK_COUPON == "TRIAL_COMEBACK_20"

    def test_coupon_checkout_url(self):
        from services.trial_email_sequence import get_coupon_checkout_url
        url = get_coupon_checkout_url()
        assert "coupon=TRIAL_COMEBACK_20" in url
        assert "smartlic.tech" in url or "planos" in url


# ============================================================================
# AC19: Stats query tests
# ============================================================================

class TestGetTrialUserStats:
    """AC19: Test get_trial_user_stats function."""

    def test_returns_dict_with_required_keys(self):
        """AC12: Returns all required fields."""
        mock_base_stats = MagicMock()
        mock_base_stats.model_dump.return_value = {
            "searches_count": 5,
            "opportunities_found": 20,
            "total_value_estimated": 500_000,
            "pipeline_items_count": 3,
            "sectors_searched": ["software"],
        }

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"created_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()}]
        )

        with patch("services.trial_stats.get_trial_usage_stats", return_value=mock_base_stats), \
             patch("supabase_client.get_supabase", return_value=mock_sb):
            from services.trial_email_sequence import get_trial_user_stats
            result = get_trial_user_stats("user-123")

        assert "searches_executed" in result
        assert "opportunities_found" in result
        assert "total_value_analyzed" in result
        assert "pipeline_items" in result
        assert "days_remaining" in result
        assert result["searches_executed"] == 5
        assert result["days_remaining"] in (3, 4)  # 14 - 10, +/- 1 due to time-of-day

    def test_days_remaining_zero_when_expired(self):
        """Days remaining is 0 when trial has expired."""
        mock_base_stats = MagicMock()
        mock_base_stats.model_dump.return_value = {
            "searches_count": 0,
            "opportunities_found": 0,
            "total_value_estimated": 0,
            "pipeline_items_count": 0,
            "sectors_searched": [],
        }

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"created_at": (datetime.now(timezone.utc) - timedelta(days=35)).isoformat()}]
        )

        with patch("services.trial_stats.get_trial_usage_stats", return_value=mock_base_stats), \
             patch("supabase_client.get_supabase", return_value=mock_sb):
            from services.trial_email_sequence import get_trial_user_stats
            result = get_trial_user_stats("user-456")

        assert result["days_remaining"] == 0

    def test_handles_missing_profile(self):
        """Returns 0 days_remaining when profile not found."""
        mock_base_stats = MagicMock()
        mock_base_stats.model_dump.return_value = {
            "searches_count": 0,
            "opportunities_found": 0,
            "total_value_estimated": 0,
            "pipeline_items_count": 0,
            "sectors_searched": [],
        }

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        with patch("services.trial_stats.get_trial_usage_stats", return_value=mock_base_stats), \
             patch("supabase_client.get_supabase", return_value=mock_sb):
            from services.trial_email_sequence import get_trial_user_stats
            result = get_trial_user_stats("user-missing")

        assert result["days_remaining"] == 0

    def test_handles_db_error_gracefully(self):
        """Returns 0 days_remaining on DB error."""
        mock_base_stats = MagicMock()
        mock_base_stats.model_dump.return_value = {
            "searches_count": 0,
            "opportunities_found": 0,
            "total_value_estimated": 0,
            "pipeline_items_count": 0,
            "sectors_searched": [],
        }

        mock_sb = MagicMock()
        mock_sb.table.side_effect = Exception("DB unavailable")

        with patch("services.trial_stats.get_trial_usage_stats", return_value=mock_base_stats), \
             patch("supabase_client.get_supabase", return_value=mock_sb):
            from services.trial_email_sequence import get_trial_user_stats
            result = get_trial_user_stats("user-err")

        assert result["days_remaining"] == 0
        assert result["searches_executed"] == 0


# ============================================================================
# AC18: Cron job / process_trial_emails tests
# ============================================================================

class TestProcessTrialEmails:
    """AC18: Test the process_trial_emails dispatch function."""

    @pytest.mark.asyncio
    async def test_disabled_flag_skips(self):
        """AC3: When TRIAL_EMAILS_ENABLED=false, does nothing."""
        with patch("config.TRIAL_EMAILS_ENABLED", False):
            from services.trial_email_sequence import process_trial_emails
            result = await process_trial_emails()
            assert result.get("disabled") is True
            assert result["sent"] == 0

    @pytest.mark.asyncio
    async def test_sends_welcome_email_day_0(self):
        """AC1: Day 0 users receive welcome email."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain

                call_count = [0]
                def execute():
                    call_count[0] += 1
                    if call_count[0] == 1:  # First call is for day 0 (welcome)
                        return MagicMock(data=[{
                            "id": "user-welcome-uuid",
                            "email": "new@example.com",
                            "full_name": "Novo Usuario",
                            "plan_type": "free_trial",
                            "marketing_emails_enabled": True,
                        }])
                    return MagicMock(data=[])
                chain.execute = AsyncMock(side_effect=execute)
                return chain
            elif name == "trial_email_log":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.limit.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[]))
                chain.insert.return_value = chain
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        mock_stats = {
            **ZERO_STATS,
            "searches_executed": 0,
            "total_value_analyzed": 0,
            "pipeline_items": 0,
            "days_remaining": 14,
        }

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("services.trial_email_sequence.get_trial_user_stats", return_value=mock_stats), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails()

            assert result["sent"] >= 1
            mock_send.assert_called()
            first_call = mock_send.call_args_list[0]
            assert "Bem-vindo" in first_call.kwargs.get("subject", "") or "Bem-vindo" in str(first_call)

    @pytest.mark.asyncio
    async def test_skips_converted_users(self):
        """AC4: Users who converted to paid are skipped."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[{
                    "id": "user-paid-uuid",
                    "email": "paid@example.com",
                    "full_name": "Paid User",
                    "plan_type": "smartlic_pro",
                    "marketing_emails_enabled": True,
                }]))
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails()

            assert result["converted_skipped"] >= 1
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_unsubscribed_marketing_but_sends_conversion(self):
        """AC5 + P2 §1.2: Users who opted out of marketing emails still receive conversion emails.

        Marketing emails (welcome, engagement) are skipped, but conversion-critical
        emails (paywall_alert, value, last_day, expired) are still sent.
        """
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[{
                    "id": "user-unsub-uuid",
                    "email": "unsub@example.com",
                    "full_name": "Unsub User",
                    "plan_type": "free_trial",
                    "marketing_emails_enabled": False,
                }]))
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails()

            # Marketing emails (welcome, engagement) should be skipped
            assert result["unsubscribed_skipped"] >= 1
            # Conversion emails (paywall_alert, value, last_day, expired) should still be sent
            assert mock_send.call_count >= 1
            sent_types = [
                call.kwargs.get("tags", call.args[-1] if len(call.args) > 3 else [])
                for call in mock_send.call_args_list
            ]
            # Verify only conversion emails were sent (no welcome/engagement)
            for call in mock_send.call_args_list:
                tags = call.kwargs.get("tags", [])
                email_type = next((t["value"] for t in tags if t["name"] == "type"), None)
                assert email_type in ("paywall_alert", "value", "last_day", "expired"), \
                    f"Marketing email '{email_type}' should not be sent to unsubscribed user"

    @pytest.mark.asyncio
    async def test_skips_fully_unsubscribed_users(self):
        """AC5: Users who opted out of BOTH marketing and conversion emails get no emails."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[{
                    "id": "user-unsub-uuid",
                    "email": "unsub@example.com",
                    "full_name": "Unsub User",
                    "plan_type": "free_trial",
                    "marketing_emails_enabled": False,
                    "trial_conversion_emails_enabled": False,
                }]))
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails()

            assert result["unsubscribed_skipped"] >= 1
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_idempotency_skips_already_sent(self):
        """AC6: Running job twice doesn't send duplicate emails."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain

                call_count = [0]
                def execute():
                    call_count[0] += 1
                    if call_count[0] == 1:
                        return MagicMock(data=[{
                            "id": "user-dup-uuid",
                            "email": "dup@example.com",
                            "full_name": "Dup User",
                            "plan_type": "free_trial",
                            "marketing_emails_enabled": True,
                        }])
                    return MagicMock(data=[])
                chain.execute = AsyncMock(side_effect=execute)
                return chain
            elif name == "trial_email_log":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.limit.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": "existing-log"}]))
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("email_service.send_email_async") as mock_send, \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails()

            assert result["skipped"] >= 1
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_limit_respected(self):
        """AC10: Batch limit stops processing after max emails."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()

        def table_side_effect(name):
            if name == "profiles":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.gte.return_value = chain
                chain.lt.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[
                    {
                        "id": f"user-batch-{i}",
                        "email": f"batch{i}@example.com",
                        "full_name": f"Batch User {i}",
                        "plan_type": "free_trial",
                        "marketing_emails_enabled": True,
                    }
                    for i in range(10)
                ]))
                return chain
            elif name == "trial_email_log":
                chain = MagicMock()
                chain.select.return_value = chain
                chain.eq.return_value = chain
                chain.limit.return_value = chain
                chain.execute = AsyncMock(return_value=MagicMock(data=[]))
                chain.insert.return_value = chain
                return chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        mock_stats_dict = {
            **ZERO_STATS,
            "searches_executed": 0,
            "total_value_analyzed": 0,
            "pipeline_items": 0,
            "days_remaining": 14,
        }

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect), \
             patch("services.trial_email_sequence.get_trial_user_stats", return_value=mock_stats_dict), \
             patch("email_service.send_email_async"), \
             patch("metrics.TRIAL_EMAILS_SENT"):

            result = await process_trial_emails(batch_size=5)

            assert result["sent"] <= 5

    @pytest.mark.asyncio
    async def test_no_users_at_milestone(self):
        """No users at any milestone = zero sent."""
        from services.trial_email_sequence import process_trial_emails

        mock_sb = MagicMock()
        empty_chain = MagicMock()
        empty_chain.select.return_value = empty_chain
        empty_chain.eq.return_value = empty_chain
        empty_chain.gte.return_value = empty_chain
        empty_chain.lt.return_value = empty_chain
        empty_chain.execute = AsyncMock(return_value=MagicMock(data=[]))

        mock_sb.table.return_value = empty_chain

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect):

            result = await process_trial_emails()
            assert result["sent"] == 0
            assert result["errors"] == 0


# ============================================================================
# Unsubscribe + Webhook tests
# ============================================================================

class TestUnsubscribe:
    """Test unsubscribe token generation and verification."""

    def test_token_roundtrip(self):
        from services.trial_email_sequence import _generate_unsubscribe_token, verify_unsubscribe_token
        user_id = "test-user-123"
        token = _generate_unsubscribe_token(user_id)
        assert verify_unsubscribe_token(user_id, token) is True

    def test_invalid_token_rejected(self):
        from services.trial_email_sequence import verify_unsubscribe_token
        assert verify_unsubscribe_token("test-user-123", "invalid-token") is False

    def test_different_user_rejected(self):
        from services.trial_email_sequence import _generate_unsubscribe_token, verify_unsubscribe_token
        token = _generate_unsubscribe_token("user-1")
        assert verify_unsubscribe_token("user-2", token) is False

    def test_url_generation(self):
        from services.trial_email_sequence import get_unsubscribe_url
        url = get_unsubscribe_url("user-123")
        assert "user_id=user-123" in url
        assert "token=" in url


class TestRenderEmail:
    """Test _render_email dispatcher for all 6 types."""

    def test_all_6_types_render(self):
        """All 6 email types render without error."""
        from services.trial_email_sequence import _render_email

        for email_type in [
            "welcome", "engagement", "paywall_alert",
            "value", "last_day", "expired",
        ]:
            subject, html = _render_email(
                email_type=email_type,
                user_name="Test User",
                stats=SAMPLE_STATS,
                unsubscribe_url=UNSUB_URL,
            )
            assert subject, f"Empty subject for {email_type}"
            assert "<!DOCTYPE html>" in html, f"Invalid HTML for {email_type}"

    def test_unknown_type_raises(self):
        from services.trial_email_sequence import _render_email
        with pytest.raises(ValueError, match="Unknown email type"):
            _render_email(email_type="nonexistent", user_name="T", stats={})

    def test_expired_includes_coupon(self):
        """AC14: Expired email render includes coupon URL."""
        from services.trial_email_sequence import _render_email
        subject, html = _render_email(
            email_type="expired",
            user_name="Test",
            stats=SAMPLE_STATS,
        )
        assert "coupon" in html.lower() or "20%" in html

    def test_expired_subject_includes_20_off(self):
        """AC14: Expired email subject mentions 20% off."""
        from services.trial_email_sequence import _render_email
        subject, html = _render_email(
            email_type="expired",
            user_name="Test",
            stats=SAMPLE_STATS,
        )
        assert "20%" in subject


class TestResendWebhook:
    """AC11: Test Resend webhook handler."""

    @pytest.mark.asyncio
    async def test_handles_opened_event(self):
        from services.trial_email_sequence import handle_resend_webhook

        mock_sb = MagicMock()
        mock_chain = MagicMock()
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.is_.return_value = mock_chain
        mock_chain.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_sb.table.return_value = mock_chain

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect):
            result = await handle_resend_webhook("email.opened", {"email_id": "res-123"})
            assert result is True

    @pytest.mark.asyncio
    async def test_handles_clicked_event(self):
        from services.trial_email_sequence import handle_resend_webhook

        mock_sb = MagicMock()
        mock_chain = MagicMock()
        mock_chain.update.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.is_.return_value = mock_chain
        mock_chain.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_sb.table.return_value = mock_chain

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("supabase_client.sb_execute", side_effect=_sb_execute_side_effect):
            result = await handle_resend_webhook("email.clicked", {"email_id": "res-456"})
            assert result is True

    @pytest.mark.asyncio
    async def test_ignores_unknown_event(self):
        from services.trial_email_sequence import handle_resend_webhook
        result = await handle_resend_webhook("email.bounced", {"email_id": "res-789"})
        assert result is False

    @pytest.mark.asyncio
    async def test_skips_missing_email_id(self):
        from services.trial_email_sequence import handle_resend_webhook
        result = await handle_resend_webhook("email.opened", {})
        assert result is False


# ============================================================================
# Cron Integration tests
# ============================================================================

class TestCronJobIntegration:
    """Test cron_jobs.py integration with trial email sequence."""

    def test_trial_sequence_constants_exist(self):
        from cron_jobs import TRIAL_SEQUENCE_INTERVAL_SECONDS, TRIAL_SEQUENCE_BATCH_SIZE
        assert TRIAL_SEQUENCE_INTERVAL_SECONDS == 86400
        assert TRIAL_SEQUENCE_BATCH_SIZE == 50

    @pytest.mark.asyncio
    async def test_start_trial_sequence_task_returns_task(self):
        import asyncio
        from cron_jobs import start_trial_sequence_task
        task = await start_trial_sequence_task()
        assert isinstance(task, asyncio.Task)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


# ============================================================================
# Helpers
# ============================================================================

async def _sb_execute_side_effect(query):
    """Mock sb_execute: call .execute() on the query chain."""
    if hasattr(query, 'execute'):
        result = query.execute
        if callable(result):
            ret = result()
            if hasattr(ret, '__await__'):
                return await ret
            return ret
        return result
    return query


_mock_sb_execute = AsyncMock(side_effect=_sb_execute_side_effect)
