"""Checkpoint management for PNCP ingestion pipeline.

Checkpoints track the last successfully crawled date for each (UF, modalidade)
combination so that incremental crawls can resume where they left off without
re-fetching data that hasn't changed.

Tables used:
  - ingestion_checkpoints  — per-(uf, modalidade, source) last-success record
  - ingestion_runs         — per-batch run metadata and final statistics
"""

import logging
from datetime import date
from typing import Any

from supabase_client import get_supabase

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Checkpoint reads
# ---------------------------------------------------------------------------

async def get_last_checkpoint(
    uf: str,
    modalidade: int,
    source: str = "pncp",
) -> date | None:
    """Return the last successfully crawled date for (uf, modalidade, source).

    Queries ingestion_checkpoints for the most recent row with
    status='completed' and returns its ``last_date`` as a Python date.

    Returns None if no checkpoint exists yet.
    """
    supabase = get_supabase()
    try:
        result = (
            supabase
            .table("ingestion_checkpoints")
            .select("last_date")
            .eq("uf", uf)
            .eq("modalidade_id", modalidade)
            .eq("source", source)
            .eq("status", "completed")
            .order("last_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if rows:
            raw_date = rows[0].get("last_date")
            if raw_date:
                return _parse_date(raw_date)
        return None
    except Exception as exc:
        logger.warning(
            "get_last_checkpoint: uf=%s modalidade=%s — %s: %s",
            uf,
            modalidade,
            type(exc).__name__,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Checkpoint writes
# ---------------------------------------------------------------------------

async def save_checkpoint(
    uf: str,
    modalidade: int,
    last_date: date,
    records_fetched: int,
    crawl_batch_id: str,
    source: str = "pncp",
) -> None:
    """Upsert a completed checkpoint after a successful crawl.

    Uses an upsert on the (uf, modalidade, source) unique constraint.
    """
    supabase = get_supabase()
    try:
        payload: dict[str, Any] = {
            "uf": uf,
            "modalidade_id": modalidade,
            "source": source,
            "last_date": last_date.isoformat(),
            "records_fetched": records_fetched,
            "crawl_batch_id": crawl_batch_id,
            "status": "completed",
            "error_message": None,
        }
        (
            supabase
            .table("ingestion_checkpoints")
            .upsert(payload, on_conflict="source,uf,modalidade_id,crawl_batch_id")
            .execute()
        )
        logger.debug(
            "save_checkpoint: uf=%s modalidade=%s last_date=%s records=%d",
            uf,
            modalidade,
            last_date,
            records_fetched,
        )
    except Exception as exc:
        logger.error(
            "save_checkpoint: uf=%s modalidade=%s — %s: %s",
            uf,
            modalidade,
            type(exc).__name__,
            exc,
        )


async def mark_checkpoint_failed(
    uf: str,
    modalidade: int,
    crawl_batch_id: str,
    error_message: str,
    source: str = "pncp",
) -> None:
    """Mark the checkpoint for (uf, modalidade) as failed.

    Does not overwrite ``last_date`` — keeps the last known good date intact
    so that the next incremental crawl can recover from the right starting point.
    """
    supabase = get_supabase()
    try:
        payload: dict[str, Any] = {
            "uf": uf,
            "modalidade_id": modalidade,
            "source": source,
            "crawl_batch_id": crawl_batch_id,
            "status": "failed",
            "error_message": error_message[:2000],  # Truncate for column limit
        }
        (
            supabase
            .table("ingestion_checkpoints")
            .upsert(payload, on_conflict="source,uf,modalidade_id,crawl_batch_id")
            .execute()
        )
        logger.warning(
            "mark_checkpoint_failed: uf=%s modalidade=%s batch=%s",
            uf,
            modalidade,
            crawl_batch_id,
        )
    except Exception as exc:
        logger.error(
            "mark_checkpoint_failed: uf=%s modalidade=%s — could not write failure record: %s: %s",
            uf,
            modalidade,
            type(exc).__name__,
            exc,
        )


# ---------------------------------------------------------------------------
# Ingestion run lifecycle
# ---------------------------------------------------------------------------

async def create_ingestion_run(
    crawl_batch_id: str,
    run_type: str,
) -> None:
    """Insert a new ingestion_runs row at the start of a crawl.

    Args:
        crawl_batch_id: Unique identifier for this run (e.g. "full_20260325_050000").
        run_type: "full" or "incremental".
    """
    supabase = get_supabase()
    try:
        payload: dict[str, Any] = {
            "crawl_batch_id": crawl_batch_id,
            "run_type": run_type,
            "status": "running",
        }
        (
            supabase
            .table("ingestion_runs")
            .insert(payload)
            .execute()
        )
        logger.info(
            "create_ingestion_run: batch_id=%s type=%s — run started",
            crawl_batch_id,
            run_type,
        )
    except Exception as exc:
        # Non-fatal: monitoring is best-effort; crawl should proceed regardless
        logger.warning(
            "create_ingestion_run: could not insert run record — %s: %s",
            type(exc).__name__,
            exc,
        )


async def complete_ingestion_run(
    crawl_batch_id: str,
    *,
    status: str = "completed",
    total_fetched: int = 0,
    inserted: int = 0,
    updated: int = 0,
    unchanged: int = 0,
    ufs_completed: list[str] | None = None,
    ufs_failed: list[str] | None = None,
    error_message: str | None = None,
) -> None:
    """Update ingestion_runs with final statistics after a crawl completes.

    Args:
        crawl_batch_id: Run identifier to update.
        status: Final status — "completed", "failed", or "partial".
        total_fetched: Total raw records received from the API.
        inserted: New rows inserted into pncp_raw_bids.
        updated: Existing rows updated (content_hash changed).
        unchanged: Rows with no change (deduplicated).
        ufs_completed: List of UF codes successfully processed.
        ufs_failed: List of UF codes that encountered errors.
        error_message: Optional error string for failed/partial runs.
    """
    supabase = get_supabase()
    try:
        payload: dict[str, Any] = {
            "status": status,
            "total_fetched": total_fetched,
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "ufs_completed": ufs_completed or [],
            "ufs_failed": ufs_failed or [],
        }
        if error_message:
            payload["error_message"] = error_message[:2000]

        (
            supabase
            .table("ingestion_runs")
            .update(payload)
            .eq("crawl_batch_id", crawl_batch_id)
            .execute()
        )
        logger.info(
            "complete_ingestion_run: batch_id=%s status=%s "
            "fetched=%d inserted=%d updated=%d unchanged=%d "
            "ufs_ok=%s ufs_fail=%s",
            crawl_batch_id,
            status,
            total_fetched,
            inserted,
            updated,
            unchanged,
            ufs_completed or [],
            ufs_failed or [],
        )
    except Exception as exc:
        logger.warning(
            "complete_ingestion_run: could not update run record — %s: %s",
            type(exc).__name__,
            exc,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_date(raw: Any) -> date | None:
    """Parse a date value from Supabase (string or date object)."""
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            # Handle "2026-03-25" or "2026-03-25T00:00:00"
            return date.fromisoformat(raw[:10])
        except ValueError:
            logger.warning("_parse_date: could not parse '%s' as a date", raw)
    return None
