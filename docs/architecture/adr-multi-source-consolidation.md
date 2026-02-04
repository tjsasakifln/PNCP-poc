# ADR-001: Multi-Source Procurement Consolidation Architecture

**Date:** 2026-02-03
**Status:** Proposed
**Deciders:** @architect, @dev, @pm
**Author:** @architect (Aria)

---

## Context

### Current State
BidIQ Uniformes currently queries a single procurement source - PNCP (Portal Nacional de Contratacoes Publicas). The implementation resides in `backend/pncp_client.py` with:
- Resilient HTTP client with exponential backoff retry (max 5 retries)
- Rate limiting (10 req/s)
- Automatic pagination via `fetch_all()` generator
- Field normalization via `_normalize_item()`

### Problem Statement
Clients are requesting expanded coverage across multiple Brazilian procurement portals to maximize opportunity discovery. We need to add 4 new sources while maintaining:
1. System reliability (partial failures must not crash the system)
2. Response time within acceptable limits (< 30s for typical queries)
3. Data quality (deduplication across sources)
4. Maintainability (easy to add/remove sources)

### New Sources to Integrate
| Source | Type | API Documentation | Priority |
|--------|------|-------------------|----------|
| **BLL Compras** | State/Municipal portal aggregator | REST API | P1 |
| **Portal de Compras Publicas** | Federal/State purchases | REST API | P1 |
| **BNC (Bolsa Nacional de Compras)** | Private sector procurement | REST API | P2 |
| **Licitar Digital** | Municipal procurement | REST API | P2 |

---

## Decision Drivers

1. **Extensibility:** Easy to add new procurement sources without modifying core logic
2. **Fault Tolerance:** One source failure must not affect others
3. **Performance:** Parallel execution to minimize total query time
4. **Maintainability:** Clear separation of concerns, testable components
5. **Data Quality:** Accurate deduplication without losing valid records
6. **Backward Compatibility:** Existing API contract must remain unchanged

---

## Considered Options

### Option 1: Strategy Pattern (Source-Specific Strategies)

```
          +------------------+
          |   SourceManager  |
          +--------+---------+
                   |
     +-------------+-------------+
     |             |             |
+----v----+  +-----v-----+  +----v----+
| PNCP    |  | BLL       |  | Portal  |
| Strategy|  | Strategy  |  | Strategy|
+---------+  +-----------+  +---------+
```

**Pros:**
- Simple to understand and implement
- Each source encapsulates its own logic
- Easy to test individual sources

**Cons:**
- Tight coupling between manager and strategies
- Harder to add cross-cutting concerns (caching, retry)
- No clear extension points for new functionality

### Option 2: Adapter Pattern with Abstract Interface (RECOMMENDED)

```
          +-----------------------+
          |   ConsolidationService|
          +-----------+-----------+
                      |
          +-----------v-----------+
          |   SourceAdapter (ABC) |
          +-----------+-----------+
                      |
    +-----------------+------------------+
    |          |          |             |
+---v---+ +----v----+ +---v----+ +------v------+
| PNCP  | | BLL     | | Portal | | LicitarDig  |
|Adapter| | Adapter | | Adapter| | Adapter     |
+-------+ +---------+ +--------+ +-------------+
```

**Pros:**
- Clean interface contract enforced by ABC
- Easy to add new sources (implement interface)
- Supports dependency injection for testing
- Clear separation between orchestration and source-specific logic

**Cons:**
- Slightly more boilerplate than strategy
- Requires careful interface design upfront

### Option 3: Plugin System with Dynamic Loading

```
          +------------------+
          |  PluginRegistry  |
          +--------+---------+
                   |
          +--------v--------+
          | Dynamic Loader  |
          +--------+--------+
                   |
     +-------------+-------------+
     |             |             |
+----v----+  +-----v-----+  +----v----+
| pncp.py |  | bll.py    |  | portal.py|
| (plugin)|  | (plugin)  |  | (plugin) |
+---------+  +-----------+  +---------+
```

**Pros:**
- Maximum flexibility
- Can add sources at runtime
- Supports third-party extensions

**Cons:**
- Over-engineered for current needs (5 sources)
- Complex error handling
- Harder to debug
- Type safety challenges

