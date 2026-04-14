"""STORY-2.8 (TD-DB-011) AC3 + soft-delete columns:
validate migration 20260414131000_profiles_soft_delete_and_email_unique.sql
and confirm the partial UNIQUE index already ships via 20260224000000.
"""
from pathlib import Path
import re

import pytest


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"

SOFT_DELETE_MIGRATION = MIGRATIONS_DIR / "20260414131000_profiles_soft_delete_and_email_unique.sql"
PHONE_EMAIL_MIGRATION = MIGRATIONS_DIR / "20260224000000_phone_email_unique.sql"


@pytest.fixture(scope="module")
def soft_delete_sql() -> str:
    assert SOFT_DELETE_MIGRATION.exists(), f"Missing: {SOFT_DELETE_MIGRATION}"
    return SOFT_DELETE_MIGRATION.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def phone_email_sql() -> str:
    assert PHONE_EMAIL_MIGRATION.exists(), f"Missing: {PHONE_EMAIL_MIGRATION}"
    return PHONE_EMAIL_MIGRATION.read_text(encoding="utf-8")


class TestPartialUniqueIndexAlreadyEnforced:
    """AC3 is satisfied upstream by STORY-258 (partial unique on profiles.email)."""

    def test_partial_unique_index_exists_in_previous_migration(self, phone_email_sql: str):
        assert "idx_profiles_email_unique" in phone_email_sql
        # partial: WHERE email IS NOT NULL
        assert re.search(
            r"UNIQUE INDEX\s+idx_profiles_email_unique.*?WHERE\s+email\s+IS\s+NOT\s+NULL",
            phone_email_sql,
            re.IGNORECASE | re.DOTALL,
        )


class TestSoftDeleteMigration:
    def test_migration_exists(self):
        assert SOFT_DELETE_MIGRATION.exists()

    def test_adds_deleted_at_column(self, soft_delete_sql: str):
        assert re.search(
            r"ADD COLUMN IF NOT EXISTS\s+deleted_at\s+timestamptz",
            soft_delete_sql,
            re.IGNORECASE,
        )

    def test_adds_deleted_reason_column(self, soft_delete_sql: str):
        assert re.search(
            r"ADD COLUMN IF NOT EXISTS\s+deleted_reason\s+text",
            soft_delete_sql,
            re.IGNORECASE,
        )

    def test_adds_migrated_to_column_with_fk(self, soft_delete_sql: str):
        assert re.search(
            r"ADD COLUMN IF NOT EXISTS\s+migrated_to\s+uuid",
            soft_delete_sql,
            re.IGNORECASE,
        )
        # FK back to profiles.id with ON DELETE SET NULL
        assert re.search(
            r"REFERENCES\s+public\.profiles\s*\(\s*id\s*\)\s+ON DELETE SET NULL",
            soft_delete_sql,
            re.IGNORECASE,
        )

    def test_adds_active_index(self, soft_delete_sql: str):
        assert "idx_profiles_active" in soft_delete_sql
        assert re.search(
            r"WHERE\s+deleted_at\s+IS\s+NULL",
            soft_delete_sql,
            re.IGNORECASE,
        )

    def test_ensures_partial_unique_index_defensively(self, soft_delete_sql: str):
        """Migration guards against environments missing 20260224000000."""
        assert "idx_profiles_email_unique" in soft_delete_sql

    def test_wrapped_in_transaction(self, soft_delete_sql: str):
        assert "BEGIN;" in soft_delete_sql
        assert "COMMIT;" in soft_delete_sql

    def test_is_idempotent(self, soft_delete_sql: str):
        """No plain ADD COLUMN without IF NOT EXISTS."""
        add_columns = re.findall(r"ADD COLUMN\s+\w+", soft_delete_sql, re.IGNORECASE)
        add_if_not = re.findall(
            r"ADD COLUMN IF NOT EXISTS\s+\w+", soft_delete_sql, re.IGNORECASE
        )
        assert len(add_columns) == len(add_if_not), (
            "Every ADD COLUMN must be ADD COLUMN IF NOT EXISTS"
        )

    def test_has_column_comments_for_audit(self, soft_delete_sql: str):
        """Operators rely on COMMENT ON COLUMN to understand soft-delete semantics."""
        assert "COMMENT ON COLUMN public.profiles.deleted_at" in soft_delete_sql
        assert "COMMENT ON COLUMN public.profiles.deleted_reason" in soft_delete_sql
        assert "COMMENT ON COLUMN public.profiles.migrated_to" in soft_delete_sql
