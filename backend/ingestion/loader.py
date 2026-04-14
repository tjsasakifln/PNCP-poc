"""Load transformed PNCP records into Supabase via RPC.

Uses two Supabase stored procedures:
  - upsert_pncp_raw_bids(p_records jsonb)  — bulk upsert returning counts
  - purge_old_bids(p_retention_days int)   — delete rows older than N days

STORY-438: When EMBEDDING_ENABLED=true, generates text-embedding-3-small
embeddings for objeto_compra in batches before upserting. Failures are
logged but never block the upsert (graceful degradation).
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase_client import get_supabase
from ingestion.config import INGESTION_UPSERT_BATCH_SIZE


def _apply_date_fallbacks(records: list[dict]) -> list[dict]:
    """STORY-2.12 AC4: ensure data_publicacao/data_abertura are never NULL.

    Caller-supplied lists are mutated in place and returned for chaining.
    """
    fallback = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    for r in records:
        if not r.get("data_publicacao"):
            r["data_publicacao"] = fallback
        if not r.get("data_abertura"):
            r["data_abertura"] = r["data_publicacao"]
    return records

logger = logging.getLogger(__name__)

# Batch size for OpenAI embeddings API calls (max 2048 inputs, 100 is practical)
_EMBEDDING_BATCH_SIZE = 100


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

async def bulk_upsert(
    records: list[dict],
    *,
    batch_size: int = INGESTION_UPSERT_BATCH_SIZE,
) -> dict[str, int]:
    """Upsert records into pncp_raw_bids via Supabase RPC.

    STORY-438: When EMBEDDING_ENABLED=true, generates embeddings for
    objeto_compra in batches of 100 before upsert. Embedding failures
    are logged but do NOT block the upsert.

    The RPC function ``upsert_pncp_raw_bids`` must accept a single jsonb
    parameter ``p_records`` and return a row with columns:
        inserted int, updated int, unchanged int

    Args:
        records: List of row dicts produced by transformer.transform_batch().
        batch_size: Max rows per RPC call (default 500, tuned for 1 MB limit).

    Returns:
        Aggregated counts: {"inserted": N, "updated": N, "unchanged": N, "total": N, "batches": N}
    """
    if not records:
        logger.debug("bulk_upsert: no records to upsert")
        return {"inserted": 0, "updated": 0, "unchanged": 0, "total": 0, "batches": 0}

    # STORY-2.12 AC4: defence-in-depth. The transformer already applies a
    # fallback, but re-assert the invariant here so a hand-written caller
    # that bypassed transform_pncp_item cannot insert NULL data_publicacao.
    _null_pub = sum(1 for r in records if not r.get("data_publicacao"))
    if _null_pub:
        logger.warning(
            "bulk_upsert: %d/%d records still had NULL data_publicacao — "
            "applying loader-level fallback",
            _null_pub,
            len(records),
        )
        records = _apply_date_fallbacks(records)

    # STORY-438: Enrich records with embeddings when enabled
    from config.features import EMBEDDING_ENABLED
    if EMBEDDING_ENABLED:
        records = await _enrich_with_embeddings(records)

    totals: dict[str, int] = {"inserted": 0, "updated": 0, "unchanged": 0, "total": 0, "batches": 0}
    batches = _chunk(records, batch_size)
    supabase = get_supabase()

    for batch_idx, batch in enumerate(batches):
        batch_num = batch_idx + 1
        logger.info(
            "bulk_upsert: batch %d — upserting %d records",
            batch_num,
            len(batch),
        )

        try:
            payload = _serialize_batch(batch)

            result = (
                supabase
                .rpc("upsert_pncp_raw_bids", {"p_records": payload})
                .execute()
            )

            counts = _extract_counts(result, batch_num)
            totals["inserted"] += counts.get("inserted", 0)
            totals["updated"] += counts.get("updated", 0)
            totals["unchanged"] += counts.get("unchanged", 0)
            totals["total"] += len(batch)
            totals["batches"] += 1

            logger.info(
                "bulk_upsert: batch %d done — inserted=%d updated=%d unchanged=%d",
                batch_num,
                counts.get("inserted", 0),
                counts.get("updated", 0),
                counts.get("unchanged", 0),
            )

        except Exception as exc:
            logger.error(
                "bulk_upsert: batch %d failed — %s: %s — skipping and continuing",
                batch_num,
                type(exc).__name__,
                exc,
            )
            # Continue with remaining batches — partial success is better than abort
            continue

    logger.info(
        "bulk_upsert: complete — inserted=%d updated=%d unchanged=%d total=%d batches=%d",
        totals["inserted"],
        totals["updated"],
        totals["unchanged"],
        totals["total"],
        totals["batches"],
    )
    return totals


# ---------------------------------------------------------------------------
# Purge
# ---------------------------------------------------------------------------

async def purge_old_bids(retention_days: int = 30) -> int:
    """Delete rows from pncp_raw_bids older than retention_days.

    Calls the ``purge_old_bids`` Supabase RPC which returns the number
    of deleted rows.

    Args:
        retention_days: Rows with fetched_at older than this many days are deleted.

    Returns:
        Number of deleted rows (0 on error).
    """
    supabase = get_supabase()
    try:
        result = (
            supabase
            .rpc("purge_old_bids", {"p_retention_days": retention_days})
            .execute()
        )
        deleted = _extract_scalar(result, default=0)
        logger.info("purge_old_bids: deleted %d rows (retention=%d days)", deleted, retention_days)
        return deleted
    except Exception as exc:
        logger.error("purge_old_bids: failed — %s: %s", type(exc).__name__, exc)
        return 0


# ---------------------------------------------------------------------------
# STORY-438: Embedding helpers
# ---------------------------------------------------------------------------

async def _enrich_with_embeddings(records: list[dict]) -> list[dict]:
    """Generate embeddings for objeto_compra and add to records.

    Processes in batches of _EMBEDDING_BATCH_SIZE. Failures are logged but
    records without embeddings are still included (embedding=None).

    Returns the same records list with 'embedding' field added where possible.
    """
    texts = [r.get("objeto_compra") or "" for r in records]
    embeddings = await _generate_embeddings_batch(texts)

    enriched = []
    for record, embedding in zip(records, embeddings):
        r = dict(record)
        if embedding is not None:
            r["embedding"] = embedding
        enriched.append(r)

    embedded_count = sum(1 for e in embeddings if e is not None)
    logger.info(
        "bulk_upsert: generated %d/%d embeddings",
        embedded_count,
        len(records),
    )
    return enriched


async def _generate_embeddings_batch(
    texts: list[str],
) -> list[list[float] | None]:
    """Generate embeddings for a list of texts using text-embedding-3-small.

    Processes in sub-batches of _EMBEDDING_BATCH_SIZE. Returns a list of
    the same length as texts; None entries indicate failures.
    """
    results: list[list[float] | None] = [None] * len(texts)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
    except Exception as exc:
        logger.warning("_generate_embeddings_batch: OpenAI client unavailable — %s", exc)
        return results

    for start in range(0, len(texts), _EMBEDDING_BATCH_SIZE):
        batch_texts = texts[start : start + _EMBEDDING_BATCH_SIZE]
        # Use empty string placeholder for blank texts (OpenAI rejects empty strings)
        sanitized = [t if t.strip() else "sem descrição" for t in batch_texts]

        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=sanitized,
                dimensions=256,
            )
            for i, item in enumerate(response.data):
                results[start + i] = item.embedding
        except Exception as exc:
            logger.warning(
                "_generate_embeddings_batch: batch %d-%d failed — %s: %s",
                start,
                start + len(batch_texts),
                type(exc).__name__,
                exc,
            )
            # Leave results[start:start+batch_size] as None — upsert still proceeds

    return results


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _chunk(lst: list, size: int) -> list[list]:
    """Split a list into chunks of at most ``size`` items."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def _serialize_batch(batch: list[dict]) -> list[dict]:
    """Prepare batch for Supabase RPC.

    The supabase-py client serialises RPC params as JSON automatically,
    so we return the list directly (not a JSON string — that would be
    sent as a scalar, causing 'cannot get array length of a scalar').

    We do a json round-trip to coerce non-serialisable values (dates,
    Decimals) to strings, matching what the RPC function expects.
    """
    return json.loads(json.dumps(batch, default=str, ensure_ascii=False))


