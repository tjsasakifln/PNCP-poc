# CRIT-048: SSE Pipe Failure Regression no Frontend

**Epic:** Production Stability
**Sprint:** Sprint 5
**Priority:** P2 — MEDIUM
**Story Points:** 5 SP
**Estimate:** 3-4 horas
**Owner:** @dev

---

## Problem

O erro `failed to pipe response` no proxy SSE `/api/buscar-progress` regrediu apesar das correções CRIT-012 e CRIT-026:

**Sentry Evidence:**
- SMARTLIC-FRONTEND-1: `Error: failed to pipe response` — 18 events, **REGRESSED**, /api/buscar-progress (2d ago - 1wk)
- SMARTLIC-FRONTEND-4: `Error: failed to pipe response` — 2 events, NEW, /api/buscar-progress (2d ago)
- SMARTLIC-BACKEND-1M: `CRIT-026: SSE generator abrupt finish — TimeoutError: Timeout reading from redis-hejg.railway.internal:6379` — 7 events (2d ago)

**Fixes já aplicados (que não resolveram completamente):**
- CRIT-012: `bodyTimeout: 0` no undici, AbortController cleanup
- CRIT-026: Heartbeat a cada 15s, waiting events dentro do generator

---

## Root Cause Analysis

A cadeia de falha provável:
1. Redis Railway timeout (30s socket_timeout) durante SSE read → backend SSE generator crashes
2. Backend fecha connection abruptamente → Next.js proxy recebe "terminated" response
3. Next.js tenta pipar response já terminada → `failed to pipe response`
4. Retry logic (MAX_SSE_RETRIES=1) tenta 1x mas o backend SSE generator já encerrou

**Por que CRIT-012 não resolveu:** O fix tratou bodyTimeout do client→proxy, mas o problema real é proxy→backend (Redis timeout mata o generator upstream).

---

## Acceptance Criteria

### Diagnóstico

- [ ] **AC1:** Correlacionar timestamps de SMARTLIC-FRONTEND-1 com SMARTLIC-BACKEND-1M para confirmar que Redis timeout causa pipe failure
- [ ] **AC2:** Adicionar logging estruturado no SSE proxy com `upstream_status` e `upstream_error` quando pipe falha

### Fix Backend (SSE Generator)

- [ ] **AC3:** No `event_generator()` (routes/search.py), capturar `TimeoutError` do Redis e emitir SSE event `error` graceful em vez de crash
- [ ] **AC4:** Se Redis timeout durante SSE, fallback para polling do search state via Supabase (search_sessions table)
- [ ] **AC5:** Aumentar Redis socket_timeout no contexto de SSE reads para 60s (vs 30s global)

### Fix Frontend (Proxy)

- [ ] **AC6:** Quando `failed to pipe response`, o proxy deve retornar SSE event `error` com `retry: 5000` para o client reconectar
- [ ] **AC7:** Incrementar MAX_SSE_RETRIES de 1 para 2 (total 3 tentativas)

### Validação

- [ ] **AC8:** Testes existentes passam sem regressão
- [ ] **AC9:** Monitorar Sentry 24h — 0 novos `failed to pipe response` events

---

## Notas

- Redis Railway pode ter latency spikes (shared infra) — socket_timeout de 30s pode ser marginal
- O fallback time-based simulation no frontend já existe (se SSE falha totalmente, usa progress simulado)
- Considerar migrar SSE state de Redis Queue para Supabase Realtime (elimina Redis dependency no hot path)
