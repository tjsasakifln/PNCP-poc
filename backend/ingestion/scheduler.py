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

from arq import func as arq_func

from ingestion.config import DATALAKE_ENABLED
from ingestion.contracts_crawler import CONTRACTS_FULL_CRAWL_TIMEOUT, CONTRACTS_INCREMENTAL_TIMEOUT

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


# arq.func() wraps coroutines with per-job timeout for WorkerSettings.functions
# (used when jobs are manually enqueued via enqueue_job()).
# arq.cron() expects raw coroutines — do NOT pass Function objects to cron().
# config.py imports both: raw for cron(), _func for WorkerSettings.functions.
contracts_full_crawl_func = arq_func(
    contracts_full_crawl_job, timeout=CONTRACTS_FULL_CRAWL_TIMEOUT,
)
contracts_incremental_func = arq_func(
    contracts_incremental_job, timeout=CONTRACTS_INCREMENTAL_TIMEOUT,
)


async def ingestion_backfill_job(ctx: dict) -> dict:
    """ARQ job: One-time historical backfill of PNCP bids.

    Crawls up to 365 days back in 7-day chunks to capture all currently
    open bids that were published before the regular crawl window.

    Feature flag: DATALAKE_ENABLED must be true.
    NOT scheduled on cron — triggered manually via enqueue_job.
    Expected runtime: 4-8h. Timeout: 10h safety.

    Returns:
        dict with status, records_upserted, duration_s.
    """
    if not DATALAKE_ENABLED:
        logger.info("[Ingestion:Backfill] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()
    logger.info("[Ingestion:Backfill] Starting historical backfill")

    try:
        from ingestion.crawler import crawl_backfill
        result = await crawl_backfill()
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error(
            f"[Ingestion:Backfill] Failed after {duration_s}s: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await _notify_failure("Backfill", f"{type(e).__name__}: {e}", duration_s)
        return {
            "status": "failed",
            "error": str(e),
            "duration_s": duration_s,
        }

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        f"[Ingestion:Backfill] Completed in {duration_s}s — "
        f"records={result.get('inserted', 0)}"
    )
    return {**result, "duration_s": duration_s}


# arq.func() wrapper for manual enqueue_job() invocation
ingestion_backfill_func = arq_func(
    ingestion_backfill_job, timeout=36000,  # 10h safety
)


async def enrich_entities_job(ctx: dict) -> dict:
    """ARQ job: Enriquece fornecedores com dados cadastrais da BrasilAPI.

    Sprint 2 Parte 13: popula enriched_entities para habilitar paginas
    /fornecedores/{cnpj} com razao social, CNAE, Simples Nacional, etc.

    Agendado diariamente as 08:00 UTC (5am BRT), apos o contracts crawl.
    Criterio de staleness: 30 dias sem enriquecimento.
    Teto por execucao: 5.000 CNPJs. Timeout ARQ: 2h (7200s).

    Returns:
        dict com status, enriched, skipped, failed, total_fetched, duration_s.
    """
    from ingestion.config import DATALAKE_ENABLED
    if not DATALAKE_ENABLED:
        logger.info("[Enricher] Ignorado — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()
    logger.info("[Enricher] Iniciando enriquecimento de fornecedores")

    try:
        from ingestion.enricher import enrich_entities_job as _run
        result = await _run()
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error("[Enricher] Falha critica apos %.1fs: %s", duration_s, e, exc_info=True)
        await _notify_failure("Enricher", f"{type(e).__name__}: {e}", duration_s)
        return {"status": "failed", "error": str(e), "duration_s": duration_s}

    return result


enrich_entities_func = arq_func(
    enrich_entities_job, timeout=7200,  # 2h safety
)


async def enrich_municipios_job(ctx: dict) -> dict:
    """ARQ job: Enriquece municipios com dados IBGE (populacao, nome oficial).

    Sprint 4 Parte 13: popula enriched_entities para habilitar paginas
    /municipios/{slug} com dados geograficos do IBGE.

    Agendado diariamente as 09:00 UTC (6am BRT), 1h apos o enricher de fornecedores.
    Criterio de staleness: 30 dias. Timeout ARQ: 1h (3600s).
    """
    from ingestion.config import DATALAKE_ENABLED
    if not DATALAKE_ENABLED:
        logger.info("[EnricherMunicipio] Ignorado — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()
    logger.info("[EnricherMunicipio] Iniciando enriquecimento de municipios")

    try:
        from ingestion.enricher import enrich_municipios_job as _run
        result = await _run()
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error("[EnricherMunicipio] Falha critica apos %.1fs: %s", duration_s, e, exc_info=True)
        await _notify_failure("EnricherMunicipio", f"{type(e).__name__}: {e}", duration_s)
        return {"status": "failed", "error": str(e), "duration_s": duration_s}

    return result


async def ingestion_purge_job(ctx: dict) -> dict:
    """ARQ job: Purge closed bids from pncp_raw_bids.

    Purges bids whose data_encerramento passed more than PURGE_GRACE_DAYS ago.
    Open bids (data_encerramento in the future) are NEVER purged.

    Runs daily 2h after full crawl (07:00 UTC = 4am BRT).
    Feature flag: DATALAKE_ENABLED must be true.
    Expected runtime: < 1 min. Timeout: 10 min safety.

    Returns:
        dict with status, deleted, grace_days, duration_s.
    """
    if not DATALAKE_ENABLED:
        logger.info("[Ingestion:Purge] Skipped — DATALAKE_ENABLED=false")
        return {"status": "skipped", "reason": "DATALAKE_ENABLED=false"}

    start = time.monotonic()

    from ingestion.config import INGESTION_PURGE_GRACE_DAYS
    logger.info(
        f"[Ingestion:Purge] Starting purge — grace_days={INGESTION_PURGE_GRACE_DAYS}"
    )

    try:
        from ingestion.loader import purge_old_bids
        deleted = await purge_old_bids(INGESTION_PURGE_GRACE_DAYS)
    except Exception as e:
        duration_s = round(time.monotonic() - start, 1)
        logger.error(
            f"[Ingestion:Purge] Failed after {duration_s}s: {type(e).__name__}: {e}",
            exc_info=True,
        )
        await _notify_failure(
            "Purge",
            f"{type(e).__name__}: {e}",
            duration_s,
            {"grace_days": INGESTION_PURGE_GRACE_DAYS},
        )
        return {
            "status": "failed",
            "error": str(e),
            "grace_days": INGESTION_PURGE_GRACE_DAYS,
            "duration_s": duration_s,
        }

    duration_s = round(time.monotonic() - start, 1)
    logger.info(
        f"[Ingestion:Purge] Completed in {duration_s}s — deleted={deleted} rows "
        f"(grace={INGESTION_PURGE_GRACE_DAYS} days after encerramento)"
    )
    return {
        "status": "completed",
        "deleted": deleted,
        "grace_days": INGESTION_PURGE_GRACE_DAYS,
        "duration_s": duration_s,
    }
