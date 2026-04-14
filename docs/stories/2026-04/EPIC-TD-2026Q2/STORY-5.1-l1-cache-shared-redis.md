# STORY-5.1: L1 Cache Shared via Redis (TD-SYS-010)

**Priority:** P2 | **Effort:** S (8h) | **Squad:** @dev + @architect | **Status:** Draft
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** L1 cache compartilhado entre Gunicorn workers (via Redis), **so that** hit ratio melhore em deployments multi-worker.

## Acceptance Criteria
- [ ] AC1: `backend/cache.py` migra de InMemoryCache para Redis-backed (key namespace `l1:*`)
- [ ] AC2: TTL 4h mantido; hot/warm/cold priority via Redis SET com TTL diferenciado
- [ ] AC3: Métrica Prometheus `l1_cache_hit_ratio` aumenta >20%
- [ ] AC4: Backward compat — interface API igual

## Tasks
- [ ] Refactor cache.py
- [ ] Migration validation
- [ ] Métricas
- [ ] Test cache hit ratio em load test (STORY-3.3)

## Dev Notes
- `backend/redis_client.py` já existe
- TD-SYS-010 ref

## Definition of Done
- [ ] Migrated + metrics show improvement + backward compat

## Risks
- R1: Redis lat extra → mitigation: pipeline batch reads

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
