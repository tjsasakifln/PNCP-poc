# Story MSP-001-03: Architecture Design

**Story ID:** MSP-001-03
**GitHub Issue:** #158 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @architect
**Created:** February 3, 2026

---

## Story

**As a** technical architect,
**I want** a detailed architecture design for multi-source procurement integration,
**So that** the development team has clear technical guidance for implementation.

---

## Objective

Create a comprehensive architecture document that addresses:

1. Multi-client orchestration patterns
2. Resilience and fault tolerance
3. Rate limiting strategies per source
4. Data flow and transformation pipeline
5. Monitoring and observability
6. Performance optimization

---

## Acceptance Criteria

### AC1: Architecture Document
- [ ] High-level architecture diagram created
- [ ] Component responsibilities documented
- [ ] Data flow diagrams for key scenarios
- [ ] Integration patterns defined
- [ ] Document saved at `docs/architecture/multi-source-architecture.md`

### AC2: Client Design Pattern
- [ ] Base client abstraction defined
- [ ] Retry strategy per source documented
- [ ] Circuit breaker configuration specified
- [ ] Rate limiting strategy per source
- [ ] Timeout policies documented

### AC3: Consolidation Service Design
- [ ] Parallel vs sequential fetching strategy
- [ ] Result aggregation approach
- [ ] Deduplication algorithm
- [ ] Error handling when sources fail
- [ ] Partial results handling

### AC4: Configuration Design
- [ ] Source configuration schema
- [ ] Feature flags for source enable/disable
- [ ] Environment-specific settings
- [ ] Secret management approach

### AC5: Performance Design
- [ ] Caching strategy
- [ ] Concurrent request limits
- [ ] Response time budgets
- [ ] Memory usage considerations

### AC6: Monitoring Design
- [ ] Metrics to collect per source
- [ ] Health check endpoints
- [ ] Alerting thresholds
- [ ] Dashboard requirements

### AC7: ADRs (Architecture Decision Records)
- [ ] ADR-001: Multi-source integration pattern
- [ ] ADR-002: Retry and circuit breaker strategy
- [ ] ADR-003: Deduplication approach
- [ ] ADR-004: Configuration management

---

## Technical Tasks

### Task 1: Analyze Current Architecture (0.5 SP)
- [ ] Review existing PNCP client implementation
- [ ] Document current retry/resilience patterns
- [ ] Identify reusable components
- [ ] Note areas needing refactoring

### Task 2: Design Client Abstraction (1.5 SP)
- [ ] Design `BaseClient` interface
- [ ] Define retry configuration per source
- [ ] Design circuit breaker integration
- [ ] Document rate limiting approach

### Task 3: Design Consolidation Service (1.5 SP)
- [ ] Design parallel fetching orchestration
- [ ] Define aggregation logic
- [ ] Design deduplication algorithm
- [ ] Plan partial failure handling

### Task 4: Design Configuration & Monitoring (1 SP)
- [ ] Create configuration schema
- [ ] Define monitoring metrics
- [ ] Design health check system
- [ ] Plan alerting strategy

### Task 5: Documentation & ADRs (0.5 SP)
- [ ] Write architecture document
- [ ] Create ADR records
- [ ] Review with team

---

## Architecture Design (Draft)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                          │
│  POST /api/buscar  GET /api/download  GET /api/health               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Consolidation Service                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Orchestrator │──│ Aggregator   │──│ Deduplicator │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│   PNCP    │ │    BLL    │ │    PCP    │ │    BNC    │ │  Licitar  │
│  Client   │ │  Client   │ │  Client   │ │  Client   │ │  Client   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
      │             │             │             │             │
      ▼             ▼             ▼             ▼             ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  pncp.    │ │  bll.     │ │ pcp.com.br│ │  bnc.     │ │ licitar.  │
│  gov.br   │ │  org.br   │ │           │ │  org.br   │ │ digital   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

### Component Design

```
backend/
├── clients/
│   ├── __init__.py
│   ├── base_client.py       # Abstract base with retry, circuit breaker
│   ├── pncp_client.py       # Refactored to extend base
│   ├── bll_client.py
│   ├── pcp_client.py
│   ├── bnc_client.py
│   └── licitar_client.py
├── services/
│   ├── __init__.py
│   ├── consolidation.py     # Main orchestration
│   ├── deduplication.py     # Cross-source matching
│   └── source_manager.py    # Health, enable/disable
├── schemas/
│   ├── unified_schema.py
│   ├── source_schemas.py
│   └── transformers.py
└── config/
    ├── __init__.py
    └── sources.py           # Source configuration
```

