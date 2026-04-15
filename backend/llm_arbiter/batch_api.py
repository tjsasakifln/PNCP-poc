"""STORY-4.1 (TD-SYS-014) — OpenAI Batch API offline reclassification.

OpenAI's Batch API has a 24h SLA — incompatible with the live ``/buscar`` p95
goal. This module targets the **offline** ``reclassify_pending_bids_job``
flow only, where latency is already on the order of hours/days.

Flow:

1. ``submit_batch(items, setor_name, termos_busca, search_id)`` — build
   JSONL, upload via Files API, create a batch, persist metadata in Redis,
   return ``batch_id``.
2. Cron ``start_llm_batch_poll_task`` polls every ``LLM_BATCH_POLL_INTERVAL_S``.
3. ``poll_batch(batch_id)`` — returns parsed results when the batch is
   ``completed`` (else ``None``).

All operations are gated on ``LLM_BATCH_ENABLED`` so the feature can be
rolled out per-environment without code changes.
"""

from __future__ import annotations

import io
import json
import logging
import time as _time
from typing import Any, Optional

logger = logging.getLogger(__name__)


REDIS_KEY_PENDING_BATCHES = "smartlic:llm_batch:pending"
REDIS_KEY_BATCH_META = "smartlic:llm_batch:{batch_id}:meta"


# ---------------------------------------------------------------------------
# Redis helpers (graceful when Redis is unavailable)
# ---------------------------------------------------------------------------


async def _get_redis():
    try:
        from redis_pool import get_redis_pool

        return await get_redis_pool()
    except Exception as exc:
        logger.debug("STORY-4.1: Redis pool unavailable: %s", exc)
        return None


async def _persist_batch_meta(batch_id: str, meta: dict) -> None:
    redis = await _get_redis()
    if redis is None:
        return
    try:
        await redis.sadd(REDIS_KEY_PENDING_BATCHES, batch_id)
        await redis.hset(
            REDIS_KEY_BATCH_META.format(batch_id=batch_id),
            mapping={k: json.dumps(v) if not isinstance(v, str) else v for k, v in meta.items()},
        )
        # TTL 72h so stale metadata is reaped even if cron drops the ball.
        await redis.expire(REDIS_KEY_BATCH_META.format(batch_id=batch_id), 3 * 24 * 3600)
    except Exception as exc:
        logger.warning("STORY-4.1: Failed to persist batch meta: %s", exc)


async def _drop_batch_meta(batch_id: str) -> None:
    redis = await _get_redis()
    if redis is None:
        return
    try:
        await redis.srem(REDIS_KEY_PENDING_BATCHES, batch_id)
        await redis.delete(REDIS_KEY_BATCH_META.format(batch_id=batch_id))
    except Exception as exc:
        logger.debug("STORY-4.1: Failed to drop batch meta: %s", exc)


async def list_pending_batch_ids() -> list[str]:
    redis = await _get_redis()
    if redis is None:
        return []
    try:
        members = await redis.smembers(REDIS_KEY_PENDING_BATCHES)
        return [m.decode() if isinstance(m, (bytes, bytearray)) else str(m) for m in members]
    except Exception as exc:
        logger.debug("STORY-4.1: Failed to list pending batches: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Batch submission
# ---------------------------------------------------------------------------


def _build_batch_jsonl(items: list[dict], setor_name: Optional[str], termos_busca: list[str]) -> bytes:
    """Build the JSONL payload consumed by the OpenAI Batch API.

    Each line is a ``/v1/chat/completions`` request with a ``custom_id`` we
    can use later to pair the response back with the source bid.
    """

    from llm_arbiter.prompt_builder import (
        _build_zero_match_batch_prompt,
        _build_zero_match_batch_prompt_terms,
    )
    from llm_arbiter.classification import LLM_MAX_TOKENS, LLM_MODEL, LLM_TEMPERATURE

    payload_items = [
        {"objeto": it.get("objeto", ""), "valor": it.get("valor", 0.0)} for it in items
    ]
    if termos_busca:
        prompt = _build_zero_match_batch_prompt_terms(termos=list(termos_busca), items=payload_items)
    else:
        prompt = _build_zero_match_batch_prompt(
            setor_id=None, setor_name=setor_name or "", items=payload_items
        )
    buf = io.BytesIO()
    for idx, _ in enumerate(items):
        entry = {
            "custom_id": f"item-{idx}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max(LLM_MAX_TOKENS, 200),
                "temperature": LLM_TEMPERATURE,
            },
        }
        buf.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
    return buf.getvalue()


