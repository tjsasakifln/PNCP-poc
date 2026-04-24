"""Configuration for PNCP Data Lake ingestion pipeline.

All values are tuned for Supabase free tier limits:
- Max DB connections: 20 (free tier)
- Storage: 500 MB
- Row limits: soft limit around 50k rows per table

Environment variables override defaults at runtime.
"""

import os

# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------

DATALAKE_ENABLED = os.getenv("DATALAKE_ENABLED", "true").lower() in ("true", "1")
DATALAKE_QUERY_ENABLED = os.getenv("DATALAKE_QUERY_ENABLED", "true").lower() in ("true", "1")

# ---------------------------------------------------------------------------
# Crawl schedule (UTC hours)
# ---------------------------------------------------------------------------

# Full crawl runs once daily at 5 UTC = 2am BRT
INGESTION_FULL_CRAWL_HOUR_UTC = int(os.getenv("INGESTION_FULL_CRAWL_HOUR_UTC", "5"))

# Incremental crawls at 11, 17, 23 UTC = 8am, 2pm, 8pm BRT
INGESTION_INCREMENTAL_HOURS = [
    int(h)
    for h in os.getenv("INGESTION_INCREMENTAL_HOURS", "11,17,23").split(",")
]

# ---------------------------------------------------------------------------
# Date range
# ---------------------------------------------------------------------------

# How many days back to crawl on a full crawl
INGESTION_DATE_RANGE_DAYS = int(os.getenv("INGESTION_DATE_RANGE_DAYS", "7"))  # DISK-IO-002: 10→7 days; incremental crawl covers last 3 days 3x/day

# How many days back to crawl on incremental (+ 1 day overlap applied at runtime)
INGESTION_INCREMENTAL_DAYS = int(os.getenv("INGESTION_INCREMENTAL_DAYS", "3"))

# ---------------------------------------------------------------------------
# Rate limiting & concurrency
# ---------------------------------------------------------------------------

# UFs per batch (matches PNCP_BATCH_SIZE from main config)
INGESTION_BATCH_SIZE_UFS = int(os.getenv("INGESTION_BATCH_SIZE_UFS", "5"))

# Seconds to sleep between UF batches (avoids PNCP rate limits)
INGESTION_BATCH_DELAY_S = float(os.getenv("INGESTION_BATCH_DELAY_S", "2.0"))

# Max pages fetched per (UF, modalidade) combination
INGESTION_MAX_PAGES = int(os.getenv("INGESTION_MAX_PAGES", "50"))

# Max simultaneous UF crawls (asyncio.Semaphore)
INGESTION_CONCURRENT_UFS = int(os.getenv("INGESTION_CONCURRENT_UFS", "5"))

# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

# Rows per Supabase RPC call — keep under Supabase 1 MB request limit
INGESTION_UPSERT_BATCH_SIZE = int(os.getenv("INGESTION_UPSERT_BATCH_SIZE", "500"))

# ---------------------------------------------------------------------------
# Scope filters
# ---------------------------------------------------------------------------

# Modalidades to crawl: 4=Concorrência, 5=Pregão Eletr., 6=Pregão Pres.,
# 7=Contratação Direta, 8=Inexigibilidade, 12=Credenciamento
INGESTION_MODALIDADES = [
    int(m)
    for m in os.getenv("INGESTION_MODALIDADES", "4,5,6,7,8,12").split(",")
]

# UFs to crawl — all Brazilian states + DF
INGESTION_UFS = os.getenv(
    "INGESTION_UFS",
    "AC,AL,AM,AP,BA,CE,DF,ES,GO,MA,MG,MS,MT,PA,PB,PE,PI,PR,RJ,RN,RO,RR,RS,SC,SE,SP,TO",
).split(",")

# ---------------------------------------------------------------------------
# Retention / Purge
# ---------------------------------------------------------------------------

# STORY-OBS-001: retention bumped 30→400 days so SEO programmatic pages
# (observatorio, alertas, municipios, orgao) have ~13 months of history.
INGESTION_RETENTION_DAYS = int(os.getenv("INGESTION_RETENTION_DAYS", "400"))

# Days after data_encerramento before a closed bid is purged (default 30).
# Bids still open (data_encerramento in the future) are NEVER purged.
INGESTION_PURGE_GRACE_DAYS = int(os.getenv(
    "INGESTION_PURGE_GRACE_DAYS",
    str(INGESTION_RETENTION_DAYS),
))

# ---------------------------------------------------------------------------
# Backfill (one-time historical crawl)
# ---------------------------------------------------------------------------

# Total days to backfill (API max = 365)
INGESTION_BACKFILL_DAYS = int(os.getenv("INGESTION_BACKFILL_DAYS", "365"))

# Chunk size in days — keeps results under 50-page cap for high-volume UFs
INGESTION_BACKFILL_CHUNK_DAYS = int(os.getenv("INGESTION_BACKFILL_CHUNK_DAYS", "7"))
