"""CRIT-029: Histórico dedup — prevent duplicate session entries on cache hits.

AC1: Same params within 5min → single history entry (not duplicate)
AC2: Cache hits (duration < 2s) merged with original session (update, not insert)
AC3: Dedup checks (user_id + sectors + ufs + data_range) not just search_id
AC4: Integration test: busca + retry → 1 history entry
AC5: Unit test: cache hit same params → update instead of insert
AC6: Zero regression

Root cause: supabase-py .eq() serializes Python lists as "['a','b']" instead of
PostgreSQL array literal format "{a,b}", causing the param dedup query to silently
return empty → every search creates a new session → duplicates.
Fix: Use .filter("col", "eq", "{val1,val2}") with explicit PG array literals.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FluidMock:
    """Mock that returns itself for any chained PostgREST call, with custom execute().

    This decouples tests from the exact chain order (.eq/.filter/.gte etc.),
    so tests survive refactors that change query builder method order.
    """

    def __init__(self, execute_data=None, execute_side_effect=None):
        self._execute_data = execute_data if execute_data is not None else []
        self._execute_side_effect = execute_side_effect

    def __getattr__(self, name):
        if name == "execute":
            if self._execute_side_effect:
                def _exec():
                    raise self._execute_side_effect
                return _exec
            return lambda: MagicMock(data=self._execute_data)
        # Any other method call (.select, .eq, .filter, .gte, .order, .limit)
        # returns self for fluid chaining
        return lambda *a, **kw: self

    def __call__(self, *args, **kwargs):
        return self


def make_insert_mock(session_id):
    """Create a mock table that responds to .insert().execute() with given ID."""
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": session_id}]
    )
    return mock_table


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_args():
    return {
        "user_id": "user-crit029-test",
        "sectors": ["informatica"],
        "ufs": ["SP", "RJ"],
        "data_inicial": "2026-02-01",
        "data_final": "2026-02-10",
        "custom_keywords": None,
        "search_id": "search-crit029-001",
    }


# ===========================================================================
# AC1: Same params within 5min → single history entry
# ===========================================================================

class TestParameterBasedDedup:
    """CRIT-029 AC1+AC3: Parameter-based dedup prevents duplicates."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_no_dedup_match_creates_new_session(self, mock_get_sb, mock_profile, base_args):
        """When no recent session with same params exists, create new one."""
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # search_id dedup → no match
                return FluidMock(execute_data=[])
            elif call_count == 2:
                # param dedup → no match
                return FluidMock(execute_data=[])
            else:
                # INSERT
                return make_insert_mock("new-session-id")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-session-id"
        assert call_count == 3  # search_id check + param check + insert

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_param_dedup_returns_existing_session(self, mock_get_sb, mock_profile, base_args):
        """When session with same params exists within 5min, reuse it."""
        call_count = 0
        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # search_id dedup → no match
                return FluidMock(execute_data=[])
            elif call_count == 2:
                # param dedup → MATCH
                return FluidMock(execute_data=[{"id": "existing-param-session", "created_at": recent_time}])
            else:
                return make_insert_mock("should-not-reach")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "existing-param-session"
        assert call_count == 2  # Only search_id check + param check, no insert

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_param_dedup_failure_falls_through_to_insert(self, mock_get_sb, mock_profile, base_args):
        """If param dedup check fails (DB error), fall through to insert."""
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # search_id check → no match
                return FluidMock(execute_data=[])
            elif call_count == 2:
                # param dedup → DB error
                return FluidMock(execute_side_effect=Exception("DB timeout"))
            else:
                # Insert succeeds
                return make_insert_mock("fallback-insert-id")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "fallback-insert-id"


# ===========================================================================
# AC2: Cache hits merged with original session
# ===========================================================================

class TestCacheHitMerge:
    """CRIT-029 AC2: Cache hits (fast responses) update existing session."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_second_search_same_params_reuses_session(self, mock_get_sb, mock_profile, base_args):
        """Simulates: search A (183s) creates session, search B (0.5s cache) reuses it."""
        call_count = 0
        original_session_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # search_id check → no match (different search_id)
                return FluidMock(execute_data=[])
            elif call_count == 2:
                # param dedup → finds original session from 1 minute ago
                return FluidMock(execute_data=[{
                    "id": "original-session-from-search-A",
                    "created_at": original_session_time,
                }])
            else:
                return make_insert_mock("should-not-reach")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        # Second search has a different search_id (frontend generates new one each time)
        base_args["search_id"] = "search-crit029-002-different"

        from quota import register_search_session
        result = await register_search_session(**base_args)

        # Should reuse the existing session, not create new
        assert result == "original-session-from-search-A"
        assert call_count == 2  # No insert

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_different_params_creates_new_session(self, mock_get_sb, mock_profile, base_args):
        """Different sector → should NOT match dedup → new session."""
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FluidMock(execute_data=[])
            elif call_count == 2:
                return FluidMock(execute_data=[])
            else:
                return make_insert_mock("new-sector-session")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        base_args["sectors"] = ["vestuario"]

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-sector-session"


# ===========================================================================
# AC3: Dedup uses composite key (user + sectors + ufs + date_range)
# ===========================================================================

class TestCompositeKeyDedup:
    """CRIT-029 AC3: Dedup verifies full composite key."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_different_ufs_creates_new_session(self, mock_get_sb, mock_profile, base_args):
        """Different UFs → not a duplicate → new session."""
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FluidMock(execute_data=[])
            elif call_count == 2:
                return FluidMock(execute_data=[])
            else:
                return make_insert_mock("new-ufs-session")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        base_args["ufs"] = ["MG", "BA"]

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-ufs-session"

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_different_dates_creates_new_session(self, mock_get_sb, mock_profile, base_args):
        """Different date range → not a duplicate → new session."""
        call_count = 0

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FluidMock(execute_data=[])
            elif call_count == 2:
                return FluidMock(execute_data=[])
            else:
                return make_insert_mock("new-dates-session")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        base_args["data_final"] = "2026-02-20"

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "new-dates-session"

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_ufs_sorted_for_consistent_matching(self, mock_get_sb, mock_profile, base_args):
        """UFs should be sorted before comparison to ensure RJ,SP matches SP,RJ."""
        call_count = 0
        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FluidMock(execute_data=[])
            elif call_count == 2:
                return FluidMock(execute_data=[{
                    "id": "sorted-match-session",
                    "created_at": recent_time,
                }])
            else:
                return make_insert_mock("should-not-reach")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        # UFs in reverse order (RJ, SP instead of SP, RJ)
        base_args["ufs"] = ["RJ", "SP"]

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "sorted-match-session"

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_no_search_id_still_does_param_dedup(self, mock_get_sb, mock_profile, base_args):
        """Even without search_id, param-based dedup still works."""
        call_count = 0
        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call is param dedup (search_id check skipped)
                return FluidMock(execute_data=[{
                    "id": "param-match-no-sid",
                    "created_at": recent_time,
                }])
            else:
                return make_insert_mock("should-not-reach")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        base_args["search_id"] = None

        from quota import register_search_session
        result = await register_search_session(**base_args)

        assert result == "param-match-no-sid"


