# CRIT-003: Implementar State Machine Explicito para Buscas

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 2: Consistencia

## Prioridade
P0

## Estimativa
20h

## Descricao

Hoje, o estado de uma busca e efemero — vive em dicts in-memory (`_active_trackers`, `_background_results`, `_active_background_tasks`) e asyncio.Queues que sao destruidos no restart do servidor. Nao existe tabela dedicada de estado de execucao, e os eventos SSE sao fire-and-forget sem persistencia.

Esta story implementa um state machine explicito e persistido para buscas, garantindo que:
1. Todo estado transiciona de forma deterministica e auditavel
2. Restart do servidor nao perde buscas em andamento
3. SSE pode ser derivado do estado persistido (nao o contrario)
4. Frontend pode recuperar estado via polling quando SSE falha

### Estado atual (evidencia):

| Storage | TTL | Sobrevive restart? |
|---------|-----|-------------------|
| `_active_trackers` dict (progress.py:287) | 5 min | NAO |
| Redis `bidiq:progress:{search_id}` | 5 min | Sim (se Redis) |
| Redis pub/sub channel | Efemero | NAO |
| `_background_results` dict (search.py:61) | 10 min | NAO |
| `_active_background_tasks` dict (search.py:63) | Ate completar | NAO |

### Problemas criticos:
- Tracker TTL (300s) < Pipeline FETCH_TIMEOUT (360s) — tracker pode ser limpo antes da busca terminar
- Race condition: POST response e SSE terminal event nao sao sincronizados
- Se SSE cai e reconecta, eventos emitidos entre disconnect e reconnect sao perdidos permanentemente
- ARQ job results (`llm_ready`, `excel_ready`) nao tem polling fallback — se SSE cai, ficam "processing" eternamente
- Dual EventSource no frontend (`useSearchProgress` + `useUfProgress`) duplica conexoes sem coordenacao

## Especialistas Consultados
- Systems Architect (State Machine Specialist) — mapeamento completo do lifecycle
- UX Architect — user journey durante falhas de SSE
- Observability Architect — gaps de rastreamento

## Evidencia da Investigacao

### SSE Events (16 tipos, nenhum persistido):
- Terminais: `complete`, `degraded`, `error`, `refresh_available`
- Informativos: `connecting`, `fetching`, `uf_status`, `batch_progress`, `filtering`, `filtering_complete`, `llm`, `excel`, `llm_ready`, `excel_ready`, `partial_results`, `revalidated`

### Frontend state variables (dispersos, nao machine):
- `loading`, `loadingStep`, `statesProcessed`, `error`, `quotaError`, `result`, `searchId`, `useRealProgress`, `liveFetchInProgress`, `sseEvent`, `sseAvailable`, `sseDisconnected`, `isDegraded`, `partialProgress`, `refreshAvailable`

### Race condition documentada:
- POST retorna quando `pipeline.run()` completa (search_pipeline.py)
- Wrapper emite terminal SSE event logo apos (routes/search.py:480-497)
- Frontend pode receber terminal SSE ANTES ou DEPOIS do POST response

## Criterios de Aceite

### State Machine Definition
- [x] AC1: Criar enum `SearchState` com transicoes validas: `models/search_state.py` — 11 estados, `VALID_TRANSITIONS` map
- [x] AC2: Cada transicao de estado DEVE ser persistida em banco — `search_state_manager.py` fire-and-forget via `asyncio.create_task`
- [x] AC3: Transicoes invalidas devem ser rejeitadas com log CRITICAL — `validate_transition()` em `models/search_state.py`
- [x] AC4: Cada estado carrega metadata — `StateTransition` dataclass com timestamp, duration_since_previous, details

### Persistencia de Estado
- [x] AC5: Criar tabela `search_state_transitions` (audit trail) — `migrations/008_search_state_transitions.sql`
- [x] AC6: Cada transicao gera INSERT nesta tabela (fire-and-forget) — `_persist_transition()` via `asyncio.create_task`
- [x] AC7: Endpoint `GET /v1/search/{search_id}/timeline` — `routes/search.py:306`

### SSE Derivado de Estado
- [x] AC8: SSE events derivados do estado persistido — SSE endpoint lê DB state quando tracker inexiste (reconnect)
- [x] AC9: Se SSE reconecta, cliente recebe estado ATUAL do banco — `routes/search.py:198-222` via `get_current_state()`
- [x] AC10: ProgressTracker fallback para estado do banco — SSE endpoint route-level fallback quando Queue vazia

### Polling Fallback
- [x] AC11: Endpoint `GET /v1/search/{search_id}/status` — `routes/search.py:286`, proxy `app/api/search-status/route.ts`
- [x] AC12: Frontend polling quando `sseDisconnected=true` (intervalo 3s) — `useSearchPolling.ts` + `useSearch.ts:222`
- [x] AC13: Polling para quando status terminal — `TERMINAL_STATUSES` set check em `useSearchPolling.ts:96`

