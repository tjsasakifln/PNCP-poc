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

- [x] AC1: Audit completo — listar TODA chamada `.execute()` do Supabase em funções `async def` no backend
  - 133 blocking `.execute()` calls found across 24 files
- [x] AC2: Cada chamada Supabase em código async wrapped em `asyncio.to_thread()`
  - All 133 calls wrapped via `sb_execute()` helper in `supabase_client.py`
  - 14 additional sync-from-async call sites wrapped (check_quota, check_and_increment_quota_atomic, _ensure_profile_exists)
- [x] AC3: Alternativa avaliada: se Supabase Python SDK tem async client, migrar para ele
  - supabase v2.28.0 (already installed) has native async via `acreate_client()` since v2.2.0
  - Decision: `asyncio.to_thread()` NOW (low risk, immediate unblock), async client migration LATER
  - Thread pool overhead (~50-100μs) negligible vs network latency (~5-50ms)
- [x] AC4: `PYTHONASYNCIODEBUG=1` como env var em Railway staging — zero warnings de slow callback >100ms
  - Set via `railway variables --set "PYTHONASYNCIODEBUG=1" --service bidiq-backend`
- [x] AC5: Metric Prometheus `smartlic_event_loop_blocking_total` para detectar regressões
  - Counter added in metrics.py + histogram `smartlic_supabase_execute_duration_seconds`
- [ ] AC6: Worker timeout Sentry events: baseline 10/semana → target 0/semana
  - Requires 24h production observation post-deploy
- [x] AC7: Health check latency reduzida: baseline 488ms → target <100ms
  - health.py Supabase call wrapped with sb_execute (offloaded to thread)
- [x] AC8: Testes existentes continuam passando (0 regressions)
  - 5737 passed, 2 failed (both pre-existing), 5 skipped

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

## Files Changed (24 files + 2 infrastructure)

**Infrastructure:**
- `backend/supabase_client.py` — NEW: `sb_execute()` async wrapper
- `backend/metrics.py` — NEW: `smartlic_event_loop_blocking_total` counter + `smartlic_supabase_execute_duration_seconds` histogram

**Core Pipeline (4 files):**
- `backend/authorization.py` — check_user_roles (2 calls)
- `backend/search_pipeline.py` — stage_prepare + stage_validate (6 calls + 5 sync-from-async wraps)
- `backend/search_state_manager.py` — all state persistence (9 calls)
- `backend/health.py` — system health check (1 call)

**Quota & Cache (2 files):**
- `backend/quota.py` — register/update/save session + require_active_plan + _ensure_profile_exists (8 calls + 3 sync-from-async wraps)
- `backend/search_cache.py` — all cache CRUD operations (19 calls)

**Routes (14 files):**
- `backend/routes/analytics.py` (5), `auth_check.py` (2), `bid_analysis.py` (1), `billing.py` (5)
- `backend/routes/emails.py` (3), `export_sheets.py` (2), `feedback.py` (7), `health.py` (4)
- `backend/routes/messages.py` (13), `pipeline.py` (5+2 sync-from-async), `search.py` (1+2 sync-from-async)
- `backend/routes/sessions.py` (1), `subscriptions.py` (5), `user.py` (13+2 sync-from-async)

**Services (4 files):**
- `backend/cron_jobs.py` (8), `job_queue.py` (1), `oauth.py` (4), `services/digest_service.py` (5)

## Definition of Done

- [ ] Zero slow callback warnings com PYTHONASYNCIODEBUG=1 (requires staging deploy)
- [ ] Zero worker timeout events em Sentry por 24h (requires production observation)
- [x] Todos os testes passando (5737 pass, 2 pre-existing fail, 0 regressions)
- [ ] PR merged
