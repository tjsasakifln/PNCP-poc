"""CRIT-011: Tests for search_sessions search_id migration and related features.

T1: Migration SQL is valid (parse without error)
T2: search_id saved correctly when creating search session
T3: Startup recovery marks stale sessions as failed/timed_out (with search_id)
T4: Startup recovery works without search_id column (backward compatible)
T5: Cleanup marks in_progress > 1h as timed_out
T6: Cleanup deletes failed/timed_out > 7 days
T7: Migration is idempotent (can execute 2x without error)
"""

import os
import sys
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# T1: Migration SQL is valid
# ---------------------------------------------------------------------------

class TestMigrationValidity:
    """T1: Verify migration SQL files exist and have valid structure."""

    def test_backend_migration_exists_and_valid(self):
        """T1: Backend migration file exists and contains expected SQL."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations",
            "009_add_search_id_to_search_sessions.sql"
        )
        assert os.path.exists(migration_path), "Migration file must exist"

        with open(migration_path, "r") as f:
            sql = f.read()

        # Verify key SQL statements
        assert "ALTER TABLE search_sessions" in sql
        assert "ADD COLUMN IF NOT EXISTS search_id" in sql
        assert "UUID" in sql
        assert "DEFAULT NULL" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_search_sessions_search_id" in sql
        assert "CREATE INDEX IF NOT EXISTS idx_search_sessions_status_created" in sql
        assert "COMMENT ON COLUMN" in sql

    def test_supabase_migration_exists_and_valid(self):
        """T1: Supabase migration file exists with identical content."""
        supabase_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "supabase", "migrations"
        )
        # Find the CRIT-011 migration file
        found = [
            f for f in os.listdir(supabase_dir)
            if "add_search_id_to_search_sessions" in f
        ]
        assert len(found) == 1, f"Expected 1 supabase migration, found {len(found)}: {found}"

        with open(os.path.join(supabase_dir, found[0]), "r") as f:
            sql = f.read()

        assert "ALTER TABLE search_sessions" in sql
        assert "ADD COLUMN IF NOT EXISTS search_id" in sql

    def test_migration_idempotent_sql(self):
        """T7: Migration uses IF NOT EXISTS everywhere for idempotency."""
        migration_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations",
            "009_add_search_id_to_search_sessions.sql"
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        # Every ALTER/CREATE should use IF NOT EXISTS
        assert sql.count("IF NOT EXISTS") >= 3, (
            "Migration must use IF NOT EXISTS for column + 2 indexes"
        )


# ---------------------------------------------------------------------------
# T2: search_id saved correctly when creating search session
# ---------------------------------------------------------------------------

class TestSearchIdPersistence:
    """T2: Verify search_id is included in session registration."""

    @pytest.mark.asyncio
    async def test_search_id_saved_in_session(self):
        """T2: register_search_session includes search_id in insert data."""
        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()
        mock_execute = MagicMock()

        mock_sb.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = MagicMock(
            data=[{"id": "session-123"}]
        )

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("quota._ensure_profile_exists", return_value=True):
            from quota import register_search_session
            session_id = await register_search_session(
                user_id="user-1",
                sectors=["vestuario"],
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                custom_keywords=None,
                search_id="test-search-uuid-123",
            )

        assert session_id == "session-123"

        # Verify insert was called with search_id in data
        insert_call = mock_table.insert.call_args
        insert_data = insert_call[0][0]
        assert insert_data["search_id"] == "test-search-uuid-123"

    @pytest.mark.asyncio
    async def test_search_id_omitted_when_none(self):
        """T2: register_search_session omits search_id when not provided."""
        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_insert = MagicMock()

        mock_sb.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = MagicMock(
            data=[{"id": "session-456"}]
        )

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("quota._ensure_profile_exists", return_value=True):
            from quota import register_search_session
            session_id = await register_search_session(
                user_id="user-1",
                sectors=["vestuario"],
                ufs=["SP"],
                data_inicial="2026-01-01",
                data_final="2026-01-10",
                custom_keywords=None,
                search_id=None,
            )

        assert session_id == "session-456"

        insert_data = mock_table.insert.call_args[0][0]
        assert "search_id" not in insert_data


# ---------------------------------------------------------------------------
# T3: Startup recovery marks stale sessions (with search_id)
# ---------------------------------------------------------------------------

class TestStartupRecovery:
    """T3: Verify startup recovery handles stale sessions correctly."""

    @pytest.mark.asyncio
    async def test_recovery_marks_old_sessions_timed_out(self):
        """T3: Sessions older than max_age_minutes are marked timed_out."""
        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(minutes=20)).isoformat()

        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_in = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()

        mock_sb.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.in_.return_value = mock_in
        mock_in.execute.return_value = MagicMock(data=[
            {"id": "s1", "search_id": "sid-1", "status": "processing", "started_at": old_time},
        ])
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            from search_state_manager import recover_stale_searches
            total = await recover_stale_searches(max_age_minutes=10)

        assert total == 1
        # Verify update was called with timed_out status
        update_call = mock_table.update.call_args
        assert update_call[0][0]["status"] == "timed_out"
        assert update_call[0][0]["error_code"] == "timeout"

    @pytest.mark.asyncio
    async def test_recovery_marks_recent_sessions_failed(self):
        """T3: Sessions younger than max_age_minutes are marked failed."""
        now = datetime.now(timezone.utc)
        recent_time = (now - timedelta(minutes=3)).isoformat()

        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_in = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()

        mock_sb.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.in_.return_value = mock_in
        mock_in.execute.return_value = MagicMock(data=[
            {"id": "s2", "search_id": "sid-2", "status": "created", "started_at": recent_time},
        ])
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            from search_state_manager import recover_stale_searches
            total = await recover_stale_searches(max_age_minutes=10)

        assert total == 1
        update_call = mock_table.update.call_args
        assert update_call[0][0]["status"] == "failed"
        assert update_call[0][0]["error_code"] == "server_restart"


# ---------------------------------------------------------------------------
# T4: Startup recovery backward compatible (no search_id column)
# ---------------------------------------------------------------------------

class TestStartupRecoveryBackwardCompat:
    """T4: Recovery works when search_id column doesn't exist yet."""

    @pytest.mark.asyncio
    async def test_recovery_without_search_id_column(self):
        """T4: Recovery falls back to query without search_id on 42703 error."""
        now = datetime.now(timezone.utc)
        old_time = (now - timedelta(minutes=20)).isoformat()

        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_select_with_sid = MagicMock()
        mock_select_without_sid = MagicMock()
        mock_in_fail = MagicMock()
        mock_in_ok = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()

        mock_sb.table.return_value = mock_table

        # First call (with search_id) fails with 42703
        call_count = [0]
        def select_side_effect(columns):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call includes search_id → will fail
                result = MagicMock()
                result.in_ = MagicMock(side_effect=Exception(
                    "{'code': '42703', 'message': 'column search_sessions.search_id does not exist'}"
                ))
                return result
            else:
                # Second call without search_id → succeeds
                result = MagicMock()
                mock_in_ok = MagicMock()
                mock_in_ok.execute.return_value = MagicMock(data=[
                    {"id": "s3", "status": "processing", "started_at": old_time},
                ])
                result.in_.return_value = mock_in_ok
                return result

        mock_table.select.side_effect = select_side_effect
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb), \
             patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            from search_state_manager import recover_stale_searches
            total = await recover_stale_searches(max_age_minutes=10)

        # Should still recover the session (without crashing)
        assert total == 1
        # Verify it was called twice (first with search_id, then without)
        assert mock_table.select.call_count == 2

    @pytest.mark.asyncio
    async def test_recovery_no_crash_on_missing_column(self):
        """T4: Recovery doesn't crash or block startup on missing column."""
        mock_sb = MagicMock()
        mock_table = MagicMock()

        mock_sb.table.return_value = mock_table

        # Both calls fail (simulating total DB issue)
        mock_select = MagicMock()
        mock_select.in_.side_effect = Exception(
            "{'code': '42703', 'message': 'column search_sessions.search_id does not exist'}"
        )
        mock_table.select.return_value = mock_select

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            from search_state_manager import recover_stale_searches
            # Should NOT raise — returns 0
            total = await recover_stale_searches(max_age_minutes=10)

        assert total == 0


