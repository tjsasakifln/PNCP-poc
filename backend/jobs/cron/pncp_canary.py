"""STORY-4.5 (TD-SYS-002) — ARQ cron task for PNCP breaking-change canary.

Runs ``run_pncp_canary`` every ``PNCP_CANARY_INTERVAL_S`` seconds (default 600s
= 10 min). Follows the same ``start_*_task`` convention as the rest of
``backend/jobs/cron/*`` so ``scheduler.register_all_cron_tasks`` can pick it up.

Rationale for a separate task (rather than extending ``start_health_canary_task``):

- Different cadence: health canary runs every 5 min for uptime; breaking-change
  detection is background noise-sensitive and fine at 10 min.
- Different escalation surface: health canary writes incidents to Supabase;
  this canary pages Sentry with fingerprints.
- Isolated failure domain: a schema check bug shouldn't suppress uptime data.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


async def _pncp_canary_loop() -> None:
    from config import PNCP_CANARY_INTERVAL_S

    try:
        from pncp_canary import run_pncp_canary
    except ImportError as exc:  # pragma: no cover - defensive
        logger.error("STORY-4.5: pncp_canary module unavailable: %s", exc)
        return

    # Stagger startup so we don't hit PNCP the moment the worker boots.
    await asyncio.sleep(60)
    while True:
        try:
            result = await run_pncp_canary()
            if result.healthy:
                logger.info(
                    "STORY-4.5: PNCP canary healthy (status=%s)",
                    result.details.get("status_code") if result.details else "unknown",
                )
            else:
                logger.warning(
                    "STORY-4.5: PNCP canary unhealthy reason=%s failures=%d alerted=%s",
                    result.reason,
                    result.consecutive_failures,
                    result.alerted,
                )
            await asyncio.sleep(PNCP_CANARY_INTERVAL_S)
        except asyncio.CancelledError:
            logger.info("STORY-4.5: PNCP canary task cancelled")
            raise
        except Exception as exc:  # noqa: BLE001 — defensive, never let loop die
            logger.error("STORY-4.5: PNCP canary iteration error: %s", exc, exc_info=True)
            await asyncio.sleep(60)  # short retry on unexpected error


async def start_pncp_canary_task() -> asyncio.Task:
    """Start the PNCP canary loop and return the created task."""

    task = asyncio.create_task(_pncp_canary_loop(), name="pncp_canary")
    logger.info("STORY-4.5: PNCP canary task started (interval: 10m)")
    return task


__all__ = ["start_pncp_canary_task"]
