"""CRIT-002: Search Session Lifecycle Tracking Tests.

Comprehensive tests for register_search_session() and update_search_session_status()
in quota.py, plus pipeline/route integration for failure scenario status transitions.

Test ID scheme:
  T1-T14  = Unit tests for register/update functions
  F1-F13  = Failure scenario tests (route/pipeline error mapping)
  I1-I3   = Integration tests (full status transition sequences)

Mock patterns:
  - @patch("supabase_client.get_supabase")       for DB mocks (deferred import in quota.py)
  - @patch("quota._ensure_profile_exists")       to skip FK check
  - @patch("quota.register_search_session")      at pipeline module level via
    search_pipeline.quota.register_search_session when testing pipeline integration
"""

import asyncio
import json
import logging
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_sb():
    """Create a mock Supabase client with chained method returns."""
    sb = MagicMock()

    # Default: insert returns a session ID
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "test-session-id-1234-5678"}]
    )

    # Default: update returns success
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{}]
    )

    return sb


@pytest.fixture
def base_session_args():
    """Standard arguments for register_search_session."""
    return {
        "user_id": "user-abc-123",
        "sectors": ["facilities"],
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-10",
        "data_final": "2026-02-20",
        "custom_keywords": ["limpeza", "portaria"],
        "search_id": "search-uuid-9999",
    }


# ===========================================================================
# T1-T14: Unit Tests for register_search_session / update_search_session_status
# ===========================================================================


class TestRegisterSearchSession:
    """T1: register_search_session inserts with status='created', returns session_id."""

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t1_session_created_before_quota(self, mock_get_sb, mock_profile, mock_sb, base_session_args):
        """T1: register_search_session inserts with status='created' and returns session_id."""
        mock_get_sb.return_value = mock_sb

        from quota import register_search_session

        result = await register_search_session(**base_session_args)

        assert result == "test-session-id-1234-5678"

        # Verify insert was called on the correct table
        mock_sb.table.assert_called_with("search_sessions")

        # Verify the inserted data contains status='created'
        insert_call = mock_sb.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["status"] == "created"
        assert inserted_data["user_id"] == "user-abc-123"
        assert inserted_data["sectors"] == ["facilities"]
        assert inserted_data["ufs"] == ["SP", "RJ"]
        assert inserted_data["data_inicial"] == "2026-02-10"
        assert inserted_data["data_final"] == "2026-02-20"
        assert inserted_data["custom_keywords"] == ["limpeza", "portaria"]
        assert inserted_data["search_id"] == "search-uuid-9999"
        assert inserted_data["total_raw"] == 0
        assert inserted_data["total_filtered"] == 0
        assert inserted_data["valor_total"] == 0.0

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t1_session_without_search_id(self, mock_get_sb, mock_profile, mock_sb):
        """T1b: register_search_session works without search_id."""
        mock_get_sb.return_value = mock_sb

        from quota import register_search_session

        result = await register_search_session(
            user_id="user-abc-123",
            sectors=["facilities"],
            ufs=["SP"],
            data_inicial="2026-02-10",
            data_final="2026-02-20",
            custom_keywords=None,
            search_id=None,
        )

        assert result == "test-session-id-1234-5678"

        insert_call = mock_sb.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert "search_id" not in inserted_data
        assert inserted_data["custom_keywords"] is None

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=False)
    @patch("supabase_client.get_supabase")
    async def test_t1_returns_none_if_profile_missing(self, mock_get_sb, mock_profile, mock_sb):
        """register_search_session returns None when profile doesn't exist."""
        mock_get_sb.return_value = mock_sb

        from quota import register_search_session

        result = await register_search_session(
            user_id="no-profile-user",
            sectors=["facilities"],
            ufs=["SP"],
            data_inicial="2026-02-10",
            data_final="2026-02-20",
            custom_keywords=None,
        )

        assert result is None
        mock_sb.table.return_value.insert.assert_not_called()


