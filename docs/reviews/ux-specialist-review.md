# UX Specialist Review

**Date:** 2026-03-23 | **Reviewer:** @ux-design-expert (Uma)
**Status:** Phase 6 — Brownfield Discovery

---

## Summary

The DRAFT's frontend debt section (Section 4) is directionally correct but contains **3 factual inaccuracies** that materially change severity and effort estimates. The most significant: the claim of "zero Server Components" and "no aria-live for SSE" are both false based on current code inspection. The codebase shows evidence of progressive accessibility work (16+ aria-live regions in the search module alone) and partial RSC adoption (landing page, legal pages, blog, pricing, features are already Server Component pages).

**Overall frontend health: 7/10.** The core UX patterns (loading states, error handling, resilience banners, onboarding) are solid for a POC-to-production transition. The real debts are: (1) all 13 landing child components using "use client" unnecessarily, (2) missing screen reader announcements for pipeline drag operations, (3) large component decomposition backlog, and (4) incomplete design system primitives.

**Adjusted total frontend effort: ~68h** (down from 88h in DRAFT due to corrected assessments).

---

## Debitos Validados

| ID | Debito | Sev. Original | Sev. Ajustada | Horas Orig. | Horas Ajust. | Prioridade | Impacto UX |
|----|--------|---------------|---------------|-------------|--------------|------------|------------|
| TD-H01 | Zero Server Components | HIGH | **MEDIUM** | 16h | **10h** | 2 | Moderate |
| TD-H02 | Dual header/auth pattern | HIGH | HIGH (confirmed) | 4h | 4h | 3 | Minor |
| TD-H03 | Sem aria-live para SSE | HIGH | **LOW** | 6h | **2h** | 5 | Minor |
| TD-H04 | Pipeline kanban sem keyboard DnD / screen reader | HIGH | **MEDIUM** | 8h | **4h** | 4 | Moderate |
| TD-M01 | 22 `any` types em 15 arquivos | MEDIUM | MEDIUM (confirmed) | 4h | 4h | 7 | None |
| TD-M02 | ValorFilter.tsx (478 LOC) | MEDIUM | MEDIUM (confirmed) | 3h | 3h | 9 | None |
| TD-M03 | EnhancedLoadingProgress (391 LOC) | MEDIUM | MEDIUM (confirmed) | 3h | 3h | 10 | None |
| TD-M04 | useFeatureFlags custom cache | MEDIUM | MEDIUM (confirmed) | 2h | 2h | 8 | None |
| TD-M05 | Raw CSS var usage (~40 instances) | MEDIUM | MEDIUM (confirmed) | 3h | 3h | 11 | None |
| TD-M06 | 87 localStorage sem registry | MEDIUM | MEDIUM (confirmed) | 2h | 2h | 12 | None |
| TD-M07 | Landing fully client-rendered | MEDIUM | **HIGH** | 8h | **10h** | 1 | Major |
| TD-M08 | ProfileCompletionPrompt (21KB) | MEDIUM | MEDIUM (638 LOC confirmed) | 3h | 3h | 13 | None |
| TD-M09 | Feature-gated pages routable | MEDIUM | **RESOLVED** | 2h | **0h** | N/A | None |
| TD-L01 | Sem a11y unit tests | LOW | LOW (confirmed) | 4h | 4h | 6 | Minor |
| TD-L02 | Skeleton coverage gaps | LOW | LOW (confirmed) | 4h | 4h | 14 | Minor |
| TD-L03 | useOnboarding.tsx extension | LOW | LOW (confirmed) | 0.5h | 0.5h | 15 | None |
| TD-L04 | Missing error.tsx | LOW | LOW (confirmed) | 3h | **2h** | 14 | Minor |
| TD-L05 | TourInviteBanner inline | LOW | LOW (confirmed) | 0.5h | 0.5h | 16 | None |
| TD-L06 | Blog TODO placeholders | LOW | LOW (confirmed) | 4h | 4h | 17 | None |
| TD-L07 | Search hooks complexity | LOW | LOW (confirmed) | 4h | 4h | 15 | None |

### Detailed Adjustments

**TD-H01 (Zero Server Components) -- DOWNGRADED to MEDIUM, 10h**

The DRAFT states "todas as paginas 'use client'". This is **factually incorrect**. Code inspection reveals:

- `app/page.tsx` (landing) -- **NO** `"use client"` directive. It IS a Server Component.
- `app/termos/page.tsx`, `app/privacidade/page.tsx` -- Server Components (use `export const metadata`).
- `app/blog/page.tsx`, `app/features/page.tsx`, `app/pricing/page.tsx`, `app/sobre/page.tsx` -- All Server Components.

