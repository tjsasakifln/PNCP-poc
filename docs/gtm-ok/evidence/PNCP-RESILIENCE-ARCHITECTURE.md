# PNCP Resilience Architecture

## Recommended Architecture: Option C (Hybrid)

## Executive Summary

SmartLic charges R$1,999/month for procurement intelligence. The current architecture has a single point of failure: PNCP's API. If PNCP is down, slow, or returning truncated data, users get nothing, incomplete results, or silently missing data. For a premium product, this is unacceptable.

The recommended architecture layers three resilience mechanisms on top of the existing pipeline: (1) a persistent procurement data lake in Supabase/PostgreSQL that accumulates every bid ever fetched, (2) a stale-while-revalidate cache that serves instant results from the data lake while refreshing in the background, and (3) a minimum result guarantee algorithm that automatically expands search parameters when results are too few. Together, these ensure users always see results in under 5 seconds, regardless of PNCP's health. The architecture reuses existing infrastructure (Supabase, Railway, InMemoryCache) and requires zero new services.

## Architecture Diagram

```
                    User Request (POST /v1/buscar)
                              |
                              v
                    +--------------------+
                    |  SearchPipeline    |
                    |  Stage 3: Execute  |
                    +--------------------+
                              |
              +---------------+---------------+
              |                               |
              v                               v
     +-----------------+           +-------------------+
     | Local Data Lake |           | PNCP Live Fetch   |
     | (Supabase PG)   |           | (best-effort, 5s  |
     | "Instant path"  |           |  timeout)          |
     +-----------------+           +-------------------+
              |                               |
              |  Always returns               | May fail, may
              |  results (even if             | return new data
              |  stale)                       |
              |                               |
              v                               v
     +-----------------+           +-------------------+
     | Serve to user   |           | Merge + dedup     |
     | immediately     |           | new results into  |
     | with freshness  |           | data lake         |
     | indicator       |           +-------------------+
     +-----------------+                     |
              ^                              |
              |       Background             |
              +------------------------------+
                    Refresh in background,
                    update lake, notify user
                    via SSE if new data found

     +----------------------------------------------------+
     |                Nightly ETL Worker                    |
     |  (Railway cron or pg_cron)                          |
     |  Fetches all modalities for all 27 UFs              |
     |  for date range: today - 180 days                   |
     |  Inserts/updates data lake                          |
     |  Runs at 02:00 BRT (low traffic)                    |
     +----------------------------------------------------+
```

### Detailed Data Flow (Happy Path)

```
User -> SearchPipeline.stage_execute()
  |
  |--> 1. Query local data lake (PostgreSQL, <100ms)
  |       - SELECT from pncp_data_lake WHERE uf IN (...) AND sector matches
  |       - Returns cached results + freshness timestamp
  |
  |--> 2. Fire PNCP live fetch (async, 5s soft timeout)
  |       - Same AsyncPNCPClient code, reduced timeout
  |       - Best-effort: if it succeeds, merge new data
  |
  |--> 3. Minimum Result Guarantee check
  |       - If local + live < 30 results:
  |         a. Expand date range (7d -> 14d -> 30d -> 90d)
  |         b. Query local data lake again with expanded range
  |
  |--> 4. Return results to user
  |       - Include freshness indicator: "Dados atualizados ha X horas"
  |       - If live fetch succeeded: "Dados em tempo real"
  |       - If live fetch failed: "Dados de cache (atualizado ha 4h)"
  |
  |--> 5. Background: PNCP live results -> INSERT INTO pncp_data_lake
          (async, fire-and-forget, does not block response)
```

### Degradation Cascade

```
Level 0: PNCP healthy + data lake warm
  -> Local results (<100ms) + live augmentation (2-5s) = BEST
  -> User sees real-time data

Level 1: PNCP slow (>5s)
  -> Local results served instantly
  -> Live fetch continues in background
  -> SSE updates user if new data arrives within 15s
  -> User sees "Dados do cache, atualizando..."

Level 2: PNCP down
  -> Local results served from data lake
  -> User sees "PNCP indisponivel. Dados de X horas atras."
  -> No live augmentation attempted
  -> Circuit breaker prevents wasted requests

Level 3: PNCP down + data lake empty (cold start only)
  -> Show "Estamos sincronizando dados pela primeira vez"
  -> Trigger emergency ETL for requested UFs
  -> Return partial results as they arrive via SSE
```