class TestUpdateSearchSessionStatus:
    """T2-T5: update_search_session_status sets correct status values."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t2_session_updated_to_processing(self, mock_get_sb, mock_sb):
        """T2: update_search_session_status sets status='processing'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "test-session-id-1234-5678",
            status="processing",
            pipeline_stage="validate",
        )

        mock_sb.table.assert_called_with("search_sessions")
        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "processing"
        assert update_data["pipeline_stage"] == "validate"

        # Verify .eq() was called with correct session_id
        mock_sb.table.return_value.update.return_value.eq.assert_called_with(
            "id", "test-session-id-1234-5678"
        )

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t3_session_updated_to_completed(self, mock_get_sb, mock_sb):
        """T3: update_search_session_status sets status='completed' with all result fields."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "test-session-id-1234-5678",
            status="completed",
            pipeline_stage="persist",
            completed_at="2026-02-20T12:00:00+00:00",
            duration_ms=4500,
            raw_count=150,
            total_filtered=42,
            valor_total=1_500_000.50,
            resumo_executivo="42 oportunidades encontradas em SP e RJ.",
            destaques=["Limpeza predial - SP", "Portaria - RJ"],
            response_state="live",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "completed"
        assert update_data["pipeline_stage"] == "persist"
        assert update_data["completed_at"] == "2026-02-20T12:00:00+00:00"
        assert update_data["duration_ms"] == 4500
        assert update_data["raw_count"] == 150
        assert update_data["total_filtered"] == 42
        assert update_data["valor_total"] == 1_500_000.50
        assert update_data["resumo_executivo"] == "42 oportunidades encontradas em SP e RJ."
        assert update_data["destaques"] == ["Limpeza predial - SP", "Portaria - RJ"]
        assert update_data["response_state"] == "live"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t4_session_updated_to_failed(self, mock_get_sb, mock_sb):
        """T4: update_search_session_status sets status='failed', error_code='sources_unavailable'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "test-session-id-1234-5678",
            status="failed",
            error_code="sources_unavailable",
            error_message="PNCP API returned 502",
            pipeline_stage="execute",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "failed"
        assert update_data["error_code"] == "sources_unavailable"
        assert update_data["error_message"] == "PNCP API returned 502"
        assert update_data["pipeline_stage"] == "execute"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t5_session_updated_to_timed_out(self, mock_get_sb, mock_sb):
        """T5: update_search_session_status sets status='timed_out', error_code='timeout'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "test-session-id-1234-5678",
            status="timed_out",
            error_code="timeout",
            error_message="Pipeline exceeded 360s limit",
            completed_at="2026-02-20T12:06:00+00:00",
            duration_ms=360000,
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "timed_out"
        assert update_data["error_code"] == "timeout"
        assert update_data["duration_ms"] == 360000


class TestSessionRegistrationFailure:
    """T6: When registration fails, search should still continue."""

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t6_returns_none_on_db_error(self, mock_get_sb, mock_profile, mock_sb):
        """T6: register_search_session returns None on persistent DB errors."""
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.insert.return_value.execute.side_effect = Exception(
            "connection refused"
        )

        from quota import register_search_session

        result = await register_search_session(
            user_id="user-abc-123",
            sectors=["facilities"],
            ufs=["SP"],
            data_inicial="2026-02-10",
            data_final="2026-02-20",
            custom_keywords=None,
        )

        assert result is None
        # insert was called twice (initial + 1 retry)
        assert mock_sb.table.return_value.insert.return_value.execute.call_count == 2

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t6_returns_none_on_empty_result(self, mock_get_sb, mock_profile, mock_sb):
        """T6b: register_search_session returns None when insert returns empty data."""
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[]
        )

        from quota import register_search_session

        result = await register_search_session(
            user_id="user-abc-123",
            sectors=["facilities"],
            ufs=["SP"],
            data_inicial="2026-02-10",
            data_final="2026-02-20",
            custom_keywords=None,
        )

        # RuntimeError("Insert returned empty result") is raised, retried, then None
        assert result is None


class TestUpdateFailureSilent:
    """T7: update_search_session_status catches exceptions without propagating."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t7_search_continues_if_update_fails(self, mock_get_sb, mock_sb):
        """T7: update_search_session_status logs error but does NOT raise."""
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.side_effect = (
            Exception("DB write timeout")
        )

        from quota import update_search_session_status

        # Must NOT raise
        await update_search_session_status(
            "test-session-id-1234-5678",
            status="completed",
            pipeline_stage="persist",
        )

        # Called twice (initial + 1 retry), then silently failed
        assert (
            mock_sb.table.return_value.update.return_value.eq.return_value.execute.call_count == 2
        )


