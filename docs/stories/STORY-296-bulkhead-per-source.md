# STORY-296: Bulkhead Per Source

**Sprint:** 1 — Make It Reliable
**Size:** M (4-8h)
**Root Cause:** RC-5
**Depends on:** STORY-295
**Industry Standard:** [Microsoft — Bulkhead Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

## Contexto

Hoje todas as fontes (PNCP, PCP, ComprasGov) compartilham o mesmo pool de conexões httpx e o mesmo semáforo de concorrência. Se PNCP trava (rate limit, downtime), consome todas as conexões e PCP/ComprasGov ficam sem recursos.

O Bulkhead Pattern isola cada fonte em seu próprio pool, garantindo que falha de uma não impacte as outras.

## Acceptance Criteria

- [x] AC1: Cada fonte tem seu próprio `asyncio.Semaphore` limitando concorrência
  - PNCP: max 5 concurrent requests (respeitando rate limits)
  - PCP v2: max 3 concurrent requests
  - ComprasGov: max 3 concurrent requests
- [x] AC2: Cada fonte tem seu próprio `httpx.AsyncClient` com connection pool isolado
- [x] AC3: Timeout por fonte configurável via env vars: `PNCP_SOURCE_TIMEOUT`, `PCP_SOURCE_TIMEOUT`, `COMPRASGOV_SOURCE_TIMEOUT`
- [x] AC4: Se PNCP esgota seu semáforo, PCP/ComprasGov continuam normalmente
- [x] AC5: Prometheus metrics por fonte: `smartlic_source_active_requests` (gauge), `smartlic_source_pool_exhausted_total` (counter)
- [x] AC6: Health endpoint reporta status por fonte: `{ pncp: "healthy", pcp: "degraded", comprasgov: "healthy" }`
- [x] AC7: Testes existentes continuam passando

## Technical Design

```python
class SourceBulkhead:
    """Isolates a data source with its own connection pool and concurrency limit."""

    def __init__(self, name: str, max_concurrent: int, timeout: float):
        self.name = name
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=max_concurrent + 2),
            timeout=httpx.Timeout(timeout)
        )
        self._active = 0

    async def execute(self, coro):
        async with self._semaphore:
            self._active += 1
            try:
                return await coro
            finally:
                self._active -= 1
```

## Files Changed

- `backend/bulkhead.py` — **NEW** SourceBulkhead class + registry + initialization
- `backend/config.py` — per-source timeout/concurrency env vars
- `backend/metrics.py` — per-source gauges/counters (active_requests, pool_exhausted, semaphore_wait)
- `backend/consolidation.py` — inject bulkheads per source, wrap _fetch_source
- `backend/search_pipeline.py` — pass bulkheads to ConsolidationService
- `backend/main.py` — initialize bulkheads at startup + health endpoint bulkhead status
- `backend/pncp_client.py` — httpx.Limits for pool isolation (AC2)
- `backend/clients/portal_compras_client.py` — httpx.Limits for pool isolation (AC2)
- `backend/clients/compras_gov_client.py` — httpx.Limits for pool isolation (AC2)
- `backend/tests/conftest.py` — autouse fixture to reset bulkhead registry
- `backend/tests/test_bulkhead.py` — **NEW** 31 tests covering all ACs

## Definition of Done

- [x] Falha de PNCP não impacta latência de PCP/ComprasGov
- [x] Metrics visíveis per-source no /metrics endpoint
- [x] Todos os testes passando
- [ ] PR merged
