# D01/D04 Evidence: Multi-Source Pipeline Architecture Analysis

**Date:** 2026-02-17
**Analyst:** @architect (Phase 1 GTM-OK v2.0)
**Scope:** End-to-end data flow for PNCP + Portal de Compras Publicas (PCP) multi-source search

---

## 1. Architecture Overview

### Source Configuration

The system supports 8 data sources via `source_config/sources.py`:

| Source | Priority | Auth | Default Enabled |
|--------|----------|------|-----------------|
| PNCP | 1 (highest) | None (open) | Yes |
| Portal de Compras (PCP) | 2 | publicKey param | Yes |
| Licitar Digital | 3 | API key | Yes |
| ComprasGov | 4 | None (open) | Yes |
| Portal Transparencia | 3 | API key | No |
| BLL Compras | 4 | API key | No |
| BNC | 5 | API key | No |
| Querido Diario | 5 | None (open) | No |

**Critical gate:** Multi-source is only active when `ENABLE_MULTI_SOURCE=true` environment variable is set. Default is `"false"`. This means the production system currently runs in PNCP-only mode unless explicitly enabled.

### Data Flow Paths

```
                     ENABLE_MULTI_SOURCE?
                     /               \
                   false             true
                   /                   \
        _execute_pncp_only()    _execute_multi_source()
               |                         |
   buscar_todas_ufs_paralelo()   ConsolidationService.fetch_all()
               |                   /          |          \
       raw PNCP dicts        PNCP         PCP       ComprasGov
       (preserve all         Adapter      Adapter    (fallback)
        API fields)             |            |
                          UnifiedProcurement objects
                                    |
                          to_legacy_format()  <-- DATA LOSS HERE
                                    |
                            legacy dict format
                                    |
                            deduplication
                                    |
                  ctx.licitacoes_raw (merged list)
                                    |
                        aplicar_todos_filtros()
                                    |
                      licitacoes_filtradas + stats
```

---

## 2. PNCP Client (Primary Source) -- `pncp_client.py`

### Resilience Mechanisms

| Mechanism | Implementation | Status |
|-----------|---------------|--------|
| Retry with backoff | 5 retries, 2s base, 2x exponential, 60s cap, +/-50% jitter | WORKING |
| Rate limiting | 100ms min interval (10 req/s) | WORKING |
| Circuit breaker | Per-source singletons (PNCP: threshold=50, PCP: threshold=30, 120s cooldown) | WORKING |
| Health canary | Lightweight SP/mod-6 probe before full search, 5s timeout | WORKING |
| Per-modality timeout | 15s default, 1 retry with 3s backoff | WORKING |
| Per-UF timeout | 30s normal, 45s degraded mode | WORKING |
| UF retry | Failed UFs retried once after 5s, 45s timeout | WORKING |
| Degraded mode | Reduced concurrency (3 UFs), priority-ordered by population | WORKING |
| Date chunking | Splits ranges >30 days into 30-day chunks | WORKING |
| Content-type validation | Verifies JSON content-type before parsing | WORKING |
| JSON parse error handling | Retries on invalid JSON | WORKING |
| 429 handling | Respects Retry-After header | WORKING |
| Request-ID tracing | Forwards X-Request-ID to PNCP | WORKING |

### Pagination

- Page size: 20 items per page (PNCP API default)
- Max pages per UF/modality: 500 (= 10,000 records per combination)
- Pagination field: `paginasRestantes` (remaining pages count)
- Deduplication: In-memory `seen_ids` set per `numeroControlePNCP`

### Truncation Detection (GTM-FIX-004)

When `max_pages` is reached while `paginasRestantes > 0`, the system:
1. Sets `was_truncated = True` on the `ParallelFetchResult`
2. Records which UFs were truncated
3. Propagates `is_truncated`, `truncated_ufs`, and `truncation_details` to `SearchContext`
4. Frontend displays `TruncationWarningBanner`

**Verdict:** PNCP client is production-quality. Well-tested (32+ tests), comprehensive error handling.

---

## 3. PCP Client (Secondary Source) -- `clients/portal_compras_client.py`

### Implementation

| Feature | Implementation | Status |
|---------|---------------|--------|
| Auth | `publicKey` URL parameter | WORKING |
| Retry | 3 retries with exponential backoff (2^n * jitter) | WORKING |
| Rate limiting | 200ms between requests (5 req/s) | WORKING |
| Pagination | Via `quantidadeTotal` field, calculated page count | WORKING |
| Date conversion | ISO (YYYY-MM-DD) to BR (DD/MM/AAAA) via `date_parser.py` | WORKING |
| Value calculation | Sums `VL_UNITARIO_ESTIMADO * QT_ITENS` across lots/items | WORKING |
| Health check | Minimal query (UF=SP, page 1) with 5s timeout | WORKING |
| Object enrichment | Concatenates `DS_OBJETO` + all `DS_ITEM` for keyword matching | WORKING |
| Truncation | Hard limit at page 100 (5,000 records) | WORKING |
| Error handling | Auth errors (401/403), rate limits (429), server errors (5xx) | WORKING |