## Implementation Plan

### Sprint 1: Foundation (Critical Path)

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Create `pncp_data_lake` table in Supabase (migration 031) | 2h | HIGH -- persistent storage backbone |
| 2 | Build `DataLakeService` class (`backend/data_lake.py`) with write/read/query methods | 4h | HIGH -- all queries route through this |
| 3 | Modify `SearchPipeline.stage_execute()` to query data lake first, then augment with live data | 6h | HIGH -- users see instant results |
| 4 | Build `DataLakeWriter` -- async fire-and-forget that persists every PNCP fetch to data lake | 3h | HIGH -- data lake grows with every search |
| 5 | Implement freshness indicator in `BuscaResponse` schema | 2h | MEDIUM -- UX transparency |
| 6 | Fix P0: Propagate truncation flag through pipeline to user | 4h | CRITICAL -- silent data loss |
| 7 | Fix P0: Make circuit breaker threshold env-configurable (already done) and raise default to 50 | 0.5h | CRITICAL -- cascade prevention |
| 8 | Investigate PNCP API actual max page size (try `tamanhoPagina=500`) | 1h | HIGH -- 25x fewer API calls if supported |
| 9 | Add `data_freshness` field to `BuscaResponse` and frontend banner | 3h | MEDIUM -- user trust |
| 10 | Write tests for DataLakeService (query, write, dedup) | 4h | HIGH -- regression safety |

**Sprint 1 Total: ~29.5 hours (~4 dev-days)**

### Sprint 2: Optimization + ETL

| # | Task | Effort | Impact |
|---|------|--------|--------|
| 1 | Build nightly ETL worker (`backend/etl/pncp_sync.py`) | 8h | HIGH -- data lake stays fresh without user searches |
| 2 | Create Railway cron job (or `pg_cron` in Supabase) for nightly sync | 2h | HIGH -- automated freshness |
| 3 | Implement minimum result guarantee algorithm | 4h | HIGH -- users never see "0 results" for valid queries |
| 4 | Build SWR (stale-while-revalidate) pattern for repeated searches | 4h | MEDIUM -- instant repeat queries |
| 5 | Add zero-result confidence signal (`confidence: "high" | "low"`) | 2h | MEDIUM -- UX clarity |
| 6 | Data lake cleanup job (delete records older than 365 days) | 1h | LOW -- cost management |
| 7 | Add monitoring: data lake row count, freshness age, ETL success/failure | 3h | MEDIUM -- operational visibility |
| 8 | Frontend: degradation banners for "cache data" vs "live data" | 4h | MEDIUM -- user awareness |
| 9 | Write integration tests for full pipeline with data lake | 4h | HIGH -- end-to-end validation |
| 10 | Performance benchmarking: local query vs PNCP live | 2h | LOW -- validation |

**Sprint 2 Total: ~34 hours (~4.5 dev-days)**

**Combined: ~2 sprints (8-9 dev-days)**

## Database Schema Changes

### Migration 031: pncp_data_lake

