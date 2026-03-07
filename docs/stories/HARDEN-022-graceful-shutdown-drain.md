# HARDEN-022: Graceful Shutdown com Task Drain

**Severidade:** MEDIA
**Esforço:** 30 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Quando Railway trigga shutdown, tasks fire-and-forget, Redis connections e ThreadPoolExecutor tasks não são drenados. Gunicorn mata processo após grace period, deixando connections abertas.

## Critérios de Aceitação

- [x] AC1: Lifespan handler com `@asynccontextmanager`
- [x] AC2: Shutdown cancela `_active_background_tasks`
- [x] AC3: Shutdown aguarda pending tasks (gather com timeout 10s)
- [x] AC4: Shutdown fecha Redis pool explicitamente
- [x] AC5: Shutdown cancela cron tasks
- [x] AC6: Teste valida cleanup sequence

## Arquivos Afetados

- `backend/main.py` — lifespan handler
- `backend/redis_pool.py` — close_pool()
- `backend/routes/search.py` — _active_background_tasks access
