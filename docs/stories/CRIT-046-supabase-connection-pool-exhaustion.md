# CRIT-046: Supabase Connection Pool Exhaustion

**Epic:** Production Stability
**Sprint:** Sprint 5
**Priority:** P1 — HIGH
**Story Points:** 5 SP
**Estimate:** 3-4 horas
**Owner:** @dev + @architect

---

## Problem

Sentry registrou `ConnectionError: Too many connections` no endpoint `/v1/buscar` (SMARTLIC-BACKEND-26, 5h ago). O Supabase client Python usa `httpx.AsyncClient` internamente com **pool default de 10 conexões** — insuficiente para a carga de produção:

- 2 Gunicorn workers × requests concorrentes
- Background SWR revalidation (até 3 concurrent)
- ARQ worker (LLM summaries, Excel generation)
- SSE generators (long-lived connections)
- Cron jobs (trial emails, session cleanup, cache warmup)

**Sentry Evidence:**
- SMARTLIC-BACKEND-26: `ConnectionError: Too many connections` — /v1/buscar (5h ago, 1 event)
- SMARTLIC-BACKEND-1V: `STARTUP GATE: Supabase unreachable — Server disconnected` (22h ago, FATAL)
- SMARTLIC-BACKEND-1T: `RemoteProtocolError: Server disconnected` — supabase_client (22h ago)

**Esses 3 eventos podem ter a mesma root cause:** pool de conexões exaurido causa cascade de desconexões.

---

## Root Cause Analysis

O `supabase-py` cria um `httpx.AsyncClient` com defaults:
- `max_connections=10` (httpx default)
- `max_keepalive_connections=5` (httpx default)
- Sem retry on connection error

Com 2 workers + ARQ + SWR revalidation + cron, facilmente > 10 conexões simultâneas ao Supabase.

**Supabase Pro:** 100 database connections (não é o gargalo). O gargalo é o pool HTTP no cliente Python.

---

## Acceptance Criteria

### Diagnóstico

- [ ] **AC1:** Adicionar métrica Prometheus `smartlic_supabase_pool_active_connections` (gauge) ao `supabase_client.py`
- [ ] **AC2:** Logar tamanho do pool em `sb_execute()` quando pool > 80% utilização

### Fix

- [ ] **AC3:** Configurar `httpx.AsyncClient` com `limits=httpx.Limits(max_connections=50, max_keepalive_connections=20)` no `supabase_client.py`
- [ ] **AC4:** Adicionar `timeout=httpx.Timeout(30.0, connect=10.0)` explícito (não depender do default httpx de 5s)
- [ ] **AC5:** Implementar retry com backoff para `ConnectionError` no `sb_execute()` (1 retry, 1s delay)

### Validação

- [ ] **AC6:** Testes existentes passam sem regressão
- [ ] **AC7:** Monitorar Sentry por 24h — 0 novos eventos `ConnectionError: Too many connections`

---

## Notas

- O `supabase-py` expõe `options` dict no `create_client()` — verificar se aceita `httpx_client` customizado
- Se `supabase-py` não permitir customizar o pool, considerar fork ou patch no `__init__`
- Alternativa: usar `postgrest-py` direto com httpx client configurado
- Redis pool já foi otimizado (50 connections, CRIT-026) — mesmo padrão necessário para Supabase
