# GTM-RESILIENCE-A04 — Resposta Parcial Antecipada (Progressive Delivery)

**Track:** A — "Nunca Resposta Vazia" (P0)
**Prioridade:** P0
**Sprint:** 1
**Estimativa:** 6-8 horas
**Gaps cobertos:** P-06 (Pipeline sincrono para o usuario — sem resposta parcial antecipada)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A investigacao estrategica (FRENTE 1 — P-06) identificou que o pipeline de busca e inteiramente sincrono do ponto de vista do usuario: `pipeline.run()` bloqueia ate que TODOS os estagios (Validate → Prepare → Execute → Filter → Enrich → Generate → Persist) completem antes de retornar a resposta HTTP. Com o timeout chain atual (FE 480s, Pipeline 360s), o usuario pode esperar ate **6 minutos** sem ver nenhum resultado.

### Fluxo atual

```
Usuario clica "Buscar"
  → POST /buscar (bloqueia 30-360s)
  → SSE mostra progresso textual ("Buscando SP...", "Filtrando...")
  → Pipeline completa TODOS os estagios
  → HTTP 200 com TODOS os resultados de uma vez
  → Frontend renderiza tudo
```

O SSE atual e informativo (mostra progresso) mas nao entrega dados intermediarios. O usuario ve mensagens de texto sobre o que esta acontecendo, mas nao pode examinar resultados parciais enquanto espera.

### Oportunidade

Quando cache existe para uma busca, os dados de cache podem ser entregues **imediatamente** (< 500ms) enquanto o fetch ao vivo continua em background. O usuario comeca a examinar resultados instantaneamente, e a UI atualiza incrementalmente quando novos dados chegam.

---

## Problema

1. **Latencia percebida inaceitavel**: 30-360s de espera antes de ver qualquer dado. Para um produto premium de R$1.999/mes, isso e incompativel com a expectativa de valor.

2. **Dados existem mas nao sao usados**: Se cache L1/L2/L3 possui resultados para esta busca (o que ocorre em ~60% das buscas repetidas), esses dados so sao considerados como FALLBACK apos falha — nunca como ANTECIPACAO.

3. **SSE subutilizado**: O canal SSE ja esta aberto e funcional, transmitindo eventos de progresso. Ele poderia tambem transmitir blocos de dados parciais (ex: resultados de UFs ja completadas), mas hoje so transmite metadata textual.

---

## Solucao Proposta

### 1. Cache-first response

Quando a busca e iniciada e cache existe:
- Retornar dados do cache imediatamente na resposta HTTP com `response_state: "cached"`
- Disparar fetch ao vivo em background task (`asyncio.create_task`)
- SSE stream permanece aberto para updates

### 2. SSE incremental data delivery

Novo tipo de evento SSE `"partial_results"`:
```json
{
  "stage": "partial_results",
  "progress": 45,
  "message": "5 de 9 UFs processadas",
  "detail": {
    "new_results_count": 23,
    "total_so_far": 67,
    "ufs_completed": ["SP", "RJ", "MG", "PR", "SC"],
    "ufs_pending": ["BA", "CE", "PE", "RS"]
  }
}
```

O frontend, ao receber `"partial_results"`, atualiza a contagem e opcionalmente recarrega os resultados completos via endpoint auxiliar.

### 3. Endpoint de refresh

Novo endpoint `GET /buscar-results/{search_id}` que retorna o estado atual dos resultados de uma busca em andamento. O frontend pode poll este endpoint quando recebe `"partial_results"` para obter os dados atualizados sem esperar o pipeline completar.

### 4. Merge strategy

Quando o fetch ao vivo completa e o cache foi entregue inicialmente:
- SSE emite `"refresh_available"` com diff summary (N novos, M atualizados, K removidos)
- Frontend mostra banner: "Dados atualizados disponiveis" com botao para recarregar
- Merge automatico opcional (configuravel) substitui dados cached por dados ao vivo

---

