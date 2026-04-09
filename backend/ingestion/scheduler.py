"""ARQ cron job definitions for PNCP data lake ingestion.

These jobs are registered in job_queue.WorkerSettings when DATALAKE_ENABLED=true.
They are intentionally thin wrappers — all logic lives in crawler.py / loader.py.

Schedule (default, all UTC):
  - Full crawl:         05:00 daily  (2am BRT)
  - Incremental crawl: 11:00, 17:00, 23:00  (8am, 2pm, 8pm BRT)
  - Purge:             07:00 daily  (4am BRT, 2h after full crawl)

Timeouts (ARQ-enforced):
  - Full crawl:    4h  (14400s) — 30-60 min expected, safety margin for retries
  - Incremental:   1h  (3600s)  — 10-20 min expected
  - Purge:        10m  (600s)   — simple DELETE, no heavy I/O
"""

import logging
import time

from ingestion.config import DATALAKE_ENABLED

logger = logging.getLogger(__name__)


async def _notify_failure(
    job_name: str, error: str, duration_s: float, extra: dict | None = None
) -> None:
    """DEBT-04 AC4: Send Slack + Sentry notifications for ingestion job failure."""
    # Sentry capture
    try:
        import sentry_sdk
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("ingestion.job", job_name)
            scope.set_extra("duration_s", duration_s)
            scope.set_extra("error", error)
            sentry_sdk.capture_message(
                f"[Ingestion:{job_name}] Job failed after {duration_s:.1f}s: {error}",
                level="error",
            )
    except Exception:
        pass

    # Slack notification (no-op if webhook not configured)
    try:
        from services.slack_notifier import notify_ingestion_failure
        await notify_ingestion_failure(job_name, error, duration_s, extra)
    except Exception as exc:
        logger.warning("[Ingestion:%s] Could not send Slack alert: %s", job_name, exc)


async def ingestion_full_crawl_job(ctx: dict) -> dict:
    """ARQ job: Full PNCP crawl. Daily at 2am BRT (5am UTC).

    Feature flag: DATALAKE_ENABLED must be true.
    Expected runtime: 30-60 min. Timeout: 4h safety.

    Returns:
        dict with status, ufs_processed, records_upserted, duration_s.
    """
    if not DATALAKE_ENABLED:
        logger.info("[Ingestion:FullCrawl] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()
    logger.info("[Ingestion:FullCrawl] Starting full PNCP crawl")

    try:
        from ingestion.crawler import crawl_full
        result = await crawl_full()
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error(
            f"[Ingestion:FullCrawl] Failed after {duration_s}s: {type(e).__name__}: {e}",
            exc_info=True,
        )
        # DEBT-04 AC4: Notify Slack + Sentry on ingestion failure
        await _notify_failure("FullCrawl", f"{type(e).__name__}: {e}", duration_s)
        return {
            "status": "failed",
            "error": str(e),
            "duration_s": duration_s,
        }

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        f"[Ingestion:FullCrawl] Completed in {duration_s}s — "
        f"records={result.get('records_upserted', 0)}"
    )
    return {**result, "duration_s": duration_s}


async def ingestion_incremental_job(ctx: dict) -> dict:
    """ARQ job: Incremental PNCP crawl. 3x/day (11:00, 17:00, 23:00 UTC).

    Feature flag: DATALAKE_ENABLED must be true.
    Expected runtime: 10-20 min. Timeout: 1h safety.

    Returns:
        dict with status, ufs_processed, records_upserted, duration_s.
    """
    if not DATALAKE_ENABLED:
        logger.info("[Ingestion:Incremental] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()
    logger.info("[Ingestion:Incremental] Starting incremental PNCP crawl")

    try:
        from ingestion.crawler import crawl_incremental
        result = await crawl_incremental()
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error(
            f"[Ingestion:Incremental] Failed after {duration_s}s: {type(e).__name__}: {e}",
            exc_info=True,
        )
        # DEBT-04 AC4: Notify Slack + Sentry on ingestion failure
        await _notify_failure("Incremental", f"{type(e).__name__}: {e}", duration_s)
        return {
            "status": "failed",
            "error": str(e),
            "duration_s": duration_s,
        }

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        f"[Ingestion:Incremental] Completed in {duration_s}s — "
        f"records={result.get('records_upserted', 0)}"
    )
    return {**result, "duration_s": duration_s}