async def submit_batch(
    items: list[dict],
    *,
    setor_name: Optional[str],
    termos_busca: list[str],
    search_id: Optional[str] = None,
) -> Optional[str]:
    """Submit a batch if the feature is enabled and we have enough items.

    Returns the ``batch_id`` on successful submission, else ``None``.
    """

    try:
        from config import LLM_BATCH_ENABLED, LLM_BATCH_MIN_ITEMS
    except Exception:
        return None

    if not LLM_BATCH_ENABLED or len(items) < LLM_BATCH_MIN_ITEMS:
        return None

    try:
        from llm_arbiter.async_runtime import _get_async_client

        client = _get_async_client()

        payload = _build_batch_jsonl(items, setor_name, termos_busca)

        file_obj = await client.files.create(file=("batch.jsonl", payload), purpose="batch")
        batch = await client.batches.create(
            input_file_id=file_obj.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"search_id": search_id or "", "item_count": str(len(items))},
        )

        meta = {
            "file_id": file_obj.id,
            "submitted_at": _time.time(),
            "item_count": len(items),
            "setor_name": setor_name or "",
            "termos_busca": termos_busca,
            "search_id": search_id or "",
        }
        await _persist_batch_meta(batch.id, meta)

        try:
            from metrics import LLM_BATCH_JOBS_ACTIVE

            LLM_BATCH_JOBS_ACTIVE.inc()
        except Exception:
            pass

        logger.info(
            "STORY-4.1: Submitted batch %s with %d items (search_id=%s)",
            batch.id,
            len(items),
            search_id,
        )
        return batch.id
    except Exception as exc:
        logger.error("STORY-4.1: Failed to submit batch: %s", exc, exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Batch polling
# ---------------------------------------------------------------------------


async def poll_batch(batch_id: str) -> Optional[list[dict]]:
    """Poll a batch by id.

    Returns
    -------
    None
        Batch is still ``in_progress``/``finalizing`` — caller should try
        again next cron tick.
    list[dict]
        Parsed per-item response payloads when the batch is ``completed``.
        Caller is responsible for mapping ``custom_id`` back to source rows.
    """

    try:
        from llm_arbiter.async_runtime import _get_async_client

        client = _get_async_client()
        batch = await client.batches.retrieve(batch_id)
        status = getattr(batch, "status", None)
        if status in {"in_progress", "validating", "finalizing"}:
            return None

        if status == "completed":
            output_file_id = getattr(batch, "output_file_id", None)
            if not output_file_id:
                logger.error("STORY-4.1: batch %s completed without output_file_id", batch_id)
                await _drop_batch_meta(batch_id)
                return []
            file_resp = await client.files.content(output_file_id)
            # OpenAI SDK returns an object with a ``.text`` / ``.read()`` — support both.
            if hasattr(file_resp, "text"):
                body = file_resp.text
            elif hasattr(file_resp, "read"):
                body = (await file_resp.read()).decode("utf-8")
            else:
                body = str(file_resp)
            parsed: list[dict] = []
            for line in body.splitlines():
                if not line.strip():
                    continue
                try:
                    parsed.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    logger.warning("STORY-4.1: skipping malformed batch line: %s", exc)
            await _drop_batch_meta(batch_id)
            try:
                from metrics import LLM_BATCH_JOBS_ACTIVE

                LLM_BATCH_JOBS_ACTIVE.dec()
            except Exception:
                pass
            return parsed

        # expired | failed | cancelled — give up
        logger.error("STORY-4.1: batch %s terminal with status=%s", batch_id, status)
        await _drop_batch_meta(batch_id)
        try:
            from metrics import LLM_BATCH_JOBS_ACTIVE

            LLM_BATCH_JOBS_ACTIVE.dec()
        except Exception:
            pass
        return []
    except Exception as exc:
        logger.error("STORY-4.1: poll_batch failed for %s: %s", batch_id, exc, exc_info=True)
        return None


__all__ = [
    "REDIS_KEY_BATCH_META",
    "REDIS_KEY_PENDING_BATCHES",
    "list_pending_batch_ids",
    "poll_batch",
    "submit_batch",
]
