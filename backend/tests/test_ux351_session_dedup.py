"""UX-351: Session dedup + Portuguese error messages tests.

AC1: Prevent duplicate session entries for the same search_id.
AC6-AC7: Error messages stored in Portuguese (search_state_manager).
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_sb():
    """Create a mock Supabase client with chained method returns."""
    sb = MagicMock()

    # Default: insert returns a session ID
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "new-session-id"}]
    )

    # Default: select returns empty (no existing session)
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[]
    )

    # Default: update returns success
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{}]
    )

    return sb


@pytest.fixture
def base_args():
    return {
        "user_id": "user-test-123",
        "sectors": ["informatica"],
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-01",
        "data_final": "2026-02-10",
        "custom_keywords": None,
        "search_id": "search-abc-999",
    }


# ===========================================================================
# AC1: Dedup — reuse existing session for same search_id
# ===========================================================================

class TestSessionDedup:
    """UX-351 AC1: Prevent duplicate session entries."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_creates_new_session_when_no_existing(self, mock_get_sb, mock_profile, mock_sb, base_args):
        """When no session exists for search_id, insert a new one."""
        mock_get_sb.return_value = mock_sb

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-session-id"
        # Verify insert was called
        mock_sb.table.return_value.insert.assert_called_once()
        insert_data = mock_sb.table.return_value.insert.call_args[0][0]
        assert insert_data["search_id"] == "search-abc-999"
        assert insert_data["status"] == "created"

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_reuses_existing_session_for_same_search_id(self, mock_get_sb, mock_profile, mock_sb, base_args):
        """When session already exists for search_id, return existing ID without inserting."""
        mock_get_sb.return_value = mock_sb

        # Mock: select returns an existing session
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "existing-session-id"}]
        )

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "existing-session-id"
        # Verify insert was NOT called
        mock_sb.table.return_value.insert.assert_not_called()

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_no_dedup_check_without_search_id(self, mock_get_sb, mock_profile, mock_sb, base_args):
        """When search_id is None, skip dedup and always insert."""
        mock_get_sb.return_value = mock_sb
        base_args["search_id"] = None

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-session-id"
        # Should have called insert (no dedup check for None search_id)
        mock_sb.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_dedup_check_failure_falls_through_to_insert(self, mock_get_sb, mock_profile, mock_sb, base_args):
        """If dedup check raises an exception, fall through to normal insert."""
        mock_get_sb.return_value = mock_sb

        # Mock: select raises an exception
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("DB error")

        # But insert should still work (reset side_effect for table calls)
        # Need to handle the chaining correctly - insert is a separate chain
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            mock_table = MagicMock()
            if call_count == 1:
                # First call: select (dedup check) - will fail
                mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("DB error")
            else:
                # Second call: insert
                mock_table.insert.return_value.execute.return_value = MagicMock(
                    data=[{"id": "fallback-session-id"}]
                )
            return mock_table

        mock_sb.table.side_effect = table_side_effect

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "fallback-session-id"


# ===========================================================================
# AC6-AC7: Portuguese error messages in search_state_manager
# ===========================================================================

class TestPortugueseErrorMessages:
    """UX-351 AC6-AC7: Error messages stored in Portuguese."""

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_stale_search_recovery_uses_portuguese_timed_out(self, mock_get_sb):
        """Old stale searches get Portuguese error message for timed_out."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Mock: select returns a stale session (old timestamp)
        from datetime import datetime, timezone, timedelta
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()

        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "stale-1",
                "status": "processing",
                "created_at": old_time,
                "search_id": "search-stale-1",
            }]
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])

        # Import and run recovery
        from search_state_manager import recover_stale_searches
        await recover_stale_searches()

        # Verify update was called with Portuguese message
        update_calls = mock_sb.table.return_value.update.call_args_list
        if update_calls:
            update_data = update_calls[0][0][0]
            assert update_data["error_message"] == "O servidor reiniciou durante o processamento."
            assert update_data["status"] == "timed_out"

    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    async def test_recent_search_recovery_uses_portuguese_failed(self, mock_get_sb):
        """Recent stale searches get Portuguese error message for failed."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Mock: select returns a recent stale session (< 10 min old)
        from datetime import datetime, timezone, timedelta
        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()

        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "stale-2",
                "status": "processing",
                "created_at": recent_time,
                "search_id": "search-stale-2",
            }]
        )
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])

        from search_state_manager import recover_stale_searches
        await recover_stale_searches()

        update_calls = mock_sb.table.return_value.update.call_args_list
        if update_calls:
            update_data = update_calls[0][0][0]
            assert update_data["error_message"] == "O servidor reiniciou. Tente novamente."
            assert update_data["status"] == "failed"
