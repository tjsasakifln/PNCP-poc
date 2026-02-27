# STORY-306: Cache Correctness & Data Integrity

**Sprint:** IMPORTANT — Semana 2
**Size:** M (6-8h)
**Root Cause:** Diagnostic Report 2026-02-27 — HIGH H8, MEDIUM M4
**Depends on:** STORY-303 (backend precisa estar de pe)
**Industry Standard:** [Akamai — Cache Key Query Parameters](https://techdocs.akamai.com/property-mgr/docs/cache-key-query-param), [Redis Cache Key Design](https://leapcell.io/blog/optimizing-database-performance-with-redis-cache-key-design-and-invalidation-strategies)

## Contexto

O cache do SmartLic pode servir dados ERRADOS silenciosamente. A cache key exclui `date_from` e `date_to`, o que significa que duas buscas pelo mesmo setor/UF mas com periodos DIFERENTES (ex: ultimos 7 dias vs ultimos 30 dias) retornam o MESMO resultado cacheado. O usuario recebe dados de um periodo que nao pediu.

**Evidencia:**
- `backend/search_cache.py:109-123` — funcao `compute_search_hash()`:
```python
normalized = {
    "setor_id": params.get("setor_id"),
    "ufs": sorted(params.get("ufs", [])),
    "status": params.get("status"),
    "modalidades": sorted(params.get("modalidades") or []) or None,
    "modo_busca": params.get("modo_busca"),
}
```
- `date_from` e `date_to` NAO estao no dict normalizado
- Comentario no codigo (linhas 110-114): "Excludes dates intentionally — stale cache should serve regardless of date range"

**Segundo problema:** TTLs inconsistentes entre camadas de cache:
- L1 InMemory: 4h (`REDIS_CACHE_TTL_SECONDS = 14400`)
- L2 Supabase: 24h (`CACHE_STALE_HOURS = 24`)
- L3 Local file: 24h (`LOCAL_CACHE_TTL_HOURS = 24`)
- Fresh window: 6h (`CACHE_FRESH_HOURS = 6`)

Os TTLs criam janelas onde uma camada serve "fresh" e outra serve "stale" para a mesma query.

**Fundamentacao tecnica:**
- [Akamai — Cache Key Query Parameters](https://techdocs.akamai.com/property-mgr/docs/cache-key-query-param): "Different query parameters should ideally result in different cache keys to avoid serving incorrect cached data"
- [Redis Cache Key Design](https://leapcell.io/blog/optimizing-database-performance-with-redis-cache-key-design-and-invalidation-strategies): "Using a deterministic key generation function reduces cache misses and avoids stale or incorrect data"
- [OneUpTime — Query Cache Design 2026](https://oneuptime.com/blog/post/2026-01-30-query-cache-design/view): "Include version information in cache keys so stale keys are naturally orphaned"
- [Singhajit — Caching Strategies](https://singhajit.com/caching-strategies-explained/): "Always set TTL — stale data is often worse than no cache. The hardest part of query caching is knowing when to invalidate"

## Acceptance Criteria

### Cache Key Correctness

- [x] AC1: `compute_search_hash()` inclui `date_from` e `date_to` no dict normalizado
- [x] AC2: Formato de data normalizado para ISO 8601 (YYYY-MM-DD) antes de incluir no hash — evita variacao de formato
- [x] AC3: Busca com setor=X, UF=SP, periodo=7d retorna cache DIFERENTE de setor=X, UF=SP, periodo=30d
- [x] AC4: Cache key inclui TODOS os parametros que afetam o resultado:

| Parametro | Incluido Antes | Incluido Agora |
|-----------|---------------|----------------|
| setor_id | Sim | Sim |
| ufs | Sim (sorted) | Sim (sorted) |
| status | Sim | Sim |
| modalidades | Sim (sorted) | Sim (sorted) |
| modo_busca | Sim | Sim |
| date_from | **NAO** | **SIM** |
| date_to | **NAO** | **SIM** |

### Fallback para Cache sem Data (SWR)

- [x] AC5: Quando busca falha (todas as fontes down), o sistema PODE servir cache de qualquer data range como fallback — mas DEVE marcar o resultado como `"cache_fallback": true, "cache_date_range": "2026-02-20 a 2026-02-25"` no response
- [x] AC6: Frontend exibe aviso visual quando `cache_fallback: true`: "Resultados de cache (periodo X a Y). Dados podem estar desatualizados."
- [x] AC7: Logica de fallback: primeiro tenta cache com key EXATA (incluindo datas) → se nao encontra, tenta cache do mesmo setor/UF SEM datas (fallback) → se nao encontra, retorna vazio

### TTL Unification

- [x] AC8: Documentar TTL policy em um unico local (`backend/cache_policy.py` ou constantes em `search_cache.py`):

| Camada | TTL | Status | Comportamento |
|--------|-----|--------|---------------|
| L1 InMemory | 4h | Fresh 0-4h | Serve direto |
| L2 Redis | 4h | Fresh 0-4h | Serve se L1 miss |
| L3 Supabase | 24h | Stale 4-24h | Serve como fallback + trigger revalidacao |
| L4 Local File | 24h | Emergency | Serve se Supabase down |

- [x] AC9: L1 e L2 com MESMO TTL (4h) — nao faz sentido L1=4h e L2=24h
- [x] AC10: SWR (Stale-While-Revalidate): entre 4-24h, serve stale E dispara revalidacao em background
- [x] AC11: Apos 24h, cache expirado — nova busca obrigatoria (nao serve dados de >24h exceto em emergency)

### Mitigacao de Thundering Herd no Deploy

- [x] AC12: Dual-read por 24h pos-deploy: ao buscar no cache, tentar key NOVA primeiro → se miss, tentar key ANTIGA (sem datas) → se miss, busca live. Controlado por flag `CACHE_LEGACY_KEY_FALLBACK` (default `true`, desabilitar manualmente apos 24h)
- [x] AC13: Cache warming pos-deploy: background task que revalida as 10 queries mais populares (baseado em `search_sessions` recentes) nos primeiros 5 minutos apos startup

### Testes

- [x] AC14: Teste: mesma query com datas diferentes gera cache keys diferentes
- [x] AC15: Teste: fallback serve cache antigo com flag `cache_fallback: true`
- [x] AC16: Teste: dual-read retorna cache de key antiga quando key nova miss
- [x] AC17: Teste: SWR dispara revalidacao em background quando serve stale
- [x] AC18: Testes existentes passando (6072 backend, 3595 frontend)

## Technical Notes

### Por que incluir datas no cache key (e nao era assim antes)

A decisao original de excluir datas foi tomada para maximizar cache hits em cenarios de fallback. O raciocinio era: "se todas as fontes estao down, melhor servir resultados de qualquer periodo do que nada."

O problema: isso tambem serve resultados de periodo errado quando as fontes ESTAO FUNCIONANDO. Um usuario busca "ultimos 7 dias" e recebe resultados de "ultimos 30 dias" que estavam cacheados — sem saber.

**Solucao:** Cache key COM datas para operacao normal + fallback EXPLÍCITO (sem datas) para quando fontes falham. Dois niveis de lookup no cache.

### Impacto no cache hit rate

Incluir datas no cache key vai REDUZIR o hit rate inicialmente. Isso e esperado e correto. Dados errados servidos com 90% hit rate sao piores que dados corretos com 60% hit rate. O SWR background revalidation vai compensar.

### RISCO: Thundering Herd no Deploy

Mudar a cache key invalida TODOS os cache entries existentes instantaneamente. No deploy, 100% das buscas serao cache miss, gerando requests simultaneos para as 3 APIs governamentais. Com 50 usuarios ativos, isso pode tripar os circuit breakers e causar DDoS nos endpoints governamentais.

**Mitigacao obrigatoria (AC17-AC18):** Dual-read por 24h pos-deploy — tentar key nova primeiro, se miss tentar key antiga. Isso faz a transicao ser gradual em vez de cliff.

### Nota sobre TTL L2

A arquitetura atual usa InMemory (L1) + Supabase (L3) + Local File (L4). A tabela TTL em AC8 introduz "L2 Redis" por clareza futura, mas o sistema atual nao usa Redis como camada de cache de busca (Redis e usado para circuit breaker state e feature flags). Se Redis nao for adicionado como L2 nesta story, manter a tabela com as camadas existentes (L1 InMemory, L2 Supabase, L3 Local File).

## Rollback Plan

| Condicao | Acao | Tempo |
|----------|------|-------|
| Thundering herd causa circuit breakers OPEN | Feature flag `CACHE_LEGACY_KEY_FALLBACK=true` (ativa dual-read ilimitado) | < 2 min (env var) |
| Cache hit rate cai abaixo de 20% por 1h | Reverter commit + redeploy | < 15 min |
| Frontend cache fallback UI confusa | Desabilitar banner via feature flag `SHOW_CACHE_FALLBACK_BANNER=false` | < 2 min |

## Smoke Test Pos-Deploy

```bash
# 1. Cache key diferente para datas diferentes
curl -s "https://api.smartlic.tech/debug/cache-key?setor=vestuario&ufs=SP&date_from=2026-02-20&date_to=2026-02-27"
curl -s "https://api.smartlic.tech/debug/cache-key?setor=vestuario&ufs=SP&date_from=2026-02-01&date_to=2026-02-27"
# Esperado: hashes DIFERENTES

# 2. Cache hit rate nao zerou (dual-read funcionando)
curl -s https://api.smartlic.tech/health | jq '.dependencies.cache'
# Esperado: hit_rate > 0 (nao 0%)
```

## Files to Change

| File | Mudanca |
|------|---------|
| `backend/search_cache.py:109-123` | Incluir `date_from`/`date_to` em `compute_search_hash()` |
| `backend/search_cache.py` | Adicionar fallback lookup sem datas |
| `backend/search_cache.py` | Unificar TTL constants |
| `backend/search_pipeline.py` | Propagar `cache_fallback` flag no response |
| `frontend/` (resultados page) | Exibir aviso de cache fallback |
| `backend/tests/test_search_cache.py` | Testes de cache key e fallback |

## Definition of Done

- [x] Cache key inclui todos os parametros que afetam resultados (incluindo datas)
- [x] Duas buscas com datas diferentes retornam resultados diferentes
- [x] Fallback explicito com flag visual para o usuario
- [x] TTLs consistentes entre camadas
- [x] Testes cobrindo cache key, fallback, TTL
