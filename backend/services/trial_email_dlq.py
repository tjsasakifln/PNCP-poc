"""STORY-418: Helpers around the trial_email_dlq table.

The module is deliberately small and has two responsibilities:

1. ``enqueue`` — called from ``trial_email_sequence.process_trial_emails``
   whenever a send fails (render error, Resend throttle, Supabase CB).
   It never raises — a broken DLQ must never break the primary send
   loop, which would re-introduce the silent failure we are trying to
   fix in the first place.

2. ``reprocess_pending`` — drained daily (9am BRT) by a new ARQ cron.
   Uses an exponential backoff of 30s → 60s → 120s and marks a row
   ``abandoned_at`` after 5 total attempts so Sentry can alert instead
   of retrying forever.

The table contract is defined by
``supabase/migrations/20260410132000_story418_trial_email_dlq.sql``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

# STORY-418: module-level imports so tests can monkeypatch them. The
# original in-function imports worked at runtime but defeat pytest's
# monkeypatch.setattr() on the helpers — and the incident response
# story has high-signal tests we do not want to sacrifice.
from supabase_client import get_supabase, sb_execute  # noqa: E402

logger = logging.getLogger(__name__)

# STORY-418: backoff schedule (seconds) — must fit inside the 24h gap
# between cron runs so a user never skips an entire milestone.
RETRY_BACKOFFS = [30, 60, 120]
MAX_ATTEMPTS = 5  # 3 backoffs + 2 cron pickups = 5 total


async def enqueue(
    *,
    user_id: str,
    email_address: str,
    email_type: str,
    email_number: int,
    payload: Optional[dict[str, Any]] = None,
    error: Exception | str,
) -> bool:
    """Insert a failed send into ``trial_email_dlq``.

    Best-effort: any exception is swallowed and logged so the caller
    (process_trial_emails) can continue the batch. Returns True on
    successful enqueue, False otherwise.
    """
    try:
        sb = get_supabase()
        row = {
            "user_id": user_id,
            "email_address": email_address,
            "email_type": email_type,
            "email_number": email_number,
            "payload": payload or {},
            "attempts": 1,
            "last_error": _truncate(str(error), 1000),
            "next_retry_at": (
                datetime.now(timezone.utc) + timedelta(seconds=RETRY_BACKOFFS[0])
            ).isoformat(),
        }
        await sb_execute(
            sb.table("trial_email_dlq").insert(row),
            category="write",
        )
        _emit_metric_enqueued(email_type, reason_from_error(error))
        logger.warning(
            "STORY-418: trial_email_dlq enqueued",
            extra={
                "user_id": user_id[:8] + "***",
                "email_type": email_type,
                "email_number": email_number,
                "reason": reason_from_error(error),
            },
        )
        return True
    except Exception as dlq_err:
        # Catch-all — DLQ must never bring down the primary loop.
        logger.error(
            "STORY-418: failed to enqueue into trial_email_dlq "
            "(original error kept, DLQ write lost): %s",
            dlq_err,
        )
        return False


async def reprocess_pending(limit: int = 100) -> dict[str, int]:
    """STORY-418: Drain up to ``limit`` pending DLQ rows.

    Called by the daily cron in ``cron_jobs.py``. Selects rows where
    ``reprocessed_at IS NULL`` and ``next_retry_at <= now()``; for each,
    re-renders the email via the shared ``_render_email`` helper from
    trial_email_sequence and attempts a send. Successful sends mark the
    row ``reprocessed_at``; transient failures bump ``attempts`` and
    schedule the next retry; hard failures (attempts > MAX_ATTEMPTS)
    set ``abandoned_at`` and emit a Sentry warning.
    """
    stats = {"considered": 0, "reprocessed": 0, "retried": 0, "abandoned": 0}

    try:
        sb = get_supabase()
        now_iso = datetime.now(timezone.utc).isoformat()

        result = await sb_execute(
            sb.table("trial_email_dlq")
            .select("*")
            .is_("reprocessed_at", "null")
            .is_("abandoned_at", "null")
            .lte("next_retry_at", now_iso)
            .order("created_at")
            .limit(limit),
            category="read",
        )
        rows = result.data or []
        stats["considered"] = len(rows)
    except Exception as e:
        logger.error("STORY-418: DLQ scan failed: %s", e)
        return stats

    if not rows:
        return stats

    # Lazy import to avoid a heavy import cycle between services/ and
    # the email renderer when running unit tests that only want the
    # enqueue path.
    from services.trial_email_sequence import _render_email, get_unsubscribe_url
    from email_service import send_email_async

    for row in rows:
        row_id = row["id"]
        user_id = row["user_id"]
        email_addr = row["email_address"]
        email_type = row["email_type"]
        attempts = int(row.get("attempts") or 0)
        payload = row.get("payload") or {}

        try:
            stats_for_render = dict(payload.get("stats") or {})
            stats_for_render.setdefault("user_id", user_id)
            subject, html = _render_email(
                email_type=email_type,
                user_name=payload.get("user_name") or email_addr.split("@")[0],
                stats=stats_for_render,
                unsubscribe_url=get_unsubscribe_url(user_id),
            )
            send_email_async(
                to=email_addr,
                subject=subject,
                html=html,
                tags=[
                    {"name": "category", "value": "trial_sequence_dlq_retry"},
                    {"name": "type", "value": email_type},
                ],
            )
            await sb_execute(
                sb.table("trial_email_dlq")
                .update(
                    {
                        "reprocessed_at": datetime.now(timezone.utc).isoformat(),
                        "reprocessed_count": int(row.get("reprocessed_count") or 0) + 1,
                    }
                )
                .eq("id", row_id),
                category="write",
            )
            stats["reprocessed"] += 1
            _emit_metric_reprocessed(email_type)
        except Exception as send_err:
            next_attempts = attempts + 1
            if next_attempts >= MAX_ATTEMPTS:
                try:
                    await sb_execute(
                        sb.table("trial_email_dlq")
                        .update(
                            {
                                "abandoned_at": datetime.now(timezone.utc).isoformat(),
                                "attempts": next_attempts,
                                "last_error": _truncate(str(send_err), 1000),
                            }
                        )
                        .eq("id", row_id),
                        category="write",
                    )
                except Exception:
                    pass
                stats["abandoned"] += 1
                logger.error(
                    "STORY-418: trial_email_dlq abandoning after %d attempts for "
                    "user=%s***, email_type=%s",
                    next_attempts,
                    user_id[:8],
                    email_type,
                )
            else:
                backoff = RETRY_BACKOFFS[min(attempts, len(RETRY_BACKOFFS) - 1)]
                try:
                    await sb_execute(
                        sb.table("trial_email_dlq")
                        .update(
                            {
                                "attempts": next_attempts,
                                "last_error": _truncate(str(send_err), 1000),
                                "next_retry_at": (
                                    datetime.now(timezone.utc)
                                    + timedelta(seconds=backoff)
                                ).isoformat(),
                            }
                        )
                        .eq("id", row_id),
                        category="write",
                    )
                except Exception:
                    pass
                stats["retried"] += 1

    logger.info("STORY-418: trial_email_dlq reprocess stats: %s", stats)
    return stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def reason_from_error(error: Exception | str) -> str:
    """Short, label-friendly reason string used for metrics / logs."""
    if isinstance(error, Exception):
        name = type(error).__name__
        msg = str(error)
    else:
        name = "str"
        msg = str(error)
    if "CircuitBreakerOpenError" in name or "circuit breaker" in msg.lower():
        return "supabase_cb_open"
    if "Timeout" in name or "timeout" in msg.lower():
        return "timeout"
    if "PGRST" in msg:
        return "postgrest_error"
    return "other"


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _emit_metric_enqueued(email_type: str, reason: str) -> None:
    try:
        from metrics import TRIAL_EMAIL_DLQ_ENQUEUED

        TRIAL_EMAIL_DLQ_ENQUEUED.labels(email_type=email_type, reason=reason).inc()
    except Exception:
        pass


def _emit_metric_reprocessed(email_type: str) -> None:
    try:
        from metrics import TRIAL_EMAIL_DLQ_REPROCESSED

        TRIAL_EMAIL_DLQ_REPROCESSED.labels(email_type=email_type).inc()
    except Exception:
        pass
