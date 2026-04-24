"""STORY-OBS-001: One-time backfill of pncp_raw_bids for historical months
lost to the 12/30-day purge window.

Run manually post-deploy (after the retention 400-day migration has been
applied). Calls the existing `crawl_backfill` function with a wider window
so Jan–current-month rows are re-fetched from PNCP and upserted.

Usage:
    cd backend
    python -m scripts.backfill_pncp_historical --days 120

Notes:
- The RPC `upsert_pncp_raw_bids` dedups via content_hash, so re-runs are safe.
- Backfill uses reduced concurrency (3 UFs parallel, 3s delay) to avoid
  rate-limiting the PNCP API while incremental crawls run in parallel.
- Expect ~30-60 min runtime for 120 days × 27 UFs × 6 modalidades.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date


logger = logging.getLogger("backfill_pncp_historical")


async def _main(total_days: int, chunk_days: int) -> int:
    from ingestion.crawler import crawl_backfill

    today = date.today()
    logger.info(
        "Starting PNCP historical backfill: today=%s total_days=%d chunk_days=%d "
        "(covers approx %s → %s)",
        today,
        total_days,
        chunk_days,
        (today.toordinal() - total_days),
        today,
    )

    result = await crawl_backfill(total_days=total_days, chunk_days=chunk_days)

    logger.info(
        "Backfill complete: fetched=%d inserted=%d updated=%d skipped=%d",
        result.get("fetched", 0),
        result.get("inserted", 0),
        result.get("updated", 0),
        result.get("skipped", 0),
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill pncp_raw_bids with historical data (PNCP API)."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=120,
        help="Total days of history to backfill (default: 120 — covers Jan–today for an April run).",
    )
    parser.add_argument(
        "--chunk-days",
        type=int,
        default=7,
        help="Window size per crawl batch (default: 7). Must stay ≤30 per PNCP limits.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.days < 1 or args.days > 365:
        logger.error("--days must be between 1 and 365 (PNCP API max). Got: %d", args.days)
        return 2
    if args.chunk_days < 1 or args.chunk_days > 30:
        logger.error("--chunk-days must be between 1 and 30. Got: %d", args.chunk_days)
        return 2

    return asyncio.run(_main(args.days, args.chunk_days))


if __name__ == "__main__":
    sys.exit(main())