async def contracts_full_crawl_job(ctx: dict) -> dict:
    """ARQ job: Full contracts crawl. Daily at 06:00 UTC (3am BRT).

    Crawls last 730 days of PNCP contracts and indexes by ni_fornecedor.
    Expected runtime: 3-6h for full backfill, ~30 min for daily refresh.
    Timeout: 8h safety.
    """
    if not DATALAKE_ENABLED:
        logger.info("[ContractsCrawler:Full] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    import time as _time
    start = _time.monotonic()
    logger.info("[ContractsCrawler:Full] Starting full contracts crawl")
    try:
        from ingestion.contracts_crawler import run_full_crawl
        result = await run_full_crawl()
    except Exception as e:
        duration_s = round(_time.monotonic() - start, 1)
        logger.error("[ContractsCrawler:Full] Failed after %.1fs: %s", duration_s, e, exc_info=True)
        await _notify_failure("ContractsFull", f"{type(e).__name__}: {e}", duration_s)
        try:
            from ingestion.metrics import CONTRACTS_RUNS_TOTAL, CONTRACTS_RUN_DURATION
            CONTRACTS_RUNS_TOTAL.labels(run_type="full", status="failed").inc()
            CONTRACTS_RUN_DURATION.labels(run_type="full").observe(duration_s)
        except Exception:
            pass
        return {"status": "failed", "error": str(e), "duration_s": duration_s}

    duration_s = round(_time.monotonic() - start, 1)
    logger.info("[ContractsCrawler:Full] Completed in %.1fs — ins=%d", duration_s, result.get("inserted", 0))

    try:
        from ingestion.metrics import CONTRACTS_INGESTED, CONTRACTS_PAGES_FETCHED, CONTRACTS_RUNS_TOTAL, CONTRACTS_RUN_DURATION
        status = result.get("status", "completed")
        CONTRACTS_RUNS_TOTAL.labels(run_type="full", status=status).inc()
        CONTRACTS_RUN_DURATION.labels(run_type="full").observe(duration_s)
        CONTRACTS_PAGES_FETCHED.labels(run_type="full").inc(result.get("pages_fetched", 0))
        CONTRACTS_INGESTED.labels(action="inserted", run_type="full").inc(result.get("inserted", 0))
        CONTRACTS_INGESTED.labels(action="updated", run_type="full").inc(result.get("updated", 0))
        CONTRACTS_INGESTED.labels(action="unchanged", run_type="full").inc(result.get("unchanged", 0))
    except Exception:
        pass

    return {**result, "duration_s": duration_s}


async def contracts_incremental_job(ctx: dict) -> dict:
    """ARQ job: Incremental contracts crawl. 3×/day (12:00, 18:00, 00:00 UTC).

    Crawls last 3 days (+1 overlap). Expected runtime: 5-15 min.
    Timeout: 1h safety.
    """
    if not DATALAKE_ENABLED:
        logger.info("[ContractsCrawler:Incr] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    import time as _time
    start = _time.monotonic()
    logger.info("[ContractsCrawler:Incr] Starting incremental contracts crawl")
    try:
        from ingestion.contracts_crawler import run_incremental_crawl
        result = await run_incremental_crawl()
    except Exception as e:
        duration_s = round(_time.monotonic() - start, 1)
        logger.error("[ContractsCrawler:Incr] Failed after %.1fs: %s", duration_s, e, exc_info=True)
        await _notify_failure("ContractsIncr", f"{type(e).__name__}: {e}", duration_s)
        try:
            from ingestion.metrics import CONTRACTS_RUNS_TOTAL, CONTRACTS_RUN_DURATION
            CONTRACTS_RUNS_TOTAL.labels(run_type="incremental", status="failed").inc()
            CONTRACTS_RUN_DURATION.labels(run_type="incremental").observe(duration_s)
        except Exception:
            pass
        return {"status": "failed", "error": str(e), "duration_s": duration_s}

    duration_s = round(_time.monotonic() - start, 1)
    logger.info("[ContractsCrawler:Incr] Completed in %.1fs — ins=%d", duration_s, result.get("inserted", 0))

    try:
        from ingestion.metrics import CONTRACTS_INGESTED, CONTRACTS_PAGES_FETCHED, CONTRACTS_RUNS_TOTAL, CONTRACTS_RUN_DURATION
        status = result.get("status", "completed")
        CONTRACTS_RUNS_TOTAL.labels(run_type="incremental", status=status).inc()
        CONTRACTS_RUN_DURATION.labels(run_type="incremental").observe(duration_s)
        CONTRACTS_PAGES_FETCHED.labels(run_type="incremental").inc(result.get("pages_fetched", 0))
        CONTRACTS_INGESTED.labels(action="inserted", run_type="incremental").inc(result.get("inserted", 0))
        CONTRACTS_INGESTED.labels(action="updated", run_type="incremental").inc(result.get("updated", 0))
        CONTRACTS_INGESTED.labels(action="unchanged", run_type="incremental").inc(result.get("unchanged", 0))
    except Exception:
        pass

    return {**result, "duration_s": duration_s}


async def ingestion_purge_job(ctx: dict) -> dict:
    """ARQ job: Purge old bids older than retention_days from pncp_raw_bids.

    Runs daily 2h after full crawl (07:00 UTC = 4am BRT).
    Feature flag: DATALAKE_ENABLED must be true.
    Expected runtime: < 1 min. Timeout: 10 min safety.

    Returns:
        dict with status, deleted, retention_days, duration_s.
    """
    if not DATALAKE_ENABLED:
        logger.info("[Ingestion:Purge] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()

    from ingestion.config import INGESTION_RETENTION_DAYS
    logger.info(
        f"[Ingestion:Purge] Starting purge — retention_days={INGESTION_RETENTION_DAYS}"
    )

    try:
        from ingestion.loader import purge_old_bids
        deleted = await purge_old_bids(INGESTION_RETENTION_DAYS)
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error(
            f"[Ingestion:Purge] Failed after {duration_s}s: {type(e).__name__}: {e}",
            exc_info=True,
        )
        # DEBT-04 AC4: Notify Slack + Sentry on ingestion failure
        await _notify_failure(
            "Purge",
            f"{type(e).__name__}: {e}",
            duration_s,
            {"retention_days": INGESTION_RETENTION_DAYS},
        )
        return {
            "status": "failed",
            "error": str(e),
            "retention_days": INGESTION_RETENTION_DAYS,
            "duration_s": duration_s,
        }

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        f"[Ingestion:Purge] Completed in {duration_s}s — deleted={deleted} rows "
        f"(retention={INGESTION_RETENTION_DAYS} days)"
    )
    return {
        "status": "completed",
        "deleted": deleted,
        "retention_days": INGESTION_RETENTION_DAYS,
        "duration_s": duration_s,
    }
