# DEBT-S1.3: Design System Foundation -- UI Primitives + Tokens
**Epic:** EPIC-DEBT
**Sprint:** 1
**Priority:** P1
**Estimated Hours:** 60h
**Assignee:** TBD

## Objetivo

Estabelecer a fundacao do design system: (1) mover AuthProvider para localizacao correta, (2) corrigir useIsMobile layout shift, (3) criar 5 componentes UI primitivos com Radix UI + CVA (Shadcn pattern), e (4) migrar ~1,754 ocorrencias de inline `var()` para Tailwind tokens. Esta story e o maior investimento do epic e desbloqueia FE-03 (buscar refactor) no Sprint 2.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| FE-34 | AuthProvider em localizacao incorreta. `app/components/AuthProvider.tsx` importado por `components/`. Causa circular imports (FE-26). | MEDIUM | 2h |
| FE-07 | useIsMobile initial false flash. `useState(false)` causa layout shift em mobile. | HIGH | 2h |
| FE-02 | Component library UI ausente. Faltam Card, Badge, Modal, Dialog, Select, Tabs, Tooltip. | HIGH | 24h |
| FE-01 | Inline `var()` ao inves de Tailwind tokens. ~1,754 ocorrencias. Codemod regex cobre ~80%. | HIGH | 32h |

## Acceptance Criteria

- [ ] AC1: AuthProvider movido para `contexts/AuthProvider.tsx` ou `components/AuthProvider.tsx` (fora de `app/components/`)
- [ ] AC2: Todos os 7 arquivos que importam AuthProvider atualizados com novo path
- [ ] AC3: Zero circular imports entre `components/` e `app/components/`
- [ ] AC4: useIsMobile usa `matchMedia` sincrono no initializer (sem flash de `false`)
- [ ] AC5: Lighthouse CLS < 0.1 em viewport mobile (375px)
- [ ] AC6: Componentes Card, Modal/Dialog, Badge, Select, Tabs criados em `components/ui/`
- [ ] AC7: Cada componente UI tem variantes via CVA (class-variance-authority)
- [ ] AC8: Cada componente UI tem testes unitarios
- [ ] AC9: `grep -r 'var(--' frontend/app/ | wc -l` retorna <50 (excecoes: gradient, glass, text-hero)
- [ ] AC10: Visual regression screenshots identicos pre/pos codemod (5 paginas-chave)

## Tasks

### Fase 1: Pre-requisitos (4h)
- [ ] T1: Mover AuthProvider para `contexts/AuthProvider.tsx`
- [ ] T2: Atualizar todos os imports de AuthProvider (7 arquivos)
- [ ] T3: Fix useIsMobile com `matchMedia` sincrono no `useState` initializer
- [ ] T4: Testar layout em mobile (375px) -- verificar CLS

### Fase 2: Component Library (24h)
- [ ] T5: Setup `components/ui/` com pattern Radix UI + CVA
- [ ] T6: Implementar Card (variantes: default, elevated, bordered, interactive)
- [ ] T7: Implementar Modal/Dialog (via Radix Dialog, com focus trap)
- [ ] T8: Implementar Badge (variantes: default, success, warning, error, info)
- [ ] T9: Implementar Select (via Radix Select, com search)
- [ ] T10: Implementar Tabs (via Radix Tabs, com keyboard navigation)
- [ ] T11: Escrever testes unitarios para cada componente
- [ ] T12: Documentar usage de cada componente (JSDoc ou README)

### Fase 3: Token Migration Codemod (32h)
- [ ] T13: Capturar visual regression screenshots de 5 paginas-chave (pre-codemod)
- [ ] T14: Criar codemod script para mapear `var(--X)` -> Tailwind tokens
- [ ] T15: Rodar codemod em modo dry-run e revisar output
- [ ] T16: Aplicar codemod (~80% automatico)
- [ ] T17: Corrigir ~20% edge cases manualmente (gradient, glass, text-hero ficam como `var()`)
- [ ] T18: Comparar screenshots pos-codemod com baseline
- [ ] T19: Rodar full frontend test suite

## Testes Requeridos

- [ ] AuthProvider imports resolvem corretamente (build + tests)
- [ ] useIsMobile: sem layout shift em 375px viewport
- [ ] Card, Modal, Badge, Select, Tabs: testes unitarios de render, variantes, a11y
- [ ] Modal: focus trap funciona (tab cycling)
- [ ] Select: keyboard navigation (arrow keys, enter, escape)
- [ ] Visual regression: screenshots pre/pos codemod identicos
- [ ] Frontend test count >= 5583
- [ ] `npm run build` sem erros

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **Ordem de execucao obrigatoria:** FE-34 -> FE-07 -> FE-02 -> FE-01. Cada fase depende da anterior.
- **FE-01 depende de FE-02:** Componentes novos ja usam tokens corretos, servem de referencia para codemod.
- **Tokens sem mapeamento Tailwind** (`--gradient-*`, `--glass-*`, `--text-hero`) ficam como `var()` -- nao e debt.
- **32h de FE-01:** 2h codemod script + 20h validacao + 10h edge cases manuais.
- Esta story desbloqueia: FE-03 (buscar refactor), FE-09 (component locations), FE-26 (circular imports).

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Frontend"
- AuthProvider: `frontend/app/components/AuthProvider.tsx`
- useIsMobile: `frontend/hooks/useIsMobile.ts`
- Components: `frontend/components/`
- Tailwind config: `frontend/tailwind.config.ts`
