# STORY-2.10: Rate Limit em Endpoints Públicos (TD-SYS-017)

**Priority:** P1 (security — scraping vulnerability + DoS vector)
**Effort:** S (4-8h)
**Squad:** @dev + @architect quality gate
**Status:** Ready for Review
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** SmartLic,
**I want** rate limit em endpoints públicos (`/stats_public/*`, `/setores`, `/planos`),
**so that** evite scraping abusivo + DoS.

---

## Acceptance Criteria

### AC1: Token bucket Redis

- [x] Dependency `rate_limit_public` factory em `backend/public_rate_limit.py` (Depends() callable, idiomático FastAPI; reusa `RateLimiter` existente)
- [x] Identifica caller por último IP do `X-Forwarded-For` (unauth) ou `request.state.user_id` (auth)
- [x] Limit: 60 req/min IP; 600/min user authenticado
- [x] Resposta 429 com `Retry-After` header

### AC2: Aplicar a endpoints

- [x] `routes/stats_public.py` — aplicado
- [x] `routes/plans.py` — GET /plans com rate limit
- [x] `routes/sectors_public.py` (endpoint /v1/setores) — aplicado

### AC3: Métricas

- [x] Prometheus counter `smartlic_rate_limit_hits_total{endpoint, caller_type}` em `metrics.py`
- [x] Sentry alert (warning level) quando IP excede burst threshold — dedup via Redis SETNX 60s TTL

### AC4: Testes

- [x] 11 testes passando em `backend/tests/test_public_rate_limit.py` (XFF extraction, 429+Retry-After, Prometheus counter, Sentry burst alert dedup, fail-open)

---

## Tasks / Subtasks

- [x] Task 1: Token bucket Redis primitive (AC1) — reusou `rate_limiter.rate_limiter` singleton
- [x] Task 2: Dependency factory integration (AC1)
- [x] Task 3: Aplicar a endpoints (AC2)
- [x] Task 4: Métricas + Sentry (AC3)
- [x] Task 5: Tests (AC4)

## Dev Notes

- `backend/redis_client.py` já tem Redis pool
- Pattern token bucket: `INCR key EXPIRE 60` ou Redis Lua script atomic
- Ver `backend/quota.py` para reference de atomic Redis ops

## Testing

- pytest com fakeredis ou Redis test container
- Load test: 100 RPS por 30s

## File List

- **Created**:
  - `backend/public_rate_limit.py` (Depends() factory — nota: arquivo em `backend/` porque `middleware.py` já existe como arquivo, não diretório)
  - `backend/tests/test_public_rate_limit.py`
- **Modified**:
  - `backend/metrics.py` (counter `RATE_LIMIT_HITS`)
  - `backend/routes/stats_public.py`
  - `backend/routes/plans.py`
  - `backend/routes/sectors_public.py`

## Definition of Done

- [x] Dependency ativo + endpoints protegidos + métricas

## Risks

- **R1**: Falsa positivo em CDN/proxy IPs compartilhados — mitigation: whitelist conhecidos

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — Depends() factory (não middleware), 11 tests. Reusou RateLimiter singleton. | @dev (EPIC-TD Sprint 1 batch) |