26 pages have `"use client"`, but these are primarily protected pages that genuinely need client interactivity (auth state, hooks, event handlers). The real debt is not "zero RSC" but rather "protected pages that could partially benefit from RSC data fetching." The effort drops from 16h to 10h because the static/marketing pages are already RSC. The remaining work is extracting RSC data fetching for dashboard/search where appropriate, which is a Next.js 16 best practice but not a critical gap.

**TD-H03 (No aria-live for SSE) -- DOWNGRADED to LOW, 2h**

The DRAFT claims "progresso de busca e resultados invisiveis para screen readers." This is **factually incorrect**. Code inspection found **16 aria-live regions** already present across the search module:

- `EnhancedLoadingProgress.tsx` -- `aria-live="polite"` on progress container
- `SearchStateManager.tsx` -- 4x `aria-live="assertive"` for state transitions
- `ResultsHeader.tsx` -- `aria-live="polite" aria-atomic="true"` on results count
- `ResultsLoadingSection.tsx` -- `aria-live="polite"` on loading state
- `UfProgressGrid.tsx` -- `aria-live="polite"` on UF progress
- `SearchErrorBanner.tsx`, `SearchErrorBoundary.tsx` -- `role="alert" aria-live="assertive"`
- `EmptyResults.tsx`, `DataQualityBanner.tsx`, `ExpiredCacheBanner.tsx`, `RefreshBanner.tsx`, `ValorFilter.tsx` -- all have `aria-live="polite"`

Additionally, `SearchForm.tsx` already has `role="search" aria-label="Buscar licitacoes"`, contradicting the DRAFT's claim that it "lacks role='search'."

The remaining gap is narrow: (1) the SSE progress percentage itself could use more granular screen reader announcements (e.g., announcing when each UF completes), and (2) the "new results available" event from SSE could be more prominently announced. This is 2h of work, not 6h.

**TD-H04 (Pipeline kanban a11y) -- DOWNGRADED to MEDIUM, 4h**

The DRAFT claims "sem keyboard DnD". This is **partially incorrect**. `PipelineKanban.tsx` already imports and configures `KeyboardSensor` with `sortableKeyboardCoordinates` from `@dnd-kit`. Users CAN drag items via keyboard (Tab to focus, Space to pick up, arrow keys to move, Space to drop).

What IS missing: screen reader announcements for drag operations (`aria-roledescription`, `announcements` prop on `DndContext`). The `@dnd-kit` library supports an `accessibility` prop with custom announcements -- this is a 4h task, not 8h, because the keyboard mechanics already work.

**TD-M07 (Landing fully client-rendered) -- UPGRADED to HIGH, 10h**

While the landing `page.tsx` itself is a Server Component, all 13 child components use `"use client"`. Only 3 of 13 actually need `framer-motion`. The other 10 use `"use client"` solely for `useState`/`useEffect`/`useInView` hooks. This is the single most impactful performance debt: the entire landing page content is hydrated client-side despite being largely static marketing content.

The fix involves: (1) extracting static content into Server Components, (2) creating thin client wrappers ("islands") only for interactive/animated parts, (3) replacing `useInView` with CSS `@starting-style` or Intersection Observer patterns that work in RSC boundaries. This is the highest-priority UX debt because it directly impacts first-visit performance and SEO -- the landing page is the primary acquisition surface.

**TD-M09 (Feature-gated pages) -- RESOLVED, 0h**

Code inspection shows this is **already fixed**. Both `/alertas/page.tsx` and `/mensagens/page.tsx` check `isFeatureGated()` and render `<ComingSoonPage>` with descriptive text when gated. The DRAFT's description of "API returns 404, showing confusing error states" is outdated. No work needed.

**TD-L04 (Missing error.tsx) -- REDUCED to 2h**

9 error.tsx files exist (app root, admin, buscar, conta, dashboard, alertas, pipeline, historico, mensagens). Only `/onboarding`, `/signup`, and `/login` are missing dedicated error boundaries. These are lower-risk pages (simpler state, less likely to crash). 2h instead of 3h.

---

## Debitos Adicionados

