# STORY-TD-008: SWR Adoption + Pipeline Refactor Foundation

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Frontend / Backend
**Estimativa:** 44-60h (34-46h codigo + 10-14h testes)
**Prioridade:** P1
**Debt IDs:** FE-08, TD-A02

## Objetivo

Dois trabalhos estruturais que reduzem complexidade em camadas diferentes: (1) adotar SWR como data fetching library no frontend, substituindo fetch manual + useEffect + loading states em todos GET endpoints, e (2) refatorar `search_pipeline.py` (800+ linhas, god module) em stages modulares no backend.

**Por que combinados:** Ambos sao os maiores esforcos do Tier 1 e nao tem dependencias entre si — podem progredir em paralelo por diferentes desenvolvedores. Estao na mesma story por agrupamento de sprint capacity.

## Acceptance Criteria

### Parte 1: SWR Adoption (FE-08) — 20-28h

#### Fase A: Setup + GET Endpoints Simples
- [ ] AC1: Instalar `swr` e configurar `SWRConfig` provider global em `app/layout.tsx` com defaults (revalidateOnFocus: false, dedupingInterval: 5000)
- [ ] AC2: Criar `lib/fetcher.ts` com fetcher padrao que inclui auth headers e error handling
- [ ] AC3: Migrar `GET /v1/me` (user profile) para `useSWR` — substituir fetch manual em hooks/componentes
- [ ] AC4: Migrar `GET /v1/plans` (pricing) para `useSWR`
- [ ] AC5: Migrar `GET /v1/analytics/*` (dashboard) para `useSWR`
- [ ] AC6: Migrar `GET /v1/pipeline` para `useSWR`
- [ ] AC7: Migrar `GET /v1/sessions` (historico) para `useSWR`
- [ ] AC8: Migrar `GET /v1/trial-status` para `useSWR`

#### Fase B: Mutations + Complexos
- [ ] AC9: Configurar `useSWRMutation` para POST/PATCH/DELETE em pipeline (add, move, delete items)
- [ ] AC10: Configurar `useSWRMutation` para POST feedback
- [ ] AC11: Implementar optimistic updates para pipeline drag-and-drop
- [ ] AC12: Cache invalidation via `mutate()` apos mutations bem-sucedidas

#### Fase C: Remocao de Codigo Manual
- [ ] AC13: Remover useEffect-based fetch patterns substituidos pelo SWR (minimo 10 ocorrencias)
- [ ] AC14: Remover loading/error states manuais substituidos pelos de SWR
- [ ] AC15: `useFetchWithBackoff` mantido APENAS para endpoints que SWR nao cobre (ex: busca com SSE)

#### Validacao SWR
- [ ] AC16: Todos 2681+ frontend tests passam
- [ ] AC17: Network tab mostra request deduplication (mesma key nao faz 2 requests simultaneos)
- [ ] AC18: Revalidation on window focus desabilitado (per AC1)
- [ ] AC19: Error retry funciona (SWR default: 3 retries com backoff)

### Parte 2: Pipeline Refactor Foundation (TD-A02) — 24-32h

- [ ] AC20: Decompor `search_pipeline.py` em modulos:
  - `pipeline/orchestrator.py` — entry point, timeout management, result assembly (<200 lines)
  - `pipeline/source_fetcher.py` — parallel source fetching, per-source circuit breakers
  - `pipeline/consolidation.py` — dedup, merge, priority resolution (pode ser o existente `consolidation.py` renomeado)
  - `pipeline/filtering.py` — keyword matching, LLM classification, viability assessment chain
  - `pipeline/cache_manager.py` — SWR cache read/write, L1/L2 coordination
- [ ] AC21: Cada modulo < 300 linhas
- [ ] AC22: Interface publica de `search_pipeline.executar_pipeline()` permanece IDENTICA
- [ ] AC23: Timeout chain preservada: Pipeline(110s) > Consolidation(100s) > PerSource(80s) > PerUF(30s)
- [ ] AC24: SSE progress events emitidos nos mesmos pontos (nao mudar UX)
- [ ] AC25: Circuit breaker behavior inalterado

#### Validacao Pipeline
- [ ] AC26: Todos 5774+ backend tests passam (zero regressions)
- [ ] AC27: Busca E2E funciona: 3 fontes, SSE progress, resultados, filtros
- [ ] AC28: Metricas Prometheus inalteradas (mesmos nomes, mesmos labels)
- [ ] AC29: `mypy .` passa sem novos erros

## Technical Notes

### SWR Setup

**Global config:**
```typescript
// app/layout.tsx
import { SWRConfig } from 'swr';

<SWRConfig value={{
  fetcher: (url: string) => fetch(url).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  }),
  revalidateOnFocus: false,
  dedupingInterval: 5000,
  errorRetryCount: 3,
}}>
  {children}
</SWRConfig>
```

**Migration pattern (per endpoint):**
```typescript
// BEFORE (manual fetch)
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);
useEffect(() => {
  fetch('/api/me').then(r => r.json()).then(setData).catch(setError).finally(() => setLoading(false));
}, []);

// AFTER (SWR)
const { data, error, isLoading } = useSWR('/api/me');
```

**SWR does NOT replace useSearch for /buscar:** The search endpoint is POST + SSE, which SWR doesn't handle. `useSearch` (decomposed in TD-006) continues to manage the search lifecycle.

### Pipeline Refactor

**Module structure:**
```
backend/
  pipeline/
    __init__.py
    orchestrator.py      # executar_pipeline(), timeout mgmt
    source_fetcher.py    # fetch_all_sources(), per-source CB
    filtering.py         # apply_filters(), keyword + LLM chain
    cache_manager.py     # check_cache(), save_cache(), SWR logic
```

**Key constraint:** `search_pipeline.py` is imported by `routes/search.py` as `from search_pipeline import executar_pipeline`. The import path must remain valid (either keep the old file as re-export or update imports).

**Recommended approach:** Create `pipeline/` package, move logic incrementally, keep `search_pipeline.py` as thin re-export during transition:
```python
# search_pipeline.py (transition wrapper)
from pipeline.orchestrator import executar_pipeline  # re-export
```

## Dependencies

- **TD-006** (useSearch decomposition) DEVE estar completo antes da Parte 1 — SWR adoption works with the decomposed hooks, not the monolithic useSearch
- TD-007 (SearchResults decomp) pode rodar em paralelo
- Parte 2 (pipeline refactor) nao tem dependencias frontend — pode iniciar imediatamente

## Definition of Done
- [ ] SWR installed and configured globally
- [ ] 6+ GET endpoints migrated to useSWR
- [ ] Pipeline mutations using useSWRMutation
- [ ] Manual fetch/useEffect patterns removed (10+ occurrences)
- [ ] search_pipeline.py decomposed into 4-5 modules (<300 lines each)
- [ ] Public interface of executar_pipeline() unchanged
- [ ] All 5774+ backend tests passing
- [ ] All 2681+ frontend tests passing
- [ ] TypeScript and mypy pass
- [ ] E2E search flow functional
- [ ] Reviewed by @architect (pipeline design) and @dev (SWR patterns)
