"""DEBT-04 AC4: Slack webhook notifications for critical system failures.

Provides a lightweight fire-and-forget Slack notifier using httpx.
Only active when SLACK_INGESTION_WEBHOOK_URL is set.

Usage:
    from services.slack_notifier import notify_ingestion_failure
    await notify_ingestion_failure("FullCrawl", "Connection timeout", 42.0)
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

# DEBT-04 AC4: Slack webhook URL for ingestion failure alerts.
# Set SLACK_INGESTION_WEBHOOK_URL in Railway env to enable Slack notifications.
SLACK_INGESTION_WEBHOOK_URL: str = os.getenv("SLACK_INGESTION_WEBHOOK_URL", "")

_TIMEOUT_S = 5.0


async def notify_ingestion_failure(
    job_name: str,
    error: str,
    duration_s: float,
    extra: dict | None = None,
) -> None:
    """Send Slack notification for ingestion job failure.

    No-op when SLACK_INGESTION_WEBHOOK_URL is not set.
    Never raises — all errors are swallowed and logged.

    Args:
        job_name: Human-readable job name (e.g. "FullCrawl", "Incremental").
        error: Error message or exception string.
        duration_s: How long the job ran before failing.
        extra: Optional dict of extra fields to include in the attachment.
    """
    if not SLACK_INGESTION_WEBHOOK_URL:
        logger.debug(
            "[SlackNotifier] SLACK_INGESTION_WEBHOOK_URL not set — skipping notification for %s failure",
            job_name,
        )
        return

    fields = [
        {"title": "Job", "value": job_name, "short": True},
        {"title": "Duration", "value": f"{duration_s:.1f}s", "short": True},
        {"title": "Error", "value": str(error)[:500], "short": False},
    ]
    if extra:
        for k, v in extra.items():
            fields.append({"title": k, "value": str(v)[:200], "short": True})

    payload = {
        "text": f":rotating_light: *SmartLic Ingestion Failure: {job_name}*",
        "attachments": [
            {
                "color": "danger",
                "fields": fields,
                "footer": "SmartLic PNCP Ingestion",
                "ts": int(__import__("time").time()),
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(SLACK_INGESTION_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
        logger.info(
            "[SlackNotifier] Sent ingestion failure alert for %s to Slack", job_name
        )
    except Exception as exc:
        logger.warning(
            "[SlackNotifier] Failed to send Slack notification for %s: %s",
            job_name,
            exc,
        )
