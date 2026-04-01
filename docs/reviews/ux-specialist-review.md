# UX Specialist Review — SmartLic

**Reviewer:** @ux-design-expert (Uma)
**Date:** 2026-03-31
**DRAFT Reviewed:** docs/prd/technical-debt-DRAFT.md (Section 3: Frontend/UX Debts, Section 7: Questions)
**Frontend Spec Reference:** docs/frontend/frontend-spec.md (Phase 3)

---

## Summary

The DRAFT's Section 3 (Frontend/UX Debts, FE-001 through FE-032) is well-structured and captures the majority of genuine UX-impacting technical debt. The @architect team correctly identified the two most critical user-facing issues: the search progress stall at 78% (FE-001) and the anxiety-inducing error 524 exposure (FE-006). The prioritization matrix (Section 5) correctly places these as P0.

However, my review reveals three significant adjustments:

1. **FE-003 (ViabilityBadge title attr) has already been resolved.** The component now uses a custom accessible tooltip with `role="tooltip"`, `aria-describedby`, keyboard support, and tap-to-toggle on mobile. This debt should be marked RESOLVED and removed from the remediation backlog. The DRAFT incorrectly estimates 4h of work for something already done.

2. **FE-015 (prefers-reduced-motion) is partially resolved.** The global CSS already includes a `@media (prefers-reduced-motion: reduce)` rule that disables all CSS animations. The `useInView` hook and `AnimateOnScroll` component also check for reduced motion. The remaining gap is Framer Motion JavaScript-driven animations on the landing page, which bypass the CSS rule. Scope reduced from "not respected" to "one gap in JS-driven animations."

3. **FE-009 (aria-live) is partially resolved.** Multiple search sub-components already include `aria-live` attributes (BannerStack, DataQualityBanner, EnhancedLoadingProgress, EmptyResults, ErrorDetail, ExpiredCacheBanner, and others -- 28+ usages found). The remaining gap is narrower than described.

4. **Three debts are missing from the DRAFT** that have meaningful UX impact: landing page excessive hydration, pipeline kanban missing drag announcements for screen readers, and colorblind-unsafe chart palette.