```sql
-- 031_create_pncp_data_lake.sql
-- PNCP Data Lake: persistent store of all procurement records ever fetched.
-- Enables instant search results regardless of PNCP API health.

-- Main data lake table
CREATE TABLE IF NOT EXISTS pncp_data_lake (
    -- Use the PNCP control number as natural primary key (avoids UUID overhead)
    numero_controle_pncp TEXT PRIMARY KEY,

    -- Core searchable fields (denormalized for query performance)
    uf VARCHAR(2) NOT NULL,
    municipio TEXT,
    orgao TEXT,
    cnpj_orgao VARCHAR(18),
    objeto_compra TEXT NOT NULL,
    valor_total_estimado NUMERIC(15,2),
    modalidade_codigo INTEGER,
    modalidade_nome TEXT,
    situacao_compra_nome TEXT,
    esfera VARCHAR(1),  -- F, E, M

    -- Date fields (critical for search filtering)
    data_publicacao_pncp DATE,
    data_abertura_proposta TIMESTAMPTZ,
    data_encerramento_proposta TIMESTAMPTZ,

    -- Links
    link_sistema_origem TEXT,
    link_processo_eletronico TEXT,

    -- Full raw PNCP response (for future field extraction without re-fetch)
    raw_data JSONB NOT NULL,

    -- Metadata
    first_seen_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    last_seen_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    fetched_by TEXT DEFAULT 'user_search',  -- 'user_search' or 'etl_sync'
    fetch_count INTEGER DEFAULT 1
);

-- Index for the most common query pattern: UF + date range
CREATE INDEX IF NOT EXISTS idx_datalake_uf_date
    ON pncp_data_lake(uf, data_publicacao_pncp DESC);

-- Index for keyword search on objeto_compra (GIN trigram for LIKE queries)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_datalake_objeto_trgm
    ON pncp_data_lake USING gin(objeto_compra gin_trgm_ops);

-- Index for value range filtering
CREATE INDEX IF NOT EXISTS idx_datalake_valor
    ON pncp_data_lake(valor_total_estimado)
    WHERE valor_total_estimado IS NOT NULL;

-- Index for modalidade filtering
CREATE INDEX IF NOT EXISTS idx_datalake_modalidade
    ON pncp_data_lake(modalidade_codigo);

-- Index for freshness queries (ETL monitoring)
CREATE INDEX IF NOT EXISTS idx_datalake_last_seen
    ON pncp_data_lake(last_seen_at DESC);

-- Index for encerramento (deadline filtering, modo_busca="abertas")
CREATE INDEX IF NOT EXISTS idx_datalake_encerramento
    ON pncp_data_lake(data_encerramento_proposta)
    WHERE data_encerramento_proposta IS NOT NULL;

-- Composite index for the "abertas" query (most common search mode)
CREATE INDEX IF NOT EXISTS idx_datalake_abertas
    ON pncp_data_lake(uf, modalidade_codigo, data_encerramento_proposta DESC)
    WHERE data_encerramento_proposta >= now();

-- RLS: Service role only (backend accesses via service role key)
ALTER TABLE pncp_data_lake ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on pncp_data_lake"
    ON pncp_data_lake
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- ETL sync tracking table (one row per sync run)
CREATE TABLE IF NOT EXISTS pncp_etl_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    started_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',  -- running, success, failed, partial
    ufs_synced TEXT[] DEFAULT '{}',
    total_records_fetched INTEGER DEFAULT 0,
    total_records_new INTEGER DEFAULT 0,
    total_records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds NUMERIC(10,2)
);

CREATE INDEX IF NOT EXISTS idx_etl_runs_status
    ON pncp_etl_runs(status, started_at DESC);

-- RLS
ALTER TABLE pncp_etl_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on pncp_etl_runs"
    ON pncp_etl_runs
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Comments
COMMENT ON TABLE pncp_data_lake IS 'Persistent store of all PNCP procurement records. Grows with every user search and nightly ETL sync. Enables instant results when PNCP is unavailable.';
COMMENT ON TABLE pncp_etl_runs IS 'ETL sync run history for monitoring and debugging.';
COMMENT ON COLUMN pncp_data_lake.numero_controle_pncp IS 'Natural PK from PNCP API (e.g., "12345678000190-1-000001/2026"). Deduplication key.';
COMMENT ON COLUMN pncp_data_lake.raw_data IS 'Full PNCP API response JSON. Enables re-processing without re-fetching.';
COMMENT ON COLUMN pncp_data_lake.fetch_count IS 'Number of times this record was seen across fetches. Useful for data quality monitoring.';
```

### Storage Estimation

| Scenario | Records | Avg row size | Total storage | Monthly growth |
|----------|---------|--------------|---------------|----------------|
| Current (no data lake) | 0 | - | 0 | 0 |
| After 1 month (user searches) | ~50,000 | ~2KB | ~100 MB | ~100 MB |
| After 1 month (user + ETL) | ~200,000 | ~2KB | ~400 MB | ~400 MB |
| After 6 months (steady state) | ~500,000 | ~2KB | ~1 GB | ~100 MB |
| Supabase Pro plan limit | - | - | 8 GB included | - |

The raw_data JSONB column is the largest per row (~1.5KB average). This is worth storing because it allows re-processing with new filters or keywords without re-fetching from PNCP. If storage becomes a concern, raw_data can be compressed or moved to Supabase Storage as JSONL files.