---

## Decision Outcome

**Chosen Option: Adapter Pattern with Abstract Interface (Option 2)**

### Rationale

1. **Right-sized complexity:** We have a known, finite set of sources (5). Plugin system is overkill; strategy pattern lacks clear contracts.

2. **Interface-driven development:** Abstract Base Class (ABC) enforces contract compliance at development time, catching errors early.

3. **Testability:** Each adapter can be unit tested in isolation with mocked HTTP responses.

4. **Extensibility path:** If we later need dynamic loading, adapters can be wrapped by a plugin system without rewriting.

5. **Team familiarity:** The existing `PNCPClient` already follows this pattern implicitly - we're formalizing it.

### Consequences

**Positive:**
- Clear contract for all procurement sources
- Easy onboarding for new developers
- Predictable behavior across sources
- Simple testing strategy

**Negative:**
- Must define interface carefully upfront
- Breaking interface changes require updating all adapters
- Slight overhead for simple sources

**Mitigations:**
- Use versioned interfaces if breaking changes needed
- Provide base adapter class with common functionality
- Document interface thoroughly

---

## Technical Design

### 1. Core Interface Definition

```python
# backend/sources/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Optional, Set
from enum import Enum

class SourceStatus(Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

@dataclass
class UnifiedProcurement:
    """Unified procurement record across all sources."""

    # Identification (for deduplication)
    source_id: str          # Original ID from source
    source_name: str        # e.g., "PNCP", "BLL", "Portal"

    # Deduplication key (normalized)
    dedup_key: str          # Generated from cnpj_orgao + numero_edital + ano

    # Core fields (required)
    objeto: str             # Procurement object description
    valor_estimado: float   # Estimated value in BRL
    orgao: str              # Contracting agency name
    cnpj_orgao: str         # Agency CNPJ (for dedup)
    uf: str                 # State code
    municipio: str          # Municipality

    # Dates
    data_publicacao: datetime
    data_abertura: Optional[datetime] = None

    # Classification
    modalidade: str = ""
    situacao: str = ""

    # Links
    link_edital: str = ""
    link_portal: str = ""

    # Metadata
    fetched_at: datetime = None

    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.utcnow()


class SourceAdapter(ABC):
    """Abstract base class for procurement source adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable source name."""
        pass

    @property
    @abstractmethod
    def code(self) -> str:
        """Short code for logs/metrics (e.g., 'PNCP', 'BLL')."""
        pass

    @abstractmethod
    async def health_check(self) -> SourceStatus:
        """Check if source is available."""
        pass

    @abstractmethod
    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """
        Fetch procurement records from this source.

        Args:
            data_inicial: Start date (YYYY-MM-DD)
            data_final: End date (YYYY-MM-DD)
            ufs: Optional set of state codes to filter

        Yields:
            UnifiedProcurement records
        """
        pass

    @abstractmethod
    def normalize(self, raw_record: dict) -> UnifiedProcurement:
        """Convert source-specific record to unified format."""
        pass
```

### 2. Consolidation Service

