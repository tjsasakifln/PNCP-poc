"""STORY-2.8 (TD-DB-011): tests for backend/scripts/dedup_profiles_email.py.

Covers:
  * Cluster building — dedupes case-insensitively, skips NULL / soft-deleted.
  * Winner heuristic — last_sign_in_at > paying > created_at > id.
  * DRY-RUN default — no writes.
  * --execute without CONFIRM_DEDUP=YES — exit code 2, no writes.
  * --execute WITH CONFIRM_DEDUP=YES — exercises FK repoint + soft-delete + audit.
  * CSV plan file written before any mutation.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Make scripts/ importable
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

import dedup_profiles_email as dedup  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _profile(
    _id: str,
    email: str,
    *,
    last_sign_in_at: str | None = None,
    created_at: str = "2025-01-01T00:00:00+00:00",
    deleted_at: str | None = None,
    plan_type: str = "free",
    stripe_customer_id: str | None = None,
) -> dict:
    return {
        "id": _id,
        "email": email,
        "last_sign_in_at": last_sign_in_at,
        "created_at": created_at,
        "deleted_at": deleted_at,
        "plan_type": plan_type,
        "stripe_customer_id": stripe_customer_id,
    }


class _ChainableMock:
    """Minimal fluent-API mock that mirrors supabase-py builder behaviour.

    Records every call and allows returning a fixed response.data.
    """

    def __init__(self, script: "_DBScript") -> None:
        self._script = script
        self._table = None

    # supabase.table("foo").select("*").eq("x", 1).execute()
    def table(self, name: str) -> "_ChainableMock":
        self._script.calls.append(("table", name))
        self._table = name
        return self

    def select(self, *a, **kw) -> "_ChainableMock":
        return self

    def range(self, *a, **kw) -> "_ChainableMock":
        return self

    def in_(self, *a, **kw) -> "_ChainableMock":
        return self

    def eq(self, col, val) -> "_ChainableMock":
        self._script.calls.append(("eq", self._table, col, val))
        return self

    def update(self, payload) -> "_ChainableMock":
        self._script.calls.append(("update", self._table, dict(payload)))
        return self

    def insert(self, payload) -> "_ChainableMock":
        self._script.calls.append(("insert", self._table, dict(payload) if isinstance(payload, dict) else payload))
        return self

    def execute(self):
        # Pop a queued response for this table; default to empty list.
        data = self._script.responses.get(self._table, [])
        # Once-only consumption: allow tests to queue up a sequence
        if isinstance(data, list) and data and isinstance(data[0], list):
            data = self._script.responses[self._table].pop(0)
        return SimpleNamespace(data=data)


class _DBScript:
    """Holds scripted responses + recorded calls for _ChainableMock."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.responses: dict[str, list] = {}


@pytest.fixture
def script() -> _DBScript:
    return _DBScript()


@pytest.fixture
def fake_sb(script: _DBScript) -> _ChainableMock:
    return _ChainableMock(script)


# ---------------------------------------------------------------------------
# Cluster building
# ---------------------------------------------------------------------------


class TestBuildClusters:
    def test_groups_by_lowered_email(self):
        profs = [
            _profile("a", "User@Example.com"),
            _profile("b", "user@example.com"),
            _profile("c", "unique@example.com"),
        ]
        clusters = dedup.build_clusters(profs)
        assert "user@example.com" in clusters
        assert len(clusters["user@example.com"]) == 2
        assert "unique@example.com" not in clusters  # no dup

    def test_skips_null_and_blank_emails(self):
        profs = [
            _profile("a", ""),
            _profile("b", ""),
            _profile("c", None),
        ]
        assert dedup.build_clusters(profs) == {}

    def test_skips_soft_deleted(self):
        profs = [
            _profile("a", "x@y.com", deleted_at="2026-01-01T00:00:00+00:00"),
            _profile("b", "x@y.com"),
        ]
        assert dedup.build_clusters(profs) == {}


# ---------------------------------------------------------------------------
# Winner heuristic
# ---------------------------------------------------------------------------


class TestPickWinner:
    def test_most_recent_last_sign_in_wins(self):
        a = _profile("a", "x@y.com", last_sign_in_at="2026-01-01T00:00:00+00:00")
        b = _profile("b", "x@y.com", last_sign_in_at="2026-02-01T00:00:00+00:00")
        assert dedup.pick_winner([a, b], paying_ids=set())["id"] == "b"

    def test_paying_beats_non_paying_when_last_sign_in_tied(self):
        a = _profile("a", "x@y.com")  # no last_sign_in
        b = _profile("b", "x@y.com")
        winner = dedup.pick_winner([a, b], paying_ids={"b"})
        assert winner["id"] == "b"

    def test_oldest_created_at_wins_on_further_tie(self):
        a = _profile("a", "x@y.com", created_at="2026-02-01T00:00:00+00:00")
        b = _profile("b", "x@y.com", created_at="2025-02-01T00:00:00+00:00")
        winner = dedup.pick_winner([a, b], paying_ids=set())
        assert winner["id"] == "b"

    def test_deterministic_final_tiebreak_by_id(self):
        a = _profile("a", "x@y.com")
        b = _profile("b", "x@y.com")
        # Both identical -> id sort picks 'a'
        winner = dedup.pick_winner([a, b], paying_ids=set())
        assert winner["id"] == "a"


