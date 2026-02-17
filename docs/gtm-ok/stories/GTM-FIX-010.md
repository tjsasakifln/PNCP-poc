# GTM-FIX-010: Implement SWR Cache for PNCP Results

## Dimension Impact
- Moves D01 (Data Completeness) +1 (7/10 → 8/10)
- Moves D04 (Error Handling) +1 (6/10 → 7/10)

## Problem
Zero local data persistence. When PNCP API is down (happens frequently), users get empty error screens with no fallback. No minimum result guarantee. Previous successful searches are lost. Industry standard (Google, GitHub, Twitter) is to serve stale cached data with timestamp disclaimer when live fetch fails.

## Solution
Implement Stale-While-Revalidate (SWR) cache pattern:

1. **Persist search results** in PostgreSQL table `search_cache`
2. **On search request**: Try live PNCP fetch first
3. **On PNCP failure**: Serve stale cache with yellow banner: "⚠️ Dados de X horas atrás (PNCP indisponível)"
4. **Cache strategy**: Store raw PNCP results + metadata (search_params hash, timestamp)
5. **TTL policy**: Fresh (0-6h), Stale (6-24h), Expired (>24h, delete)
6. **Prefer stale over empty**: Always show something if available

## Acceptance Criteria
- [ ] AC1: Create `search_cache` table with schema: id, user_id, search_hash, params_json, results_json, fetched_at, created_at
- [ ] AC2: `search_hash = sha256(json.dumps(sorted(params)))` for deduplication
- [ ] AC3: After successful PNCP fetch, insert/update row in search_cache
- [ ] AC4: On PNCP fetch failure, query search_cache for matching search_hash
- [ ] AC5: If cache hit (age < 24h), return cached results with `is_from_cache: true, cache_age_hours: N`
- [ ] AC6: If no cache hit, return error (no fake data)
- [ ] AC7: Frontend displays StaleCacheBanner when `is_from_cache === true`
- [ ] AC8: Banner text: "⚠️ Resultados de [X horas] atrás. PNCP temporariamente indisponível. Dados podem estar desatualizados."
- [ ] AC9: Banner includes "Tentar novamente" button → re-fetch with force_refresh=true
- [ ] AC10: Backend test: test_cache_hit_on_pncp_failure()
- [ ] AC11: Backend test: test_cache_miss_returns_error()
- [ ] AC12: Backend test: test_cache_expired_not_served()
- [ ] AC13: Frontend test: test_stale_cache_banner_display()
- [ ] AC14: Manual test: Disconnect PNCP → verify cached results served
- [ ] AC15: Migration: `backend/supabase/migrations/YYYYMMDDHHMMSS_create_search_cache.sql`

## Effort: M (3-5 days)
## Priority: P1 (Resilience)
## Dependencies: None

## Files to Modify
- `backend/supabase/migrations/YYYYMMDDHHMMSS_create_search_cache.sql` (NEW)
- `backend/cache.py` (NEW - cache logic module)
- `backend/main.py` (integrate cache in buscar_licitacoes)
- `backend/tests/test_cache.py` (NEW - 15+ tests)
- `frontend/types/busca.ts` (add is_from_cache, cache_age_hours)
- `frontend/app/buscar/page.tsx` (add StaleCacheBanner)
- `frontend/components/buscar/StaleCacheBanner.tsx` (NEW)
- `frontend/__tests__/buscar/stale-cache.test.tsx` (NEW)

## Database Schema

**Migration: `create_search_cache.sql`**
```sql
CREATE TABLE search_cache (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  search_hash TEXT NOT NULL,
  params_json JSONB NOT NULL,
  results_json JSONB NOT NULL,
  result_count INTEGER NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, search_hash)
);

CREATE INDEX idx_search_cache_user_hash ON search_cache(user_id, search_hash);
CREATE INDEX idx_search_cache_fetched_at ON search_cache(fetched_at);

-- RLS Policies
ALTER TABLE search_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own cache"
  ON search_cache FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own cache"
  ON search_cache FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own cache"
  ON search_cache FOR UPDATE
  USING (auth.uid() = user_id);
```

## Backend Implementation

**cache.py:**
```python
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
from supabase_client import supabase

CACHE_FRESH_HOURS = 6
CACHE_STALE_HOURS = 24

def compute_search_hash(params: dict) -> str:
    """Generate deterministic hash from search params."""
    normalized = json.dumps(params, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()

def save_to_cache(user_id: str, params: dict, results: list) -> None:
    """Persist search results to cache."""
    search_hash = compute_search_hash(params)
    supabase.table("search_cache").upsert({
        "user_id": user_id,
        "search_hash": search_hash,
        "params_json": params,
        "results_json": results,
        "result_count": len(results),
        "fetched_at": datetime.utcnow().isoformat(),
    }).execute()

def get_from_cache(user_id: str, params: dict) -> Optional[dict]:
    """Retrieve cached results if available and not expired."""
    search_hash = compute_search_hash(params)
    response = supabase.table("search_cache").select("*").eq(
        "user_id", user_id
    ).eq("search_hash", search_hash).execute()

    if not response.data:
        return None

    cache_entry = response.data[0]
    fetched_at = datetime.fromisoformat(cache_entry["fetched_at"])
    age_hours = (datetime.utcnow() - fetched_at).total_seconds() / 3600

    if age_hours > CACHE_STALE_HOURS:
        return None  # Expired

    return {
        "results": cache_entry["results_json"],
        "is_from_cache": True,
        "cache_age_hours": round(age_hours, 1),
        "is_stale": age_hours > CACHE_FRESH_HOURS,
    }
```