### Resilience Pattern

```python
# Per-source configuration
@dataclass
class SourceConfig:
    name: str
    enabled: bool = True
    base_url: str = ""
    timeout: float = 30.0

    # Retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0

    # Rate limiting
    requests_per_second: float = 5.0
    burst_limit: int = 10

    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_requests: int = 3
```

### Consolidation Flow

```python
async def fetch_all_sources(request: SearchRequest) -> ConsolidatedResult:
    """
    Parallel fetch from all enabled sources with graceful degradation.
    """
    sources = source_manager.get_enabled_sources()

    # Launch parallel fetches
    tasks = [
        fetch_with_timeout(client, request, timeout=SOURCE_TIMEOUT)
        for client in sources
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate results, handling failures
    all_items = []
    errors = []

    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            errors.append(SourceError(source=source.name, error=str(result)))
            logger.warning(f"Source {source.name} failed: {result}")
        else:
            all_items.extend(result)

    # Deduplicate across sources
    unique_items = deduplicator.deduplicate(all_items)

    return ConsolidatedResult(
        items=unique_items,
        total=len(unique_items),
        sources_queried=len(sources),
        sources_failed=len(errors),
        errors=errors
    )
```

### Deduplication Strategy

```python
def deduplicate(items: list[UnifiedProcurement]) -> list[UnifiedProcurement]:
    """
    Remove duplicates across sources using fingerprint matching.

    Priority order when same bid found on multiple sources:
    1. PNCP (official government source)
    2. Source with most complete data
    3. Most recently updated
    """
    seen_fingerprints: dict[str, UnifiedProcurement] = {}

    # Sort by source priority
    sorted_items = sorted(items, key=lambda x: SOURCE_PRIORITY.get(x.source, 99))

    for item in sorted_items:
        fp = item.fingerprint or generate_fingerprint(item)
        if fp not in seen_fingerprints:
            seen_fingerprints[fp] = item
        else:
            # Check if new item has more complete data
            existing = seen_fingerprints[fp]
            if completeness_score(item) > completeness_score(existing):
                seen_fingerprints[fp] = item

    return list(seen_fingerprints.values())
```

---

## ADR Template

### ADR-001: Multi-Source Integration Pattern

**Status:** Proposed

**Context:**
We need to integrate 5 different procurement sources with varying API designs, reliability levels, and data formats.

**Decision:**
Use a unified client abstraction with per-source adapters, orchestrated by a consolidation service that handles parallel fetching and graceful degradation.

**Consequences:**
- (+) Clean separation of concerns
- (+) Easy to add new sources
- (+) Individual source failures don't block others
- (-) Increased complexity
- (-) Need to manage multiple configurations

---

## Monitoring Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `source.request.count` | Total requests per source | N/A |
| `source.request.latency` | Response time per source | p99 > 10s |
| `source.request.errors` | Error count per source | > 10/min |
| `source.circuit.state` | Circuit breaker state | OPEN |
| `consolidation.duration` | Total consolidation time | > 30s |
| `deduplication.matches` | Duplicate records found | N/A |

---

## Definition of Done

- [ ] Architecture document complete
- [ ] All diagrams created
- [ ] ADRs written and reviewed
- [ ] Configuration schema defined
- [ ] Monitoring metrics documented
- [ ] Team review completed
- [ ] Sign-off from @pm

---

## Story Points: 5 SP

**Complexity:** Medium (clear scope, familiar patterns)
**Uncertainty:** Low (patterns well-established)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-01 | Blocks this story | Need API research for source-specific configs |

---

## Blocks

- MSP-001-04 (Base Client Refactoring)
- MSP-001-05 through MSP-001-09 (All implementation stories)

---

## Files to Create

- `docs/architecture/multi-source-architecture.md` - Main architecture doc
- `docs/architecture/diagrams/multi-source-flow.png` - Flow diagrams
- `docs/decisions/ADR-001-multi-source-pattern.md`
- `docs/decisions/ADR-002-retry-circuit-breaker.md`
- `docs/decisions/ADR-003-deduplication.md`
- `docs/decisions/ADR-004-configuration.md`

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research Story: `docs/stories/STORY-156-api-research-discovery.md`
- Existing PNCP client: `backend/pncp_client.py`

---

**Story Status:** READY (pending dependency completion)
**Estimated Duration:** 2-3 days
**Priority:** P1 - Critical Path
