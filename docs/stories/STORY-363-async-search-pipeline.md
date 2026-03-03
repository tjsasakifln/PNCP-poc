# STORY-363 — Decouple Search Pipeline from HTTP Request (Async Architecture)

**Status:** done
**Priority:** P0 — Production (causa raiz de CRIT-048, PDF 404, Excel quebrado)
**Origem:** Conselho CTO Advisory — Analise de exports quebrados (2026-03-03)
**Componentes:** backend/routes/search.py, backend/job_queue.py, backend/search_pipeline.py, backend/progress.py
**Depende de:** STORY-362 (TTL + L3 persistence)
**Bloqueia:** STORY-364 (Excel Resilience), STORY-365 (SSE Reconnection)
**Estimativa:** ~8-12h

---

## Contexto — A Causa Raiz

O `POST /buscar` executa o pipeline de busca inteiro **dentro da request HTTP**. O pipeline pode levar ate 360 segundos (timeout chain: Pipeline=360s > Consolidation=300s > PerSource=180s). Porem:

- **Railway hard timeout:** ~120-300 segundos (Railway proxy mata a conexao HTTP)
- **Gunicorn timeout:** 180 segundos (mata o worker)

Quando Railway ou Gunicorn matam a request:
1. `store_background_results()` **nunca executa** (esta apos o pipeline)
2. `_persist_results_to_redis()` **nunca executa**
3. Resultados sao **perdidos permanentemente**
4. PDF, Excel, Google Sheets — todos retornam 404 ("busca expirada")

### Evidencia

```
[SSE-PROXY] CRIT-048: Pipe failure: {
  "error_type": "AbortError",
  "search_id": "873dda5d-3149-4e8c-b3d0-4f41690dbce4",
  "upstream_status": 200,
  "upstream_error": "This operation was aborted",
  "elapsed_ms": 171890    ← ~172 segundos, morto pelo Railway
}
```

| Arquivo | Linha | Problema |
|---------|-------|----------|
| `backend/routes/search.py` | 932, 1080 | `store_background_results()` chamado APOS pipeline — se abort, nunca executa |
| `backend/routes/search.py` | 933, 1081 | `_persist_results_to_redis()` chamado APOS pipeline — idem |
| `backend/config.py` | — | Timeout chain: FE(480s) > Pipeline(360s) > Railway(~120-300s) = **desastre** |

### Arquitetura Atual (quebrada)

```
Frontend ──POST /buscar──→ Backend (Gunicorn worker)
                            │
                            ├─ PNCP client (até 180s)
                            ├─ PCP client (até 180s)
                            ├─ ComprasGov client (até 180s)
                            ├─ Consolidation (até 300s)
                            ├─ Filter + LLM (até 60s)
                            ├─ store_background_results()  ← NUNCA ALCANCA se timeout
                            └─ return BuscaResponse         ← NUNCA RETORNA se timeout
```

### Arquitetura Proposta (resiliente)

```
Frontend ──POST /buscar──→ Backend Web (responde em <3s)
                            │
                            ├─ Gerar search_id
                            ├─ Enqueue job no ARQ (Redis)
                            └─ return {search_id, status: "processing"}

                          ARQ Worker (sem timeout HTTP)
                            │
                            ├─ PNCP + PCP + ComprasGov
                            ├─ Consolidation + Filter + LLM
                            ├─ store_background_results()  ← SEMPRE executa
                            ├─ _persist_results_to_redis() ← SEMPRE executa
                            └─ persist_to_supabase_l3()    ← SEMPRE executa

Frontend ──GET /buscar-progress/{id}──→ SSE (progress)
Frontend ──GET /search/{id}/results──→ JSON (resultados finais)
```

## Acceptance Criteria

### Core: Async Pipeline