### Page Limit

PCP has a hard page limit of 100 pages. If `quantidadeTotal` exceeds this, results are truncated and `was_truncated` is set. This is lower than PNCP's 500-page limit.

**Verdict:** PCP client is well-implemented with proper error handling and normalization.

---

## 4. Consolidation Service -- `consolidation.py`

### Orchestration

The `ConsolidationService` runs all source adapters in parallel via `asyncio.gather` with:

1. **Per-source timeouts:** Default 25s (configurable via `CONSOLIDATION_TIMEOUT_PER_SOURCE`, env default=50s)
2. **Global timeout:** Default 60s (configurable via `CONSOLIDATION_TIMEOUT_GLOBAL`, env default=120s)
3. **Health-aware timeout adjustment:** When PNCP is degraded, alternative sources get 40s timeout and global timeout increases to 90s
4. **Partial result salvage:** On timeout, records already yielded by the async generator are preserved with status `"partial"` instead of being discarded entirely. This is a strong design.

### Deduplication

**Algorithm:** Priority-based dedup on `dedup_key` field.

```python
dedup_key = f"{cnpj_digits}:{numero_edital}:{ano}"
# Fallback: f"{cnpj_digits}:{md5(normalized_objeto)[:12]}:{int(valor)}"
```

- PNCP priority=1 (wins), PCP priority=2
- Value discrepancy logging: warns when same procurement has >5% value difference across sources
- Records with no `dedup_key` are always included (keyed by object ID)

**Concern:** The fallback dedup key uses `md5(objeto)[:12]` + `int(valor)`. Two genuinely different procurements with the same CNPJ, similar descriptions, and same integer value would collide. However, the 12-char MD5 prefix makes this unlikely in practice.

### Fallback Cascade

```
Primary sources (PNCP + PCP) in parallel
          |
          v (all fail?)
ComprasGov last-resort adapter (40s timeout)
          |
          v (also fails?)
AllSourcesFailedError raised
          |
          v (caught in search_pipeline.py)
Supabase stale cache query
          |
          v (no cache?)
Empty results with degradation_reason
```

This 4-level cascade is well-designed. ComprasGov as a fallback is only tried when it was NOT already included as a primary adapter, preventing duplicate attempts.

---

## 5. CRITICAL BUG: `to_legacy_format()` Data Loss

### Finding

**File:** `backend/clients/base.py`, lines 255-283
**Severity:** HIGH -- affects data completeness in multi-source mode

The `UnifiedProcurement.to_legacy_format()` method is missing critical field mappings:

| UnifiedProcurement Field | Expected Legacy Key | Actually Mapped? |
|--------------------------|-------------------|-----------------|
| `source_id` | `numeroControlePNCP`, `codigoCompra` | YES |
| `objeto` | `objetoCompra` | YES |
| `valor_estimado` | `valorTotalEstimado` | YES |
| `orgao` | `nomeOrgao` | YES |
| `cnpj_orgao` | `cnpjOrgao` | YES |
| `uf` | `uf` | YES |
| `municipio` | `municipio` | YES |
| `data_publicacao` | `dataPublicacaoPncp` | YES |
| `data_abertura` | `dataAberturaProposta` | YES |
| `modalidade` | `modalidadeNome` | YES |
| `situacao` | `situacaoCompraNome` | YES |
| `link_edital` | `linkSistemaOrigem` | YES |
| `link_portal` | `linkProcessoEletronico` | YES |
| **`data_encerramento`** | **`dataEncerramentoProposta`** | **NO -- MISSING** |
| **`esfera`** | **`esferaId`** | **NO -- MISSING** |
| **`poder`** | **N/A (not used by filter)** | **NO -- MISSING** |
| **`numero_edital`** | **`numeroEdital`** | **NO -- MISSING** |
| **`ano`** | **`anoCompra`** | **NO -- MISSING** |

### Impact Analysis

