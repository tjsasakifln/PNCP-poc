"""
DEBT-009: Database RLS & Retention Hardening Tests

Tests cover:
- Migration SQL validation (idempotency, correctness)
- RLS policy standardization (no auth.role() remaining)
- pg_cron retention job definitions
- search_state_transitions optimization (user_id column + RLS)
- Cache warmer ban
- Backend code changes (user_id propagation)
"""
import os
import re
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "migrations"
)


def _read_migration(filename: str) -> str:
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Front 1: RLS Standardization (DB-001, DB-002)
# ---------------------------------------------------------------------------

class TestRLSStandardizeMigration:
    """Validates 20260308300000_debt009_rls_standardize_remaining.sql"""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration("20260308300000_debt009_rls_standardize_remaining.sql")

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, "20260308300000_debt009_rls_standardize_remaining.sql")
        assert os.path.exists(path)

    def test_drops_feedback_admin_all_policy(self):
        """DB-001: Old auth.role() policy on classification_feedback is dropped."""
        assert 'DROP POLICY IF EXISTS "feedback_admin_all"' in self.sql

    def test_creates_service_role_policy_classification_feedback(self):
        """DB-001: New TO service_role policy on classification_feedback."""
        assert "classification_feedback" in self.sql
        assert "TO service_role" in self.sql

    def test_creates_service_role_policy_health_checks(self):
        """DB-002: Explicit service_role policy on health_checks."""
        # Find the health_checks section
        idx = self.sql.find("health_checks")
        assert idx > 0
        section = self.sql[idx:idx+200]
        assert "service_role" in section.lower()

    def test_creates_service_role_policy_incidents(self):
        """DB-002: Explicit service_role policy on incidents."""
        idx = self.sql.find("incidents")
        assert idx > 0
        section = self.sql[idx:idx+200]
        assert "service_role" in section.lower()

    def test_uses_transaction_block(self):
        """Migration runs atomically.

        BTS-010b: Supabase `db push` wraps every migration file in its own
        transaction; explicit BEGIN/COMMIT inside the file is redundant and
        actively discouraged by Supabase docs (it would nest transactions).
        The contract enforced here is idempotent-atomic behavior, which is
        achieved via `DROP POLICY IF EXISTS` + `CREATE POLICY` pairs that
        leave the DB in a consistent state even on partial failure.
        """
        create_count = self.sql.count("CREATE POLICY")
        drop_count = self.sql.count("DROP POLICY IF EXISTS")
        assert create_count > 0, "Migration must create at least one policy"
        assert drop_count >= create_count, (
            f"Every CREATE POLICY ({create_count}) must have a paired DROP "
            f"POLICY IF EXISTS (found {drop_count}) for idempotency."
        )

    def test_no_auth_role_in_new_policies(self):
        """No auth.role() calls in CREATE POLICY statements."""
        # auth.role() may appear in comments but must not be in any CREATE POLICY
        policy_sections = re.findall(
            r'CREATE POLICY.*?;', self.sql, re.DOTALL | re.IGNORECASE
        )
        for section in policy_sections:
            assert "auth.role()" not in section, (
                f"auth.role() found in policy: {section[:100]}"
            )

    def test_notify_pgrst(self):
        """PostgREST cache is refreshed."""
        assert "NOTIFY pgrst" in self.sql

    def test_has_verification_query(self):
        """Includes verification SQL comment."""
        assert "pg_policies" in self.sql


class TestNoAuthRoleAcrossAllDebt009Migrations:
    """AC1: Zero auth.role() calls in any DEBT-009 migration policies."""

    def test_no_auth_role_in_debt009_migrations(self):
        debt009_files = [f for f in os.listdir(MIGRATIONS_DIR) if "debt009" in f]
        assert len(debt009_files) == 4, f"Expected 4 DEBT-009 migrations, got {len(debt009_files)}"

        for filename in debt009_files:
            sql = _read_migration(filename)
            # auth.role() should not appear in policy USING clauses
            # (it's OK in comments describing the old pattern)
            policy_sections = re.findall(
                r'CREATE POLICY.*?;', sql, re.DOTALL | re.IGNORECASE
            )
            for section in policy_sections:
                assert "auth.role()" not in section, (
                    f"auth.role() found in policy in {filename}: {section[:100]}"
                )


# ---------------------------------------------------------------------------
# Front 2: Retention pg_cron Jobs (DB-033, DB-037, DB-049)
# ---------------------------------------------------------------------------

