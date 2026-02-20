# CRIT-007: Testes de Falha End-to-End

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 4: Validacao

## Prioridade
P0

## Estimativa
20h

## Descricao

O sistema nao possui infraestrutura de testes de integracao. O diretorio `backend/tests/integration/` nao existe. O job `integration-tests` no CI e um stub que imprime "will be implemented in issue #27". O hook `useSearch.test.ts` esta em quarentena. Todos os testes de falha existentes sao unit-level com mocks isolados — nenhum testa a interacao real entre modulos durante falhas.

Resultado: falhas cascata entre modulos sao invisiveis. O glue entre stages do pipeline nunca e testado. Se o cache crashar e o pipeline deveria servir dados parciais, isso nunca foi verificado com os modulos reais interagindo.

### Situacao atual:

| Area | Testes existentes | O que falta |
|------|-------------------|-------------|
| Cache failures individuais | 19 (test_search_cache) + 40 (test_cache_multi_level) | Cache + DB + pipeline cascata |
| PNCP client failures | 42 (test_pncp_client) + 20 (test_pncp_resilience) | PNCP fail + cache fallback full flow |
| Pipeline stages | 10 (test_search_pipeline) + 20 (test_generate_persist) | Full pipeline com falha real entre stages |
| Job queue | 42 (test_job_queue) | Queue dispatch fail -> inline fallback real |
| Frontend proxy | 12 (buscar.test.ts) | 504 timeout, SSE failure recovery |
| useSearch hook | **QUARENTENA** | Todos os cenarios de falha do hook |
| Integration | **ZERO** (diretorio nao existe) | Tudo |
| E2E failure | **ZERO** | Tudo |

### 7 cenarios P0 sem cobertura:

1. **Full pipeline failure cascade** — nenhum teste exercita SearchPipeline real do stage_validate ao stage_persist onde falha real (nao mock de stage) propaga
2. **Queue dispatch fail -> inline fallback** — testes verificam `enqueue_job` retorna None, mas nao que pipeline REALMENTE faz fallback inline
3. **Supabase totalmente indisponivel** — testes mockam falha individual (cache read, session save), nenhum simula DB down para request inteiro
4. **All sources + all caches fail** — `test_pipeline_resilience` testa sources fail com cache disponivel. Nao testa o worst case absoluto
5. **Client nunca conecta SSE** — nenhum teste verifica que POST /buscar retorna dados completos independente de SSE
6. **Frontend 504 gateway timeout** — buscar.test.ts testa 500, 502, 503 mas NAO 504/408
7. **Queue dispatch -> worker fail -> inline fallback verificado** — bridge entre deteccao e fallback nao testada

## Especialistas Consultados
- QA Architect (Failure Testing Specialist)
- Systems Architect (Integration Test Design)

## Evidencia da Investigacao

### CI/CD stub (`.github/workflows/tests.yml` L190-219):
```yaml
integration-tests:
  runs-on: ubuntu-latest
  continue-on-error: true  # NAO BLOQUEIA BUILD
  steps:
    - run: echo "will be implemented in issue #27"
```

### useSearch.test.ts em quarentena:
- Localizado em `frontend/__tests__/quarantine/hooks/useSearch.test.ts`
- Motivo provavel: dependencias complexas (SSE, fetch, timers)

### Testes de falha que EXISTEM (para nao duplicar):
- `test_search_cache.py`: Supabase read/write fail, cascade L1->L2->L3, all levels miss
- `test_pncp_client.py`: retry 500/503, 429 Retry-After, ConnectionError, TimeoutError
- `test_pncp_resilience.py`: circuit breaker open/close/half-open
- `test_consolidation.py`: one source timeout, all sources fail
- `test_pipeline_resilience.py`: ComprasGov 503, unexpected RuntimeError, stale cache fallback
- `test_job_queue.py`: pool None, ping fail, enqueue RuntimeError, LLM/Excel job failures
- `test_progress.py`: Redis lost during emit, Redis error on delete
- `__tests__/api/buscar.test.ts`: 500, 502, 503, network error
- `__tests__/gtm-fix-033-sse-resilience.test.tsx`: SSE retry, disconnect during search

