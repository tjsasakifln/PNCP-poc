"""jobs.queue.config — ARQ WorkerSettings and cron job configuration."""
import logging

logger = logging.getLogger(__name__)

arq_log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"arq_fmt": {"format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", "datefmt": "%Y-%m-%d %H:%M:%S"}},
    "handlers": {"stdout": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "arq_fmt"}},
    "root": {"level": "INFO", "handlers": ["stdout"]},
}

# Build worker Redis settings at module level
try:
    from job_queue import _get_redis_settings
    _worker_redis_settings = _get_redis_settings()
except Exception:
    _worker_redis_settings = None

# Build cron jobs list
try:
    from arq.cron import cron as _arq_cron
    from config import CACHE_REFRESH_INTERVAL_HOURS, CACHE_REFRESH_BATCH_SIZE
    from jobs.queue.jobs import cache_refresh_job, cache_warming_job, daily_digest_job, email_alerts_job

    _cron_timeout = max(300, CACHE_REFRESH_BATCH_SIZE * 10)
    _cron_hours = set(range(0, 24, CACHE_REFRESH_INTERVAL_HOURS))
    _worker_cron_jobs = [_arq_cron(cache_refresh_job, hour=_cron_hours, minute=0, timeout=_cron_timeout)]

    from config import CACHE_WARMING_ENABLED, CACHE_WARMING_INTERVAL_HOURS as _warming_hours
    if CACHE_WARMING_ENABLED:
        _worker_cron_jobs.append(_arq_cron(cache_warming_job, hour=set(range(0, 24, _warming_hours)), minute=30, timeout=1800))

    from config import DIGEST_ENABLED, DIGEST_HOUR_UTC
    if DIGEST_ENABLED:
        _worker_cron_jobs.append(_arq_cron(daily_digest_job, hour={DIGEST_HOUR_UTC}, minute=0, timeout=1800))

    from config import ALERTS_ENABLED, ALERTS_HOUR_UTC
    if ALERTS_ENABLED:
        _worker_cron_jobs.append(_arq_cron(email_alerts_job, hour={ALERTS_HOUR_UTC}, minute=0, timeout=1800))

    try:
        from ingestion.config import DATALAKE_ENABLED
        if DATALAKE_ENABLED:
            from ingestion.scheduler import ingestion_full_crawl_job, ingestion_incremental_job, ingestion_purge_job
            from ingestion.config import INGESTION_FULL_CRAWL_HOUR_UTC, INGESTION_INCREMENTAL_HOURS
            _worker_cron_jobs.extend([
                _arq_cron(ingestion_full_crawl_job, hour={INGESTION_FULL_CRAWL_HOUR_UTC}, minute=0, timeout=14400),
                _arq_cron(ingestion_incremental_job, hour=set(INGESTION_INCREMENTAL_HOURS), minute=0, timeout=3600),
                _arq_cron(ingestion_purge_job, hour={INGESTION_FULL_CRAWL_HOUR_UTC + 2}, minute=0, timeout=600),
            ])
            # Supplier contracts index: 3x/week full crawl (Mon/Wed/Fri 06 UTC) + same days incremental
            # CONTRACTS_CRAWL_WEEKDAYS env var: comma-separated weekday names (default: mon,wed,fri)
            # Set CONTRACTS_CRAWL_WEEKDAYS=mon,tues,wed,thurs,fri,sat,sun for daily crawl
            from ingestion.scheduler import (
                contracts_full_crawl_job, contracts_full_crawl_func,
                contracts_incremental_job, contracts_incremental_func,
            )
            from ingestion.contracts_crawler import CONTRACTS_FULL_CRAWL_TIMEOUT, CONTRACTS_INCREMENTAL_TIMEOUT
            _contracts_enabled = __import__("os").getenv("CONTRACTS_INGESTION_ENABLED", "true").lower() in ("true", "1")
            if _contracts_enabled:
                _WDAY = {"mon": 0, "tues": 1, "wed": 2, "thurs": 3, "fri": 4, "sat": 5, "sun": 6}
                _raw_weekdays = __import__("os").getenv("CONTRACTS_CRAWL_WEEKDAYS", "mon,wed,fri")
                _contracts_weekdays = {_WDAY[w] for w in (d.strip() for d in _raw_weekdays.split(",")) if w in _WDAY}
                _worker_cron_jobs.append(
                    _arq_cron(contracts_full_crawl_job, weekday=_contracts_weekdays, hour={INGESTION_FULL_CRAWL_HOUR_UTC + 1}, minute=0, timeout=CONTRACTS_FULL_CRAWL_TIMEOUT),
                )
                _worker_cron_jobs.append(
                    _arq_cron(contracts_incremental_job, weekday=_contracts_weekdays, hour={12, 18, 0}, minute=0, timeout=CONTRACTS_INCREMENTAL_TIMEOUT),
                )
            # Sprint 2 Parte 13: enriquecimento de fornecedores (BrasilAPI)
            # Diario as 08:00 UTC (5am BRT), apos o contracts crawl das 06:00 UTC
            from ingestion.scheduler import enrich_entities_job
            _worker_cron_jobs.append(
                _arq_cron(enrich_entities_job, hour={8}, minute=0, timeout=7200),
            )
            # Sprint 4 Parte 13: enriquecimento de municipios (IBGE)
            # Diario as 09:00 UTC (6am BRT), 1h apos o enricher de fornecedores
            from ingestion.scheduler import enrich_municipios_job
            _worker_cron_jobs.append(
                _arq_cron(enrich_municipios_job, hour={9}, minute=0, timeout=3600),
            )
    except ImportError:
        pass
