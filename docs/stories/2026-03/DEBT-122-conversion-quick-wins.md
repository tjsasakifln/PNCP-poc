# DEBT-122: Ship Conversion Quick Wins
**Priority:** P1
**Effort:** 3h
**Owner:** @dev
**Sprint:** Week 1, Day 1-2

## Context

Three low-effort, high-impact conversion improvements were identified in the GTM assessment. The `TestimonialSection` component already exists and is used on `/planos` but is not imported on the landing page. The pricing page defaults to monthly billing (R$397/mo) instead of annual (R$297/mo), anchoring users on the higher price. The Consultoria plan CTA uses a raw `<button>` instead of the `<Button>` component, losing loading state feedback. Combined estimated impact: +8-18% conversion improvement.

## Acceptance Criteria

### Testimonials on Landing Page (P1-006)

- [x] AC1: `TestimonialSection` component imported and rendered on the landing page between existing sections
- [x] AC2: Section is visible on both desktop and mobile
- [x] AC3: No layout shift or CLS regression (section has fixed height or skeleton)

### Annual Billing Default (P1-012)

- [x] AC4: `/planos` loads with annual billing selected by default (not monthly)
- [x] AC5: `?billing=monthly` URL param overrides the default to monthly
- [x] AC6: `?billing=semiannual` URL param overrides the default to semiannual
- [x] AC7: Existing pricing page tests pass without modification

### Consultoria CTA Button (P2-016)

- [x] AC8: Consultoria plan CTA uses `<Button>` component (not raw `<button>`)
- [x] AC9: Button shows loading spinner during checkout redirect
- [x] AC10: Consistent styling with SmartLic Pro CTA button

## Technical Notes

**Testimonials (AC1-AC3):**
- Component location: check `/planos/page.tsx` for the existing import path
- Add import + JSX line in `frontend/app/(landing)/page.tsx`
- Position: after `StatsSection` or `HowItWorksSection` (test both, pick what flows better)

**Annual Default (AC4-AC7):**
- File: `frontend/app/planos/page.tsx` approximately line 92
- Change: `useState<BillingPeriod>("monthly")` to `useState<BillingPeriod>("annual")`
- Verify URL param override logic still works (check for `useSearchParams` reading `billing` param)

**Consultoria CTA (AC8-AC10):**
- File: `frontend/app/planos/page.tsx` approximately line 604
- Replace `<button>` with `<Button>` component (same one used for Pro plan CTA)
- Add loading state prop tied to checkout flow

## Test Requirements

- [x] Existing landing page tests pass
- [x] Existing pricing page tests pass
- [ ] Manual verification: `/planos` shows annual prices on load
- [ ] Manual verification: `/planos?billing=monthly` shows monthly prices

## Files to Modify

- `frontend/app/(landing)/page.tsx` -- import + render TestimonialSection
- `frontend/app/planos/page.tsx` -- annual default + Consultoria button fix

## Definition of Done

- [x] All ACs pass
- [x] Tests pass (existing + new)
- [ ] No regressions in CI
- [x] Code reviewed
