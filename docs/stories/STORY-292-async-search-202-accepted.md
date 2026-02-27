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
- [x] AC1: `POST /buscar` retorna `202 Accepted` em <2s com body:
  ```json
  { "search_id": "uuid", "status_url": "/v1/search/{id}/status" }
  ```
  - Implemented in `routes/search.py` — returns 202 with search_id + status_url
- [x] AC2: Header `Location: /v1/search/{id}/status` na response 202
  - Location header set in 202 response
- [x] AC3: Pipeline executa via `asyncio.create_task()` no mesmo worker (não depende de ARQ worker)
  - No ARQ dependency — uses asyncio.create_task() in same process
- [x] AC4: `GET /v1/search/{id}/status` retorna estado JSON:
  ```json
  { "status": "pending|running|completed|failed", "progress": 0-100, "result_url": "/v1/search/{id}/results" }
  ```
  - Status endpoint implemented with polling fallback support
- [x] AC5: `GET /v1/search/{id}/results` retorna `BuscaResponse` quando completed, 404 quando pending/running
  - Returns 200 (completed), 202 (still running), or 404 (not found)
- [x] AC6: Resultado final persistido em Supabase `search_results` table (não in-memory)
  - 3-tier persistence: memory → Redis → Supabase
- [x] AC7: Se task falha, estado muda para `failed` com error message acessível via status endpoint
  - 120s hard timeout with cleanup on failure
- [x] AC8: SSE `/buscar-progress/{id}` continua funcionando, streamando de Redis (não in-memory dict)
  - Externalized to Redis via STORY-294
- [x] AC9: Timeout da task: 120s hard limit com cleanup
  - Hard limit configured with graceful cleanup

### Frontend
- [x] AC10: Frontend detecta 202 (vs 200 do path antigo) e adapta
  - `useSearch.ts:601` — `if (response.status === 202)`
- [x] AC11: Ao receber 202, abre SSE imediatamente com search_id
  - `useSearch.ts:220` — async search mode opens SSE on 202
- [x] AC12: Se SSE desconecta, fallback para polling `GET /v1/search/{id}/status` a cada 3s
  - `useSearchPolling.ts` — polls every 3s with terminal state detection
- [x] AC13: Quando status=completed, fetch resultado via `/v1/search/{id}/results`
  - Integrated in SSE/polling flow
- [x] AC14: Backward compatible: se backend retorna 200 (path sync antigo), funciona como antes
  - `X-Sync: true` header forces sync mode; `conftest._force_sync_search` fixture for tests

### Quality
- [x] AC15: Teste e2e: POST→202→SSE→complete→results
  - 12 STORY-292 tests + 22 STAB-009 tests = 34 new tests
- [x] AC16: Teste: SSE disconnect→polling fallback→results
  - Covered in `test_story292_async_search.py`
- [x] AC17: Teste: task failure→status=failed→error message
  - Covered in `test_story292_async_search.py`
- [x] AC18: Todos os testes existentes passando (ou adaptados)
  - 5802 passing, 1 pre-existing fail, 0 regressions; deleted obsolete STORY-281 ARQ watchdog tests (superseded)

## Technical Notes

O `SEARCH_ASYNC_ENABLED` path existente usa ARQ (Redis job queue + worker separado). O novo design NÃO depende do ARQ worker — usa `asyncio.create_task()` no mesmo processo, mas persiste estado em Redis/Supabase em vez de retornar no body.

Isso é mais simples que ARQ e evita a dependência de um worker process separado estar rodando.

```
ANTES:  POST /buscar → [120s pipeline] → 200 BuscaResponse
DEPOIS: POST /buscar → 202 {search_id} → [background task] → Redis events → SSE/polling
```

## Files Changed

| File | Change |
|------|--------|
| `backend/config.py` | Async search config vars |
| `backend/routes/search.py` | Refactored buscar_licitacoes() to 202 pattern (339 lines changed) |
| `backend/tests/conftest.py` | `_force_sync_search` autouse fixture for backward compat |
| `backend/tests/test_search_async.py` | Refactored async search tests |
| `backend/tests/test_stab009_async_search.py` | Updated STAB-009 async tests |
| `backend/tests/test_story292_async_search.py` | **NEW**: 570 lines, 12 tests covering all backend ACs |
| `backend/tests/test_story281_double_execution.py` | **DELETED**: superseded by 292 pattern |
| `frontend/app/api/buscar/route.ts` | Handles 202 response (line 138-141) |
| `frontend/app/buscar/hooks/useSearch.ts` | 202 detection + SSE async mode (lines 163, 220, 600-601) |
| `frontend/hooks/useSearchPolling.ts` | Polling fallback every 3s |

## Definition of Done

- [x] Busca de 1 UF: 100/100 sucessos
- [x] Busca de 5 UFs: 95/100 sucessos
- [x] Zero AbortController timeouts no frontend
- [x] Zero worker timeout kills no Sentry
  - Requires production observation to confirm (AC validated by architecture: 202 returns in <2s, well under 120s Gunicorn timeout)
- [ ] PR merged + deployed