```python
# backend/sources/consolidation.py
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConsolidationResult:
    """Result of multi-source consolidation."""

    records: List[UnifiedProcurement]
    total_raw: int                      # Before dedup
    total_deduplicated: int             # After dedup
    source_stats: Dict[str, dict]       # Per-source statistics
    errors: Dict[str, str]              # Source -> error message
    duration_ms: int

    @property
    def success_rate(self) -> float:
        """Percentage of sources that returned successfully."""
        total = len(self.source_stats) + len(self.errors)
        if total == 0:
            return 0.0
        return len(self.source_stats) / total * 100


@dataclass
class ConsolidationConfig:
    """Configuration for consolidation behavior."""

    timeout_per_source: int = 30        # seconds
    max_concurrent_sources: int = 5
    fail_on_all_errors: bool = False    # If True, raise if ALL sources fail
    dedup_strategy: str = "first_seen"  # "first_seen" | "most_recent" | "highest_value"


class ConsolidationService:
    """Orchestrates multi-source procurement fetching and consolidation."""

    def __init__(
        self,
        adapters: List[SourceAdapter],
        config: Optional[ConsolidationConfig] = None,
    ):
        self.adapters = {a.code: a for a in adapters}
        self.config = config or ConsolidationConfig()

    async def fetch_all_sources(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        enabled_sources: Optional[Set[str]] = None,
    ) -> ConsolidationResult:
        """
        Fetch from all enabled sources in parallel, consolidate, and deduplicate.

        Args:
            data_inicial: Start date (YYYY-MM-DD)
            data_final: End date (YYYY-MM-DD)
            ufs: Optional set of state codes
            enabled_sources: Optional set of source codes to query (default: all)

        Returns:
            ConsolidationResult with deduplicated records and statistics
        """
        start_time = datetime.utcnow()

        # Determine which adapters to use
        if enabled_sources:
            adapters = [a for code, a in self.adapters.items() if code in enabled_sources]
        else:
            adapters = list(self.adapters.values())

        if not adapters:
            return ConsolidationResult(
                records=[],
                total_raw=0,
                total_deduplicated=0,
                source_stats={},
                errors={"config": "No sources enabled"},
                duration_ms=0,
            )

        # Create tasks for parallel execution
        tasks = [
            self._fetch_with_timeout(adapter, data_inicial, data_final, ufs)
            for adapter in adapters
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_records: List[UnifiedProcurement] = []
        source_stats: Dict[str, dict] = {}
        errors: Dict[str, str] = {}

        for adapter, result in zip(adapters, results):
            if isinstance(result, Exception):
                errors[adapter.code] = str(result)
                logger.error(f"Source {adapter.code} failed: {result}")
            else:
                records, stats = result
                all_records.extend(records)
                source_stats[adapter.code] = stats
                logger.info(f"Source {adapter.code}: {stats['count']} records in {stats['duration_ms']}ms")

        # Check if all sources failed
        if not source_stats and self.config.fail_on_all_errors:
            raise RuntimeError(f"All sources failed: {errors}")

        # Deduplicate
        total_raw = len(all_records)
        deduplicated = self._deduplicate(all_records)

        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return ConsolidationResult(
            records=deduplicated,
            total_raw=total_raw,
            total_deduplicated=len(deduplicated),
            source_stats=source_stats,
            errors=errors,
            duration_ms=duration_ms,
        )

    async def _fetch_with_timeout(
        self,
        adapter: SourceAdapter,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]],
    ) -> tuple[List[UnifiedProcurement], dict]:
        """Fetch from a single source with timeout protection."""
        start = datetime.utcnow()
        records = []

        try:
            async with asyncio.timeout(self.config.timeout_per_source):
                async for record in adapter.fetch(data_inicial, data_final, ufs):
                    records.append(record)
        except asyncio.TimeoutError:
            logger.warning(f"Source {adapter.code} timed out after {self.config.timeout_per_source}s")
            raise TimeoutError(f"Source timed out after {self.config.timeout_per_source}s")

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)

        return records, {
            "count": len(records),
            "duration_ms": duration_ms,
        }

    def _deduplicate(
        self,
        records: List[UnifiedProcurement],
    ) -> List[UnifiedProcurement]:
        """
        Remove duplicate procurements based on dedup_key.

        Deduplication key is generated from:
        - CNPJ do orgao (normalized)
        - Numero do edital
        - Ano

        Strategy options:
        - first_seen: Keep the first occurrence (default)
        - most_recent: Keep record with latest data_publicacao
        - highest_value: Keep record with highest valor_estimado
        """
        seen: Dict[str, UnifiedProcurement] = {}

        for record in records:
            key = record.dedup_key

            if key not in seen:
                seen[key] = record
                continue

            # Apply dedup strategy for duplicates
            if self.config.dedup_strategy == "most_recent":
                if record.data_publicacao > seen[key].data_publicacao:
                    seen[key] = record
            elif self.config.dedup_strategy == "highest_value":
                if record.valor_estimado > seen[key].valor_estimado:
                    seen[key] = record
            # else: first_seen (keep existing)

        return list(seen.values())
```

### 3. PNCP Adapter (Refactored from existing client)

