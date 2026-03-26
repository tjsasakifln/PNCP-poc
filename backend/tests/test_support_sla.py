"""Tests for STORY-353: Support SLA infrastructure.

AC9: Mock business hours vs weekends, test cron job, SLA endpoint, reply tracking.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
import pytest

from business_hours import calculate_business_hours, is_within_business_hours


# ============================================================================
# AC8+AC9: Business Hours Calculation
# ============================================================================


class TestCalculateBusinessHours:
    """Test business hours calculation with various scenarios."""

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_same_day_within_hours(self):
        """Full day within business hours = 10h."""
        start = datetime(2026, 3, 2, 11, 0, tzinfo=timezone.utc)  # 08:00 BRT
        end = datetime(2026, 3, 2, 21, 0, tzinfo=timezone.utc)    # 18:00 BRT
        result = calculate_business_hours(start, end)
        assert result == 10.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_partial_day(self):
        """Half day: 8:00-13:00 BRT = 5h."""
        start = datetime(2026, 3, 2, 11, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 2, 16, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 5.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_weekend_skipped(self):
        """Friday 17:00 BRT to Monday 09:00 BRT = 2h (1h Fri + 1h Mon)."""
        start = datetime(2026, 2, 27, 20, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 2.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_entirely_weekend(self):
        """Saturday to Sunday = 0h."""
        start = datetime(2026, 2, 28, 10, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 0.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_two_full_business_days(self):
        """Monday 8:00 to Wednesday 18:00 BRT = 30h (3 full days)."""
        start = datetime(2026, 3, 2, 11, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 4, 21, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 30.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_before_business_hours(self):
        """6:00-7:00 BRT = 0h (before opening)."""
        start = datetime(2026, 3, 2, 9, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 0.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_after_business_hours(self):
        """19:00-22:00 BRT = 0h (after closing)."""
        start = datetime(2026, 3, 2, 22, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 3, 1, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 0.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_end_before_start(self):
        """End before start = 0h."""
        start = datetime(2026, 3, 2, 15, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 2, 14, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 0.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_naive_datetimes_assumed_utc(self):
        """Naive datetimes are treated as UTC."""
        start = datetime(2026, 3, 2, 11, 0)
        end = datetime(2026, 3, 2, 16, 0)
        result = calculate_business_hours(start, end)
        assert result == 5.0

    @patch("config.BUSINESS_HOURS_START", 9)
    @patch("config.BUSINESS_HOURS_END", 17)
    def test_custom_hours_9_to_17(self):
        """Custom 9-17 BRT = 8h per day."""
        start = datetime(2026, 3, 2, 12, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 2, 20, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 8.0

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_cross_midnight(self):
        """Mon 16:00 BRT to Tue 10:00 BRT = 4h (2h Mon + 2h Tue)."""
        start = datetime(2026, 3, 2, 19, 0, tzinfo=timezone.utc)
        end = datetime(2026, 3, 3, 13, 0, tzinfo=timezone.utc)
        result = calculate_business_hours(start, end)
        assert result == 4.0


class TestIsWithinBusinessHours:
    """Test business hours boundary check."""

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_within_hours_weekday(self):
        dt = datetime(2026, 3, 2, 13, 0, tzinfo=timezone.utc)
        assert is_within_business_hours(dt) is True

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_outside_hours_weekday(self):
        dt = datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc)
        assert is_within_business_hours(dt) is False

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_weekend_saturday(self):
        dt = datetime(2026, 2, 28, 13, 0, tzinfo=timezone.utc)
        assert is_within_business_hours(dt) is False

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_weekend_sunday(self):
        dt = datetime(2026, 3, 1, 15, 0, tzinfo=timezone.utc)
        assert is_within_business_hours(dt) is False

    @patch("config.BUSINESS_HOURS_START", 8)
    @patch("config.BUSINESS_HOURS_END", 18)
    def test_at_closing_time(self):
        dt = datetime(2026, 3, 2, 21, 0, tzinfo=timezone.utc)
        assert is_within_business_hours(dt) is False


# ============================================================================
# AC3+AC4: Cron Job — check_unanswered_messages
# ============================================================================


class TestCheckUnansweredMessages:
    """Test the cron job that checks for unanswered messages."""

    @pytest.mark.asyncio
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    @patch("supabase_client.get_supabase")
    @patch("config.SUPPORT_SLA_ALERT_THRESHOLD_HOURS", 20)
    async def test_no_unanswered(self, mock_get_sb, mock_sb_execute):
        """No unanswered conversations = no alerts."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_get_sb.return_value = mock_sb

        mock_sb_execute.return_value = Mock(data=[])

        from cron_jobs import check_unanswered_messages
        result = await check_unanswered_messages()

        assert result["checked"] == 0
        assert result["breached"] == 0
        assert result["alerted"] == 0

    @pytest.mark.asyncio
    @patch("email_service.send_email_async")
    @patch("business_hours.calculate_business_hours", return_value=25.0)
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    @patch("supabase_client.get_supabase")
    @patch("config.SUPPORT_SLA_ALERT_THRESHOLD_HOURS", 20)
    async def test_breached_sends_alert(
        self, mock_get_sb, mock_sb_execute, mock_calc_bh, mock_send_email
    ):
        """Conversations exceeding threshold trigger alert email."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_get_sb.return_value = mock_sb

        mock_sb_execute.return_value = Mock(data=[
            {
                "id": "conv-1",
                "user_id": "user-1",
                "subject": "Preciso de ajuda",
                "category": "suporte",
                "created_at": "2026-02-27T10:00:00+00:00",
            }
        ])

        from cron_jobs import check_unanswered_messages
        result = await check_unanswered_messages()

        assert result["checked"] == 1
        assert result["breached"] == 1
        assert result["alerted"] == 1
        mock_send_email.assert_called_once()

        call_args = mock_send_email.call_args
        assert "[SLA]" in call_args.kwargs.get("subject", call_args[1].get("subject", ""))

    @pytest.mark.asyncio
    @patch("business_hours.calculate_business_hours", return_value=5.0)
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    @patch("supabase_client.get_supabase")
    @patch("config.SUPPORT_SLA_ALERT_THRESHOLD_HOURS", 20)
    async def test_under_threshold_no_alert(
        self, mock_get_sb, mock_sb_execute, mock_calc_bh
    ):
        """Conversations under threshold don't trigger alerts."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_get_sb.return_value = mock_sb

        mock_sb_execute.return_value = Mock(data=[
            {
                "id": "conv-1",
                "user_id": "user-1",
                "subject": "Pergunta rapida",
                "category": "suporte",
                "created_at": "2026-03-01T10:00:00+00:00",
            }
        ])

        from cron_jobs import check_unanswered_messages
        result = await check_unanswered_messages()

        assert result["checked"] == 1
        assert result["breached"] == 0
        assert result["alerted"] == 0


