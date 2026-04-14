# STORY-2.10: Rate Limit em Endpoints Públicos (TD-SYS-017)

**Priority:** P1 (security — scraping vulnerability + DoS vector)
**Effort:** S (4-8h)
**Squad:** @dev + @architect quality gate
**Status:** Draft
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

- [ ] Middleware `rate_limit_public` em `backend/`
- [ ] Identifica caller por IP (sem auth) ou user_id (com auth)
- [ ] Limit: 60 req/min IP; 600/min user authenticado
- [ ] Resposta 429 com `Retry-After` header

### AC2: Aplicar a endpoints

- [ ] `routes/stats_public.py` — todas rotas
- [ ] `routes/plans.py` (GET /plans, /setores)
- [ ] Marketing endpoints

### AC3: Métricas

- [ ] Prometheus counter `rate_limit_hits_total{endpoint, ip_or_user}`
- [ ] Sentry alert se >100 hits/min de mesmo IP

### AC4: Testes

- [ ] pytest: simula 70 requests rápidos → 11 retornam 429

---

## Tasks / Subtasks

- [ ] Task 1: Token bucket Redis primitive (AC1)
- [ ] Task 2: Middleware integration (AC1)
- [ ] Task 3: Aplicar a endpoints (AC2)
- [ ] Task 4: Métricas + Sentry (AC3)
- [ ] Task 5: Tests (AC4)

## Dev Notes

- `backend/redis_client.py` já tem Redis pool
- Pattern token bucket: `INCR key EXPIRE 60` ou Redis Lua script atomic
- Ver `backend/quota.py` para reference de atomic Redis ops

## Testing

- pytest com fakeredis ou Redis test container
- Load test: 100 RPS por 30s

## Definition of Done

- [ ] Middleware ativo + endpoints protegidos + métricas

## Risks

- **R1**: Falsa positivo em CDN/proxy IPs compartilhados — mitigation: whitelist conhecidos

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
