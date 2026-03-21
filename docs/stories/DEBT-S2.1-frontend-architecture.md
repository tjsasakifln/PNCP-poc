# DEBT-S2.1: Frontend Architecture -- Components + Hooks Consolidation
**Epic:** EPIC-DEBT
**Sprint:** 2
**Priority:** P2
**Estimated Hours:** 65h
**Assignee:** TBD

## Objetivo

Refatorar a arquitetura frontend: simplificar a pagina Buscar (39 componentes + 9 hooks), unificar localizacao de componentes, resolver circular imports, padronizar error pages, e adicionar Storybook, Shepherd token compliance, SVG accessibility, e modal focus management.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| FE-03 | Complexidade da pagina Buscar. 39 componentes em `app/buscar/components/` + 9 hooks. | HIGH | 16h |
| FE-09 | Localizacao inconsistente de componentes. `components/`, `app/components/`, `app/buscar/components/` sem fronteira clara. | MEDIUM | 8h |
| FE-26 | Imports circulares potenciais. 7 arquivos em `components/` importam de `app/components/AuthProvider`. | MEDIUM | 4h |
| FE-04 | Error pages inconsistentes. Root usa inline var(), per-route usa Tailwind tokens. | MEDIUM | 3h |
| FE-06 | Dual footer. Buscar footer tem funcionalidades contextuais. Unificar visualmente com variantes. | MEDIUM | 4h |
| FE-12 | Pages sem PageErrorBoundary sub-page. Faltam boundaries em componentes internos. | MEDIUM | 3h |
| FE-14 | Feature-gated pages roteáveis. `/alertas` e `/mensagens` acessiveis via URL direta. | MEDIUM | 2h |
| FE-16 | Sem Storybook. ROI cresce apos component library (FE-02). | MEDIUM | 16h |
| FE-18 | Shepherd.js usa Tailwind raw. 15+ usos que NAO respeitam design tokens. Dark mode inconsistente. | MEDIUM | 2h |
| FE-20 | SVGs sem `aria-hidden`. Lacuna em SVGs inline menores. | MEDIUM | 3h |
| FE-21 | Focus nao retorna apos modal close. BuscarModals, InviteMemberModal, CancelSubscriptionModal. | MEDIUM | 4h |

## Acceptance Criteria

- [ ] AC1: Pagina Buscar refatorada com <25 componentes diretos (extrair sub-composites)
- [ ] AC2: Hooks de buscar consolidados (max 5 hooks com responsabilidades claras)
- [ ] AC3: Fronteira clara entre `components/` (shared), `app/components/` (layout), `app/buscar/components/` (page-specific)
- [ ] AC4: Zero imports circulares entre `components/` e `app/components/`
- [ ] AC5: Todos error.tsx usam Tailwind tokens consistentemente (exceto root que usa inline by design)
- [ ] AC6: Footer unificado com variante contextual para Buscar (single component, multiple variants)
- [ ] AC7: PageErrorBoundary adicionado em componentes internos criticos (buscar, pipeline, dashboard)
- [ ] AC8: Feature-gated pages (`/alertas`, `/mensagens`) retornam 404 ou redirect quando feature flag desabilitada
- [ ] AC9: Storybook configurado com stories para todos componentes de `components/ui/`
- [ ] AC10: Shepherd.js tour usa design tokens (nao `bg-white`, `text-gray-700` raw)
- [ ] AC11: Todos SVGs inline tem `aria-hidden="true"` quando decorativos
- [ ] AC12: Focus retorna ao trigger element apos fechar modal (BuscarModals, InviteMember, CancelSubscription)

## Tasks

### Fase 1: Structure (12h)
- [ ] T1: Definir convencao de pastas (`components/` vs `app/components/` vs page-specific)
- [ ] T2: Mover componentes para localizacao correta conforme convencao
- [ ] T3: Resolver imports circulares (depende de FE-34 feito no Sprint 1)
- [ ] T4: Atualizar todos os imports afetados

### Fase 2: Buscar Refactor (16h)
- [ ] T5: Identificar componentes que podem ser agrupados em composites
- [ ] T6: Extrair sub-composites (ex: SearchFilters, SearchResultsPanel, ProgressSection)
- [ ] T7: Consolidar hooks (ex: useSearchState, useSearchProgress, useSearchResults)
- [ ] T8: Atualizar testes da pagina buscar

### Fase 3: Error Pages + Footer (10h)
- [ ] T9: Padronizar error.tsx com Tailwind tokens (manter root inline by design)
- [ ] T10: Criar Footer com variantes (default, buscar) via props
- [ ] T11: Adicionar PageErrorBoundary em paginas criticas

### Fase 4: Feature Gates + Accessibility (9h)
- [ ] T12: Implementar gate para `/alertas` e `/mensagens` (404 quando flag off)
- [ ] T13: Atualizar Shepherd.js tour config para usar design tokens
- [ ] T14: Adicionar `aria-hidden="true"` em SVGs decorativos
- [ ] T15: Implementar focus return em modais (useRef + onClose callback)

### Fase 5: Storybook (16h)
- [ ] T16: Configurar Storybook com Next.js + Tailwind
- [ ] T17: Criar stories para Card, Modal, Badge, Select, Tabs (de FE-02)
- [ ] T18: Criar stories para componentes existentes (SearchForm, PlanCard, etc.)
- [ ] T19: Configurar Storybook CI (optional: deploy para Chromatic)

## Testes Requeridos

- [ ] Frontend test count >= 5583 (nenhum teste removido)
- [ ] `npm run build` sem erros
- [ ] Pagina buscar funciona end-to-end (E2E)
- [ ] Modais retornam focus ao trigger element
- [ ] Feature-gated pages retornam 404 quando flag off
- [ ] Storybook build passa sem erros
- [ ] a11y: axe-core 0 critical violations (manter baseline)

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **Depende de DEBT-S1.3:** FE-34 (AuthProvider move), FE-02 (component library) devem estar completos.
- **FE-03 e a maior tarefa individual (16h)** -- considerar split em sub-PRs.
- **FE-16 (Storybook):** ROI cresce significativamente com component library do Sprint 1.
- **FE-26 circular imports:** Com FE-34 resolvido no Sprint 1, a maioria dos circular imports desaparece. Revalidar antes de comecar.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Frontend"
- Buscar page: `frontend/app/buscar/page.tsx`
- Buscar components: `frontend/app/buscar/components/`
- Shared components: `frontend/components/`
- Error pages: `frontend/app/*/error.tsx`