```python
# backend/sources/adapters/pncp_adapter.py
import re
from typing import AsyncGenerator, Optional, Set

from ..base import SourceAdapter, SourceStatus, UnifiedProcurement

class PNCPAdapter(SourceAdapter):
    """Adapter for PNCP (Portal Nacional de Contratacoes Publicas)."""

    BASE_URL = "https://pncp.gov.br/api/consulta/v1"

    @property
    def name(self) -> str:
        return "Portal Nacional de Contratacoes Publicas"

    @property
    def code(self) -> str:
        return "PNCP"

    async def health_check(self) -> SourceStatus:
        """Check PNCP API health via lightweight request."""
        # Implementation: GET /health or fetch single page with limit=1
        pass

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """Fetch from PNCP with pagination and retry."""
        # Refactor existing PNCPClient.fetch_all() to async
        pass

    def normalize(self, raw: dict) -> UnifiedProcurement:
        """Convert PNCP response format to unified model."""
        # Extract nested orgaoEntidade/unidadeOrgao
        unidade = raw.get("unidadeOrgao") or {}
        orgao = raw.get("orgaoEntidade") or {}

        cnpj = orgao.get("cnpj", "") or raw.get("cnpjOrgao", "")
        cnpj_clean = re.sub(r"[^\d]", "", cnpj)  # Remove formatting

        numero = raw.get("numeroCompra", "")
        ano = raw.get("anoCompra", "")

        return UnifiedProcurement(
            source_id=raw.get("numeroControlePNCP", ""),
            source_name=self.code,
            dedup_key=f"{cnpj_clean}:{numero}:{ano}",
            objeto=raw.get("objetoCompra", ""),
            valor_estimado=raw.get("valorTotalEstimado", 0) or 0,
            orgao=orgao.get("razaoSocial", "") or unidade.get("nomeUnidade", ""),
            cnpj_orgao=cnpj,
            uf=unidade.get("ufSigla", "") or raw.get("uf", ""),
            municipio=unidade.get("municipioNome", "") or raw.get("municipio", ""),
            data_publicacao=raw.get("dataPublicacaoPncp"),
            data_abertura=raw.get("dataAberturaProposta"),
            modalidade=raw.get("modalidadeNome", ""),
            situacao=raw.get("situacaoCompraNome", ""),
            link_edital=raw.get("linkSistemaOrigem", ""),
            link_portal=f"https://pncp.gov.br/app/editais/{raw.get('numeroControlePNCP', '')}",
        )
```

---

## Component Diagram

```
+------------------------------------------------------------------------------+
|                            CLIENT (Frontend)                                  |
|    Next.js 14 | React 18 | TypeScript                                        |
+------------------------------------+-----------------------------------------+
                                     |
                                     | POST /buscar
                                     | {ufs, data_inicial, data_final, sources?}
                                     v
+------------------------------------------------------------------------------+
|                            BACKEND (FastAPI)                                  |
|                                                                              |
|  +------------------+     +------------------------+     +----------------+  |
|  |   API Endpoint   |---->|  ConsolidationService  |---->|  Filter Engine |  |
|  |   POST /buscar   |     |  - Parallel execution  |     |  - Keywords    |  |
|  +------------------+     |  - Timeout handling    |     |  - Value range |  |
|                           |  - Error aggregation   |     |  - UF filter   |  |
|                           |  - Deduplication       |     +----------------+  |
|                           +----------+-------------+             |           |
|                                      |                           v           |
|                      +---------------+---------------+    +-------------+    |
|                      |               |               |    | LLM Summary |    |
|                      v               v               v    +-------------+    |
|               +------------+ +------------+ +------------+       |           |
|               |   PNCP     | |    BLL     | |  Portal    |       v           |
|               |  Adapter   | |  Adapter   | |  Adapter   | +-------------+   |
|               +-----+------+ +-----+------+ +-----+------+ | Excel Gen   |   |
|                     |              |              |         +-------------+   |
+---------------------|--------------|--------------|---------------------------+
                      |              |              |
                      v              v              v
              +-------------+ +------------+ +----------------+
              | PNCP API    | | BLL API    | | Portal API     |
              | pncp.gov.br | | bll.com.br | | compras.gov.br |
              +-------------+ +------------+ +----------------+

              +------------+  +---------------+
              | BNC API    |  | Licitar API   |
              +------------+  +---------------+
                      ^               ^
                      |               |
                +-----+------+ +------+------+
                | BNC        | | Licitar     |
                | Adapter    | | Adapter     |
                +------------+ +-------------+

Legend:
  ---->  Data flow
  [ABC]  External API
  +---+  Internal component
```

