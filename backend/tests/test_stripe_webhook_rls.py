"""STORY-2.7 (TD-DB-010): validate migration fixing Stripe webhook RLS admin policy.

Ensures 20260414130000_fix_stripe_webhook_rls_admin.sql:
  - Exists as a file
  - Uses derived is_master logic (is_admin = true OR plan_type = 'master')
  - Drops the legacy policy before recreating
  - Does not regress to legacy plan_type='master'-only check
"""
import os
import re
from pathlib import Path

import pytest


MIGRATION_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "supabase"
    / "migrations"
    / "20260414130000_fix_stripe_webhook_rls_admin.sql"
)


@pytest.fixture(scope="module")
def migration_sql() -> str:
    assert MIGRATION_PATH.exists(), f"Missing migration: {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


class TestStripeWebhookRLSMigration:
    def test_migration_exists(self):
        assert MIGRATION_PATH.exists(), f"Migration file missing: {MIGRATION_PATH}"

    def test_drops_policy_before_recreate(self, migration_sql: str):
        """Idempotency: migration drops the policy before recreating it."""
        assert "DROP POLICY IF EXISTS" in migration_sql
        assert '"webhook_events_select_admin"' in migration_sql

    def test_policy_uses_is_admin_check(self, migration_sql: str):
        """STORY-2.7 AC1: policy accepts is_admin = true."""
        assert re.search(r"is_admin\s*=\s*true", migration_sql, re.IGNORECASE)

    def test_policy_uses_plan_type_master(self, migration_sql: str):
        """STORY-2.7 AC1: policy accepts plan_type = 'master' as derived is_master."""
        assert re.search(
            r"plan_type\s*=\s*'master'", migration_sql, re.IGNORECASE
        ), "Policy must grant access to plan_type='master' users (derived is_master)"

    def test_policy_logical_or_between_admin_and_master(self, migration_sql: str):
        """STORY-2.7 AC1: the two conditions are OR-joined, not AND."""
        # Extract the CREATE POLICY block to scope the check
        match = re.search(
            r"CREATE POLICY\s+\"webhook_events_select_admin\".*?;",
            migration_sql,
            re.DOTALL | re.IGNORECASE,
        )
        assert match, "CREATE POLICY block not found"
        block = match.group(0)
        assert re.search(r"is_admin\s*=\s*true\s*OR\s*profiles\.plan_type\s*=\s*'master'", block, re.IGNORECASE) \
            or re.search(r"plan_type\s*=\s*'master'\s*OR\s*profiles?\.?is_admin\s*=\s*true", block, re.IGNORECASE), (
                "Conditions must be OR-joined to mirror backend authorization.py derivation"
            )

    def test_policy_scoped_to_authenticated_role(self, migration_sql: str):
        """Preserve scoping improvement from migration 028."""
        assert re.search(r"TO\s+authenticated", migration_sql, re.IGNORECASE)

    def test_for_select_only(self, migration_sql: str):
        """Policy applies to SELECT only (read-only debug access)."""
        match = re.search(
            r"CREATE POLICY\s+\"webhook_events_select_admin\".*?;",
            migration_sql,
            re.DOTALL | re.IGNORECASE,
        )
        assert match
        assert re.search(r"FOR\s+SELECT", match.group(0), re.IGNORECASE)

    def test_has_comment_for_audit(self, migration_sql: str):
        """Every policy change must ship with a COMMENT ON POLICY for auditability."""
        assert "COMMENT ON POLICY" in migration_sql
        assert "STORY-2.7" in migration_sql or "TD-DB-010" in migration_sql

    def test_wrapped_in_transaction(self, migration_sql: str):
        """Atomicity: all-or-nothing migration."""
        assert "BEGIN;" in migration_sql
        assert "COMMIT;" in migration_sql
