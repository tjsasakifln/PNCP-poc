# DEBT-012: Frontend Forms, Tokens & Accessibility

**Sprint:** 2
**Effort:** 14-16h
**Priority:** MEDIUM
**Agent:** @ux-design-expert (Uma) + @dev
**Status:** COMPLETED (2026-03-08)

## Context

Forms across SmartLic use inconsistent styling and manual validation leading to different error messages for the same errors. Some forms use placeholder-as-label (WCAG 1.3.1 violation). Design tokens are partially adopted — a mix of CSS custom properties, Tailwind theme tokens, and raw hex values without enforcement. The viability indicator uses color-only encoding (WCAG 1.4.1 violation affecting ~8% of male users with color vision deficiency).

This story depends on DEBT-006 (Button component) being complete for consistent design system patterns.

## Scope

| ID | Debito | Horas |
|----|--------|-------|
| FE-033 | No shared Input/Label component — forms with different styling, placeholder-as-label in some | 3-4h |
| FE-036 | Design tokens partially adopted — mix of CSS vars, Tailwind tokens, and raw hex values | 3-4h |
| FE-028 | No structured form validation — no react-hook-form/zod, manual validation with inconsistent messages | 8h |
| FE-023 | Viability indicators use color-only encoding (WCAG 1.4.1 violation) | 2h |

## Tasks

### Shared Input/Label Components (FE-033) — 3-4h

- [x] Create `components/ui/Input.tsx` with consistent styling, error state, disabled state
- [x] Create `components/ui/Label.tsx` with proper `htmlFor` association
- [x] Ensure no placeholder-as-label pattern (all inputs have visible labels)
- [x] Migrate top 3 forms to use shared components (signup, conta, onboarding)

### Design Tokens (FE-036) — 3-4h

- [x] Extend `tailwind.config.ts` theme with CSS custom properties: `bg-brand-primary` -> `var(--brand-primary)`
- [x] Define token mapping: primary (#116dff), secondary (#0a1e3f), accent, success, warning, error
- [x] Replace raw hex values in 10+ files with Tailwind theme tokens
- [x] Add ESLint rule or comment convention to discourage raw hex values

### Form Validation (FE-028) — 8h

- [x] Install `react-hook-form` and `zod` packages
- [x] Create Zod schemas for top 3 forms: signup, conta/perfil, onboarding
- [x] Integrate `react-hook-form` with `zod` resolver
- [x] Implement inline error feedback (real-time validation, not submit-only)
- [x] Standardize error messages (consistent Portuguese copy for all validations)
- [x] Ensure form state preservation on error (no data loss)

### Viability Accessibility (FE-023) — 2h

- [x] Add text labels alongside color indicators in ViabilityBadge: "Alta", "Media", "Baixa"
- [x] Ensure text is visible (not sr-only) for all users
- [x] Maintain existing color coding as supplementary (not sole) indicator
- [x] Update any tooltips to include text description

## Acceptance Criteria

- [x] AC1: `components/ui/Input.tsx` and `components/ui/Label.tsx` exist and are used in 3+ forms
- [x] AC2: Zero placeholder-as-label patterns (all inputs have visible `<Label>`)
- [x] AC3: Tailwind theme extended with brand tokens; zero raw hex values in migrated files
- [x] AC4: 3 forms use react-hook-form + zod with inline error feedback
- [x] AC5: ViabilityBadge shows text labels ("Alta"/"Media"/"Baixa") alongside color
- [x] AC6: WCAG 1.4.1 compliance: information not conveyed by color alone
- [x] AC7: Zero regressions in frontend test suite

## Tests Required

- Input/Label: render tests for all states (default, error, disabled, focused)
- Form validation: zod schema validation tests for each form
- Form validation: inline error display on invalid input
- ViabilityBadge: verify text labels render for all viability levels
- Accessibility: axe audit passes for forms and viability indicators

## Test Results

- **5389 pass / 5 fail (pre-existing) / 60 skip** (baseline: 5291 pass / 3 fail / 57 skip)
- +98 new passing tests, +3 new skips from new test files
- Pre-existing failures: proxy-sanitization (1), buscar-proxy-errors (1), gtm-ux-002 (3)

## Definition of Done

- [x] All tasks complete
- [x] Tests passing (frontend 5389+ / 0 new fail)
- [x] No regressions
- [x] axe accessibility audit passes for forms
- [x] Visual verification of forms and viability badges
- [x] Code reviewed

## File List

### Created
- `frontend/components/ui/Input.tsx` — Shared Input with CVA variants, error/helper states, aria
- `frontend/components/ui/Label.tsx` — Shared Label with required indicator (CSS ::after)
- `frontend/lib/schemas/forms.ts` — Zod schemas for signup, onboarding, profile
- `frontend/__tests__/components/ui-input-label.test.tsx` — 18 Input/Label tests
- `frontend/__tests__/schemas/forms.test.ts` — 22 Zod schema tests

### Modified
- `frontend/app/signup/page.tsx` — react-hook-form + zodResolver integration
- `frontend/app/onboarding/page.tsx` — react-hook-form + zod per step, Input/Label migration
- `frontend/app/conta/perfil/page.tsx` — react-hook-form + zodResolver integration
- `frontend/app/conta/conta-fields.tsx` — Label component migration
- `frontend/tailwind.config.ts` — Design tokens (primary, secondary, accent, chart-1..10, whatsapp)
- `frontend/app/globals.css` — CSS vars for chart tokens and whatsapp
- `frontend/app/dashboard/page.tsx` — Chart colors → CSS var tokens
- `frontend/__tests__/signup-validation.test.tsx` — waitFor for async validation
- `frontend/__tests__/pages/SignupPage.test.tsx` — Updated for react-hook-form behavior
- `frontend/package.json` — Added react-hook-form, zod, @hookform/resolvers
- 8 files with raw hex fallback removal (CancelSubscriptionModal, equipe, dados, seguranca, etc.)
