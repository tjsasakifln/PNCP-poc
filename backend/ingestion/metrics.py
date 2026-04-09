"""Prometheus metrics for the PNCP Data Lake ingestion pipeline.

Follows the same graceful-degradation pattern as backend/metrics.py:
if prometheus_client is not installed, all metric operations become
silent no-ops so the application works without errors.

Metric naming convention: smartlic_ingestion_*
"""

import logging

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Histogram, Gauge
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed — ingestion metrics disabled (no-op mode)")


class _NoopMetric:
    """Drop-in replacement for Prometheus metrics when library is unavailable."""

    def inc(self, *args, **kwargs):
        pass

    def dec(self, *args, **kwargs):
        pass

    def set(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self


def _counter(name: str, documentation: str, labelnames: list[str] | None = None) -> Counter:
    if not _PROMETHEUS_AVAILABLE:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    return Counter(name, documentation, **kwargs)


def _histogram(
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
    buckets: list[float] | None = None,
) -> Histogram:
    if not _PROMETHEUS_AVAILABLE:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    if buckets:
        kwargs["buckets"] = buckets
    return Histogram(name, documentation, **kwargs)


def _gauge(name: str, documentation: str, labelnames: list[str] | None = None) -> Gauge:
    if not _PROMETHEUS_AVAILABLE:
        return _NoopMetric()
    kwargs = {}
    if labelnames:
        kwargs["labelnames"] = labelnames
    return Gauge(name, documentation, **kwargs)


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

INGESTION_RECORDS_FETCHED = _counter(
    "smartlic_ingestion_records_fetched_total",
    "Total raw records received from the PNCP API",
    labelnames=["uf", "modalidade"],
)

INGESTION_RECORDS_UPSERTED = _counter(
    "smartlic_ingestion_records_upserted_total",
    "Total records upserted into pncp_raw_bids (inserted or updated)",
    labelnames=["uf", "modalidade", "action"],  # action: inserted | updated
)

INGESTION_UFS_PROCESSED = _counter(
    "smartlic_ingestion_ufs_processed_total",
    "Total UF+modalidade combinations successfully crawled",
    labelnames=["modalidade"],
)

INGESTION_UFS_FAILED = _counter(
    "smartlic_ingestion_ufs_failed_total",
    "Total UF+modalidade combinations that failed during crawl",
    labelnames=["modalidade"],
)

INGESTION_PAGES_FETCHED = _counter(
    "smartlic_ingestion_pages_fetched_total",
    "Total PNCP API pages fetched across all UF+modalidade combinations",
    labelnames=["uf", "modalidade"],
)

INGESTION_RUNS_TOTAL = _counter(
    "smartlic_ingestion_runs_total",
    "Total ingestion runs started",
    labelnames=["run_type", "status"],  # run_type: full | incremental; status: completed | failed | partial
)

# ---------------------------------------------------------------------------
# Histograms
# ---------------------------------------------------------------------------

INGESTION_RUN_DURATION = _histogram(
    "smartlic_ingestion_run_duration_seconds",
    "Total duration of a full or incremental ingestion run",
    labelnames=["run_type"],
    buckets=[30, 60, 120, 300, 600, 900, 1800, 3600],
)

INGESTION_UPSERT_BATCH_DURATION = _histogram(
    "smartlic_ingestion_upsert_batch_duration_seconds",
    "Duration of a single bulk_upsert RPC call",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# ---------------------------------------------------------------------------
# Gauges
# ---------------------------------------------------------------------------

INGESTION_LAST_RUN_TIMESTAMP = _gauge(
    "smartlic_ingestion_last_run_timestamp_seconds",
    "Unix timestamp of the most recent completed ingestion run",
    labelnames=["run_type"],
)

INGESTION_ROWS_IN_TABLE = _gauge(
    "smartlic_ingestion_pncp_raw_bids_rows",
    "Approximate row count in pncp_raw_bids (updated after each full crawl)",
)

# ---------------------------------------------------------------------------
# Contracts crawler metrics
# ---------------------------------------------------------------------------

CONTRACTS_INGESTED = _counter(
    "smartlic_contracts_ingested_total",
    "Contracts upserted into pncp_supplier_contracts",
    labelnames=["action", "run_type"],  # action: inserted | updated | unchanged; run_type: full | incremental
)

CONTRACTS_PAGES_FETCHED = _counter(
    "smartlic_contracts_pages_fetched_total",
    "PNCP /contratos pages successfully fetched",
    labelnames=["run_type"],
)

CONTRACTS_RUNS_TOTAL = _counter(
    "smartlic_contracts_runs_total",
    "Total contracts crawl runs started",
    labelnames=["run_type", "status"],  # run_type: full | incremental; status: completed | partial | failed | skipped
)

CONTRACTS_RUN_DURATION = _histogram(
    "smartlic_contracts_run_duration_seconds",
    "Total duration of a contracts crawl run",
    labelnames=["run_type"],
    buckets=[30, 60, 300, 600, 1800, 3600, 7200, 14400],
)
