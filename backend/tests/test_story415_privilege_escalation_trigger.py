"""STORY-415: Regression guard for the prevent_privilege_escalation trigger.

We cannot easily spin up PostgreSQL in unit tests, so this module validates
the SQL migration file statically. That is sufficient to prevent the exact
regression that hit production on 2026-04-10 (Sentry 7388075442,
``record "new" has no field "is_master"``) because the root cause was a
static SQL reference to a column that never existed — not a runtime bug.

Invariants guarded:

1. The latest trigger migration MUST NOT reference ``NEW.is_master`` or
   ``OLD.is_master``. Any re-introduction should be blocked in review.

2. The new migration (20260410130000_story415_fix_is_master_trigger.sql)
   MUST still guard ``is_admin`` and ``plan_type`` — those are the real
   protected columns.

3. The older migration that introduced the bug
   (20260404000000_security_hardening_rpc_rls.sql) is allowed to keep its
   original body because the newer ``CREATE OR REPLACE FUNCTION`` overrides
   it at deploy time; we only check ordering.

We also verify that the backend derives ``is_master`` from ``plan_type``
in authorization.py, which is the assumption that justifies removing the
column reference. If someone turns it into a real column in the future,
this test will surface the divergence.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"

STORY_415_MIGRATION = MIGRATIONS_DIR / "20260410130000_story415_fix_is_master_trigger.sql"
ORIGINAL_MIGRATION = MIGRATIONS_DIR / "20260404000000_security_hardening_rpc_rls.sql"


@pytest.fixture(scope="module")
def story415_sql() -> str:
    assert STORY_415_MIGRATION.exists(), (
        f"STORY-415 migration missing: {STORY_415_MIGRATION}"
    )
    return STORY_415_MIGRATION.read_text(encoding="utf-8")


def test_story415_migration_drops_is_master_reference(story415_sql: str) -> None:
    """The replacement function body must NOT reference is_master at all."""
    # We allow "is_master" to appear in SQL comments that *explain* the fix,
    # but not in code. Strip comment lines before checking.
    code_lines = [
        line for line in story415_sql.splitlines() if not line.strip().startswith("--")
    ]
    code_body = "\n".join(code_lines)

    assert "NEW.is_master" not in code_body, (
        "STORY-415 migration must not reference NEW.is_master — "
        "that column does not exist on profiles."
    )
    assert "OLD.is_master" not in code_body, (
        "STORY-415 migration must not reference OLD.is_master — "
        "that column does not exist on profiles."
    )


def test_story415_migration_still_guards_is_admin_and_plan_type(story415_sql: str) -> None:
    """The real privileged columns must stay protected by the trigger."""
    assert "NEW.is_admin IS DISTINCT FROM OLD.is_admin" in story415_sql
    assert "NEW.plan_type IS DISTINCT FROM OLD.plan_type" in story415_sql


def test_story415_migration_creates_or_replaces_function(story415_sql: str) -> None:
    """Replacement must be idempotent — CREATE OR REPLACE, not CREATE."""
    assert re.search(
        r"CREATE OR REPLACE FUNCTION\s+public\.prevent_privilege_escalation",
        story415_sql,
    ), "Function must be created with CREATE OR REPLACE"


def test_story415_migration_runs_after_original() -> None:
    """STORY-415 migration filename must sort after the bug-introducing one."""
    assert STORY_415_MIGRATION.name > ORIGINAL_MIGRATION.name, (
        "STORY-415 migration must sort after 20260404000000_security_hardening... "
        "otherwise supabase db push will apply the buggy body last."
    )


def test_is_master_is_still_derived_in_backend() -> None:
    """Sanity check: the backend derivation we rely on must still exist.

    If this test ever fails, it means someone introduced a real is_master
    column — at which point the trigger needs a NEW.is_master check again
    and this whole migration must be revisited.
    """
    authorization_py = REPO_ROOT / "backend" / "authorization.py"
    source = authorization_py.read_text(encoding="utf-8")
    # Any of these shapes count as "is_master is derived, not a column".
    patterns = [
        r"is_master\s*=\s*.*is_admin",
        r"is_master\s*=\s*.*plan_type",
        r'plan_type\s*==\s*["\']master["\']',
    ]
    assert any(re.search(p, source) for p in patterns), (
        "authorization.py no longer derives is_master from is_admin/plan_type. "
        "STORY-415 assumes the derivation — revisit the trigger migration."
    )