## Acceptance Criteria

### AC1 — Cache-first: resposta imediata quando cache existe
Quando a busca e iniciada e `get_from_cache_cascade()` retorna dados validos (fresh ou stale), o endpoint `/buscar` DEVE retornar HTTP 200 com os dados do cache em < 2s, com `response_state: "cached"` e `live_fetch_in_progress: true`.

### AC2 — Background fetch disparado apos cache-first
Apos retornar a resposta do cache, o pipeline DEVE disparar `asyncio.create_task()` para executar o fetch ao vivo completo. O SSE stream permanece aberto para updates.

### AC3 — SSE evento `"partial_results"` emitido por UF
A cada UF completada durante o fetch ao vivo, o `ProgressTracker` DEVE emitir evento `"partial_results"` com: `new_results_count`, `total_so_far`, `ufs_completed`, `ufs_pending`.

### AC4 — SSE evento `"refresh_available"` quando fetch completa
Quando o fetch ao vivo completa (apos cache-first), o SSE DEVE emitir `"refresh_available"` com: `total_live`, `total_cached`, `new_count`, `updated_count`, `removed_count`.

### AC5 — Endpoint `GET /buscar-results/{search_id}`
Novo endpoint que retorna os resultados atuais de uma busca em andamento ou recem-completada. Retorna 404 se `search_id` nao existe ou expirou.

### AC6 — Frontend: renderiza cache imediatamente
Quando `response_state === "cached"` e `live_fetch_in_progress === true`, o frontend DEVE renderizar os resultados do cache imediatamente com indicador visual de "Atualizando..." (spinner sutil, nao loading screen).

### AC7 — Frontend: interpreta `"partial_results"` via SSE
O hook `useSearchProgress` DEVE reconhecer `"partial_results"` como evento nao-terminal e expor campo `partialProgress: { newCount, totalSoFar, ufsCompleted, ufsPending }`.

### AC8 — Frontend: banner "Dados atualizados disponiveis"
Quando SSE emite `"refresh_available"`, o frontend DEVE mostrar banner discreto (nao modal) com: "Dados atualizados disponiveis — X novas oportunidades" e botao "Atualizar resultados".

### AC9 — Frontend: botao "Atualizar resultados" faz fetch de `/buscar-results/{search_id}`
Ao clicar no banner de refresh, o frontend DEVE chamar `GET /buscar-results/{search_id}` e substituir os dados em tela pelos dados ao vivo, removendo o banner.

### AC10 — Busca sem cache: fluxo inalterado
Quando cache nao existe para a busca corrente, o fluxo DEVE permanecer sincrono (pipeline bloqueia ate conclusao) — sem regressao.

### AC11 — Background task nao bloqueia shutdown
A task de background DEVE ter timeout proprio (= FETCH_TIMEOUT) e DEVE ser cancelavel em caso de shutdown do servidor (graceful shutdown).

### AC12 — Teste backend: cache-first retorna em < 2s
Teste que mede latencia: quando cache existe, `/buscar` DEVE retornar resposta HTTP em menos de 2000ms (com mock de cache).

### AC13 — Teste backend: background fetch executa apos resposta
Teste que verifica: apos resposta cache-first, a task de background e criada e executa o fetch ao vivo (mock de pipeline stages).

### AC14 — Teste backend: `"partial_results"` emitido
Teste que verifica: durante fetch ao vivo, `ProgressTracker` emite `"partial_results"` com contagem correta a cada UF completada.

### AC15 — Teste backend: endpoint `GET /buscar-results/{search_id}` retorna dados
Teste: apos busca completar, `GET /buscar-results/{search_id}` retorna os resultados com HTTP 200.

### AC16 — Teste frontend: renderizacao imediata de cache
Teste de componente: response com `response_state="cached"` + `live_fetch_in_progress=true` → resultados renderizados + indicador "Atualizando...".