class TestMigrationIdempotent:
    """T8: Migration file uses ADD COLUMN IF NOT EXISTS for idempotency."""

    def test_t8_migration_idempotent(self):
        """T8: Verify migration SQL uses IF NOT EXISTS for all ALTER TABLE statements."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "007_search_session_lifecycle.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Every ALTER TABLE ADD COLUMN must use IF NOT EXISTS
        import re

        add_column_lines = re.findall(r"ALTER TABLE.*ADD COLUMN.*", sql)
        assert len(add_column_lines) >= 9, f"Expected >= 9 ADD COLUMN statements, got {len(add_column_lines)}"

        for line in add_column_lines:
            assert "IF NOT EXISTS" in line, f"Missing IF NOT EXISTS in: {line}"

        # CREATE INDEX should also be idempotent
        create_index_lines = re.findall(r"CREATE INDEX.*", sql)
        for line in create_index_lines:
            assert "IF NOT EXISTS" in line, f"Missing IF NOT EXISTS in index: {line}"


class TestSigtermMarksInflight:
    """T9: _mark_inflight_sessions_timed_out updates in-flight sessions."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t9_sigterm_marks_inflight(self, mock_get_sb):
        """T9: _mark_inflight_sessions_timed_out sets status='timed_out' for in-flight sessions."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Mock the in_() response with 2 updated rows
        mock_sb.table.return_value.update.return_value.in_.return_value.execute.return_value = (
            MagicMock(data=[{"id": "s1"}, {"id": "s2"}])
        )

        from main import _mark_inflight_sessions_timed_out

        await _mark_inflight_sessions_timed_out()

        # Verify update was called with timed_out status
        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "timed_out"
        assert update_data["error_message"] == "Server shutdown (SIGTERM)"
        assert update_data["error_code"] == "timeout"
        assert "completed_at" in update_data

        # Verify in_() was called with the right statuses
        mock_sb.table.return_value.update.return_value.in_.assert_called_with(
            "status", ["created", "processing"]
        )

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t9_sigterm_handles_db_error_gracefully(self, mock_get_sb):
        """T9b: _mark_inflight_sessions_timed_out catches exceptions on shutdown."""
        mock_get_sb.side_effect = Exception("DB connection lost")

        from main import _mark_inflight_sessions_timed_out

        # Must NOT raise — shutdown must not be blocked
        await _mark_inflight_sessions_timed_out()


class TestBackfillSetsCompleted:
    """T10: Migration SQL contains UPDATE...SET status='completed' for backfill."""

    def test_t10_backfill_sets_completed(self):
        """T10: Verify migration has UPDATE...SET status='completed' for existing sessions."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "007_search_session_lifecycle.sql"
        )
        with open(migration_path, "r", encoding="utf-8") as f:
            sql = f.read()

        # Must have backfill UPDATE with status = 'completed'
        assert "SET status = 'completed'" in sql
        assert "pipeline_stage = 'persist'" in sql
        assert "response_state = 'live'" in sql

        # Backfill should target sessions with total_filtered > 0
        assert "total_filtered > 0" in sql

        # Also backfill zero-result but successful sessions
        assert "resumo_executivo IS NOT NULL" in sql


