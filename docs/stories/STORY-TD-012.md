# STORY-TD-012: Search State Refactor -- Context + useReducer

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P2

## Estimativa
32h

## Descricao

Esta story elimina o prop drilling massivo na pagina de busca, substituindo a abordagem atual (42 props no SearchForm, 35 props no SearchResults, 528 linhas no useSearchFilters) por React Context + useReducer.

**Problema atual:**
- `SearchForm` recebe ~42 props via prop drilling (interface: 84 linhas, linhas 18-102)
- `SearchResults` recebe ~35 props (interface: 73 linhas, linhas 21-94)
- `useSearchFilters` tem 528 linhas com 40+ state variables -- impossivel testar/debugar
- Qualquer mudanca de filtro cascadeia por 4+ camadas de componentes

**Solucao: Cluster F do assessment**

1. **SearchContext (React Context + useReducer)** -- Criar contexto scoped a `/buscar` que encapsula todo o estado de busca. SearchForm e SearchResults acessam estado via `useSearchContext()` com 0 props.

2. **Split de useSearchFilters** -- Decompor o hook monolitico (528 linhas) em 4+ sub-hooks:
   - `useUFSelection` -- Estado de selecao de UFs
   - `useDateRange` -- Estado de range de datas
   - `useSectorFilter` -- Estado de filtro de setor
   - `useSearchExecution` -- Logica de execucao de busca

3. **Reducer puro e testavel** -- Estado gerenciado por reducer function que e uma pure function, testavel sem React.

**Impacto:** Elimina interfaces de 84 e 73 linhas. Cada sub-hook pode ser testado independentemente. Adicionar novo filtro nao requer mudanca em 4+ componentes.

## Itens de Debito Relacionados
- FE-01 (HIGH): SearchForm recebe ~42 props via prop drilling
- FE-02 (HIGH): SearchResults recebe ~35 props
- FE-03 (HIGH): `useSearchFilters` tem 528 linhas com 40+ state variables

## Criterios de Aceite

### Context
- [ ] `SearchContext` criado em `buscar/context/SearchContext.tsx`
- [ ] Provider wraps `/buscar` page (nao toda a app)
- [ ] `useSearchContext()` hook para consumir o contexto
- [ ] TypeScript types corretos para state e actions

### Reducer
- [ ] Reducer e pure function (sem side effects)
- [ ] Actions tipadas via discriminated union
- [ ] Reducer testavel sem React (import e chamar diretamente)
- [ ] Estado inicial documentado

### Componentes
- [ ] `SearchFormProps` interface removida (ou < 5 props)
- [ ] `SearchResultsProps` interface removida (ou < 5 props)
- [ ] SearchForm usa `useSearchContext()` diretamente
- [ ] SearchResults usa `useSearchContext()` diretamente
- [ ] Nenhum prop drilling de estado de busca

### Hooks
- [ ] `useSearchFilters.ts` < 100 linhas (orquestra sub-hooks)
- [ ] 4+ sub-hooks criados, cada um < 100 linhas
- [ ] Cada sub-hook independentemente testavel

### Funcionalidade
- [ ] Todos os filtros funcionam identicamente antes e depois
- [ ] Busca completa funciona identicamente
- [ ] Download de Excel funciona
- [ ] SSE progress funciona
- [ ] Saved searches funcionam
- [ ] E2E Playwright tests (de TD-011) passam

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| -- | Reducer: action SET_UF atualiza estado corretamente | Unitario (pure function) | P2 |
| -- | Reducer: action SEARCH_START atualiza loading state | Unitario | P2 |
| -- | useUFSelection: selecao/desselecao funciona | Unitario (hook test) | P2 |
| -- | E2E: fluxo completo de busca (de TD-011) | E2E | P2 |
| -- | TypeScript: `npx tsc --noEmit` passa | Type check | P2 |

## Dependencias
- **Blocks:** STORY-TD-013 (testes unitarios para nova arquitetura dependem dela existir)
- **Blocked by:** STORY-TD-011 (parcial -- E2E safety net deve existir antes do refactor)

## Riscos
- **CR-02:** Refactor de prop drilling QUEBRA testes existentes e pode causar regressoes visuais. E2E de TD-011 sao o safety net.
- Risco de introducao de bugs sutis na logica de estado. Reducer puro mitiga (testavel unitariamente).
- Risco de performance se Context re-renderizar demasiadamente. Usar `useMemo` e `useCallback` onde necessario.

## Rollback Plan
- Manter branch com implementacao antiga durante 2 semanas apos merge.
- Se E2E falharem apos merge: reverter e iterar.
- Feature flag possivel mas complexo para Context (nao recomendado).

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + E2E)
- [ ] CI/CD green
- [ ] TypeScript check clean (`npx tsc --noEmit`)
- [ ] Nenhuma regressao visual identificada
- [ ] Deploy em staging verificado
- [ ] Performance: pagina de busca carrega em < 2s (sem regressao)
