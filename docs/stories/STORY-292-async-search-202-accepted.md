# STORY-292: Async Search — 202 Accepted Pattern

**Sprint:** 0 — Make It Work
**Size:** XL (16-24h)
**Root Cause:** RC-4
**Depends on:** STORY-290 (unblock event loop), STORY-291 (CB Supabase)
**Blocks:** STORY-294, STORY-295, STORY-298
**Industry Standard:** [Microsoft — Async Request-Reply Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)

## Contexto

`POST /buscar` executa toda a pipeline inline (auth→fetch→filter→LLM→Excel→persist) e retorna resultado no body. Para 27 UFs pode levar 80-120s. Frontend tem AbortController de 115s. Gunicorn timeout 120s. Margem: zero.

O código já tem `SEARCH_ASYNC_ENABLED` (default false) e path parcial para ARQ jobs. Esta story completa e ativa esse path como o path DEFAULT.

## Acceptance Criteria

### Backend
- [ ] AC1: `POST /buscar` retorna `202 Accepted` em <2s com body:
  ```json
  { "search_id": "uuid", "status_url": "/v1/search/{id}/status" }
  ```
- [ ] AC2: Header `Location: /v1/search/{id}/status` na response 202
- [ ] AC3: Pipeline executa via `asyncio.create_task()` no mesmo worker (não depende de ARQ worker)
- [ ] AC4: `GET /v1/search/{id}/status` retorna estado JSON:
  ```json
  { "status": "pending|running|completed|failed", "progress": 0-100, "result_url": "/v1/search/{id}/results" }
  ```
- [ ] AC5: `GET /v1/search/{id}/results` retorna `BuscaResponse` quando completed, 404 quando pending/running
- [ ] AC6: Resultado final persistido em Supabase `search_results` table (não in-memory)
- [ ] AC7: Se task falha, estado muda para `failed` com error message acessível via status endpoint
- [ ] AC8: SSE `/buscar-progress/{id}` continua funcionando, streamando de Redis (não in-memory dict)
- [ ] AC9: Timeout da task: 120s hard limit com cleanup

### Frontend
- [ ] AC10: Frontend detecta 202 (vs 200 do path antigo) e adapta
- [ ] AC11: Ao receber 202, abre SSE imediatamente com search_id
- [ ] AC12: Se SSE desconecta, fallback para polling `GET /v1/search/{id}/status` a cada 3s
- [ ] AC13: Quando status=completed, fetch resultado via `/v1/search/{id}/results`
- [ ] AC14: Backward compatible: se backend retorna 200 (path sync antigo), funciona como antes

### Quality
- [ ] AC15: Teste e2e: POST→202→SSE→complete→results
- [ ] AC16: Teste: SSE disconnect→polling fallback→results
- [ ] AC17: Teste: task failure→status=failed→error message
- [ ] AC18: Todos os testes existentes passando (ou adaptados)

## Technical Notes

O `SEARCH_ASYNC_ENABLED` path existente usa ARQ (Redis job queue + worker separado). O novo design NÃO depende do ARQ worker — usa `asyncio.create_task()` no mesmo processo, mas persiste estado em Redis/Supabase em vez de retornar no body.

Isso é mais simples que ARQ e evita a dependência de um worker process separado estar rodando.

```
ANTES:  POST /buscar → [120s pipeline] → 200 BuscaResponse
DEPOIS: POST /buscar → 202 {search_id} → [background task] → Redis events → SSE/polling
```

## Files to Change

- `backend/routes/search.py` — refactor buscar_licitacoes() para 202 pattern
- `backend/search_pipeline.py` — persist resultado em Supabase ao final
- `backend/progress.py` — garantir Redis como primary store (não in-memory)
- `frontend/app/api/buscar/route.ts` — handle 202 response
- `frontend/app/buscar/page.tsx` — adapt to 202 + polling fallback
- `frontend/hooks/useSearch.ts` — new state machine for async search

## Definition of Done

- [ ] Busca de 1 UF: 100/100 sucessos
- [ ] Busca de 5 UFs: 95/100 sucessos
- [ ] Zero AbortController timeouts no frontend
- [ ] Zero worker timeout kills no Sentry
- [ ] PR merged + deployed
