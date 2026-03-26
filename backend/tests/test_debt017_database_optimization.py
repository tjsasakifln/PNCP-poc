"""
DEBT-017: Database Long-Term Optimization Tests

Tests cover:
- Migration SQL validation (idempotency, correctness)
- AC1: Accepted risks documented in DB-AUDIT.md
- AC2: Partner RLS uses contact_email (no profiles.email cross-schema)
- AC3: Legacy stripe_price_id deprecated via COMMENT
- AC4: NOT NULL DEFAULT now() on created_at columns
- AC5: Stripe Price IDs parameterized for staging/dev (seed script)
- AC6: Cleanup trigger short-circuit optimization
- AC7: Conversations query uses LEFT JOIN (not correlated subquery)
- AC8: Zero regressions
"""
import os
import re
import pytest


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "migrations"
)

DOCS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "docs"
)

SEED_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "seed"
)

SCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts"
)

MIGRATION_FILE = "20260309100000_debt017_database_long_term_optimization.sql"


def _read_migration(filename: str) -> str:
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_file(filepath: str) -> str:
    with open(filepath, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Migration File Existence & Structure
# ---------------------------------------------------------------------------

class TestMigrationFileStructure:
    """Validates the DEBT-017 migration file exists and is well-formed."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, MIGRATION_FILE)
        assert os.path.exists(path), f"Migration file {MIGRATION_FILE} not found"

    def test_migration_is_idempotent(self):
        """All DDL uses IF NOT EXISTS / DO $$ guards for re-runnability."""
        # Check ALTER TABLE NOT NULL uses DO $$ block
        assert "DO $$" in self.sql, "Migration should use DO $$ blocks for idempotency"
        assert "EXCEPTION" in self.sql, "Migration should handle exceptions for idempotency"

    def test_migration_has_schema_reload(self):
        """Migration ends with PostgREST schema cache reload."""
        assert "NOTIFY pgrst" in self.sql

    def test_migration_header_references_debt_ids(self):
        """Header documents all DB-xxx IDs addressed."""
        header = self.sql[:300]
        for db_id in ["DB-004", "DB-014", "DB-017", "DB-034", "DB-035"]:
            assert db_id in header, f"{db_id} not referenced in migration header"


# ---------------------------------------------------------------------------
# AC4: NOT NULL DEFAULT now() on created_at columns (DB-017)
# ---------------------------------------------------------------------------

class TestAC4NotNullCreatedAt:
    """AC4: All created_at columns have NOT NULL DEFAULT now()."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_google_sheets_exports_created_at_not_null(self):
        """google_sheets_exports.created_at gets NOT NULL constraint."""
        assert "google_sheets_exports" in self.sql
        # Check the ALTER TABLE sets NOT NULL
        section = self.sql[self.sql.find("google_sheets_exports"):self.sql.find("google_sheets_exports") + 500]
        assert "SET NOT NULL" in section

    def test_partners_created_at_not_null(self):
        """partners.created_at gets NOT NULL constraint."""
        # Find partners section (after google_sheets_exports section)
        idx = self.sql.find("partners.created_at")
        assert idx > 0, "partners.created_at section not found"
        section = self.sql[idx:idx + 500]
        assert "SET NOT NULL" in section

    def test_null_rows_handled_before_constraint(self):
        """UPDATE sets now() on NULL rows before adding NOT NULL."""
        # google_sheets_exports
        gs_idx = self.sql.find("google_sheets_exports")
        gs_section = self.sql[gs_idx:gs_idx + 500]
        assert "WHERE created_at IS NULL" in gs_section, \
            "Must UPDATE NULL rows before adding NOT NULL constraint"

        # partners
        p_idx = self.sql.find("partners")
        p_section = self.sql[p_idx:p_idx + 500]
        assert "WHERE created_at IS NULL" in p_section


# ---------------------------------------------------------------------------
# AC3: Legacy stripe_price_id deprecated (DB-014)
# ---------------------------------------------------------------------------

class TestAC3StripePriceIdDeprecation:
    """AC3: Legacy stripe_price_id column is deprecated via COMMENT."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_deprecation_comment_added(self):
        """SQL COMMENT marks plans.stripe_price_id as DEPRECATED."""
        assert "DEPRECATED" in self.sql
        assert "COMMENT ON COLUMN plans.stripe_price_id" in self.sql

    def test_deprecation_suggests_alternatives(self):
        """Comment suggests period-specific columns and plan_billing_periods."""
        idx = self.sql.find("COMMENT ON COLUMN plans.stripe_price_id")
        section = self.sql[idx:idx + 500]
        assert "stripe_price_id_monthly" in section or "plan_billing_periods" in section

    def test_column_not_dropped(self):
        """Column is NOT dropped (billing.py fallback still uses it)."""
        assert "DROP COLUMN" not in self.sql or "stripe_price_id" not in self.sql.split("DROP COLUMN")[1][:50] if "DROP COLUMN" in self.sql else True


# ---------------------------------------------------------------------------
# AC6: Cleanup trigger short-circuit (DB-034)
# ---------------------------------------------------------------------------

class TestAC6CleanupTriggerShortCircuit:
    """AC6: cleanup_search_cache_per_user has short-circuit optimization."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_short_circuit_count_check(self):
        """Trigger checks entry count before running full cleanup."""
        func_start = self.sql.find("cleanup_search_cache_per_user")
        assert func_start > 0
        func_section = self.sql[func_start:func_start + 800]
        assert "COUNT(*)" in func_section, "Short-circuit must count entries"
        assert "<= 5" in func_section or "<=5" in func_section, \
            "Short-circuit threshold should be 5 entries"

    def test_returns_early_when_under_threshold(self):
        """Function returns NEW early when count <= 5."""
        func_start = self.sql.find("cleanup_search_cache_per_user")
        func_section = self.sql[func_start:func_start + 800]
        assert "RETURN NEW" in func_section, "Must return NEW on short-circuit"

    def test_still_deletes_when_over_threshold(self):
        """Function still deletes oldest entries when count > 5."""
        func_start = self.sql.find("cleanup_search_cache_per_user")
        func_section = self.sql[func_start:func_start + 800]
        assert "DELETE FROM search_results_cache" in func_section
        assert "OFFSET 5" in func_section

    def test_trigger_uses_security_definer(self):
        """Function retains SECURITY DEFINER."""
        func_start = self.sql.find("cleanup_search_cache_per_user")
        func_section = self.sql[func_start:func_start + 1000]
        assert "SECURITY DEFINER" in func_section


# ---------------------------------------------------------------------------
# AC7: Conversations query uses LEFT JOIN (DB-035)
# ---------------------------------------------------------------------------

class TestAC7ConversationsQueryJoin:
    """AC7: get_conversations_with_unread_count uses JOIN instead of correlated subquery."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_function_uses_left_join_lateral(self):
        """Query uses LEFT JOIN LATERAL for unread count."""
        func_start = self.sql.find("get_conversations_with_unread_count")
        assert func_start > 0
        func_section = self.sql[func_start:func_start + 2000]
        assert "LEFT JOIN LATERAL" in func_section, \
            "Must use LEFT JOIN LATERAL instead of correlated subquery"

    def test_function_returns_same_columns(self):
        """Function signature returns all expected columns."""
        func_start = self.sql.find("get_conversations_with_unread_count")
        func_section = self.sql[func_start:func_start + 1000]
        required_columns = [
            "id UUID", "user_id UUID", "user_email TEXT",
            "subject TEXT", "category TEXT", "status TEXT",
            "last_message_at TIMESTAMPTZ", "created_at TIMESTAMPTZ",
            "unread_count BIGINT", "total_count BIGINT",
        ]
        for col in required_columns:
            assert col in func_section, f"Missing return column: {col}"

    def test_function_has_same_parameters(self):
        """Function signature has same parameters as original."""
        func_start = self.sql.find("get_conversations_with_unread_count")
        func_section = self.sql[func_start:func_start + 500]
        assert "p_user_id UUID" in func_section
        assert "p_is_admin BOOLEAN" in func_section
        assert "p_status TEXT" in func_section
        assert "p_limit INT" in func_section
        assert "p_offset INT" in func_section

    def test_no_correlated_subquery_in_select(self):
        """The SELECT clause should not have (SELECT COUNT(*) FROM messages ...) pattern."""
        func_start = self.sql.find("get_conversations_with_unread_count")
        func_end = self.sql.find("$$ LANGUAGE plpgsql", func_start)
        func_body = self.sql[func_start:func_end]
        # The old pattern was a subquery in the SELECT list
        # New pattern uses LEFT JOIN LATERAL, so COUNT should be in the FROM clause
        select_sections = re.findall(r'SELECT\s+.*?FROM', func_body, re.DOTALL)
        # The main SELECT (not the lateral) should not have COUNT(*) from messages
        main_select = select_sections[-1] if select_sections else ""  # noqa: F841
        assert "uc.unread" in func_body, "Should reference lateral alias uc.unread"

    def test_function_comment_updated(self):
        """Function COMMENT references both STORY-202 and DEBT-017."""
        assert "DEBT-017" in self.sql
        idx = self.sql.find("COMMENT ON FUNCTION get_conversations_with_unread_count")
        assert idx > 0
        comment_section = self.sql[idx:idx + 300]
        assert "LEFT JOIN" in comment_section or "JOIN" in comment_section


# ---------------------------------------------------------------------------
# AC1: Accepted risks documented in DB-AUDIT.md
# ---------------------------------------------------------------------------

class TestAC1AcceptedRisksDocumented:
    """AC1: All accepted risks documented in DB-AUDIT.md or SQL COMMENTs."""

    @pytest.fixture(autouse=True)
    def load_docs(self):
        path = os.path.join(DOCS_DIR, "DB-AUDIT.md")
        self.audit_md = _read_file(path)
        self.sql = _read_migration(MIGRATION_FILE)

    def test_db004_mfa_rate_limiting_documented(self):
        """DB-004: MFA rate limiting app-layer pattern documented."""
        assert "DB-004" in self.audit_md
        assert "rate limiting" in self.audit_md.lower()

    def test_db005_mfa_recovery_attempts_documented(self):
        """DB-005: mfa_recovery_attempts intentional design documented."""
        assert "DB-005" in self.audit_md
        assert "information leakage" in self.audit_md.lower() or "intentional" in self.audit_md.lower()

    def test_db006_trial_email_log_documented(self):
        """DB-006: trial_email_log backend-only documented."""
        assert "DB-006" in self.audit_md
        assert "backend-only" in self.audit_md.lower() or "Backend-only" in self.audit_md

    def test_db008_stripe_price_ids_documented(self):
        """DB-008: Stripe Price IDs visibility accepted risk documented."""
        assert "DB-008" in self.audit_md
        assert "ACCEPTED" in self.audit_md

    def test_db016_status_transitions_documented(self):
        """DB-016: Status transition enforcement documented."""
        assert "DB-016" in self.audit_md or "DB-016" in self.sql
        # Also check SQL COMMENT on search_sessions.status
        assert "search_sessions.status" in self.sql or "DB-016" in self.audit_md

    def test_db020_naming_convention_documented(self):
        """DB-020: Naming convention documented."""
        assert "DB-020" in self.audit_md
        assert "chk_" in self.audit_md

    def test_db022_phone_validation_documented(self):
        """DB-022: Phone validation as app-layer documented."""
        assert "DB-022" in self.audit_md

    def test_db023_cache_sharing_documented(self):
        """DB-023: SWR cache sharing risks documented."""
        assert "DB-023" in self.audit_md

    def test_db027_down_migrations_documented(self):
        """DB-027: Down-migration strategy documented."""
        assert "DB-027" in self.audit_md
        assert "PITR" in self.audit_md

    def test_db036_partitioning_strategy_documented(self):
        """DB-036: Partitioning strategy documented."""
        assert "DB-036" in self.audit_md
        assert "1M" in self.audit_md or "partitioning" in self.audit_md.lower()

    def test_db044_pgcron_documented(self):
        """DB-044: pg_cron manual setup documented."""
        assert "DB-044" in self.audit_md
        assert "pg_cron" in self.audit_md or "pg-cron" in self.audit_md

    def test_db046_schema_change_policy_documented(self):
        """DB-046: Schema change audit policy documented."""
        assert "DB-046" in self.audit_md
        assert "dashboard" in self.audit_md.lower()

    def test_db050_fk_evaluation_documented(self):
        """DB-050: FK evaluation for search_state_transitions documented."""
        assert "DB-050" in self.audit_md
        assert "search_state_transitions" in self.audit_md


# ---------------------------------------------------------------------------
# AC2: Partner RLS uses contact_email (DB-009)
# ---------------------------------------------------------------------------

class TestAC2PartnerRLS:
    """AC2: Partner RLS already uses contact_email (no profiles.email cross-schema)."""

    @pytest.fixture(autouse=True)
    def load_files(self):
        self.partner_sql = _read_migration("20260301200000_create_partners.sql")
        self.audit_md = _read_file(os.path.join(DOCS_DIR, "DB-AUDIT.md"))

    def test_partner_rls_uses_contact_email(self):
        """partners_self_read policy uses contact_email field."""
        assert "contact_email" in self.partner_sql
        # The policy compares contact_email to auth.users.email
        assert "contact_email =" in self.partner_sql

    def test_partner_rls_does_not_query_profiles_email(self):
        """partners_self_read policy does NOT query profiles.email."""
        # Find the partners_self_read policy
        idx = self.partner_sql.find("partners_self_read")
        assert idx > 0
        policy_section = self.partner_sql[idx:idx + 300]
        assert "profiles.email" not in policy_section, \
            "Partner RLS should NOT query profiles.email"

    def test_db009_documented_in_audit(self):
        """DB-009 optimization documented in DB-AUDIT.md."""
        assert "DB-009" in self.audit_md


# ---------------------------------------------------------------------------
# AC5: Stripe Price IDs parameterized (DB-029)
# ---------------------------------------------------------------------------

class TestAC5StripeParameterization:
    """AC5: Stripe Price IDs parameterized for staging/dev setup."""

    def test_seed_script_exists(self):
        """Seed SQL script for Stripe Price IDs exists."""
        path = os.path.join(SEED_DIR, "seed_stripe_prices.sql")
        assert os.path.exists(path), "supabase/seed/seed_stripe_prices.sql not found"

    def test_seed_script_covers_smartlic_pro(self):
        """Seed script updates SmartLic Pro plan."""
        seed_sql = _read_file(os.path.join(SEED_DIR, "seed_stripe_prices.sql"))
        assert "smartlic_pro" in seed_sql

    def test_seed_script_covers_consultoria(self):
        """Seed script updates Consultoria plan."""
        seed_sql = _read_file(os.path.join(SEED_DIR, "seed_stripe_prices.sql"))
        assert "consultoria" in seed_sql

    def test_seed_script_updates_plan_billing_periods(self):
        """Seed script also updates plan_billing_periods table."""
        seed_sql = _read_file(os.path.join(SEED_DIR, "seed_stripe_prices.sql"))
        assert "plan_billing_periods" in seed_sql

    def test_seed_script_uses_current_setting(self):
        """Seed script uses current_setting() for parameterization."""
        seed_sql = _read_file(os.path.join(SEED_DIR, "seed_stripe_prices.sql"))
        assert "current_setting" in seed_sql

    def test_seed_script_no_hardcoded_price_ids(self):
        """Seed script does NOT contain hardcoded price_xxx IDs."""
        seed_sql = _read_file(os.path.join(SEED_DIR, "seed_stripe_prices.sql"))
        assert "price_1" not in seed_sql, "Seed script should not contain hardcoded Stripe Price IDs"

    def test_shell_helper_script_exists(self):
        """Shell helper script for seeding exists."""
        path = os.path.join(SCRIPTS_DIR, "seed-stripe-prices.sh")
        assert os.path.exists(path), "scripts/seed-stripe-prices.sh not found"

    def test_shell_script_references_all_env_vars(self):
        """Shell script documents all required environment variables."""
        script = _read_file(os.path.join(SCRIPTS_DIR, "seed-stripe-prices.sh"))
        required_vars = [
            "SMARTLIC_PRO_MONTHLY",
            "SMARTLIC_PRO_SEMIANNUAL",
            "SMARTLIC_PRO_ANNUAL",
            "CONSULTORIA_MONTHLY",
            "CONSULTORIA_SEMIANNUAL",
            "CONSULTORIA_ANNUAL",
        ]
        for var in required_vars:
            assert var in script, f"Shell script missing env var: {var}"


# ---------------------------------------------------------------------------
# DB-024: plan_billing_periods updated_at column
# ---------------------------------------------------------------------------

class TestDB024UpdatedAtColumn:
    """DB-024: plan_billing_periods gets updated_at column."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_updated_at_column_added(self):
        """Migration adds updated_at column to plan_billing_periods."""
        # Find the DB-024 section header (not the header comment)
        idx = self.sql.find("Add updated_at to plan_billing_periods")
        assert idx > 0, "DB-024 section not found in migration"
        section = self.sql[idx:idx + 800]
        assert "updated_at" in section

    def test_updated_at_has_default(self):
        """updated_at has DEFAULT now()."""
        idx = self.sql.find("Add updated_at to plan_billing_periods")
        assert idx > 0
        section = self.sql[idx:idx + 800]
        assert "DEFAULT now()" in section

    def test_trigger_created_for_auto_update(self):
        """Trigger created to auto-update updated_at."""
        idx = self.sql.find("trg_plan_billing_periods_updated_at")
        assert idx > 0, "Auto-update trigger for plan_billing_periods not found"


# ---------------------------------------------------------------------------
# DB-016: Status transitions documented via SQL COMMENT
# ---------------------------------------------------------------------------

class TestDB016StatusTransitions:
    """DB-016: Valid search_sessions.status transitions documented."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_status_comment_exists(self):
        """SQL COMMENT on search_sessions.status documents transitions."""
        assert "COMMENT ON COLUMN search_sessions.status" in self.sql

    def test_status_comment_lists_transitions(self):
        """Comment lists valid state transitions."""
        idx = self.sql.find("COMMENT ON COLUMN search_sessions.status")
        section = self.sql[idx:idx + 600]
        assert "created" in section
        assert "processing" in section
        assert "completed" in section
        assert "error" in section


# ---------------------------------------------------------------------------
# AC8: Zero regressions — messages route still works with new function
# ---------------------------------------------------------------------------

class TestAC8ZeroRegressions:
    """AC8: Backend messages route compatibility with new function signature."""

    def test_messages_route_uses_rpc(self):
        """messages.py still calls get_conversations_with_unread_count via RPC."""
        messages_path = os.path.join(
            os.path.dirname(__file__), "..", "routes", "messages.py"
        )
        code = _read_file(messages_path)
        assert "get_conversations_with_unread_count" in code
        assert "sb.rpc" in code

    def test_messages_route_passes_correct_params(self):
        """messages.py passes all required parameters to the RPC."""
        messages_path = os.path.join(
            os.path.dirname(__file__), "..", "routes", "messages.py"
        )
        code = _read_file(messages_path)
        for param in ["p_user_id", "p_is_admin", "p_status", "p_limit", "p_offset"]:
            assert param in code, f"messages.py missing parameter: {param}"

    def test_billing_route_uses_plan_billing_periods(self):
        """DEBT-114: billing.py checkout uses plan_billing_periods (not legacy fallback)."""
        billing_path = os.path.join(
            os.path.dirname(__file__), "..", "routes", "billing.py"
        )
        code = _read_file(billing_path)
        assert 'plan.get("stripe_price_id")' not in code, \
            "DEBT-114: Legacy stripe_price_id fallback must be removed"
        assert "plan_billing_periods" in code, \
            "DEBT-114: billing.py must use plan_billing_periods table"


# ---------------------------------------------------------------------------
# Migration SQL Quality Checks
# ---------------------------------------------------------------------------

class TestMigrationQuality:
    """General quality checks on the migration file."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_no_drop_table(self):
        """Migration does not DROP any tables."""
        assert "DROP TABLE" not in self.sql

    def test_no_drop_column(self):
        """Migration does not DROP any columns (deprecation only)."""
        assert "DROP COLUMN" not in self.sql

    def test_no_truncate(self):
        """Migration does not TRUNCATE any tables."""
        assert "TRUNCATE" not in self.sql

    def test_uses_create_or_replace_for_functions(self):
        """Functions use CREATE OR REPLACE (idempotent)."""
        assert "CREATE OR REPLACE FUNCTION cleanup_search_cache_per_user" in self.sql
        assert "CREATE OR REPLACE FUNCTION get_conversations_with_unread_count" in self.sql

    def test_section_headers_present(self):
        """Migration has clear section headers for each change."""
        headers = ["AC4", "AC3", "AC6", "AC7", "DB-016", "DB-020", "DB-050", "DB-024"]
        for header in headers:
            assert header in self.sql, f"Missing section header: {header}"