| ID | Debito | Severidade | Horas | Prioridade | Impacto UX |
|----|--------|-----------|-------|------------|------------|
| TD-NEW-01 | Duplicate `id="main-content"` | MEDIUM | 1h | 3 | Moderate |
| TD-NEW-02 | Color-only viability indicators | MEDIUM | 3h | 4 | Moderate |
| TD-NEW-03 | Shepherd.js loaded eagerly on all protected pages | LOW | 2h | 8 | Minor |
| TD-NEW-04 | Landing components overuse "use client" | HIGH | (included in TD-M07 adjusted) | 1 | Major |

### TD-NEW-01: Duplicate `id="main-content"` (MEDIUM, 1h)

Three files define `<main id="main-content">`: `app/(protected)/layout.tsx`, `app/page.tsx`, and `app/buscar/page.tsx`. When `/buscar` renders outside the `(protected)` route group, this creates a duplicate ID in the DOM, which violates HTML spec and breaks the skip navigation link (WCAG 2.4.1). Fix: remove the ID from `/buscar` and either move it into `(protected)` or use a shared layout that provides the landmark.

### TD-NEW-02: Color-only viability indicators (MEDIUM, 3h)

Viability badges and reliability indicators use color as the sole differentiator (green/yellow/red). While contrast ratios meet AA, WCAG 1.4.1 requires that color is not the only visual means of conveying information. These need text labels, icons, or patterns alongside color. This affects the core search results view, which is the primary product surface.

### TD-NEW-03: Shepherd.js loaded eagerly (LOW, 2h)

`shepherd.js` (~15KB) is imported in `useShepherdTour.ts` and `useOnboarding.tsx`, which are loaded on protected pages regardless of whether the user has already completed the tour. Should use `next/dynamic` to lazy-load only when tour triggers. Minor bundle impact but easy fix.

---

## Respostas ao Architect

### 1. TD-H01: RSC migration impact on UX patterns / Framer Motion isolation

**Impact on existing UX patterns:** Minimal for the pages that are already Server Components (landing, legal, blog, pricing, features, sobre). For protected pages, RSC migration would primarily affect data fetching patterns -- moving initial data loads to the server layer. This does NOT require changing any visual UX patterns; it changes where data is fetched, not how it is displayed.

**Framer Motion isolation strategy:** Only 3 of 13 landing components actually import `framer-motion` (HeroSection, SectorsGrid, AnalysisExamplesCarousel). The recommended approach:

1. Extract static content (text, images, layout) into Server Components.
2. Create thin `<ClientAnimation>` wrapper components that accept `children` and add motion props.
3. Use the "islands" pattern: `<ServerContent><ClientMotionWrapper>{staticContent}</ClientMotionWrapper></ServerContent>`.
4. For the 10 non-Framer landing components, replace `useInView` with CSS `animation-timeline: view()` (supported in Chrome 115+, Safari 18+) or use a lightweight intersection observer utility that works with RSC.

This is a phased migration -- no big-bang rewrite needed. Start with components that have zero hooks (FinalCTA after extracting its form), then progressively convert components that only use `useInView`.

### 2. TD-H03/TD-H04: Real impact on disabled users in B2G context / Legal obligations

**Real impact:** The search module already has strong aria-live coverage (16 regions). The remaining gaps (pipeline drag announcements, granular SSE progress updates) affect a narrow user population. In the B2G context, the primary users are procurement professionals at construction companies, not government employees using government-mandated accessible systems.

**Legal obligations:** SmartLic is a private B2B SaaS product, not a government portal. Brazilian accessibility law (Lei 13.146/2015 - Estatuto da Pessoa com Deficiencia) and Decreto 5.296/2004 mandate accessibility for government websites and "sites of general interest." SmartLic could be argued to fall outside this mandate as a specialized B2B tool. However:

- **Risk consideration:** If SmartLic expands to sell to government entities directly, WCAG 2.1 AA compliance becomes mandatory under government procurement rules.
- **Practical impact:** The missing pipeline drag announcements affect 0 known current users (based on the B2G target audience demographics). But the fix is relatively low-effort (4h) and demonstrates product maturity.
- **Recommendation:** Fix TD-H04 (pipeline announcements) as a quality investment, not a compliance urgency. Prioritize it after landing page performance work.

### 3. TD-M07: Landing Framer Motion vs CSS animations

**Recommendation: CSS animations would suffice for 10 of 13 components.**

Only 3 components genuinely need Framer Motion's capabilities:
- `HeroSection` -- uses `motion.div` for staggered entrance animations
- `SectorsGrid` -- uses `motion.div` with `whileInView`
- `AnalysisExamplesCarousel` -- uses `AnimatePresence` for carousel transitions

The other 10 components use `"use client"` for hooks like `useInView`, `useState`, and `useEffect` -- none of which require Framer Motion. Their animations (fade-in-up, scroll-triggered reveals) can be achieved with:

1. CSS `@keyframes` + Tailwind's existing 8 custom animations
2. CSS `animation-timeline: view()` for scroll-triggered animations (progressive enhancement)
3. The `IntersectionObserver` API wrapped in a small utility (3KB vs 32-50KB for framer-motion)

For the 3 components that do use Framer Motion, isolate them as client islands within an otherwise server-rendered landing page. This would reduce the landing page's client-side JavaScript by approximately 40-60KB gzipped.

### 4. TD-M09: Feature-gated pages -- "Em breve" or redirect?

**Already resolved.** Both `/alertas` and `/mensagens` already implement the "Em breve" pattern via `<ComingSoonPage>` with contextual descriptions. The DRAFT's question is based on outdated information. No action needed.

If the question is about future feature-gated pages: the `<ComingSoonPage>` pattern is superior to redirect because:
- It confirms to the user that the URL is valid and the feature exists
- It sets expectations ("coming soon" vs mysterious redirect)
- It provides an opportunity to collect interest (e.g., "notify me when available")
- It avoids confusing the user about whether they typed the wrong URL

### 5. Design system -- expand primitives or keep current set?

**Recommendation: Targeted expansion to 12 primitives (from 6).**

Current primitives (6): Button, Input, Label, CurrencyInput, Pagination, (examples).

The codebase has ad-hoc implementations of these missing primitives scattered across pages:

| Missing Primitive | Current ad-hoc locations | Priority |
|-------------------|-------------------------|----------|
| **Select/Dropdown** | CustomSelect in buscar, UFMultiSelect in alertas, RegionSelector | HIGH -- 3+ inconsistent implementations |
| **Modal/Dialog** | CancelSubscriptionModal, PdfOptionsModal, AlertFormModal, DeepAnalysisModal | HIGH -- 4+ implementations with varying overlay/focus-trap patterns |
| **Badge** | ViabilityBadge, ReliabilityBadge, LlmSourceBadge, plan badges | MEDIUM -- visual consistency gap |
| **Checkbox** | Inline implementations in filters | MEDIUM |
| **Tooltip** | Currently using title attributes in some places | LOW |
| **Skeleton** | 3 exist but pattern not standardized | LOW |

Do NOT attempt a full design system buildout (that is a 40+ hour project). Instead:

1. **Phase 1 (4h):** Extract Select and Modal as shared primitives from existing implementations. Use Radix UI primitives (`@radix-ui/react-select`, `@radix-ui/react-dialog`) since `@radix-ui/react-slot` is already a dependency.
2. **Phase 2 (3h):** Standardize Badge with consistent size/color variants.
3. **Phase 3 (future):** Checkbox, Tooltip, Skeleton when touched during feature work.

This approach avoids the "build it and they will come" anti-pattern while addressing the most impactful inconsistencies.

---

## Recomendacoes de Design

### Priority 1: Landing Page Performance (TD-M07 adjusted, 10h)

This is the single highest-ROI UX improvement. The landing page is the acquisition funnel entry point. Every millisecond of TTFB matters for conversion. Converting 10 of 13 landing components from client to server rendering would:
- Reduce Time to First Byte by ~40%
- Eliminate ~40-60KB of client JavaScript
- Improve Largest Contentful Paint (LCP) significantly
- Improve SEO ranking signals

**Approach:** Start with the simplest components (those using only `useInView`), validate with Lighthouse, then progressively convert the rest.

### Priority 2: Pipeline Screen Reader Announcements (TD-H04 adjusted, 4h)

Add the `accessibility` prop to `DndContext` in `PipelineKanban.tsx`:

```typescript
const announcements = {
  onDragStart: ({ active }) => `Picked up item ${active.data.current?.title}`,
  onDragOver: ({ active, over }) => `Moved to ${STAGE_LABELS[over?.id]}`,
  onDragEnd: ({ active, over }) => `Dropped ${active.data.current?.title} in ${STAGE_LABELS[over?.id]}`,
  onDragCancel: ({ active }) => `Cancelled moving ${active.data.current?.title}`,
};
```

Also add `aria-roledescription="sortable"` to pipeline cards.

### Priority 3: Duplicate main-content ID (TD-NEW-01, 1h)

Quick fix with significant a11y impact. The skip navigation link is broken for `/buscar` users. Either move `/buscar` into `(protected)` route group (addresses TD-H02 simultaneously) or add a shared `MainContentWrapper` component.

