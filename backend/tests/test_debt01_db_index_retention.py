"""
DEBT-01: Composite Index + Retention Policies — Tests

Acceptance Criteria covered:
  AC1: Composite index idx_pncp_raw_bids_dashboard_query criado
  AC2: 3 acoes de cron na migration (stripe add, alert_sent_items update, trial_email_log add)
  AC3: COMMENT content_hash corrigido MD5 -> SHA-256
  AC4: Zero downtime — IF NOT EXISTS + unschedule/schedule idempotente
"""

import os
import re
import pytest

MIGRATIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "supabase", "migrations"
)

MIGRATION_FILE = "20260408210000_debt01_index_retention.sql"


def _read_migration(filename: str) -> str:
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

class TestMigrationFileStructure:
    """Migration file exists and has correct header."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_migration_file_exists(self):
        path = os.path.join(MIGRATIONS_DIR, MIGRATION_FILE)
        assert os.path.exists(path), f"Migration file {MIGRATION_FILE} not found"

    def test_header_references_all_td_ids(self):
        """Migration header documents all TD IDs addressed."""
        header = self.sql[:800]
        for td_id in ["TD-019", "TD-025", "TD-026", "TD-027", "TD-022"]:
            assert td_id in header, f"{td_id} not referenced in migration header"

    def test_header_references_debt01(self):
        """Header mentions DEBT-01."""
        assert "DEBT-01" in self.sql[:200]


# ---------------------------------------------------------------------------
# AC1: Composite Index
# ---------------------------------------------------------------------------

class TestCompositeIndex:
    """AC1: idx_pncp_raw_bids_dashboard_query existe e tem a definicao correta."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_index_name_present(self):
        """Index has the canonical name from the story."""
        assert "idx_pncp_raw_bids_dashboard_query" in self.sql

    def test_index_on_correct_table(self):
        """Index targets pncp_raw_bids."""
        assert "pncp_raw_bids" in self.sql

    def test_index_covers_three_columns(self):
        """Composite on (uf, modalidade_id, data_publicacao DESC)."""
        # Normalize whitespace for flexible matching
        sql_flat = re.sub(r"\s+", " ", self.sql)
        assert "uf, modalidade_id, data_publicacao DESC" in sql_flat

    def test_index_has_partial_predicate(self):
        """Partial index only covers active rows (WHERE is_active = true)."""
        assert "is_active = true" in self.sql or "is_active=true" in self.sql

    def test_index_is_idempotent(self):
        """Uses IF NOT EXISTS for safe re-run."""
        assert "IF NOT EXISTS idx_pncp_raw_bids_dashboard_query" in self.sql

    def test_index_has_comment(self):
        """Index includes a COMMENT documenting purpose."""
        assert "COMMENT ON INDEX" in self.sql
        assert "TD-019" in self.sql

    def test_no_concurrently_in_migration(self):
        """CONCURRENTLY removed from migration SQL — incompativel com transacao.
        Producao recebe CREATE INDEX CONCURRENTLY via instrucao manual no story.
        """
        # Verify CONCURRENTLY is only in comments, not in executable SQL
        executable_lines = [
            line for line in self.sql.splitlines()
            if not line.strip().startswith("--") and "CONCURRENTLY" in line
        ]
        assert len(executable_lines) == 0, (
            "CONCURRENTLY found in executable SQL — will fail inside migration transaction. "
            "Apply manually in production. Offending lines: " + str(executable_lines)
        )


# ---------------------------------------------------------------------------
# AC2: Retention Cron Jobs
# ---------------------------------------------------------------------------

