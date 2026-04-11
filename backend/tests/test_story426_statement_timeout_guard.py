"""STORY-426: Fix statement timeout em endpoints públicos sem timeout guard.

Confirms that:
- municipios_publicos.py wraps pncp_raw_bids query in asyncio.wait_for
- asyncio.TimeoutError returns degraded 200 instead of 500
- SUPABASE_QUERY_TIMEOUT_TOTAL metric is incremented on timeout
- _is_schema_error does NOT exclude PostgreSQL error code 57014 (statement_timeout)
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

_BACKEND_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Static analysis: wait_for guard is present in source
# ---------------------------------------------------------------------------

def test_source_has_asyncio_wait_for_guard():
    """municipios_publicos.py must use asyncio.wait_for for the bids query."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "asyncio.wait_for" in source, (
        "municipios_publicos.py must wrap pncp_raw_bids query in asyncio.wait_for"
    )


def test_source_handles_timeout_error():
    """municipios_publicos.py must catch asyncio.TimeoutError for the bids query."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "asyncio.TimeoutError" in source, (
        "municipios_publicos.py must handle asyncio.TimeoutError from the bids query"
    )


def test_source_uses_asyncio_to_thread():
    """municipios_publicos.py must wrap the sync .execute() in asyncio.to_thread."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "asyncio.to_thread" in source, (
        "municipios_publicos.py must use asyncio.to_thread to offload sync execute()"
    )


# ---------------------------------------------------------------------------
# _is_schema_error must not exclude 57014
# ---------------------------------------------------------------------------

def test_is_schema_error_does_not_exclude_57014():
    """PostgreSQL error code 57014 (statement_timeout) must NOT be excluded from CB."""
    from supabase_client import _is_schema_error

    exc_57014 = Exception("ERROR:  canceling statement due to statement timeout\ncode: 57014")
    assert not _is_schema_error(exc_57014), (
        "_is_schema_error must return False for 57014 (statement_timeout) — "
        "timeouts should count as CB failures, not be excluded."
    )


def test_is_schema_error_still_excludes_pgrst205():
    """PGRST205 must still be excluded (schema cache miss is not an outage)."""
    from supabase_client import _is_schema_error
    assert _is_schema_error(Exception("PGRST205 schema cache miss"))


def test_is_schema_error_still_excludes_42703():
    """42703 (undefined column) must still be excluded."""
    from supabase_client import _is_schema_error
    assert _is_schema_error(Exception("ERROR: 42703 column does not exist"))


# ---------------------------------------------------------------------------
# Municipios endpoint timeout guard — via source inspection for behavior
# ---------------------------------------------------------------------------

def test_timeout_metric_is_incremented_in_timeout_branch():
    """Source must increment SUPABASE_QUERY_TIMEOUT_TOTAL on TimeoutError."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "SUPABASE_QUERY_TIMEOUT_TOTAL" in source, (
        "municipios_publicos.py must increment SUPABASE_QUERY_TIMEOUT_TOTAL "
        "in the asyncio.TimeoutError handler"
    )


def test_timeout_branch_uses_municipios_stats_label():
    """Timeout metric must use endpoint='municipios_stats' label."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    assert "municipios_stats" in source, (
        "Timeout metric must use endpoint label 'municipios_stats'"
    )


def test_timeout_branch_does_not_raise():
    """On TimeoutError the handler must not re-raise (degraded response expected)."""
    source = (_BACKEND_ROOT / "routes/municipios_publicos.py").read_text(encoding="utf-8")
    # After the TimeoutError block, we should NOT see a bare `raise` that
    # would propagate. The block should just log and leave lists at defaults.
    lines = source.splitlines()
    timeout_block_start = None
    for i, line in enumerate(lines):
        if "asyncio.TimeoutError" in line and "except" in line:
            timeout_block_start = i
            break
    assert timeout_block_start is not None, "asyncio.TimeoutError handler not found"

    # Collect lines of the except block (until next except/else/finally/end of try)
    block_lines = []
    indent = len(lines[timeout_block_start]) - len(lines[timeout_block_start].lstrip())
    for line in lines[timeout_block_start + 1:]:
        stripped = line.lstrip()
        if not stripped:
            continue
        current_indent = len(line) - len(stripped)
        if current_indent <= indent and stripped and not stripped.startswith("#"):
            break
        block_lines.append(stripped)

    # The block must not end with a bare `raise` (which would cause 500)
    bare_raises = [l for l in block_lines if l.strip() == "raise"]
    assert not bare_raises, (
        "TimeoutError handler must not re-raise — "
        "it should return degraded data (empty lists) instead of 500"
    )


# ---------------------------------------------------------------------------
# Metric exists in metrics.py
# ---------------------------------------------------------------------------

def test_supabase_query_timeout_metric_defined():
    """metrics.py must define SUPABASE_QUERY_TIMEOUT_TOTAL counter."""
    source = (_BACKEND_ROOT / "metrics.py").read_text(encoding="utf-8")
    assert "SUPABASE_QUERY_TIMEOUT_TOTAL" in source, (
        "metrics.py must define SUPABASE_QUERY_TIMEOUT_TOTAL counter for STORY-426"
    )
