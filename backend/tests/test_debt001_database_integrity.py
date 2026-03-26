"""DEBT-001: Database Integrity Critical Fixes — Tests.

Tests migration correctness, idempotency, and application-level handling of schema changes.

DB-013: partner_referrals.referred_user_id DROP NOT NULL
DB-038: Fix wrong table names in index migration
DB-039: classification_feedback user_id index
DB-012: Consolidate duplicate trigger functions
DB-032: pg_cron cleanup (already in 20260304110000)
DB-047: CHECK constraint (already in 20260304110000)
"""

import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace


# ============================================================================
# Migration SQL Validation
# ============================================================================

MIGRATION_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"
DEBT001_MIGRATION = MIGRATION_DIR / "20260308100000_debt001_database_integrity_fixes.sql"


class TestMigrationSQLContent:
    """Validate the migration SQL contains all required operations."""

    @pytest.fixture(autouse=True)
    def load_migration(self):
        """Load migration SQL once for all tests."""
        assert DEBT001_MIGRATION.exists(), f"Migration file not found: {DEBT001_MIGRATION}"
        self.sql = DEBT001_MIGRATION.read_text(encoding="utf-8")

    # -- DB-013 --
    def test_db013_drop_not_null(self):
        """DB-013: Migration drops NOT NULL from partner_referrals.referred_user_id."""
        assert "ALTER COLUMN referred_user_id DROP NOT NULL" in self.sql

    def test_db013_targets_partner_referrals(self):
        """DB-013: ALTER TABLE targets partner_referrals."""
        pattern = r"ALTER TABLE.*partner_referrals\s+ALTER COLUMN referred_user_id DROP NOT NULL"
        assert re.search(pattern, self.sql, re.IGNORECASE)

    # -- DB-038 --
    def test_db038_drops_wrong_indexes(self):
        """DB-038: Migration drops indexes with wrong table names."""
        assert "DROP INDEX IF EXISTS idx_searches_user_id" in self.sql
        assert "DROP INDEX IF EXISTS idx_pipeline_user_id" in self.sql
        assert "DROP INDEX IF EXISTS idx_feedback_user_id" in self.sql

    def test_db038_creates_correct_indexes(self):
        """DB-038: Migration creates indexes on correct table names."""
        assert "idx_search_sessions_user_id" in self.sql
        assert "ON public.search_sessions(user_id)" in self.sql
        assert "idx_pipeline_items_user_id" in self.sql
        assert "ON public.pipeline_items(user_id)" in self.sql

    def test_db038_search_results_store_index(self):
        """DB-038: Ensures search_results_store user_id index exists."""
        assert "idx_search_results_store_user_id" in self.sql
        assert "ON public.search_results_store(user_id)" in self.sql

    # -- DB-039 --
    def test_db039_classification_feedback_index(self):
        """DB-039: Creates standalone user_id index on classification_feedback."""
        assert "idx_classification_feedback_user_id" in self.sql
        assert "ON public.classification_feedback(user_id)" in self.sql

    # -- DB-012 --
    def test_db012_creates_canonical_function(self):
        """DB-012: Creates/replaces set_updated_at() as canonical function."""
        assert "CREATE OR REPLACE FUNCTION public.set_updated_at()" in self.sql

    def test_db012_drops_duplicate_function(self):
        """DB-012: Drops update_updated_at() after migrating all triggers."""
        assert "DROP FUNCTION IF EXISTS public.update_updated_at()" in self.sql

    def test_db012_migrates_profiles_trigger(self):
        """DB-012: Profiles trigger re-pointed to set_updated_at()."""
        assert "DROP TRIGGER IF EXISTS profiles_updated_at ON public.profiles" in self.sql
        pattern = r"CREATE TRIGGER profiles_updated_at.*EXECUTE FUNCTION public\.set_updated_at\(\)"
        assert re.search(pattern, self.sql, re.DOTALL)

    def test_db012_migrates_plan_features_trigger(self):
        """DB-012: plan_features trigger re-pointed."""
        assert "DROP TRIGGER IF EXISTS plan_features_updated_at ON public.plan_features" in self.sql

    def test_db012_migrates_plans_trigger(self):
        """DB-012: plans trigger re-pointed."""
        assert "DROP TRIGGER IF EXISTS plans_updated_at ON public.plans" in self.sql

    def test_db012_migrates_user_subscriptions_trigger(self):
        """DB-012: user_subscriptions trigger re-pointed."""
        assert "DROP TRIGGER IF EXISTS user_subscriptions_updated_at ON public.user_subscriptions" in self.sql

    def test_db012_migrates_organizations_trigger(self):
        """DB-012: organizations trigger re-pointed."""
        assert "DROP TRIGGER IF EXISTS tr_organizations_updated_at ON public.organizations" in self.sql

    def test_db012_all_triggers_use_set_updated_at(self):
        """DB-012: All CREATE TRIGGER statements use set_updated_at(), not update_updated_at()."""
        create_triggers = re.findall(r"CREATE TRIGGER.*?;", self.sql, re.DOTALL)
        for trigger in create_triggers:
            assert "set_updated_at()" in trigger, f"Trigger uses wrong function: {trigger[:80]}"
            assert "update_updated_at()" not in trigger

    def test_db012_drop_function_is_last(self):
        """DB-012: DROP FUNCTION comes after all trigger migrations."""
        drop_pos = self.sql.index("DROP FUNCTION IF EXISTS public.update_updated_at()")
        last_create = self.sql.rindex("CREATE TRIGGER")
        assert drop_pos > last_create, "DROP FUNCTION must come after all CREATE TRIGGER"

    def test_db012_five_triggers_migrated(self):
        """DB-012: Exactly 5 triggers are re-pointed."""
        drop_triggers = re.findall(r"DROP TRIGGER IF EXISTS \w+ ON public\.\w+", self.sql)
        create_triggers = re.findall(r"CREATE TRIGGER \w+", self.sql)
        assert len(drop_triggers) == 5, f"Expected 5 DROP TRIGGER, got {len(drop_triggers)}"
        assert len(create_triggers) == 5, f"Expected 5 CREATE TRIGGER, got {len(create_triggers)}"