# ---------------------------------------------------------------------------
# CSV plan generation
# ---------------------------------------------------------------------------


class TestWritePlanCSV:
    def test_csv_has_header_and_rows(self, tmp_path):
        clusters = {
            "x@y.com": [
                _profile("w", "x@y.com", last_sign_in_at="2026-02-01T00:00:00+00:00"),
                _profile("l1", "x@y.com"),
                _profile("l2", "x@y.com"),
            ]
        }
        out = tmp_path / "plan.csv"
        plan = dedup.write_plan_csv(clusters, paying_ids=set(), output_path=out)
        assert out.exists()
        assert len(plan) == 1
        assert plan[0]["winner_id"] == "w"
        assert set(plan[0]["loser_ids"].split(";")) == {"l1", "l2"}

        with out.open(encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        assert rows[0] == [
            "email",
            "cluster_size",
            "winner_id",
            "loser_ids",
            "winner_last_sign_in",
            "winner_is_paying",
            "recommendation",
        ]
        assert rows[1][0] == "x@y.com"
        assert rows[1][1] == "3"


# ---------------------------------------------------------------------------
# CLI invariants
# ---------------------------------------------------------------------------


class TestCLIInvariants:
    def test_default_is_dry_run_no_writes(
        self,
        tmp_path,
        monkeypatch,
        script,
        fake_sb,
    ):
        monkeypatch.setattr(dedup, "_get_client", lambda: fake_sb)
        script.responses["profiles"] = [
            _profile("w", "x@y.com", last_sign_in_at="2026-02-01T00:00:00+00:00"),
            _profile("l", "x@y.com"),
        ]
        rc = dedup.main(["--output-dir", str(tmp_path)])
        assert rc == 0
        # CSV must exist
        csvs = list(tmp_path.glob("dedup_profiles_email_*.csv"))
        assert len(csvs) == 1
        # No update/insert calls in dry-run
        updates = [c for c in script.calls if c[0] == "update"]
        inserts = [c for c in script.calls if c[0] == "insert"]
        assert updates == [], f"dry-run leaked updates: {updates}"
        assert inserts == [], f"dry-run leaked inserts: {inserts}"

    def test_execute_without_env_confirm_refuses(
        self,
        tmp_path,
        monkeypatch,
        script,
        fake_sb,
    ):
        monkeypatch.delenv(dedup.CONFIRM_ENV, raising=False)
        monkeypatch.setattr(dedup, "_get_client", lambda: fake_sb)
        rc = dedup.main(["--execute", "--output-dir", str(tmp_path)])
        assert rc == 2
        # Should NOT have fetched anything (fail fast)
        assert ("table", "profiles") not in script.calls

    def test_execute_with_env_confirm_writes(
        self,
        tmp_path,
        monkeypatch,
        script,
        fake_sb,
    ):
        monkeypatch.setenv(dedup.CONFIRM_ENV, dedup.CONFIRM_VALUE)
        monkeypatch.setattr(dedup, "_get_client", lambda: fake_sb)
        script.responses["profiles"] = [
            _profile("w", "x@y.com", last_sign_in_at="2026-02-01T00:00:00+00:00"),
            _profile("l1", "x@y.com"),
        ]
        rc = dedup.main(["--execute", "--output-dir", str(tmp_path)])
        assert rc == 0

        tables_updated = {c[1] for c in script.calls if c[0] == "update"}
        # Expect FK repoint on all dependent tables PLUS profiles soft-delete
        for fk_table in dedup.FK_TABLES_USER_ID:
            assert fk_table in tables_updated, f"missing FK repoint on {fk_table}"
        assert "profiles" in tables_updated, "missing soft-delete update on profiles"

        # And at least one audit event was inserted
        audit_inserts = [
            c for c in script.calls if c[0] == "insert" and c[1] == "audit_events"
        ]
        assert len(audit_inserts) == 1
        details = audit_inserts[0][2].get("details", {})
        assert audit_inserts[0][2]["event_type"] == "profile_dedup_merged"
        assert details.get("winner_id") == "w"
        assert details.get("loser_ids") == ["l1"]


# ---------------------------------------------------------------------------
# Hash helper
# ---------------------------------------------------------------------------


def test_hash_id_truncated_16_hex():
    h = dedup._hash_id("11111111-2222-3333-4444-555555555555")
    assert h is not None
    assert len(h) == 16
    # Hex chars only
    int(h, 16)


def test_hash_id_none_for_blank():
    assert dedup._hash_id("") is None
    assert dedup._hash_id(None) is None
