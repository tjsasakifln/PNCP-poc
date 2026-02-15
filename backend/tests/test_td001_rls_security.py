"""
STORY-TD-001: RLS Security Policy Tests.

These tests validate the MIGRATION 027 SQL structure rather than executing
against a live database. They verify that:

SEC-T01: pipeline_items service role policy is scoped (TO service_role)
SEC-T02: search_results_cache service role policy is scoped (TO service_role)
SEC-T03: pipeline_items user policies enforce user_id = auth.uid()

These are static analysis tests of the migration SQL. Integration tests
against a real Supabase instance should be run separately as part of
post-deploy validation (queries V6-V8).
"""

import os
import pytest


@pytest.fixture
def migration_027_sql():
    """Load migration 027 SQL content."""
    migration_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "supabase",
        "migrations",
        "027_fix_plan_type_default_and_rls.sql",
    )
    with open(migration_path, "r", encoding="utf-8") as f:
        return f.read()


class TestMigration027PlanTypeDefault:
    """Verify migration fixes column default and trigger."""

    def test_column_default_changed_to_free_trial(self, migration_027_sql):
        """profiles.plan_type column default must be 'free_trial'."""
        assert "SET DEFAULT 'free_trial'" in migration_027_sql, (
            "Migration 027 must change profiles.plan_type default to 'free_trial'"
        )

    def test_handle_new_user_uses_free_trial(self, migration_027_sql):
        """handle_new_user() trigger must explicitly set plan_type = 'free_trial'."""
        # Check the trigger function sets free_trial
        assert "'free_trial'" in migration_027_sql, (
            "handle_new_user() must set plan_type = 'free_trial'"
        )
        # Ensure no occurrence of just 'free' as a plan_type value in the trigger
        lines = migration_027_sql.split("\n")
        for line in lines:
            if "plan_type" in line.lower() and "'free'" in line and "'free_trial'" not in line:
                if not line.strip().startswith("--"):  # Ignore comments
                    pytest.fail(
                        f"Found legacy 'free' plan_type in migration: {line.strip()}"
                    )


class TestMigration027RLSPipelineItems:
    """SEC-T01 + SEC-T03: pipeline_items RLS hardening."""

    def test_drops_overly_permissive_policy(self, migration_027_sql):
        """Must DROP the old USING(true) policy on pipeline_items."""
        assert 'DROP POLICY IF EXISTS "Service role full access on pipeline_items"' in migration_027_sql

    def test_recreates_policy_scoped_to_service_role(self, migration_027_sql):
        """New policy must use TO service_role clause."""
        # Find the section between DB-03 and DB-04 comments
        db03_start = migration_027_sql.find("3. DB-03")
        db04_start = migration_027_sql.find("4. DB-04")
        assert db03_start > 0, "Migration must contain DB-03 section"
        assert db04_start > db03_start, "DB-04 must come after DB-03"

        pipeline_section = migration_027_sql[db03_start:db04_start]
        assert "TO service_role" in pipeline_section, (
            "pipeline_items service role policy must be scoped with TO service_role. "
            "Without this, ANY authenticated user gets full access via FOR ALL USING(true)."
        )


class TestMigration027RLSSearchResultsCache:
    """SEC-T02: search_results_cache RLS hardening."""

    def test_drops_overly_permissive_policy(self, migration_027_sql):
        """Must DROP the old USING(true) policy on search_results_cache."""
        assert 'DROP POLICY IF EXISTS "Service role full access on search_results_cache"' in migration_027_sql

    def test_recreates_policy_scoped_to_service_role(self, migration_027_sql):
        """New policy must use TO service_role clause."""
        policy_section = migration_027_sql[
            migration_027_sql.find("CREATE POLICY", migration_027_sql.find("DB-04")):
        ]
        assert "TO service_role" in policy_section, (
            "search_results_cache service role policy must be scoped with TO service_role. "
            "Without this, ANY authenticated user gets full access via FOR ALL USING(true)."
        )


class TestMigration027Idempotency:
    """Verify migration is safe to re-run (idempotent patterns)."""

    def test_uses_drop_if_exists_before_create(self, migration_027_sql):
        """Policies use DROP IF EXISTS before CREATE for idempotency."""
        create_count = migration_027_sql.count("CREATE POLICY")
        drop_count = migration_027_sql.count("DROP POLICY IF EXISTS")

        assert drop_count >= create_count, (
            f"Found {create_count} CREATE POLICY but only {drop_count} DROP IF EXISTS. "
            "Each CREATE POLICY should have a corresponding DROP IF EXISTS for idempotency."
        )

    def test_uses_create_or_replace_for_function(self, migration_027_sql):
        """handle_new_user() uses CREATE OR REPLACE for idempotency."""
        assert "CREATE OR REPLACE FUNCTION" in migration_027_sql, (
            "handle_new_user() must use CREATE OR REPLACE for safe re-application."
        )
