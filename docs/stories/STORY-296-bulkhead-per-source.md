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

- [ ] AC1: Cada fonte tem seu próprio `asyncio.Semaphore` limitando concorrência
  - PNCP: max 5 concurrent requests (respeitando rate limits)
  - PCP v2: max 3 concurrent requests
  - ComprasGov: max 3 concurrent requests
- [ ] AC2: Cada fonte tem seu próprio `httpx.AsyncClient` com connection pool isolado
- [ ] AC3: Timeout por fonte configurável via env vars: `PNCP_SOURCE_TIMEOUT`, `PCP_SOURCE_TIMEOUT`, `COMPRASGOV_SOURCE_TIMEOUT`
- [ ] AC4: Se PNCP esgota seu semáforo, PCP/ComprasGov continuam normalmente
- [ ] AC5: Prometheus metrics por fonte: `smartlic_source_active_requests` (gauge), `smartlic_source_pool_exhausted_total` (counter)
- [ ] AC6: Health endpoint reporta status por fonte: `{ pncp: "healthy", pcp: "degraded", comprasgov: "healthy" }`
- [ ] AC7: Testes existentes continuam passando

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

## Files to Change

- `backend/pncp_client.py` — use bulkhead semaphore
- `backend/portal_compras_client.py` — use bulkhead semaphore
- `backend/compras_gov_client.py` — use bulkhead semaphore
- `backend/consolidation.py` — inject bulkheads per source
- `backend/config.py` — per-source timeout/concurrency config
- `backend/health.py` — per-source health status
- `backend/metrics.py` — per-source gauges/counters

## Definition of Done

- [ ] Falha de PNCP não impacta latência de PCP/ComprasGov
- [ ] Metrics visíveis per-source no /metrics endpoint
- [ ] Todos os testes passando
- [ ] PR merged
