# GTM-RESILIENCE-B05 — Admin Cache Dashboard + Metricas de Observabilidade

**Track:** B — Cache Inteligente
**Prioridade:** P1
**Sprint:** 3
**Estimativa:** 6-8 horas
**Gaps Endereados:** C-05, C-06
**Dependencias:** GTM-RESILIENCE-B03 (metadata), GTM-RESILIENCE-B04 (Redis), GTM-RESILIENCE-B02 (prioridade)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

O SmartLic possui um modulo `analytics_events.py` referenciado em `search_cache.py` (linha 471), mas **o arquivo nao existe**. Isso causa `ImportError` silencioso no bloco try/except, fazendo com que toda a telemetria de cache seja descartada. Alem disso, nao existe nenhuma interface administrativa para inspecionar o estado do cache, forcar invalidacao, ou visualizar metricas de eficacia.

### Estado Atual

- **analytics_events.py**: Referenciado mas nao existe — tracking silenciosamente falha
- **Health endpoint**: `GET /v1/health` mostra status basico de Redis mas sem metricas de cache
- **Admin UI**: Nenhuma — operador nao pode inspecionar cache, ver hit rate, ou invalidar entradas
- **Cache operations**: Logadas via `logger.info()` mas sem agregacao ou trending
- **Sentry**: Tags de cache_operation existem mas sem dashboard configurado

### Impacto Operacional

- **Cego para eficacia**: Impossivel saber se cache esta ajudando ou atrapalhando
- **Sem invalidacao**: Se dados corrompidos entrarem no cache, nao ha como limpar sem deploy
- **Debug impossivel**: "Por que a busca do usuario X esta desatualizada?" — sem ferramenta para investigar
- **Sem baseline**: Impossivel medir impacto de mudancas no cache (TTL, prioridade, evicao)

---

## Problema

1. **Modulo analytics ausente**: `analytics_events.py` nao existe, toda telemetria de cache e descartada silenciosamente
2. **Sem metricas agregadas**: hit rate, miss rate, stale %, age distribution nao sao calculados
3. **Sem interface admin**: Operador nao pode inspecionar entradas, ver estado de degradacao, ou forcar invalidacao
4. **Sem historico**: Impossivel trending (cache hit rate ontem vs hoje)

---

## Solucao

### 1. Modulo analytics_events.py (Stub Funcional)

Criar modulo com funcao `track_event(event_name, properties)` que:
- Em producao: envia para Mixpanel (se MIXPANEL_TOKEN configurado)
- Em desenvolvimento: loga via `logger.debug()`
- Fallback: nunca falha (fire-and-forget)

### 2. Endpoint de Metricas de Cache

`GET /v1/admin/cache/metrics` (admin-only) retorna:

```json
{
  "hit_rate_24h": 0.73,
  "miss_rate_24h": 0.27,
  "stale_served_24h": 15,
  "fresh_served_24h": 42,
  "total_entries": 87,
  "priority_distribution": {"hot": 12, "warm": 35, "cold": 40},
  "age_distribution": {"0-1h": 15, "1-6h": 30, "6-12h": 25, "12-24h": 17},
  "degraded_keys": 3,
  "avg_fetch_duration_ms": 4500,
  "top_keys": [
    {"params_hash": "abc123", "access_count": 47, "priority": "hot", "age_hours": 1.2}
  ]
}
```

### 3. Endpoint de Invalidacao

`DELETE /v1/admin/cache/{params_hash}` — invalida entrada especifica em todos os niveis (Supabase + Redis + Local).

`DELETE /v1/admin/cache` — invalida TODAS as entradas (nuclear option, com confirmacao).

### 4. Endpoint de Inspecao

`GET /v1/admin/cache/{params_hash}` — retorna detalhes completos da entrada:
- search_params, results_count, sources, fetched_at, priority, fail_streak, coverage, etc.

### 5. Frontend Admin Page (Minima)

Pagina `/admin/cache` com:
- Dashboard de metricas (numeros + mini-graficos)
- Tabela de entradas com filtro por usuario/prioridade/status
- Botao de invalidacao por entrada
- Botao "Invalidar Tudo" com confirmacao

---

## Criterios de Aceite

### AC1 — Modulo analytics_events.py funcional
Criar `backend/analytics_events.py` com funcao `track_event(event_name: str, properties: dict)`. Se `MIXPANEL_TOKEN` configurado, envia via Mixpanel SDK. Senao, loga via `logger.debug()`. Nunca levanta excecao.
**Teste**: Chamar `track_event("test", {"key": "value"})` sem MIXPANEL_TOKEN; verificar log debug. Com token mock; verificar chamada ao SDK.

### AC2 — Cache operations rastreadas
Todas as chamadas existentes a `_track_cache_operation()` em `search_cache.py` agora chegam em `analytics_events.track_event()` em vez de falhar silenciosamente.
**Teste**: Executar `get_from_cache()` + `save_to_cache()`; verificar que `track_event` foi chamado com evento `cache_operation`.

### AC3 — Endpoint GET /v1/admin/cache/metrics
Retorna JSON com: `hit_rate_24h`, `miss_rate_24h`, `stale_served_24h`, `total_entries`, `priority_distribution`, `age_distribution`, `degraded_keys`, `avg_fetch_duration_ms`.
**Teste**: Inserir entries mistas; chamar endpoint; verificar campos e valores.

### AC4 — Metricas calculadas dos ultimos 24h
Hit rate e miss rate calculados a partir de eventos trackeados nas ultimas 24h (armazenados em Redis counter ou Supabase).
**Teste**: Simular 10 hits e 5 misses; verificar hit_rate == 0.67.

