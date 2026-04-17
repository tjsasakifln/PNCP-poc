# STORY-5.13: UX Micro-Fixes Bundle (TD-FE-017, 018, 019, 020, 021, 052, 053)

**Priority:** P2 | **Effort:** L (25-40h) | **Squad:** @ux-design-expert + @dev | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** usuário SmartLic, **I want** múltiplas UX rough edges suavizadas, **so that** experiência seja mais polida.

## Acceptance Criteria
- [x] AC1 (TD-FE-017): Shepherd tour dismiss persistente — **Already implemented by STORY-4.2** (Tour A11y component with `markTourPermanentlyDismissed()` + localStorage)
- [x] AC2 (TD-FE-018): Bottom nav mobile `fixed bottom-0` + `h-16` spacer div — **Already implemented** in BottomNav.tsx
- [x] AC3 (TD-FE-019): "Atualizado X min atrás" FreshnessIndicator badge integrado no ResultsHeader
- [x] AC4 (TD-FE-020): Form validation errors com `role="alert" aria-live="assertive"` — signup, login, conta forms
- [x] AC5 (TD-FE-021): Blog content responsive via Tailwind `prose` utilities (max-w-none + prose-lg) — **Already implemented** in BlogArticleLayout
- [x] AC6 (TD-FE-052): SWR mutate revalidate — **Already implemented** with `mutate()` pattern (admin pages, alertas, pipeline)
- [x] AC7 (TD-FE-053): `LoadingResultsSkeleton` dimensions match real ResultCard (p-4/p-6, title+3 lines+meta) — **Already implemented**

## Implementation Notes

### AC1: Tour Persistence (Pre-existing)
- `Tour.tsx` lines 70-86: `isTourPermanentlyDismissed()` / `markTourPermanentlyDismissed()`
- localStorage key: `smartlic_tour_{tourId}_dismissed_permanent`
- "Não mostrar novamente" button triggers permanent dismiss

### AC2: Bottom Nav (Pre-existing)
- `BottomNav.tsx` line 144: `fixed bottom-0 left-0 right-0 z-50`
- Line 262-263: `h-16 aria-hidden="true"` spacer prevents content occlusion
- `lg:hidden` ensures mobile-only rendering

### AC3: FreshnessIndicator Integration (NEW)
- Integrated into `ResultsHeader.tsx` next to results count
- Uses `coverage_metadata.data_timestamp` → `ultima_atualizacao` → `cached_at` fallback chain
- Freshness type from `coverage_metadata.freshness` with fallback to `cached ? "cached_stale" : "live"`

### AC4: Form Validation Accessibility (NEW)
- Added `role="alert" aria-live="assertive"` to error messages in:
  - `signup/components/SignupForm.tsx` (email errors)
  - `conta/conta-fields.tsx` (SelectField, NumberField errors)
- Login form already had `role="alert"` on error banner
- `ResultsHeader` already has `aria-live="polite"` (line 31)

### AC5: Blog Responsive (Pre-existing)
- `BlogArticleLayout.tsx` line 272: `prose prose-lg dark:prose-invert max-w-none`
- Tailwind prose handles responsive images, max-width, and typography automatically

### AC6: SWR Mutate (Pre-existing)
- Admin pages: `mutateMetrics()`, `mutateUsers()`, `mutateSla()` after mutations
- Alertas: optimistic `mutateAlerts()` on toggle/delete
- Feature flags: `mutate()` after PATCH/reload

### AC7: Skeleton Dimensions (Pre-existing)
- `LoadingResultsSkeleton`: p-4/p-6 container + h-6 title + 3×h-4 content lines + flex meta row
- Matches ResultCard structure: summary + stats + badges

## File List
- `frontend/app/buscar/components/search-results/ResultsHeader.tsx` — AC3
- `frontend/app/signup/components/SignupForm.tsx` — AC4
- `frontend/app/conta/conta-fields.tsx` — AC4
- `docs/stories/2026-04/EPIC-TD-2026Q2/STORY-5.13-ux-micro-fixes-bundle.md` — this file

## Definition of Done
- [x] All 7 ACs met

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Implementation: AC3 FreshnessIndicator + AC4 aria-live. AC1/2/5/6/7 verified pre-existing. | @dev |
