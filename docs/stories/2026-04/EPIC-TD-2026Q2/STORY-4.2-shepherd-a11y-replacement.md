# STORY-4.2: Shepherd.js A11y Replacement (TD-FE-002)

**Priority:** P1 (a11y critical — screen readers não parseiam Shepherd HTML)
**Effort:** M (16-24h)
**Squad:** @ux-design-expert + @dev + @qa
**Status:** InReview
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
- [x] **Decisão de biblioteca**: custom React solution com `focus-trap-react` (já é devDep, usado em 11 arquivos). Economiza ~20KB net vs Shepherd + CSS. Mais controle sobre ARIA do que `react-joyride` (50KB) ou `intro.js` (a11y frágil).

### AC2: Tour component com ARIA

- [x] `frontend/components/tour/Tour.tsx`:
  - `role="dialog"` + `aria-modal="false"` (tour não bloqueia a página)
  - `aria-live="polite"` em live region anunciando "Passo N de M: {title}"
  - `aria-labelledby` + `aria-describedby` vinculados a `<h2>` e `<p>` do step
  - FocusTrap com `returnFocusOnDeactivate: true`, `tabbableOptions.displayCheck: 'none'` (compat jsdom), `fallbackFocus` na div do step
- [x] Keyboard handling completo: ESC cancela (onSkip), ArrowRight avança, ArrowLeft volta, Tab/Shift+Tab permanecem no card

### AC3: Migration

- [x] Componente Tour + helpers (`isTourPermanentlyDismissed`, `markTourPermanentlyDismissed`) commitados em `frontend/components/tour/`
- [ ] **Migração faseada dos 4 callsites** (`GuidedTour`, dashboard/page.tsx, pipeline/page.tsx, DemoClient.tsx): follow-up em batches isolados. `useShepherdTour` hook continua funcionando via Shepherd.js (deps preservadas neste commit) até que cada callsite seja migrado. Isso evita o big-bang rewrite de 7 arquivos simultâneos.
- [ ] Remoção de `shepherd.js` de `package.json` + deletion de `styles/shepherd-theme.css`: último passo da migração faseada

### AC4: Verification

- [x] Unit tests: `frontend/__tests__/components/Tour.test.tsx` (11 tests, 11/11 pass) cobrindo ARIA attributes, live region, keyboard navigation, focus trap, onComplete/onSkip, permanent dismiss, disabled prop, onStepChange
- [ ] axe-core via Playwright (novo `e2e-tests/tour-a11y.spec.ts`): adicionado durante a migração faseada de cada callsite
- [ ] Manual screen reader (NVDA/VoiceOver): executado durante QA pós-migração

### AC5: Dismiss permanente

- [x] Botão "Não mostrar novamente" → `localStorage.setItem('smartlic_tour_{tourId}_dismissed_permanent', 'true')`
- [x] Hook `isTourPermanentlyDismissed(tourId)` + `markTourPermanentlyDismissed(tourId)` exportados
- [x] Resolve TD-FE-017 (tour não dismissível)

---

## Tasks / Subtasks

- [x] Task 1: Audit Shepherd usage atual
- [x] Task 2: Tool selection (custom + focus-trap-react)
- [x] Task 3: Implementar `<Tour>` (AC2)
- [ ] Task 4: Migrar `/onboarding` (phased follow-up)
- [x] Task 5: Persistent dismiss (AC5)
- [x] Task 6: Unit tests (11/11)
- [ ] Task 7: Remove `shepherd.js` (último passo da migração faseada)

## Dev Notes

- **Por que phased migration?** Os 7 callsites usam `useShepherdTour` hook que encapsula a lib. Um big-bang rewrite tocaria 7 arquivos simultaneamente — alto risco de regressão visual em fluxos críticos (onboarding, buscar, dashboard, pipeline). Phased approach: cada callsite é migrado isoladamente + Chromatic snapshot antes de remover Shepherd.
- **Focus-trap + jsdom quirks**: jsdom retorna `offsetWidth/Height === 0` para todos elementos, fazendo `focus-trap` lançar erro em CI. Bypass via `tabbableOptions: { displayCheck: 'none' }` + `fallbackFocus`.
- **Bundle size follow-up**: remover `shepherd.js` da `package.json` economiza ~30KB. Ganho net vs adicionar código custom (~3KB): +27KB livre. Execução no último PR da migração faseada.
- **Live region**: `aria-live="polite"` + `aria-atomic="true"` em div `sr-only`. Screen readers anunciam "Passo 1 de 3: Bem-vindo" a cada transição sem interromper o foco atual.

## File List

### Created

- `frontend/components/tour/Tour.tsx` — componente principal + helpers `isTourPermanentlyDismissed`/`markTourPermanentlyDismissed`
- `frontend/__tests__/components/Tour.test.tsx` — 11 unit tests

### Modified

Nenhum (migration dos callsites é follow-up).

## Testing

- 11/11 unit tests passam em `frontend/__tests__/components/Tour.test.tsx`
- Tests cobrem: ARIA attributes, aria-live region, keyboard navigation (ArrowRight/Left, ESC), focus trap, onComplete on last step, onSkip via ESC, permanent dismiss via button, disabled prop, onStepChange callback, round-trip de `isTourPermanentlyDismissed`/`markTourPermanentlyDismissed`
- axe-core Playwright + manual SR: durante QA da migração faseada

## Definition of Done

- [x] Tour component com ARIA + focus-trap + dismiss permanente + 11 unit tests
- [ ] Migration dos 4 callsites (follow-up)
- [ ] Remoção de shepherd.js (follow-up)

**Follow-up story:** `TD-FE-002b — Shepherd callsite migration sweep` cobrindo:
1. Reescrever `useShepherdTour` internamente para usar Tour (preserva API externa)
2. Migrar GuidedTour, dashboard/page.tsx, pipeline/page.tsx, DemoClient.tsx
3. Atualizar 3 test mocks (`shepherd-tours.test.tsx`, `useOnboarding.test.tsx`, `GuidedTour.test.tsx`)
4. axe-core Playwright spec novo + manual SR
5. `npm uninstall shepherd.js` + remove `styles/shepherd-theme.css`
6. Chromatic snapshots antes/depois em onboarding + buscar + dashboard + pipeline + demo

## Risks

- **R1**: Custom solution mais code para manter — mitigado: 1 arquivo (Tour.tsx) ~200 LOC vs manter dependência de lib externa. ✅
- **R2**: Callsites mistos durante migração (alguns Shepherd, outros Tour) — mitigado: phased approach isola cada callsite em PR próprio. ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Tour component + ARIA + focus-trap + 11 tests + helpers. Migração dos callsites e remoção de shepherd.js ficam como follow-up TD-FE-002b para reduzir blast radius. | @dev |