**1. `dataEncerramentoProposta` missing:**
- `filtrar_por_prazo_aberto()` at filter.py:1706 checks `lic.get("dataEncerramentoProposta")` -- will be `None` for ALL multi-source records
- Status inference (`status_inference.py:88`) checks `dataEncerramentoProposta` -- will return `None`
- `_calcular_dias_restantes()` in search_pipeline.py:177 checks `dataEncerramentoProposta` -- urgency will be `None`
- **Result:** In multi-source mode, ALL records (from both PNCP and PCP) lose deadline data. The "abertas" (open) filter mode will not correctly filter expired bids. Urgency badges will not appear on the frontend.

**2. `PNCPLegacyAdapter.fetch()` also drops PNCP encerramento data:**
- At pncp_client.py:1588-1603, the adapter creates `UnifiedProcurement` but does NOT set `data_encerramento` or `data_publicacao` from the PNCP raw fields
- This means even PNCP data in multi-source mode loses these fields

**3. `esferaId` missing:**
- `filtrar_por_esfera()` at filter.py:1248 checks `esferaId` or `esfera` -- will be empty for multi-source records
- **Result:** Esfera filter effectively becomes a no-op. All records pass through regardless of the user's esfera selection. However, the filter is conservative (missing field = include), so this causes false positives rather than data loss.

**4. `numeroEdital` missing:**
- Used for display in Excel output
- Missing from legacy format means Excel columns may be empty for PCP records

### Scope of Impact

This bug ONLY manifests when `ENABLE_MULTI_SOURCE=true`. In the default PNCP-only path, raw API dicts preserve all fields naturally. The bug is latent -- it exists in the code but is not currently affecting production if multi-source is not enabled.

---

## 6. Cache Strategy (GTM-FIX-010) -- `search_cache.py`

### Two-Level Cache Architecture

| Level | Storage | TTL | Use Case |
|-------|---------|-----|----------|
| L1: InMemoryCache | In-process dict (`redis_pool.py` fallback) | 4 hours | Proactive: serve fresh results without API call |
| L2: Supabase | `search_results_cache` table | 24 hours (6h fresh, 6-24h stale) | Resilience: serve when ALL live sources fail |

### Cache Key

```python
params = {
    "setor_id": ...,
    "ufs": sorted(...),
    "status": ...,
    "modalidades": sorted(...) or None,
    "modo_busca": ...,
}
hash = sha256(json.dumps(params, sort_keys=True))
```

**Note:** Dates are intentionally excluded from the cache key. This is documented as intentional -- "stale cache should serve regardless of date range since it's better than nothing when all sources are down." This is a reasonable trade-off for a failover cache.

### Cache Write Policy

- **Write-through:** After successful fetch, results are written to both L1 (InMemory) and L2 (Supabase)
- **L2 uses UPSERT** on `(user_id, params_hash)` -- prevents unbounded growth
- **Non-blocking:** Cache write failures are logged and ignored (never block the response)
- **Source tracking:** `sources_json` field records which sources contributed to the cached result (AC8r)

### Cache Read Policy

- **L1 checked first** (fast, in-process)
- **L2 only on failure cascade** (all sources failed, or PNCP degraded)
- **Freshness tiering:**
  - 0-6 hours: Fresh (served directly)
  - 6-24 hours: Stale (served only when live sources fail, with `cached=true` flag)
  - >24 hours: Expired (not served, returns `None`)
- **`cached_sources` propagated** to frontend for display

### Cache Concerns

1. **User-scoped cache:** Cache is keyed by `(user_id, params_hash)`. Two users with identical search parameters get separate cache entries. This prevents cross-user data leakage but reduces cache hit rate.

2. **Cache coherence:** When `force_fresh=True`, the InMemory cache is bypassed but Supabase cache is NOT cleared. Old stale entries persist until TTL expiry. This is acceptable for a failover cache.

3. **Cache size:** No explicit size limits on InMemory cache. For high-volume production, this could grow unbounded in a long-lived process. The 4-hour TTL provides some natural cleanup.

---

## 7. Failure Mode Analysis

### Single-Source Failures

| Scenario | Code Path | What Happens | User Impact |
|----------|-----------|--------------|-------------|
| **(a) PNCP 500, PCP works** | `_wrap_source` catches exception, returns `status="error"` for PNCP. PCP records deduped alone. | `is_partial=true`, degradation banner shown. PCP results displayed. | Moderate -- fewer results but functional |
| **(b) PCP 500, PNCP works** | Same pattern. PCP status="error", PNCP records returned normally. | `is_partial=true`, degradation banner. PNCP results displayed. | Minimal -- primary source unaffected |
| **(c) PNCP timeout, PCP fast** | `_wrap_source` catches `TimeoutError`. Partial records salvaged if generator yielded any before timeout. PCP returns fully. | Partial PNCP + full PCP. `is_partial=true`. | Moderate -- some PNCP data may be salvaged |
| **(d) PCP timeout, PNCP fast** | Same pattern reversed. PNCP returns fully, PCP partial/empty. | PNCP results complete, PCP partial. | Minimal |

