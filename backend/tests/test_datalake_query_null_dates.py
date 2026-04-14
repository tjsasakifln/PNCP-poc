"""STORY-2.12 (TD-DB-015) AC2 + AC3:
validate the date-handling migrations for pncp_raw_bids.

These tests are regex-based (no live DB) so they run in CI as part of the
backend suite.  Database-side verification is captured in the comments at
the bottom of each migration file.
"""
from pathlib import Path
import re

import pytest


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"

BACKFILL_MIG = MIGRATIONS_DIR / "20260414132000_backfill_pncp_raw_bids_dates.sql"
COALESCE_MIG = MIGRATIONS_DIR / "20260414133000_search_datalake_coalesce_dates.sql"


@pytest.fixture(scope="module")
def backfill_sql() -> str:
    assert BACKFILL_MIG.exists(), f"missing migration: {BACKFILL_MIG}"
    return BACKFILL_MIG.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def coalesce_sql() -> str:
    assert COALESCE_MIG.exists(), f"missing migration: {COALESCE_MIG}"
    return COALESCE_MIG.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC2 — backfill migration
# ---------------------------------------------------------------------------


class TestBackfillMigration:
    def test_backfills_data_publicacao_from_ingested_at(self, backfill_sql: str):
        assert re.search(
            r"UPDATE\s+public\.pncp_raw_bids\s+SET\s+data_publicacao\s*=\s*\(?\s*ingested_at\s*-\s*INTERVAL\s*'1\s+day'\s*\)?",
            backfill_sql,
            re.IGNORECASE,
        )

    def test_only_updates_null_rows(self, backfill_sql: str):
        """Idempotency: every UPDATE is guarded by WHERE ... IS NULL."""
        updates = re.findall(
            r"UPDATE\s+public\.pncp_raw_bids.*?;",
            backfill_sql,
            re.DOTALL | re.IGNORECASE,
        )
        assert updates, "expected at least one UPDATE in migration"
        for u in updates:
            assert re.search(r"IS\s+NULL", u, re.IGNORECASE), (
                f"UPDATE missing IS NULL guard: {u[:120]}"
            )

    def test_data_abertura_backfilled_from_data_publicacao(self, backfill_sql: str):
        assert re.search(
            r"UPDATE\s+public\.pncp_raw_bids\s+SET\s+data_abertura\s*=\s*data_publicacao\s+WHERE\s+data_abertura\s+IS\s+NULL",
            backfill_sql,
            re.IGNORECASE | re.DOTALL,
        )

    def test_does_not_backfill_data_encerramento(self, backfill_sql: str):
        """data_encerramento must remain NULL-tolerant — asserted in header comment."""
        assert not re.search(
            r"UPDATE\s+public\.pncp_raw_bids\s+SET\s+data_encerramento\s*=",
            backfill_sql,
            re.IGNORECASE,
        ), "data_encerramento must not be backfilled"

    def test_wrapped_in_transaction(self, backfill_sql: str):
        assert "BEGIN;" in backfill_sql
        assert "COMMIT;" in backfill_sql

    def test_has_statement_timeout_guard(self, backfill_sql: str):
        """Large backfills need statement_timeout — otherwise we risk Railway 120s kill."""
        assert re.search(r"SET LOCAL statement_timeout", backfill_sql, re.IGNORECASE)


# ---------------------------------------------------------------------------
# AC3 — search_datalake COALESCE migration
# ---------------------------------------------------------------------------


class TestSearchDatalakeCoalesce:
    def test_coalesces_data_publicacao_to_ingested_at(self, coalesce_sql: str):
        """Date filter falls back to ingested_at when data_publicacao IS NULL."""
        assert re.search(
            r"COALESCE\(\s*b\.data_publicacao\s*,\s*b\.ingested_at\s*\)",
            coalesce_sql,
            re.IGNORECASE,
        )

    def test_coalesces_data_encerramento_for_abertas_mode(self, coalesce_sql: str):
        """'abertas' filter falls back to ingested_at + 30 days when data_encerramento IS NULL."""
        assert re.search(
            r"COALESCE\(\s*b\.data_encerramento\s*,\s*b\.ingested_at\s*\+\s*INTERVAL\s*'30\s+days'\s*\)",
            coalesce_sql,
            re.IGNORECASE,
        )

    def test_preserves_signature(self, coalesce_sql: str):
        """Same 12-param signature as 20260413000001_search_datalake_hybrid.sql."""
        assert "p_ufs            TEXT[]" in coalesce_sql
        assert "p_tsquery        TEXT" in coalesce_sql
        assert "p_websearch_text TEXT" in coalesce_sql
        assert "p_modalidades    INTEGER[]" in coalesce_sql
        assert "p_embedding      VECTOR(256)" in coalesce_sql
        assert "p_modo           TEXT" in coalesce_sql

    def test_preserves_return_shape(self, coalesce_sql: str):
        """Same RETURNS TABLE shape (16 cols including ts_rank)."""
        for col in (
            "pncp_id",
            "uf",
            "objeto_compra",
            "valor_total_estimado",
            "modalidade_id",
            "situacao_compra",
            "data_publicacao",
            "data_abertura",
            "data_encerramento",
            "link_pncp",
            "esfera_id",
            "ts_rank",
        ):
            assert col in coalesce_sql, f"return column {col} missing"

    def test_preserves_hybrid_scoring(self, coalesce_sql: str):
        """FTS + cosine scoring weights (0.4 / 0.6) must still be present."""
        assert re.search(
            r"0\.4\s*\*\s*ts_rank\(.*?\)\s*\+\s*0\.6\s*\*\s*\(1\.0\s*-\s*\(b\.embedding\s*<=>\s*p_embedding\)\)",
            coalesce_sql,
            re.IGNORECASE | re.DOTALL,
        )

    def test_preserves_security_definer_and_grants(self, coalesce_sql: str):
        assert re.search(r"SECURITY DEFINER", coalesce_sql, re.IGNORECASE)
        assert re.search(r"GRANT EXECUTE.*authenticated", coalesce_sql, re.IGNORECASE)
        assert re.search(r"GRANT EXECUTE.*service_role", coalesce_sql, re.IGNORECASE)

    def test_preserves_p_modo_validation(self, coalesce_sql: str):
        assert re.search(
            r"p_modo NOT IN \('publicacao', 'abertas'\)",
            coalesce_sql,
            re.IGNORECASE,
        )

    def test_preserves_tsquery_error_fallback(self, coalesce_sql: str):
        """EXCEPTION WHEN OTHERS must still fall back to plainto_tsquery."""
        # At least two EXCEPTION blocks (sector tsquery + websearch)
        assert (
            coalesce_sql.count("plainto_tsquery('portuguese'")
            >= 2
        )

    def test_comment_references_story(self, coalesce_sql: str):
        assert "STORY-2.12" in coalesce_sql

    def test_uses_create_or_replace_not_drop(self, coalesce_sql: str):
        """Same signature — use CREATE OR REPLACE to avoid transiently dropping the function."""
        assert "CREATE OR REPLACE FUNCTION" in coalesce_sql

    def test_order_by_preserves_nulls_last(self, coalesce_sql: str):
        """Since data_publicacao can theoretically be NULL, ORDER BY must handle it."""
        assert re.search(
            r"ORDER BY.*?data_publicacao DESC\s+NULLS\s+LAST",
            coalesce_sql,
            re.IGNORECASE | re.DOTALL,
        )
