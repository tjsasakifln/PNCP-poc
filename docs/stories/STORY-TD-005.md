# STORY-TD-005: Frontend Design System Foundation (Button + Prop Grouping)

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Frontend
**Estimativa:** 10-14h (8-10h codigo + 2-4h testes)
**Prioridade:** P1
**Debt IDs:** FE-27 (= FE-06), FE-10

## Objetivo

Estabelecer a base do design system frontend com dois trabalhos fundamentais: (1) criar um componente Button compartilhado via Shadcn/ui que substitui os 50+ botoes ad-hoc espalhados pelas 22 paginas, e (2) agrupar as 55 props de SearchResults.tsx em 6-8 typed objects para reduzir prop drilling e preparar a decomposicao (TD-007).

**Por que agora:** FE-27 (Button) e FE-10 (prop grouping) sao pre-requisitos obrigatorios de TD-007 (SearchResults decomposition). Sem eles, a decomposicao seria fragil e exigiria retrabalho.

## Acceptance Criteria

### Button Component via Shadcn/ui (FE-27) — 4-6h
- [ ] AC1: Inicializar Shadcn/ui no projeto (`npx shadcn-ui@latest init`) com configuracao compativel ao tailwind.config.ts existente
- [ ] AC2: Instalar componente Button via `npx shadcn-ui@latest add button`
- [ ] AC3: Criar variantes customizadas SmartLic: `primary` (azul brand), `secondary`, `destructive`, `ghost`, `link`, `outline`
- [ ] AC4: Cada variante tem tamanhos: `sm`, `default`, `lg`, `icon`
- [ ] AC5: Button suporta `loading` state (spinner + texto, disabled enquanto loading)
- [ ] AC6: Button suporta `asChild` para composicao com `Link` do Next.js
- [ ] AC7: Substituir botoes em pelo menos 5 paginas criticas: `/buscar`, `/login`, `/signup`, `/planos`, `/pipeline`
- [ ] AC8: `npm run build` passa sem erros apos setup do Shadcn/ui (verificar tailwind.config nao quebrou)
- [ ] AC9: Visual regression check em todas as paginas modificadas (screenshot antes/depois)

### Prop Grouping SearchResults (FE-10) — 6-8h
- [ ] AC10: Definir interfaces TypeScript para agrupamento das 55 props em ~6-8 typed objects:
  ```typescript
  interface SearchResultsProps {
    data: SearchResultsData;        // results, totalCount, filterStats, etc.
    filters: SearchFilters;         // selectedUFs, valueRange, sector, etc.
    actions: SearchResultsActions;  // onFilter, onSort, onExport, etc.
    display: SearchResultsDisplay;  // viewMode, isLoading, error, etc.
    llm: LLMState;                  // summary, llmReady, summaryLoading, etc.
    pipeline: PipelineActions;      // onAddToPipeline, pipelineItems, etc.
  }
  ```
- [ ] AC11: SearchResults.tsx aceita novo formato de props (manter backward compat temporariamente se necessario)
- [ ] AC12: buscar/page.tsx atualizado para passar props agrupadas
- [ ] AC13: Todas as 55 props originais estao mapeadas em pelo menos um grupo (nenhuma perdida)
- [ ] AC14: TypeScript strict mode passa sem erros (`npx tsc --noEmit`)

### Validacao
- [ ] AC15: Todos 2681+ frontend tests passam
- [ ] AC16: Zero TypeScript errors
- [ ] AC17: `npm run lint` passa
- [ ] AC18: Build de producao (`npm run build`) sucesso

## Technical Notes

**Shadcn/ui init considerations:**
- Shadcn/ui modifica `tailwind.config.ts` (adiciona `cssVariables`, `darkMode`, paths). Backup antes.
- Requer `components.json` na raiz do frontend.
- Components gerados em `components/ui/` — nao sao dependencias externas, sao codigo proprio.
- Next.js 16 + React 18 compativel (verificar versao do Shadcn/ui para compatibilidade).

**Prop grouping strategy:**
1. Agrupar por dominio (data, filters, actions, display, llm, pipeline)
2. Cada interface em arquivo proprio: `types/search-results.ts`
3. Usar `Pick<>` e `Omit<>` para derivar sub-types se necessario
4. Manter spread operator nos sub-componentes para minimizar mudancas internas

**Risco Shadcn/ui + Tailwind:**
- Shadcn/ui usa CSS variables para theming — pode conflitar com classes Tailwind hardcoded existentes
- Testar em dark mode apos setup (projeto ja tem dark mode via WCAG fix UX-410)

## Dependencies

- Nenhuma — pode iniciar imediatamente
- BLOQUEIA: TD-007 (SearchResults decomposition) depende de AC10-AC14

## Definition of Done
- [ ] Shadcn/ui inicializado e Button component disponivel
- [ ] Button usado em 5+ paginas criticas
- [ ] 55 props agrupadas em 6-8 typed objects
- [ ] Zero TypeScript errors
- [ ] All frontend tests passing (2681+)
- [ ] Build de producao sucesso
- [ ] Visual check em paginas modificadas
- [ ] Reviewed by @ux-design-expert