### Cross-Source Failures

| Scenario | Code Path | What Happens | User Impact |
|----------|-----------|--------------|-------------|
| **(e) Both return 500** | Both sources fail -> ComprasGov fallback tried -> if that fails -> `AllSourcesFailedError` -> Supabase cache queried -> stale results or empty | If cache exists: stale data with `cached=true`. If no cache: empty results with degradation reason. | Significant -- user gets stale or no data |
| **(f) Both timeout** | Global timeout fires. Partial records salvaged from both. If none salvaged -> fallback cascade. | Same as (e) but partial salvage possible. | Significant |
| **(g) PNCP empty, PCP has results** | PNCP returns 0 records (not an error). PCP records returned. `is_partial=false` (no failures). | PCP results displayed normally. | None -- working as designed |
| **(h) PNCP has results, PCP empty** | PCP returns 0 records. PNCP results returned. | PNCP results displayed. | None |

### Dedup & Prioritization

| Scenario | Code Path | What Happens | Concern |
|----------|-----------|--------------|---------|
| **(i) Same bid in both sources** | `_deduplicate` matches on `dedup_key` (cnpj:edital:ano). PNCP version kept (priority=1). | Correct dedup. Value discrepancy logged if >5%. | **Dedup depends on both sources having matching CNPJ + edital number + year.** If PCP uses different edital numbering, dedup may miss duplicates. |
| **(j) Value discrepancies** | Logged as WARNING when >5% difference. Higher-priority source's value kept. | Warning logged but no action taken. | Acceptable -- logging provides visibility |
| **(k) Cross-source pagination** | Each source paginates independently. Results merged after both complete. | N/A -- sources don't share pagination state. | Correct design |

---

## 8. Data Completeness Analysis

### Per-Source Max Results

| Source | Page Size | Max Pages | Max Records/UF | 27 UFs Max |
|--------|-----------|-----------|----------------|------------|
| PNCP | 20 | 500 | 10,000/modality, ~40,000/UF (4 modalities) | ~1,080,000 |
| PCP | 50 | 100 | 5,000/UF | ~135,000 |
| ComprasGov | 500 | N/A (fallback only) | N/A | N/A |

### Truncation Behavior

- **PNCP:** Truncation detected per-UF-per-modality. `truncated_ufs` list propagated to frontend. User sees banner.
- **PCP:** Truncation detected at page 100 limit. `was_truncated` flag set on adapter.
- **Multi-source:** Per-source truncation flags merged into `truncation_details` dict (e.g., `{"pncp": true, "portal_compras": false}`).

### Result Guarantee

There is NO minimum result guarantee. If all sources fail and no cache exists, the user gets 0 results with a degradation message. This is acceptable for a resilience-first design -- returning incorrect/fabricated data would be worse.

---

## 9. Scoring

### D01: Core Value Delivery -- Score: 6/10

**Justification:**

**Strengths (+):**
- PNCP client is excellent: 5 retry levels, circuit breaker, health canary, per-modality timeouts, UF retry, degraded mode
- Multi-source architecture is well-designed with proper adapter interface, parallel execution, and partial result salvage
- 4-level fallback cascade (primary -> partial -> ComprasGov -> cache) ensures maximum data availability
- Truncation detection and user notification is thorough
- Filtering pipeline is comprehensive with fail-fast optimization
- Dedup with priority and value discrepancy monitoring
- 92+ backend tests for PCP, 32+ for PNCP, 25 for date parser

**Weaknesses (-):**
- **CRITICAL:** `to_legacy_format()` drops `dataEncerramentoProposta` -- deadline filtering and urgency badges broken in multi-source mode
- **CRITICAL:** `PNCPLegacyAdapter` also drops `data_encerramento` and `data_publicacao` when wrapping PNCP data -- even PNCP records lose these fields in multi-source path
- `ENABLE_MULTI_SOURCE` defaults to `false` -- multi-source is effectively dead code unless explicitly enabled
- `esferaId` missing from legacy format means esfera filter is a no-op in multi-source mode (false positives)
- `numeroEdital` missing from legacy format means Excel reports have empty edital columns for non-PNCP records

**The core PNCP-only path works well (would be 7-8/10). The multi-source path has a significant data integrity bug that drops deadline data for ALL records, breaking the "abertas" filter mode and urgency classification. Since multi-source is not enabled by default, the actual production impact is limited today, but the feature cannot be safely activated without fixing `to_legacy_format()`.**