class TestRetentionCronJobs:
    """AC2: 3 acoes de cron presentes na migration."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_three_schedule_calls(self):
        """Exactly 3 cron.schedule() calls — stripe, alert_sent_items, trial_email_log."""
        schedules = re.findall(r"cron\.schedule\(", self.sql)
        assert len(schedules) == 3, (
            f"Expected 3 cron.schedule() calls, got {len(schedules)}"
        )

    def test_three_unschedule_calls(self):
        """Each schedule is preceded by an unschedule (idempotency)."""
        unschedules = re.findall(r"cron\.unschedule\(", self.sql)
        assert len(unschedules) == 3, (
            f"Expected 3 cron.unschedule() calls, got {len(unschedules)}"
        )

    @pytest.mark.parametrize("job_name,table,retention_clause", [
        (
            "cleanup-stripe-webhooks",
            "stripe_webhook_events",
            "90 days",
        ),
        (
            "cleanup-alert-sent-items",
            "alert_sent_items",
            "90 days",
        ),
        (
            "cleanup-trial-email-log",
            "trial_email_log",
            "1 year",
        ),
    ])
    def test_job_exists_with_correct_table_and_retention(
        self, job_name: str, table: str, retention_clause: str
    ):
        """TD-025/026/027: Each job targets the correct table and retention period."""
        assert job_name in self.sql, f"Job '{job_name}' not found in migration"
        # Verify table and retention appear near the job (within 400 chars)
        idx = self.sql.find(job_name)
        context = self.sql[max(0, idx - 50) : idx + 400]
        assert table in context, (
            f"Table '{table}' not found near job '{job_name}'"
        )
        assert retention_clause in context, (
            f"Retention '{retention_clause}' not found near job '{job_name}'"
        )

    def test_stripe_uses_processed_at_column(self):
        """TD-025: stripe_webhook_events cleanup filters on processed_at."""
        idx = self.sql.find("cleanup-stripe-webhooks")
        context = self.sql[idx : idx + 400]
        assert "processed_at" in context

    def test_alert_sent_items_uses_sent_at_column(self):
        """TD-026: alert_sent_items cleanup filters on sent_at."""
        idx = self.sql.find("cleanup-alert-sent-items")
        context = self.sql[idx : idx + 400]
        assert "sent_at" in context

    def test_trial_email_log_uses_sent_at_column(self):
        """TD-027: trial_email_log cleanup filters on sent_at."""
        idx = self.sql.find("cleanup-trial-email-log")
        context = self.sql[idx : idx + 400]
        assert "sent_at" in context

    def test_alert_sent_items_not_180_days(self):
        """TD-026: Confirma que o erro 180 days (DEBT-009) foi corrigido para 90 days."""
        # Find the alert_sent_items cron block specifically
        idx = self.sql.find("cleanup-alert-sent-items")
        context = self.sql[idx : idx + 400]
        assert "180 days" not in context, (
            "alert_sent_items still using 180 days — should be 90 days (TD-026 correction)"
        )

    def test_trial_email_log_is_monthly_schedule(self):
        """TD-027: trial_email_log e pequena — cron mensal suficiente."""
        # Monthly cron: minute hour day-of-month * *  e.g. '0 2 1 * *'
        monthly_pattern = re.search(r"'\d+ \d+ 1 \* \*'", self.sql)
        assert monthly_pattern is not None, (
            "Expected a monthly cron schedule (day-of-month=1) for trial_email_log"
        )

    def test_health_checks_not_rescheduled(self):
        """TD-NEW-001: health_checks ja agendado no DEBT-009 — sem acao aqui."""
        assert "cleanup-health-checks" not in self.sql, (
            "cleanup-health-checks should not be rescheduled in DEBT-01 (already done in DEBT-009)"
        )


# ---------------------------------------------------------------------------
# AC3: content_hash COMMENT corrigido
# ---------------------------------------------------------------------------

class TestContentHashComment:
    """AC3: COMMENT da coluna content_hash menciona SHA-256, nao MD5."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_comment_on_content_hash_present(self):
        """COMMENT ON COLUMN statement exists for content_hash."""
        assert "COMMENT ON COLUMN" in self.sql
        assert "content_hash" in self.sql

    def test_comment_mentions_sha256(self):
        """Comment explicitly says SHA-256."""
        # Find the COMMENT statement
        idx = self.sql.find("content_hash")
        context = self.sql[max(0, idx - 50) : idx + 200]
        assert "SHA-256" in context, (
            "content_hash COMMENT does not mention SHA-256"
        )

    def test_comment_does_not_say_md5(self):
        """TD-022: MD5 reference removed from the actual COMMENT ON COLUMN statement."""
        # Find the executable COMMENT ON COLUMN statement (not the header comment line)
        idx = self.sql.find("COMMENT ON COLUMN")
        assert idx >= 0, "COMMENT ON COLUMN not found"
        context = self.sql[idx : idx + 300]
        assert "MD5" not in context, (
            "content_hash COMMENT still mentions MD5 — should be SHA-256"
        )

    def test_comment_mentions_upsert_function(self):
        """Comment explains purpose: used by upsert_pncp_raw_bids."""
        idx = self.sql.find("COMMENT ON COLUMN")
        assert idx >= 0, "COMMENT ON COLUMN not found"
        context = self.sql[idx : idx + 300]
        assert "upsert_pncp_raw_bids" in context