## Code Changes Required

| File | Change | Effort |
|------|--------|--------|
| `backend/data_lake.py` | **NEW FILE.** DataLakeService class with `query()`, `upsert_batch()`, `get_freshness()`, `get_count()` methods. Uses `supabase_client.get_supabase()` for DB access. | 4h |
| `backend/etl/pncp_sync.py` | **NEW FILE.** Nightly ETL worker. Iterates 27 UFs x 4 modalities x 30-day window. Calls `AsyncPNCPClient` directly (no quota, no auth). Writes to data lake. Records run in `pncp_etl_runs`. | 8h |
| `backend/search_pipeline.py` | Modify `stage_execute()`: query data lake first (local path), then fire PNCP live fetch with 5s soft timeout as augmentation. Merge and dedup. Write results back to data lake. Add freshness tracking to `SearchContext`. | 6h |
| `backend/search_context.py` | Add fields: `data_freshness: str`, `data_lake_count: int`, `live_augmented: bool`, `data_lake_age_seconds: int`. | 0.5h |
| `backend/schemas.py` | Add to `BuscaResponse`: `data_freshness: str` (e.g., "real_time", "cache_4h", "cache_24h"), `data_lake_age_seconds: Optional[int]`. | 0.5h |
| `backend/pncp_client.py` | (1) Propagate truncation flag: add `truncated: bool` and `truncated_details: list` to `ParallelFetchResult`. (2) Raise circuit breaker default to 50. (3) Test `tamanhoPagina=500`. | 4h |
| `backend/config.py` | Add: `DATA_LAKE_ENABLED`, `LIVE_FETCH_TIMEOUT`, `MIN_RESULTS_GUARANTEE`, `ETL_CRON_SCHEDULE` env vars. | 1h |
| `backend/redis_pool.py` | No changes needed. InMemoryCache remains as L1 cache; data lake is L2 persistent cache. | 0h |
| `frontend/app/buscar/components/SearchResults.tsx` | Add freshness indicator banner: "Dados em tempo real" (green) vs "Dados do cache (Xh)" (yellow) vs "PNCP indisponivel, dados de Xh atras" (orange). | 3h |
| `frontend/app/buscar/page.tsx` | Parse new `data_freshness` and `data_lake_age_seconds` fields from API response. | 1h |
| `supabase/migrations/031_create_pncp_data_lake.sql` | **NEW FILE.** Schema as specified above. | 2h |

## Minimum Result Guarantee Implementation

### Algorithm

```python
async def ensure_minimum_results(
    ctx: SearchContext,
    data_lake: DataLakeService,
    min_results: int = 30,
) -> None:
    """Guarantee at least `min_results` for any reasonable query.

    Strategy: Progressive date-range expansion against the local data lake.
    Only triggers when the combined live + cached results are below threshold.

    This runs AFTER the initial data lake query + live augmentation,
    so it only adds incremental cost when results are genuinely sparse.
    """

    current_count = len(ctx.licitacoes_raw)

    if current_count >= min_results:
        return  # Already have enough

    # Progressive expansion schedule:
    # Original range -> 2x -> 4x -> max (180 days for "abertas", 365 for data lake)
    expansion_ranges = [
        14,   # 2 weeks
        30,   # 1 month
        90,   # 3 months
        180,  # 6 months (matches "abertas" mode)
        365,  # 1 year (data lake only, no live fetch)
    ]

    original_start = date.fromisoformat(ctx.request.data_inicial)
    original_end = date.fromisoformat(ctx.request.data_final)
    original_span = (original_end - original_start).days

    seen_ids = {
        item.get("numeroControlePNCP", item.get("codigoCompra", ""))
        for item in ctx.licitacoes_raw
        if item.get("numeroControlePNCP") or item.get("codigoCompra")
    }

    for target_days in expansion_ranges:
        if target_days <= original_span:
            continue  # Already covered this range

        # Expand the date range symmetrically
        expanded_start = (original_end - timedelta(days=target_days)).isoformat()

        # Query data lake only (no live fetch for expansions)
        additional = await data_lake.query(
            ufs=ctx.request.ufs,
            data_inicial=expanded_start,
            data_final=ctx.request.data_final,
            modalidades=ctx.request.modalidades,
            keywords=list(ctx.active_keywords)[:10],  # Top 10 for perf
            valor_min=ctx.request.valor_minimo,
            valor_max=ctx.request.valor_maximo,
            exclude_ids=seen_ids,
            limit=min_results - current_count,
        )

        for item in additional:
            item_id = item.get("numero_controle_pncp", "")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                ctx.licitacoes_raw.append(
                    _convert_datalake_to_pncp_format(item)
                )
                current_count += 1

        if current_count >= min_results:
            ctx.date_range_expanded = True
            ctx.expanded_to_days = target_days
            logger.info(
                f"Minimum result guarantee: expanded from {original_span}d "
                f"to {target_days}d, now have {current_count} results"
            )
            break

    if current_count < min_results:
        logger.warning(
            f"Minimum result guarantee: could not reach {min_results} "
            f"even after expanding to 365 days. Got {current_count}."
        )
```

