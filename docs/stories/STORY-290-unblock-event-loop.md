# STORY-290: Unblock Event Loop — Eliminar Chamadas Síncronas em Código Async

**Sprint:** 0 — Make It Work
**Size:** L (8-16h)
**Root Cause:** RC-2
**Blocks:** STORY-292
**Industry Standard:** [FastAPI — async/await](https://fastapi.tiangolo.com/async/)

## Contexto

O Supabase Python client (postgrest-py) é síncrono. Chamadas `.execute()` dentro de `async def` bloqueiam o event loop do Uvicorn por 200-500ms cada. Durante esse tempo, NENHUMA coroutine roda — SSE heartbeats param, Gunicorn não recebe heartbeat do worker, mata o processo com SIGABRT.

**Evidência Sentry:** `WORKER KILLED BY TIMEOUT` (5 events), `Worker was sent SIGABRT` (5 events)
**Evidência código:** `search_pipeline.py:878` — sync `.execute()` em `async def stage_prepare()`

## Acceptance Criteria

- [ ] AC1: Audit completo — listar TODA chamada `.execute()` do Supabase em funções `async def` no backend
- [ ] AC2: Cada chamada Supabase em código async wrapped em `asyncio.to_thread()`
- [ ] AC3: Alternativa avaliada: se Supabase Python SDK tem async client, migrar para ele
- [ ] AC4: `PYTHONASYNCIODEBUG=1` como env var em Railway staging — zero warnings de slow callback >100ms
- [ ] AC5: Metric Prometheus `smartlic_event_loop_blocking_total` para detectar regressões
- [ ] AC6: Worker timeout Sentry events: baseline 10/semana → target 0/semana
- [ ] AC7: Health check latency reduzida: baseline 488ms → target <100ms
- [ ] AC8: Testes existentes continuam passando (0 regressions)

## Technical Notes

```python
# ANTES (bloqueia event loop):
async def stage_prepare(self, ctx):
    row = db.table("profiles").select("context_data").eq("id", uid).execute()

# DEPOIS (offload para thread pool):
async def stage_prepare(self, ctx):
    row = await asyncio.to_thread(
        lambda: db.table("profiles").select("context_data").eq("id", uid).execute()
    )
```

Ou wrapper genérico:
```python
async def sb_execute(query):
    """Non-blocking Supabase query execution."""
    return await asyncio.to_thread(query.execute)
```

## Files to Change

- `backend/search_pipeline.py` — stage_prepare, stage_validate, stage_persist
- `backend/routes/search.py` — require_active_plan, session registration
- `backend/quota.py` — check_quota, check_and_increment_quota_atomic
- `backend/auth.py` — _check_user_roles
- `backend/search_cache.py` — Supabase cache reads/writes
- `backend/health.py` — cache health check

## Definition of Done

- [ ] Zero slow callback warnings com PYTHONASYNCIODEBUG=1
- [ ] Zero worker timeout events em Sentry por 24h
- [ ] Todos os testes passando
- [ ] PR merged