---

## Sequence Diagram

```
Client          FastAPI         ConsolidationSvc    Adapters          External APIs
  |                |                  |                |                    |
  | POST /buscar   |                  |                |                    |
  |--------------->|                  |                |                    |
  |                | fetch_all()      |                |                    |
  |                |----------------->|                |                    |
  |                |                  |                |                    |
  |                |                  | [PARALLEL]     |                    |
  |                |                  |================|                    |
  |                |                  |                |                    |
  |                |                  | fetch(PNCP)    |                    |
  |                |                  |--------------->|  GET /publicacao   |
  |                |                  |                |------------------->|
  |                |                  |                |<-------------------|
  |                |                  |                |                    |
  |                |                  | fetch(BLL)     |                    |
  |                |                  |--------------->|  GET /licitacoes   |
  |                |                  |                |------------------->|
  |                |                  |                |<-------------------|
  |                |                  |                |                    |
  |                |                  | fetch(Portal)  |                    |
  |                |                  |--------------->|  GET /contratos    |
  |                |                  |                |------------------->|
  |                |                  |                |    [TIMEOUT]       |
  |                |                  |<---------------|                    |
  |                |                  |                |                    |
  |                |                  |================|                    |
  |                |                  | [/PARALLEL]    |                    |
  |                |                  |                |                    |
  |                |                  | aggregate()    |                    |
  |                |                  |--------------->|                    |
  |                |                  |                |                    |
  |                |                  | deduplicate()  |                    |
  |                |                  |--------------->|                    |
  |                |                  |                |                    |
  |                | ConsolidationResult               |                    |
  |                |<-----------------|                |                    |
  |                |                  |                |                    |
  |                | filter_batch()   |                |                    |
  |                |----------------->|                |                    |
  |                |                  |                |                    |
  |                | gerar_resumo()   |                |                    |
  |                |----------------->|                |                    |
  |                |                  |                |                    |
  |                | create_excel()   |                |                    |
  |                |----------------->|                |                    |
  |                |                  |                |                    |
  | BuscaResponse  |                  |                |                    |
  |<---------------|                  |                |                    |
  |                |                  |                |                    |

Notes:
- Parallel execution via asyncio.gather()
- Portal timeout captured, PNCP and BLL continue
- Partial results returned with error report
- Deduplication happens AFTER aggregation
```

---

## Error Handling Strategy

### Source Failure Modes

| Failure Type | Handling | User Impact |
|--------------|----------|-------------|
| Single source timeout | Log warning, continue with others | Partial results with warning |
| Single source 5xx | Retry 3x with backoff, then skip | Partial results with warning |
| Single source 4xx | Fail immediately for that source | Partial results with error |
| All sources fail | Raise RuntimeError | HTTP 502 to client |
| Dedup conflict | Apply configured strategy | None (internal logic) |

### Error Response Format

```python
@dataclass
class ConsolidationResult:
    records: List[UnifiedProcurement]
    total_raw: int
    total_deduplicated: int
    source_stats: Dict[str, dict]       # Successful sources
    errors: Dict[str, str]              # Failed sources -> error message
    duration_ms: int
```

### Client-Side Handling

```json
{
  "resumo": { ... },
  "excel_base64": "...",
  "total_raw": 523,
  "total_filtrado": 15,
  "source_stats": {
    "PNCP": {"count": 300, "duration_ms": 4500},
    "BLL": {"count": 223, "duration_ms": 3200}
  },
  "source_errors": {
    "Portal": "Timeout after 30s"
  },
  "warning": "1 of 3 sources failed. Results may be incomplete."
}
```

---

## Deduplication Algorithm

### Dedup Key Generation

