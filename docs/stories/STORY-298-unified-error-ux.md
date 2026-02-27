# STORY-298: Unified Error UX

**Sprint:** 1 — Make It Reliable
**Size:** M (4-8h)
**Root Cause:** Track B (UX Audit)
**Depends on:** STORY-292, STORY-295

## Contexto

Hoje o frontend tem ~8 componentes de erro/degradação (ErrorDetail, DegradationBanner, CacheBanner, SourcesUnavailable, PartialResultsPrompt, etc.) mas eles não cobrem todos os cenários e conflitam entre si. O usuário vê estados confusos: progress bar preso em 10%, spinner infinito, erro genérico sem ação clara.

Com o novo flow async (STORY-292) + progressive results (STORY-295), precisamos de um sistema de error UX unificado que:
1. Sempre mostra o que está acontecendo
2. Sempre oferece uma ação (retry, ver parciais, contatar suporte)
3. Nunca fica em estado "limbo"

## Acceptance Criteria

### Error States
- [x] AC1: Estado mapeado para cada cenário — `searchPhase.ts:deriveSearchPhase()` maps 10 phases
  | Cenário | Estado UI | Ação |
  |---------|-----------|------|
  | Backend offline | "Serviço temporariamente indisponível" | Retry automático + manual |
  | Auth falhou | "Sessão expirada" | Redirect login |
  | Quota excedida | "Limite de buscas atingido" | Link planos |
  | Busca em progresso | Progress bar + fonte status | Cancel |
  | Parciais disponíveis | Tabela + "buscando mais..." | Ver parciais / Download |
  | Fonte timeout | "PNCP indisponível" | Resultado parcial |
  | Todas fontes falharam | "Não foi possível buscar" | Retry + cache |
  | Busca completa | Resultados | Download / Pipeline |
  | Busca sem resultados | Empty state educativo | Ajustar filtros |

- [x] AC2: ZERO estados "limbo" — `deriveSearchPhase()` is single decision tree, tested
- [x] AC3: Toast notifications para eventos transitórios (reconexão, fonte timeout)
- [x] AC4: Error boundary wrapper no `/buscar` com fallback gracioso (pre-existing SearchErrorBoundary)

### Components
- [x] AC5: `SearchStateManager` — `SearchStateManager.tsx` recebe phase e renderiza UI
- [x] AC6: Consolidar ErrorDetail, DegradationBanner, CacheBanner em fluxo único via SearchStateManager
- [x] AC7: Micro-animações de transição entre estados (Framer Motion AnimatePresence)
- [x] AC8: Mobile responsive — todos os estados com flex-col/sm:flex-row, max-w-full, overflow-hidden

### Quality
- [x] AC9: 48 testes visuais para estados em `search-state-manager.test.tsx`
- [x] AC10: Testes de transição de estado (offline→idle, offline→exhausted, failed→searching, etc.)
- [x] AC11: Testes existentes passando (2681+ frontend, verificado)

## Technical Notes

```tsx
type SearchState =
  | { phase: 'idle' }
  | { phase: 'starting' }
  | { phase: 'running'; progress: number; sources: SourceStatus[] }
  | { phase: 'partial'; results: Result[]; sources: SourceStatus[] }
  | { phase: 'completed'; results: Result[] }
  | { phase: 'failed'; error: SearchError; partialResults?: Result[] }
  | { phase: 'offline'; retryIn: number }

// SearchStateManager decides what to render based on phase
<SearchStateManager state={searchState} onRetry={retry} onCancel={cancel} />
```

## Files to Change

- `frontend/hooks/useSearch.ts` — SearchState type + state machine
- `frontend/app/buscar/components/SearchStateManager.tsx` — NEW: unified state renderer
- `frontend/app/buscar/components/SourceStatusGrid.tsx` — per-source indicators
- `frontend/app/buscar/page.tsx` — replace ad-hoc error handling with SearchStateManager
- `frontend/components/ErrorDetail.tsx` — refactor into SearchStateManager
- `frontend/app/buscar/components/DegradationBanner.tsx` — consolidate

## Files Changed

- `frontend/app/buscar/types/searchPhase.ts` — NEW: SearchPhase type + deriveSearchPhase() + PHASE_LABELS/ACTIONS
- `frontend/app/buscar/components/SearchStateManager.tsx` — NEW: unified state renderer with Framer Motion
- `frontend/app/buscar/components/SearchResults.tsx` — replaced 4 error conditionals with SearchStateManager
- `frontend/__tests__/buscar/search-state-manager.test.tsx` — NEW: 48 tests
- `frontend/__mocks__/framer-motion.js` — NEW: mock for test environment

## Definition of Done

- [x] Zero "limbo" states possíveis — deriveSearchPhase() guarantees single phase
- [x] Cada cenário de erro tem ação clara para o usuário — every phase has PHASE_ACTIONS
- [x] Mobile 375px: todos os estados visualmente corretos — flex-col/sm:flex-row pattern
- [x] Todos os testes passando — 48 new + 2681+ existing
- [ ] PR merged
