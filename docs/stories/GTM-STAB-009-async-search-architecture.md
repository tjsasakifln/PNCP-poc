# GTM-STAB-009 — Modelo de Busca Async (POST Retorna Imediato, Resultados via SSE/Polling)

**Status:** To Do
**Priority:** P2 — Medium (arquitetural, resolve timeout permanentemente)
**Severity:** Architecture — elimina dependência de request longa
**Created:** 2026-02-24
**Sprint:** GTM Stabilization (pós-P0/P1)
**Relates to:** GTM-STAB-003 (timeout chain), GTM-STAB-004 (partial results), GTM-RESILIENCE-F01 (ARQ jobs)

---

## Problema

O modelo atual é **síncrono**: `POST /buscar` bloqueia até o pipeline completar (30-120s+). Isso é fundamentalmente incompatível com:

- Railway proxy timeout (120s)
- Gunicorn worker timeout
- Browser connection limits
- Mobile network instability
- Escalabilidade (1 worker = 1 busca simultânea)

### Modelo atual:
```
Client → POST /buscar → [30-120s bloqueado] → JSON response
         GET /buscar-progress/{id} → SSE (progress only, no results)
```

### Modelo proposto:
```
Client → POST /buscar → 202 Accepted {search_id, status_url} (< 1s)
         GET /buscar-progress/{id} → SSE (progress + partial results)
         GET /v1/search/{id}/results → Polling (final results when ready)
```

---

## Acceptance Criteria

### AC1: POST /buscar retorna 202 Accepted imediatamente
- [ ] `POST /buscar` valida request, cria search_id, enqueue pipeline como ARQ job
- [ ] Response imediata (<1s):
  ```json
  {
    "search_id": "2328ffbe-...",
    "status": "queued",
    "status_url": "/v1/search/2328ffbe-.../status",
    "progress_url": "/buscar-progress/2328ffbe-...",
    "estimated_duration_s": 45
  }
  ```
- [ ] HTTP 202 (não 200) — semântica correta para async
- [ ] Pipeline executa em background (ARQ job ou asyncio.create_task)

### AC2: Pipeline como background job
- [ ] Nova function: `search_pipeline_job(search_id, request_params)` em `job_queue.py`
- [ ] Job executa todo o pipeline (fetch → filter → classify → score → save)
- [ ] Progresso emitido via SSE tracker (mesmo mecanismo atual)
- [ ] Resultado final salvo em Supabase (search_sessions + cache)
- [ ] Se Redis/ARQ indisponível: fallback para asyncio.create_task no web process

### AC3: GET /v1/search/{id}/status — polling endpoint
- [ ] Retorna status atual da busca:
  ```json
  {
    "search_id": "2328ffbe-...",
    "status": "processing|completed|failed|partial",
    "progress_pct": 70,
    "elapsed_s": 45,
    "ufs_completed": ["SP", "ES"],
    "ufs_pending": ["MG", "RJ"],
    "results_count": 28,
    "results_url": "/v1/search/2328ffbe-.../results"
  }
  ```
- [ ] Quando status=completed: `results_url` contém resultado final
- [ ] Endpoint leve (<50ms) — lê de Redis/Supabase, não do pipeline

### AC4: GET /v1/search/{id}/results — resultado final
- [ ] Retorna `BuscaResponse` completo quando pronto
- [ ] Se não pronto: 202 com status (redireciona para polling)
- [ ] Se falhou: 200 com partial results (se disponíveis) ou 404
- [ ] Cache-friendly: response com `Cache-Control: max-age=300` (5 min)

### AC5: Frontend migration
- [ ] `useSearch` hook:
  1. POST /buscar → recebe search_id + 202
  2. Conecta SSE /buscar-progress/{id} (progress + partial)
  3. Quando SSE `complete`: GET /v1/search/{id}/results
  4. Fallback: se SSE falha, polling /v1/search/{id}/status a cada 5s
- [ ] Transição suave: UI mostra progresso imediatamente (não espera response)
- [ ] Se GET results falha: usar partial results do SSE

### AC6: Backward compatibility
- [ ] `POST /buscar` com header `X-Sync: true` ou query `?sync=true` mantém comportamento síncrono
- [ ] Frontend antigo (sem atualização) continua funcionando
- [ ] Transição gradual: flag `ASYNC_SEARCH_ENABLED` (default false inicialmente)
- [ ] Quando stable, flip para default true

### AC7: Timeout eliminado
- [ ] Com async, POST retorna em <1s → ZERO chance de Railway timeout
- [ ] Pipeline job no worker: sem timeout de proxy (worker pode rodar por 10min se necessário)
- [ ] SSE/polling: reconexão automática se desconectar
- [ ] Resultado: ELIMINA 524, WORKER TIMEOUT, SIGABRT, failed to pipe

### AC8: Testes
- [ ] Backend: test POST /buscar retorna 202 com search_id
- [ ] Backend: test /status endpoint retorna progress
- [ ] Backend: test /results endpoint retorna BuscaResponse quando ready
- [ ] Backend: test fallback síncrono com X-Sync: true
- [ ] Frontend: test useSearch com modelo async
- [ ] E2E: busca completa end-to-end no modelo async

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/routes/search.py` | AC1: POST retorna 202, AC3+AC4: novos endpoints |
| `backend/job_queue.py` | AC2: search_pipeline_job |
| `backend/search_pipeline.py` | AC2: executar como job, salvar resultado |
| `backend/config.py` | AC6: ASYNC_SEARCH_ENABLED flag |
| `frontend/app/buscar/hooks/useSearch.ts` | AC5: async flow + polling fallback |
| `frontend/app/api/buscar/route.ts` | AC5: proxy 202 + new endpoints |

---

## Decisões Técnicas

- **202 Accepted** — HTTP semântica correta para operações async. Client entende que precisa poll/listen.
- **ARQ job** — Pipeline pesado (PNCP fetch + LLM calls) deve rodar no worker, não no web process.
- **Polling fallback** — SSE é ideal mas não 100% confiável (proxies, firewalls). Polling é universal e resiliente.
- **Feature flag** — Mudança arquitetural grande, rollback instantâneo se problemas.
- **Esta é a solução definitiva** — GTM-STAB-003 (timeout fit) é paliativo. Esta story elimina a causa raiz.

## Estimativa
- **Esforço:** 12-16h (mudança arquitetural)
- **Risco:** Alto (toca todo o fluxo de busca)
- **Squad:** @architect (design) + @dev (backend async) + @dev (frontend migration) + @qa (E2E)

## Nota

Esta story é P2 porque GTM-STAB-003 (timeout chain reduction) resolve o problema no curto prazo. Esta é a solução **definitiva** que elimina a causa raiz (request longa = vulnerabilidade a timeout). Implementar após P0+P1 estarem stable.