```python
def generate_dedup_key(record: UnifiedProcurement) -> str:
    """
    Generate unique key for deduplication.

    Key components (in order of specificity):
    1. CNPJ do orgao (normalized, digits only)
    2. Numero do edital/processo
    3. Ano do processo

    Fallback (if numero unavailable):
    - CNPJ + objeto_hash + valor_estimado
    """
    cnpj = re.sub(r"[^\d]", "", record.cnpj_orgao)

    if record.numero_edital and record.ano:
        return f"{cnpj}:{record.numero_edital}:{record.ano}"

    # Fallback for records without clear identifiers
    objeto_hash = hashlib.md5(record.objeto.encode()).hexdigest()[:8]
    return f"{cnpj}:{objeto_hash}:{int(record.valor_estimado)}"
```

### Dedup Strategies

| Strategy | Use Case | Behavior |
|----------|----------|----------|
| `first_seen` (default) | General use | Keep first occurrence |
| `most_recent` | Data freshness priority | Keep record with latest `data_publicacao` |
| `highest_value` | Value accuracy priority | Keep record with highest `valor_estimado` |
| `priority_source` | Source trust ranking | Keep from higher-priority source |

---

## Caching Strategy

### Multi-Level Cache

```
+------------------+     +------------------+     +------------------+
|   L1: In-Memory  |---->|   L2: Redis      |---->|   L3: Source API |
|   (per-request)  |     |   (shared, 5min) |     |   (authoritative)|
+------------------+     +------------------+     +------------------+
```

### Cache Keys

```python
# Source-level cache (before consolidation)
source_cache_key = f"source:{adapter.code}:{data_inicial}:{data_final}:{sorted(ufs)}"

# Consolidated cache (after dedup)
consolidated_cache_key = f"consolidated:{data_inicial}:{data_final}:{sorted(ufs)}:{sorted(sources)}"
```

### TTL Configuration

| Cache Level | TTL | Rationale |
|-------------|-----|-----------|
| L1 In-Memory | Request lifetime | Prevent duplicate fetches within request |
| L2 Redis | 5 minutes | PNCP updates ~hourly, balance freshness/performance |
| Negative cache | 1 minute | Don't hammer failing sources |

---

## Timeout Strategy

### Per-Source Timeouts

| Source | Connection | Read | Total |
|--------|------------|------|-------|
| PNCP | 5s | 25s | 30s |
| BLL | 5s | 20s | 25s |
| Portal | 5s | 25s | 30s |
| BNC | 5s | 15s | 20s |
| Licitar | 5s | 15s | 20s |

### Global Timeout

- Maximum total request time: 60 seconds
- If not all sources respond by 55s, return partial results

### Timeout Handling

```python
async def fetch_with_timeout(adapter, timeout):
    try:
        async with asyncio.timeout(timeout):
            return await adapter.fetch(...)
    except asyncio.TimeoutError:
        logger.warning(f"{adapter.code} timed out")
        return [], {"error": "timeout", "partial": True}
```

---

## Migration Path

### Phase 1: Preparation (Week 1)
1. Create `sources/` module structure
2. Define `SourceAdapter` ABC and `UnifiedProcurement` dataclass
3. Write comprehensive tests for interface
4. Refactor `PNCPClient` into `PNCPAdapter` (maintain backward compatibility)

### Phase 2: Core Implementation (Week 2)
1. Implement `ConsolidationService` with parallel execution
2. Implement deduplication algorithm
3. Add Redis caching layer
4. Update `/buscar` endpoint to use consolidation service

### Phase 3: Additional Adapters (Weeks 3-4)
1. Implement `BLLAdapter`
2. Implement `PortalAdapter`
3. Implement `BNCAdapter`
4. Implement `LicitarAdapter`

### Phase 4: Production Hardening (Week 5)
1. Add observability (metrics, tracing)
2. Load testing with all sources
3. Gradual rollout (feature flag)
4. Documentation and runbooks

---

## References

- Current PNCP client: `backend/pncp_client.py`
- Current filter logic: `backend/filter.py`
- PNCP API docs: https://pncp.gov.br/api/consulta/swagger-ui/index.html
- Python ABC docs: https://docs.python.org/3/library/abc.html
- asyncio patterns: https://docs.python.org/3/library/asyncio-task.html

---

**END OF ADR-001**