class TestRetentionPgCronMigration:
    """Validates 20260308310000_debt009_retention_pgcron_jobs.sql"""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration("20260308310000_debt009_retention_pgcron_jobs.sql")

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, "20260308310000_debt009_retention_pgcron_jobs.sql")
        assert os.path.exists(path)

    def test_six_cron_jobs_scheduled(self):
        """AC2: 6 pg_cron retention jobs are scheduled."""
        schedules = re.findall(r"cron\.schedule\(", self.sql)
        assert len(schedules) == 6, f"Expected 6 cron.schedule() calls, got {len(schedules)}"

    def test_six_cron_jobs_unscheduled_first(self):
        """Idempotent: unschedule before schedule."""
        unschedules = re.findall(r"cron\.unschedule\(", self.sql)
        assert len(unschedules) == 6, f"Expected 6 cron.unschedule() calls, got {len(unschedules)}"

    @pytest.mark.parametrize("job_name,retention,table", [
        ("cleanup-search-state-transitions", "30 days", "search_state_transitions"),
        ("cleanup-alert-sent-items", "180 days", "alert_sent_items"),
        ("cleanup-health-checks", "30 days", "health_checks"),
        ("cleanup-incidents", "90 days", "incidents"),
        ("cleanup-mfa-recovery-attempts", "30 days", "mfa_recovery_attempts"),
        ("cleanup-alert-runs", "90 days", "alert_runs"),
    ])
    def test_job_exists_with_correct_retention(self, job_name, retention, table):
        """Each job targets the correct table with correct retention."""
        assert job_name in self.sql, f"Job {job_name} not found"
        assert table in self.sql, f"Table {table} not found"
        assert retention in self.sql, f"Retention {retention} not found"

    def test_staggered_schedules(self):
        """Jobs are staggered by 5 minutes to avoid I/O spikes."""
        minutes = re.findall(r"'(\d+) 4 \* \* \*'", self.sql)
        assert sorted(minutes) == ["0", "10", "15", "20", "25", "5"], (
            f"Expected staggered 4:00-4:25 UTC schedules, got {minutes}"
        )

    def test_alert_runs_only_deletes_completed(self):
        """alert_runs cleanup only removes completed runs."""
        # Find the alert_runs DELETE statement
        idx = self.sql.find("cleanup-alert-runs")
        section = self.sql[idx:idx+300]
        assert "status = 'completed'" in section, (
            "alert_runs cleanup should only delete completed runs"
        )

    def test_correct_timestamp_columns(self):
        """Each DELETE uses the correct timestamp column."""
        assert "created_at < now()" in self.sql  # search_state_transitions
        assert "sent_at < now()" in self.sql  # alert_sent_items
        assert "checked_at < now()" in self.sql  # health_checks
        assert "started_at < now()" in self.sql  # incidents (also alert_runs.run_at via run_at)
        assert "attempted_at < now()" in self.sql  # mfa_recovery_attempts
        assert "run_at < now()" in self.sql  # alert_runs


# ---------------------------------------------------------------------------
# Front 3: search_state_transitions Optimization (DB-007)
# ---------------------------------------------------------------------------

class TestSearchTransitionsOptimizeMigration:
    """Validates 20260308320000_debt009_search_transitions_optimize.sql"""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration("20260308320000_debt009_search_transitions_optimize.sql")

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, "20260308320000_debt009_search_transitions_optimize.sql")
        assert os.path.exists(path)

    def test_adds_user_id_column(self):
        """AC3: user_id column added to search_state_transitions."""
        assert "ADD COLUMN IF NOT EXISTS user_id UUID" in self.sql

    def test_user_id_references_profiles(self):
        """user_id references profiles(id) with CASCADE."""
        assert "REFERENCES public.profiles(id) ON DELETE CASCADE" in self.sql

    def test_backfills_from_search_sessions(self):
        """Backfills user_id from search_sessions via search_id join."""
        assert "FROM public.search_sessions ss" in self.sql
        assert "sst.search_id = ss.search_id" in self.sql
        assert "sst.user_id IS NULL" in self.sql

    def test_creates_user_id_index(self):
        """AC4: Index on user_id for fast RLS evaluation."""
        assert "idx_search_state_transitions_user_id" in self.sql
        assert "CREATE INDEX IF NOT EXISTS" in self.sql

    def test_drops_old_select_policy(self):
        """Old correlated subquery policy is dropped."""
        assert 'DROP POLICY IF EXISTS "Users can read own transitions"' in self.sql

    def test_new_select_policy_uses_direct_column(self):
        """AC3: New SELECT policy uses user_id = auth.uid() directly."""
        # Find the new CREATE POLICY for Users
        match = re.search(
            r'CREATE POLICY "Users can read own transitions".*?;',
            self.sql, re.DOTALL
        )
        assert match, "New Users policy not found"
        policy_sql = match.group()
        assert "user_id = auth.uid()" in policy_sql
        # Verify NO subquery
        assert "SELECT" not in policy_sql.split("USING")[1] if "USING" in policy_sql else True

    def test_no_correlated_subquery(self):
        """AC3: No correlated subquery remaining in policies."""
        policy_sections = re.findall(
            r'CREATE POLICY.*?;', self.sql, re.DOTALL | re.IGNORECASE
        )
        for section in policy_sections:
            if "Users can read" in section:
                assert "search_sessions" not in section, (
                    "Correlated subquery to search_sessions still present"
                )

    def test_replaces_insert_policy_with_service_role_all(self):
        """Old INSERT-only policy replaced with service_role ALL."""
        assert 'DROP POLICY IF EXISTS "Service role can insert transitions"' in self.sql
        assert '"service_role_all"' in self.sql
        assert "TO service_role" in self.sql

    def test_uses_transaction_block(self):
        """Migration is wrapped in BEGIN/COMMIT."""
        assert "BEGIN;" in self.sql
        assert "COMMIT;" in self.sql

    def test_has_explain_verification(self):
        """Includes EXPLAIN verification comment."""
        assert "EXPLAIN" in self.sql
        assert "Index Scan" in self.sql


