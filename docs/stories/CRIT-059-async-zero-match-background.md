# CRIT-059: Mover Zero-Match LLM para Background (ARQ Job Async)

**Prioridade:** HIGH
**Componente:** Backend — filter.py, search_pipeline.py, job_queue.py, progress.py, routes/search.py; Frontend — SearchResults, useSearch
**Origem:** Incidente 2026-03-05 — LLM zero-match dentro do filtro sincrono causa timeout de pipeline
**Status:** TODO
**Dependencias:** CRIT-057 + CRIT-058 (safety nets devem existir antes desta refatoracao)
**Estimativa:** 1-2 dias

## Problema

A arquitetura atual executa classificacao LLM zero-match DENTRO de `aplicar_todos_filtros()` — uma funcao sincrona chamada na thread do request. Mesmo com cap (CRIT-058) e budget (CRIT-057), o design fundamental e fragil:

1. **Chamadas LLM bloqueiam o pipeline sincrono** — qualquer aumento de latencia da OpenAI API propaga diretamente para o tempo de resposta
2. **Resultados keyword-match ficam retidos** — usuario espera 30-60s extras por classificacoes zero-match que poderia receber incrementalmente
3. **Nao escala** — 10 usuarios simultaneos com 200 zero-match cada = 2.000 calls LLM sequenciais

### Precedente no Codebase

O pattern ja existe: **F01 (ARQ Job Queue)** faz exatamente isso para LLM summaries:
- `job_queue.py` despacha `generate_summary_job` para ARQ worker
- Resposta imediata com `gerar_resumo_fallback()`
- SSE emite `llm_ready` quando summary fica pronta
- Frontend atualiza resultado in-place

Zero-match deve seguir o mesmo pattern.

## Acceptance Criteria

### AC1: Separar zero-match do filtro sincrono
- [ ] `aplicar_todos_filtros()` NAO faz mais chamadas LLM zero-match inline
- [ ] Filtro retorna resultados keyword-match imediatamente
- [ ] Itens zero-match sao coletados em `zero_match_candidates: List[dict]`
- [ ] `zero_match_candidates` e retornado no resultado do filtro (nao descartado)

### AC2: ARQ job para zero-match classification
- [ ] Novo job: `classify_zero_match_job(search_id, candidates, setor, sector_name)` em `job_queue.py`
- [ ] Job aplica cap (CRIT-058) e budget (CRIT-057) internamente
- [ ] Job salva resultados classificados no Redis: `zero_match:{search_id}` (TTL 1h)
- [ ] Job emite SSE event ao completar

### AC3: SSE eventos incrementais
- [ ] Novo evento SSE: `zero_match_started` — emitido quando job e enfileirado
  ```json
  {"event": "zero_match_started", "data": {"candidates": 1831, "will_classify": 200}}
  ```
- [ ] Novo evento SSE: `zero_match_progress` — emitido a cada batch completado
  ```json
  {"event": "zero_match_progress", "data": {"classified": 80, "total": 200, "approved": 12}}
  ```
- [ ] Novo evento SSE: `zero_match_ready` — emitido quando classificacao termina
  ```json
  {"event": "zero_match_ready", "data": {"total_classified": 200, "approved": 42, "rejected": 158}}
  ```

### AC4: Endpoint de fetch dos resultados zero-match
- [ ] `GET /v1/search/{search_id}/zero-match` — retorna itens aprovados pelo LLM zero-match
- [ ] Response: lista de licitacoes com `_relevance_source: "llm_zero_match"` e enrichment
- [ ] 404 se job ainda nao completou; 200 com lista vazia se nenhum aprovado
- [ ] Rate limit: 10 req/min por user (evitar polling agressivo)

### AC5: Frontend — resultados incrementais
- [ ] Ao receber `zero_match_started`: mostrar badge "Analisando mais X oportunidades com IA..."
- [ ] Ao receber `zero_match_progress`: atualizar progress bar/counter dentro do badge
- [ ] Ao receber `zero_match_ready`: fetch `/v1/search/{id}/zero-match` e merge com resultados existentes
- [ ] Resultados zero-match aparecem com badge visual distinto (ex: "Classificado por IA")
- [ ] Se usuario navega para outra pagina e volta, fetch do endpoint (nao depende do SSE)

### AC6: Resposta imediata do pipeline
- [ ] `POST /buscar` retorna em <30s com resultados keyword-match
- [ ] Campo `zero_match_job_id` no BuscaResponse indica que classificacao esta em andamento
- [ ] Campo `zero_match_candidates_count` indica quantos itens estao pendentes
- [ ] `is_simplified` NAO e ativado por causa de zero-match (zero-match nao conta para budget)