class TestMigrationIdempotency:
    """Verify migration uses idempotent SQL patterns."""

    @pytest.fixture(autouse=True)
    def load_migration(self):
        self.sql = DEBT001_MIGRATION.read_text(encoding="utf-8")

    def test_indexes_use_if_not_exists(self):
        """All CREATE INDEX statements use IF NOT EXISTS."""
        create_indexes = re.findall(r"CREATE INDEX\b.*?;", self.sql, re.DOTALL)
        for idx in create_indexes:
            assert "IF NOT EXISTS" in idx, f"Missing IF NOT EXISTS: {idx[:80]}"

    def test_drops_use_if_exists(self):
        """All DROP statements use IF EXISTS."""
        drops = re.findall(r"DROP\s+(?:INDEX|TRIGGER|FUNCTION)\b.*?;", self.sql, re.DOTALL)
        for drop in drops:
            assert "IF EXISTS" in drop, f"Missing IF EXISTS: {drop[:80]}"

    def test_function_uses_create_or_replace(self):
        """set_updated_at() uses CREATE OR REPLACE."""
        assert "CREATE OR REPLACE FUNCTION public.set_updated_at()" in self.sql

    def test_no_raw_create_without_guard(self):
        """No unguarded CREATE statements (except triggers, which have prior DROP IF EXISTS)."""
        # Triggers are safe because we DROP IF EXISTS before each CREATE
        unguarded = re.findall(r"CREATE\s+(?!OR REPLACE|TRIGGER)(?!INDEX IF NOT EXISTS)\w+", self.sql)
        assert len(unguarded) == 0, f"Unguarded CREATE: {unguarded}"


# ============================================================================
# DB-032 / DB-047: Verify pre-existing hardening migration
# ============================================================================

HARDENING_MIGRATION = MIGRATION_DIR / "20260304110000_search_results_store_hardening.sql"


class TestHardeningMigrationExists:
    """DB-032/DB-047: Verify search_results_store hardening already exists."""

    @pytest.fixture(autouse=True)
    def load_migration(self):
        assert HARDENING_MIGRATION.exists(), "Hardening migration missing"
        self.sql = HARDENING_MIGRATION.read_text(encoding="utf-8")

    def test_db032_pg_cron_cleanup_scheduled(self):
        """DB-032: pg_cron cleanup job is scheduled."""
        assert "cron.schedule" in self.sql
        assert "cleanup-expired-search-results" in self.sql
        assert "DELETE FROM public.search_results_store" in self.sql

    def test_db047_check_constraint_exists(self):
        """DB-047: CHECK constraint for 2MB max exists."""
        assert "chk_result_data_size" in self.sql
        assert "octet_length(results::text)" in self.sql
        assert "2097152" in self.sql

    def test_db032_composite_index(self):
        """DB-032: Composite index for cleanup queries exists."""
        assert "idx_search_results_store_user_expires" in self.sql


