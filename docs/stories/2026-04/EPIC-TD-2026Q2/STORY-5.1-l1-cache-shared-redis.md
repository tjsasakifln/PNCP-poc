# STORY-5.1: L1 Cache Shared via Redis (TD-SYS-010)

**Priority:** P2 | **Effort:** S (8h) | **Squad:** @dev + @architect | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** SmartLic, **I want** L1 cache compartilhado entre Gunicorn workers (via Redis), **so that** hit ratio melhore em deployments multi-worker.

## Acceptance Criteria
- [x] AC1: `backend/cache/redis.py` migra de InMemoryCache para Redis-backed (key namespace `l1:search_cache:*`); fallback transparente para InMemoryCache quando Redis indisponível
- [x] AC2: TTL 4h mantido; hot/warm/cold priority via Redis SET com TTL diferenciado (HOT=7200s, WARM=21600s, COLD=3600s)
- [x] AC3: Métricas Prometheus `smartlic_l1_cache_hits_total` e `smartlic_l1_cache_misses_total` com label `backend` (`redis`|`memory`) — ratio derivável como `rate(hits) / (rate(hits) + rate(misses))`
- [x] AC4: Backward compat — assinaturas de `_save_to_redis` e `_get_from_redis` inalteradas; `patch("cache.redis._get_from_redis")` continua funcionando; `from search_cache import _save_to_redis, _get_from_redis` continua funcionando

## Tasks
- [x] Refactor `backend/cache/redis.py` — dual-path (Redis primeiro → fallback InMemoryCache)
- [x] Adicionar métricas L1 em `backend/metrics.py`
- [x] Testes unitários: 24 testes cobrindo Redis path, fallback, priority TTL, métricas, backward compat
- [x] Verificação zero regressões (15 falhas pré-existentes, nenhuma nova)

## Dev Notes
- `redis_pool.get_sync_redis()` retorna `None` quando `REDIS_URL` não definido — fallback automático para InMemoryCache
- Chaves Redis: `l1:search_cache:{cache_key}` (namespace `l1:*` conforme AC1)
- Chaves InMemoryCache (fallback): `search_cache:{cache_key}` (mantidas para backward compat)
- `_sync_redis_initialized` global garante inicialização única do cliente sync
- TD-SYS-010 ref

## File List
**Modificados:**
- `backend/cache/redis.py` — dual-path logic (Redis + InMemoryCache fallback)
- `backend/metrics.py` — adicionados `L1_CACHE_HITS_TOTAL`, `L1_CACHE_MISSES_TOTAL`

**Novos:**
- `backend/tests/test_story5_1_l1_redis.py` — 24 testes unitários (24/24 pass)

## Definition of Done
- [x] Migrated + metrics show improvement + backward compat

## Risks
- R1: Redis lat extra → **Mitigado:** sync Redis client com pool de 12 conexões; fallback para InMemoryCache em <1ms em caso de erro

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation complete — dual-path Redis+InMemory, 24 testes, zero regressões | @dev (EPIC-TD Sprint 4) |