def _extract_counts(result: Any, batch_num: int) -> dict[str, int]:
    """Extract inserted/updated/unchanged counts from the RPC result.

    The Supabase Python client returns results as a list of dicts.
    The RPC is expected to return a single-row result set.
    """
    try:
        data = result.data
        if isinstance(data, list) and data:
            row = data[0]
            return {
                "inserted": int(row.get("inserted", 0)),
                "updated": int(row.get("updated", 0)),
                "unchanged": int(row.get("unchanged", 0)),
            }
        # RPC returned nothing — treat as 0 counts (may happen on empty batches)
        logger.debug("bulk_upsert: batch %d RPC returned empty data", batch_num)
        return {"inserted": 0, "updated": 0, "unchanged": 0}
    except Exception as exc:
        logger.warning(
            "bulk_upsert: batch %d could not parse RPC counts — %s: %s",
            batch_num,
            type(exc).__name__,
            exc,
        )
        return {"inserted": 0, "updated": 0, "unchanged": 0}


def _extract_scalar(result: Any, default: int = 0) -> int:
    """Extract a scalar integer from an RPC result."""
    try:
        data = result.data
        if isinstance(data, (int, float)):
            return int(data)
        if isinstance(data, list) and data:
            row = data[0]
            if isinstance(row, (int, float)):
                return int(row)
            if isinstance(row, dict):
                # First value found in the dict
                val = next(iter(row.values()), default)
                return int(val)
        return default
    except Exception:
        return default
