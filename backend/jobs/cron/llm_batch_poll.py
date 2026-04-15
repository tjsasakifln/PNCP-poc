"""STORY-4.1 (TD-SYS-014) — ARQ cron for OpenAI Batch API polling.

Runs every ``LLM_BATCH_POLL_INTERVAL_S`` seconds (default 60s) iff
``LLM_BATCH_ENABLED`` is truthy. For each pending batch, calls
``llm_arbiter.batch_api.poll_batch`` — the batch metadata is dropped from
Redis once the batch reaches a terminal state (completed / failed / expired).
"""

from __future__ import annotations

import asyncio
import logging
import time as _time

logger = logging.getLogger(__name__)


async def _llm_batch_poll_loop() -> None:
    try:
        from config import LLM_BATCH_ENABLED, LLM_BATCH_POLL_INTERVAL_S
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("STORY-4.1: LLM batch flags unavailable: %s", exc)
        return
    if not LLM_BATCH_ENABLED:
        logger.info("STORY-4.1: LLM batch polling disabled (LLM_BATCH_ENABLED=false)")
        return

    try:
        from llm_arbiter.batch_api import list_pending_batch_ids, poll_batch
    except ImportError as exc:  # pragma: no cover - defensive
        logger.error("STORY-4.1: llm_arbiter.batch_api unavailable: %s", exc)
        return

    # Stagger start so worker boot doesn't hammer the API.
    await asyncio.sleep(30)
    while True:
        try:
            batch_ids = await list_pending_batch_ids()
            for batch_id in batch_ids:
                started = _time.time()
                result = await poll_batch(batch_id)
                duration = _time.time() - started
                try:
                    from metrics import LLM_BATCH_JOB_DURATION

                    LLM_BATCH_JOB_DURATION.observe(duration)
                except Exception:
                    pass
                if result is None:
                    logger.debug("STORY-4.1: batch %s still in progress", batch_id)
                else:
                    logger.info(
                        "STORY-4.1: batch %s resolved with %d items (duration=%.1fs)",
                        batch_id,
                        len(result),
                        duration,
                    )
            await asyncio.sleep(LLM_BATCH_POLL_INTERVAL_S)
        except asyncio.CancelledError:
            logger.info("STORY-4.1: LLM batch poll task cancelled")
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("STORY-4.1: batch poll iteration error: %s", exc, exc_info=True)
            await asyncio.sleep(60)


async def start_llm_batch_poll_task() -> asyncio.Task:
    """Start the LLM batch polling loop and return the created task."""

    task = asyncio.create_task(_llm_batch_poll_loop(), name="llm_batch_poll")
    logger.info("STORY-4.1: LLM batch poll task started")
    return task


__all__ = ["start_llm_batch_poll_task"]