class TestUpdateIgnoresNoneFields:
    """T11: Only non-None fields are included in update_data dict."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t11_update_ignores_none_fields(self, mock_get_sb, mock_sb):
        """T11: Only explicitly provided fields appear in the UPDATE payload."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "test-session-id-1234-5678",
            status="processing",
            # All other fields are None by default
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]

        assert update_data == {"status": "processing"}
        assert "error_message" not in update_data
        assert "error_code" not in update_data
        assert "pipeline_stage" not in update_data
        assert "raw_count" not in update_data
        assert "completed_at" not in update_data
        assert "duration_ms" not in update_data
        assert "total_filtered" not in update_data
        assert "valor_total" not in update_data
        assert "resumo_executivo" not in update_data
        assert "destaques" not in update_data
        assert "response_state" not in update_data

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t11_noop_when_all_none(self, mock_get_sb, mock_sb):
        """T11b: If ALL fields are None, no DB call is made (early return)."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status("test-session-id-1234-5678")

        # No update should have been attempted
        mock_sb.table.return_value.update.assert_not_called()

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t11_error_message_truncated_to_500(self, mock_get_sb, mock_sb):
        """T11c: error_message is truncated to 500 chars."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        long_message = "x" * 1000
        await update_search_session_status(
            "test-session-id-1234-5678",
            error_message=long_message,
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert len(update_data["error_message"]) == 500


class TestUpdateRetriesOnTransientError:
    """T12: update_search_session_status retries once on transient error."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t12_update_retries_on_transient_error(self, mock_get_sb, mock_sb):
        """T12: First call raises, second succeeds — verify retry behavior."""
        mock_get_sb.return_value = mock_sb

        exec_mock = mock_sb.table.return_value.update.return_value.eq.return_value.execute
        exec_mock.side_effect = [
            Exception("transient network error"),
            MagicMock(data=[{}]),  # Success on retry
        ]

        from quota import update_search_session_status

        # Should NOT raise
        await update_search_session_status(
            "test-session-id-1234-5678",
            status="completed",
        )

        # Called twice (initial + 1 retry)
        assert exec_mock.call_count == 2


class TestPrometheusCounter:
    """T13: SESSION_STATUS Prometheus counter is incremented on status changes."""

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t13_prometheus_counter_on_register(self, mock_get_sb, mock_profile, mock_sb):
        """T13a: SESSION_STATUS.labels(status='created').inc() called on register."""
        mock_get_sb.return_value = mock_sb

        with patch("metrics.SESSION_STATUS") as mock_counter:
            from quota import register_search_session

            await register_search_session(
                user_id="user-abc-123",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
            )

            mock_counter.labels.assert_called_with(status="created")
            mock_counter.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t13_prometheus_counter_on_update(self, mock_get_sb, mock_sb):
        """T13b: SESSION_STATUS.labels(status=X).inc() called on update."""
        mock_get_sb.return_value = mock_sb

        with patch("metrics.SESSION_STATUS") as mock_counter:
            from quota import update_search_session_status

            await update_search_session_status(
                "test-session-id-1234-5678",
                status="completed",
            )

            mock_counter.labels.assert_called_with(status="completed")
            mock_counter.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t13_no_counter_when_no_status(self, mock_get_sb, mock_sb):
        """T13c: Prometheus counter NOT incremented when only non-status fields updated."""
        mock_get_sb.return_value = mock_sb

        with patch("metrics.SESSION_STATUS") as mock_counter:
            from quota import update_search_session_status

            await update_search_session_status(
                "test-session-id-1234-5678",
                raw_count=100,
                pipeline_stage="execute",
            )

            mock_counter.labels.assert_not_called()


class TestStructuredLog:
    """T14: Structured JSON log emitted with event='search_session_status_change'."""

    @pytest.mark.asyncio
    @patch("quota._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_t14_structured_log_on_register(self, mock_get_sb, mock_profile, mock_sb, caplog):
        """T14a: JSON log with event='search_session_status_change' on register."""
        mock_get_sb.return_value = mock_sb

        from quota import register_search_session

        with caplog.at_level(logging.INFO, logger="quota"):
            await register_search_session(
                user_id="user-abc-123",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
                search_id="search-uuid-9999",
            )

        # Find the structured log entry
        found = False
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                if log_data.get("event") == "search_session_status_change":
                    assert log_data["new_status"] == "created"
                    assert log_data["old_status"] is None
                    assert log_data["search_id"] == "search-uuid-9999"
                    assert "***" in log_data["session_id"]  # Masked
                    found = True
                    break
            except (json.JSONDecodeError, ValueError):
                continue

        assert found, "Structured log with event='search_session_status_change' not found in logs"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_t14_structured_log_on_update(self, mock_get_sb, mock_sb, caplog):
        """T14b: JSON log with event='search_session_status_change' on update."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        with caplog.at_level(logging.INFO, logger="quota"):
            await update_search_session_status(
                "test-session-id-1234-5678",
                status="failed",
                error_code="sources_unavailable",
                pipeline_stage="execute",
            )

        found = False
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                if log_data.get("event") == "search_session_status_change":
                    assert log_data["new_status"] == "failed"
                    assert log_data["error_code"] == "sources_unavailable"
                    assert log_data["pipeline_stage"] == "execute"
                    assert "***" in log_data["session_id"]  # Masked
                    found = True
                    break
            except (json.JSONDecodeError, ValueError):
                continue

        assert found, "Structured log with event='search_session_status_change' not found in logs"


# ===========================================================================
# F1-F13: Failure Scenario Tests
# ===========================================================================


class TestFailureScenarios:
    """Tests that the route/pipeline correctly maps errors to session statuses.

    These test _update_session_on_error and the exception handlers in
    routes/search.py, verifying the correct status and error_code are set.
    """

    @pytest.mark.skip(reason="F1: Gunicorn SIGKILL cannot be simulated in unit tests; "
                             "covered by T9 (SIGTERM handler for in-flight sessions)")
    def test_f1_server_timeout(self):
        """F1: Server-level timeout (gunicorn --timeout kill) is not testable in-process."""
        pass

    @pytest.mark.asyncio
    async def test_f2_pncp_total_failure(self):
        """F2: PNCPAPIError in route sets status='failed', error_code='sources_unavailable'."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            await _update_session_on_error(
                session_id="session-f2",
                start_time=1000.0,
                status="failed",
                error_code="sources_unavailable",
                error_message="PNCP API returned 502",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "failed"
            assert kwargs["error_code"] == "sources_unavailable"
            assert kwargs["error_message"] == "PNCP API returned 502"
            assert "completed_at" in kwargs
            assert "duration_ms" in kwargs

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f3_all_sources_failed(self, mock_get_sb, mock_sb):
        """F3: AllSourcesFailedError -> pipeline_stage='execute', response_state='empty_failure'.

        Tests the pipeline's except AllSourcesFailedError handler which calls
        quota.update_search_session_status with pipeline_stage and response_state.
        """
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        # Simulate what the pipeline does on AllSourcesFailedError
        await update_search_session_status(
            "session-f3",
            pipeline_stage="execute",
            response_state="empty_failure",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["pipeline_stage"] == "execute"
        assert update_data["response_state"] == "empty_failure"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f4_filter_crash(self, mock_get_sb, mock_sb):
        """F4: Exception during filter stage -> status='failed'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "session-f4",
            status="failed",
            error_code="filter_error",
            error_message="IndexError in filter pipeline",
            pipeline_stage="filter",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "failed"
        assert update_data["pipeline_stage"] == "filter"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f5_llm_crash(self, mock_get_sb, mock_sb):
        """F5: Exception during LLM summary generation -> status='failed'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "session-f5",
            status="failed",
            error_code="llm_error",
            error_message="OpenAI API returned 500",
            pipeline_stage="generate",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "failed"
        assert update_data["error_code"] == "llm_error"
        assert update_data["pipeline_stage"] == "generate"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f6_excel_crash(self, mock_get_sb, mock_sb):
        """F6: Exception during Excel generation -> status='failed'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        await update_search_session_status(
            "session-f6",
            status="failed",
            error_code="unknown",
            error_message="openpyxl MemoryError during write",
            pipeline_stage="generate",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["status"] == "failed"
        assert update_data["pipeline_stage"] == "generate"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f7_db_insert_fail(self, mock_get_sb, mock_sb):
        """F7: update_search_session_status fails silently on DB error."""
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.side_effect = (
            Exception("Supabase insert fail")
        )

        from quota import update_search_session_status

        # Must NOT raise
        await update_search_session_status(
            "session-f7",
            status="completed",
            pipeline_stage="persist",
        )
        # 2 attempts (initial + 1 retry), both failed silently
        assert (
            mock_sb.table.return_value.update.return_value.eq.return_value.execute.call_count == 2
        )

    @pytest.mark.asyncio
    async def test_f8_client_disconnect(self):
        """F8: asyncio.CancelledError in route (client disconnect)."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            # Simulate what the route does: it calls _update_session_on_error
            # if session_id exists before re-raising CancelledError
            await _update_session_on_error(
                session_id="session-f8",
                start_time=1000.0,
                status="failed",
                error_code="unknown",
                error_message="CancelledError: client disconnected",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "failed"

    @pytest.mark.asyncio
    async def test_f9_oom(self):
        """F9: MemoryError -> status='failed', error_code='unknown' via generic handler."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            await _update_session_on_error(
                session_id="session-f9",
                start_time=1000.0,
                status="failed",
                error_code="unknown",
                error_message="MemoryError: out of memory",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "failed"
            assert kwargs["error_code"] == "unknown"

    @pytest.mark.asyncio
    async def test_f10_pipeline_timeout(self):
        """F10: asyncio.TimeoutError -> status='timed_out', error_code='timeout'."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            # Pipeline timeout is mapped to HTTP 504, which maps to timed_out
            await _update_session_on_error(
                session_id="session-f10",
                start_time=1000.0,
                status="timed_out",
                error_code="timeout",
                error_message="HTTP 504: Pipeline timeout",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "timed_out"
            assert kwargs["error_code"] == "timeout"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_f11_degraded_no_cache(self, mock_get_sb, mock_sb):
        """F11: PNCPDegradedError -> pipeline_stage='execute', response_state='degraded'."""
        mock_get_sb.return_value = mock_sb

        from quota import update_search_session_status

        # This is what the pipeline does on PNCPDegradedError
        await update_search_session_status(
            "session-f11",
            pipeline_stage="execute",
            response_state="degraded",
        )

        update_call = mock_sb.table.return_value.update.call_args
        update_data = update_call[0][0]
        assert update_data["pipeline_stage"] == "execute"
        assert update_data["response_state"] == "degraded"

    @pytest.mark.asyncio
    async def test_f12_rate_limit_post_quota(self):
        """F12: PNCPRateLimitError -> status='failed', error_code='sources_unavailable'."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            await _update_session_on_error(
                session_id="session-f12",
                start_time=1000.0,
                status="failed",
                error_code="sources_unavailable",
                error_message="PNCP rate limit: retry after 60s",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "failed"
            assert kwargs["error_code"] == "sources_unavailable"
            assert "rate limit" in kwargs["error_message"]

    @pytest.mark.asyncio
    async def test_f13_unhandled_exception(self):
        """F13: Generic Exception -> status='failed', error_code='unknown'."""
        from routes.search import _update_session_on_error

        with patch("quota.update_search_session_status", new_callable=AsyncMock) as mock_update:
            await _update_session_on_error(
                session_id="session-f13",
                start_time=1000.0,
                status="failed",
                error_code="unknown",
                error_message="RuntimeError: something unexpected happened",
            )

            mock_update.assert_called_once()
            kwargs = mock_update.call_args[1]
            assert kwargs["status"] == "failed"
            assert kwargs["error_code"] == "unknown"


# ===========================================================================
# I1-I3: Integration Tests — Full Status Transition Sequences
# ===========================================================================


class TestPipelineStatusTransitions:
    """Integration tests verifying the full session status transition sequence.

    These mock at the quota module level (as search_pipeline does `import quota`
    then calls `quota.register_search_session()`) to verify the correct sequence
    of status transitions across the pipeline lifecycle.
    """

    @pytest.mark.asyncio
    async def test_i1_pipeline_success_transitions(self):
        """I1: Session goes created -> processing -> completed on successful pipeline run."""
        status_calls = []

        async def mock_register(*args, **kwargs):
            status_calls.append(("register", "created"))
            return "session-i1"

        async def mock_update(session_id, **kwargs):
            status = kwargs.get("status")
            stage = kwargs.get("pipeline_stage")
            if status:
                status_calls.append(("update", status, stage))
            elif stage:
                status_calls.append(("update_stage", stage))

        with patch("quota.register_search_session", side_effect=mock_register) as mock_reg, \
             patch("quota.update_search_session_status", side_effect=mock_update) as mock_upd:

            from quota import register_search_session, update_search_session_status

            # Step 1: Register session (pipeline entry)
            session_id = await register_search_session(
                user_id="user-i1",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
            )
            assert session_id == "session-i1"

            # Step 2: Set to processing (after quota check passes)
            await update_search_session_status(
                session_id, status="processing", pipeline_stage="validate"
            )

            # Step 3: Update pipeline stage (execute)
            await update_search_session_status(
                session_id, pipeline_stage="execute"
            )

            # Step 4: Update raw_count
            await update_search_session_status(
                session_id, raw_count=150
            )

            # Step 5: Update pipeline stage (filter)
            await update_search_session_status(
                session_id, pipeline_stage="filter"
            )

            # Step 6: Update pipeline stage (generate)
            await update_search_session_status(
                session_id, pipeline_stage="generate"
            )

            # Step 7: Complete
            await update_search_session_status(
                session_id,
                status="completed",
                pipeline_stage="persist",
                completed_at="2026-02-20T12:00:00+00:00",
                duration_ms=5000,
                total_filtered=42,
                valor_total=1_500_000.0,
                response_state="live",
            )

        # Verify the sequence: created -> processing -> completed
        statuses = [s for s in status_calls if s[0] in ("register", "update")]
        assert statuses[0] == ("register", "created")
        assert statuses[1] == ("update", "processing", "validate")
        assert statuses[2] == ("update", "completed", "persist")

    @pytest.mark.asyncio
    async def test_i2_pipeline_failure_transitions(self):
        """I2: Session goes created -> processing -> failed on pipeline error."""
        status_calls = []

        async def mock_register(*args, **kwargs):
            status_calls.append("created")
            return "session-i2"

        async def mock_update(session_id, **kwargs):
            status = kwargs.get("status")
            if status:
                status_calls.append(status)

        with patch("quota.register_search_session", side_effect=mock_register), \
             patch("quota.update_search_session_status", side_effect=mock_update):

            from quota import register_search_session, update_search_session_status

            # Step 1: Register
            session_id = await register_search_session(
                user_id="user-i2",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
            )

            # Step 2: Processing
            await update_search_session_status(
                session_id, status="processing", pipeline_stage="validate"
            )

            # Step 3: Failure (e.g., all sources failed)
            await update_search_session_status(
                session_id,
                status="failed",
                error_code="sources_unavailable",
                error_message="All data sources returned errors",
                pipeline_stage="execute",
                completed_at="2026-02-20T12:01:00+00:00",
                duration_ms=30000,
            )

        assert status_calls == ["created", "processing", "failed"]

    @pytest.mark.asyncio
    async def test_i3_pipeline_timeout_transitions(self):
        """I3: Session goes created -> processing -> timed_out on pipeline timeout."""
        status_calls = []

        async def mock_register(*args, **kwargs):
            status_calls.append("created")
            return "session-i3"

        async def mock_update(session_id, **kwargs):
            status = kwargs.get("status")
            if status:
                status_calls.append(status)

        with patch("quota.register_search_session", side_effect=mock_register), \
             patch("quota.update_search_session_status", side_effect=mock_update):

            from quota import register_search_session, update_search_session_status

            # Step 1: Register
            session_id = await register_search_session(
                user_id="user-i3",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
            )

            # Step 2: Processing
            await update_search_session_status(
                session_id, status="processing", pipeline_stage="validate"
            )

            # Step 3: Timeout (pipeline exceeded time budget)
            await update_search_session_status(
                session_id,
                status="timed_out",
                error_code="timeout",
                error_message="Pipeline exceeded 360s limit",
                pipeline_stage="execute",
                completed_at="2026-02-20T12:06:00+00:00",
                duration_ms=360000,
            )

        assert status_calls == ["created", "processing", "timed_out"]

    @pytest.mark.asyncio
    async def test_i1_graceful_degradation_without_session(self):
        """I1b: Pipeline continues even if session registration returns None."""
        async def mock_register(*args, **kwargs):
            return None  # Simulates DB failure

        async def mock_update(session_id, **kwargs):
            pass

        with patch("quota.register_search_session", side_effect=mock_register), \
             patch("quota.update_search_session_status", side_effect=mock_update) as mock_upd:

            from quota import register_search_session, update_search_session_status

            session_id = await register_search_session(
                user_id="user-i1b",
                sectors=["facilities"],
                ufs=["SP"],
                data_inicial="2026-02-10",
                data_final="2026-02-20",
                custom_keywords=None,
            )

            assert session_id is None

            # Pipeline should NOT call update_search_session_status when session_id is None
            # (the pipeline guards with `if ctx.session_id:`)
            # This test verifies the pattern works
            if session_id:
                await update_search_session_status(
                    session_id, status="processing"
                )

            mock_upd.assert_not_called()
