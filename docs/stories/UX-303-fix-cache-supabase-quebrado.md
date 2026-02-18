# Story UX-303: Fix Cache Supabase Quebrado (Falha Silenciosa)

**Epic:** EPIC-UX-PREMIUM-2026-02
**Story ID:** UX-303
**Priority:** 🔴 P0 CRITICAL
**Story Points:** 5 SP
**Created:** 2026-02-18
**Owner:** @devops + @dev
**Status:** 🟢 CONCLUÍDO (code-level)

---

## Story Overview

**Problema:** Schema migration para coluna `fetched_at` não foi aplicada em produção. Cache Supabase falha silenciosamente, desperdiçando processamento.

**Evidência de Logs:**
```
Failed to save to Supabase cache:
{'code': 'PGRST204', 'message': "Could not find the 'fetched_at' column of 'search_results_cache' in the schema cache"}

Processamento: 11.106 resultados → cache falha → próxima busca reprocessa tudo
```

**Impacto:**
- Feature de cache 100% não-funcional
- Desperdício de recursos (11k results reprocessados sempre)
- Usuário não sabe que cache está quebrado
- Zero hit rate quando deveria ser >60%

**Goal:** Cache funcional com fallback de 3 níveis + monitoramento ativo.

---

## Acceptance Criteria

### AC1: Migration `fetched_at` Aplicada em Produção
- [ ] **GIVEN** migration file existe: `027_search_cache_add_sources_and_fetched_at.sql`
- [ ] **WHEN** executada em produção via Supabase CLI
- [ ] **THEN** coluna `fetched_at` existe em `search_results_cache`
- [ ] **AND** query `SELECT fetched_at FROM search_results_cache LIMIT 1` retorna sucesso

**Migration SQL:**
```sql
-- 027_search_cache_add_sources_and_fetched_at.sql
ALTER TABLE search_results_cache
ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_search_results_cache_fetched_at
ON search_results_cache(fetched_at DESC);
```

### AC2: Cache Save com Retry + Fallback
- [ ] **GIVEN** save to Supabase falha
- [ ] **WHEN** erro é capturado
- [ ] **THEN** tenta salvar em Redis (2º nível)
- [ ] **AND** se Redis falha, salva em arquivo local (3º nível)
- [ ] **AND** NÃO crasha a busca

**Implementação:**
```python
async def save_to_cache_with_fallback(cache_key, results):
    # Nível 1: Supabase (persistente, 24h TTL)
    try:
        await save_to_supabase_cache(cache_key, results)
        logger.info(f"✓ Cache saved to Supabase: {len(results)} results")
        return {"level": "supabase", "success": True}
    except Exception as e:
        logger.error(f"Supabase cache failed: {e}", exc_info=True)
        sentry_sdk.capture_exception(e)

    # Nível 2: Redis (in-memory, 4h TTL)
    try:
        await save_to_redis_cache(cache_key, results, ttl=14400)
        logger.warning(f"⚠️ Fallback: Cache saved to Redis (Supabase failed)")
        return {"level": "redis", "success": True}
    except Exception as e:
        logger.error(f"Redis cache failed: {e}")

    # Nível 3: Local file (último recurso, 1h TTL)
    try:
        await save_to_local_cache(cache_key, results, ttl=3600)
        logger.warning(f"⚠️ Fallback: Cache saved to local file (Redis failed)")
        return {"level": "local", "success": True}
    except Exception as e:
        logger.error(f"All cache levels failed: {e}")
        return {"level": "none", "success": False}
```

### AC3: Cache Hit Rate Monitoring
- [ ] **GIVEN** cache operations
- [ ] **WHEN** busca completa
- [ ] **THEN** emite métrica:
  ```python
  mixpanel.track("cache_operation", {
      "hit": True/False,
      "level": "supabase" | "redis" | "local" | "miss",
      "cache_age_seconds": 7200,
      "results_count": 11106
  })
  ```
- [ ] **AND** Dashboard Mixpanel mostra:
  - Cache hit rate (%)
  - Avg cache age
  - Cache level distribution

### AC4: Cache Stale Policy (GTM-FIX-010)
- [ ] **GIVEN** cache existe com idade conhecida
- [ ] **WHEN** verifica TTL
- [ ] **THEN** classifica como:
  - **Fresh:** 0-6h (serve direto)
  - **Stale:** 6-24h (serve com aviso)
  - **Expired:** >24h (não serve, refetch)

**Implementação:**
```python
def get_cache_status(fetched_at: datetime) -> CacheStatus:
    age_hours = (datetime.utcnow() - fetched_at).total_seconds() / 3600

    if age_hours <= 6:
        return CacheStatus.FRESH
    elif age_hours <= 24:
        return CacheStatus.STALE
    else:
        return CacheStatus.EXPIRED
```