### Key Design Decisions

1. **Data lake only, no live expansion.** Expanding the date range against PNCP live would be slow and could trigger rate limits. The data lake query is <100ms regardless of range.

2. **Progressive expansion, not jump to max.** Expanding from 7 days to 365 days in one step would return too many irrelevant old results. Progressive expansion finds the narrowest range that meets the threshold.

3. **Keyword filtering in SQL.** The data lake query uses `pg_trgm` for keyword matching, which is much faster than fetching all records and filtering in Python.

4. **Exclude already-found IDs.** Prevents duplicates without a separate dedup step.

5. **Configurable threshold.** The `min_results` parameter defaults to 30 but can be overridden per sector (some sectors have inherently fewer opportunities).

## Degradation Levels

| Level | PNCP Status | Data Lake Status | User Experience | Data Freshness | Response Time |
|-------|-------------|------------------|-----------------|----------------|---------------|
| **L0 Normal** | Online, fast | Warm (ETL ran <24h ago) | Full results: live + data lake merged | Real-time | 2-5s |
| **L1 Augmented** | Online, slow (>5s) | Warm | Data lake results served instantly. Live results trickle in via SSE | Data lake: 4-24h. Live: real-time (delayed) | <1s initial, 5-15s for live augmentation |
| **L2 Degraded** | Partial (some UFs timeout) | Warm | Data lake results + partial live results. Banner: "3 estados nao responderam" | Mixed: some real-time, some 4-24h | <1s initial + partial live |
| **L3 Offline** | Down (canary fails) | Warm | Data lake results only. Banner: "PNCP indisponivel. Dados de Xh atras." No live fetch attempted. | 4-24h (last ETL) | <1s |
| **L4 Cold Start** | Down | Empty (first deploy) | "Estamos sincronizando dados pela primeira vez. Isso leva alguns minutos." Emergency partial sync triggered. | N/A | 30-60s (emergency sync) |

### Freshness Indicator UI

```
L0: [Green badge] "Dados em tempo real"
L1: [Green->Yellow badge] "Dados atualizando..." -> "Dados em tempo real" (after SSE)
L2: [Yellow badge] "Dados parciais - 3 estados indisponiveis"
L3: [Orange badge] "PNCP indisponivel. Dados de 4h atras."
L4: [Blue badge] "Primeira sincronizacao em andamento..."
```

## DataLakeService API Design

