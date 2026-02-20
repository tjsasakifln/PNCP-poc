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
- [ ] AC1: Criar enum `SearchState` com transicoes validas:
  ```
  CREATED -> VALIDATING -> FETCHING -> FILTERING -> ENRICHING -> GENERATING -> PERSISTING -> COMPLETED
                |              |            |           |             |              |
                +-> FAILED     +-> FAILED   +-> FAILED  +-> FAILED   +-> FAILED     +-> FAILED
                |              |
                +-> RATE_LIMITED +-> TIMED_OUT
  ```
- [ ] AC2: Cada transicao de estado DEVE ser persistida em banco (tabela `search_executions` ou coluna `status`/`pipeline_stage` em `search_sessions` de CRIT-002)
- [ ] AC3: Transicoes invalidas devem ser rejeitadas com log CRITICAL (ex: COMPLETED -> FETCHING)
- [ ] AC4: Cada estado carrega metadata: `timestamp`, `duration_since_previous`, `details` (JSON)

### Persistencia de Estado
- [ ] AC5: Criar tabela `search_state_transitions` (audit trail):
  ```sql
  id UUID PK, search_id UUID FK, from_state TEXT, to_state TEXT,
  stage TEXT, details JSONB, created_at TIMESTAMPTZ DEFAULT now()
  ```
- [ ] AC6: Cada transicao gera INSERT nesta tabela (fire-and-forget, nao bloqueia pipeline)
- [ ] AC7: Endpoint `GET /v1/search/{search_id}/timeline` retorna todas as transicoes

### SSE Derivado de Estado
- [ ] AC8: SSE events devem ser DERIVADOS do estado persistido, nao o contrario
- [ ] AC9: Se SSE reconecta, cliente recebe estado ATUAL do banco (nao depende de Queue in-memory)
- [ ] AC10: ProgressTracker deve ler estado do banco quando Queue esta vazia (fallback)

### Polling Fallback
- [ ] AC11: Criar endpoint `GET /v1/search/{search_id}/status` que retorna estado atual:
  ```json
  {
    "search_id": "...",
    "status": "fetching",
    "progress": 45,
    "stage": "execute",
    "started_at": "...",
    "elapsed_ms": 15000,
    "ufs_completed": 5,
    "ufs_total": 12,
    "ufs_failed": ["AC", "RR"],
    "llm_status": "processing",
    "excel_status": "pending"
  }
  ```
- [ ] AC12: Frontend implementa polling quando `sseDisconnected=true` (intervalo 3s)
- [ ] AC13: Polling automaticamente para quando status e terminal (completed/failed/timed_out)

### Tracker TTL Fix
- [ ] AC14: `_TRACKER_TTL` em progress.py DEVE ser >= Pipeline FETCH_TIMEOUT + margem: `300 -> 420` (7 min)
- [ ] AC15: Tracker cleanup nao remove trackers com busca em `status='processing'` no banco

### Startup Recovery
- [ ] AC16: Na inicializacao do servidor, queries `search_sessions WHERE status = 'processing'`
- [ ] AC17: Buscas com `started_at` > 10 min atras: marcar como `status='timed_out'`, `error_message='Server restart during processing'`
- [ ] AC18: Buscas com `started_at` < 10 min: marcar como `status='failed'`, `error_message='Server restart — retry recommended'`

### Frontend Consolidation
- [ ] AC19: Consolidar `useSearchProgress` + `useUfProgress` em uma unica conexao SSE com event dispatch
- [ ] AC20: Unica instancia de EventSource gerencia todos os event types
- [ ] AC21: Se SSE falha apos 1 retry, switch para polling endpoint (AC11)

### Observability
- [ ] AC22: Prometheus histogram `search_state_duration_seconds{state="fetching|filtering|..."}` — tempo em cada estado
- [ ] AC23: Log estruturado em cada transicao com `search_id`, `from_state`, `to_state`, `duration_ms`

## Testes Obrigatorios

- [ ] State machine rejects invalid transitions
- [ ] Every pipeline stage updates state correctly
- [ ] Server restart marks processing searches as timed_out
- [ ] SSE reconnection receives current state from DB
- [ ] Polling endpoint returns correct state during each pipeline stage
- [ ] Tracker TTL >= FETCH_TIMEOUT verified
- [ ] Dual EventSource consolidated (no duplicate connections)
- [ ] Timeline endpoint returns full transition history
- [ ] Frontend switches from SSE to polling on disconnect
- [ ] Concurrent searches maintain independent state

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
