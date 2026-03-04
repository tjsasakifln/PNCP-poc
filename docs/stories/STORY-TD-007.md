# STORY-TD-007: SearchResults Decomposition

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Frontend
**Estimativa:** 14-18h (10-14h codigo + 4h testes)
**Prioridade:** P1
**Debt IDs:** FE-01

## Objetivo

Decompor o mega-componente `SearchResults.tsx` (1,581 linhas, ~55 props) em sub-componentes coesos. Este e o maior componente do sistema e o principal bloqueador de manutencao no frontend. Apos a decomposicao, o componente principal deve ter <300 linhas e servir apenas como layout orchestrator.

**Impacto direto:** Reduz tempo de compreensao de ~30min para ~5min. Desbloqueia modificacoes independentes (ex: mudar layout de resultados sem tocar em toolbar ou filtros).

## Acceptance Criteria

### Decomposicao em Sub-componentes
- [ ] AC1: Extrair `ResultCard` — card individual de licitacao (titulo, orgao, valor, UF, badges de relevancia, viability score, feedback buttons, acoes)
- [ ] AC2: Extrair `ResultsList` — lista/grid de ResultCards com virtualizacao e empty state
- [ ] AC3: Extrair `ResultsToolbar` — sort controls, view mode toggle (list/grid), items per page, export buttons
- [ ] AC4: Extrair `ResultsHeader` — total count, filter stats display, LLM source badges, sector info
- [ ] AC5: Extrair `ResultsPagination` — pagination controls com page numbers e navigation
- [ ] AC6: Extrair `ResultsFilters` — inline filter chips, active filters display, clear all
- [ ] AC7: `SearchResults.tsx` se torna layout orchestrator (<300 linhas) que compoe os sub-componentes

### Interface e Props
- [ ] AC8: Cada sub-componente recebe props do grupo correspondente definido em TD-005 (AC10):
  - `ResultCard` recebe item individual + actions subset
  - `ResultsList` recebe `data` + `display`
  - `ResultsToolbar` recebe `actions` + `display`
  - `ResultsHeader` recebe `data` + `llm`
- [ ] AC9: Nenhum prop drilling alem de 1 nivel (sub-componente nao passa props para sub-sub-componentes)
- [ ] AC10: Todos sub-componentes sao exportados de `app/buscar/components/` (co-localizados)

### Testes
- [ ] AC11: Cada sub-componente tem test suite proprio (minimo: render, key interactions, edge cases)
- [ ] AC12: Testes existentes de SearchResults adaptados para nova estrutura
- [ ] AC13: Snapshot tests criados ANTES da decomposicao como safety net (comparar output antes/depois)

### Validacao
- [ ] AC14: Todos 2681+ frontend tests passam (zero regressions)
- [ ] AC15: SearchResults.tsx < 300 linhas
- [ ] AC16: Cada sub-componente < 250 linhas
- [ ] AC17: TypeScript strict mode passa (`npx tsc --noEmit`)
- [ ] AC18: Visual output identico ao original (pixel comparison nas 3 view modes)
- [ ] AC19: Performance: nenhum aumento perceptivel no re-render count (React DevTools Profiler)
- [ ] AC20: Acessibilidade: keyboard navigation e screen reader behavior inalterados

## Technical Notes

**Decomposition approach (incremental, not big-bang):**
1. Criar snapshot tests do SearchResults atual (HTML output)
2. Extrair um sub-componente por vez
3. Rodar suite completa apos cada extracao
4. Comparar snapshot antes/depois

**Co-location pattern:**
```
app/buscar/components/
  search-results/
    SearchResults.tsx          # Orchestrator (<300 lines)
    ResultCard.tsx             # Individual result card
    ResultsList.tsx            # List/grid container
    ResultsToolbar.tsx         # Sort, view, export controls
    ResultsHeader.tsx          # Count, stats, badges
    ResultsPagination.tsx      # Page navigation
    ResultsFilters.tsx         # Active filter chips
    index.ts                   # Re-exports
    __tests__/
      ResultCard.test.tsx
      ResultsList.test.tsx
      ...
```

**Props flow (using TD-005 grouped types):**
```typescript
// SearchResults.tsx (orchestrator)
export function SearchResults({ data, filters, actions, display, llm, pipeline }: SearchResultsProps) {
  return (
    <div>
      <ResultsHeader data={data} llm={llm} />
      <ResultsToolbar actions={actions} display={display} />
      <ResultsFilters filters={filters} onClear={actions.onClearFilters} />
      <ResultsList data={data} display={display} actions={actions} pipeline={pipeline} />
      <ResultsPagination data={data} actions={actions} />
    </div>
  );
}
```

**Risco alto (268 testes afetados):** Muitos testes atuais renderizam SearchResults diretamente e verificam elementos internos. Apos decomposicao, esses testes podem quebrar se procuram elementos por data-testid ou text content que agora esta em sub-componentes. Estrategia: manter data-testids identicos nos sub-componentes.

## Dependencies

- **TD-005** (Button + prop grouping) DEVE estar completo — AC10-AC14 de TD-005 definem os typed prop groups usados aqui
- Pode rodar em paralelo com TD-006 (hooks sao independentes de componentes)

## Definition of Done
- [ ] SearchResults.tsx < 300 linhas (orchestrator)
- [ ] 6 sub-componentes extraidos e funcionais
- [ ] Cada sub-componente < 250 linhas
- [ ] Cada sub-componente tem test suite
- [ ] Snapshot comparison confirma output identico
- [ ] All 2681+ frontend tests passing
- [ ] Zero TypeScript errors
- [ ] Visual parity confirmada
- [ ] Keyboard nav + screen reader inalterados
- [ ] Reviewed by @ux-design-expert (visual) and @qa (tests)
