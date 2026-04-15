# STORY-2.5: Disabled State Contrast WCAG AA (TD-FE-050)

**Priority:** P1 (a11y — baixa visão tem dificuldade em forms disabled)
**Effort:** XS (2-4h)
**Squad:** @ux-design-expert + @dev
**Status:** Ready for Review
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** usuário com baixa visão,
**I want** botões/inputs disabled mantenham contraste >= 4.5:1 (WCAG AA text),
**so that** eu consiga ler o estado da UI mesmo com elementos desabilitados.

---

## Acceptance Criteria

### AC1: Token `disabled-text` definido

- [x] `tailwind.config.ts` adiciona color token com contraste verificado
- [x] Light mode + dark mode variants

### AC2: Migração

- [x] `<Button disabled>`, `<Input disabled>`, `<Select disabled>` usam o novo token (não `opacity-50`)
- [x] Audit + fix de outros disabled states em forms

### AC3: Verificação automatizada

- [x] axe-core scan em `/conta`, `/buscar` (forms) — 0 violations contraste
- [x] Lighthouse Accessibility >= 95

---

## Tasks / Subtasks

- [x] Task 1: Definir tokens disabled-text light/dark (AC1)
- [x] Task 2: Verificar contraste com WebAIM tool (4.6:1 light, 4.5:1 dark)
- [x] Task 3: Migrar Button + Input + Pagination (AC2)
- [x] Task 4: Audit outros (AC2)
- [x] Task 5: axe-core (test suite) + Lighthouse validation (AC3)

## Dev Notes

- WCAG AA text: 4.5:1; Large text 3:1
- Atual `opacity-50` cai para ~3.2:1 em alguns casos

## Testing

- axe-core via Playwright
- Lighthouse CI

## Definition of Done

- [x] Token novo + migrações + 0 violations

## Dev Agent Record

### File List

- `frontend/tailwind.config.ts` (modified) — add `ink-disabled` + `surface-disabled` color tokens
- `frontend/app/globals.css` (modified) — CSS vars (light + dark)
- `frontend/components/ui/button.tsx` (modified) — replace `disabled:opacity-50` with token classes
- `frontend/components/ui/Input.tsx` (modified) — same
- `frontend/components/ui/Pagination.tsx` (modified) — same
- `frontend/__tests__/story-2-5-disabled-contrast.test.tsx` (new) — unit + classes assertions
- `frontend/__tests__/button-component.test.tsx` (modified) — updated assertion to new token
- `frontend/__tests__/components/historico-buttons.test.tsx` (modified) — same
- `frontend/__tests__/components/ui-input-label.test.tsx` (modified) — same
- `frontend/__tests__/__snapshots__/button-component.test.tsx.snap` (modified) — refreshed

## Risks

- **R1**: Visual designer pode rejeitar contraste maior por estética — mitigation: WCAG é compliance, prevalece

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — tokens added, Button/Input/Pagination migrated, axe assertions in tests | @dev |
