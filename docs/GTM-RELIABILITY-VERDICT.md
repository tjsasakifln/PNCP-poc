# GTM Reliability Verdict — SmartLic

**Date:** 2026-02-26
**Verdict:** **NO-GO** — Sistema fundamentalmente não entrega o core flow de forma confiável.
**Condição para re-avaliação:** Completar Sprint 0 + Sprint 1 (estimativa: 5-7 dias).

---

## O Problema Real

A cada 10 tentativas de busca, 10 falham em alguma etapa. O sistema tem 65+ módulos, 304+ testes, circuit breakers, cache SWR, LLM arbiter, SSE streaming — mas **a busca não funciona de forma consistente**. Isso não é um bug. É uma falha arquitetural.

A ironia: o componente mais engenhado do sistema (PNCP client com circuit breaker, retry, batching) provavelmente funciona. As falhas vêm da **infraestrutura ao redor** — auth, state management, async/sync mixing, timeout chain.

---

## 5 Root Causes Identificados (Análise de Código + Produção)

### RC-1: Supabase como Single Point of Failure (SPOF)

**O que acontece:** Toda busca passa por `require_auth` → `require_active_plan` → `check_quota` → `register_session` antes de tocar qualquer API. São 4-6 chamadas Supabase **síncronas** no hot path. Se Supabase tem latência (pool exhaustion, cold start, RLS), 100% das buscas falham no gate.

**Evidência no código:**
- `routes/search.py:881` — `require_active_plan()` roda ANTES do try block, ANTES do tracker ser criado
- Se falha, não há SSE error event, não há session tracking → frontend fica em limbo
- Supabase é chamado para: auth, plan status, quota, session, cache L2, profile, histórico

**Padrão da indústria violado:** Circuit Breaker Pattern (Microsoft Azure Architecture Center). Supabase não tem circuit breaker. Todo outro serviço externo (PNCP, Redis, OpenAI) tem, mas a dependência mais crítica não.