Total estimated remediation for the FE debt section: **~128h** (down from DRAFT's ~148h after removing resolved items and adjusting estimates, but up slightly from adding 4 new items).

---

## Debts Validated

| ID | Debt | Original Severity | Adjusted Severity | Hours | UX Impact | Notes |
|----|------|-------------------|-------------------|-------|-----------|-------|
| FE-001 | Search stuck at 78% for 130+ seconds | CRITICAL | **CRITICAL** | 12 | Direct user trust erosion | Confirmed. Highest-impact UX debt. Users cannot distinguish "working" from "broken." SSE progress stalls during filtering/LLM phases. Must fix with CROSS-001. |
| FE-002 | `useSearchOrchestration` mega-hook | HIGH | **HIGH** | 16 | Indirect -- regression risk to core UX | Confirmed at 369 lines (not 200+ as DRAFT states). Imports 15 hooks/modules. Decomposition essential for maintainability. |
| FE-003 | ViabilityBadge uses `title` for critical data | HIGH | **RESOLVED** | 0 | N/A | **Already fixed.** `components/ViabilityBadge.tsx` (213 lines) now has a custom `ViabilityTooltip` with `role="tooltip"`, `aria-describedby`, keyboard Enter/Space toggle, Escape dismiss, outside-click dismiss, and tap-to-toggle on mobile. Zero `title` attributes remain. 21 accessibility-related attributes present. Remove from backlog. |
| FE-004 | Divergent auth guard patterns | HIGH | **HIGH** | 8 | Security + UX inconsistency | Confirmed. `/buscar` uses manual `useEffect` redirect (line 37 of useSearchOrchestration), while other protected pages use `(protected)/layout.tsx`. |
| FE-005 | Dual component directory structure | HIGH | **HIGH** | 12 | Developer confusion slows feature velocity | Confirmed: 51 files in `app/components/` vs 33 in `components/`. Reducing estimate from 16h to 12h -- the move is mechanical once the rule is defined. |
| FE-006 | Error 524 exposes technical details | HIGH | **HIGH** | 6 | User anxiety, churn risk | Confirmed. Retry counter (1/3, 2/3, 3/3) signals fragility to users. |
| FE-007 | 12 banners on search page | MEDIUM | **HIGH** (upgrade) | 8 | Cognitive overload on core page | Upgrading. 12 banner types on the most important page is excessive. `BannerStack.tsx` (204 lines) has a priority system but no cap on simultaneous display. Need max 2 visible at once. |
| FE-008 | `/admin` uses useState + manual fetch | MEDIUM | **MEDIUM** | 4 | Stale data for admin users | Confirmed. Low user-facing impact (admin-only). |
| FE-009 | No `aria-live` for dynamic search results | MEDIUM | **MEDIUM** (partially resolved) | 2 | Screen readers miss results | Partially addressed: 28+ `aria-live` usages found in search module (BannerStack, DataQualityBanner, EnhancedLoadingProgress, EmptyResults, ErrorDetail, etc.). Remaining gap: 6 banners still lack `aria-live`, and the primary results count announcement could be more explicit. Reducing from 4h to 2h. |
| FE-010 | `mensagens/page.tsx` at 591 lines | MEDIUM | **MEDIUM** | 8 | Maintainability of messaging feature | Confirmed at exactly 591 lines. |
| FE-011 | Potential `any` types in API proxy routes | MEDIUM | **LOW** (downgrade) | 4 | No direct UX impact | Downgrading. Type safety is a DX concern, not a UX concern. |
| FE-012 | SVG icons lacking `role="img"` or `aria-label` | MEDIUM | **MEDIUM** | 3 | Informational icons invisible to screen readers | Confirmed. Reducing estimate from 4h to 3h -- mostly mechanical audit. |
| FE-013 | Inconsistent landmarks | MEDIUM | **LOW** (downgrade) | 2 | Navigation for assistive tech | Code review found `<main>` in 25+ pages including `(protected)/layout.tsx`, `buscar/page.tsx`, `pipeline/page.tsx`, and all landing pages. Gap is narrower than described: some `id` inconsistency and minor `conta/equipe/` branching issues. Reducing from 4h to 2h. |
| FE-014 | Forms missing `aria-describedby` | MEDIUM | **MEDIUM** | 3 | Form fields lack context for SR users | Confirmed. Reducing from 4h to 3h. |
| FE-015 | `prefers-reduced-motion` not respected | MEDIUM | **LOW** (downgrade, partially resolved) | 2 | Motion-sensitive users | **Partially resolved.** `globals.css` line 349 includes comprehensive `@media (prefers-reduced-motion: reduce)` rule disabling all CSS animations/transitions. `useInView` and `AnimateOnScroll` also check. Only gap: Framer Motion JS-driven animations on landing page. Reducing from 4h to 2h. |
| FE-016 | No ErrorBoundary on SWRProvider/UserProvider | MEDIUM | **MEDIUM** | 3 | App crashes to generic error on provider failure | Confirmed. 7-deep provider hierarchy with no boundary. |
| FE-017 | Frontend feature gates hardcoded | MEDIUM | **LOW** (downgrade) | 3 | No direct UX impact | Downgrading. A `useFeatureFlags` hook already exists fetching from `/api/feature-flags`. This is DX/architecture, not UX. Reducing from 6h to 3h. |
| FE-018 | Dark mode contrast on search form | MEDIUM | **MEDIUM** | 2 | Reduced readability in dark mode | Confirmed. |
| FE-019 | 60+ API proxy routes consolidation | MEDIUM | **LOW** (downgrade) | 6 | No direct UX impact | Downgrading. Purely DX/maintenance concern. |
| FE-020 | No edge caching for stable endpoints | MEDIUM | **MEDIUM** | 2 | Slower page loads for returning users | Confirmed. `/api/setores` and `/api/plans` change monthly at most. |
| FE-021 | Inline SVGs vs lucide-react | LOW | **LOW** | 3 | Minor bundle size | Confirmed. Reducing from 4h to 3h. |
| FE-022 | Raw hex values vs semantic tokens | LOW | **LOW** | 4 | Visual inconsistency risk | Confirmed. Concentrated in secondary components (KeyboardShortcutsHelp, ProfileCongratulations, TestimonialSection). |
| FE-023 | `/conta` redirect flash | LOW | **LOW** | 2 | Momentary flash | Confirmed. |
| FE-024 | Duplicate footers | LOW | **LOW** | 2 | Landmark confusion | Confirmed. |
| FE-025 | RootLayout async for CSP nonce | LOW | **LOW** | 2 | No UX impact | Confirmed. |
| FE-026 | SEO pages thin/duplicate content risk | LOW | **LOW** | 4 | SEO ranking risk | Confirmed. |
| FE-027 | SearchResults.tsx backward-compat re-exports | LOW | **LOW** | 1 | No UX impact | Confirmed. |
| FE-028 | Dark mode brand-blue contrast borderline | LOW | **MEDIUM** (upgrade) | 2 | A11y compliance risk | Upgrading. `#116dff` vs `#121212` at 4.5:1 is the minimum AA threshold. For small text (under 18px) this fails. Brand-blue is used for links and interactive elements which are frequently small text. Use `#3388ff` in dark mode (~5.2:1). |
| FE-029 | Focus order in BuscarModals + BottomNav overlay | LOW | **LOW** | 3 | Modal stacking confusion for keyboard users | Confirmed. |
| FE-030 | Mobile search limited vertical space | LOW | **MEDIUM** (upgrade) | 4 | Mobile conversion impact | Upgrading. Mobile is likely 40-60% of B2G traffic. Search form fills viewport; results invisible without scrolling. |
| FE-031 | Dashboard chart sparse for low-usage users | LOW | **LOW** | 3 | Perception of low value during trial | Confirmed. |
| FE-032 | Pipeline empty state wordy | LOW | **LOW** | 1 | Minor friction | Confirmed. |

**Validation Summary:** 32 debts reviewed. 1 resolved (FE-003). 3 upgraded (FE-007, FE-028, FE-030). 5 downgraded (FE-011, FE-013, FE-015, FE-017, FE-019). 23 confirmed as-is. Net hours saved: ~20h from resolved/reduced items.

---

## Debts Added

| ID | Debt | Severity | Hours | UX Impact | Rationale |
|----|------|----------|-------|-----------|-----------|
| FE-033 | **Landing page excessive hydration** -- All 13 child components of the landing page use `"use client"`, but only 3 actually need Framer Motion. The other 10 use it solely for `useState`/`useEffect`/`useInView`. This forces full client-side hydration of marketing content, degrading TTFB, LCP, and SEO for the primary acquisition surface. | HIGH | 10 | Landing page performance directly affects conversion. Estimated LCP improvement from ~3.5s to ~2.0s. | Identified in Phase 3 frontend spec but missing from DRAFT. |
| FE-034 | **Pipeline kanban missing drag announcements for screen readers** -- `PipelineKanban.tsx` configures `KeyboardSensor` with `sortableKeyboardCoordinates` (keyboard DnD works), but the `DndContext` lacks the `accessibility` prop for `onDragStart`/`onDragOver`/`onDragEnd`/`onDragCancel` announcements, and cards lack `aria-roledescription="sortable"`. | MEDIUM | 4 | Drag-and-drop invisible to screen reader users. Pipeline is a core feature for retained users. | WCAG 2.1 AA requires operable drag-and-drop for assistive technology. |
| FE-035 | **Chart colors not colorblind-safe** -- The 10-color chart palette (`--chart-1` through `--chart-10`) relies entirely on hue differentiation. No patterns, shapes, or data labels supplement the color coding. ~8% of male users have color vision deficiency. | LOW | 4 | Inaccessible data visualization for colorblind users. | Identified in Phase 3 frontend spec Recommendation 12 but omitted from DRAFT. |
| FE-036 | **Shepherd.js loaded eagerly on all protected pages** -- `shepherd.js` (~15KB) is imported in `useShepherdTour.ts` and `useOnboarding.tsx`, loaded on all protected pages regardless of whether the user has already completed the tour. Should use `next/dynamic` for lazy-load. | LOW | 2 | ~15KB unnecessary JS per page load for 95%+ of page views. | Bundle size optimization with clear implementation path. |

---

## Debts Challenged

### FE-003 (ViabilityBadge title attr) -- CHALLENGED: ALREADY RESOLVED

The DRAFT lists this as HIGH severity requiring 4 hours. Upon inspection of `frontend/components/ViabilityBadge.tsx` (213 lines), the component has already been refactored. The code contains explicit comments referencing `DEBT-FE-002` as the fix ticket. The current implementation:

- Uses a custom `ViabilityTooltip` component (not HTML `title`)
- Implements `role="tooltip"` with `useId()`-generated IDs
- Links trigger and tooltip via `aria-describedby`
- Supports keyboard activation (Enter, Space) and Escape dismissal
- Supports tap-to-toggle on mobile via `onClick`
- Dismisses on outside click
- Contains 21 accessibility-related attributes across the component

**Recommendation:** Remove from backlog entirely. Mark as RESOLVED in the final assessment. This saves 4h from the estimate.

### FE-015 (prefers-reduced-motion) -- CHALLENGED: PARTIALLY RESOLVED

The DRAFT describes this as "not systematically respected." This is inaccurate. Evidence from the codebase:

1. `globals.css` line 349-355: `@media (prefers-reduced-motion: reduce)` rule sets `animation-duration: 0.01ms !important` and `transition-duration: 0.01ms !important` on all elements -- the most robust CSS-level approach possible.
2. `hooks/useInView.ts` line 20: Checks `window.matchMedia('(prefers-reduced-motion: reduce)')` and skips animations.
3. `components/ui/AnimateOnScroll.tsx` line 57: Same media query check.

The only remaining gap is Framer Motion's JavaScript-driven animations (primarily on the landing page), which execute outside CSS and are not caught by the global media query rule. Fix is to add `useReducedMotion()` from `framer-motion` to components using `<motion.div>`.

**Recommendation:** Downgrade to LOW, reduce estimate to 2h.

### FE-013 (Inconsistent landmarks) -- CHALLENGED: NARROWER THAN DESCRIBED

Code review found `<main>` elements in 25+ pages, including all critical paths: `(protected)/layout.tsx`, `buscar/page.tsx`, `pipeline/page.tsx`, `alertas/page.tsx`, `status/page.tsx`, `conta/layout.tsx`, and all landing/blog/sobre pages. The actual gap is minor: inconsistent `id` attributes (some use `main-content`, others `buscar-content`, others have no id) and potential `<main>` duplication in conditional branches of `conta/equipe/` pages.

**Recommendation:** Downgrade to LOW, reduce estimate to 2h.

### FE-011 (any types in proxy routes) -- CHALLENGED: NOT A UX DEBT

This is a pure developer experience and type safety concern. Users are never affected by `any` types in API proxy routes. Furthermore, a code search for `: any` in `frontend/app/api/**/*.ts` returned zero confirmed results -- the DRAFT's language was speculative ("potential any types").

**Recommendation:** Downgrade to LOW. Move to System Debt section if retained.

---

## Answers to Architect

### Q1 (Section 7): FE-001 -- Maximum acceptable wait time before showing partial results?

**45 seconds** is the maximum before the UI must change state. Based on B2G user research patterns and web app UX standards:

- **0-15 seconds:** Normal progress animation. Users are patient in this window.
- **15-30 seconds:** Show phase-specific messages. Transition from "Consultando fontes..." to "Filtrando resultados..." resets the user's patience timer. Each phase change signals progress.
- **30-45 seconds:** Show "Classificando relevancia com IA..." message. The mention of AI sets expectations for computational work.
- **45+ seconds:** Prominent "Taking longer than expected" state with three options: (a) "Ver resultados parciais" (primary CTA), (b) "Continuar aguardando" (secondary), (c) "Cancelar busca" (tertiary link). The partial results option should be available as soon as any results have passed filtering.

**Phase-specific messages are essential.** The current "Filtrando resultados" is too vague for a 130-second stall. Users tolerate long waits when they can see progress being made. The distinction between fetching, filtering, classifying, and generating gives users a mental model of the work happening. At 45s, switch from determinate progress bar to an indeterminate animation with phase text -- this prevents the "stuck" perception even when the actual percentage has not changed.

### Q2 (Section 7): FE-007 -- Which banners do users interact with?

Without direct Mixpanel/Clarity data (which should be instrumented), my assessment by UX heuristics and banner type:

**High value (keep always visible):**
1. `SearchErrorBanner` -- Users must know search failed
2. `PartialResultsPrompt` -- Actionable: "Load more results"
3. `SourcesUnavailable` -- Sets expectations about result completeness

**Medium value (show contextually, dismiss on interaction):**
4. `CacheBanner` -- Useful but could be a subtle indicator
5. `FilterRelaxedBanner` -- Actionable: explains why filters were relaxed
6. `DataQualityBanner` -- Informational, can be collapsed

**Low value (candidates for consolidation or removal):**
7. `ExpiredCacheBanner` -- Merge with CacheBanner
8. `TruncationWarningBanner` -- Edge case
9. `RefreshBanner` -- Can be an icon button
10. `OnboardingBanner` -- Only for new users, auto-dismiss
11. `PartialTimeoutBanner` -- Merge with PartialResultsPrompt
12. `TourInviteBanner` -- Only for new users, auto-dismiss

**Consolidation opportunities:**
- `CacheBanner` + `ExpiredCacheBanner` + `RefreshBanner` = single `CacheStatusBanner` with 3 states
- `PartialResultsPrompt` + `PartialTimeoutBanner` = single `PartialBanner` with variants
- `OnboardingBanner` can be replaced by the existing Shepherd.js tour

**Recommendation:** Maximum 2 banners visible simultaneously. The existing `BannerStack` priority system should add a `maxVisible: 2` cap. Error banners suppress all others. Informational banners collapse to a single expandable "N more notifications" row after 5 seconds.

### Q3 (Section 7): FE-005 -- Component directory separation rule?

Yes, the proposed structure aligns with my design system vision, with one refinement -- providers should be extracted into their own directory:

```
components/               # Design system primitives + shared UI
  ui/                     # Button, Input, Label, etc.
  skeletons/              # Loading skeletons
  EmptyState.tsx          # Generic empty states
  ErrorBoundary.tsx       # Error handling
  NavigationShell.tsx     # App shell layout
  Sidebar.tsx             # Desktop nav
  BottomNav.tsx           # Mobile nav
  ViabilityBadge.tsx      # Shared badge

providers/                # NEW directory
  AuthProvider.tsx
  ThemeProvider.tsx
  SWRProvider.tsx
  UserProvider.tsx
  AnalyticsProvider.tsx
  BackendStatusProvider.tsx

app/buscar/components/    # Search domain (already well-organized)
app/components/           # DEPRECATE -- empty and remove
```

**Providers are not components** -- they are infrastructure. They should live in `providers/` at the root level. The `app/components/` directory should be emptied: everything currently there is either a provider (move to `providers/`), a shared component (move to `components/`), or a page-specific component (move to the relevant `app/[page]/components/`).

### Q4 (Section 7): FE-003 -- ViabilityBadge mobile interaction pattern?

**Already resolved.** The current implementation uses tap-to-expand inline, which is the correct choice:

- Bottom sheets (option b) are too heavy for a tooltip -- they interrupt scanning flow
- Separate detail views (option c) navigate away from results, disruptive during comparison
- Inline expand (option a) keeps user in context and allows quick comparison between results

The current `ViabilityTooltip` component toggles via `onClick` on mobile and positions the tooltip below the badge. No further action needed.

One optional enhancement: on mobile, add a subtle info icon next to the first ViabilityBadge a user encounters to teach the tap interaction pattern. After first tap, suppress via localStorage.

### Q5 (Section 7): A11Y-002 -- Should the fix change visual presentation?

**Already resolved** (see FE-003 above). The current tooltip-on-demand pattern is the correct UX choice. An always-visible mini breakdown below each badge would add ~40px vertical space per result card, creating excessive visual noise in the results list. The current hover (desktop) + tap (mobile) pattern balances information density with accessibility.

### Q6 (Section 7): FE-018 -- Dark mode contrast: global or targeted?

**Targeted borders on interactive elements only.** Increasing `--surface-2` globally would change the visual weight of every card, section, and container in dark mode -- a risky visual regression.

Specific fix:
- Add `border border-ink/10` (10% opacity of ink color) to: sector dropdown, date inputs, value range inputs, UF multi-select
- Increase `--surface-2` in dark mode by one step (+5% lightness) ONLY for the search form container
- Do NOT change card surfaces, sidebar, or modal backgrounds

This is a 2-hour change in Tailwind config + 3-4 component files.

### Q7 (Section 7): UX-CRIT-002 -- Silent retry indicator?

Yes, show a subtle progress indicator during silent retries, but make it calming:

- **Silent retry phase (attempts 1-2):** Small pulsing dot (brand-blue, 8px) in the search form header with text "Connecting..." in `--ink-muted` color. No error styling, no red, no counter. This signals "working" without signaling "broken."
- **After silent retries exhausted (attempt 3 failed):** Show error banner with messaging: "Nao foi possivel conectar a fonte de dados. Geralmente isso se resolve sozinho. [Tentar novamente]" -- one calm retry button, no counter, no HTTP codes.
- **Never show:** The word "erro" in the silent retry phase, HTTP status codes, or attempt counters.

### Q8 (Section 7): FE-030 -- Collapse title or description for returning users?

**Collapse the description only, not the title.** The title "Busca de Licitacoes" provides essential wayfinding. The description text ("Encontre oportunidades...") is onboarding copy that returning users do not need.

Implementation:
- **First visit:** Full title + description + sector selector + CTA (current behavior)
- **Returning users** (localStorage flag `has_searched_before`): Title (smaller, `text-lg` instead of `text-xl`) + sector selector + CTA. Description hidden. This recovers ~60px of vertical space on mobile.
- **Onboarding flow:** Always show full version during onboarding auto-search, regardless of `has_searched_before`, because the user is being guided.

The `has_searched_before` flag should be set after the first manual search (not auto-search from onboarding), so the compact header appears from the second visit onward.

---

## Design Recommendations

### Component Architecture

1. **Provider extraction:** Move all 6 providers from `app/components/` to a new `providers/` directory. This is the highest-leverage architectural change for DX clarity.

2. **BannerStack enhancement:** The existing `BannerStack.tsx` already has a priority system. Add: `maxVisible` prop (default 2), auto-collapse for informational banners after 5s, and an expandable "N more notifications" row when banners are suppressed.

3. **useSearchOrchestration decomposition (369 lines -> ~150 lines):**

| Sub-hook to extract | Estimated LOC | Dependencies |
|---------------------|---------------|--------------|
| `useSearchModals` (save, keyboard, upgrade, PDF, trial, payment recovery) | ~60 | planInfo, session |
| `useSearchTours` (search tour, results tour, onboarding coordination) | ~50 | session, trackEvent |
| `useSearchBillingGuard` (trial/plan checks, auth redirect) | ~50 | planInfo, session, authLoading |
| `usePdfGeneration` (PDF modal, loading, download) | ~40 | session, searchId, sectorName |

The remaining `useSearchOrchestration` becomes a ~150-line compositor that imports these 4 hooks + `useSearchFilters` + `useSearch` and assembles the `searchResultsProps` return value.

### Design System

1. **Dark mode brand-blue variant:** Define `--brand-blue-dark: #3388ff` for dark mode small text. Keep `#116dff` for large text and filled backgrounds. This fixes FE-028 at the token level.

2. **Dark mode form input borders:** Establish a rule: all form inputs in dark mode must have `border border-ink/10` minimum. Apply via Tailwind config extension.

3. **Badge component standardization:** Extract shared pattern from ViabilityBadge, ReliabilityBadge, LlmSourceBadge, and plan badges into a generic `Badge` primitive with props for color, icon, size, and tooltip content.

### Accessibility

1. **Results count announcement:** Add `<span aria-live="polite" className="sr-only">` to `ResultsHeader` that updates when results arrive: "{count} oportunidades encontradas".

2. **SVG classification audit:** Classify all inline SVGs as decorative (`aria-hidden="true"`) or informational (`role="img" aria-label="..."`). Priority: status icons in `/historico` and `/mensagens` that may carry meaning.

3. **Pipeline drag announcements:** Add `accessibility` prop to `DndContext` with Portuguese-language announcements for drag start/over/end/cancel events. Add `aria-roledescription="item ordenavel"` to pipeline cards.

4. **Automated a11y testing expansion:** `@axe-core/playwright` is already a devDependency with tests in `e2e-tests/accessibility-audit.spec.ts`. Expand coverage to onboarding, conta, mensagens, and admin pages.

### Performance UX

1. **Landing page Server Component conversion:** Convert 10 of 13 landing page child components from `"use client"` to Server Components. Only HeroSection (interactive CTA), SectorsGrid (dynamic), and AnalysisExamplesCarousel (animation) need client-side JS. Estimated LCP improvement: ~3.5s to ~2.0s.

2. **Edge caching:** Add `Cache-Control: public, s-maxage=3600, stale-while-revalidate=86400` to `/api/setores` and `/api/plans`. Eliminates ~100ms per search page load for returning users.

3. **Shepherd.js lazy loading:** Wrap import in `next/dynamic` to load only when tour is activated. Saves ~15KB per page view for the 95%+ of views where the tour is not needed.

---

## Resolution Order Recommended

Ordered by user impact, considering dependencies between items.

### Sprint 1 -- User Trust and Acquisition (P0, ~36h)

| Priority | ID | Debt | Hours | Justification |
|----------|-----|------|-------|---------------|
| 1 | FE-001 + CROSS-001 | Search stuck at 78% -- add phase-specific progress events + "longer than expected" UI | 12 | Highest UX impact. Users closing tabs during legitimate searches = lost trials. |
| 2 | FE-006 | Error 524 silent retry + calm messaging | 6 | Second highest anxiety-inducing UX issue. |
| 3 | FE-007 | Banner consolidation -- max 2 visible, priority suppression | 8 | Cognitive overload on the core page. |
| 4 | FE-033 | Landing page RSC conversion (10 of 13 components) | 10 | Landing LCP directly affects trial signups. |

### Sprint 2 -- Architecture and Security (P1, ~38h)

| Priority | ID | Debt | Hours | Justification |
|----------|-----|------|-------|---------------|
| 5 | FE-004 | Unify auth guard patterns | 8 | Security debt. Must resolve before scaling. |
| 6 | FE-005 | Component directory consolidation + provider extraction | 12 | Enables all future frontend work. |
| 7 | FE-002 | Decompose useSearchOrchestration | 16 | Depends on FE-005 (clear structure). Enables FE-004 (auth extraction). |
| 8 | FE-028 | Dark mode brand-blue contrast fix | 2 | WCAG AA compliance gap, trivial to fix. |

### Sprint 3 -- Accessibility and Polish (P2, ~33h)

| Priority | ID | Debt | Hours | Justification |
|----------|-----|------|-------|---------------|
| 9 | FE-030 | Mobile search compact header for returning users | 4 | Mobile conversion improvement. |
| 10 | FE-009 | Complete aria-live on remaining banners + results count | 2 | Screen reader accessibility for core feature. |
| 11 | FE-034 | Pipeline kanban drag announcements | 4 | Screen reader accessibility for retained users. |
| 12 | FE-012 | SVG accessibility audit | 3 | WCAG compliance. |
| 13 | FE-014 | Forms aria-describedby | 3 | WCAG compliance. |
| 14 | FE-010 | Decompose mensagens/page.tsx | 8 | Maintainability of second most complex page. |
| 15 | FE-016 | ErrorBoundary on provider stack | 3 | Resilience. |
| 16 | FE-018 | Dark mode form contrast | 2 | Readability. |
| 17 | FE-020 | Edge caching for stable endpoints | 2 | Performance with minimal effort. |
| 18 | FE-008 | Admin page SWR migration | 4 | Consistency. |

### Backlog (P3, ~44h)

FE-013 (2h), FE-015 (2h), FE-017 (3h), FE-021 (3h), FE-022 (4h), FE-023 (2h), FE-024 (2h), FE-025 (2h), FE-026 (4h), FE-027 (1h), FE-029 (3h), FE-031 (3h), FE-032 (1h), FE-035 (4h), FE-036 (2h). Also FE-011 (4h) and FE-019 (6h) which are DX concerns not UX.

**Total: ~151h** (36 + 38 + 33 + 44) across 35 items (32 original - 1 resolved + 4 added).

---

## Risk Assessment

### R-UX-001: Trial Conversion Loss from Search UX Issues (HIGH)

**Debts:** FE-001, FE-006, FE-007
**Risk:** During the 14-day trial, if a user's first 2-3 searches hit the "stuck at 78%" issue or an error 524 with technical retry counters, conversion probability drops sharply. B2G users are busy professionals who will not troubleshoot or wait 2+ minutes for a search that appears broken.
**Quantified impact:** Assuming 20% of searches hit the long-running path and 50% of those users abandon, approximately 10% of trial users may have a degraded first experience.
**Mitigation:** Sprint 1 items (FE-001, FE-006, FE-007).

### R-UX-002: Acquisition Performance from Landing Page Hydration (HIGH)

**Debt:** FE-033
**Risk:** The landing page is the primary acquisition surface. All 13 child components using `"use client"` forces full client-side hydration of marketing content. Estimated LCP ~3.5s vs target ~2.0s. Every 100ms of load time reduces conversion by ~1% (industry research). A 1.5s gap represents a meaningful conversion loss.
**Mitigation:** Sprint 1 item (FE-033). Convert 10 components to Server Components.

### R-UX-003: Accessibility Legal Exposure (MEDIUM)

**Debts:** FE-028, FE-009, FE-012, FE-014, FE-034, FE-035
**Risk:** Brazilian Lei 13.146/2015 (Lei Brasileira de Inclusao) requires digital accessibility. SmartLic interfaces with government procurement systems and targets B2G companies -- the exact domain where accessibility compliance is scrutinized. The brand-blue contrast failure (FE-028) for small text and missing pipeline drag announcements (FE-034) are the most visible gaps.
**Mitigation:** Sprint 2 (FE-028) and Sprint 3 (FE-009, FE-012, FE-014, FE-034) items.

### R-UX-004: Auth Guard Divergence Leading to Data Exposure (HIGH)

**Debt:** FE-004
**Risk:** The dual auth pattern creates a window where a code change to `(protected)/layout.tsx` is not reflected in `/buscar`'s manual `useEffect` check, potentially exposing search data to unauthenticated users.
**Mitigation:** Sprint 2 (FE-004). Treat as security fix, not UX cleanup.

### R-UX-005: Mobile User Abandonment (MEDIUM)

**Debts:** FE-030, FE-029
**Risk:** If B2G users access SmartLic from mobile during field visits, the current search experience where the form fills the entire viewport and results require scrolling may cause abandonment. Users may not realize the search produced results below the fold.
**Mitigation:** Sprint 3 (FE-030).

### R-UX-006: Developer Velocity Degradation (LOW, compounding)

**Debts:** FE-002, FE-005, FE-010
**Risk:** The 369-line mega-hook, dual component directories, and 591-line page file slow down every frontend feature addition. As the product grows, this velocity drag compounds. New developers will struggle with the ambiguous component structure.
**Mitigation:** Sprint 2 (FE-005, FE-002) and Sprint 3 (FE-010).

---

*Review completed 2026-03-31 by @ux-design-expert (Uma) as Phase 6 of Brownfield Discovery workflow.*
*Previous draft review (2026-03-30) superseded by this version -- updated to cover all 32 DRAFT items (FE-001 through FE-032), answer all 8 architect questions, and reflect latest code verification.*
*Next: Phase 7 (@qa gate review).*
