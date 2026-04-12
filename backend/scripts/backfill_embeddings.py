#!/usr/bin/env python3
"""Backfill embeddings for pncp_raw_bids rows where embedding IS NULL.

Uses text-embedding-3-small (dimensions=256) — same model used during ingestion.

Usage:
    # Dry run (estimate cost, no writes)
    python scripts/backfill_embeddings.py --dry-run

    # Actual backfill
    python scripts/backfill_embeddings.py

    # Limit rows to process (useful for staged rollout)
    python scripts/backfill_embeddings.py --max-rows 5000

    # Adjust concurrency between batches (default: 0.5s sleep between calls)
    python scripts/backfill_embeddings.py --sleep 1.0

STORY-438 AC5.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
import time

# Add backend/ to sys.path so local imports work when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

_FETCH_BATCH_SIZE = 500   # rows fetched from Supabase per page
_EMBED_BATCH_SIZE = 100   # texts per OpenAI embeddings call
_MODEL = "text-embedding-3-small"
_DIMENSIONS = 256
# OpenAI pricing: $0.02 / 1M tokens (text-embedding-3-small as of Apr 2026)
_COST_PER_1M_TOKENS = 0.02
_AVG_TOKENS_PER_OBJECT = 25  # rough average for objeto_compra


async def _fetch_null_embedding_rows(
    supabase: object,
    offset: int,
    limit: int,
) -> list[dict]:
    """Fetch rows from pncp_raw_bids where embedding IS NULL and is_active = true."""
    try:
        result = (
            supabase  # type: ignore[attr-defined]
            .table("pncp_raw_bids")
            .select("pncp_id, objeto_compra")
            .is_("embedding", "null")
            .eq("is_active", True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.error("fetch_null_embedding_rows: failed at offset=%d — %s", offset, exc)
        return []


async def _generate_embeddings(
    client: object,
    texts: list[str],
) -> list[list[float] | None]:
    """Generate embeddings for a list of texts. Returns None entries on failure."""
    sanitized = [t.strip() if t and t.strip() else "sem descrição" for t in texts]
    try:
        response = await client.embeddings.create(  # type: ignore[attr-defined]
            model=_MODEL,
            input=sanitized,
            dimensions=_DIMENSIONS,
        )
        return [item.embedding for item in response.data]
    except Exception as exc:
        logger.warning("_generate_embeddings: failed — %s: %s", type(exc).__name__, exc)
        return [None] * len(texts)


async def _update_embeddings(
    supabase: object,
    updates: list[dict],  # list of {"pncp_id": str, "embedding": list[float]}
) -> int:
    """Update embedding column for a list of rows. Returns count of successful updates."""
    updated = 0
    for row in updates:
        try:
            supabase.table("pncp_raw_bids").update(  # type: ignore[attr-defined]
                {"embedding": row["embedding"]}
            ).eq("pncp_id", row["pncp_id"]).execute()
            updated += 1
        except Exception as exc:
            logger.warning(
                "_update_embeddings: failed for pncp_id=%s — %s",
                row["pncp_id"],
                exc,
            )
    return updated


async def run_backfill(
    dry_run: bool = False,
    max_rows: int | None = None,
    sleep_between_batches: float = 0.5,
) -> None:
    """Main backfill loop."""
    from supabase_client import get_supabase
    from openai import AsyncOpenAI

    supabase = get_supabase()
    client = AsyncOpenAI()

    logger.info("=" * 60)
    logger.info("Backfill Embeddings — STORY-438")
    logger.info("Model: %s (dimensions=%d)", _MODEL, _DIMENSIONS)
    logger.info("Dry run: %s", dry_run)
    logger.info("=" * 60)

    # Count rows to process
    try:
        count_result = (
            supabase.table("pncp_raw_bids")
            .select("pncp_id", count="exact")
            .is_("embedding", "null")
            .eq("is_active", True)
            .execute()
        )
        total_rows = count_result.count or 0
    except Exception as exc:
        logger.error("Cannot count rows: %s", exc)
        total_rows = 0

    if max_rows:
        total_rows = min(total_rows, max_rows)

    estimated_tokens = total_rows * _AVG_TOKENS_PER_OBJECT
    estimated_cost_usd = (estimated_tokens / 1_000_000) * _COST_PER_1M_TOKENS
    estimated_cost_brl = estimated_cost_usd * 5.0  # approximate USD→BRL

    logger.info("Rows to backfill:  %d", total_rows)
    logger.info("Estimated tokens:  %d", estimated_tokens)
    logger.info("Estimated cost:    $%.4f USD / R$%.4f BRL", estimated_cost_usd, estimated_cost_brl)

    if dry_run:
        logger.info("DRY RUN — no writes performed. Exiting.")
        return

    if total_rows == 0:
        logger.info("No rows to backfill. All embeddings are present.")
        return

    logger.info("Starting backfill...")
    start_time = time.monotonic()
    total_batches = (total_rows + _FETCH_BATCH_SIZE - 1) // _FETCH_BATCH_SIZE
    processed = 0
    errors = 0
    offset = 0
    batch_num = 0

    while True:
        rows = await _fetch_null_embedding_rows(supabase, offset, _FETCH_BATCH_SIZE)
        if not rows:
            break

        batch_num += 1
        texts = [r.get("objeto_compra") or "" for r in rows]

        # Generate embeddings in sub-batches of _EMBED_BATCH_SIZE
        all_embeddings: list[list[float] | None] = []
        for sub_start in range(0, len(texts), _EMBED_BATCH_SIZE):
            sub_texts = texts[sub_start : sub_start + _EMBED_BATCH_SIZE]
            sub_embeddings = await _generate_embeddings(client, sub_texts)
            all_embeddings.extend(sub_embeddings)
            if sleep_between_batches > 0:
                await asyncio.sleep(sleep_between_batches)

        # Build update payloads
        updates = [
            {"pncp_id": row["pncp_id"], "embedding": emb}
            for row, emb in zip(rows, all_embeddings)
            if emb is not None
        ]
        batch_errors = len(rows) - len(updates)
        errors += batch_errors

        if updates:
            updated = await _update_embeddings(supabase, updates)
            processed += updated
        else:
            logger.warning("Batch %d: all embeddings failed", batch_num)

        logger.info(
            "Batch %d/%d — inserted %d embeddings (%d errors) [total: %d/%d]",
            batch_num,
            total_batches,
            len(updates),
            batch_errors,
            processed,
            total_rows,
        )

        offset += len(rows)
        if max_rows and processed >= max_rows:
            logger.info("max_rows=%d reached. Stopping.", max_rows)
            break

    elapsed = time.monotonic() - start_time
    logger.info("=" * 60)
    logger.info("Backfill complete in %.1fs", elapsed)
    logger.info("Processed: %d rows, Errors: %d", processed, errors)
    logger.info("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Backfill pgvector embeddings for pncp_raw_bids (STORY-438)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate cost and row count without writing anything",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Maximum number of rows to backfill (useful for staged rollout)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Sleep time in seconds between OpenAI sub-batches (default: 0.5)",
    )
    args = parser.parse_args()

    asyncio.run(run_backfill(
        dry_run=args.dry_run,
        max_rows=args.max_rows,
        sleep_between_batches=args.sleep,
    ))


if __name__ == "__main__":
    main()