except Exception:
    _worker_cron_jobs = []


async def _worker_on_startup(ctx: dict) -> None:
    import os as _os
    try:
        from config import setup_logging
        setup_logging(level=_os.getenv("LOG_LEVEL", "INFO"))
        logger.info("CRIT-051: Worker logging configured to stdout")
    except Exception as _log_err:
        logger.warning(f"CRIT-051: Failed to configure worker logging: {_log_err}")

    redis = ctx.get("redis")
    if redis and hasattr(redis, "connection_pool"):
        pool = redis.connection_pool
        if hasattr(pool, "connection_kwargs"):
            pool.connection_kwargs.setdefault("socket_timeout", 30)
            pool.connection_kwargs.setdefault("socket_connect_timeout", 10)
            pool.connection_kwargs.setdefault("socket_keepalive", True)
            logger.info("CRIT-038: Worker Redis pool hardened — socket_timeout=%ss", pool.connection_kwargs.get("socket_timeout"))
    else:
        logger.warning("CRIT-038: Could not access worker Redis connection pool for hardening")


class WorkerSettings:
    """ARQ worker configuration. Start with: arq job_queue.WorkerSettings"""
    from jobs.queue.jobs import (
        llm_summary_job, excel_generation_job, cache_refresh_job, bid_analysis_job,
        cache_warming_job, daily_digest_job, email_alerts_job,
        reclassify_pending_bids_job, classify_zero_match_job,
    )
    from jobs.queue.search import search_job

    _ingestion_functions: list = []
    try:
        from ingestion.config import DATALAKE_ENABLED as _dl_enabled
        if _dl_enabled:
            from ingestion.scheduler import (
                ingestion_full_crawl_job, ingestion_incremental_job, ingestion_purge_job,
                ingestion_backfill_func,
                contracts_full_crawl_func, contracts_incremental_func,
                enrich_entities_func,
                enrich_municipios_job,
            )
            _ingestion_functions = [
                ingestion_full_crawl_job, ingestion_incremental_job, ingestion_purge_job,
                ingestion_backfill_func,
                contracts_full_crawl_func, contracts_incremental_func,
                enrich_entities_func,
                enrich_municipios_job,
            ]
    except ImportError:
        pass

    functions = [
        llm_summary_job, excel_generation_job, cache_refresh_job, search_job,
        bid_analysis_job, cache_warming_job, daily_digest_job, email_alerts_job,
        reclassify_pending_bids_job, classify_zero_match_job,
        *_ingestion_functions,
    ]
    cron_jobs = _worker_cron_jobs
    on_startup = _worker_on_startup
    redis_settings = _worker_redis_settings
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    health_check_interval = 30
    retry_delay = 5.0