# ===========================================================================
# AC4: Integration-level test: search + cache-hit retry → 1 entry
# ===========================================================================

class TestSearchRetryDedup:
    """CRIT-029 AC4: Search + immediate retry produces only 1 history entry."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_search_then_retry_produces_single_session(self, mock_get_sb, mock_profile, base_args):
        """First call creates session, second call (retry) reuses it."""
        first_session_id = "session-first-call"
        call_count = 0
        creation_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # First register_search_session call:
                # 1. search_id check → no match
                # 2. param dedup → no match
                return FluidMock(execute_data=[])
            elif call_count == 3:
                # Insert for first call
                return make_insert_mock(first_session_id)
            elif call_count == 4:
                # Second register_search_session: search_id check → no match
                return FluidMock(execute_data=[])
            elif call_count == 5:
                # Second call: param dedup → match (first session)
                return FluidMock(execute_data=[{
                    "id": first_session_id,
                    "created_at": creation_time,
                }])
            else:
                return make_insert_mock("should-not-reach")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        from quota import register_search_session

        # First search
        result1 = await register_search_session(**base_args)
        assert result1 == first_session_id

        # Retry (different search_id, same params)
        base_args["search_id"] = "search-crit029-retry"
        result2 = await register_search_session(**base_args)
        assert result2 == first_session_id

        # Both calls return the same session ID → only 1 history entry
        assert result1 == result2


# ===========================================================================
# AC5: Unit test — verify .filter() uses PostgreSQL array literal format
# ===========================================================================

class TestPostgresArrayLiteral:
    """CRIT-029 AC5: Verify the dedup query uses correct PG array format."""

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_filter_called_with_pg_array_format(self, mock_get_sb, mock_profile, base_args):
        """Dedup query must use .filter() with PostgreSQL array literal, not .eq() with Python list."""
        call_count = 0
        filter_calls = []

        class TrackingFluidMock:
            """Tracks .filter() calls to verify PG array format."""
            def __init__(self):
                self._filter_args = []

            def __getattr__(self, name):
                if name == "execute":
                    return lambda: MagicMock(data=[])
                if name == "filter":
                    def _filter(*args, **kwargs):
                        filter_calls.append(args)
                        return self
                    return _filter
                return lambda *a, **kw: self

            def __call__(self, *args, **kwargs):
                return self

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return FluidMock(execute_data=[])
            elif call_count == 2:
                # param dedup — use tracking mock
                return TrackingFluidMock()
            else:
                return make_insert_mock("new-id")

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        from quota import register_search_session
        await register_search_session(**base_args)

        # Verify .filter() was called with PG array literal format
        assert len(filter_calls) == 2, f"Expected 2 .filter() calls, got {len(filter_calls)}"

        # First filter: sectors — sorted ["informatica"] → "{informatica}"
        assert filter_calls[0] == ("sectors", "eq", "{informatica}")

        # Second filter: ufs — sorted ["SP", "RJ"] → ["RJ", "SP"] → "{RJ,SP}"
        assert filter_calls[1] == ("ufs", "eq", "{RJ,SP}")

    @pytest.mark.asyncio
    @patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
    @patch("supabase_client.get_supabase")
    async def test_insert_stores_sorted_arrays(self, mock_get_sb, mock_profile, base_args):
        """INSERT must store sorted sectors and ufs for consistent dedup matching."""
        call_count = 0
        insert_data = []

        def table_side_effect(table_name):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return FluidMock(execute_data=[])
            else:
                mock_table = MagicMock()
                def capture_insert(data):
                    insert_data.append(data)
                    result_mock = MagicMock()
                    result_mock.execute.return_value = MagicMock(data=[{"id": "new-id"}])
                    return result_mock
                mock_table.insert.side_effect = capture_insert
                return mock_table

        sb = MagicMock()
        sb.table.side_effect = table_side_effect
        mock_get_sb.return_value = sb

        # UFs in non-sorted order
        base_args["ufs"] = ["SP", "RJ"]

        from quota import register_search_session
        await register_search_session(**base_args)

        assert len(insert_data) == 1
        assert insert_data[0]["ufs"] == ["RJ", "SP"], "UFs must be sorted on insert"
        assert insert_data[0]["sectors"] == ["informatica"], "Sectors must be sorted on insert"
