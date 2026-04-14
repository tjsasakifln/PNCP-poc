# STORY-4.3: ESLint no-arbitrary-values + Hex Cleanup (TD-FE-004)

**Priority:** P1 (design system bypass — 194 hex hardcoded)
**Effort:** S-M (8-16h)
**Squad:** @ux-design-expert + @dev
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** ESLint blocando inline hex colors + 194 existentes migrados para tokens,
**so that** design system seja consistent + dark mode funcione automaticamente.

---

## Acceptance Criteria

### AC1: ESLint rule

- [ ] `eslint-plugin-tailwindcss` ou custom rule blocks `bg-[#xxx]`, `text-[#xxx]`, `style={{ color: '#xxx' }}`
- [ ] CI fail em PR com violation
- [ ] Allow exceptions com `// eslint-disable-next-line` + reason

### AC2: Migration

- [ ] Audit + map 194 hex → token equivalent
- [ ] Substituir com `bg-primary`, `text-success`, etc.
- [ ] Cases sem token equivalent: adicionar token novo em `tailwind.config.ts`

### AC3: Visual regression

- [ ] Percy diff <1% pós-migration

---

## Tasks / Subtasks

- [ ] Task 1: ESLint rule setup (AC1)
- [ ] Task 2: Audit hex usage
- [ ] Task 3: Map hex → token (algumas additions ao config)
- [ ] Task 4: Migration (codemod ou manual)
- [ ] Task 5: Visual regression (AC3)

## Dev Notes

- 194 matches `#[0-9a-fA-F]{6}` em frontend
- Tailwind config tem 50+ tokens já

## Testing

- ESLint passes
- Percy visual regression

## Definition of Done

- [ ] Rule active + 194 migrated + Percy <1%

## Risks

- **R1**: Token additions visualmente diferentes — mitigation: review com @ux

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
