"""STORY-419: Regression tests for the NUMERIC(14,2) overflow on
search_sessions.valor_total.

The production incident (Sentry 7369847734, 2026-04-10) happened because:
  1. The DB column was NUMERIC(14,2) — ceiling R$ 999.999.999.999,99.
  2. BuscaRequest had no server-side cap on ``valor_maximo``.
  3. quota.session_tracker.update_session_status passed the pipeline sum
     straight to PostgREST, which responded with SQLSTATE 22003.

The fix has three layers:
  * DB column widened to NUMERIC(18,2) via migration
    20260410131000_story419_widen_valor_total.sql.
  * BuscaRequest.valor_maximo / valor_minimo get a Pydantic validator
    that caps values at 1e15 (one decade of headroom vs. 1e16).
  * update_session_status caps the persisted valor_total defensively
    so a corrupted upstream sum does not reintroduce 22003.

These tests cover layers 2 and 3 — the migration is covered statically
by a separate test that inspects the SQL file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.search import BuscaRequest


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260410131000_story419_widen_valor_total.sql"
)


# ---------------------------------------------------------------------------
# Layer 2: Pydantic validator
# ---------------------------------------------------------------------------


def _valid_base_payload(**overrides):
    """Base payload for BuscaRequest — kept minimal so validators fire."""
    base = {
        "ufs": ["SP"],
        "data_inicial": "2026-04-01",
        "data_final": "2026-04-10",
        "modo_busca": "publicacao",
    }
    base.update(overrides)
    return base


def test_valor_maximo_at_ceiling_is_allowed() -> None:
    """Exactly 1e15 is the published ceiling, so it must round-trip."""
    req = BuscaRequest(**_valid_base_payload(valor_maximo=1e15))
    assert req.valor_maximo == 1e15


def test_valor_maximo_above_ceiling_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        BuscaRequest(**_valid_base_payload(valor_maximo=1e15 + 1))
    assert "1 quatrilhão" in str(exc.value) or "STORY-419" in str(exc.value)


def test_valor_minimo_above_ceiling_is_rejected() -> None:
    """Cap applies to both ends — the validator guards valor_minimo too."""
    with pytest.raises(ValidationError):
        BuscaRequest(**_valid_base_payload(valor_minimo=2e15, valor_maximo=3e15))


def test_valor_maximo_none_still_allowed() -> None:
    """None means "no upper limit" — the validator must be a pass-through."""
    req = BuscaRequest(**_valid_base_payload(valor_maximo=None))
    assert req.valor_maximo is None


def test_negative_valor_maximo_still_rejected_by_ge_zero() -> None:
    """Existing ge=0 contract must not regress when we add the new validator."""
    with pytest.raises(ValidationError):
        BuscaRequest(**_valid_base_payload(valor_maximo=-1.0))


# ---------------------------------------------------------------------------
# Layer 3: session tracker defensive cap
# ---------------------------------------------------------------------------


def test_session_tracker_source_caps_valor_total() -> None:
    """STORY-419: static guard — the session tracker source MUST contain
    the cap logic so a future refactor cannot silently drop it.

    We inspect the file instead of exercising the full update path
    because ``update_session_status`` imports its Supabase helpers
    lazily inside the function body (to keep the blast radius of import
    errors small), which defeats ``monkeypatch.setattr``. A static
    check is good enough: the cap is arithmetic on a local variable.
    """

    source = (
        REPO_ROOT / "backend" / "quota" / "session_tracker.py"
    ).read_text(encoding="utf-8")

    # The cap constant must live inside session_tracker (defensive
    # alongside the request-time validator in schemas/search.py).
    assert "_VALOR_TOTAL_CEILING" in source
    assert "1e15" in source
    # And the cap must be applied before assigning into update_data.
    assert "numeric_valor = _VALOR_TOTAL_CEILING" in source, (
        "STORY-419: session_tracker must overwrite valor_total with "
        "the ceiling when the upstream value exceeds it."
    )


# ---------------------------------------------------------------------------
# Layer 1: migration sanity (static check — no DB required)
# ---------------------------------------------------------------------------


def test_story419_migration_widens_to_numeric_18_2() -> None:
    assert MIGRATION.exists(), f"STORY-419 migration missing: {MIGRATION}"
    body = MIGRATION.read_text(encoding="utf-8")
    assert "search_sessions" in body
    assert "valor_total" in body
    assert "NUMERIC(18, 2)" in body or "NUMERIC(18,2)" in body
