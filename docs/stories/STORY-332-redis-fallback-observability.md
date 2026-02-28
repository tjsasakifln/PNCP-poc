# STORY-332: Métricas e alertas para Redis down com fallback InMemoryCache

**Prioridade:** P2 (observabilidade)
**Complexidade:** S (Small)
**Sprint:** CRIT-SEARCH

## Problema

Quando Redis fica indisponível (timeout), o sistema faz fallback silencioso para InMemoryCache. Não há métricas, alertas, ou visibilidade no admin dashboard.

**Evidência:** Log "Redis connection failed: Timeout connecting to server — using InMemoryCache fallback" sem métrica correspondente.

## Causa Raiz

O fallback InMemoryCache funciona corretamente para single-worker, mas não há instrumentação para diferenciar "Redis healthy" de "Redis down + InMemory fallback".

## Critérios de Aceite

- [ ] AC1: Métrica Prometheus `smartlic_redis_available` (gauge, 0/1) atualizada a cada health check
- [ ] AC2: Métrica `smartlic_redis_fallback_duration_seconds` (gauge)
- [ ] AC3: `GET /health/cache` inclui `redis_status: "connected" | "fallback"`
- [ ] AC4: Admin dashboard (`/admin/cache`) mostra indicador visual de Redis status
- [ ] AC5: Se Redis em fallback > 5min, log WARNING a cada 60s (não a cada request)
- [ ] AC6: Teste: simular Redis timeout → verificar métricas

## Arquivos Afetados

- `backend/redis_pool.py` (métricas)
- `backend/routes/health.py` (campo no response)
- `backend/metrics.py` (declarar métricas)
- `frontend/app/admin/cache/page.tsx` (indicador visual)
- `backend/tests/test_redis_fallback_metrics.py` (novo)