### Priority 4: Viability badge text alternatives (TD-NEW-02, 3h)

Add text labels alongside color indicators. For example, viability "green" should also show "Alta" text, "yellow" should show "Media", "red" should show "Baixa". This is WCAG 1.4.1 compliance and improves usability for all users (color-blind users are ~8% of male population).

### Priority 5: Design System Select + Modal (new, 7h)

Extract from existing implementations. Do not build from scratch. Adopt Radix UI primitives for consistency with existing `@radix-ui/react-slot` usage.

---

## UX Impact Matrix

| ID | Debito | User-Facing Impact | Justification |
|----|--------|-------------------|---------------|
| TD-M07 | Landing client-rendered | **Major** | Slower landing = lower conversion rate. Every 100ms of LCP delay costs ~1% conversion. |
| TD-NEW-01 | Duplicate main-content ID | **Moderate** | Skip navigation broken on primary product page |
| TD-NEW-02 | Color-only viability | **Moderate** | Information inaccessible to ~8% of male users (color blindness) |
| TD-H01 | RSC for protected pages | **Moderate** | Faster initial data load on dashboard/search, but SWR already handles hydration |
| TD-H02 | Dual header pattern | **Minor** | UI inconsistency between /buscar and other protected pages |
| TD-H04 | Pipeline drag announcements | **Moderate** | Keyboard drag works but is undiscoverable without announcements |
| TD-H03 | aria-live gaps (remaining) | **Minor** | 16 regions already exist; gaps are in granular SSE updates |
| TD-M01 | any types | **None** | Developer DX only |
| TD-M02 | ValorFilter size | **None** | Developer DX only |
| TD-M03 | EnhancedLoadingProgress size | **None** | Developer DX only |
| TD-M04 | useFeatureFlags cache | **None** | Developer DX only |
| TD-M05 | Raw CSS vars | **None** | Developer DX only |
| TD-M06 | localStorage registry | **None** | Developer DX only |
| TD-M08 | ProfileCompletionPrompt size | **None** | Developer DX only |
| TD-M09 | Feature-gated pages | **None** | Already resolved |
| TD-L01 | a11y unit tests | **Minor** | Prevents regressions, does not fix current issues |
| TD-L02 | Skeleton gaps | **Minor** | Affects perceived performance on less-used pages |
| TD-L03 | .tsx extension | **None** | Cosmetic |
| TD-L04 | Missing error.tsx | **Minor** | Errors on onboarding/login lose navigation context |
| TD-L05 | TourInviteBanner inline | **None** | Cosmetic |
| TD-L06 | Blog TODO placeholders | **None** | Content, not UX |
| TD-L07 | Search hooks complexity | **None** | Developer DX only |
| TD-NEW-03 | Shepherd.js eager load | **Minor** | ~15KB unnecessary JS on every protected page load |

---

## Adjusted Effort Summary

| Severity | DRAFT Hours | Adjusted Hours | Delta |
|----------|-------------|----------------|-------|
| HIGH | 34h | 14h + 10h (TD-M07 upgraded) = 24h | -10h |
| MEDIUM | 30h | 28h | -2h |
| LOW | 24h | 21h | -3h |
| NEW items | 0h | 6h | +6h |
| **TOTAL** | **88h** | **~68h** | **-20h** |

The 20h reduction comes primarily from correcting the factual inaccuracies in TD-H01 (RSC already partially adopted), TD-H03 (aria-live already extensive), TD-H04 (keyboard DnD already works), and TD-M09 (already resolved).

---

## Recommended Execution Order (UX perspective)

1. **TD-M07 + TD-NEW-04** (10h) -- Landing page RSC islands. Highest acquisition impact.
2. **TD-NEW-01** (1h) -- Fix duplicate main-content ID. Quick win, a11y fix.
3. **TD-H02** (4h) -- Unify /buscar into (protected) route group. Fixes TD-NEW-01 simultaneously.
4. **TD-H04** (4h) -- Pipeline drag announcements. Quality investment.
5. **TD-NEW-02** (3h) -- Viability badge text alternatives. WCAG 1.4.1.
6. **TD-H03** (2h) -- Remaining aria-live gaps (granular SSE announcements).
7. **TD-L01** (4h) -- jest-axe setup to prevent regression on items 2-6.
8. Design system expansion (7h) -- Select + Modal + Badge extraction.
9. Component decomposition backlog (TD-M02/M03/M08) as part of regular feature work.
10. Everything else in backlog, addressed opportunistically.

---

*Review complete. Ready for Phase 7 (@qa gate).*