### AC5: Frontend Indicador de Cache
- [ ] **GIVEN** busca retorna resultados em cache
- [ ] **WHEN** exibe resultados
- [ ] **THEN** mostra banner:
  ```tsx
  <CacheBanner
    status="fresh" | "stale"
    ageHours={3.5}
    sources={["pncp", "portal_compras"]}
    onRefresh={() => refetchWithForce(true)}
  />
  ```

**Exemplo UI:**
```
┌─────────────────────────────────────────────────┐
│ ✓ Resultados de 3 horas atrás (cache fresco)    │
│   Fontes: PNCP + Portal de Compras Públicas     │
│                                    [Atualizar ↻] │
└─────────────────────────────────────────────────┘
```

### AC6: Sentry Alert para Cache Failure
- [ ] **GIVEN** cache Supabase falha
- [ ] **WHEN** erro capturado
- [ ] **THEN** envia Sentry alert:
  ```python
  sentry_sdk.capture_exception(e, extra={
      "cache_operation": "save",
      "cache_key": cache_key,
      "results_count": len(results),
      "error_code": e.code if hasattr(e, 'code') else None
  })
  ```
- [ ] **AND** Sentry rule: alert #ops-alerts se >10 falhas em 1h

### AC7: Health Check Endpoint para Cache
- [ ] **GIVEN** endpoint `/health/cache`
- [ ] **WHEN** chamado
- [ ] **THEN** retorna status de cada nível:
  ```json
  {
    "supabase": {
      "status": "healthy" | "degraded" | "down",
      "latency_ms": 45,
      "last_error": null
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 3,
      "last_error": null
    },
    "local": {
      "status": "healthy",
      "files_count": 12,
      "total_size_mb": 34.5
    }
  }
  ```

### AC8: Automatic Cache Cleanup (Local Files)
- [ ] **GIVEN** cache local acumula arquivos antigos
- [ ] **WHEN** cron job roda (diário)
- [ ] **THEN** deleta arquivos >24h
- [ ] **AND** loga quantidade deletada

**Implementação:**
```python
async def cleanup_local_cache():
    cache_dir = Path("/tmp/smartlic_cache")
    now = datetime.utcnow()
    deleted_count = 0

    for file_path in cache_dir.glob("*.json"):
        age_hours = (now - datetime.fromtimestamp(file_path.stat().st_mtime)).total_seconds() / 3600

        if age_hours > 24:
            file_path.unlink()
            deleted_count += 1

    logger.info(f"Cleaned up {deleted_count} local cache files")
```

### AC9: Cache Warming (Opcional)
- [ ] **GIVEN** busca popular conhecida (ex: "Uniformes, SP")
- [ ] **WHEN** cache expira
- [ ] **THEN** background job re-fetcha proativamente
- [ ] **AND** próximo usuário vê cache fresh

### AC10: Tests de Cache Multi-Level
- [ ] **GIVEN** teste automatizado
- [ ] **WHEN** simula falha em cada nível
- [ ] **THEN** verifica fallback para próximo nível
- [ ] **AND** busca nunca falha por cache quebrado

---

## Technical Implementation

### DevOps: Apply Migration

```bash
# Connect to Supabase production
npx supabase link --project-ref fqqyovlzdzimiwfofdjk

# Apply migration
npx supabase db push

# Verify
npx supabase db pull
```

### Backend: Multi-Level Cache

```python
# backend/search_cache.py

from enum import Enum
from typing import Optional, Dict, Any
import redis
import json
from pathlib import Path

class CacheLevel(str, Enum):
    SUPABASE = "supabase"
    REDIS = "redis"
    LOCAL = "local"
    MISS = "miss"

class CacheStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"

# Redis client (se disponível)
try:
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
except:
    redis_client = None

async def save_to_cache_with_fallback(
    cache_key: str,
    results: List[dict],
    search_params: dict
) -> Dict[str, Any]:
    # Nível 1: Supabase
    try:
        await _save_to_supabase(cache_key, results, search_params)
        logger.info(f"✓ Supabase cache: {len(results)} results")
        return {"level": CacheLevel.SUPABASE, "success": True}
    except Exception as e:
        logger.error(f"Supabase cache failed: {e}", exc_info=True)
        sentry_sdk.capture_exception(e, extra={
            "cache_operation": "save_supabase",
            "cache_key": cache_key,
            "results_count": len(results)
        })

    # Nível 2: Redis
    if redis_client:
        try:
            cache_data = {
                "results": results,
                "search_params": search_params,
                "fetched_at": datetime.utcnow().isoformat()
            }
            redis_client.setex(
                f"cache:{cache_key}",
                14400,  # 4h TTL
                json.dumps(cache_data)
            )
            logger.warning(f"⚠️ Redis fallback: {len(results)} results")
            return {"level": CacheLevel.REDIS, "success": True}
        except Exception as e:
            logger.error(f"Redis cache failed: {e}")

    # Nível 3: Local file
    try:
        cache_dir = Path("/tmp/smartlic_cache")
        cache_dir.mkdir(exist_ok=True)

        cache_file = cache_dir / f"{cache_key}.json"
        cache_data = {
            "results": results,
            "search_params": search_params,
            "fetched_at": datetime.utcnow().isoformat()
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        logger.warning(f"⚠️ Local file fallback: {len(results)} results")
        return {"level": CacheLevel.LOCAL, "success": True}

    except Exception as e:
        logger.error(f"All cache levels failed: {e}")
        return {"level": CacheLevel.MISS, "success": False}

async def get_from_cache_multi_level(
    cache_key: str,
    allow_stale: bool = False
) -> Optional[Dict[str, Any]]:
    # Try Supabase first
    try:
        data = await _get_from_supabase(cache_key)
        if data:
            status = _get_cache_status(data["fetched_at"])
            if status == CacheStatus.FRESH or (allow_stale and status == CacheStatus.STALE):
                return {**data, "cache_level": CacheLevel.SUPABASE, "cache_status": status}
    except Exception as e:
        logger.error(f"Supabase cache read failed: {e}")

    # Try Redis
    if redis_client:
        try:
            cached = redis_client.get(f"cache:{cache_key}")
            if cached:
                data = json.loads(cached)
                return {**data, "cache_level": CacheLevel.REDIS, "cache_status": CacheStatus.FRESH}
        except Exception as e:
            logger.error(f"Redis cache read failed: {e}")

    # Try local file
    cache_file = Path(f"/tmp/smartlic_cache/{cache_key}.json")
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                data = json.load(f)
            status = _get_cache_status(datetime.fromisoformat(data["fetched_at"]))
            if status == CacheStatus.FRESH or (allow_stale and status == CacheStatus.STALE):
                return {**data, "cache_level": CacheLevel.LOCAL, "cache_status": status}
        except Exception as e:
            logger.error(f"Local cache read failed: {e}")

    return None
```

