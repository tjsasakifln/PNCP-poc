"""STORY-418: Regression tests for the trial_email_dlq resilience layer.

We cover two goals:

1. ``enqueue`` must route a failed send into the DLQ table and must
   **never** raise, even if the DLQ write itself blows up.
2. ``reason_from_error`` must translate common failure shapes into
   stable metric labels so Grafana panels stay readable.

Integration tests for the reprocess cron are deliberately out of scope
here — they would require booting the full trial_email_sequence module
plus Resend mocks, and the Sentry incident was driven by the enqueue
path being missing entirely.
"""

from __future__ import annotations

from typing import Any

import pytest

from services import trial_email_dlq
from services.trial_email_dlq import RETRY_BACKOFFS, enqueue, reason_from_error


# ---------------------------------------------------------------------------
# reason_from_error — stable metric labels
# ---------------------------------------------------------------------------


def test_reason_from_error_classifies_cb_open() -> None:
    class _Fake(Exception):
        pass
    _Fake.__name__ = "CircuitBreakerOpenError"
    assert reason_from_error(_Fake("Supabase CB OPEN")) == "supabase_cb_open"


def test_reason_from_error_classifies_timeouts() -> None:
    class ReadTimeout(Exception):
        pass

    assert reason_from_error(ReadTimeout("boom")) == "timeout"


def test_reason_from_error_classifies_postgrest() -> None:
    assert reason_from_error(Exception("PGRST204 cache miss")) == "postgrest_error"


def test_reason_from_error_defaults_to_other() -> None:
    assert reason_from_error(ValueError("something weird")) == "other"


# ---------------------------------------------------------------------------
# enqueue — best-effort, never raises
# ---------------------------------------------------------------------------


class _FakeQuery:
    def __init__(self, captured: dict):
        self._captured = captured

    def insert(self, data):
        self._captured["insert"] = data
        return self


class _FakeTable:
    def __init__(self, captured: dict):
        self._captured = captured

    def table(self, name: str):
        self._captured.setdefault("tables_hit", []).append(name)
        return _FakeQuery(self._captured)


@pytest.mark.asyncio
async def test_enqueue_writes_row_and_returns_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def _fake_sb_execute(_query, **_kw):
        captured["sb_execute_called"] = True
        class _R:
            data = [{"id": "00000000-0000-0000-0000-000000000000"}]
        return _R()

    monkeypatch.setattr(trial_email_dlq, "get_supabase", lambda: _FakeTable(captured))
    monkeypatch.setattr(trial_email_dlq, "sb_execute", _fake_sb_execute)

    ok = await enqueue(
        user_id="abcd1234-0000-0000-0000-000000000000",
        email_address="fulano@example.com",
        email_type="value",
        email_number=7,
        payload={"stats": {"searches_count": 3}},
        error=Exception("PGRST204 boom"),
    )
    assert ok is True
    assert captured.get("sb_execute_called") is True
    row = captured["insert"]
    assert row["email_type"] == "value"
    assert row["email_number"] == 7
    assert row["attempts"] == 1
    assert "next_retry_at" in row


@pytest.mark.asyncio
async def test_enqueue_returns_false_when_supabase_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """enqueue must NEVER propagate an exception to the primary loop."""

    def _broken():
        raise RuntimeError("supabase client unavailable")

    monkeypatch.setattr(trial_email_dlq, "get_supabase", _broken)

    ok = await enqueue(
        user_id="abcd1234-0000-0000-0000-000000000000",
        email_address="fulano@example.com",
        email_type="value",
        email_number=7,
        error=Exception("render error"),
    )
    assert ok is False  # silent failure — logged, never raised


# ---------------------------------------------------------------------------
# Backoff schedule — first retry must fit in the 5-min CB cooldown
# ---------------------------------------------------------------------------


def test_retry_backoff_first_delay_shorter_than_cb_cooldown() -> None:
    """The first retry should fire before the next Supabase CB half-open cycle.
    Otherwise a brief outage would still skip a milestone email.
    """
    assert RETRY_BACKOFFS[0] <= 60


# ---------------------------------------------------------------------------
# Migration file exists and locks the table to service_role
# ---------------------------------------------------------------------------


def test_dlq_migration_is_service_role_only() -> None:
    from pathlib import Path

    migration = (
        Path(__file__).resolve().parents[2]
        / "supabase"
        / "migrations"
        / "20260410132000_story418_trial_email_dlq.sql"
    )
    assert migration.exists(), "STORY-418: DLQ migration missing"
    body = migration.read_text(encoding="utf-8")
    assert "ENABLE ROW LEVEL SECURITY" in body
    assert "service_role" in body
    assert "trial_email_dlq_pending_idx" in body