- [x] **AC1:** `POST /buscar` retorna em <3 segundos com `{search_id, status: "processing", message: "Busca iniciada"}` (HTTP 202)
- [x] **AC2:** Pipeline de busca executa no ARQ Worker via novo job `execute_search_pipeline`
- [x] **AC3:** Worker persiste resultados em L1 (memory via RPC/event) + L2 (Redis) + L3 (Supabase) ao concluir, **independente** do estado da conexao HTTP
- [x] **AC4:** Se o Worker falhar/crashar, o job e retried automaticamente (max_retries=1)
- [x] **AC5:** `POST /buscar` nunca excede Railway timeout (~120s) — eliminando CRIT-048 como classe de erro

### Progress Tracking

- [x] **AC6:** Progress state persistido no Redis (key: `smartlic:progress:{search_id}`) em vez de apenas `asyncio.Queue` in-memory
- [x] **AC7:** `GET /buscar-progress/{search_id}` le progress do Redis, permitindo reconexao SSE sem perda de estado
- [x] **AC8:** Worker emite progress events no Redis (cada UF concluida, cada fonte concluida)

### Compatibilidade

- [x] **AC9:** `GET /v1/search/{search_id}/status` continua funcionando (ja existe, sem mudanca)
- [x] **AC10:** `GET /v1/search/{search_id}/results` continua funcionando (ja existe, sem mudanca)
- [x] **AC11:** Frontend funciona sem mudancas — SSE progress continua via `GET /buscar-progress/{id}`
- [x] **AC12:** Manter fallback sync para buscas pequenas (1-2 UFs, cache hit) — se resultado disponivel em <5s, retornar inline (otimizacao, nao obrigatorio)

### Seguranca

- [x] **AC13:** Worker valida que o user_id do job corresponde a um usuario valido
- [x] **AC14:** Rate limiting de jobs por usuario (max 3 concurrent searches)

### Testes

- [x] **AC15:** Teste: `POST /buscar` retorna 202 com search_id em <3s
- [x] **AC16:** Teste: Worker processa job e persiste resultados
- [x] **AC17:** Teste: SSE reconnect apos desconexao recebe estado atual
- [x] **AC18:** Teste: Pipeline completa mesmo se frontend desconecta
- [x] **AC19:** Zero regressoes nos testes existentes (5131+ backend, 2681+ frontend)

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/routes/search.py` | Refactor `buscar()`: enqueue job + return 202. Refactor `buscar_progress_stream()`: ler progress do Redis |
| `backend/job_queue.py` | Novo job `execute_search_pipeline`. Config ARQ: timeout, retries |
| `backend/search_pipeline.py` | Adaptar para executar em worker context (sem request object) |
| `backend/progress.py` | Persistir progress no Redis em vez de `asyncio.Queue` |
| `backend/search_context.py` | Adaptar para worker context |
| `backend/config.py` | Novos env vars: `SEARCH_JOB_TIMEOUT`, `MAX_CONCURRENT_SEARCHES` |

## Riscos e Mitigacao

| Risco | Probabilidade | Mitigacao |
|-------|---------------|-----------|
| Regressao em testes existentes | Alta | Run full test suite, fix mock patterns |
| Race condition: frontend pede resultados antes do worker terminar | Media | `GET /search/{id}/status` retorna 202 com progress |
| Worker crash perde job | Baixa | ARQ retry + Redis persistence |
| Deploy zero-downtime: requests em andamento | Media | Feature flag `ASYNC_SEARCH_ENABLED` para rollout gradual |

## Notas Tecnicas

- O ARQ Worker ja esta separado via `PROCESS_TYPE=worker` em `start.sh`
- O Web process e o Worker compartilham Redis — progress events via Redis Pub/Sub ou polling
- Para L1 (in-memory) no web process: o worker nao pode escrever diretamente. Opcoes:
  1. Web process le de L2 (Redis) quando L1 miss — ja implementado em `get_background_results_async()`
  2. Redis Pub/Sub para notificar web process — mais complexo, desnecessario
- **Feature flag recomendado:** `ASYNC_SEARCH_ENABLED=true` — permite rollback rapido para modo sync
- O frontend ja tem fallback para polling via `GET /v1/search/{id}/status` — nao requer mudancas
