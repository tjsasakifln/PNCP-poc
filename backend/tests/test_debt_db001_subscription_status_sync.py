"""
DEBT-DB-001: Subscription Status Sync Trigger Tests

Validates the migration that syncs user_subscriptions.subscription_status
to profiles.subscription_status via a PostgreSQL trigger.

Tests:
- Migration SQL structure and idempotency
- Enum mapping correctness (user_subscriptions -> profiles values)
- Trigger fires on INSERT and UPDATE of subscription_status
- Unknown status values are safely ignored
"""
import os
import re


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "migrations"
)

MIGRATION_FILE = "20260321100000_debt_db001_subscription_status_sync.sql"


def _read_migration() -> str:
    path = os.path.join(MIGRATIONS_DIR, MIGRATION_FILE)
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestMigrationSQL:
    """Validate migration SQL content and structure."""

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, MIGRATION_FILE)
        assert os.path.isfile(path), f"Migration file not found: {path}"

    def test_creates_function(self):
        sql = _read_migration()
        assert "CREATE OR REPLACE FUNCTION sync_subscription_status_to_profile" in sql

    def test_creates_trigger(self):
        sql = _read_migration()
        assert "CREATE TRIGGER trg_sync_subscription_status" in sql

    def test_trigger_fires_on_insert_and_update(self):
        sql = _read_migration()
        assert "AFTER INSERT OR UPDATE OF subscription_status" in sql
        assert "ON user_subscriptions" in sql

    def test_trigger_is_idempotent(self):
        """DROP IF EXISTS before CREATE ensures idempotency."""
        sql = _read_migration()
        assert "DROP TRIGGER IF EXISTS trg_sync_subscription_status" in sql

    def test_function_is_security_definer(self):
        """SECURITY DEFINER is needed to update profiles table across RLS."""
        sql = _read_migration()
        assert "SECURITY DEFINER" in sql

    def test_uses_is_distinct_from(self):
        """IS DISTINCT FROM prevents no-op updates when status hasn't changed."""
        sql = _read_migration()
        assert "IS DISTINCT FROM" in sql


class TestEnumMapping:
    """Validate the enum mapping from user_subscriptions to profiles."""

    # profiles CHECK: trial, active, canceling, past_due, expired
    # user_subscriptions CHECK: active, trialing, past_due, canceled, expired
    EXPECTED_MAPPINGS = {
        "active": "active",
        "trialing": "trial",
        "past_due": "past_due",
        "canceled": "canceling",
        "expired": "expired",
    }

    def test_all_user_subscriptions_statuses_mapped(self):
        """Every user_subscriptions status value must be mapped in the trigger."""
        sql = _read_migration()
        for us_status in self.EXPECTED_MAPPINGS:
            assert f"'{us_status}'" in sql, (
                f"user_subscriptions status '{us_status}' not found in migration"
            )

    def test_maps_to_valid_profiles_values(self):
        """Every mapped value must be a valid profiles.subscription_status."""
        sql = _read_migration()
        valid_profiles_statuses = {"trial", "active", "canceling", "past_due", "expired"}
        for us_status, profile_status in self.EXPECTED_MAPPINGS.items():
            assert profile_status in valid_profiles_statuses, (
                f"Mapped status '{profile_status}' is not a valid profiles value"
            )
            assert f"'{profile_status}'" in sql

    def test_trialing_maps_to_trial(self):
        """Critical mapping: user_subscriptions 'trialing' -> profiles 'trial'."""
        sql = _read_migration()
        # Find the WHEN 'trialing' line and verify the mapped value
        pattern = r"WHEN\s+'trialing'\s+THEN\s+mapped_status\s*:=\s*'trial'"
        assert re.search(pattern, sql), "trialing -> trial mapping not found"

    def test_canceled_maps_to_canceling(self):
        """Critical mapping: user_subscriptions 'canceled' -> profiles 'canceling'."""
        sql = _read_migration()
        pattern = r"WHEN\s+'canceled'\s+THEN\s+mapped_status\s*:=\s*'canceling'"
        assert re.search(pattern, sql), "canceled -> canceling mapping not found"

    def test_unknown_status_handled_safely(self):
        """Unknown status values should result in NULL (no update)."""
        sql = _read_migration()
        assert "ELSE mapped_status := NULL" in sql

    def test_null_mapped_status_skips_update(self):
        """When mapped_status is NULL, the UPDATE should be skipped."""
        sql = _read_migration()
        assert "IF mapped_status IS NOT NULL" in sql


class TestMigrationComments:
    """Validate documentation comments in migration."""

    def test_has_function_comment(self):
        sql = _read_migration()
        assert "COMMENT ON FUNCTION sync_subscription_status_to_profile" in sql

    def test_has_trigger_comment(self):
        sql = _read_migration()
        assert "COMMENT ON TRIGGER trg_sync_subscription_status" in sql

    def test_documents_source_of_truth(self):
        sql = _read_migration()
        assert "source of truth" in sql.lower() or "Source of truth" in sql