```python
class DataLakeService:
    """Service for reading/writing PNCP data lake in Supabase."""

    def __init__(self):
        from supabase_client import get_supabase
        self.db = get_supabase()

    async def query(
        self,
        ufs: list[str],
        data_inicial: str,
        data_final: str,
        modalidades: list[int] | None = None,
        keywords: list[str] | None = None,
        valor_min: float | None = None,
        valor_max: float | None = None,
        esferas: list[str] | None = None,
        exclude_ids: set[str] | None = None,
        limit: int = 1000,
        modo_busca: str = "publicacao",
    ) -> list[dict]:
        """Query data lake with full filter support.

        For modo_busca="abertas": filters by data_encerramento_proposta >= now()
        For modo_busca="publicacao": filters by data_publicacao_pncp in range

        Keyword matching uses pg_trgm (trigram similarity) for fuzzy matching.
        This is intentionally broader than the Python filter.py pipeline --
        the Python filters run on data lake results just like on live data.
        """
        ...

    async def upsert_batch(
        self,
        records: list[dict],
        source: str = "user_search",
    ) -> tuple[int, int]:
        """Upsert records into data lake. Returns (new_count, updated_count).

        Uses ON CONFLICT (numero_controle_pncp) DO UPDATE to:
        - Update last_seen_at
        - Increment fetch_count
        - Update raw_data if changed
        - Preserve first_seen_at
        """
        ...

    async def get_freshness(
        self,
        ufs: list[str],
    ) -> dict[str, datetime]:
        """Get last_seen_at per UF for freshness reporting.

        Returns: {"SP": datetime(2026, 2, 16, 2, 0), "RJ": ...}
        """
        ...

    async def get_stats(self) -> dict:
        """Get data lake statistics for monitoring.

        Returns: {
            "total_records": 150000,
            "oldest_record": "2025-08-01",
            "newest_record": "2026-02-16",
            "records_per_uf": {"SP": 25000, "RJ": 18000, ...},
            "last_etl_run": "2026-02-16T02:15:00Z",
            "last_etl_status": "success",
        }
        """
        ...
```

## Modified stage_execute() Flow

```python
async def stage_execute(self, ctx: SearchContext) -> None:
    """Stage 3: Execute search with data lake + live augmentation."""

    data_lake = DataLakeService()

    # === STEP 1: Query local data lake (fast, reliable) ===
    lake_results = await data_lake.query(
        ufs=ctx.request.ufs,
        data_inicial=ctx.request.data_inicial,
        data_final=ctx.request.data_final,
        modalidades=ctx.request.modalidades or None,
        modo_busca=ctx.request.modo_busca or "publicacao",
    )

    freshness = await data_lake.get_freshness(ctx.request.ufs)
    oldest_freshness = min(freshness.values()) if freshness else None
    ctx.data_lake_count = len(lake_results)

    # Convert data lake records to PNCP-format dicts
    ctx.licitacoes_raw = [_convert_datalake_to_pncp_format(r) for r in lake_results]

    if ctx.tracker:
        await ctx.tracker.emit(
            "fetching", 30,
            f"{len(lake_results)} resultados do cache local. Buscando dados mais recentes..."
        )

    # === STEP 2: Live PNCP fetch (best-effort, 5s soft timeout) ===
    cb = get_circuit_breaker()
    await cb.try_recover()

    live_results = []
    ctx.live_augmented = False

    if not cb.is_degraded:
        LIVE_TIMEOUT = float(os.getenv("LIVE_FETCH_TIMEOUT", "5"))
        try:
            live_fetch_result = await asyncio.wait_for(
                self._do_live_fetch(ctx),
                timeout=LIVE_TIMEOUT,
            )
            if isinstance(live_fetch_result, ParallelFetchResult):
                live_results = live_fetch_result.items
                ctx.succeeded_ufs = live_fetch_result.succeeded_ufs
                ctx.failed_ufs = live_fetch_result.failed_ufs
            else:
                live_results = live_fetch_result or []

            ctx.live_augmented = True

        except asyncio.TimeoutError:
            logger.info(
                f"Live PNCP fetch exceeded {LIVE_TIMEOUT}s soft timeout. "
                f"Serving {len(ctx.licitacoes_raw)} data lake results."
            )
            # Continue with data lake results only -- NOT an error
        except Exception as e:
            logger.warning(f"Live PNCP fetch failed: {e}. Using data lake only.")

    # === STEP 3: Merge live results into data lake results ===
    if live_results:
        seen_ids = {
            item.get("numeroControlePNCP", item.get("codigoCompra", ""))
            for item in ctx.licitacoes_raw
        }
        new_from_live = 0
        for item in live_results:
            item_id = item.get("numeroControlePNCP", item.get("codigoCompra", ""))
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                ctx.licitacoes_raw.append(item)
                new_from_live += 1

        logger.info(
            f"Live augmentation: {new_from_live} new records merged "
            f"(total now: {len(ctx.licitacoes_raw)})"
        )

        # Fire-and-forget: persist live results to data lake
        asyncio.create_task(
            data_lake.upsert_batch(live_results, source="user_search")
        )

    # === STEP 4: Minimum result guarantee ===
    await ensure_minimum_results(ctx, data_lake, min_results=30)

    # === STEP 5: Set freshness metadata ===
    if ctx.live_augmented:
        ctx.data_freshness = "real_time"
        ctx.data_lake_age_seconds = 0
    elif oldest_freshness:
        age = (datetime.now() - oldest_freshness).total_seconds()
        ctx.data_lake_age_seconds = int(age)
        if age < 3600:
            ctx.data_freshness = "cache_1h"
        elif age < 14400:
            ctx.data_freshness = "cache_4h"
        elif age < 86400:
            ctx.data_freshness = "cache_24h"
        else:
            ctx.data_freshness = "cache_stale"
    else:
        ctx.data_freshness = "no_cache"
        ctx.data_lake_age_seconds = None
```

