"""Tests for UX-433: Histórico mostra excesso de falhas e timeouts.

AC3: hide_old_failures param in GET /sessions
AC4: instant failure (< 3s) deletion in update_search_session_status
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from auth import require_auth
from database import get_db
from routes.sessions import router


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
MOCK_USER = {"id": "user-123-uuid", "email": "test@example.com", "role": "authenticated"}


def _create_client(mock_db=None):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth] = lambda: MOCK_USER
    if mock_db is not None:
        app.dependency_overrides[get_db] = lambda: mock_db
    return TestClient(app)


def _mock_sb(data=None, count=0):
    sb = Mock()
    sb.table.return_value = sb
    sb.select.return_value = sb
    sb.eq.return_value = sb
    sb.in_.return_value = sb
    sb.or_.return_value = sb
    sb.order.return_value = sb
    sb.range.return_value = sb
    result = Mock(data=data or [], count=count)
    sb.execute.return_value = result
    return sb


# ──────────────────────────────────────────────────────────────────────────────
# AC3: hide_old_failures query param
# ──────────────────────────────────────────────────────────────────────────────
class TestHideOldFailures:
    """GET /sessions?hide_old_failures= (UX-433 AC3)"""

    def test_default_hides_old_failures(self):
        """hide_old_failures=True (default): or_ filter is applied to exclude old failures."""
        sb = _mock_sb(data=[], count=0)
        client = _create_client(mock_db=sb)

        resp = client.get("/sessions")

        assert resp.status_code == 200
        # or_ should have been called with the age filter
        sb.or_.assert_called_once()
        filter_arg = sb.or_.call_args[0][0]
        assert "status.not.in.(failed,timed_out)" in filter_arg
        assert "created_at.gte." in filter_arg

    def test_hide_old_failures_false_skips_age_filter(self):
        """hide_old_failures=False: or_ age filter NOT applied."""
        sb = _mock_sb(data=[], count=0)
        client = _create_client(mock_db=sb)

        resp = client.get("/sessions?hide_old_failures=false")

        assert resp.status_code == 200
        # or_ should NOT have been called (no age filter)
        sb.or_.assert_not_called()

    def test_hide_old_failures_not_applied_with_explicit_failed_status(self):
        """When status=failed, age filter is skipped (user explicitly wants failures)."""
        sb = _mock_sb(data=[], count=0)
        client = _create_client(mock_db=sb)

        resp = client.get("/sessions?status=failed")

        assert resp.status_code == 200
        # status=failed uses in_() filter, not or_() age filter
        sb.in_.assert_called_once_with("status", ["failed", "timed_out"])
        sb.or_.assert_not_called()

    def test_hide_old_failures_not_applied_with_completed_status(self):
        """When status=completed, age filter is skipped (completed has no failures)."""
        sb = _mock_sb(data=[], count=0)
        client = _create_client(mock_db=sb)

        resp = client.get("/sessions?status=completed")

        assert resp.status_code == 200
        # status=completed uses or_() for ISSUE-040 legacy logic, not the age filter
        sb.or_.assert_called_once()
        filter_arg = sb.or_.call_args[0][0]
        # Should be the completed-status filter, not the age filter
        assert "status.eq.completed" in filter_arg
        assert "status.not.in.(failed,timed_out)" not in filter_arg

    def test_age_filter_uses_7_day_window(self):
        """The age cutoff is exactly 7 days ago."""
        sb = _mock_sb(data=[], count=0)
        client = _create_client(mock_db=sb)

        before_call = datetime.now(timezone.utc) - timedelta(days=7)
        resp = client.get("/sessions")
        after_call = datetime.now(timezone.utc) - timedelta(days=7)

        assert resp.status_code == 200
        filter_arg = sb.or_.call_args[0][0]
        # Extract the date portion from the filter string
        # format: "...created_at.gte.2026-01-03T..."
        date_start = filter_arg.find("created_at.gte.") + len("created_at.gte.")
        date_str = filter_arg[date_start:]
        parsed = datetime.fromisoformat(date_str)
        assert before_call <= parsed.replace(tzinfo=timezone.utc) <= after_call


# ──────────────────────────────────────────────────────────────────────────────
# AC4: Instant failure deletion
# ──────────────────────────────────────────────────────────────────────────────
class TestInstantFailureDeletion:
    """update_search_session_status with instant failures (UX-433 AC4)"""

    @pytest.mark.asyncio
    async def test_instant_failure_deletes_session(self):
        """status='failed' + duration_ms < 3000 triggers DELETE instead of UPDATE."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.delete.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(return_value=Mock(data=[]))

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="failed",
                duration_ms=2999,
            )

        # DELETE should have been called, not UPDATE
        mock_sb.delete.assert_called_once()
        mock_sb.eq.assert_called_once_with("id", "session-abc-123")

    @pytest.mark.asyncio
    async def test_instant_failure_exactly_3000ms_is_not_deleted(self):
        """duration_ms = 3000 is NOT an instant failure — boundary condition."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(return_value=Mock(data=[]))

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="failed",
                duration_ms=3000,
            )

        # UPDATE should have been called, NOT delete
        mock_sb.update.assert_called_once()
        mock_sb.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_timed_out_is_never_deleted_regardless_of_duration(self):
        """status='timed_out' is never treated as instant failure (it ran for a while)."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(return_value=Mock(data=[]))

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="timed_out",
                duration_ms=500,  # Even very short timed_out is NOT deleted
            )

        mock_sb.update.assert_called_once()
        mock_sb.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_without_duration_ms_is_not_deleted(self):
        """status='failed' without duration_ms is not deleted (no info to decide)."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(return_value=Mock(data=[]))

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="failed",
                duration_ms=None,  # Unknown duration — keep the record
            )

        mock_sb.update.assert_called_once()
        mock_sb.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_normal_failed_search_updates_not_deletes(self):
        """status='failed' with duration_ms >= 3000 updates session normally."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(return_value=Mock(data=[]))

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="failed",
                duration_ms=45000,
                error_message="Pipeline timeout at source PNCP",
            )

        mock_sb.update.assert_called_once()
        update_payload = mock_sb.update.call_args[0][0]
        assert update_payload["status"] == "failed"
        assert "error_message" in update_payload
        mock_sb.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_failure_does_not_propagate(self):
        """If DELETE throws, the function catches and logs — no exception raised."""
        from quota.session_tracker import update_search_session_status

        mock_sb = Mock()
        mock_sb.table.return_value = mock_sb
        mock_sb.delete.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.execute = AsyncMock(side_effect=Exception("DB connection error"))

        # Should NOT raise
        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await update_search_session_status(
                session_id="session-abc-123",
                status="failed",
                duration_ms=500,
            )
        # If we get here, no exception was raised — test passes
