# STORY-2.2: Codemod `<button>` → `<Button>` (TD-FE-005)

**Priority:** P1 (design system coherence; ARIA labels everywhere)
**Effort:** S (8h)
**Squad:** @ux-design-expert (lead) + @dev (executor) + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** dev SmartLic,
**I want** todos os ~390 botões nativos `<button>` migrados para o componente CVA `<Button>`,
**so that** design system seja consistente, ARIA labels obrigatórios, e variants centralizadas.

---

## Acceptance Criteria

### AC1: Codemod executado

- [ ] Script jscodeshift / ts-morph migra `<button className="...">` → `<Button variant="..." size="...">`
- [ ] Mapping de classes Tailwind → variant inferido por padrões comuns
- [ ] Cases ambíguos marcados com TODO comment (não auto-migrate)

### AC2: ESLint rule preventing regression

- [ ] Custom ESLint rule ou `eslint-plugin-react` config blocks `<button>` em `frontend/`
- [ ] Allow exceptions com `// eslint-disable-next-line` + reason

### AC3: Visual regression OK

- [ ] Percy diff <1% em rotas /buscar, /pipeline, /dashboard, /conta

### AC4: Tests pass

- [ ] Existing 2681+ jest pass
- [ ] Existing 60 Playwright pass

---

## Tasks / Subtasks

- [ ] Task 1: Audit current `<Button>` API e variants (AC1)
- [ ] Task 2: Write codemod script
- [ ] Task 3: Run codemod + manual review TODOs (AC1)
- [ ] Task 4: ESLint rule setup (AC2)
- [ ] Task 5: Visual regression validation (AC3)
- [ ] Task 6: Test suite run (AC4)

## Dev Notes

- `<Button>` em `frontend/components/Button.tsx` (CVA-based, canonical)
- ~629 button instances; 62% nativos = ~390 to migrate
- Codemod tools: jscodeshift (preferred for React), ts-morph

## Testing

- jest existing
- Percy visual regression
- Playwright E2E

## Definition of Done

- [ ] All native `<button>` migrated (or marked TODO)
- [ ] ESLint rule active
- [ ] Visual regression <1%
- [ ] All tests pass

## Risks

- **R1**: Variant mapping incorreto → mitigation: codemod conservative + manual review
- **R2**: Some buttons need custom styling not in CVA variants → mitigation: extend Button variants

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
