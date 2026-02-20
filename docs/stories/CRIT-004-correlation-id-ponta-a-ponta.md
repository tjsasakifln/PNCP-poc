# CRIT-004: Propagar Correlation ID Ponta a Ponta

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 1: Fundacao (paralelo com CRIT-001)

## Prioridade
P0

## Estimativa
12h

## Descricao

O sistema possui tres mecanismos de identidade independentes que NUNCA se conectam:

| ID | Escopo | Gerado por | Propagado ate |
|----|--------|-----------|---------------|
| `X-Correlation-ID` | Sessao browser (per-tab) | Frontend (`correlationId.ts`) | **DESCARTADO no proxy Next.js** |
| `X-Request-ID` | Request HTTP (per-call) | Next.js proxy OU backend middleware | PNCP API, OpenAI API, audit logs |
| `search_id` | Busca (per-search) | Frontend (`crypto.randomUUID()`) | SSE channel, ARQ jobs, Redis keys |

Resultado: e impossivel reconstruir a jornada completa de uma busca a partir dos logs. Dado um `search_id`, nao se consegue encontrar os logs de filtering, consolidation, ou jobs ARQ associados.

## Especialistas Consultados
- Observability Architect (Distributed Tracing Specialist)

## Evidencia da Investigacao

### 10 Gaps Identificados:

1. **GAP 1** — Frontend `X-Correlation-ID` descartado no proxy (`frontend/app/api/buscar/route.ts` L69-73 gera novo `X-Request-ID`)
2. **GAP 2** — SSE proxy (`buscar-progress/route.ts` L27-31) nao forwarda headers de correlacao
3. **GAP 3** — `search_id` nao esta em ContextVar nem no log context. Nao da pra grep logs por search_id
4. **GAP 4** — `filter.py` L2521-2522 gera proprio `trace_id` de 8 chars, independente do sistema
5. **GAP 5** — `consolidation.py` nao tem acesso ao `search_id`
6. **GAP 6** — ARQ jobs: `_trace_id`/`_span_id` injetados por `enqueue_job()` (L136-145) mas NUNCA consumidos — funcoes nao aceitam `**kwargs`
7. **GAP 7** — Worker ARQ nao tem `request_id_var` ContextVar — logs mostram `request_id="-"`
8. **GAP 8** — SSE events incluem `trace_id` mas nao `request_id` ou `search_id`
9. **GAP 9** — Download proxy nao forwarda correlacao
10. **GAP 10** — Nenhum ponto no codigo conhece os 3 IDs simultaneamente

### Resultado: Impossivel reconstruir jornada

| Cenario | Possivel? |
|---------|-----------|
| Log lines de um HTTP request | SIM (grep request_id) |
| Correlacionar HTTP -> SSE | PARCIAL (timing) |
| Busca -> ARQ background job | **NAO** |
| Browser -> Backend | **NAO** |
| Filter decisions -> busca | **NAO** |

## Criterios de Aceite

### Proxy Header Forwarding
- [ ] AC1: `frontend/app/api/buscar/route.ts` deve forwardar `X-Correlation-ID` do browser alem do `X-Request-ID` que ja gera
- [ ] AC2: `frontend/app/api/buscar-progress/route.ts` deve forwardar `Authorization` + `X-Correlation-ID`
- [ ] AC3: `frontend/app/api/download/route.ts` deve forwardar `X-Request-ID` e `X-Correlation-ID`
- [ ] AC4: Todos os proxies em `frontend/app/api/` devem seguir o mesmo padrao de header forwarding

### Backend ContextVar
- [ ] AC5: Criar `search_id_var = ContextVar("search_id", default="-")` em `middleware.py`
- [ ] AC6: `CorrelationIDMiddleware` deve ler `X-Correlation-ID` do request e armazenar (alem de `X-Request-ID`)
- [ ] AC7: No handler `/buscar`, setar `search_id_var` com o `search_id` do body antes de chamar pipeline
- [ ] AC8: `RequestIDFilter` em middleware.py deve injetar `search_id` (alem de `request_id`, `trace_id`, `span_id`) em todo log record

### Log Format
- [ ] AC9: Log format de producao deve incluir `search_id`:
  ```
  %(asctime)s | %(levelname)s | req=%(request_id)s | search=%(search_id)s | trace=%(trace_id)s | %(name)s | %(message)s
  ```
