# CRIT-071: Partial Results Progressivo via SSE

**Prioridade:** P1 — Melhoria estrutural
**Componente:** Backend (progress.py, search_pipeline.py) + Frontend (useSearchSSEHandler.ts, useSearchExecution.ts)
**Origem:** Investigacao CRIT-070 — `recoverPartialSearch()` retorna null porque SSE so transporta contadores, nao dados reais
**Status:** DONE
**Dependencias:** CRIT-070
**Estimativa:** 1-2 dias

## Problema

Hoje o `recoverPartialSearch()` frequentemente retorna `null` porque partials so sao salvos quando eventos SSE `uf_complete` chegam com `result` populado. Mas `result` e `null` durante o fetch (setado para null na linha 276 de `useSearchExecution.ts`). Os SSE events de progresso chegam, mas nao tem dados de licitacoes para salvar — apenas contadores. O partial esta vazio justamente quando mais e necessario.

### Fluxo atual (falho)

```
1. buscar() → setResult(null) (limpa estado anterior)
2. POST /buscar inicia (bloqueante, 115-224s)
3. SSE emite uf_complete { uf: "SP", found: 320 }
4. savePartialSearch(searchId, result, ...) → result e NULL → partial vazio
5. Timeout → recoverPartialSearch() → null → sem fallback
```

### Fluxo desejado

```
1. buscar() → setResult(null)
2. POST /buscar inicia
3. SSE emite partial_data { licitacoes: [...320 items], batch_index: 1 }
4. Frontend acumula em result.licitacoes (append-only)
5. savePartialSearch(searchId, result, ...) → result TEM DADOS
6. Timeout → recoverPartialSearch() → mostra 320+ resultados parciais
```

### Referencia da industria

Google, Algolia e plataformas de busca modernas entregam resultados **incrementalmente** conforme ficam disponíveis. O SmartLic ja tem o canal SSE funcional — falta transportar dados reais, nao apenas contadores.

## Acceptance Criteria

### AC1: Backend — Emitir evento SSE `partial_data`
- [x] No `search_pipeline.py`, apos cada batch de UFs filtrado, emitir evento SSE:
  ```
  event: partial_data
  data: { "licitacoes": [...], "batch_index": N, "ufs_completed": ["SP","RJ"], "is_final": false }
  ```
- [x] Emitir a cada 5 UFs completas (ou quando batch completo se PNCP_BATCH_SIZE < 5)
- [x] Licitacoes ja devem estar filtradas (pos-keyword, pos-LLM se disponivel)

### AC2: Backend — Limite de payload SSE
- [x] Se batch tem >500 licitacoes, enviar apenas metadados:
  ```
  event: partial_data
  data: { "count": 847, "batch_index": 2, "ufs_completed": ["MG","ES","RJ","SP","PR"], "is_final": false, "truncated": true }
  ```
- [x] Dados completos ficam no cache L1 para `GET /v1/search/{id}/results?partial=true`

### AC3: Backend — Acumular parciais no ProgressTracker
- [x] Novo campo `partial_licitacoes: list[dict]` no `ProgressTracker` (progress.py)
- [x] Callback `on_uf_complete` em `pncp_client.py` alimenta o tracker com resultados filtrados
- [x] Tracker acumula append-only, nunca substitui

### AC4: Frontend — Processar `partial_data` no SSE handler
- [x] `useSearchSSEHandler.ts`: novo case para `partial_data`
- [x] Acumular licitacoes em estado local (ref ou state) — append-only, sem duplicatas (dedup por `id`)
- [x] Atualizar `result` progressivamente: `setResult(prev => ({ ...prev, licitacoes: [...accumulated] }))`

### AC5: Frontend — Salvar partial com dados reais
- [x] `savePartialSearch()` usar dados acumulados do SSE, nao `result` (que pode ser null no inicio)
- [x] Garantir que partial salvo no localStorage tem licitacoes reais

### AC6: Frontend — Banner de resultados parciais
- [x] Quando mostrando partial data: banner "Mostrando X de ~Y resultados. Alguns estados ainda nao completaram."
- [x] Banner some quando POST retorna resultado completo

### AC7: Feature flag
- [x] `PARTIAL_DATA_SSE_ENABLED` (backend config.py, default `True`)
- [x] Se desabilitado, comportamento atual (apenas contadores) preservado

### AC8: Testes
- [x] Backend: emissao de `partial_data` com licitacoes reais a cada batch
- [x] Backend: truncamento quando >500 itens
- [x] Frontend: acumulacao progressiva sem duplicatas
- [x] Frontend: abort com partial_data acumulado → mostra resultados
- [x] Frontend: savePartialSearch tem dados reais (nao null)

## File List

| Arquivo | Mudanca |
|---------|---------|
| `backend/progress.py` | ProgressTracker com partial_licitacoes |
| `backend/search_pipeline.py` | Emitir partial_data events apos batch de UFs |
| `backend/config.py` | Feature flag PARTIAL_DATA_SSE_ENABLED |
| `frontend/app/buscar/hooks/useSearchSSEHandler.ts` | Processar partial_data, acumular |
| `frontend/app/buscar/hooks/useSearchExecution.ts` | Partial recovery melhorado |
| `frontend/app/buscar/hooks/useSearchPersistence.ts` | savePartialSearch com dados SSE |
| `frontend/__tests__/` | Testes unitarios |
| `backend/tests/` | Testes unitarios |

## Referencia

- [Algolia: Progressive Search Results](https://www.algolia.com/blog/ux/mobile-search-ux-part-three-seach-results-display)
- [Vercel: Begin streaming within 25s](https://vercel.com/docs/functions/limitations)
- [Datto: Powering Live UI with SSE](https://datto.engineering/post/powering-a-live-ui-with-server-sent-events)
