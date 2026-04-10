"""STORY-414: Regression tests for the schema contract gate.

We exercise three layers:

1. ``validate_schema_contract`` — behavioural parity with CRIT-004 (the
   pre-existing passive check). We pin it via a tiny stub client.
2. ``enforce_schema_contract`` — the new strict-mode wrapper. In passive
   mode it logs CRITICAL and returns; in strict mode it raises
   ``SchemaContractViolation`` and updates the cache consumed by the
   admin endpoint.
3. ``get_last_status`` — the cache itself must be JSON-safe so the
   /admin/schema-contract-status endpoint can serialise it directly.

We deliberately do NOT depend on Supabase or FastAPI here — those are
slow to boot and not needed to validate the gate logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from schemas import contract as contract_module
from schemas.contract import (
    SchemaContractViolation,
    enforce_schema_contract,
    get_last_status,
    validate_schema_contract,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fake_db(columns_by_table: dict[str, list[str]]):
    """Build a stub Supabase client whose RPC returns the given columns.

    The contract module calls ``db.rpc("get_table_columns_simple", ...)``
    and expects ``result.data`` to be a list of ``{"column_name": ...}``.
    """
    db = MagicMock()

    def _rpc(fn_name, params):  # noqa: ARG001
        table = params.get("p_table_name")
        cols = columns_by_table.get(table, [])
        result = MagicMock()
        result.data = [{"column_name": c} for c in cols]
        chain = MagicMock()
        chain.execute.return_value = result
        return chain

    db.rpc.side_effect = _rpc
    return db


@pytest.fixture(autouse=True)
def _reset_status_cache() -> None:
    """Each test starts with a clean status cache."""
    contract_module._last_status.update(
        {
            "passed": None,
            "missing": [],
            "checked_at": 0.0,
            "strict_mode": False,
        }
    )


# ---------------------------------------------------------------------------
# Layer 1: validate_schema_contract (unchanged passive behaviour)
# ---------------------------------------------------------------------------


def test_validate_passes_when_all_columns_present() -> None:
    db = _make_fake_db(
        {
            "search_sessions": [
                "id", "user_id", "search_id", "status", "started_at",
                "completed_at", "created_at",
            ],
            "search_results_cache": ["id", "params_hash", "results", "created_at"],
            "profiles": ["id", "plan_type", "email"],
        }
    )
    passed, missing = validate_schema_contract(db)
    assert passed is True
    assert missing == []


def test_validate_reports_missing_columns() -> None:
    db = _make_fake_db(
        {
            "search_sessions": ["id", "user_id"],  # deliberately short
            "search_results_cache": ["id", "params_hash", "results", "created_at"],
            "profiles": ["id", "plan_type", "email"],
        }
    )
    passed, missing = validate_schema_contract(db)
    assert passed is False
    assert "search_sessions.search_id" in missing
    assert "search_sessions.status" in missing


# ---------------------------------------------------------------------------
# Layer 2: enforce_schema_contract strict/passive modes
# ---------------------------------------------------------------------------


def test_enforce_strict_raises_on_violation() -> None:
    db = _make_fake_db(
        {
            "search_sessions": ["id"],
            "search_results_cache": [],
            "profiles": [],
        }
    )
    with pytest.raises(SchemaContractViolation) as exc_info:
        enforce_schema_contract(db, strict=True)
    assert exc_info.value.missing  # must populate the payload
    status = get_last_status()
    assert status["passed"] is False
    assert status["strict_mode"] is True
    assert status["missing"]


def test_enforce_passive_mode_does_not_raise() -> None:
    """Default rollout (P1, production) must not abort startup on drift."""
    db = _make_fake_db(
        {
            "search_sessions": [],
            "search_results_cache": [],
            "profiles": [],
        }
    )
    passed, missing = enforce_schema_contract(db, strict=False)
    assert passed is False
    assert missing  # drift is reported via the return value + logs
    status = get_last_status()
    assert status["strict_mode"] is False
    assert status["passed"] is False


def test_enforce_strict_success_updates_cache() -> None:
    db = _make_fake_db(
        {
            "search_sessions": [
                "id", "user_id", "search_id", "status", "started_at",
                "completed_at", "created_at",
            ],
            "search_results_cache": ["id", "params_hash", "results", "created_at"],
            "profiles": ["id", "plan_type", "email"],
        }
    )
    passed, missing = enforce_schema_contract(db, strict=True)
    assert passed is True and not missing
    status = get_last_status()
    assert status["passed"] is True
    assert status["missing"] == []
    assert status["strict_mode"] is True


# ---------------------------------------------------------------------------
# Layer 3: get_last_status is JSON-safe for the admin endpoint
# ---------------------------------------------------------------------------


def test_get_last_status_is_json_safe() -> None:
    import json

    db = _make_fake_db(
        {
            "search_sessions": ["id"],
            "search_results_cache": [],
            "profiles": [],
        }
    )
    enforce_schema_contract(db, strict=False)
    status = get_last_status()
    # Must round-trip through json without custom encoders.
    dumped = json.dumps(status)
    assert "passed" in dumped
    assert "missing" in dumped
    assert "strict_mode" in dumped


# ---------------------------------------------------------------------------
# Feature flag registry sanity
# ---------------------------------------------------------------------------


def test_schema_contract_strict_is_in_feature_flag_registry() -> None:
    from config.features import _FEATURE_FLAG_REGISTRY

    assert "SCHEMA_CONTRACT_STRICT" in _FEATURE_FLAG_REGISTRY, (
        "STORY-414: SCHEMA_CONTRACT_STRICT must live in the registry so "
        "the reload endpoint can flip it without a restart."
    )
    env_var, default = _FEATURE_FLAG_REGISTRY["SCHEMA_CONTRACT_STRICT"]
    assert env_var == "SCHEMA_CONTRACT_STRICT"
    # Default MUST stay false during the 14d rollout — flipping this
    # to true should be a conscious deploy decision, not an accident.
    assert default == "false"