## Criterios de Aceite

### Infrastructure
- [ ] AC1: Criar diretorio `backend/tests/integration/` com `conftest.py` contendo fixtures compartilhadas
- [ ] AC2: Fixtures devem incluir: mock Supabase, mock PNCP responses, mock Redis, test FastAPI client
- [ ] AC3: Integration tests devem usar `TestClient` do FastAPI (nao mocks de pipeline stages)
- [ ] AC4: Habilitar job `integration-tests` no CI (`tests.yml`) — remover stub, rodar pytest real
- [ ] AC5: Integration tests devem ter marker `@pytest.mark.integration` para execucao separada

### P0 Failure Cascade Tests
- [ ] AC6: **test_full_pipeline_cascade.py** — Test SearchPipeline com todos os stages reais (nao mocked):
  - Scenario A: PNCP retorna 500 em todas UFs -> pipeline serve cache -> HTTP 200 com response_state="cached"
  - Scenario B: PNCP retorna 500 + cache vazio -> HTTP 200 com response_state="empty_failure"
  - Scenario C: Stage 4 (filter) crash -> busca registrada como failed em search_sessions
  - Scenario D: Stage 6 (LLM) timeout -> fallback summary gerado, busca completa normalmente

- [ ] AC7: **test_queue_inline_fallback.py** — Test que quando `is_queue_available()` retorna False:
  - Pipeline executa LLM inline (nao via ARQ)
  - Pipeline executa Excel inline (nao via ARQ)
  - Response contem resumo E excel_url
  - Latencia e maior mas resultado e identico

- [ ] AC8: **test_supabase_total_outage.py** — Test com ALL Supabase operations failing:
  - Quota check fails -> fallback quota info usado
  - Cache read fails -> search continues without cache
  - Cache write fails -> results still returned
  - Session save fails -> results still returned, session_id=None
  - Search STILL WORKS (degraded but functional)

- [ ] AC9: **test_absolute_worst_case.py** — All sources + all caches fail:
  - PNCP returns 500
  - PCP returns 500
  - ComprasGov returns 500
  - Supabase cache empty
  - Redis cache empty
  - InMemory cache empty
  - Assert: user gets response_state="empty_failure" with degradation_guidance
  - Assert: busca registrada em search_sessions com status='failed'
  - Assert: HTTP response is deterministic (not random/timeout)

- [ ] AC10: **test_post_independent_of_sse.py** — Test POST /buscar without SSE:
  - Client sends POST /buscar with search_id
  - Client does NOT open SSE connection
  - Backend still processes and returns full results
  - Response contains all fields (licitacoes, resumo, excel_url)

- [ ] AC11: **test_frontend_504_timeout.py** — Frontend proxy 504:
  - Mock backend that takes 500s to respond
  - Frontend proxy AbortController fires at 480s
  - Assert: HTTP 504 returned
  - Assert: response body contains user-friendly message
  - Assert: response parseable by error-messages.ts

- [ ] AC12: **test_queue_worker_fail_inline.py** — Queue dispatch + worker fail:
  - `is_queue_available()` returns True
  - `enqueue_job()` succeeds
  - Worker job fails (simulate with mock)
  - Assert: job failure is communicated via SSE (or polling)
  - Assert: fallback summary available
  - Assert: user not stuck at "processing" forever

### P1 Canary Tests
- [ ] AC13: **test_schema_canary.py** — Schema compatibility:
  - Query `information_schema.columns WHERE table_name = 'search_results_cache'`
  - Compare against expected column list from SearchResultsCacheRow model (CRIT-001)
  - Fail if any expected column is missing

- [ ] AC14: **test_pncp_api_canary.py** — PNCP API contract:
  - Send request with tamanhoPagina=50 (current max)
  - Assert: HTTP 200
  - Send request with tamanhoPagina=51
  - If HTTP 400: tamanhoPagina limit is still 50 (expected)
  - If HTTP 200: tamanhoPagina limit increased (update config)

- [ ] AC15: **test_concurrent_searches.py** — Concurrent search isolation:
  - Launch 3 concurrent searches with different search_ids
  - Assert: each search has independent progress tracker
  - Assert: each search returns independent results
  - Assert: no cross-contamination of state