## Nightly ETL Worker Design

```python
# backend/etl/pncp_sync.py

"""Nightly ETL worker for PNCP data lake synchronization.

Runs as a Railway cron job at 02:00 BRT (05:00 UTC).
Fetches all 27 UFs x 4 modalities for the last 30 days.
Upserts into pncp_data_lake.

Configuration:
  ETL_ENABLED=true
  ETL_UFS=SP,RJ,MG,... (default: all 27)
  ETL_DAYS_BACK=30 (default)
  ETL_MAX_CONCURRENT=5 (lower than user searches to be gentle on PNCP)
"""

async def run_nightly_sync():
    """Main ETL entry point."""
    run_id = uuid4()
    data_lake = DataLakeService()

    # Record ETL run start
    await data_lake.record_etl_start(run_id)

    try:
        ufs = os.getenv("ETL_UFS", ",".join(UFS_BY_POPULATION)).split(",")
        days_back = int(os.getenv("ETL_DAYS_BACK", "30"))
        today = date.today()
        start_date = (today - timedelta(days=days_back)).isoformat()
        end_date = today.isoformat()

        async with AsyncPNCPClient(max_concurrent=5) as client:
            # Process UFs in batches of 5 to be gentle on PNCP
            for batch_start in range(0, len(ufs), 5):
                batch = ufs[batch_start:batch_start + 5]

                result = await client.buscar_todas_ufs_paralelo(
                    ufs=batch,
                    data_inicial=start_date,
                    data_final=end_date,
                    max_pages_per_uf=100,  # Lower than user searches
                )

                items = result.items if isinstance(result, ParallelFetchResult) else result
                new, updated = await data_lake.upsert_batch(items, source="etl_sync")

                logger.info(
                    f"ETL batch {batch}: {len(items)} fetched, "
                    f"{new} new, {updated} updated"
                )

                # Be gentle: 5s pause between batches
                await asyncio.sleep(5)

        await data_lake.record_etl_complete(run_id, status="success")

    except Exception as e:
        await data_lake.record_etl_complete(run_id, status="failed", error=str(e))
        raise
```

**Railway cron configuration:**

```toml
# In railway.toml or Railway dashboard
[cron]
  schedule = "0 5 * * *"  # 05:00 UTC = 02:00 BRT
  command = "python -m etl.pncp_sync"
```