**Fonte:** [Microsoft Azure — Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

---

### RC-2: Chamadas Síncronas Bloqueando o Event Loop

**O que acontece:** O Supabase Python client (postgrest-py) é **síncrono**. Chamadas como `sb.table("profiles").select(...).execute()` dentro de funções `async def` bloqueiam o event loop do Uvicorn. Enquanto uma query Supabase executa (~200-500ms), NENHUMA outra coroutine roda — incluindo SSE heartbeats.

**Evidência no código:**
- `search_pipeline.py:878` — `_profile_row = _db.table("profiles").select("context_data")...execute()` — chamada síncrona em `async def stage_prepare()`
- `health.py` — health check response latency: 488ms (Track D mediu)
- Sentry: `WORKER KILLED BY TIMEOUT` (5 events) e `Worker was sent SIGABRT` (5 events) — Gunicorn mata worker porque heartbeat parou (event loop bloqueado)

**Padrão da indústria violado:** FastAPI Async Best Practices. Regra absoluta: **nunca use código síncrono dentro de `async def`**. Use `asyncio.to_thread()` para offload ou use `def` (FastAPI roda em thread pool automaticamente).

**Fonte:** [FastAPI — Concurrency and async/await](https://fastapi.tiangolo.com/async/), [FastAPI Mistakes That Kill Performance](https://dev.to/igorbenav/fastapi-mistakes-that-kill-your-performance-2b8k)

---

### RC-3: Estado In-Memory em Ambiente Multi-Worker

**O que acontece:** `WEB_CONCURRENCY=2` (Gunicorn com 2 workers). O progress tracker (`_active_trackers` em `progress.py`) é um dict in-memory. POST `/buscar` cria o tracker no worker A. GET `/buscar-progress/{id}` (SSE) pode cair no worker B → tracker não existe → espera 30s → dá erro "Search not found".

**Evidência no código:**
- `progress.py:357` — `_active_trackers: Dict[str, ProgressTracker] = {}` — in-memory, per-process
- `routes/search.py` — `_background_results`, `_active_background_tasks` — também in-memory
- `llm_arbiter.py` — `_arbiter_cache` — in-memory
- STORY-276 tentou migrar para Redis Streams, mas o fallback para in-memory persiste quando Redis não está disponível

**Padrão da indústria violado:** State externalization. Em sistemas multi-processo, todo estado compartilhado DEVE estar em storage externo (Redis, DB, shared memory). In-memory state é aceitável APENAS em single-process deployments.

**Fonte:** [Microsoft Azure — Async Request-Reply Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)

---

### RC-4: Request Síncrono para Operação de Longa Duração

**O que acontece:** `POST /buscar` é um request HTTP síncrono que executa toda a pipeline (auth → fetch → filter → LLM → Excel → persist) e retorna o resultado no body da response. Para 27 UFs, isso pode levar 80-120s. O frontend tem AbortController de 115s. A margem é de **zero**.

**Evidência no código:**
- `routes/search.py` — `buscar_licitacoes()` roda toda a pipeline inline, retorna `BuscaResponse` no body
- `SEARCH_ASYNC_ENABLED=false` por default — o path assíncrono (202 Accepted + ARQ) está desabilitado
- Frontend `route.ts` — `AbortController` com timeout de 115s
- Gunicorn timeout: 120s, Railway proxy: ~300s

**Padrão da indústria violado:** Async Request-Reply Pattern (Microsoft). Para operações >10s, o padrão é: `POST` retorna `202 Accepted` com URL de status. Cliente acompanha via polling ou SSE. O servidor NUNCA mantém o request HTTP aberto durante a execução.

**Fonte:** [Microsoft Azure — Async Request-Reply Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)

---

### RC-5: Entrega Tudo-ou-Nada (Sem Progressive Results)

**O que acontece:** O pipeline espera TODAS as fontes completarem, depois filtra tudo, depois classifica tudo, depois gera summary e Excel, e SÓ ENTÃO retorna resultado. Se uma fonte é lenta, todas as outras esperam. Se o consolidation timeout (60s) estoura, pode perder resultados já coletados.

**Evidência no código:**
- `consolidation.py` — `fetch_all()` usa `asyncio.gather()` para todas as fontes, com timeout global de 60s
- Se timeout estoura: partial salvage tenta recuperar, mas é best-effort
- Não há streaming de resultados parciais — é tudo ou nada

**Padrão da indústria violado:** Progressive Results Delivery (Meta-Search Pattern). Skyscanner, Google Flights e Kayak usam `asyncio.as_completed()` para entregar resultados conforme cada fonte responde. O usuário vê resultados imediatos da fonte mais rápida.

**Fonte:** [Skyscanner Meta-Search Aggregation](https://www.frugaltesting.com/blog/skyscanners-meta-search-aggregation-for-travel-deals), [Google Flights Deep Search](https://serpapi.com/blog/exact-google-flight-search-results-how-deep-search-mirrors-your-browser/)

---

## Consolidated GTM Audit Findings

### De Track A (Market Intelligence)
| Sev | Finding | Status com R$397 |
|-----|---------|-----------------|
| **BLOCKER** | Sem alertas email/WhatsApp (table stakes — TODO concorrente tem) | Permanece BLOCKER |
| ~~BLOCKER~~ | Pricing 5-13x acima do mercado | **DOWNGRADE → MEDIUM** (R$397 está no range R$200-500) |
| HIGH | Apenas 3 fontes de dados (vs 19+ SIGA, 6000+ ConLicitação) | Permanece |
| HIGH | Sem free tier (conversão mais difícil) | Permanece |

### De Track B (UX Audit)
| Sev | Finding |
|-----|---------|
| **BLOCKER** | Progress bar presa em 10% enquanto UF grid mostra estados completando (RC-3 + RC-4) |
| **BLOCKER** | Sentry: 5 issues ativas — APIError (44 events), worker timeout, AllSourcesFailedError (RC-1 + RC-2) |
| **BLOCKER** | Busca single-state (SP) falha com estados contraditórios simultâneos |
| HIGH | Dual error messages (red banner + "Fontes indisponíveis") — confuso |

### De Track D (Infrastructure)
| Sev | Finding |
|-----|---------|
| HIGH | Deploy workflow quebrado (Railway CLI `-y` flag) |
| HIGH | Backend CI bloqueado por lint error trivial |
| HIGH | E2E tests broken (standalone build) |
| MEDIUM | 3 test failures (OpenAPI snapshot + event loop) |

### De Track E (Business Model)
| Sev | Finding |
|-----|---------|
| HIGH | Sem alertas automatizados (maior risco de churn) |
| HIGH | CLAUDE.md com pricing stale (R$1.999 vs R$397) e trial (7d vs 30d) |
| HIGH | Sem contato para não-usuários (pré-venda) |

### De Track F (Security)
| Sev | Finding |
|-----|---------|
| MEDIUM | Missing CSP header |
| MEDIUM | Error detail leak em Google Sheets export |
| MEDIUM | Privacy policy sem base legal explícita (LGPD Art. 7) |

---

## Sprint Plan

### Sprint 0: "Make It Work" (3 dias)

**Objetivo:** Busca funciona de forma confiável para 1 UF. Zero tolerance for failure.

#### STORY-S0-01: Async Search — 202 Accepted Pattern
**O que:** `POST /buscar` retorna `202 Accepted` com `search_id` imediatamente. Pipeline executa em background task. Resultado fica disponível via SSE e polling endpoint.

**Por que (industria):** Microsoft Async Request-Reply Pattern — para operações >10s, nunca mantenha o HTTP request aberto.

**Acceptance Criteria:**
- [ ] POST /buscar retorna 202 em <2s com `{ search_id, status_url }`
- [ ] GET /v1/search/{id}/status retorna estado atual (pending/running/completed/failed)
- [ ] SSE /buscar-progress/{id} streama eventos do Redis (não in-memory)
- [ ] Resultado final persistido em Supabase (não in-memory)
- [ ] Frontend adapta: recebe 202, abre SSE, mostra resultados quando `complete`
- [ ] Se SSE desconecta, frontend faz polling no status endpoint

**Fonte:** [Microsoft — Async Request-Reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)

---

#### STORY-S0-02: Eliminar Blocking Calls no Event Loop
**O que:** Toda chamada Supabase (síncrona) deve ser wrapped em `asyncio.to_thread()`. Ou migrar para Supabase async client se disponível.

**Por que (industria):** FastAPI docs — "If you use `async def`, the code runs on the main event loop. If you call blocking I/O, it freezes everything."

**Acceptance Criteria:**
- [ ] Audit: listar TODA chamada `.execute()` do Supabase em código async
- [ ] Wrap cada uma em `asyncio.to_thread()` ou mover para `def` function
- [ ] `PYTHONASYNCIODEBUG=1` em staging — zero warnings de slow callback >100ms
- [ ] Worker timeout Sentry events eliminados (baseline: 10 events/semana → 0)

**Fonte:** [FastAPI — async/await](https://fastapi.tiangolo.com/async/), [Python asyncio Debug Mode](https://docs.python.org/3/library/asyncio-dev.html)

---

#### STORY-S0-03: Circuit Breaker no Supabase
**O que:** Adicionar circuit breaker nas chamadas Supabase do hot path (auth, quota, session). Se Supabase está lento/down, usar cache local de plan status (5min TTL).

**Por que (industria):** Circuit Breaker Pattern — toda dependência externa DEVE ter circuit breaker. Supabase é a única dependência sem.

**Acceptance Criteria:**
- [ ] Circuit breaker com sliding window (10 calls, 50% failure rate → OPEN)
- [ ] Fallback para plan status: cache em Redis/memory (5min TTL)
- [ ] Fallback para quota: permitir busca mas logar para reconciliação posterior
- [ ] `require_active_plan()` DENTRO do try block, DEPOIS do tracker ser criado
- [ ] Prometheus metric: `smartlic_supabase_circuit_breaker_state`

**Fonte:** [Resilience4j CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker), [Microsoft — Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

---

### Sprint 1: "Make It Reliable" (4 dias)

**Objetivo:** Busca funciona para múltiplos UFs com degradação graceful. Resultados parciais entregues.

#### STORY-S1-01: Progressive Results Delivery
**O que:** Usar `asyncio.as_completed()` em vez de `asyncio.gather()` na consolidação. Stremar resultados parciais via SSE conforme cada fonte completa. Filtrar e entregar incrementalmente.

**Por que (industria):** Meta-search engine pattern (Skyscanner, Google Flights). Nunca bloqueie todos os resultados esperando a fonte mais lenta.

**Acceptance Criteria:**
- [ ] SSE emite `source_complete` com resultados parciais de cada fonte
- [ ] Frontend renderiza resultados incrementalmente
- [ ] Se 1 de 3 fontes falha, usuário vê resultados das outras 2 com indicador "parcial"
- [ ] Tempo para primeiro resultado: <15s (vs 60-120s atual)

**Fonte:** [Skyscanner Meta-Search](https://www.frugaltesting.com/blog/skyscanners-meta-search-aggregation-for-travel-deals)

---

#### STORY-S1-02: Estado Externalizado em Redis
**O que:** Migrar TODO estado compartilhado de in-memory para Redis. Progress tracker, background results, background tasks, LLM cache.

**Por que (industria):** Multi-worker systems DEVEM externalizar estado. In-memory é incompatível com WEB_CONCURRENCY>1.

**Acceptance Criteria:**
- [ ] `_active_trackers` → Redis Streams (completar STORY-276)
- [ ] `_background_results` → Redis hash com TTL 10min
- [ ] `_arbiter_cache` → Redis hash com TTL 1h
- [ ] Progress tracking funciona com WEB_CONCURRENCY=4
- [ ] Teste: POST em worker A, SSE em worker B → resultados corretos

**Fonte:** [Microsoft — Async Request-Reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)

---

#### STORY-S1-03: Bulkhead — Isolamento por Fonte
**O que:** Cada fonte de dados (PNCP, PCP, ComprasGov) opera com seu próprio semáforo. Cada uma com timeout independente. Uma fonte lenta não pode consumir recursos de outra.

**Por que (industria):** Bulkhead Pattern — isolamento de recursos para evitar falhas em cascata.

**Acceptance Criteria:**
- [ ] `asyncio.Semaphore(10)` para PNCP, `Semaphore(5)` para PCP, `Semaphore(5)` para ComprasGov
- [ ] `asyncio.Semaphore(20)` para LLM calls
- [ ] Per-source timeout: 30s (reduzido de 80s do failover mode)
- [ ] Global consolidation timeout: 45s (reduzido de 60s)
- [ ] Remover `SEARCH_FETCH_TIMEOUT=360s` (dead code — nunca fires)

**Fonte:** [Microsoft — Bulkhead Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

---

#### STORY-S1-04: SSE Last-Event-ID Resumption
**O que:** Atribuir event IDs a cada SSE event. Se conexão cai e reconecta, browser envia `Last-Event-ID` header. Servidor resume do último evento.

**Por que (industria):** Especificação WHATWG SSE. Capacidade built-in que o browser implementa automaticamente via EventSource API.

**Acceptance Criteria:**
- [ ] Todo SSE event tem `id:` field (incrementing counter ou timestamp)
- [ ] Servidor armazena últimos 100 events por search_id em Redis (TTL 10min)
- [ ] Handler de SSE verifica `Last-Event-ID` header e envia eventos perdidos
- [ ] Teste: desconectar SSE, reconectar → recebe eventos que perdeu

**Fonte:** [MDN — Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)

---

### Sprint 2: "Make It Observable" (2 dias)

#### STORY-S2-01: SLOs Formais + Alerting
**O que:** Definir SLOs, instrumentar SLIs, configurar alertas.

| SLI | Target SLO | Alerta |
|-----|-----------|--------|
| Availability (2xx+3xx/total) | 99.5% / 30 dias | <99% por 5min |
| Latency p95 | <30s | >45s por 10min |
| Source completeness | ≥2/3 fontes em 95% das buscas | <1/3 por 15min |
| Error rate | <1% | >5% por 5min |

**Fonte:** [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)

---

#### STORY-S2-02: Fix CI/CD Pipeline
**O que:** 3 fixes triviais para restaurar CI/CD verde.
- Deploy workflow: remover `-y` flag de `railway variables set`
- Backend lint: remover unused import em `test_story280_boleto_pix.py`
- E2E: investigar standalone build missing `server.js`

---

### Sprint 3: "Make It Competitive" (5 dias)

#### STORY-S3-01: Alertas de Licitação por Email
**O que:** Implementar envio de alertas quando novas licitações matcham o perfil do usuário.

**Por que (industria):** Table stakes — TODOS os concorrentes (Alerta Licitação, ConLicitação, SIGA, Effecti) oferecem alertas. Sem isso, o usuário precisa fazer login diariamente.

**Acceptance Criteria:**
- [ ] User configura: setor + UFs + frequência (diário/semanal)
- [ ] Backend cron job busca novas licitações e envia email via Resend
- [ ] Template de email com top 5 oportunidades + link "Ver todas"
- [ ] Unsubscribe one-click (CAN-SPAM / LGPD compliance)

---

#### STORY-S3-02: Atualizar Documentação Stale
**O que:**
- CLAUDE.md: R$1.999 → R$397, trial 7d → 30d
- DEPLOYMENT-STATUS.md: atualizar para estado atual
- TrialExpiringBanner.tsx comment: "7-day" → "30-day"

---

## Resumo Executivo

```
PROBLEMA:  Sistema tem 65+ módulos, 304+ testes, circuit breakers, cache SWR
           ... mas a busca falha 10/10 vezes.

CAUSA:     5 anti-patterns arquiteturais (não bugs):
           1. Supabase SPOF sem circuit breaker
           2. Sync calls bloqueando event loop async
           3. Estado in-memory em multi-worker
           4. Request síncrono para operação longa
           5. Entrega tudo-ou-nada sem progressive results

SOLUÇÃO:   3 sprints fundamentados em padrões da indústria:
           Sprint 0 (3d): 202 Accepted + unblock event loop + CB no Supabase
           Sprint 1 (4d): Progressive results + Redis state + bulkhead + SSE resume
           Sprint 2 (2d): SLOs + CI/CD fix

CRITÉRIO:  Busca de 1 UF funciona 100/100 vezes (Sprint 0)
           Busca de 27 UFs funciona 95/100 vezes (Sprint 1)
           Alerting operacional (Sprint 2)
```

---

**Fontes verificáveis:**
1. [Microsoft — Async Request-Reply Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/async-request-reply)
2. [Microsoft — Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
3. [Microsoft — Bulkhead Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
4. [FastAPI — Concurrency and async/await](https://fastapi.tiangolo.com/async/)
5. [Python asyncio Debug Mode](https://docs.python.org/3/library/asyncio-dev.html)
6. [Google SRE — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
7. [MDN — Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
8. [Resilience4j — CircuitBreaker](https://resilience4j.readme.io/docs/circuitbreaker)
9. [Skyscanner Meta-Search Aggregation](https://www.frugaltesting.com/blog/skyscanners-meta-search-aggregation-for-travel-deals)
10. [RFC 5861 — Stale-While-Revalidate](https://datatracker.ietf.org/doc/html/rfc5861)
11. [Tenacity — Python Retry Library](https://tenacity.readthedocs.io/)
12. [Railway — Specs and Limits](https://docs.railway.com/networking/public-networking/specs-and-limits)
