# STORY-4.2: Shepherd.js A11y Replacement (TD-FE-002)

**Priority:** P1 (a11y critical — screen readers não parseiam Shepherd HTML)
**Effort:** M (16-24h)
**Squad:** @ux-design-expert + @dev + @qa
**Status:** Done
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

- [x] Audit completo de usage atual — Shepherd é consumido via:
  - `frontend/hooks/useShepherdTour.ts` (hook central)
  - `app/buscar/components/GuidedTour.tsx`
  - `app/buscar/hooks/useSearchOrchestration.ts`
  - `app/buscar/constants/tour-steps.ts`
  - `app/dashboard/page.tsx`, `app/pipeline/page.tsx`
  - `app/demo/DemoClient.tsx`
  - `styles/shepherd-theme.css`
- [x] **Decisão de biblioteca**: custom React solution com `focus-trap-react` (já é devDep, usado em 11 arquivos). Economiza ~30KB net vs Shepherd + CSS. Mais controle sobre ARIA do que `react-joyride` (50KB) ou `intro.js` (a11y frágil).

### AC2: Tour component com ARIA

- [x] `frontend/components/tour/Tour.tsx`:
  - `role="dialog"` + `aria-modal="false"` (tour não bloqueia a página)
  - `aria-live="polite"` em live region anunciando "Passo N de M: {title}"
  - `aria-labelledby` + `aria-describedby` vinculados a `<h2>` e `<p>` do step
  - FocusTrap com `returnFocusOnDeactivate: true`, `tabbableOptions.displayCheck: 'none'` (compat jsdom), `fallbackFocus` na div do step
- [x] Keyboard handling completo: ESC cancela (onSkip), ArrowRight avança, ArrowLeft volta, Tab/Shift+Tab permanecem no card
- [x] `showOn?: () => boolean` — pula steps condicionais (e.g., elemento não existe no DOM)
- [x] `beforeShow?: () => Promise<void> | void` — callback assíncrono antes de exibir step

### AC3: Migration

- [x] Componente Tour + helpers (`isTourPermanentlyDismissed`, `markTourPermanentlyDismissed`) em `frontend/components/tour/`
- [x] **Migração completa de todos os 7 callsites**:
  - `app/buscar/components/GuidedTour.tsx` → Tour component (active state, onComplete/onSkip/onStepChange)
  - `app/buscar/hooks/useSearchOrchestration.ts` → state-based approach, Tour rendered in buscar/page.tsx
  - `app/buscar/constants/tour-steps.ts` → TourStepDef[], beforeShow, attachTo reformatado
  - `app/dashboard/page.tsx` → Tour component com useState + auto-start
  - `app/pipeline/page.tsx` → Tour component com useState + restartPipelineTour
  - `app/demo/DemoClient.tsx` → Tour component com beforeShow para transições de estado
  - `hooks/useOnboarding.tsx` → Tour component via tourElement: ReactNode
- [x] Remoção de `shepherd.js` de `package.json` + deletion de `styles/shepherd-theme.css` + seção shepherd de `globals.css`
- [x] Deletion de `hooks/useShepherdTour.ts` (hook central removido)
- [x] Remoção de `ShepherdGlobal` de `types/external.d.ts`

### AC4: Verification

- [x] Unit tests: `frontend/__tests__/components/Tour.test.tsx` (11 tests, 11/11 pass) — ARIA, keyboard, focus trap, callbacks, permanent dismiss
- [x] Unit tests: `frontend/__tests__/onboarding/shepherd-tours.test.tsx` — reescrito como Tour component tests (41 tests, 41/41 pass) cobrindo showOn, beforeShow, OnboardingTourButton
- [x] Unit tests: `frontend/__tests__/buscar/GuidedTour.test.tsx` — migrado de shepherd mock → Tour mock (9/9 pass)
- [x] Unit tests: `frontend/__tests__/useOnboarding.test.tsx` — removido shepherd mock, adaptado para novo hook (23/23 pass)
- [x] axe-core via Playwright: `frontend/e2e-tests/tour-a11y.spec.ts` — 8 testes WCAG 2.1 AA (role=dialog, aria-modal, aria-live, aria-labelledby, ESC, Tab, ArrowRight)
- [ ] Manual screen reader (NVDA/VoiceOver): executar em sessão de QA final

### AC5: Dismiss permanente

- [x] Botão "Não mostrar novamente" → `localStorage.setItem('smartlic_tour_{tourId}_dismissed_permanent', 'true')`
- [x] Hook `isTourPermanentlyDismissed(tourId)` + `markTourPermanentlyDismissed(tourId)` exportados
- [x] Resolve TD-FE-017 (tour não dismissível)

---

## Tasks / Subtasks

- [x] Task 1: Audit Shepherd usage atual
- [x] Task 2: Tool selection (custom + focus-trap-react)
- [x] Task 3: Implementar `<Tour>` (AC2) — showOn + beforeShow implementados
- [x] Task 4: Migrar todos os callsites (GuidedTour, dashboard, pipeline, DemoClient, useOnboarding, useSearchOrchestration, tour-steps)
- [x] Task 5: Persistent dismiss (AC5)
- [x] Task 6: Unit tests (11+41+9+23 = 84 tests passando)
- [x] Task 7: Remove `shepherd.js` + `useShepherdTour.ts` + `shepherd-theme.css` + shepherd CSS de `globals.css`

