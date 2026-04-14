# STORY-4.2: Shepherd.js A11y Replacement (TD-FE-002)

**Priority:** P1 (a11y critical — screen readers não parseiam Shepherd HTML)
**Effort:** M (16-24h)
**Squad:** @ux-design-expert + @dev + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** usuário com screen reader fazendo onboarding,
**I want** os tour steps anunciados corretamente com ARIA,
**so that** eu complete onboarding sem barreiras de acessibilidade.

---

## Acceptance Criteria

### AC1: Substituir Shepherd.js

- [ ] Avaliar opções: react-joyride, intro.js, custom React solution
- [ ] Recomendação: custom solution com Tippy.js ou Floating UI (mais controle ARIA)

### AC2: Tour component com ARIA

- [ ] `<TourStep>` component:
  - `role="dialog"` ou `role="region"` apropriado
  - `aria-live="polite"` para step transitions
  - `aria-labelledby`, `aria-describedby`
  - Focus trap dentro do step

### AC3: Migration

- [ ] Substituir Shepherd em `/onboarding`
- [ ] Substituir em outras pages que usam tour (audit primeiro)

### AC4: Verification

- [ ] axe-core: 0 violations durante tour
- [ ] Manual screen reader test (NVDA/VoiceOver)

### AC5: Dismiss permanente

- [ ] Botão "Não mostrar novamente" → localStorage flag (resolve TD-FE-017 também)

---

## Tasks / Subtasks

- [ ] Task 1: Audit Shepherd usage atual
- [ ] Task 2: Tool selection
- [ ] Task 3: Implementar `<Tour>` + `<TourStep>` (AC2)
- [ ] Task 4: Migrar /onboarding (AC3)
- [ ] Task 5: Persistent dismiss (AC5)
- [ ] Task 6: axe + manual screen reader (AC4)
- [ ] Task 7: Remove `shepherd.js` da `package.json`

## Dev Notes

- Bundle save: ~30KB removendo Shepherd
- Pattern reference: react-joyride, intro.js
- Resolve TD-FE-017 (tour não dismissível) também

## Testing

- axe-core via Playwright
- Manual screen reader
- E2E onboarding flow

## Definition of Done

- [ ] Shepherd removido + custom solution + a11y validated + dismiss persistente

## Risks

- **R1**: Custom solution mais code para manter — mitigation: start com lib (react-joyride) se aceitar dependência

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
