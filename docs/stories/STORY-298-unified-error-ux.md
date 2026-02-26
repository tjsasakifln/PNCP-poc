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
- [ ] AC1: Estado mapeado para cada cenário:
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

- [ ] AC2: ZERO estados "limbo" — sempre há ação visível
- [ ] AC3: Toast notifications para eventos transitórios (reconexão, fonte timeout)
- [ ] AC4: Error boundary wrapper no `/buscar` com fallback gracioso

### Components
- [ ] AC5: `SearchStateManager` — componente que recebe estado da busca e renderiza UI apropriada
- [ ] AC6: Consolidar ErrorDetail, DegradationBanner, CacheBanner em fluxo único
- [ ] AC7: Micro-animações de transição entre estados (Framer Motion)
- [ ] AC8: Mobile responsive — todos os estados testados em 375px

### Quality
- [ ] AC9: Storybook (ou teste visual) para cada um dos 9 estados
- [ ] AC10: Teste: cada transição de estado renderiza componente correto
- [ ] AC11: Testes existentes passando

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

## Definition of Done

- [ ] Zero "limbo" states possíveis
- [ ] Cada cenário de erro tem ação clara para o usuário
- [ ] Mobile 375px: todos os estados visualmente corretos
- [ ] Todos os testes passando
- [ ] PR merged