### Tracker TTL Fix
- [x] AC14: `_TRACKER_TTL` = 420s >= FETCH_TIMEOUT 360s + margem — `progress.py:296`
- [x] AC15: Tracker cleanup nao remove trackers ativos — `_cleanup_stale()` verifica `machine.is_terminal` antes de remover

### Startup Recovery
- [x] AC16: Na inicializacao, queries search_sessions com status processing — `main.py:377` lifespan handler
- [x] AC17: Buscas > 10 min: timed_out — `recover_stale_searches()` em `search_state_manager.py`
- [x] AC18: Buscas < 10 min: failed com retry message — mesmo handler, mensagem "retry recommended"

### Frontend Consolidation
- [x] AC19: Consolidar `useSearchProgress` + `useUfProgress` em `useSearchSSE` — hook consolidado em `hooks/useSearchSSE.ts`, integrado via `useSearch.ts`
- [x] AC20: Unica instancia de EventSource gerencia todos os event types — `useSearchSSE` com `onmessage` + named event listeners
- [x] AC21: Se SSE falha apos 1 retry, switch para polling — `sseDisconnected=true` ativa `useSearchPolling`

### Observability
- [x] AC22: Prometheus histogram `search_state_duration_seconds` — `metrics.py:110`, observado em `search_state_manager.py:100`
- [x] AC23: Log estruturado em cada transicao — `search_state_manager.py:84-95` com search_id, state, stage, duration_ms

## Testes Obrigatorios

- [x] State machine rejects invalid transitions — `test_search_state.py::TestTransitionValidation`
- [x] Every pipeline stage updates state correctly — `search_pipeline.py:487-515` transitions at each stage
- [x] Server restart marks processing searches as timed_out — `TestStartupRecovery` (4 tests)
- [x] SSE reconnection receives current state from DB — `routes/search.py:198-222`
- [x] Polling endpoint returns correct state during each pipeline stage — `TestProgressEstimation` (6 tests)
- [x] Tracker TTL >= FETCH_TIMEOUT verified — `TestTrackerTTL` (420s >= 360s)
- [x] Dual EventSource consolidated (no duplicate connections) — `useSearchSSE` replaces dual hooks
- [x] Timeline endpoint returns full transition history — `routes/search.py:306-313`
- [x] Frontend switches from SSE to polling on disconnect — `useSearchPolling` + `useSearch.ts` integration
- [x] Concurrent searches maintain independent state — `TestConcurrentSearches::test_independent_state`

## Definicao de Pronto

1. Toda busca tem estado deterministico em banco a qualquer momento
2. Restart do servidor nao perde buscas — elas sao marcadas como timed_out
3. Frontend pode recuperar estado via polling quando SSE indisponivel
4. Timeline completa de transicoes auditavel via endpoint dedicado
5. Zero regressao nos testes existentes
6. Dual EventSource consolidado em conexao unica

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| DB writes a cada transicao adicionam latencia | Fire-and-forget com asyncio.create_task, nao bloqueia pipeline |
| Polling a cada 3s pode sobrecarregar DB | Cache em Redis (TTL 2s), rate limit por search_id |
| Startup recovery pode marcar buscas validas como timed_out | Usar janela de 10 min (> max pipeline timeout) |
| Consolidar SSE pode quebrar frontend | Feature flag `USE_CONSOLIDATED_SSE` (default false, opt-in) |

## Arquivos Envolvidos

### Backend (modificar):
- `backend/progress.py` — refatorar ProgressTracker para derivar de estado persistido
- `backend/routes/search.py` — emitir transicoes, novo endpoint `/status`, `/timeline`
- `backend/search_pipeline.py` — atualizar estado em cada stage
- `backend/config.py` — `_TRACKER_TTL` adjustment

### Backend (criar):
- `backend/models/search_state.py` — SearchState enum, transition validator
- `backend/search_state_manager.py` — helper functions para transicoes
- Nova migration: `035_search_state_transitions.sql`

### Frontend (modificar):
- `frontend/hooks/useSearchProgress.ts` — consolidar com useUfProgress
- `frontend/app/buscar/hooks/useUfProgress.ts` — merge into useSearchProgress
- `frontend/app/buscar/hooks/useSearch.ts` — polling fallback logic

### Frontend (criar):
- `frontend/hooks/useSearchPolling.ts` — polling fallback hook

## Dependencias

- **Bloqueada por:** CRIT-002 (precisa da coluna `status` em `search_sessions`)
- **Bloqueia:** CRIT-006 (timeout controlado depende do state machine)
