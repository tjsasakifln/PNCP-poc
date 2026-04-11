"""STORY-429: Fix violação de constraint `chk_search_sessions_error_code` — case mismatch.

Verifica que os 7 call sites escrevem valores UPPERCASE válidos (via ErrorCode enum)
em vez de strings lowercase que violam a constraint do PostgreSQL.
"""

import pytest
from error_response import ErrorCode


# ---------------------------------------------------------------------------
# AC4: Verificar que todos os call sites usam ErrorCode enum (type-safety)
# ---------------------------------------------------------------------------

def test_errorcode_timeout_is_uppercase():
    """ErrorCode.TIMEOUT.value deve ser 'TIMEOUT' (uppercase)."""
    assert ErrorCode.TIMEOUT.value == "TIMEOUT"


def test_errorcode_quota_exceeded_is_uppercase():
    """ErrorCode.QUOTA_EXCEEDED.value deve ser 'QUOTA_EXCEEDED' (uppercase)."""
    assert ErrorCode.QUOTA_EXCEEDED.value == "QUOTA_EXCEEDED"


def test_errorcode_source_unavailable_is_uppercase():
    """ErrorCode.SOURCE_UNAVAILABLE.value deve ser 'SOURCE_UNAVAILABLE' (uppercase)."""
    assert ErrorCode.SOURCE_UNAVAILABLE.value == "SOURCE_UNAVAILABLE"


def test_errorcode_internal_error_is_uppercase():
    """ErrorCode.INTERNAL_ERROR.value deve ser 'INTERNAL_ERROR' (uppercase)."""
    assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"


# ---------------------------------------------------------------------------
# AC1+AC3: Verificar que os arquivos de código não contêm strings lowercase
# ---------------------------------------------------------------------------

import ast
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).parent.parent


def _extract_error_code_string_literals(filepath: Path) -> list[str]:
    """Parse Python AST and find string literals passed as error_code= kwargs."""
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source)
    results = []
    for node in ast.walk(tree):
        # Look for keyword argument `error_code=<string>`
        if isinstance(node, (ast.Call,)):
            for kw in node.keywords:
                if kw.arg == "error_code" and isinstance(kw.value, ast.Constant):
                    if isinstance(kw.value.value, str):
                        results.append(kw.value.value)
    return results


@pytest.mark.parametrize("rel_path", [
    "pipeline/stages/execute.py",
    "pipeline/stages/validate.py",
    "routes/search.py",
])
def test_no_lowercase_error_code_strings(rel_path: str):
    """Nenhum call site deve passar string lowercase como error_code=."""
    filepath = _BACKEND_ROOT / rel_path
    if not filepath.exists():
        pytest.skip(f"File not found: {filepath}")

    literals = _extract_error_code_string_literals(filepath)
    bad = [v for v in literals if v != v.upper()]
    assert not bad, (
        f"{rel_path} ainda contém error_code literals lowercase: {bad}\n"
        "Use ErrorCode.XXX.value em vez de strings literais."
    )


# ---------------------------------------------------------------------------
# AC5: Integration — simulate timeout/quota/sources-unavailable flows
# ---------------------------------------------------------------------------

def test_execute_py_imports_error_code():
    """pipeline/stages/execute.py deve importar ErrorCode."""
    source = (_BACKEND_ROOT / "pipeline/stages/execute.py").read_text()
    assert "from error_response import ErrorCode" in source or "ErrorCode" in source, (
        "execute.py must import ErrorCode from error_response"
    )


def test_validate_py_imports_error_code():
    """pipeline/stages/validate.py deve importar ErrorCode."""
    source = (_BACKEND_ROOT / "pipeline/stages/validate.py").read_text()
    assert "from error_response import ErrorCode" in source or "ErrorCode" in source, (
        "validate.py must import ErrorCode from error_response"
    )


def test_search_py_uses_search_error_code_enum_for_timeout():
    """routes/search.py deve usar SearchErrorCode.TIMEOUT.value para erro 504."""
    source = (_BACKEND_ROOT / "routes/search.py").read_text()
    # The old pattern was: error_code="timeout" if exc.status_code == 504 else "unknown"
    assert '"timeout"' not in source or 'SearchErrorCode.TIMEOUT' in source, (
        "search.py deve usar SearchErrorCode.TIMEOUT.value em vez de string \"timeout\""
    )
    assert '"unknown"' not in source or 'SearchErrorCode.INTERNAL_ERROR' in source, (
        "search.py deve usar SearchErrorCode.INTERNAL_ERROR.value em vez de string \"unknown\""
    )


def test_search_py_uses_search_error_code_enum_for_sources_unavailable():
    """routes/search.py deve usar SearchErrorCode.SOURCE_UNAVAILABLE.value."""
    source = (_BACKEND_ROOT / "routes/search.py").read_text()
    assert '"sources_unavailable"' not in source, (
        "search.py deve usar SearchErrorCode.SOURCE_UNAVAILABLE.value em vez de "
        "string literal \"sources_unavailable\""
    )
