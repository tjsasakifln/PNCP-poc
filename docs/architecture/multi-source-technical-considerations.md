# Multi-Source Consolidation: Technical Considerations

**Date:** 2026-02-03
**Author:** @architect (Aria)
**Status:** Proposed

---

## Table of Contents

1. [Source Failure Handling](#1-source-failure-handling)
2. [Timeout Strategy](#2-timeout-strategy)
3. [Caching Strategy](#3-caching-strategy)
4. [Deduplication Algorithm](#4-deduplication-algorithm)
5. [Performance Considerations](#5-performance-considerations)
6. [Observability](#6-observability)
7. [Security Considerations](#7-security-considerations)
8. [Migration Strategy](#8-migration-strategy)

---

## 1. Source Failure Handling

### 1.1 Philosophy: Graceful Degradation

The consolidation service follows a **graceful degradation** model:
- Partial results are better than no results
- One failing source should not impact others
- Users should be informed about incomplete data

### 1.2 Failure Scenarios and Handling

| Scenario | Detection | Action | User Notification |
|----------|-----------|--------|-------------------|
| Source timeout | `asyncio.TimeoutError` | Skip source, continue | Warning in response |
| Source 5xx error | HTTP status code | Retry 3x, then skip | Warning in response |
| Source 4xx error | HTTP status code | Skip immediately | Warning in response |
| Source rate limit | HTTP 429 | Retry with `Retry-After` | None if succeeds |
| Source parse error | Exception in `normalize()` | Log, skip record | Debug log only |
| All sources fail | No successful results | Raise `ConsolidationError` | HTTP 502 |
| Network partition | Connection timeout | Skip source | Warning in response |

### 1.3 Implementation Pattern

```python
async def _fetch_with_resilience(
    self,
    adapter: SourceAdapter,
    data_inicial: str,
    data_final: str,
    ufs: Optional[Set[str]],
) -> Tuple[List[UnifiedProcurement], Optional[str]]:
    """
    Fetch from a single source with comprehensive error handling.

    Returns:
        Tuple of (records, error_message)
        - On success: (records, None)
        - On failure: ([], error_message)
    """
    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            async with asyncio.timeout(self.config.timeout_per_source):
                records = []
                async for record in adapter.fetch(data_inicial, data_final, ufs):
                    records.append(record)
                return records, None

        except asyncio.TimeoutError:
            last_error = f"Timeout after {self.config.timeout_per_source}s"
            logger.warning(f"{adapter.code}: {last_error} (attempt {attempt + 1})")
            # Don't retry timeouts - source is likely overloaded
            break

        except SourceRateLimitError as e:
            wait_time = e.retry_after or (2 ** attempt * 5)
            logger.warning(f"{adapter.code}: Rate limited, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            continue

        except SourceAPIError as e:
            if e.status_code >= 500:
                last_error = f"Server error: HTTP {e.status_code}"
                logger.warning(f"{adapter.code}: {last_error} (attempt {attempt + 1})")
                await asyncio.sleep(2 ** attempt)
                continue
            else:
                # 4xx errors - don't retry
                last_error = f"Client error: HTTP {e.status_code}"
                logger.error(f"{adapter.code}: {last_error}")
                break

        except Exception as e:
            last_error = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.exception(f"{adapter.code}: {last_error}")
            break

    return [], last_error
```

### 1.4 Partial Results Response

When some sources fail, the response includes:

```json
{
  "resumo": { "..." },
  "total_raw": 523,
  "total_filtrado": 15,
  "source_stats": {
    "PNCP": { "count": 300, "duration_ms": 4500, "status": "available" },
    "BLL": { "count": 223, "duration_ms": 3200, "status": "available" }
  },
  "source_errors": {
    "Portal": "Timeout after 30s",
    "BNC": "Server error: HTTP 503"
  },
  "consolidation_warning": "2 of 4 sources failed. Results may be incomplete. Partial data from: PNCP, BLL"
}
```

---

## 2. Timeout Strategy

### 2.1 Timeout Hierarchy

```
Global Request Timeout (60s)
|
+-- Consolidation Phase (55s)
|   |
|   +-- Source 1 (30s) ----+
|   +-- Source 2 (30s) ----+-- Parallel execution
|   +-- Source 3 (30s) ----+
|   +-- Source N (30s) ----+
|
+-- Post-Processing (5s)
    +-- Deduplication
    +-- Filtering
    +-- LLM Summary
    +-- Excel Generation
```

### 2.2 Per-Source Timeout Configuration

| Source | Connect | Read | Total | Rationale |
|--------|---------|------|-------|-----------|
| PNCP | 5s | 25s | 30s | Government API, variable response times |
| BLL | 5s | 20s | 25s | Commercial API, faster |
| Portal | 5s | 25s | 30s | Federal systems, potentially slow |
| BNC | 5s | 15s | 20s | Private sector, typically fast |
| Licitar | 5s | 15s | 20s | Municipal focus, smaller dataset |

### 2.3 Adaptive Timeout Strategy

```python
@dataclass
class AdaptiveTimeoutConfig:
    """Timeout configuration that adapts based on historical performance."""

    base_timeout: int = 30
    min_timeout: int = 10
    max_timeout: int = 60

    # Historical performance tracking
    recent_durations: List[int] = field(default_factory=list)
    max_history: int = 100

    def calculate_timeout(self) -> int:
        """Calculate timeout based on recent performance."""
        if not self.recent_durations:
            return self.base_timeout

        # Use 95th percentile + 20% buffer
        sorted_durations = sorted(self.recent_durations)
        p95_index = int(len(sorted_durations) * 0.95)
        p95_duration = sorted_durations[p95_index]

        timeout = int(p95_duration * 1.2 / 1000)  # Convert ms to seconds
        return max(self.min_timeout, min(self.max_timeout, timeout))

    def record_duration(self, duration_ms: int):
        """Record a successful fetch duration."""
        self.recent_durations.append(duration_ms)
        if len(self.recent_durations) > self.max_history:
            self.recent_durations.pop(0)
```

### 2.4 Early Termination

If the global timeout is approaching, stop waiting for slow sources:

```python
async def fetch_with_global_deadline(self, deadline: datetime):
    """Fetch with respect to global deadline."""
    remaining_time = (deadline - datetime.utcnow()).total_seconds()

    if remaining_time < 5:
        # Not enough time, skip this source
        return [], "Skipped: insufficient time remaining"

    effective_timeout = min(self.config.timeout_per_source, remaining_time - 2)
    async with asyncio.timeout(effective_timeout):
        return await self._fetch_records()
```

---

## 3. Caching Strategy

### 3.1 Cache Architecture

```
+------------------+     +------------------+     +------------------+
|   L1: Request    |     |   L2: Redis      |     |   L3: Source     |
|   (in-memory)    |---->|   (shared)       |---->|   (authoritative)|
+------------------+     +------------------+     +------------------+
     TTL: request           TTL: 5 min             TTL: N/A
     Scope: single          Scope: cluster         Scope: external
```

### 3.2 Cache Key Design

```python
def generate_cache_key(
    source_code: str,
    data_inicial: str,
    data_final: str,
    ufs: Optional[Set[str]],
) -> str:
    """
    Generate deterministic cache key.

    Format: source:{code}:{date_range}:{ufs_hash}
    """
    ufs_str = ",".join(sorted(ufs)) if ufs else "ALL"
    return f"source:{source_code}:{data_inicial}:{data_final}:{ufs_str}"


def generate_consolidated_cache_key(
    data_inicial: str,
    data_final: str,
    ufs: Optional[Set[str]],
    sources: Optional[Set[str]],
) -> str:
    """Cache key for consolidated results."""
    ufs_str = ",".join(sorted(ufs)) if ufs else "ALL"
    sources_str = ",".join(sorted(sources)) if sources else "ALL"
    return f"consolidated:{data_inicial}:{data_final}:{ufs_str}:{sources_str}"
```

### 3.3 Cache TTL Strategy

| Cache Type | TTL | Rationale |
|------------|-----|-----------|
| Source raw data | 5 minutes | PNCP updates ~hourly, balance freshness |
| Consolidated result | 3 minutes | Shorter due to aggregation overhead |
| Negative cache (errors) | 1 minute | Don't hammer failing sources |
| Health check status | 30 seconds | Quick recovery detection |

### 3.4 Cache Invalidation

```python
class CacheInvalidation:
    """Cache invalidation strategies."""

    @staticmethod
    def invalidate_on_new_data():
        """
        Invalidate when we detect new data (via ETags or Last-Modified).

        Sources that support ETags:
        - PNCP: No
        - BLL: Yes (use X-Content-Hash)
        - Portal: Yes (use Last-Modified)
        - BNC: No
        - Licitar: No
        """
        pass

    @staticmethod
    def invalidate_on_hour():
        """Invalidate cache at the top of each hour."""
        # PNCP publishes new data in hourly batches
        pass

    @staticmethod
    def force_refresh(sources: List[str]):
        """Force refresh specific sources (admin action)."""
        pass
```

### 3.5 Cache Warming

For frequently-used queries, proactively warm the cache:

```python
async def warm_cache(
    self,
    ufs_combinations: List[Set[str]],
    days_back: int = 7,
):
    """
    Pre-populate cache for common queries.

    Run as background task (e.g., every 30 minutes).
    """
    data_final = date.today().isoformat()
    data_inicial = (date.today() - timedelta(days=days_back)).isoformat()

    for ufs in ufs_combinations:
        try:
            await self.fetch_all_sources(data_inicial, data_final, ufs)
            logger.info(f"Cache warmed for UFs: {ufs}")
        except Exception as e:
            logger.warning(f"Cache warming failed for {ufs}: {e}")
```

---

## 4. Deduplication Algorithm

### 4.1 Deduplication Key Generation

The deduplication key uniquely identifies a procurement across sources:

```python
def generate_dedup_key(record: UnifiedProcurement) -> str:
    """
    Generate unique deduplication key.

    Priority order:
    1. CNPJ + Numero Edital + Ano (most reliable)
    2. CNPJ + Objeto Hash + Valor (fallback)
    3. Source ID (last resort, no cross-source dedup)

    Returns:
        Dedup key string
    """
    # Normalize CNPJ (remove formatting)
    cnpj = re.sub(r"[^\d]", "", record.cnpj_orgao)

    # Primary key: structured identification
    if record.numero_edital and record.ano:
        numero = re.sub(r"[^\w]", "", record.numero_edital.upper())
        return f"struct:{cnpj}:{numero}:{record.ano}"

    # Secondary key: content-based
    if record.objeto and record.valor_estimado:
        objeto_normalized = normalize_text(record.objeto)
        objeto_hash = hashlib.sha256(objeto_normalized.encode()).hexdigest()[:16]
        valor_bucket = int(record.valor_estimado / 1000)  # Round to nearest 1000
        return f"content:{cnpj}:{objeto_hash}:{valor_bucket}"

    # Tertiary: source-specific (no cross-source dedup)
    return f"source:{record.source_name}:{record.source_id}"


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    # Lowercase
    text = text.lower()
    # Remove accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # Remove punctuation and normalize whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = " ".join(text.split())
    return text
```

### 4.2 Deduplication Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `first_seen` | Keep first occurrence | Default, fastest |
| `most_recent` | Keep record with latest `data_publicacao` | Data freshness priority |
| `highest_value` | Keep record with highest `valor_estimado` | Value accuracy priority |
| `priority_source` | Keep from higher-priority source | Trust ranking |
| `merge` | Merge fields from multiple sources | Maximum data richness |

### 4.3 Merge Strategy Implementation

```python
def merge_duplicates(
    records: List[UnifiedProcurement],
    priority_order: List[str] = ["PNCP", "Portal", "BLL", "BNC", "Licitar"],
) -> UnifiedProcurement:
    """
    Merge duplicate records, preferring data from higher-priority sources.

    Args:
        records: List of duplicate records (same dedup_key)
        priority_order: Source priority (first = highest)

    Returns:
        Merged UnifiedProcurement
    """
    # Sort by priority
    records.sort(key=lambda r: priority_order.index(r.source_name)
                 if r.source_name in priority_order else 999)

    # Start with highest priority record
    merged = records[0]

    # Fill in missing fields from lower-priority records
    for record in records[1:]:
        if not merged.data_abertura and record.data_abertura:
            merged.data_abertura = record.data_abertura
        if not merged.link_edital and record.link_edital:
            merged.link_edital = record.link_edital
        if not merged.modalidade and record.modalidade:
            merged.modalidade = record.modalidade
        # Add more field merging as needed

    # Track which sources contributed
    merged.raw_data = merged.raw_data or {}
    merged.raw_data["_merged_from"] = [r.source_name for r in records]

    return merged
```

### 4.4 Deduplication Metrics

Track deduplication effectiveness:

```python
@dataclass
class DeduplicationMetrics:
    """Metrics for deduplication analysis."""

    total_input: int
    total_output: int
    duplicates_removed: int

    # By source
    duplicates_per_source: Dict[str, int]  # {"PNCP-BLL": 50, "PNCP-Portal": 23}

    # By key type
    struct_key_matches: int   # Matched on numero/ano
    content_key_matches: int  # Matched on objeto hash
    no_match: int             # Unique records

    @property
    def dedup_rate(self) -> float:
        """Percentage of records that were duplicates."""
        return (self.duplicates_removed / self.total_input * 100
                if self.total_input > 0 else 0.0)
```

---

## 5. Performance Considerations

### 5.1 Parallel Execution

```python
async def fetch_parallel(
    self,
    adapters: List[SourceAdapter],
    data_inicial: str,
    data_final: str,
    ufs: Optional[Set[str]],
) -> Dict[str, Tuple[List[UnifiedProcurement], Optional[str]]]:
    """
    Execute all adapter fetches in parallel.

    Uses asyncio.gather with return_exceptions=True to capture
    individual failures without canceling other tasks.
    """
    tasks = [
        self._fetch_with_resilience(adapter, data_inicial, data_final, ufs)
        for adapter in adapters
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return {
        adapter.code: (result if not isinstance(result, Exception)
                      else ([], str(result)))
        for adapter, result in zip(adapters, results)
    }
```

### 5.2 Memory Management

For large result sets, use streaming:

```python
async def fetch_streaming(
    self,
    adapter: SourceAdapter,
    data_inicial: str,
    data_final: str,
    ufs: Optional[Set[str]],
    batch_size: int = 100,
) -> AsyncGenerator[List[UnifiedProcurement], None]:
    """
    Fetch records in batches to manage memory.

    Yields batches of records instead of accumulating all in memory.
    """
    batch = []
    async for record in adapter.fetch(data_inicial, data_final, ufs):
        batch.append(record)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
```

### 5.3 Connection Pooling

```python
class AdapterConnectionPool:
    """Shared HTTP connection pool for adapters."""

    def __init__(self, max_connections_per_host: int = 10):
        self.connector = aiohttp.TCPConnector(
            limit_per_host=max_connections_per_host,
            enable_cleanup_closed=True,
            ttl_dns_cache=300,
        )
        self.session = aiohttp.ClientSession(connector=self.connector)

    async def close(self):
        await self.session.close()
```

### 5.4 Expected Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| P50 latency | < 5s | 50th percentile response time |
| P95 latency | < 15s | 95th percentile response time |
| P99 latency | < 30s | 99th percentile response time |
| Throughput | 10 req/min | Concurrent search requests |
| Memory | < 500MB | Peak memory per request |
| Error rate | < 1% | Requests returning 5xx |

---

## 6. Observability

### 6.1 Metrics to Collect

```python
# Prometheus-style metrics
METRICS = {
    # Source-level
    "source_requests_total": Counter("Total requests per source", ["source", "status"]),
    "source_latency_seconds": Histogram("Request latency per source", ["source"]),
    "source_records_total": Counter("Records fetched per source", ["source"]),
    "source_errors_total": Counter("Errors per source", ["source", "error_type"]),

    # Consolidation-level
    "consolidation_requests_total": Counter("Total consolidation requests"),
    "consolidation_latency_seconds": Histogram("End-to-end consolidation latency"),
    "consolidation_sources_queried": Histogram("Sources queried per request"),
    "consolidation_sources_succeeded": Histogram("Sources succeeded per request"),

    # Deduplication
    "dedup_input_total": Counter("Records before deduplication"),
    "dedup_output_total": Counter("Records after deduplication"),
    "dedup_duplicates_total": Counter("Duplicates removed", ["key_type"]),

    # Cache
    "cache_hits_total": Counter("Cache hits", ["cache_level", "source"]),
    "cache_misses_total": Counter("Cache misses", ["cache_level", "source"]),
}
```

### 6.2 Structured Logging

```python
# Log format for consolidation operations
logger.info(
    "Consolidation complete",
    extra={
        "event": "consolidation_complete",
        "duration_ms": result.duration_ms,
        "sources_queried": list(adapters.keys()),
        "sources_succeeded": list(result.source_stats.keys()),
        "sources_failed": list(result.errors.keys()),
        "total_raw": result.total_raw,
        "total_deduplicated": result.total_deduplicated,
        "duplicates_removed": result.duplicates_removed,
        "request_id": request_id,
    }
)
```

### 6.3 Distributed Tracing

```python
async def fetch_with_tracing(
    self,
    adapter: SourceAdapter,
    span_context: Optional[SpanContext] = None,
) -> List[UnifiedProcurement]:
    """Fetch with OpenTelemetry tracing."""
    with tracer.start_span(
        f"fetch_{adapter.code}",
        context=span_context,
        attributes={
            "source.name": adapter.name,
            "source.code": adapter.code,
        }
    ) as span:
        try:
            records = await self._fetch_records(adapter)
            span.set_attribute("records.count", len(records))
            return records
        except Exception as e:
            span.set_status(StatusCode.ERROR)
            span.record_exception(e)
            raise
```

---

## 7. Security Considerations

### 7.1 API Key Management

```python
@dataclass
class SourceCredentials:
    """Credentials for authenticated sources."""

    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    oauth_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_env(cls, source_code: str) -> "SourceCredentials":
        """Load credentials from environment variables."""
        prefix = f"{source_code.upper()}_"
        return cls(
            api_key=os.getenv(f"{prefix}API_KEY"),
            api_secret=os.getenv(f"{prefix}API_SECRET"),
            oauth_token=os.getenv(f"{prefix}OAUTH_TOKEN"),
        )
```

### 7.2 Data Sanitization

```python
def sanitize_record(record: UnifiedProcurement) -> UnifiedProcurement:
    """
    Sanitize record before processing.

    - Remove potential XSS in text fields
    - Validate CNPJ format
    - Normalize URLs
    """
    record.objeto = html.escape(record.objeto)
    record.orgao = html.escape(record.orgao)

    # Validate CNPJ (basic format check)
    cnpj_digits = re.sub(r"[^\d]", "", record.cnpj_orgao)
    if len(cnpj_digits) not in (0, 14):  # Empty or valid
        logger.warning(f"Invalid CNPJ format: {record.cnpj_orgao}")
        record.cnpj_orgao = ""

    return record
```

### 7.3 Rate Limit Protection

```python
class RateLimiter:
    """Per-source rate limiting to avoid being blocked."""

    def __init__(self, source_code: str, requests_per_second: float):
        self.source_code = source_code
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until we can make another request."""
        async with self._lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()
```

---

## 8. Migration Strategy

### 8.1 Phase 1: Foundation (Week 1)

**Goals:**
- Create module structure
- Define interfaces
- Write tests

**Tasks:**
1. Create `backend/sources/` directory structure
2. Implement `SourceAdapter` ABC and `UnifiedProcurement` dataclass
3. Write contract tests that all adapters must pass
4. Create `ConsolidationService` skeleton

**Files to Create:**
```
backend/sources/
  __init__.py
  base.py              # ABC and data models
  consolidation.py     # ConsolidationService
  exceptions.py        # Custom exceptions
  cache.py             # Cache layer
  adapters/
    __init__.py
    pncp.py            # PNCP adapter (refactored)
```

### 8.2 Phase 2: PNCP Migration (Week 2)

**Goals:**
- Refactor existing PNCPClient to new interface
- Maintain backward compatibility
- Zero production impact

**Tasks:**
1. Create `PNCPAdapter` that wraps existing `PNCPClient`
2. Add async support (initially via `asyncio.to_thread`)
3. Update `/buscar` endpoint to use consolidation service
4. Add feature flag for gradual rollout

**Backward Compatibility:**
```python
# main.py - with feature flag
USE_CONSOLIDATION = os.getenv("FEATURE_CONSOLIDATION", "false") == "true"

@app.post("/buscar")
async def buscar_licitacoes(request: BuscaRequest):
    if USE_CONSOLIDATION:
        return await buscar_with_consolidation(request)
    else:
        return await buscar_legacy(request)
```

### 8.3 Phase 3: Additional Adapters (Weeks 3-4)

**Week 3: BLL and Portal**
1. Implement `BLLAdapter`
2. Implement `PortalAdapter`
3. Integration tests with real APIs

**Week 4: BNC and Licitar**
1. Implement `BNCAdapter`
2. Implement `LicitarAdapter`
3. End-to-end testing with all 5 sources

### 8.4 Phase 4: Production Hardening (Week 5)

**Goals:**
- Full observability
- Load testing
- Documentation

**Tasks:**
1. Add Prometheus metrics
2. Add OpenTelemetry tracing
3. Load test with 5 sources
4. Update API documentation
5. Create runbooks

### 8.5 Rollout Strategy

| Stage | Feature Flag | Traffic | Monitoring |
|-------|--------------|---------|------------|
| 1 | Internal only | 0% | Full observability |
| 2 | Beta users | 1% | Error rate < 1% |
| 3 | Gradual rollout | 10% | Latency P95 < 15s |
| 4 | General availability | 50% | All metrics green |
| 5 | Default enabled | 100% | Maintain SLOs |

---

## Appendix A: Directory Structure

```
backend/
  sources/
    __init__.py
    base.py                    # SourceAdapter ABC, UnifiedProcurement
    consolidation.py           # ConsolidationService
    exceptions.py              # SourceError, SourceTimeoutError, etc.
    cache.py                   # CacheService (Redis + in-memory)
    dedup.py                   # Deduplication logic
    metrics.py                 # Prometheus metrics
    adapters/
      __init__.py
      pncp.py                  # PNCPAdapter
      bll.py                   # BLLAdapter
      portal.py                # PortalAdapter
      bnc.py                   # BNCAdapter
      licitar.py               # LicitarAdapter
  tests/
    sources/
      test_base.py             # Interface contract tests
      test_consolidation.py    # Consolidation service tests
      test_dedup.py            # Deduplication tests
      test_cache.py            # Cache tests
      adapters/
        test_pncp.py
        test_bll.py
        test_portal.py
        test_bnc.py
        test_licitar.py
```

---

## Appendix B: Configuration Example

```python
# config/sources.yaml
sources:
  pncp:
    name: "Portal Nacional de Contratacoes Publicas"
    code: "PNCP"
    base_url: "https://pncp.gov.br/api/consulta/v1"
    timeout: 30
    rate_limit_rps: 10
    priority: 1
    enabled: true

  bll:
    name: "BLL Compras"
    code: "BLL"
    base_url: "https://api.bll.com.br/v2"
    timeout: 25
    rate_limit_rps: 5
    priority: 2
    enabled: true
    credentials:
      api_key: "${BLL_API_KEY}"

  portal:
    name: "Portal de Compras Publicas"
    code: "Portal"
    base_url: "https://api.compras.gov.br/v1"
    timeout: 30
    rate_limit_rps: 10
    priority: 3
    enabled: true

  bnc:
    name: "Bolsa Nacional de Compras"
    code: "BNC"
    base_url: "https://api.bnc.org.br/v1"
    timeout: 20
    rate_limit_rps: 5
    priority: 4
    enabled: true

  licitar:
    name: "Licitar Digital"
    code: "Licitar"
    base_url: "https://api.licitardigital.com.br/v1"
    timeout: 20
    rate_limit_rps: 5
    priority: 5
    enabled: true

consolidation:
  timeout_global: 60
  fail_on_all_errors: true
  dedup_strategy: "first_seen"

cache:
  redis_url: "${REDIS_URL}"
  source_ttl: 300        # 5 minutes
  consolidated_ttl: 180  # 3 minutes
  negative_ttl: 60       # 1 minute
```

---

**END OF TECHNICAL CONSIDERATIONS**