### AC7: Graceful degradation
- [ ] Se ARQ worker esta indisponivel: zero-match candidates viram `pending_review` (como CRIT-057)
- [ ] Se Redis esta indisponivel para salvar resultados: log warning, nenhum crash
- [ ] Se job falha mid-way: resultados parciais sao salvos + SSE event `zero_match_error`
- [ ] Timeout global do job: 120s (configuravel via `ZERO_MATCH_JOB_TIMEOUT_S`)

### AC8: Metricas e observabilidade
- [ ] `smartlic_zero_match_job_duration_seconds` (Histogram)
- [ ] `smartlic_zero_match_job_status_total` (Counter, labels: status=completed|failed|timeout)
- [ ] `smartlic_zero_match_job_queue_time_seconds` (Histogram — tempo entre enqueue e start)
- [ ] Log structured: job_id, search_id, candidates_count, classified_count, approved_count, duration_s

### AC9: Testes backend
- [ ] `test_crit059_async_zero_match.py`:
  - Filtro retorna imediatamente sem LLM (zero_match_candidates populado)
  - Job classifica candidates corretamente
  - SSE eventos emitidos na ordem certa (started → progress → ready)
  - Endpoint `/search/{id}/zero-match` retorna resultados apos job completar
  - Graceful degradation: ARQ indisponivel → pending_review
  - Job timeout → resultados parciais salvos
- [ ] Zero regressoes em `test_filter.py`, `test_search_pipeline.py`

### AC10: Testes frontend
- [ ] `test_crit059_incremental_results.test.tsx`:
  - Badge "Analisando..." aparece ao receber `zero_match_started`
  - Resultados keyword-match exibidos imediatamente (sem esperar zero-match)
  - Merge correto ao receber `zero_match_ready`
  - Navegacao ida-volta busca resultados do endpoint (nao perde dados)

### AC11: Feature flag
- [ ] `ASYNC_ZERO_MATCH_ENABLED` (default: `false` — opt-in durante rollout)
- [ ] Quando `false`: comportamento atual (inline, com CRIT-057/058 como safety)
- [ ] Quando `true`: novo fluxo async
- [ ] Flip via env var sem redeploy (Railway variables)

## Diagrama de Fluxo

```
BUSCA REQUEST
  |
  v
[stage_filter] -- keyword match --> resultados_keyword (retorno imediato)
  |                                      |
  +-- zero_match_candidates ---------->  [POST /buscar response]
        |                                   campos: zero_match_job_id,
        v                                          zero_match_candidates_count
  [ARQ: classify_zero_match_job]
        |
        +-- SSE: zero_match_started
        |
        +-- batch 1..N (cap=200, budget=30s)
        |     |
        |     +-- SSE: zero_match_progress (cada batch)
        |
        +-- salva em Redis: zero_match:{search_id}
        |
        +-- SSE: zero_match_ready
              |
              v
        [GET /v1/search/{id}/zero-match] <-- frontend fetch
```

## Risco e Mitigacao

| Risco | Mitigacao |
|-------|-----------|
| ARQ worker pode estar sobrecarregado com jobs de summary + zero-match | Fila separada ou prioridade (summaries > zero-match) |
| Redis como store temporario pode perder dados em restart | TTL de 1h e suficiente; se perdeu, usuario refaz busca |
| Frontend complexity aumenta (merge de resultados) | Componente isolado `ZeroMatchResults.tsx` com estado proprio |
| Rollback se async falhar | Feature flag `ASYNC_ZERO_MATCH_ENABLED=false` reverte instantaneamente |

## File List

| Arquivo | Mudanca |
|---------|---------|
| `backend/config.py` | `ASYNC_ZERO_MATCH_ENABLED`, `ZERO_MATCH_JOB_TIMEOUT_S` |
| `backend/filter.py` | Remover LLM inline, retornar `zero_match_candidates` |
| `backend/search_pipeline.py` | Despachar ARQ job se async enabled |
| `backend/job_queue.py` | `classify_zero_match_job()` |
| `backend/progress.py` | Novos eventos SSE: `zero_match_started/progress/ready` |
| `backend/routes/search.py` | `GET /v1/search/{id}/zero-match` endpoint |
| `backend/schemas.py` | `BuscaResponse.zero_match_job_id`, `zero_match_candidates_count` |
| `backend/metrics.py` | Metricas de job |
| `backend/redis_client.py` | Helper para `zero_match:{search_id}` store |
| `frontend/hooks/useZeroMatchResults.ts` | Hook para SSE events + fetch |
| `frontend/app/buscar/components/ZeroMatchBadge.tsx` | Badge "Analisando..." |
| `frontend/app/buscar/components/SearchResults.tsx` | Merge incremental |
| `frontend/app/api/search-zero-match/route.ts` | Proxy para endpoint |
| `backend/tests/test_crit059_async_zero_match.py` | Testes backend |
| `frontend/__tests__/crit059-incremental-results.test.tsx` | Testes frontend |