### Frontend: Cache Banner

```tsx
// components/CacheBanner.tsx

interface CacheBannerProps {
  status: 'fresh' | 'stale';
  ageHours: number;
  sources: string[];
  onRefresh: () => void;
}

export const CacheBanner: React.FC<CacheBannerProps> = ({
  status,
  ageHours,
  sources,
  onRefresh
}) => {
  const Icon = status === 'fresh' ? CheckCircleIcon : ClockIcon;
  const bgColor = status === 'fresh' ? 'bg-green-50' : 'bg-yellow-50';
  const textColor = status === 'fresh' ? 'text-green-800' : 'text-yellow-800';

  const sourceNames = sources.map(s => {
    if (s === 'pncp') return 'PNCP';
    if (s === 'portal_compras') return 'Portal de Compras Públicas';
    return s;
  }).join(' + ');

  return (
    <div className={`${bgColor} ${textColor} px-4 py-3 rounded-lg flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5" />
        <div>
          <p className="font-medium">
            {status === 'fresh'
              ? `Resultados de ${formatHours(ageHours)} atrás (cache fresco)`
              : `Resultados de ${formatHours(ageHours)} atrás (cache desatualizado)`
            }
          </p>
          <p className="text-sm opacity-80">
            Fontes: {sourceNames}
          </p>
        </div>
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={onRefresh}
      >
        <RefreshIcon className="w-4 h-4 mr-2" />
        Atualizar
      </Button>
    </div>
  );
};
```

---

## File List

### DevOps
- [ ] `supabase/migrations/027_search_cache_add_sources_and_fetched_at.sql` — Migration
- [ ] `.env.production` — REDIS_URL config

### Backend
- [ ] `backend/search_cache.py` — Multi-level cache logic
- [ ] `backend/routes/health.py` — `/health/cache` endpoint
- [ ] `backend/cron_jobs.py` — Cleanup local cache
- [ ] `backend/tests/test_cache_multi_level.py` — 12 novos testes

### Frontend
- [ ] `frontend/components/CacheBanner.tsx` — NOVO componente
- [ ] `frontend/app/buscar/page.tsx` — Integrar CacheBanner
- [ ] `frontend/__tests__/cache-banner.test.tsx` — 4 novos testes

---

## Dependencies

### Blockers
- Supabase migration deve ser aplicada ANTES de deploy

### Related Stories
- UX-301 (Timeout) — Cache stale é fallback para timeout

---

## Definition of Done

- [ ] Migration aplicada em prod
- [ ] Multi-level cache funcionando
- [ ] Health check retorna status OK
- [ ] Cache hit rate >60% (métrica Mixpanel)
- [ ] 12 testes backend passam
- [ ] 4 testes frontend passam
- [ ] QA sign-off

---

## Estimation Breakdown

- Migration + DevOps: 1 SP
- Multi-level cache backend: 2 SP
- Frontend CacheBanner: 1 SP
- Testing: 1 SP

**Total:** 5 SP

---

**Status:** 🟢 CONCLUÍDO (code-level: AC2-AC10, 9/10 ACs)
**Pending:** AC1 (DevOps — apply migration in production via Supabase CLI)
**Next:** @devops `npx supabase db push` em produção