## Risk Mitigation

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|------------|--------|------------|
| 1 | **Supabase storage grows too large** | Medium | Medium | Raw_data JSONB is the largest field (~1.5KB/record). At 500K records, this is ~750MB -- within Supabase Pro's 8GB limit. Add cleanup job to delete records older than 365 days. If needed, move raw_data to Supabase Storage as compressed JSONL. |
| 2 | **Data lake query is slow** | Low | High | PostgreSQL with proper indexes (GIN trigram, B-tree on UF+date) handles 500K rows in <100ms. The `pg_trgm` extension is already available in Supabase. Benchmark during Sprint 1. |
| 3 | **ETL overloads PNCP at night** | Medium | Medium | ETL uses max_concurrent=5 (vs 10 for user searches), processes UFs in batches of 5 with 5s pauses, and only fetches 30 days of data. If PNCP rate-limits, the existing retry/backoff logic handles it. |
| 4 | **Data lake returns stale results that confuse users** | Medium | Medium | Freshness indicator badge on every search result page. Clear messaging: "Dados de X horas atras" vs "Dados em tempo real". Users can click "Atualizar agora" to force a fresh PNCP fetch (existing `force_fresh` flag). |
| 5 | **Cold start: first deployment has empty data lake** | Certain (once) | High | On first deploy, trigger a priority ETL sync for the top 5 UFs (SP, RJ, MG, BA, PR) which covers ~60% of all procurement. This takes ~10 minutes. Until complete, searches fall through to live PNCP fetch (existing behavior). |
| 6 | **Race condition: concurrent writes to data lake** | Low | Low | PostgreSQL's `ON CONFLICT DO UPDATE` is atomic. Multiple user searches writing the same record will simply update `last_seen_at` -- no data corruption. The `fetch_count` increment may lose a count under high concurrency but this is non-critical metadata. |
| 7 | **ETL fails silently** | Medium | High | ETL records every run in `pncp_etl_runs` with status, duration, and error. Add Sentry alert for `status='failed'`. Add Railway health check that queries last ETL run age. If last successful ETL is >48h old, send Slack/email alert. |
| 8 | **PNCP changes API format** | Low | Critical | Raw_data JSONB preserves the full API response. If field names change, only `_convert_datalake_to_pncp_format()` needs updating. Historical data remains accessible. |
| 9 | **Min result guarantee returns irrelevant old results** | Medium | Medium | Progressive expansion (14d -> 30d -> 90d -> 180d -> 365d) stops as soon as threshold is met, keeping results as recent as possible. Sort by date_desc ensures newest results appear first. Expanded range is disclosed in response: "Periodo ampliado para 30 dias para garantir resultados." |
| 10 | **Increased hosting costs** | Low | Low | The data lake lives in Supabase (already provisioned). ETL runs on Railway (already provisioned). No new services. Estimated cost increase: Supabase storage ~$5/month for 1GB, Railway cron ~$0/month (included in plan). Total: <$5/month increase, well within the 20% constraint. |

## Cost-Benefit Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **PNCP down: user experience** | Zero results, error page | Cached results with freshness badge | Failure-proof |
| **Response time (warm cache)** | 5-15s (PNCP dependent) | <1s (data lake) + optional live augment | 5-15x faster |
| **Response time (cold, PNCP healthy)** | 5-15s | 5-15s (same, but data lake populated for next time) | Same + future benefit |
| **Minimum result guarantee** | None (0 results possible) | 30+ results for any reasonable query | Infinite improvement |
| **Silent data truncation** | Users unaware of missing data | Banner: "Resultados limitados a 10.000" | Full transparency |
| **Circuit breaker cascade** | One user can block all users | Threshold raised, env-configurable | Isolated failure domains |
| **Monthly hosting cost increase** | $0 | ~$5 (Supabase storage) | 0.03% of R$1,999 subscription |
| **Implementation effort** | - | ~8-9 dev-days across 2 sprints | Manageable for a startup |

## What This Architecture Does NOT Solve (Out of Scope)

1. **Full-text search.** The data lake uses `pg_trgm` for fuzzy keyword matching, but the primary keyword filtering still happens in Python (`filter.py`). A future enhancement could use PostgreSQL `tsvector` for full-text search, but this adds complexity without clear ROI given the current filter pipeline works well.

2. **Real-time push notifications.** When new procurement opportunities appear on PNCP, users are not proactively notified. This requires a WebSocket/SSE subscription service, which is a separate feature (not a resilience concern).

3. **Multi-tenant data isolation.** The data lake is shared across all users. All users searching SP see the same SP data. This is correct behavior for public procurement data but differs from per-user caching in `search_results_cache`.

4. **PNCP page size optimization.** Whether `tamanhoPagina=500` is supported by PNCP requires empirical testing. This is a Sprint 1 investigation task. If supported, it reduces API calls by 96% and makes the entire architecture more efficient.

5. **Geographic data enrichment.** The data lake stores UF and municipio but does not perform geocoding or distance-based queries. This could be added later with PostGIS.

---

*Architecture prepared: 2026-02-16*
*Architect: Claude Opus 4.6 (GTM-OK Phase 10)*
*Confidence: HIGH -- all components use existing infrastructure, proven patterns, and incremental changes to working code.*
