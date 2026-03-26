"""
DEBT-104: DB Foundation — FK Standardization & Retention

Tests for:
- AC1: monthly_quota FK → profiles (already done by DEBT-100)
- AC2: user_oauth_tokens FK → profiles
- AC3: google_sheets_exports FK → profiles
- AC4: search_results_cache FK → profiles (already done)
- AC5: Orphan detection pre-migration
- AC6: search_state_transitions documentation (DEBT-017)
- AC7: search_results_cache duplicate size constraint check
- AC8: google_sheets_exports column rename (last_updated_at → updated_at)
- AC9: FK diagnostic verification
"""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ============================================================================
# Migration SQL Validation Tests
# ============================================================================


class TestMigrationSQL:
    """Validate migration file structure and content."""

    @pytest.fixture(autouse=True)
    def setup(self):
        migration_path = Path(__file__).parent.parent.parent / "supabase" / "migrations"
        self.migration_file = migration_path / "20260309300000_debt104_fk_standardization.sql"
        assert self.migration_file.exists(), f"Migration file not found: {self.migration_file}"
        self.sql = self.migration_file.read_text(encoding="utf-8")

    def test_ac2_user_oauth_tokens_fk_to_profiles(self):
        """AC2: user_oauth_tokens.user_id should reference profiles(id)."""
        assert "fk_user_oauth_tokens_user_id" in self.sql
        assert "REFERENCES profiles(id)" in self.sql
        assert "user_oauth_tokens" in self.sql
        # Verify CASCADE
        pattern = r"user_oauth_tokens.*FOREIGN KEY.*user_id.*REFERENCES profiles\(id\).*ON DELETE CASCADE"
        assert re.search(pattern, self.sql, re.DOTALL), "Missing CASCADE on user_oauth_tokens FK"

    def test_ac3_google_sheets_exports_fk_to_profiles(self):
        """AC3: google_sheets_exports.user_id should reference profiles(id)."""
        assert "fk_google_sheets_exports_user_id" in self.sql
        # Verify pattern
        pattern = r"google_sheets_exports.*FOREIGN KEY.*user_id.*REFERENCES profiles\(id\).*ON DELETE CASCADE"
        assert re.search(pattern, self.sql, re.DOTALL), "Missing CASCADE on google_sheets_exports FK"

    def test_ac5_orphan_deletion_before_fk(self):
        """AC5: Migration should delete orphans BEFORE altering FK constraints."""
        # Orphan deletion must appear before FK changes
        orphan_pos = self.sql.find("DELETE FROM user_oauth_tokens")
        fk_pos = self.sql.find("fk_user_oauth_tokens_user_id")
        assert orphan_pos < fk_pos, "Orphan deletion must come before FK constraint change"

        orphan_pos2 = self.sql.find("DELETE FROM google_sheets_exports")
        fk_pos2 = self.sql.find("fk_google_sheets_exports_user_id")
        assert orphan_pos2 < fk_pos2, "Orphan deletion must come before FK constraint change"

    def test_ac7_duplicate_constraint_check(self):
        """AC7: Migration should check for duplicate size constraints."""
        assert "chk_results_max_size" in self.sql
        assert "octet_length" in self.sql
        assert "duplicate" in self.sql.lower()

    def test_ac8_column_rename(self):
        """AC8: Migration should rename last_updated_at → updated_at."""
        assert "RENAME COLUMN last_updated_at TO updated_at" in self.sql

    def test_ac8_trigger_added(self):
        """AC8: Migration should add auto-update trigger for updated_at."""
        assert "trg_google_sheets_exports_updated_at" in self.sql
        assert "set_updated_at()" in self.sql

    def test_not_valid_pattern_used(self):
        """FK changes use NOT VALID + VALIDATE for minimal lock time."""
        assert "NOT VALID" in self.sql
        assert "VALIDATE CONSTRAINT" in self.sql

    def test_idempotent_with_if_exists(self):
        """Migration uses IF EXISTS/IF NOT EXISTS for idempotency."""
        assert "IF EXISTS" in self.sql
        assert "IF NOT EXISTS" in self.sql

    def test_drops_old_auth_users_fk(self):
        """Migration drops old auth.users FK before adding new profiles FK."""
        assert "DROP CONSTRAINT" in self.sql
        assert "user_oauth_tokens_user_id_fkey" in self.sql
        assert "google_sheets_exports_user_id_fkey" in self.sql

    def test_pgrst_reload(self):
        """Migration reloads PostgREST schema cache."""
        assert "NOTIFY pgrst, 'reload schema'" in self.sql

    def test_ac9_diagnostic_query_documented(self):
        """AC9: Post-migration FK diagnostic query is documented."""
        assert "information_schema.table_constraints" in self.sql
        assert "references_table" in self.sql


# ============================================================================
# Backend Code Tests — Column Rename (AC8)
# ============================================================================