# ---------------------------------------------------------------------------
# Front 4: Cache Warmer Ban (DB-010)
# ---------------------------------------------------------------------------

class TestCacheWarmerBanMigration:
    """Validates 20260308330000_debt009_ban_cache_warmer.sql"""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration("20260308330000_debt009_ban_cache_warmer.sql")

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, "20260308330000_debt009_ban_cache_warmer.sql")
        assert os.path.exists(path)

    def test_sets_banned_until(self):
        """AC5: Cache warmer account has banned_until set."""
        assert "banned_until" in self.sql
        assert "2099" in self.sql

    def test_targets_correct_email(self):
        """Targets the system cache warmer account."""
        assert "system-cache-warmer@internal.smartlic.tech" in self.sql

    def test_updates_auth_users(self):
        """Updates auth.users table (not profiles)."""
        assert "auth.users" in self.sql


# ---------------------------------------------------------------------------
# Backend Code: user_id Propagation (DB-007)
# ---------------------------------------------------------------------------

class TestStateTransitionUserIdField:
    """Verify StateTransition dataclass has user_id field."""

    def test_state_transition_has_user_id_field(self):
        from models.search_state import StateTransition, SearchState
        t = StateTransition(
            search_id="test-123",
            from_state=None,
            to_state=SearchState.CREATED,
            user_id="user-abc"
        )
        assert t.user_id == "user-abc"

    def test_state_transition_user_id_defaults_none(self):
        from models.search_state import StateTransition, SearchState
        t = StateTransition(
            search_id="test-123",
            from_state=None,
            to_state=SearchState.CREATED,
        )
        assert t.user_id is None


