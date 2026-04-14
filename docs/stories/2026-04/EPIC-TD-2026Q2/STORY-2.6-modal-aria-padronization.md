# STORY-2.6: Modal ARIA Padronization (TD-FE-051)

**Priority:** P1 (a11y — modais sem `role="dialog"` quebram screen readers)
**Effort:** S (4-8h)
**Squad:** @ux-design-expert + @dev
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** usuário de screen reader,
**I want** modais SmartLic sejam anunciados como "diálogo" e foco trapado dentro,
**so that** eu navegue forms modais sem perder contexto.

---

## Acceptance Criteria

### AC1: Componente `<Modal>` canônico

- [ ] `frontend/components/Modal.tsx` com `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`
- [ ] Focus trap via `focus-trap-react` (já em deps)
- [ ] Esc fecha modal; click overlay fecha (configurable)

### AC2: Migração de modais existentes

- [ ] `CancelSubscriptionModal`, `ViabilityReasonsModal`, qualquer outro modal divs ad-hoc → usar `<Modal>`

### AC3: Verificação

- [ ] axe-core em rotas com modais — 0 violations
- [ ] Manual screen reader test (NVDA/VoiceOver)

---

## Tasks / Subtasks

- [ ] Task 1: Audit modais existentes
- [ ] Task 2: Implementar `<Modal>` canônico (AC1)
- [ ] Task 3: Migrar 3-5 modais (AC2)
- [ ] Task 4: axe + manual tests (AC3)

## Dev Notes

- `focus-trap-react` já em package.json
- Pattern: render via Portal pra evitar z-index issues

## Testing

- axe-core via Playwright
- jest snapshot
- Manual screen reader

## Definition of Done

- [ ] `<Modal>` criado + 3+ migrações
- [ ] axe 0 violations

## Risks

- **R1**: Focus trap pode quebrar nested modals — mitigation: stack manager

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
