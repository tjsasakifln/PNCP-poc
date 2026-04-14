"""STORY-1.1 (EPIC-TD-2026Q2 P0): pg_cron health monitor.

Hourly ARQ cron that queries ``public.get_cron_health()`` and raises a
Sentry alert for any scheduled job that either:

  * has status = 'failed' on its most recent run, or
  * has not produced a successful run for more than ``STALE_AFTER_HOURS``
    hours (default 25h — one-day window + 1h grace).

Dedup: ``sentry_sdk.push_scope`` + ``fingerprint=['cron_job', jobname]``
prevents spam when a job fails repeatedly for the same reason.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Iterable

from supabase_client import get_supabase, sb_execute_direct

logger = logging.getLogger(__name__)

# Stale threshold: a daily cron that has not succeeded in >25h is suspect.
STALE_AFTER_HOURS = 25


def _parse_ts(value: Any) -> datetime | None:
    """Accept str / datetime / None and return a tz-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _is_stale(last_run_at: datetime | None, now: datetime) -> bool:
    if last_run_at is None:
        return True
    delta_hours = (now - last_run_at).total_seconds() / 3600.0
    return delta_hours > STALE_AFTER_HOURS


def _emit_sentry_alert(jobname: str, reason: str, row: dict[str, Any]) -> None:
    """Fire a deduplicated Sentry message for a failing / stale cron job."""
    try:
        import sentry_sdk
    except Exception:
        return

    try:
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("cron_job", jobname)
            scope.set_tag("cron_job.reason", reason)
            scope.set_extra("row", row)
            # Dedup across runs so one bad job doesn't flood the issue list.
            scope.fingerprint = ["cron_job", jobname, reason]
            sentry_sdk.capture_message(
                f"[pg_cron] {jobname} — {reason}",
                level="error",
            )
    except Exception as exc:
        logger.warning("Failed to emit Sentry alert for %s: %s", jobname, exc)


def evaluate_jobs(rows: Iterable[dict[str, Any]], *, now: datetime | None = None) -> list[dict[str, Any]]:
    """Return a list of ``{jobname, reason, row}`` entries for offending jobs.

    Pure function; extracted so that tests can exercise the decision logic
    without touching Supabase, Sentry or the ARQ runtime.
    """
    current = now or datetime.now(timezone.utc)
    problems: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        jobname = row.get("jobname") or "<unknown>"
        last_status = (row.get("last_status") or "").lower()
        last_run_at = _parse_ts(row.get("last_run_at"))

        if last_status == "failed":
            problems.append({"jobname": jobname, "reason": "last_status=failed", "row": row})
            continue

        if _is_stale(last_run_at, current):
            problems.append({"jobname": jobname, "reason": "stale", "row": row})

    return problems


async def cron_monitoring_job(ctx: dict) -> dict:
    """ARQ cron handler: scheduled hourly (minute=0).

    Returns a summary dict so the ARQ result store surfaces health without
    requiring the Sentry/dashboard side-channel.
    """
    start = time.monotonic()
    try:
        sb = get_supabase()
        result = await sb_execute_direct(sb.rpc("get_cron_health"))
        rows = getattr(result, "data", None) or []
    except Exception as exc:
        duration_s = round(time.monotonic() - start, 2)
        logger.error("[CronMonitor] RPC failed: %s", exc, exc_info=True)
        # Surface the monitoring failure itself so Sentry doesn't stay quiet
        # while the underlying signal is blind.
        _emit_sentry_alert("_monitor_self", f"rpc_error:{type(exc).__name__}", {"error": str(exc)})
        return {"status": "failed", "error": str(exc), "duration_s": duration_s}

    problems = evaluate_jobs(rows)
    for p in problems:
        _emit_sentry_alert(p["jobname"], p["reason"], p["row"])

    duration_s = round(time.monotonic() - start, 2)
    logger.info(
        "[CronMonitor] Evaluated %d jobs, %d problems in %ss",
        len(rows),
        len(problems),
        duration_s,
    )
    return {
        "status": "completed",
        "evaluated": len(rows),
        "problems": len(problems),
        "problem_jobs": [p["jobname"] for p in problems],
        "duration_s": duration_s,
    }