### Frontend Tests
- [ ] AC16: Tirar `useSearch.test.ts` da quarentena e corrigir:
  - Fix: mock fetch, EventSource, crypto.randomUUID, timers
  - Add: test buscar() with 504 response
  - Add: test buscar() with SSE disconnect + POST success
  - Add: test buscar() with timeout then retry

- [ ] AC17: **useSearch-failures.test.ts** — New test file for failure scenarios:
  - Test: search timeout shows partial results (if available)
  - Test: SSE disconnect switches to simulated progress
  - Test: retry button respects scaled cooldown
  - Test: cancel search aborts fetch and clears loading
  - Test: forceFresh failure preserves previous results

- [ ] AC18: **Playwright E2E: failure-scenarios.spec.ts**:
  - Test: search with mocked backend returning empty_failure -> SourcesUnavailable shown
  - Test: search with slow backend -> overtime messages appear
  - Test: search with 500 backend -> error card with retry button
  - (Requires mock backend or intercept)

### Documentation
- [ ] AC19: Cada teste P0 deve ter docstring explicando o cenario de producao que ele previne
- [ ] AC20: README em `backend/tests/integration/README.md` com instrucoes de execucao

## Testes Obrigatorios

(Meta-teste: os testes desta story SAO os testes obrigatorios)

Apos implementacao completa:
- [ ] `pytest backend/tests/integration/ -v` — todos passam
- [ ] `npm test -- --testPathPattern="useSearch"` — passa (fora da quarentena)
- [ ] `npm test -- --testPathPattern="useSearch-failures"` — passa
- [ ] CI integration-tests job roda e reporta (nao e stub)
- [ ] Zero regressao nos testes existentes (baseline mantida)

## Definicao de Pronto

1. Diretorio `backend/tests/integration/` existe com 7+ test files
2. Job `integration-tests` no CI executa testes reais (nao stub)
3. `useSearch.test.ts` fora da quarentena e passando
4. 7 cenarios P0 tem testes automatizados que validam:
   - (a) busca registrada em banco
   - (b) estado final consistente
   - (c) usuario recebe feedback deterministico
5. 3 canary tests monitoram contratos externos
6. Zero regressao: backend ~35 fail (pre-existing), frontend ~42 fail (pre-existing)

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| Integration tests sao lentos (DB real) | Usar SQLite in-memory ou Supabase mock com latencia zero |
| useSearch.test.ts pode ser muito complexo para tirar de quarentena | Reescrever do zero com mocks simplificados se necessario |
| E2E tests flaky com mocked backend | Usar Playwright request interception, nao mock server |
| Testes de concorrencia sao nao-deterministicos | Usar asyncio.gather com seeds fixas, repetir 3x |

## Arquivos Envolvidos

### Backend (criar):
- `backend/tests/integration/conftest.py`
- `backend/tests/integration/test_full_pipeline_cascade.py`
- `backend/tests/integration/test_queue_inline_fallback.py`
- `backend/tests/integration/test_supabase_total_outage.py`
- `backend/tests/integration/test_absolute_worst_case.py`
- `backend/tests/integration/test_post_independent_of_sse.py`
- `backend/tests/integration/test_queue_worker_fail_inline.py`
- `backend/tests/integration/test_schema_canary.py`
- `backend/tests/integration/test_pncp_api_canary.py`
- `backend/tests/integration/test_concurrent_searches.py`
- `backend/tests/integration/README.md`

### Frontend (modificar):
- `frontend/__tests__/quarantine/hooks/useSearch.test.ts` -> mover para `frontend/__tests__/hooks/`

### Frontend (criar):
- `frontend/__tests__/hooks/useSearch-failures.test.ts`
- `frontend/e2e-tests/failure-scenarios.spec.ts`

### CI (modificar):
- `.github/workflows/tests.yml` L190-219 — substituir stub por pytest real

## Dependencias

- **Bloqueada por:** CRIT-002, CRIT-003, CRIT-005 (precisa dos contratos corretos para testar)
- **Paralela com:** Nenhuma (story final de validacao)
- **Bloqueia:** Nada (story de encerramento do epic)
