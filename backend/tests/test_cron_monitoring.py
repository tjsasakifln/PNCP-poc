"""STORY-1.1 (EPIC-TD-2026Q2 P0): Tests for the pg_cron Sentry monitor.

Focus on the pure decision logic (`evaluate_jobs`) + the `cron_monitoring_job`
entry point's contract with Sentry (dedup via fingerprint).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from jobs.cron.cron_monitor import (
    STALE_AFTER_HOURS,
    _emit_sentry_alert,
    _is_stale,
    _parse_ts,
    cron_monitoring_job,
    evaluate_jobs,
)


NOW = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_parse_ts_accepts_datetime_str_and_none():
    assert _parse_ts(None) is None
    assert _parse_ts("2026-04-14T07:00:00+00:00") == datetime(
        2026, 4, 14, 7, 0, 0, tzinfo=timezone.utc
    )
    assert _parse_ts("2026-04-14T07:00:00Z") == datetime(
        2026, 4, 14, 7, 0, 0, tzinfo=timezone.utc
    )
    # Naive datetime is promoted to UTC
    naive = datetime(2026, 4, 14, 7, 0, 0)
    parsed = _parse_ts(naive)
    assert parsed is not None and parsed.tzinfo is timezone.utc
    # Garbage input doesn't raise
    assert _parse_ts("not-a-timestamp") is None


def test_is_stale_logic():
    fresh = NOW - timedelta(hours=12)
    stale = NOW - timedelta(hours=STALE_AFTER_HOURS + 1)
    assert _is_stale(fresh, NOW) is False
    assert _is_stale(stale, NOW) is True
    # Never-ran is stale
    assert _is_stale(None, NOW) is True


# ---------------------------------------------------------------------------
# evaluate_jobs — core decision matrix
# ---------------------------------------------------------------------------


def test_evaluate_jobs_flags_failed_status():
    rows = [
        {
            "jobname": "purge-old-bids",
            "last_status": "failed",
            "last_run_at": NOW - timedelta(hours=1),
        }
    ]
    problems = evaluate_jobs(rows, now=NOW)
    assert len(problems) == 1
    assert problems[0]["reason"] == "last_status=failed"


def test_evaluate_jobs_flags_stale_even_when_last_succeeded():
    rows = [
        {
            "jobname": "cleanup-search-cache",
            "last_status": "succeeded",
            "last_run_at": NOW - timedelta(hours=STALE_AFTER_HOURS + 1),
        }
    ]
    problems = evaluate_jobs(rows, now=NOW)
    assert len(problems) == 1
    assert problems[0]["reason"] == "stale"


def test_evaluate_jobs_passes_healthy_jobs():
    rows = [
        {
            "jobname": "healthy",
            "last_status": "succeeded",
            "last_run_at": NOW - timedelta(hours=2),
        }
    ]
    assert evaluate_jobs(rows, now=NOW) == []


def test_evaluate_jobs_treats_never_ran_as_stale():
    rows = [{"jobname": "never-ran", "last_status": "never_ran", "last_run_at": None}]
    problems = evaluate_jobs(rows, now=NOW)
    assert len(problems) == 1
    assert problems[0]["reason"] == "stale"


def test_evaluate_jobs_is_case_insensitive():
    rows = [{"jobname": "x", "last_status": "FAILED", "last_run_at": NOW}]
    problems = evaluate_jobs(rows, now=NOW)
    assert problems and problems[0]["reason"] == "last_status=failed"


def test_evaluate_jobs_ignores_non_dict_rows():
    rows = ["bogus", None, 42]
    assert evaluate_jobs(rows, now=NOW) == []  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Sentry emission — dedup via fingerprint
# ---------------------------------------------------------------------------


def test_emit_sentry_alert_sets_fingerprint_and_tag():
    capture = MagicMock()

    class _Scope:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def set_tag(self, key, value):
            self.tags = getattr(self, "tags", {})
            self.tags[key] = value

        def set_extra(self, key, value):
            self.extras = getattr(self, "extras", {})
            self.extras[key] = value

    scope = _Scope()
    fake_sentry = MagicMock()
    fake_sentry.push_scope.return_value = scope
    fake_sentry.capture_message = capture

    with patch.dict("sys.modules", {"sentry_sdk": fake_sentry}):
        _emit_sentry_alert("purge-old-bids", "stale", {"row": "ok"})

    assert capture.called
    args, kwargs = capture.call_args
    assert "purge-old-bids" in args[0]
    assert kwargs.get("level") == "error"
    assert scope.fingerprint == ["cron_job", "purge-old-bids", "stale"]
    assert scope.tags["cron_job"] == "purge-old-bids"
    assert scope.tags["cron_job.reason"] == "stale"


def test_emit_sentry_alert_never_raises():
    # Even when Sentry is not installed, the function must not propagate errors.
    with patch.dict("sys.modules", {"sentry_sdk": None}):
        # Calling should be a no-op; no exception.
        _emit_sentry_alert("x", "stale", {})


# ---------------------------------------------------------------------------
# cron_monitoring_job — end-to-end contract
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cron_monitoring_job_reports_problems():
    fake_rows = [
        {
            "jobname": "purge-old-bids",
            "last_status": "failed",
            "last_run_at": "2026-04-14T07:00:00+00:00",
        },
        {
            "jobname": "healthy",
            "last_status": "succeeded",
            "last_run_at": NOW.isoformat(),
        },
    ]

    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def fake_execute(_query):
        return SimpleNamespace(data=fake_rows)

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb), patch(
        "jobs.cron.cron_monitor.sb_execute_direct", side_effect=fake_execute
    ), patch("jobs.cron.cron_monitor._emit_sentry_alert") as emit:
        result = await cron_monitoring_job({})

    assert result["status"] == "completed"
    assert result["evaluated"] == 2
    assert result["problems"] == 1
    assert result["problem_jobs"] == ["purge-old-bids"]
    # Only the failing job triggers a Sentry alert.
    assert emit.call_count == 1
    call_args = emit.call_args
    assert call_args.args[0] == "purge-old-bids"
    assert call_args.args[1] == "last_status=failed"


@pytest.mark.asyncio
async def test_cron_monitoring_job_self_alerts_on_rpc_failure():
    mock_sb = MagicMock()
    mock_sb.rpc.return_value = MagicMock(name="rpc_call")

    async def failing_execute(_query):
        raise RuntimeError("supabase down")

    with patch("jobs.cron.cron_monitor.get_supabase", return_value=mock_sb), patch(
        "jobs.cron.cron_monitor.sb_execute_direct", side_effect=failing_execute
    ), patch("jobs.cron.cron_monitor._emit_sentry_alert") as emit:
        result = await cron_monitoring_job({})

    assert result["status"] == "failed"
    assert "supabase down" in result["error"]
    # Self-alert so monitoring blindness surfaces in Sentry
    assert emit.call_count == 1
    args = emit.call_args.args
    assert args[0] == "_monitor_self"
    assert args[1].startswith("rpc_error:")
