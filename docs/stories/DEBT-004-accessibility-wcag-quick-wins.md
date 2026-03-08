# DEBT-004: Accessibility Quick Wins (WCAG AA)

**Sprint:** 1
**Effort:** 7.5h
**Priority:** HIGH
**Agent:** @ux-design-expert (Uma)

## Context

Four WCAG AA violations were identified, three of which are quick wins addressable in Sprint 1. Government contracts (B2G) increasingly require accessibility compliance. Non-compliance risks disqualification from procurement processes. The violations affect screen reader users, keyboard-only users, and users with color vision deficiency (~8% of males).

FE-023 (color-only indicators) is deferred to Sprint 2 (DEBT-012) as it requires design changes to the ViabilityBadge component.

## Scope

| ID | Debito | WCAG | Horas |
|----|--------|------|-------|
| FE-034 | Missing `aria-label` on icon-only buttons — screen readers announce "button" with no context | 1.3.1, 4.1.2 | 1.5h |
| FE-022 | No focus trapping in modals (Dialog, DeepAnalysis, Upgrade, Cancel) — keyboard users trapped or escape modals | 2.4.3 | 4h |
| FE-021 | No `aria-live` for search results — screen readers not notified of dynamic content updates | 4.1.3 | 2h |

## Tasks

### Icon Button Labels (FE-034) — 1.5h

- [x] Audit all `<button>` elements with only icon/SVG children (Sidebar collapse, filter toggles, close buttons, etc.)
- [x] Add `aria-label` with descriptive text to each icon-only button
- [x] Verify no duplicate aria-labels on the same page

### Focus Trapping (FE-022) — 4h

- [x] Install `focus-trap-react` package
- [x] Wrap Dialog/Modal components with `<FocusTrap>`
- [x] Wrap DeepAnalysis modal with `<FocusTrap>`
- [x] Wrap Upgrade/CancelSubscription modals with `<FocusTrap>`
- [x] Verify Escape key closes modal and returns focus to trigger element
- [x] Test tab cycling stays within modal when open

### Search Results Announcements (FE-021) — 2h

- [x] Add `aria-live="polite"` region for search result count ("X resultados encontrados")
- [x] Add `aria-live="assertive"` for search errors
- [x] Ensure loading state changes are announced ("Buscando..." -> "X resultados")
- [x] Verify announcements work with NVDA/VoiceOver

## Acceptance Criteria

- [x] AC1: Zero icon-only buttons without `aria-label` (axe audit passes)
- [x] AC2: All modals trap focus — Tab key cycles within modal, not behind it
- [x] AC3: Escape key closes modals and returns focus to the trigger element
- [x] AC4: Screen reader announces search result count after search completes
- [x] AC5: Screen reader announces search errors via `aria-live="assertive"`
- [x] AC6: `focus-trap-react` is in `package.json` dependencies
- [x] AC7: Zero regressions in frontend test suite

## Tests Required

- Axe accessibility audit: zero violations for aria-label on buttons
- Focus trap test: open modal, tab through all focusable elements, verify focus stays inside
- Focus trap test: close modal, verify focus returns to trigger
- aria-live test: verify search results update triggers screen reader announcement
- Integration test: search flow with accessibility assertions

## Definition of Done

- [x] All tasks complete
- [x] axe-core audit passes for all authenticated pages
- [x] Tests passing (frontend 4962+ / 0 new fail)
- [x] No regressions
- [ ] Manual keyboard navigation test on buscar page
- [x] Code reviewed

## File List

| File | Change |
|------|--------|
| `frontend/package.json` | Added `focus-trap-react` dependency |
| `frontend/app/admin/partners/page.tsx` | Added `aria-label="Fechar"` to close button (FE-034) |
| `frontend/app/buscar/components/DeepAnalysisModal.tsx` | Wrapped with FocusTrap, removed manual ESC/focus handlers (FE-022) |
| `frontend/components/account/CancelSubscriptionModal.tsx` | Added FocusTrap + scroll lock + Escape handling (FE-022) |
| `frontend/components/subscriptions/DowngradeModal.tsx` | Restructured with FocusTrap + scroll lock (FE-022) |
| `frontend/components/org/InviteMemberModal.tsx` | Added FocusTrap + scroll lock (FE-022) |
| `frontend/components/billing/PaymentRecoveryModal.tsx` | Added FocusTrap (FE-022) |
| `frontend/components/MobileDrawer.tsx` | Added FocusTrap (FE-022) |
| `frontend/app/buscar/components/search-results/ResultsHeader.tsx` | Added `aria-live="polite" aria-atomic="true"` (FE-021) |
| `frontend/app/buscar/components/EmptyResults.tsx` | Added `aria-live="polite"` (FE-021) |
| `frontend/app/buscar/components/SearchStateManager.tsx` | Added `aria-live="assertive"` to 4 error states (FE-021) |
| `frontend/app/buscar/components/SearchErrorBanner.tsx` | Added `aria-live="assertive"` (FE-021) |
| `frontend/__tests__/debt-004-accessibility-wcag.test.tsx` | 19 new tests covering all ACs |
| `frontend/__tests__/components/subscriptions/DowngradeModal.test.tsx` | Fixed backdrop selector (`.fixed` → `.absolute`) |