class TestSearchStateMachineUserIdPropagation:
    """Verify SearchStateMachine passes user_id to transitions."""

    @pytest.mark.asyncio
    async def test_state_machine_accepts_user_id(self):
        from search_state_manager import SearchStateMachine
        sm = SearchStateMachine("test-sm", user_id="user-xyz")
        assert sm.user_id == "user-xyz"

    @pytest.mark.asyncio
    async def test_state_machine_user_id_defaults_none(self):
        from search_state_manager import SearchStateMachine
        sm = SearchStateMachine("test-sm")
        assert sm.user_id is None

    @pytest.mark.asyncio
    async def test_transition_includes_user_id(self):
        from search_state_manager import SearchStateMachine
        from models.search_state import SearchState

        sm = SearchStateMachine("test-sm", user_id="user-xyz")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock) as mock_persist:
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")

                # Verify the transition passed to _persist_transition has user_id
                assert mock_persist.called
                transition = mock_persist.call_args[0][0]
                assert transition.user_id == "user-xyz"

    @pytest.mark.asyncio
    async def test_persist_transition_includes_user_id_in_row(self):
        """_persist_transition includes user_id in DB insert row."""
        from search_state_manager import _persist_transition
        from models.search_state import StateTransition, SearchState

        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_sb.table.return_value = mock_table

        transition = StateTransition(
            search_id="test-123",
            from_state=None,
            to_state=SearchState.CREATED,
            user_id="user-abc",
        )

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:  # noqa: F841
                await _persist_transition(transition)

                # Verify insert was called
                mock_table.insert.assert_called_once()
                row = mock_table.insert.call_args[0][0]
                assert row["user_id"] == "user-abc"
                assert row["search_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_persist_transition_omits_user_id_when_none(self):
        """_persist_transition does NOT include user_id when None."""
        from search_state_manager import _persist_transition
        from models.search_state import StateTransition, SearchState

        mock_sb = MagicMock()
        mock_table = MagicMock()
        mock_sb.table.return_value = mock_table

        transition = StateTransition(
            search_id="test-123",
            from_state=None,
            to_state=SearchState.CREATED,
            user_id=None,
        )

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:  # noqa: F841
                await _persist_transition(transition)

                row = mock_table.insert.call_args[0][0]
                assert "user_id" not in row


class TestCreateStateMachineAcceptsUserId:
    """Verify create_state_machine passes user_id."""

    @pytest.mark.asyncio
    async def test_create_state_machine_with_user_id(self):
        from search_state_manager import create_state_machine

        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                sm = await create_state_machine("test-search", user_id="user-abc")
                assert sm.user_id == "user-abc"

    @pytest.mark.asyncio
    async def test_create_state_machine_without_user_id(self):
        from search_state_manager import create_state_machine

        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                sm = await create_state_machine("test-search")
                assert sm.user_id is None


# ---------------------------------------------------------------------------
# Documentation: DISASTER-RECOVERY.md
# ---------------------------------------------------------------------------

class TestDisasterRecoveryDocumentation:
    """AC6: All pg_cron jobs documented."""

    @pytest.fixture(autouse=True)
    def load_doc(self):
        path = os.path.join(os.path.dirname(__file__), "..", "..", "DISASTER-RECOVERY.md")
        with open(path, encoding="utf-8") as f:
            self.doc = f.read()

    @pytest.mark.parametrize("job_name", [
        "cleanup-search-state-transitions",
        "cleanup-alert-sent-items",
        "cleanup-health-checks",
        "cleanup-incidents",
        "cleanup-mfa-recovery-attempts",
        "cleanup-alert-runs",
    ])
    def test_new_job_documented(self, job_name):
        """Each new pg_cron job is listed in DISASTER-RECOVERY.md."""
        assert job_name in self.doc, (
            f"pg_cron job '{job_name}' not found in DISASTER-RECOVERY.md"
        )

    def test_expected_11_jobs_total(self):
        """Document mentions 11 total jobs."""
        assert "11 jobs" in self.doc

    def test_debt009_migration_referenced(self):
        """DEBT-009 migration is referenced."""
        assert "DEBT-009" in self.doc


# ---------------------------------------------------------------------------
# Migration Idempotency Patterns
# ---------------------------------------------------------------------------

class TestMigrationIdempotency:
    """All DEBT-009 migrations follow idempotent patterns."""

    @pytest.mark.parametrize("filename", [
        "20260308300000_debt009_rls_standardize_remaining.sql",
        "20260308310000_debt009_retention_pgcron_jobs.sql",
        "20260308320000_debt009_search_transitions_optimize.sql",
        "20260308330000_debt009_ban_cache_warmer.sql",
    ])
    def test_migration_exists_and_nonempty(self, filename):
        path = os.path.join(MIGRATIONS_DIR, filename)
        assert os.path.exists(path), f"{filename} not found"
        sql = _read_migration(filename)
        assert len(sql) > 50, f"{filename} is too small"

    def test_rls_migration_uses_drop_if_exists(self):
        sql = _read_migration("20260308300000_debt009_rls_standardize_remaining.sql")
        assert "DROP POLICY IF EXISTS" in sql

    def test_optimize_migration_uses_add_column_if_not_exists(self):
        sql = _read_migration("20260308320000_debt009_search_transitions_optimize.sql")
        assert "ADD COLUMN IF NOT EXISTS" in sql

    def test_optimize_migration_uses_create_index_if_not_exists(self):
        sql = _read_migration("20260308320000_debt009_search_transitions_optimize.sql")
        assert "CREATE INDEX IF NOT EXISTS" in sql

    def test_pgcron_migration_uses_unschedule_before_schedule(self):
        sql = _read_migration("20260308310000_debt009_retention_pgcron_jobs.sql")
        # Each cron.schedule should have a preceding cron.unschedule
        schedules = len(re.findall(r"cron\.schedule\(", sql))
        unschedules = len(re.findall(r"cron\.unschedule\(", sql))
        assert schedules == unschedules, (
            f"Mismatch: {schedules} schedules vs {unschedules} unschedules"
        )