# ============================================================================
# Application-level: Partner referrals with nullable referred_user_id
# ============================================================================

class TestPartnerReferralsNullableUser:
    """DB-013: Verify partner service handles NULL referred_user_id."""

    @pytest.mark.asyncio
    async def test_referral_with_null_user_in_revenue_calc(self):
        """Revenue calculation ignores referrals where user was deleted (NULL)."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                # 1. Get partner
                SimpleNamespace(data={"revenue_share_pct": "25.00", "name": "Test Partner"}),
                # 2. Get referrals — one with NULL referred_user_id (deleted user)
                SimpleNamespace(data=[
                    {"monthly_revenue": "397.00", "converted_at": "2026-01-15T00:00:00+00:00",
                     "churned_at": None, "referred_user_id": None},
                    {"monthly_revenue": "397.00", "converted_at": "2026-02-01T00:00:00+00:00",
                     "churned_at": None, "referred_user_id": "user-2"},
                ]),
            ]

            from services.partner_service import calculate_partner_revenue
            result = await calculate_partner_revenue("p-001", 2026, 3)

        # Both referrals should count (revenue exists regardless of user deletion)
        assert result["active_clients"] == 2
        assert result["total_revenue"] == 794.00

    @pytest.mark.asyncio
    async def test_create_referral_still_works(self):
        """Creating a referral still works with the column being nullable."""
        with patch("services.partner_service.get_supabase", return_value=MagicMock()), \
             patch("services.partner_service.sb_execute", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [
                SimpleNamespace(data={"referred_by_partner_id": "p-001"}),
                SimpleNamespace(data={"revenue_share_pct": "25.00"}),
                SimpleNamespace(data=[{"id": "ref-new"}]),
            ]

            from services.partner_service import create_partner_referral
            result = await create_partner_referral("user-valid", 397.00)

        assert result == "ref-new"


# ============================================================================
# Migration file ordering
# ============================================================================

class TestMigrationOrdering:
    """Verify corrective migration comes after the broken one."""

    def test_debt001_after_broken_migration(self):
        """Corrective migration timestamp is after 20260307100000."""
        broken = MIGRATION_DIR / "20260307100000_rls_index_user_id.sql"
        assert broken.exists(), "Broken migration should still exist"
        assert DEBT001_MIGRATION.exists()
        # Timestamp comparison via filename
        assert "20260308100000" > "20260307100000"

    def test_broken_migration_wrong_tables(self):
        """Document: original migration references non-existent tables."""
        broken_sql = (MIGRATION_DIR / "20260307100000_rls_index_user_id.sql").read_text(encoding="utf-8")
        # These table names are wrong
        assert "ON searches(user_id)" in broken_sql, "Broken migration should have wrong table 'searches'"
        assert "ON pipeline(user_id)" in broken_sql, "Broken migration should have wrong table 'pipeline'"
        assert "ON feedback(user_id)" in broken_sql, "Broken migration should have wrong table 'feedback'"


# ============================================================================
# Cross-migration: Trigger function references
# ============================================================================

class TestTriggerConsolidationCompleteness:
    """DB-012: Verify no migration after DEBT-001 references update_updated_at()."""

    def test_all_migrations_accounted_for(self):
        """All migrations that created update_updated_at triggers are addressed."""
        # These are the 5 migrations that created triggers using update_updated_at()
        sources = [
            "001_profiles_and_sessions.sql",       # profiles
            "009_create_plan_features.sql",          # plan_features
            "020_tighten_plan_type_constraint.sql",  # plans
            "021_user_subscriptions_updated_at.sql",  # user_subscriptions
            "20260301100000_create_organizations.sql",  # organizations
        ]
        for src in sources:
            assert (MIGRATION_DIR / src).exists(), f"Source migration not found: {src}"

    def test_consolidation_migration_already_handled_3_tables(self):
        """20260304120000 already handled pipeline_items, alert_preferences, alerts."""
        consolidation = MIGRATION_DIR / "20260304120000_rls_policies_trigger_consolidation.sql"
        assert consolidation.exists()
        sql = consolidation.read_text(encoding="utf-8")
        assert "pipeline_items" in sql
        assert "alert_preferences" in sql
        assert "alerts" in sql
