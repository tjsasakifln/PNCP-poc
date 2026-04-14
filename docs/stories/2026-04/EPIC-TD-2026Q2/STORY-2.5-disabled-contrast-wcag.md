# STORY-2.5: Disabled State Contrast WCAG AA (TD-FE-050)

**Priority:** P1 (a11y — baixa visão tem dificuldade em forms disabled)
**Effort:** XS (2-4h)
**Squad:** @ux-design-expert + @dev
**Status:** Draft
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

- [ ] `tailwind.config.ts` adiciona color token com contraste verificado
- [ ] Light mode + dark mode variants

### AC2: Migração

- [ ] `<Button disabled>`, `<Input disabled>`, `<Select disabled>` usam o novo token (não `opacity-50`)
- [ ] Audit + fix de outros disabled states em forms

### AC3: Verificação automatizada

- [ ] axe-core scan em `/conta`, `/buscar` (forms) — 0 violations contraste
- [ ] Lighthouse Accessibility >= 95

---

## Tasks / Subtasks

- [ ] Task 1: Definir tokens disabled-text light/dark (AC1)
- [ ] Task 2: Verificar contraste com WebAIM tool
- [ ] Task 3: Migrar Button + Input + Select (AC2)
- [ ] Task 4: Audit outros (AC2)
- [ ] Task 5: axe-core + Lighthouse validation (AC3)

## Dev Notes

- WCAG AA text: 4.5:1; Large text 3:1
- Atual `opacity-50` cai para ~3.2:1 em alguns casos

## Testing

- axe-core via Playwright
- Lighthouse CI

## Definition of Done

- [ ] Token novo + migrações + 0 violations

## Risks

- **R1**: Visual designer pode rejeitar contraste maior por estética — mitigation: WCAG é compliance, prevalece

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