# ---------------------------------------------------------------------------
# T5: Cleanup marks in_progress > 1h as timed_out
# ---------------------------------------------------------------------------

class TestSessionCleanupStale:
    """T5: Verify cleanup_stale_sessions marks stale sessions."""

    @pytest.mark.asyncio
    async def test_cleanup_marks_stale_sessions(self):
        """T5: in_progress sessions older than 1h are marked timed_out."""
        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_lt = MagicMock()
        mock_delete = MagicMock()
        mock_delete_eq = MagicMock()
        mock_delete_lt = MagicMock()

        mock_sb.table.return_value = mock_table

        # Setup update chain: .update().eq().lt().execute()
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.lt.return_value = mock_lt
        mock_lt.execute.return_value = MagicMock(data=[
            {"id": "stale-1"}, {"id": "stale-2"}
        ])

        # Setup delete chain: .delete().eq().lt().execute()
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete_eq
        mock_delete_eq.lt.return_value = mock_delete_lt
        mock_delete_lt.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            from cron_jobs import cleanup_stale_sessions
            result = await cleanup_stale_sessions()

        # 2 from in_progress + potential from created/processing
        assert result["marked_stale"] >= 2
        assert "error" not in result


# ---------------------------------------------------------------------------
# T6: Cleanup deletes failed/timed_out > 7 days
# ---------------------------------------------------------------------------

class TestSessionCleanupOld:
    """T6: Verify cleanup_stale_sessions deletes old terminal sessions."""

    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_sessions(self):
        """T6: failed/timed_out sessions older than 7 days are deleted."""
        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_lt = MagicMock()
        mock_delete = MagicMock()
        mock_delete_eq = MagicMock()
        mock_delete_lt = MagicMock()

        mock_sb.table.return_value = mock_table

        # Update chain returns 0 stale
        mock_table.update.return_value = mock_update
        mock_update.eq.return_value = mock_eq
        mock_eq.lt.return_value = mock_lt
        mock_lt.execute.return_value = MagicMock(data=[])

        # Delete chain returns deleted records
        mock_table.delete.return_value = mock_delete
        mock_delete.eq.return_value = mock_delete_eq
        mock_delete_eq.lt.return_value = mock_delete_lt

        # 3 statuses: failed, timeout, timed_out → return some for each
        mock_delete_lt.execute.side_effect = [
            MagicMock(data=[{"id": "old-1"}, {"id": "old-2"}]),  # failed
            MagicMock(data=[{"id": "old-3"}]),                     # timeout
            MagicMock(data=[]),                                     # timed_out
        ]

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            from cron_jobs import cleanup_stale_sessions
            result = await cleanup_stale_sessions()

        assert result["deleted_old"] == 3
        assert result["marked_stale"] == 0