### AC5 — Endpoint DELETE /v1/admin/cache/{params_hash}
Invalida entrada especifica em: Supabase (DELETE row), Redis (DEL key), Local (unlink file). Retorna `{"deleted_levels": ["supabase", "redis", "local"]}`.
**Teste**: Inserir entry em 3 niveis; chamar DELETE; verificar ausencia em todos os niveis.

### AC6 — Endpoint DELETE /v1/admin/cache (invalidacao total)
Invalida TODAS as entradas de cache. Requer header `X-Confirm: delete-all`. Sem header, retorna 400.
**Teste**: Chamar sem header; verificar 400. Chamar com header; verificar todas as entries removidas.

### AC7 — Endpoint GET /v1/admin/cache/{params_hash} (inspecao)
Retorna detalhes completos da entrada: `search_params`, `results_count`, `sources`, `fetched_at`, `priority`, `fail_streak`, `degraded_until`, `coverage`, `access_count`, `last_accessed_at`.
**Teste**: Inserir entry com todos os campos; chamar GET; verificar todos os campos no response.

### AC8 — Todos os endpoints admin-only
Endpoints sob `/v1/admin/cache/*` requerem autenticacao + role admin. Usuarios nao-admin recebem 403.
**Teste**: Chamar sem auth; verificar 401. Chamar com user normal; verificar 403. Chamar com admin; verificar 200.

### AC9 — Frontend pagina /admin/cache (minima)
Pagina Next.js em `app/admin/cache/page.tsx` com:
- Dashboard: hit rate, total entries, degraded keys (numeros grandes)
- Tabela: entradas com colunas (hash, priority, age, access_count, fail_streak, actions)
- Botao "Invalidar" por linha
- Botao "Invalidar Tudo" com dialog de confirmacao
**Teste**: Renderizar pagina com dados mock; verificar elementos visiveis.

### AC10 — Age distribution histogram
Metricas incluem `age_distribution` com buckets: `0-1h`, `1-6h`, `6-12h`, `12-24h`. Calculado a partir de `fetched_at` de todas as entries.
**Teste**: Inserir entries com ages variados; verificar distribuicao correta nos buckets.

---

## Arquivos Afetados

| Arquivo | Alteracao |
|---------|-----------|
| `backend/analytics_events.py` | **Novo**: modulo de tracking com Mixpanel + fallback |
| `backend/routes/admin.py` | **Novo ou atualizado**: endpoints `/v1/admin/cache/*` |
| `backend/search_cache.py` | Adicionar funcoes de metricas agregadas e invalidacao |
| `backend/main.py` | Registrar router admin se nao existir |
| `frontend/app/admin/cache/page.tsx` | **Novo**: pagina admin de cache |
| `frontend/app/api/admin/cache/route.ts` | **Novo**: proxy para endpoints admin |
| `backend/tests/test_analytics_events.py` | **Novo**: testes do modulo analytics |
| `backend/tests/test_admin_cache.py` | **Novo**: testes dos endpoints admin |
| `frontend/__tests__/admin-cache.test.tsx` | **Novo**: testes da pagina admin |

---

## Dependencias

- **GTM-RESILIENCE-B03**: Campos de metadata (fail_streak, degraded_until, coverage) devem existir
- **GTM-RESILIENCE-B04**: Redis para metricas cross-worker e invalidacao distribuida
- **GTM-RESILIENCE-B02**: Campo priority para distribuicao hot/warm/cold

---

## Nota sobre Metricas de Curto Prazo vs Longo Prazo

Para o Sprint 3, metricas sao baseadas em contadores simples (Redis INCR ou Supabase counts). Metricas historicas com trending requerem time-series (Prometheus/StatsD) e sao escopo de uma story futura (Track E).

---

## Definition of Done

- [x] Todos os 10 ACs implementados e testados
- [x] `analytics_events.py` funcional e importado sem erro
- [x] Endpoints admin protegidos e funcionais
- [x] Pagina admin renderizavel com dados reais
- [x] Invalidacao funciona em todos os 3 niveis de cache
- [x] Zero regressoes na suite de testes existente
- [x] Documentacao inline dos endpoints (docstrings com exemplos de response)

## Implementation Notes (2026-02-19)

**Commit:** `7dff141` — 8 files changed, 1929+/1-

**Files Created/Modified:**
| File | Change |
|------|--------|
| `backend/analytics_events.py` | **NEW**: Mixpanel + logger.debug fallback, fire-and-forget |
| `backend/admin.py` | 4 new endpoints under `/admin/cache/*` |
| `backend/search_cache.py` | `get_cache_metrics()`, `invalidate_cache_entry()`, `invalidate_all_cache()`, `inspect_cache_entry()` + counter tracking |
| `backend/redis_pool.py` | `InMemoryCache.incr()` + `keys_by_prefix()` methods |
| `frontend/app/admin/cache/page.tsx` | **NEW**: Admin cache dashboard page |
| `backend/tests/test_analytics_events.py` | **NEW**: 11 tests |
| `backend/tests/test_admin_cache.py` | **NEW**: 15 tests |
| `frontend/__tests__/admin-cache.test.tsx` | **NEW**: 15 tests |

**Key Design Decisions:**
- Counter-based hit/miss tracking via `InMemoryCache.incr()` (per-worker, resets on restart)
- Supabase queries for persistent metrics (total entries, priority distribution, age distribution)
- No new frontend API proxy needed — existing `app/api/admin/[...path]/route.ts` handles all admin routes
- `.gitignore` has `cache/` pattern — used `git add -f` for `frontend/app/admin/cache/page.tsx`
- Admin auth reuses existing `require_admin` dependency from admin.py

**Test Results:** 26 backend + 15 frontend = 41 new tests, zero regressions