**main.py integration:**
```python
@app.post("/buscar")
async def buscar_licitacoes(request: BuscaRequest, user_id: str = Depends(require_auth)):
    try:
        # Try live PNCP fetch
        results = await fetch_from_pncp(request)
        save_to_cache(user_id, request.dict(), results)
        return {"results": results, "is_from_cache": False}

    except PNCPAPIError as e:
        # PNCP failed, try cache
        cached = get_from_cache(user_id, request.dict())
        if cached:
            logger.warning(f"PNCP down, serving cached results (age: {cached['cache_age_hours']}h)")
            return cached

        # No cache, propagate error
        raise HTTPException(503, "PNCP indisponível e sem cache disponível")
```

## Frontend Implementation

**StaleCacheBanner.tsx:**
```tsx
interface Props {
  cacheAgeHours: number;
  onRetry: () => void;
}

export function StaleCacheBanner({ cacheAgeHours, onRetry }: Props) {
  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Clock className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-yellow-900 dark:text-yellow-100">
              Resultados em cache
            </h3>
            <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
              Exibindo dados de <strong>{Math.round(cacheAgeHours)}h atrás</strong>.
              O Portal PNCP está temporariamente indisponível. Os dados podem estar
              desatualizados.
            </p>
          </div>
        </div>
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 whitespace-nowrap"
        >
          Tentar novamente
        </button>
      </div>
    </div>
  );
}
```

**buscar/page.tsx integration:**
```tsx
const [cacheInfo, setCacheInfo] = useState<{ age: number } | null>(null);

const buscar = async () => {
  try {
    const response = await fetch('/api/buscar', { ... });
    const data = await response.json();

    if (data.is_from_cache) {
      setCacheInfo({ age: data.cache_age_hours });
    } else {
      setCacheInfo(null);
    }

    setResultados(data.results);
  } catch (error) {
    // Error handling
  }
};

return (
  <>
    {cacheInfo && (
      <StaleCacheBanner
        cacheAgeHours={cacheInfo.age}
        onRetry={() => {
          setCacheInfo(null);
          buscar();
        }}
      />
    )}
    {/* Rest of UI */}
  </>
);
```

## Testing Strategy
1. Unit test: compute_search_hash() produces consistent hashes
2. Unit test: Cache hit within 24h returns data
3. Unit test: Cache miss beyond 24h returns None
4. Integration test: PNCP success → cache updated
5. Integration test: PNCP failure + cache hit → stale data served
6. Integration test: PNCP failure + cache miss → 503 error
7. Manual test: Simulate PNCP downtime → verify banner + cached results

## Cache Cleanup Job (future enhancement)
```python
# Run daily via cron/scheduler
def cleanup_expired_cache():
    cutoff = datetime.utcnow() - timedelta(hours=CACHE_STALE_HOURS)
    supabase.table("search_cache").delete().lt("fetched_at", cutoff.isoformat()).execute()
```

## Monitoring
- Track cache hit rate: `cache_hits / (cache_hits + cache_misses)`
- Alert if cache hit rate < 10% (indicates PNCP stability improved or cache not working)
- Alert if cache age > 12h (indicates prolonged PNCP outage)
- Mixpanel event: `search_from_cache` with `age_hours` property

## Future Enhancement (not in scope)
- Shared cache: Allow users to see other users' recent searches (privacy permitting)
- Background refresh: Async task to refresh stale cache during off-peak hours
- Multi-tier cache: Redis for hot searches + PostgreSQL for cold storage
- Cache warming: Pre-fetch popular search combinations nightly

## ⚠️ REVISÃO — Impacto PCP API (2026-02-16)

**Contexto:** Com a integração do Portal de Compras Públicas (GTM-FIX-011), o cache SWR precisa cobrir ambas as fontes.

**Alterações nesta story:**

1. **AC1 revisado:** Tabela `search_cache` deve incluir campo `sources_json JSONB` para registrar quais fontes contribuíram para o resultado cacheado:
   ```sql
   sources_json JSONB NOT NULL DEFAULT '["pncp"]'::jsonb,
   -- Exemplo: ["pncp", "pcp"] ou ["pncp"] (se PCP falhou nessa busca)
   ```

2. **AC2 revisado:** `search_hash` deve incluir `sources` no cálculo (mesmo params mas fontes diferentes = cache entries diferentes? **NÃO** — mesmos params sempre buscam todas as fontes habilitadas. O hash permanece baseado apenas nos params de busca. O `sources_json` é metadata do que foi efetivamente consultado).

3. **AC5 revisado:** Quando servindo cache stale, informar quais fontes estavam disponíveis:
   ```python
   return {
       "results": cache_entry["results_json"],
       "is_from_cache": True,
       "cache_age_hours": round(age_hours, 1),
       "cached_sources": cache_entry.get("sources_json", ["pncp"]),
   }
   ```

4. **AC8 revisado:** Banner de cache deve informar fontes: "⚠️ Resultados de Xh atrás (PNCP + Portal de Compras Públicas). Dados podem estar desatualizados."

5. **Novo AC16:** Quando PCP falha mas PNCP retorna dados (ou vice-versa), o resultado NÃO é cacheado com `is_from_cache` — é um resultado parcial live. Apenas falha de TODAS as fontes triggera serving de cache.

6. **Novo AC17:** Fallback em cascata:
   ```
   Live (PNCP + PCP) → Live parcial (só PNCP ou só PCP) → Cache stale → Error 503
   ```
   O cache só é usado quando AMBAS as fontes falham. Resultado parcial (1 fonte live) é preferido sobre cache stale.

7. **Impacto no effort:** +0.5 day (de M/3-5d para M/4-5d) — lógica de merge de sources no cache.

**Dependência:** Se implementada ANTES de GTM-FIX-011, manter implementação somente-PNCP com `sources_json` defaulting to `["pncp"]`. Quando GTM-FIX-011 entrar, o campo se popula automaticamente.