class TestGoogleSheetsExportSchema:
    """Verify GoogleSheetsExportHistory schema uses updated_at."""

    def test_schema_has_updated_at(self):
        """AC8: GoogleSheetsExportHistory should use 'updated_at' not 'last_updated_at'."""
        from schemas import GoogleSheetsExportHistory

        fields = GoogleSheetsExportHistory.model_fields
        assert "updated_at" in fields, "GoogleSheetsExportHistory missing 'updated_at'"
        assert "last_updated_at" not in fields, "GoogleSheetsExportHistory still has 'last_updated_at'"

    def test_schema_serialization(self):
        """Verify schema serializes correctly with updated_at."""
        from schemas import GoogleSheetsExportHistory

        export = GoogleSheetsExportHistory(
            id="test-id",
            spreadsheet_id="sheet-1",
            spreadsheet_url="https://docs.google.com/spreadsheets/d/sheet-1",
            search_params={"ufs": ["SP"]},
            total_rows=10,
            created_at="2026-03-09T12:00:00Z",
            updated_at="2026-03-09T12:00:00Z"
        )
        data = export.model_dump()
        assert "updated_at" in data
        assert "last_updated_at" not in data


class TestExportHistoryEndpoint:
    """Test export history endpoint uses updated_at column."""

    @pytest.fixture
    def app(self):
        from routes.export_sheets import router
        test_app = FastAPI()
        test_app.include_router(router)
        return test_app

    @pytest.fixture
    def client(self, app):
        from auth import require_auth

        app.dependency_overrides[require_auth] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com"
        }
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()

    def test_export_history_returns_updated_at(self, client):
        """Export history response should contain 'updated_at' field."""
        mock_data = [
            {
                "id": "export-1",
                "spreadsheet_id": "sheet-1",
                "spreadsheet_url": "https://docs.google.com/spreadsheets/d/sheet-1",
                "search_params": {"ufs": ["SP"]},
                "total_rows": 42,
                "created_at": "2026-03-09T12:00:00Z",
                "updated_at": "2026-03-09T12:00:00Z"
            }
        ]

        mock_supabase = Mock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=mock_data
        )

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            response = client.get("/api/export/google-sheets/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data["exports"]) == 1
        assert "updated_at" in data["exports"][0]
        assert "last_updated_at" not in data["exports"][0]

    @pytest.mark.asyncio
    async def test_save_export_inserts_updated_at(self):
        """_save_export_history should insert 'updated_at' column."""
        from routes.export_sheets import _save_export_history

        mock_supabase = Mock()
        mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(data=[{}])

        with patch("routes.export_sheets.get_supabase", return_value=mock_supabase):
            await _save_export_history(
                user_id="test-user",
                spreadsheet_id="sheet-1",
                spreadsheet_url="https://example.com",
                search_params={"ufs": ["SP"]},
                total_rows=10
            )

        # Verify the insert was called with 'updated_at', not 'last_updated_at'
        insert_call = mock_supabase.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert "updated_at" in inserted_data
        assert "last_updated_at" not in inserted_data


# ============================================================================
# FK Consistency Verification Tests (AC1, AC4, AC6)
# ============================================================================


class TestPriorMigrationVerification:
    """Verify prior migrations (DEBT-100, DEBT-017) already handled ACs."""

    def test_ac1_monthly_quota_already_fixed(self):
        """AC1: DEBT-100 already fixed monthly_quota FK to profiles."""
        debt100 = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "20260309200000_debt100_db_quick_wins.sql"
        if debt100.exists():
            sql = debt100.read_text(encoding="utf-8")
            assert "monthly_quota" in sql
            assert "profiles" in sql

    def test_ac4_search_results_cache_already_fixed(self):
        """AC4: Migration 20260224 already fixed search_results_cache FK to profiles."""
        fix_file = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "20260224200000_fix_cache_user_fk.sql"
        if fix_file.exists():
            sql = fix_file.read_text(encoding="utf-8")
            assert "search_results_cache_user_id_profiles_fkey" in sql
            assert "profiles(id)" in sql

    def test_ac6_search_state_transitions_documented(self):
        """AC6: DEBT-017 already documented search_state_transitions FK absence."""
        debt017 = Path(__file__).parent.parent.parent / "supabase" / "migrations" / "20260309100000_debt017_database_long_term_optimization.sql"
        if debt017.exists():
            sql = debt017.read_text(encoding="utf-8")
            assert "search_state_transitions.search_id" in sql
            assert "No FK constraint" in sql or "Cannot add FK" in sql


# ============================================================================
# Rollback Plan Verification
# ============================================================================


class TestRollbackDocumented:
    """Verify rollback procedures are in the migration."""

    def test_migration_has_fk_constraint_names(self):
        """Rollback requires knowing constraint names — verify they're documented."""
        migration_path = Path(__file__).parent.parent.parent / "supabase" / "migrations"
        migration_file = migration_path / "20260309300000_debt104_fk_standardization.sql"
        sql = migration_file.read_text(encoding="utf-8")

        # Both new constraint names are documented
        assert "fk_user_oauth_tokens_user_id" in sql
        assert "fk_google_sheets_exports_user_id" in sql
        # Both old constraint names are documented for rollback reference
        assert "user_oauth_tokens_user_id_fkey" in sql
        assert "google_sheets_exports_user_id_fkey" in sql