### AC17 — Teste frontend: banner de refresh
Teste de componente: SSE evento `"refresh_available"` → banner aparece com contagem de novas oportunidades e botao "Atualizar".

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/search_pipeline.py` | Cache-first path; background task dispatch; `_execute_background_fetch()` |
| `backend/progress.py` | `emit_partial_results()`, `emit_refresh_available()` |
| `backend/schemas.py` | `live_fetch_in_progress: bool` no `BuscaResponse` |
| `backend/routes/search.py` | Novo endpoint `GET /buscar-results/{search_id}` |
| `frontend/hooks/useSearchProgress.ts` | Interpretar `partial_results`, `refresh_available` |
| `frontend/hooks/useSearch.ts` | Logica de cache-first + refresh |
| `frontend/app/buscar/components/RefreshBanner.tsx` | **NOVO** — banner "Dados atualizados" |
| `frontend/app/buscar/components/SearchResults.tsx` | Indicador "Atualizando..." para cache-first |
| `backend/tests/test_progressive_delivery.py` | **NOVO** — AC12-AC15 |
| `frontend/__tests__/buscar/progressive-delivery.test.tsx` | **NOVO** — AC16-AC17 |

---

## Dependencias

| Story | Relacao |
|-------|---------|
| **A-01** (Timeout Cache Fallback) | A-01 define `response_state` e `get_from_cache_cascade()` que A-04 usa para cache-first. A-01 DEVE ser completada antes de A-04. |
| **A-02** (SSE Degraded) | A-02 adiciona vocabulario de eventos SSE. A-04 estende com `partial_results` e `refresh_available`. Podem ser paralelas. |
| **A-03** (L3 Cache Read) | A-03 completa o cascade de cache. A-04 se beneficia mas nao depende — funciona com apenas L1/L2. |

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Merge de dados cached + live causa duplicatas | Media | Alto | Dedup por `pncp_id` / `source_id` com prioridade para dados live |
| Background task orfanada consome recursos | Baixa | Medio | Timeout + cancel em shutdown; max 1 task por search_id |
| SSE event storm (27 UFs = 27 partial_results) | Alta | Baixo | Debounce: emitir a cada 3 UFs ou a cada 10s, o que vier primeiro |
| Inconsistencia entre cache entregue e dados finais | Media | Medio | Banner de refresh e explicito — usuario decide quando atualizar |
| Frontend re-render excessivo | Media | Medio | Memoizar resultados; diff minimo no state update |

---

## Notas Tecnicas

### Armazenamento de resultados intermediarios

Os resultados parciais do fetch ao vivo sao armazenados no `SearchContext` da task de background. O endpoint `GET /buscar-results/{search_id}` acessa esse contexto via mapa in-memory (similar ao `ProgressTracker` registry). TTL de 10 minutos apos conclusao.

### Debounce de SSE partial_results

Para evitar flood de eventos, `partial_results` e emitido:
- A cada batch de UFs completado (nao a cada UF individual)
- Ou a cada 10 segundos se nenhum batch completou (heartbeat com contagem)
- Maximo 10 eventos `partial_results` por busca

### Compatibilidade

O endpoint `/buscar` mantém assinatura identica. O campo `live_fetch_in_progress` e adicionado (nao breaking). Clients que nao consomem SSE continuam funcionando normalmente com a resposta cache-first.

---

## Definition of Done

- [ ] Todos os 17 ACs verificados e passing
- [ ] Testes backend: 4 novos, zero regressoes
- [ ] Testes frontend: 2 novos, zero regressoes
- [ ] TypeScript check (`npx tsc --noEmit`) passing
- [ ] Demonstracao: busca com cache → resposta imediata → SSE partial_results → banner refresh
- [ ] Regressao: busca sem cache → fluxo sincrono inalterado
- [ ] Latencia cache-first < 2s medida em producao
- [ ] Code review aprovado
- [ ] Commit convencional: `feat(backend+frontend): GTM-RESILIENCE-A04 — progressive delivery with cache-first + SSE incremental`