- [ ] AC10: JSON log format (producao) deve incluir campo `search_id`

### Module Propagation
- [ ] AC11: `filter.py` deve usar `search_id_var.get()` em vez de gerar `_trace_id` proprio (L2521-2522)
- [ ] AC12: `consolidation.py` deve receber `search_id` como parametro ou ler de ContextVar
- [ ] AC13: `llm_arbiter.py` deve incluir `search_id` em logs (ja recebe como arg, garantir uso)
- [ ] AC14: `search_cache.py` deve incluir `search_id` em logs de cache hit/miss

### ARQ Job Tracing
- [ ] AC15: `llm_summary_job()` e `excel_generation_job()` devem aceitar `**kwargs` ou parametros explícitos para `_trace_id`/`_span_id`
- [ ] AC16: Jobs devem restaurar tracing context: criar child span linkado ao parent trace
- [ ] AC17: Jobs devem setar `request_id_var` com `search_id` no inicio (para que logs de jobs tenham correlacao)
- [ ] AC18: Job logs devem incluir `search_id` em structured logging

### SSE Event Correlation
- [ ] AC19: `ProgressEvent.to_dict()` deve incluir `search_id` explicitamente (alem de `trace_id`)
- [ ] AC20: SSE events devem incluir `request_id` para correlacao com HTTP request logs

### Observability Endpoint
- [ ] AC21: Criar endpoint `GET /v1/admin/search-trace/{search_id}` que agrega:
  - Status da busca (from search_sessions)
  - Timeline de transicoes de estado
  - Cache hits/misses
  - Job queue status
  - Retorna JSON com jornada completa reconstruida

### Validation
- [ ] AC22: Criar teste que verifica: dado um search_id, pode-se encontrar em logs: o request_id correspondente, o trace_id OTel, os logs de filter decisions, os logs de PNCP fetch, e o status do ARQ job
- [ ] AC23: Teste automatizado que uma busca completa produz log lines com search_id em todos os modulos: search_pipeline, consolidation, filter, llm, search_cache, progress

## Testes Obrigatorios

- [ ] Proxy forwards X-Correlation-ID to backend
- [ ] search_id_var is set in /buscar handler
- [ ] All log lines during search include search_id
- [ ] filter.py no longer generates independent trace_id
- [ ] ARQ jobs restore trace context and set search_id in logs
- [ ] SSE events include search_id
- [ ] Admin trace endpoint returns complete journey
- [ ] Regression: existing logging tests pass

## Definicao de Pronto

1. Dado um `search_id`, pode-se `grep` logs e encontrar TODA a jornada (frontend proxy -> backend -> PNCP -> filter -> LLM -> cache -> persist)
2. ARQ job logs sao correlacionaveis com a busca original
3. Nenhum modulo gera trace ID independente
4. SSE events carregam `search_id` e `request_id`
5. Zero regressao nos testes existentes

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| ContextVar nao propaga para threads (ThreadPoolExecutor em filter.py) | Copiar search_id como argumento explicito para thread workers |
| Log volume aumenta com campo adicional | search_id e UUID curto, overhead minimo |
| ARQ kwargs change pode quebrar job serialization | Testar serializacao de jobs com novos kwargs |

## Arquivos Envolvidos

### Frontend (modificar):
- `frontend/app/api/buscar/route.ts` (L69-73)
- `frontend/app/api/buscar-progress/route.ts` (L27-31)
- `frontend/app/api/download/route.ts` (L26-29)

### Backend (modificar):
- `backend/middleware.py` (L39-89 — adicionar search_id_var, ler X-Correlation-ID)
- `backend/config.py` (L109-145 — log format)
- `backend/filter.py` (L2521-2522 — remover trace independente)
- `backend/consolidation.py` (adicionar search_id parametro/ContextVar)
- `backend/progress.py` (L33-45 — ProgressEvent.to_dict)
- `backend/job_queue.py` (L136-145 inject, L231/273 consume)
- `backend/search_cache.py` (adicionar search_id a logs)
- `backend/routes/search.py` (setar search_id_var)

### Backend (criar):
- `backend/routes/admin_trace.py` — search trace endpoint

## Dependencias

- **Bloqueada por:** Nenhuma (pode iniciar imediatamente)
- **Paralela com:** CRIT-001
- **Bloqueia:** Nenhuma diretamente (melhora observabilidade para todas as outras)
