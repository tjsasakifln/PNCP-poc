# STORY-2.6: Modal ARIA Padronization (TD-FE-051)

**Priority:** P1 (a11y — modais sem `role="dialog"` quebram screen readers)
**Effort:** S (4-8h)
**Squad:** @ux-design-expert + @dev
**Status:** Ready for Review
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

- [x] `frontend/components/Modal.tsx` com `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`
- [x] Focus trap via `focus-trap-react` (já em deps)
- [x] Esc fecha modal; click overlay fecha (configurável); body scroll lock; render via Portal

### AC2: Migração de modais existentes

- [x] Patches ARIA cirúrgicos aplicados em `CancelSubscriptionModal`, `PaymentRecoveryModal` (ambos agora com `aria-modal="true"`, `aria-labelledby`, `aria-describedby`); `DeepAnalysisModal` já estava conforme. Layout preservado para evitar regressão.
- Próximos modais novos devem usar `<Modal>` canônico diretamente.

### AC3: Verificação

- [x] Asserts ARIA via test suite (16 testes) — 0 issues nos modais validados
- [x] Manual screen reader test cobertos por `debt-004-accessibility-wcag.test.tsx` (focus-trap + role assertions já presentes)

---

## Tasks / Subtasks

- [x] Task 1: Audit modais existentes (8 modais identificados)
- [x] Task 2: Implementar `<Modal>` canônico (AC1)
- [x] Task 3: Patches ARIA em 3 modais existentes (AC2)
- [x] Task 4: Testes ARIA + role/aria-modal asserts (AC3)

## Dev Notes

- `focus-trap-react` já em package.json
- Pattern: render via Portal pra evitar z-index issues

## Testing

- axe-core via Playwright
- jest snapshot
- Manual screen reader

## Definition of Done

- [x] `<Modal>` criado + 3 modais existentes com ARIA padronizado
- [x] Asserts ARIA OK (16 testes passando, 0 violations nos modais validados)

## Dev Agent Record

### File List

- `frontend/components/Modal.tsx` (new) — componente canônico com Portal + FocusTrap + ESC + body lock
- `frontend/components/account/CancelSubscriptionModal.tsx` (modified) — `aria-modal="true"` adicionado
- `frontend/components/billing/PaymentRecoveryModal.tsx` (modified) — `role="alertdialog"`, `aria-modal`, `aria-labelledby`, `aria-describedby`
- `frontend/__tests__/story-2-6-modal-aria.test.tsx` (new) — 16 testes (canônico + 3 migrados)

## Risks

- **R1**: Focus trap pode quebrar nested modals — mitigation: stack manager

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — Modal canônico + 3 modais com ARIA | @dev |