# ============================================================================
# AC6: Support SLA Endpoint
# ============================================================================


class TestSupportSlaEndpoint:
    """Test GET /admin/support-sla endpoint."""

    def _create_client(self, admin_user=None):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from admin import router, require_admin

        app = FastAPI()
        app.include_router(router)
        if admin_user:
            app.dependency_overrides[require_admin] = lambda: admin_user
        return TestClient(app)

    @patch("business_hours.calculate_business_hours", return_value=4.5)
    @patch("supabase_client.get_supabase")
    def test_sla_metrics_success(self, mock_get_sb, mock_calc_bh):
        """Returns SLA metrics for admin."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.not_ = mock_sb  # property access, not method call
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        responded_result = Mock(data=[
            {"created_at": "2026-03-01T10:00:00+00:00", "first_response_at": "2026-03-01T14:30:00+00:00"},
        ])
        pending_result = Mock(data=[], count=0)

        mock_sb.execute.side_effect = [responded_result, pending_result]
        mock_get_sb.return_value = mock_sb

        admin = {"id": "admin-001", "email": "admin@test.com"}
        client = self._create_client(admin_user=admin)

        resp = client.get("/admin/support-sla")
        assert resp.status_code == 200
        data = resp.json()
        assert "avg_response_hours" in data
        assert "pending_count" in data
        assert "breached_count" in data
        assert data["pending_count"] == 0
        assert data["breached_count"] == 0

    @patch("business_hours.calculate_business_hours", return_value=25.0)
    @patch("supabase_client.get_supabase")
    @patch("config.SUPPORT_SLA_ALERT_THRESHOLD_HOURS", 20)
    def test_sla_breached_conversations(self, mock_get_sb, mock_calc_bh):
        """Counts breached conversations correctly."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.not_ = mock_sb  # property access, not method call
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        responded_result = Mock(data=[])
        pending_result = Mock(data=[
            {"id": "conv-1", "created_at": "2026-02-25T10:00:00+00:00"},
            {"id": "conv-2", "created_at": "2026-02-26T10:00:00+00:00"},
        ], count=2)

        mock_sb.execute.side_effect = [responded_result, pending_result]
        mock_get_sb.return_value = mock_sb

        admin = {"id": "admin-001", "email": "admin@test.com"}
        client = self._create_client(admin_user=admin)

        resp = client.get("/admin/support-sla")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending_count"] == 2
        assert data["breached_count"] == 2

    @patch("supabase_client.get_supabase")
    def test_sla_no_data(self, mock_get_sb):
        """Returns zeros when no conversations exist."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.not_ = mock_sb  # property access, not method call
        mock_sb.is_.return_value = mock_sb
        mock_sb.neq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb

        mock_sb.execute.return_value = Mock(data=[], count=0)
        mock_get_sb.return_value = mock_sb

        admin = {"id": "admin-001", "email": "admin@test.com"}
        client = self._create_client(admin_user=admin)

        resp = client.get("/admin/support-sla")
        assert resp.status_code == 200
        data = resp.json()
        assert data["avg_response_hours"] == 0.0
        assert data["pending_count"] == 0
        assert data["breached_count"] == 0


# ============================================================================
# AC2: Reply tracking — first_response_at
# ============================================================================


class TestReplyTracking:
    """Test that admin reply sets first_response_at."""

    def _create_client(self, user=None):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from auth import require_auth
        from routes.messages import router

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[require_auth] = lambda: (
            user or {"id": "user-123", "email": "test@example.com"}
        )
        return TestClient(app)

    @patch("metrics.SUPPORT_RESPONSE_TIME_HOURS")
    @patch("business_hours.calculate_business_hours", return_value=3.5)
    @patch("routes.messages._is_admin", return_value=True)
    @patch("routes.messages.sb_execute", new_callable=AsyncMock)
    @patch("routes.messages._get_sb")
    def test_admin_reply_sets_first_response(
        self, mock_get_sb, mock_sb_execute, mock_is_admin,
        mock_calc_bh, mock_metric
    ):
        """Admin reply on conversation without first_response_at sets it."""
        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.insert.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.is_.return_value = mock_sb
        mock_sb.single.return_value = mock_sb

        conv_id = "a1b2c3d4-e5f6-4890-abcd-ef1234567890"

        conv_data = {
            "id": conv_id,
            "user_id": "user-456",
            "status": "aberto",
            "created_at": "2026-03-01T10:00:00+00:00",
            "first_response_at": None,
        }

        mock_sb_execute.side_effect = [
            Mock(data=conv_data),   # conv query (single)
            Mock(data=[{"id": "msg-1"}]),  # message insert
            Mock(data=[conv_data]),  # first_response_at update
            Mock(data=[conv_data]),  # status update
        ]
        mock_get_sb.return_value = mock_sb

        admin_user = {"id": "admin-999", "email": "admin@test.com"}
        client = self._create_client(user=admin_user)

        resp = client.post(
            f"/api/messages/conversations/{conv_id}/reply",
            json={"body": "Resposta do admin"},
        )

        assert resp.status_code == 201
        assert mock_sb_execute.call_count >= 3
        mock_metric.observe.assert_called_once_with(3.5)


# ============================================================================
# AC5: Prometheus metrics existence
# ============================================================================


class TestSupportMetrics:
    """Verify STORY-353 Prometheus metrics are defined."""

    def test_pending_messages_gauge_exists(self):
        from metrics import SUPPORT_PENDING_MESSAGES
        assert SUPPORT_PENDING_MESSAGES is not None
        assert hasattr(SUPPORT_PENDING_MESSAGES, "set")

    def test_response_time_histogram_exists(self):
        from metrics import SUPPORT_RESPONSE_TIME_HOURS
        assert SUPPORT_RESPONSE_TIME_HOURS is not None
        assert hasattr(SUPPORT_RESPONSE_TIME_HOURS, "observe")


# ============================================================================
# Config values
# ============================================================================


class TestSupportSlaConfig:
    """Verify STORY-353 config values are defined."""

    def test_business_hours_defaults(self):
        from config import BUSINESS_HOURS_START, BUSINESS_HOURS_END
        assert BUSINESS_HOURS_START == 8
        assert BUSINESS_HOURS_END == 18

    def test_sla_check_interval(self):
        from config import SUPPORT_SLA_CHECK_INTERVAL_SECONDS
        assert SUPPORT_SLA_CHECK_INTERVAL_SECONDS == 4 * 60 * 60

    def test_sla_alert_threshold(self):
        from config import SUPPORT_SLA_ALERT_THRESHOLD_HOURS
        assert SUPPORT_SLA_ALERT_THRESHOLD_HOURS == 20