# ---------------------------------------------------------------------------
# AC4: Zero Downtime — Idempotency checks
# ---------------------------------------------------------------------------

class TestZeroDowntime:
    """AC4: Migration e totalmente idempotente e nao causa downtime."""

    @pytest.fixture(autouse=True)
    def load_sql(self):
        self.sql = _read_migration(MIGRATION_FILE)

    def test_index_uses_if_not_exists(self):
        """CREATE INDEX uses IF NOT EXISTS — safe to re-run."""
        assert "CREATE INDEX IF NOT EXISTS" in self.sql

    def test_cron_unschedule_guarded_by_exists(self):
        """cron.unschedule calls are guarded by WHERE EXISTS to avoid errors."""
        unschedule_calls = re.findall(
            r"cron\.unschedule\(.*?\)[^;]*;",
            self.sql,
            re.DOTALL,
        )
        assert len(unschedule_calls) == 3, (
            f"Expected 3 guarded unschedule calls, got {len(unschedule_calls)}"
        )
        for call in unschedule_calls:
            assert "WHERE EXISTS" in call or "where exists" in call.lower(), (
                f"cron.unschedule not guarded by WHERE EXISTS: {call[:100]}"
            )

    def test_comment_fix_uses_replace_semantics(self):
        """COMMENT ON COLUMN is a replace operation — always idempotent."""
        # COMMENT ON COLUMN is always a SET — no guard needed, idempotent by nature
        assert "COMMENT ON COLUMN public.pncp_raw_bids.content_hash" in self.sql

    def test_no_alter_table_lock_risk(self):
        """No ALTER TABLE ... SET NOT NULL or ADD CONSTRAINT that would take locks."""
        dangerous = re.findall(
            r"ALTER TABLE.*?(SET NOT NULL|ADD CONSTRAINT|ADD COLUMN.*NOT NULL)",
            self.sql,
            re.DOTALL | re.IGNORECASE,
        )
        assert len(dangerous) == 0, (
            f"Found potentially lock-taking ALTER TABLE: {dangerous}"
        )


# ---------------------------------------------------------------------------
# Cross-check: SHA-256 in transformer matches comment
# ---------------------------------------------------------------------------

class TestTransformerHashAlgorithm:
    """Validates that transformer.py actually uses SHA-256 (not MD5)."""

    def test_transformer_uses_sha256(self):
        """ingestion/transformer.py uses hashlib.sha256 for content_hash."""
        transformer_path = os.path.join(
            os.path.dirname(__file__), "..", "ingestion", "transformer.py"
        )
        assert os.path.exists(transformer_path), "transformer.py not found"
        with open(transformer_path, encoding="utf-8") as f:
            source = f.read()
        assert "sha256" in source, (
            "hashlib.sha256 not found in transformer.py — hash algorithm mismatch"
        )
        assert "md5" not in source.lower(), (
            "MD5 reference found in transformer.py — expected SHA-256 only"
        )