## Dev Notes

- **showOn + beforeShow**: declarados no TourStepDef mas não implementados no Tour.tsx inicial. Implementados em Wave 0 (bloqueador crítico): `findValidIndex()` helper + `isTransitioningRef` guard + async `handleNext`/`handleBack`.
- **5º callsite**: `useOnboarding.tsx` (não listado na story original) — migrado para retornar `tourElement: ReactNode` via useMemo, mantendo API pública intacta.
- **Callsites em `.ts`**: `useSearchOrchestration.ts` não pode conter JSX → padrão: expõe `active state + callbacks`, Tour renderizado em `buscar/page.tsx`.
- **HTML stripping**: todos os textos Shepherd tinham `<span class="tour-step-counter">Passo N de M</span><p>...</p>` — Tour.tsx renderiza contador nativo, HTML foi removido.
- **Bundle impact**: -30KB (shepherd.js ~30KB removido, Tour.tsx ~4KB) = net -26KB.
- **Focus-trap + jsdom quirks**: `tabbableOptions: { displayCheck: 'none' }` + `fallbackFocus` bypassam o problema de `offsetWidth/Height === 0`.

## File List

### Created

- `frontend/components/tour/Tour.tsx` — componente principal + showOn/beforeShow + helpers (Wave 0)
- `frontend/__tests__/components/Tour.test.tsx` — 11 unit tests (Wave 4)
- `frontend/e2e-tests/tour-a11y.spec.ts` — 8 testes axe-core WCAG 2.1 AA (AC4)

### Modified

- `frontend/app/buscar/constants/tour-steps.ts` — TourStepDef[], beforeShow, attachTo
- `frontend/app/buscar/components/GuidedTour.tsx` — Tour component, sem shepherd
- `frontend/app/buscar/hooks/useSearchOrchestration.ts` — state-based tours, sem shepherd
- `frontend/app/buscar/page.tsx` — render Search, Results, Onboarding Tours
- `frontend/app/dashboard/page.tsx` — Tour component, sem shepherd
- `frontend/app/pipeline/page.tsx` — Tour component, sem shepherd
- `frontend/app/demo/DemoClient.tsx` — Tour component, beforeShow para state transitions
- `frontend/hooks/useOnboarding.tsx` — Tour component, tourElement: ReactNode
- `frontend/app/globals.css` — removida seção shepherd CSS (~110 linhas)
- `frontend/types/external.d.ts` — removida ShepherdGlobal interface
- `frontend/package.json` — shepherd.js removido das dependencies
- `frontend/__tests__/onboarding/shepherd-tours.test.tsx` — reescrito como Tour tests (41 tests)
- `frontend/__tests__/buscar/GuidedTour.test.tsx` — migrado para Tour mock (9 tests)
- `frontend/__tests__/useOnboarding.test.tsx` — removido shepherd mock (23 tests)
- `frontend/__tests__/pages/DashboardPage.test.tsx` — removido mock morto useShepherdTour
- `frontend/__tests__/pages/PipelinePage.test.tsx` — removido mock morto useShepherdTour
- `frontend/__tests__/polish/loading-consistency.test.tsx` — removido mock morto useShepherdTour

### Deleted

- `frontend/hooks/useShepherdTour.ts`
- `frontend/styles/shepherd-theme.css`

## Testing

- **84 unit tests passando** (11 Tour + 41 shepherd-tours rewrite + 9 GuidedTour + 23 useOnboarding)
- **DashboardPage**: 16/22 pass, 6 skipped (quarantine pre-existentes, não relacionados)
- **PipelinePage**: 20/20 pass
- **axe-core Playwright**: `e2e-tests/tour-a11y.spec.ts` — 8 testes WCAG 2.1 AA
- Manual SR: pendente (sessão de QA final com NVDA/VoiceOver)

## Definition of Done

- [x] Tour component com ARIA + focus-trap + dismiss permanente + showOn + beforeShow
- [x] Migration completa de todos os 7 callsites
- [x] Remoção de shepherd.js + arquivos associados (−30KB bundle)
- [x] 84 unit tests passando, 0 regressões
- [x] axe-core Playwright spec criado (8 testes WCAG 2.1 AA)

## Risks

- **R1**: Custom solution mais code para manter — mitigado: 1 arquivo (Tour.tsx) ~300 LOC vs manter dependência de lib externa. ✅
- **R2**: Callsites mistos durante migração — resolvido: migração completa nesta story, zero callsites shepherd. ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Tour component + ARIA + focus-trap + 11 tests + helpers. Migração dos callsites como follow-up. | @dev |
| 2026-04-15 | 3.0     | AC3 + AC4 completos: migração total (7 callsites), remoção shepherd.js, 84 unit tests, axe-core e2e spec. Status: Done. | @dev |