### D04: Data Reliability -- Score: 5/10

**Justification:**

**Strengths (+):**
- Deterministic dedup with priority resolution
- Cross-source value discrepancy monitoring (>5% warning)
- SWR cache with proper freshness tiering (fresh/stale/expired)
- `cached_sources` tracking tells the user exactly which sources contributed
- Non-blocking cache writes (never fail the search)
- Filter stats provide full transparency on why bids were rejected

**Weaknesses (-):**
- **CRITICAL:** `to_legacy_format()` data loss means multi-source records are unreliable for deadline-sensitive queries
- Dedup fallback key uses `md5(objeto)[:12]` + `int(valor)` -- risk of false dedup when CNPJ + description hash + rounded value match across genuinely different procurements (low probability but non-zero)
- Cache is user-scoped (`user_id + params_hash`) -- no cross-user benefit, low cache hit rate in early stage
- No validation that PCP `publicKey` is actually valid at startup (only fails at query time)
- No data freshness indicator per-record (only per-search `cached_at`)
- `esferaId` not mapped -- esfera filter silently becomes inclusive in multi-source mode (data quality issue: users may see results outside their selected government sphere)
- Status inference depends on `dataEncerramentoProposta` which is missing in multi-source mode -- all records will have `_status_inferido = None`

**The reliability of the PNCP-only path is solid (would be 7/10). Multi-source mode introduces a systematic field mapping gap that silently degrades data quality. The cache strategy is well-designed for resilience. The dedup algorithm is sound but could benefit from a more robust key strategy.**

---

## 10. Remediation Recommendations

### P0: Fix `to_legacy_format()` (4 hours)

Add the missing field mappings to `backend/clients/base.py`:

```python
def to_legacy_format(self) -> Dict[str, Any]:
    return {
        # ... existing fields ...
        "dataEncerramentoProposta": (
            self.data_encerramento.isoformat() if self.data_encerramento else None
        ),
        "esferaId": self.esfera,
        "poderNome": self.poder,
        "numeroEdital": self.numero_edital,
        "anoCompra": self.ano,
    }
```

### P0: Fix `PNCPLegacyAdapter.fetch()` (2 hours)

Add missing field extractions in `pncp_client.py`:

```python
yield UnifiedProcurement(
    # ... existing fields ...
    data_publicacao=self._parse_iso_datetime(item.get("dataPublicacaoPncp")),
    data_encerramento=self._parse_iso_datetime(item.get("dataEncerramentoProposta")),
    esfera=item.get("esferaId", ""),
    poder=item.get("poderNome", ""),
    numero_edital=item.get("numeroEdital", ""),
    ano=str(item.get("anoCompra", "")),
)
```

### P1: Enable multi-source by default (1 hour)

Change `ENABLE_MULTI_SOURCE` default from `"false"` to `"true"` in `search_pipeline.py:501` once P0 fixes are verified.

### P2: Cross-user cache sharing (4 hours)

Remove `user_id` from cache key for searches that are not user-specific. This dramatically increases cache hit rate.

### P3: Startup credential validation (1 hour)

Validate PCP API key at startup (make a health check call) rather than discovering auth failures at query time.

---

## 11. Test Coverage Summary

| Module | Tests | Status |
|--------|-------|--------|
| `pncp_client.py` | 32+ | PASSING |
| `portal_compras_client.py` | 51 | PASSING |
| `consolidation.py` | 16 | PASSING |
| `date_parser.py` | 25 | PASSING |
| `search_cache.py` | 19 | PASSING |
| `filter.py` | 48+ | PASSING |
| Frontend cache/source UI | 14 | PASSING |
| `to_legacy_format()` data loss | 0 | **NO TESTS** |

**The critical `to_legacy_format()` bug has zero test coverage.** No integration test verifies that multi-source records retain `dataEncerramentoProposta` after the consolidation pipeline.

---

## 12. Files Analyzed

| File | Path | Lines |
|------|------|-------|
| Search Pipeline | `backend/search_pipeline.py` | 1463 |
| PNCP Client | `backend/pncp_client.py` | 1658 |
| PCP Client | `backend/clients/portal_compras_client.py` | 576 |
| Base Adapter | `backend/clients/base.py` | 389 |
| Consolidation | `backend/consolidation.py` | 598 |
| Search Cache | `backend/search_cache.py` | 147 |
| Search Context | `backend/search_context.py` | 81 |
| Source Config | `backend/source_config/sources.py` | 615 |
| Filter Engine | `backend/filter.py` | ~2500 |
| ComprasGov Client | `backend/clients/compras_gov_client.py` | (reviewed) |
