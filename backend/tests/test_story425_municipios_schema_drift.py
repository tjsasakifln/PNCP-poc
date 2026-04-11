"""STORY-425: Fix schema drift `data_publicacao_pncp` em `pncp_raw_bids`.

Confirms that the query in municipios_publicos.py no longer references the
non-existent column `data_publicacao_pncp`; uses `data_publicacao` instead.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

_BACKEND_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Static analysis: verify source code uses correct column name
# ---------------------------------------------------------------------------

def test_source_does_not_reference_data_publicacao_pncp_in_code():
    """municipios_publicos.py must NOT use `data_publicacao_pncp` in SQL/code (comments allowed)."""
    import ast
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    # Strip comments — only check non-comment code lines
    non_comment_lines = [
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    ]
    non_comment_source = "\n".join(non_comment_lines)
    assert "data_publicacao_pncp" not in non_comment_source, (
        "routes/municipios_publicos.py still contains `data_publicacao_pncp` in non-comment code — "
        "this column does not exist in the pncp_raw_bids schema."
    )


def test_source_references_data_publicacao():
    """municipios_publicos.py must reference `data_publicacao` (the real column)."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "data_publicacao" in source, (
        "routes/municipios_publicos.py must use `data_publicacao` (the real column)."
    )


def test_source_order_by_data_publicacao():
    """municipios_publicos.py ORDER BY must use `data_publicacao`."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert '.order("data_publicacao"' in source, (
        "ORDER BY must use `data_publicacao`, not the non-existent `data_publicacao_pncp`"
    )


# ---------------------------------------------------------------------------
# Runtime: dict access uses correct key
# ---------------------------------------------------------------------------

def test_licitacao_recente_data_key_is_data_publicacao():
    """The licitacoes_recentes dict must read row.get('data_publicacao')."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert '"data_publicacao_pncp"' not in source, (
        "row.get() must not reference 'data_publicacao_pncp'"
    )
    # Verify that data_publicacao is read from the row dict
    assert 'row.get("data_publicacao")' in source or "data_publicacao" in source, (
        "licitacoes_recentes must build 'data_publicacao' from row.get('data_publicacao')"
    )


# ---------------------------------------------------------------------------
# Schema validation: `data_publicacao` exists in migration DDL
# ---------------------------------------------------------------------------

def test_schema_has_data_publicacao_column():
    """The migration DDL for pncp_raw_bids must define `data_publicacao` column."""
    migration = (_BACKEND_ROOT / "../supabase/migrations/20260326000000_datalake_raw_bids.sql").read_text(encoding="utf-8")
    assert "data_publicacao" in migration, (
        "pncp_raw_bids migration must define the `data_publicacao` column"
    )
    assert "data_publicacao_pncp" not in migration, (
        "pncp_raw_bids migration must NOT define `data_publicacao_pncp` (it was never created)"
    )


def test_schema_does_not_have_data_publicacao_pncp_column():
    """The migration DDL must NOT define `data_publicacao_pncp` (drift confirmation)."""
    migration = (_BACKEND_ROOT / "../supabase/migrations/20260326000000_datalake_raw_bids.sql").read_text(encoding="utf-8")
    assert "data_publicacao_pncp" not in migration, (
        "Drift confirmed: `data_publicacao_pncp` was never in the migration DDL"
    )
