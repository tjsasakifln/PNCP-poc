# UX Specialist Review -- v2.0 Technical Debt DRAFT

**Reviewer:** @ux-design-expert (Pixel)
**Date:** 2026-02-15
**Status:** REVIEWED
**Reviewed Document:** `docs/prd/technical-debt-DRAFT.md` v2.0 (Sections 3, 4, 6)
**Reference Document:** `docs/frontend/frontend-spec.md` (Phase 3 spec)
**Previous Review:** `docs/reviews/ux-specialist-review.md` v1.0 (2026-02-11, @Uma)
**Codebase Commit:** `b80e64a` (branch `main`)

---

## Context

This review validates the Frontend/UX section (Section 3) of the consolidated v2.0 DRAFT. The v2.0 DRAFT restructured the debt IDs from the v1.0 scheme (FE-C01, FE-H03, etc.) into a new scheme (FE-01 through FE-21, A11Y-01 through A11Y-09, UX-01 through UX-05, IC-01 through IC-07, MF-01 through MF-04). Several items from the v1.0 review were resolved or restructured. This review validates all 45 items in the new structure.

**Key changes since v1.0 review (2026-02-11):**
- FE-C01 (buscar monolith ~1100 lines) was RESOLVED -- decomposed to 384 lines + sub-components + hooks
- FE-H04 (native alert()) was RESOLVED -- toast system now in place
- FE-M08 (no middleware auth guards) was RESOLVED -- `middleware.ts` with Supabase SSR
- Several v1.0 items were reorganized/renumbered in the new structure
- New items emerged from the decomposition (prop drilling in new sub-components)

---

## 1. Debitos Validados

### 1.1 Technical Debt (HIGH) -- FE-01 through FE-04

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| FE-01 | SearchForm receives ~40 props via prop drilling | HIGH | **HIGH** (confirmed) | 16h | P2 | **High** -- Maintenance cost prevents iterative UX improvements. Every filter change cascades through 4 layers. Confirmed: `SearchFormProps` interface is 84 lines (lines 18-102) with 42 named props. |
| FE-02 | SearchResults receives ~35 props via prop drilling | HIGH | **HIGH** (confirmed) | 16h | P2 | **High** -- Same prop drilling anti-pattern. Confirmed: `SearchResultsProps` interface is 73 lines (lines 21-94) with ~35 named props. This was CREATED by the buscar decomposition that resolved FE-C01. Ironic but expected -- the decomposition moved complexity from inline code to interfaces. |
| FE-03 | `useSearchFilters` is 528 lines with 40+ state variables | HIGH | **HIGH** (confirmed) | 16h | P2 | **High** -- Impossible to test/debug individual filter behavior. Confirmed: file starts with term validation logic, then a massive hook. Splitting is the prerequisite for testability. |
| FE-04 | 17 test files quarantined in `__tests__/quarantine/` | HIGH | **HIGH** (confirmed) | 24h | P2 | **Medium** -- Indirectly affects UX because regressions ship undetected. Confirmed: 22 files in quarantine (not 17 as stated). Includes AuthProvider, useSearch, useSearchFilters, DashboardPage, MensagensPage, ContaPage, LicitacaoCard, LicitacoesPreview. The actual count should be corrected to 22 in the DRAFT. |

**Assessment note on FE-01/FE-02:** These two items are a direct consequence of resolving the old FE-C01 (buscar monolith). The monolith was correctly decomposed into sub-components, but the state was not lifted into a Context provider. The decomposition stopped at step 1 of 2: (1) extract components [done], (2) extract shared state into Context [not done]. This is architectural debt, not UX debt per se, but it blocks future UX iteration. The 16h estimate per item is accurate only if done together with FE-03; if done in isolation, each is 8h.

### 1.2 Accessibility (HIGH) -- A11Y-01, A11Y-02

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| A11Y-01 | Modal dialogs (save search, keyboard help) lack focus trap | HIGH | **HIGH** (confirmed) | 4h | P1 | **High** -- WCAG 2.4.3 Focus Order violation. Confirmed: save search dialog at `buscar/page.tsx` lines 238-274 is a `<div>` with `fixed inset-0 z-50` but no focus trap. User can Tab behind the overlay. Keyboard help dialog at lines 277-350 has the same issue. The UpgradeModal at `components/UpgradeModal.tsx` DOES have `aria-modal="true"` and `role="dialog"` (lines 119-120), proving the team knows the pattern but did not apply it consistently. |
| A11Y-02 | Modals do not use `role="dialog"` or `aria-modal="true"` | HIGH | **HIGH** (confirmed) | 4h | P1 | **High** -- WCAG 4.1.2 Name/Role/Value violation. Confirmed: save search dialog and keyboard help dialog both lack `role="dialog"` and `aria-modal`. However, `UpgradeModal.tsx` (line 119-120) and `CookieConsentBanner.tsx` (line 77) already implement this correctly. The fix is to replicate the pattern from UpgradeModal. Estimate: 2h (not 4h) since the pattern exists in-codebase. |

**Combined A11Y-01 + A11Y-02 assessment:** These two items share the same root cause (ad-hoc modal implementation instead of a reusable dialog primitive). Fixing them together takes 4h total, not 8h. The co-implementation cluster in Section 5 of the DRAFT correctly identifies this.

### 1.3 Technical Debt (MEDIUM) -- FE-05 through FE-12

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| FE-05 | Inline SVGs duplicated across 20+ files | MEDIUM | **MEDIUM** (confirmed) | 8h | P3 | **Low** -- Bundle bloat, not user-visible. Confirmed: 162 SVG/viewBox occurrences across 30+ files. lucide-react is installed but only used in 5 files. The gap between "installed" and "adopted" is significant. |
| FE-06 | Sector list hardcoded in two places | MEDIUM | **MEDIUM** (confirmed) | 4h | P3 | **Low** -- Risk of sector drift between signup and search. Not currently drifted but will as sectors evolve. |
| FE-07 | No dynamic imports for heavy dependencies | MEDIUM | **MEDIUM** (confirmed) | 8h | P2 | **Medium** -- Confirmed: zero `next/dynamic` or `React.lazy` usage anywhere in the frontend. recharts (~200KB), @dnd-kit (3 packages), framer-motion (~40KB), and shepherd.js are all static imports. This degrades LCP for first-time visitors. |
| FE-08 | Error boundary button uses `--brand-green` not defined in tokens | MEDIUM | **HIGH** (upgraded) | 1h | P0 | **High** -- Confirmed: `app/error.tsx` line 67 uses `bg-[var(--brand-green)]` which is NOT defined anywhere in `globals.css`. In production, this resolves to `background-color: var(--brand-green)` which is unset, meaning the button renders with NO visible background. Users hitting an error see a button that appears invisible or text-only. This is the error page -- the worst place for a broken CTA. Upgrade to HIGH with P0 priority. Quick win: replace with `bg-[var(--brand-navy)]` or `bg-[var(--brand-blue)]`. |
| FE-09 | No tests for SearchResults.tsx (678 lines) | MEDIUM | **MEDIUM** (confirmed) | 16h | P2 | **Medium** -- Indirectly affects UX via undetected regressions. The component has multiple conditional render paths (loading, error, empty, results, degraded, partial, cache stale). |
| FE-10 | No tests for pipeline drag-and-drop | MEDIUM | **MEDIUM** (confirmed) | 8h | P3 | **Low** -- Pipeline is a secondary feature with lower traffic. |
| FE-11 | No tests for onboarding wizard flow | MEDIUM | **MEDIUM** (confirmed) | 8h | P3 | **Low** -- Onboarding is one-time per user. Testing matters but is lower priority than search. |
| FE-12 | No tests for middleware.ts route protection | MEDIUM | **MEDIUM** (confirmed) | 8h | P3 | **Medium** -- Auth guard bugs are immediately user-visible (flash of protected content or incorrect redirects). |

### 1.4 Accessibility (MEDIUM) -- A11Y-03 through A11Y-05

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| A11Y-03 | Custom dropdowns (CustomSelect) may not announce selection changes | MEDIUM | **MEDIUM** (confirmed) | 4h | P3 | **Medium** -- AT users miss selection feedback. CustomSelect uses `<div>` with `role="combobox"` pattern. Needs `aria-activedescendant` and `aria-selected` on options. |
| A11Y-04 | Pull-to-refresh has no keyboard alternative | MEDIUM | **LOW** (downgraded) | 4h | P3 | **Low** -- Pull-to-refresh is disabled on desktop (`max-width: 767px`). Mobile keyboard users are extremely rare. The regular search button provides the same functionality. This is not a blocking issue. |
| A11Y-05 | Shepherd.js onboarding may block content without `inert` attribute | MEDIUM | **MEDIUM** (confirmed) | 4h | P3 | **Medium** -- During the onboarding tour, background content remains interactive. The `inert` attribute on the rest of the page would prevent interaction. |

### 1.5 UX Issues (MEDIUM) -- UX-01 through UX-05

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| UX-01 | Search button below the fold on desktop with accordion open | MEDIUM | **MEDIUM** (confirmed) | 4h | P2 | **Medium** -- Primary CTA not visible. The search button should be sticky or a FAB (floating action button) should appear when the button scrolls out of view. The mobile sticky behavior (`sticky bottom-4 sm:bottom-auto`) already exists but is disabled on desktop. Extend it to desktop. |
| UX-02 | Keyboard shortcuts modal lacks focus trap; Escape conflict | MEDIUM | **MEDIUM** (confirmed) | 4h | P1 | **Medium** -- This is the same root cause as A11Y-01. The keyboard help modal at `buscar/page.tsx` lines 277-350 has no focus trap, no `role="dialog"`, and the Escape key handler calls `limparSelecao()` (clear UF selection) instead of dismissing the modal. Confirmed: the global Escape handler in `useKeyboardShortcuts` fires before the modal's close handler. Fix: use capture-phase event listener on the modal (like UpgradeModal does at line 45). |
| UX-03 | Pricing page annual shows "9.6x" multiplier | MEDIUM | **HIGH** (upgraded) | 4h | P1 | **High** -- Confirmed: `planos/page.tsx` lines 546, 555, 702, 738 all use `price_brl * 9.6`. Line 738 literally says "12 meses pelo preco de 9.6" which makes no mathematical sense to users. The 9.6 comes from 12 months * 0.8 (20% discount), but displaying this as a multiplier is confusing. Users will think "9.6 what? 9.6 months? 9.6x the price?" This is a trust issue. Upgrade to HIGH. |
| UX-04 | Pipeline page not optimized for mobile | MEDIUM | **MEDIUM** (confirmed) | 16h | P3 | **Medium** -- Confirmed: `pipeline/page.tsx` line 146 uses `flex gap-4 overflow-x-auto` which creates horizontal scroll on mobile. The columns do not collapse into a vertical list. Drag-and-drop on touch is functional (PointerSensor with `distance: 8`) but awkward in horizontal scroll. |
| UX-05 | Admin page table not responsive | MEDIUM | **LOW** (downgraded) | 8h | P3 | **Low** -- Admin page is used by 1-2 people. The table is functional with horizontal scroll. Not worth 8h for such a small audience. Consider 2h for a card-based mobile view in the future. |

### 1.6 Technical Debt (LOW) -- FE-13 through FE-21

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| FE-13 | Auth guard duplicated between middleware.ts and (protected)/layout.tsx | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Middleware handles the real guard. The layout guard is redundant belt-and-suspenders. No user impact unless they conflict. |
| FE-14 | Console.log statements in AuthProvider | LOW | **LOW** (confirmed) | 1h | P3 | **Low** -- Confirmed: 5 `console.log` statements at lines 254-258, 274 for Google OAuth debugging. These leak to production console. Not user-facing but professional polish issue. |
| FE-15 | `useEffect` missing dependencies with eslint-disable | LOW | **LOW** (confirmed) | 8h | P3 | **Low** -- Confirmed: 4 occurrences across `login/page.tsx`, `planos/page.tsx`, `redefinir-senha/page.tsx`, `planos/obrigado/page.tsx`. Not directly causing visible bugs currently, but could cause stale closure issues on complex interactions. |
| FE-16 | Search state uses `window.location.href` instead of router.push | LOW | **LOW** (confirmed) | 2h | P3 | **Low** -- Confirmed: 17+ occurrences of `window.location.href` across the app. Many are legitimate (OAuth callbacks, Stripe checkout redirect). The ones in `useSearch.ts` lines 297, 405 (redirect to login on 401) cause full page reloads. Not ideal but functional. |
| FE-17 | PLAN_HIERARCHY and PLAN_FEATURES hardcoded in planos/page.tsx | LOW | **MEDIUM** (upgraded) | 4h | P2 | **Medium** -- Confirmed: `planos/page.tsx` lines 34-46 define `PLAN_HIERARCHY` and lines 55+ define `PLAN_FEATURES`, while `lib/plans.ts` has `PLAN_CONFIGS` with overlapping data. This duplication means plan changes require edits in two files, risking price/feature display drift. Upgrade because price consistency directly affects user trust. |
| FE-18 | `next.config.js` uses CommonJS | LOW | **LOW** (confirmed) | 2h | P3 | **None** -- Internal developer experience. |
| FE-19 | Pull-to-refresh CSS hack | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Fragile but currently working. |
| FE-20 | CSS class `sr-only` hardcoded inline in layout.tsx skip-nav | LOW | **LOW** (confirmed) | 1h | P3 | **None** -- Confirmed at line 96. The skip-nav link uses `className="sr-only focus:not-sr-only ..."` which is the standard Tailwind pattern. This is actually correct -- not a real debt item. The `sr-only` class IS a Tailwind utility. Consider removing this from the debt list. |
| FE-21 | `dangerouslySetInnerHTML` for theme script | LOW | **LOW** (confirmed) | 1h | P3 | **None** -- Legitimate FOUC prevention technique. Confirmed at `layout.tsx` lines 73-89. The script only reads localStorage and adds a CSS class. No user input involved. Not a real debt item. |

**Items to remove from DRAFT:** FE-20 and FE-21 are not actual debts. FE-20 uses Tailwind's `sr-only` utility correctly. FE-21 is a documented intentional pattern. Recommend removing both to avoid inflating the count.

### 1.7 UX Inconsistencies (LOW) -- IC-01 through IC-07

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| IC-01 | Hardcoded "SmartLic" in header despite APP_NAME env var | LOW | **LOW** (confirmed) | 1h | P3 | **Low** -- Confirmed: `buscar/page.tsx` line 27 defines `APP_NAME` from env, but line 123 hardcodes `SmartLic<span>.tech</span>`. The hardcoded version includes the styled `.tech` suffix, which the env var does not provide. This is intentional branding with a styled domain suffix. Not a true inconsistency -- the styled version is design-intentional. Consider keeping the hardcoded version and documenting why. |
| IC-02 | Mixed color approaches (Tailwind tokens vs inline CSS vars) | LOW | **LOW** (confirmed) | 4h | P3 | **None** -- Visually identical output. Developer experience issue only. |
| IC-03 | Icon sources mixed (lucide-react vs inline SVGs) | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- lucide-react is only used in 5 files despite being installed. The vast majority of icons are inline SVGs. |
| IC-04 | Loading spinner styles vary | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Minor visual inconsistency. Not disruptive. |
| IC-05 | Link vs anchor tag mixed for internal navigation | LOW | **LOW** (confirmed) | 2h | P3 | **Low** -- Causes full page reloads on some navigation. Related to FE-16. |
| IC-06 | Error message translation only in login page | LOW | **MEDIUM** (upgraded) | 8h | P2 | **Medium** -- Confirmed: login page has comprehensive error translation (Supabase error messages to Portuguese). Other pages show raw backend errors in English/technical language. This creates a jarring inconsistency. Example: login shows "E-mail ou senha incorretos" but a search error shows "Failed to fetch" or "502 Bad Gateway". Upgrade because error messages are a critical trust touchpoint. |
| IC-07 | Max-width container varies | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Intentional per-page variation. Search needs narrower focus (4xl), admin needs wider (7xl), landing uses custom (1200px). This is acceptable design variation, not inconsistency. Consider documenting the rationale rather than normalizing. |

### 1.8 Missing UX Feedback (LOW) -- MF-01 through MF-04

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| MF-01 | No unsaved changes confirmation when leaving mid-search | LOW | **MEDIUM** (upgraded) | 4h | P2 | **Medium** -- Users who execute a search, then navigate to `/planos` or `/historico`, lose their results with no warning. The search can take 15-60 seconds. Losing results silently after a long wait is frustrating. Use `beforeunload` event or Next.js route change listener. |
| MF-02 | No "Copied to clipboard" feedback | LOW | **LOW** (confirmed) | 2h | P3 | **Low** -- Minor feedback gap. sonner toast can be added trivially. |
| MF-03 | Pipeline drag-and-drop no haptic/audio feedback on mobile | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Nice-to-have for mobile pipeline users (small audience). |
| MF-04 | Sector change does not confirm results were cleared | LOW | **LOW** (confirmed) | 2h | P3 | **Low** -- Minor feedback gap. A toast or subtle animation would suffice. |

### 1.9 Accessibility (LOW) -- A11Y-06 through A11Y-09

| ID | Debito | Severidade Original | Severidade Ajustada | Horas | Prioridade | Impacto UX |
|----|--------|---------------------|---------------------|-------|------------|------------|
| A11Y-06 | UF buttons use `title` but no `aria-label` | LOW | **LOW** (confirmed) | 2h | P3 | **Low** -- Most AT reads `title`. Adding `aria-label` is belt-and-suspenders. |
| A11Y-07 | Keyboard shortcuts no way to disable/customize | LOW | **LOW** (confirmed) | 4h | P3 | **Low** -- Power user feature. Conflict risk with browser shortcuts is real but low frequency. |
| A11Y-08 | Some SVG icons use generic `aria-label="Icone"` | LOW | **MEDIUM** (upgraded) | 2h | P3 | **Medium** -- Confirmed: `planos/page.tsx` line 366 has `aria-label="Icone"` on a shield/checkmark icon that conveys "verified/secure" semantics. Generic labels provide no useful information to AT users. Fix: either make decorative (`aria-hidden="true"`) or use descriptive label. |
| A11Y-09 | Dark mode `--ink-muted` at 4.9:1 borderline AA | LOW | **LOW** (confirmed) | 1h | P3 | **Low** -- 4.9:1 passes AA threshold (4.5:1 minimum). Technically compliant. Improving to 5.5:1+ would be better but not required. |

---

## 2. Debitos Adicionados

The following UX issues are present in the current codebase but were NOT included in the v2.0 DRAFT. Some were identified in the v1.0 review and may have been inadvertently dropped during consolidation. Others are new findings.

| ID | Debito | Severidade | Localizacao | Horas | Impacto UX |
|----|--------|-----------|-------------|-------|------------|
| UX-NEW-01 | **Save search dialog and keyboard help dialog both lack `role="dialog"`, `aria-modal`, AND focus trap** -- These are inline `<div>` modals in `buscar/page.tsx` (lines 238-274, 277-350) that were created during the buscar decomposition but without the accessibility patterns already established in `UpgradeModal.tsx`. | HIGH | `buscar/page.tsx` lines 238-350 | 3h | High -- Three WCAG violations in the two most frequently used dialogs. Co-fix with A11Y-01 and A11Y-02. |
| UX-NEW-02 | **Pricing page "9.6" multiplier appears in user-visible text** -- Line 738: "12 meses pelo preco de 9.6" is displayed as a footnote. Users have no context for what "9.6" means. This is a raw calculation artifact leaking into copy. | HIGH | `planos/page.tsx` line 738 | 1h | High -- Confusing financial information. This is a subset of UX-03 but specifically the copy issue is worse than the mathematical display. |
| UX-NEW-03 | **Admin page uses native `confirm()` dialog** -- `admin/page.tsx` line 131 uses `window.confirm()` for user deletion. This is the same anti-pattern that was fixed for FE-H04 (native alert). The deletion confirmation should use a proper modal with clear consequences explained. | MEDIUM | `admin/page.tsx` line 131 | 2h | Medium -- Destructive action gated by a browser-native dialog that cannot be styled and feels alien to the app. |
| UX-NEW-04 | **No empty state for pipeline page** -- When the pipeline has zero items, the page shows an empty grid of column headers with no items. No guidance on how to add items (the AddToPipelineButton is on the search results page). | LOW | `pipeline/page.tsx` | 2h | Low -- First-time pipeline users see empty columns with no explanation. |
| UX-NEW-05 | **Pipeline column count forces horizontal scroll on tablet** -- 5 columns (prospecting, analyzing, decided, won, lost) in a `flex gap-4` layout. On screens 768-1024px, the last 1-2 columns are off-screen. No scroll indicator. | MEDIUM | `pipeline/page.tsx` line 146 | 2h | Medium -- Tablet users may not discover the last columns exist. |

---

## 3. Respostas ao Architect

### Q1: A11Y-01/A11Y-02 -- Radix UI vs custom modal approach?

**Recommendation: Create a lightweight `<DialogPrimitive>` component rather than installing `@radix-ui/react-dialog`.**

Rationale:
1. `@radix-ui/react-dialog` is an excellent library, but the project has zero Radix UI packages currently. Adding one opens the door to adopting the full Radix primitive set, which is a larger architectural decision.
2. The project already has a working modal pattern in `UpgradeModal.tsx` (lines 34-51) that correctly implements: Escape key handling with capture-phase listener, body scroll lock, `aria-modal="true"`, `role="dialog"`, and `aria-labelledby`.
3. What is MISSING from UpgradeModal is only the focus trap. Adding a focus trap requires ~30 lines of code (trap focus between first and last focusable element on Tab/Shift+Tab).

**Recommended approach:**
```
1. Extract a <Dialog> component from UpgradeModal.tsx that provides:
   - Fixed overlay with backdrop
   - role="dialog" + aria-modal="true"
   - aria-labelledby pointing to title element
   - Escape to close (capture phase, stopPropagation)
   - Body scroll lock
   - Focus trap (new)
   - Render via React Portal (optional, for z-index safety)

2. Refactor UpgradeModal, save search dialog, and keyboard help dialog
   to use the shared <Dialog> component.

3. Total effort: 4h (2h for Dialog primitive, 2h for 3 refactors)
```

If the team later decides to adopt Radix UI broadly (for dropdowns, popovers, tooltips, etc.), the custom Dialog can be replaced. But for now, one component does not justify a dependency.

### Q2: FE-01/FE-02/FE-03 -- State management refactor pattern?

**Recommendation: React Context + useReducer. Not Zustand.**

Rationale:
1. **Zustand** is excellent for global state, but the search state is page-scoped (only used in `/buscar`). Adding a global state library for page-local state is over-engineering.
2. **React Context + Provider** scoped to the `/buscar` route group provides the right boundary. The context dies when the user navigates away from search, which is the correct behavior.
3. **useReducer** instead of 40+ `useState` calls brings three benefits:
   - Single dispatch function replaces 40 setter props
   - Reducer logic is independently testable (pure function)
   - Actions are self-documenting (`dispatch({ type: 'SET_UF', uf: 'SP' })`)

**Implementation pattern:**
```
buscar/
  context/
    SearchContext.tsx          -- createContext + Provider wrapper
    searchReducer.ts           -- Pure reducer function (testable)
    searchActions.ts           -- Action type definitions
  hooks/
    useSearchState.ts          -- useContext(SearchContext) + selectors
    useUfSelection.ts          -- UF-specific logic (extracted from useSearchFilters)
    useDateRange.ts            -- Date-specific logic
    useTermSearch.ts           -- Term validation + management
    useAdvancedFilters.ts      -- Modalidade, esfera, municipio, valor, status
  components/
    SearchForm.tsx             -- Props: none (reads from context)
    SearchResults.tsx           -- Props: none (reads from context)
    FilterPanel.tsx            -- Props: none (reads from context)
```

**Key migration rules:**
- SearchForm and SearchResults receive ZERO props (they consume context directly)
- The `buscar/page.tsx` wraps children in `<SearchProvider>` and becomes a pure layout component
- Each sub-hook (`useUfSelection`, `useDateRange`, etc.) dispatches actions to the reducer
- The reducer is a pure function that can be unit-tested without React

**Estimated effort:** 32h total (not 48h as the sum of FE-01+FE-02+FE-03 suggests), because the three items share the same refactor work.

### Q3: UX-04 -- Pipeline mobile approach?

**Recommendation: Convert to a sortable vertical list below 768px. Do NOT try to make horizontal DnD work on mobile.**

Rationale:
1. Horizontal scrolling Kanban is fundamentally broken on mobile. Users cannot see the full board, discover hidden columns, or drag across columns without precisely coordinated horizontal scroll + vertical drag gestures.
2. @dnd-kit already supports `SortableContext` with vertical lists. The same data model works; only the visual layout changes.
3. The 5 columns should become 5 collapsible sections in a vertical list, with a count badge showing items per section.

**Mobile layout (below 768px):**
```
[Prospeccao (3)]        -- Collapsible section header
  Card 1                -- Tappable to expand/manage
  Card 2
  Card 3
[Analise (2)]           -- Collapsed by default
[Decidida (1)]
[Ganha (0)]             -- Shows empty state
[Perdida (0)]
```

**How to move items between stages on mobile:**
- Each card gets a "Mover para..." dropdown (or bottom sheet) instead of drag-and-drop
- This is actually FASTER on mobile than dragging
- @dnd-kit's touch sensors can be kept for larger tablets (1024px+)

**Estimated effort:** 16h is accurate. Breakdown: 8h for responsive layout + collapsible sections, 4h for "move to" action menu, 4h for testing across devices.

### Q4: IC-06 -- i18n plan?

**Recommendation: Do NOT invest in full i18n framework now. Instead, create a centralized error message dictionary.**

Rationale:
1. SmartLic serves exclusively Brazilian users. There is no near-term plan for English, Spanish, or other languages.
2. The immediate problem is not i18n -- it is that error messages from the backend are shown raw in Portuguese technical language or English. The login page already has a translation map (Supabase error codes to Portuguese). This pattern should be extended to ALL API error paths.
3. A full i18n framework (next-intl, react-i18next) adds complexity that is not justified for a single-language product.

**Recommended approach:**
```typescript
// lib/error-messages.ts
const ERROR_MESSAGES: Record<string, string> = {
  // HTTP status codes
  '401': 'Sua sessao expirou. Faca login novamente.',
  '403': 'Voce nao tem permissao para esta acao.',
  '404': 'Recurso nao encontrado.',
  '429': 'Muitas requisicoes. Aguarde um momento.',
  '500': 'Erro interno do servidor. Tente novamente.',
  '502': 'Servico temporariamente indisponivel.',
  '503': 'Portal PNCP temporariamente indisponivel.',
  '504': 'Tempo limite excedido. Tente com menos estados.',

  // Backend error codes
  'DATE_RANGE_EXCEEDED': 'Periodo de busca excede o limite do seu plano.',
  'RATE_LIMIT': 'Limite de requisicoes atingido.',
  'QUOTA_EXCEEDED': 'Cota mensal esgotada.',
  'SUBSCRIPTION_REQUIRED': 'Assine um plano para acessar.',

  // Generic fallback
  'UNKNOWN': 'Ocorreu um erro inesperado. Tente novamente.',
};

export function translateError(error: string | number): string {
  return ERROR_MESSAGES[String(error)] || ERROR_MESSAGES['UNKNOWN'];
}
```

**Estimated effort:** 4h (create dictionary + apply to 5-6 API call sites), not 8h.

### Q5: FE-07 -- Dynamic import priorities?

**Priority order for `next/dynamic` implementation:**

| Priority | Library | Approx Size | Page(s) | Rationale |
|----------|---------|-------------|---------|-----------|
| 1 | **recharts** | ~200KB gzipped | `/dashboard` | Largest single dependency. Only used on one page. Users who never visit dashboard should not pay this cost. |
| 2 | **@dnd-kit** (3 packages) | ~40KB combined | `/pipeline` | Only used on pipeline page. Search-only users (majority) should not load DnD. |
| 3 | **shepherd.js** | ~30KB | `/buscar` (onboarding) | Only needed on first visit. After onboarding completes, it is dead weight. Lazy-load on `onboarding-completed` localStorage check. |
| 4 | **framer-motion** | ~40KB | Landing page components | Already route-split by Next.js (landing is a separate route). Verify with bundle analyzer before acting. May already be isolated. |

**Implementation pattern:**
```typescript
// dashboard/page.tsx
const DashboardCharts = dynamic(
  () => import('./components/DashboardCharts'),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

// pipeline/page.tsx
const PipelineBoard = dynamic(
  () => import('./components/PipelineBoard'),
  { ssr: false, loading: () => <PipelineSkeleton /> }
);
```

**Estimated total effort:** 6h (not 8h). Each dynamic import takes ~1.5h including skeleton creation and testing.

### Q6: UX-03 -- Annual pricing display?

**Recommendation: Use "2 meses gratis" framing, NOT "20% desconto".**

Psychological pricing research consistently shows that "free months" framing converts better than percentage discounts for subscription products. The math is identical (12 months for the price of 10 = 2 months free = ~17% discount, or 12 for 9.6 = 20% discount), but "2 meses gratis" is immediately understandable.

**Current (confusing):**
```
R$ 2.851,20/ano
Equivalente a R$ 237,60/mes
12 meses pelo preco de 9.6
```

**Recommended:**
```
R$ 2.851,20/ano
R$ 237,60/mes (economize R$ 712,80)
2 meses gratis no plano anual
```

**Implementation:**
- Replace `price_brl * 9.6` with `price_brl * 12 * 0.8` for clarity (same result, self-documenting)
- Display: monthly equivalent price prominently
- Show savings amount in absolute currency (not percentage)
- Remove the "9.6" text entirely -- it should never appear in UI

**Estimated effort:** 2h (not 4h). The calculation logic stays the same; only the display text changes.

### Q7: FE-05 -- Icon consolidation strategy?

**Recommendation: Migrate all inline SVGs to lucide-react over time. Do NOT create a custom Icon wrapper.**

Rationale:
1. lucide-react is already installed (v0.563.0) and used in 5 files. The library has 1400+ icons covering all current inline SVG usage.
2. A custom Icon wrapper adds a layer of indirection with no clear benefit when lucide-react already provides a clean API (`<Search size={20} />`, `<X size={16} />`, `<ChevronDown />`).
3. The inline SVGs are mostly standard icons (search, close, check, warning, chevron, shield) that have direct lucide-react equivalents.

**Migration strategy:**
- Phase 1 (2h): Replace inline SVGs in the 10 most-imported components (SearchForm, SearchResults, FilterPanel, LicitacaoCard, etc.)
- Phase 2 (3h): Replace inline SVGs in remaining 20 files
- Phase 3 (1h): Remove any SVG-related inline code and verify no regressions
- Rule going forward: All new icons MUST use lucide-react. No new inline SVGs.

**Benefits:**
- Consistent sizing (lucide defaults to 24px, customizable via `size` prop)
- Consistent stroke width (lucide defaults to 2, customizable via `strokeWidth`)
- Tree-shakeable (only used icons are bundled)
- TypeScript autocomplete for icon names

**Estimated effort:** 6h total (not 8h). The replacement is mechanical -- find SVG path, identify lucide equivalent, replace.

---

## 4. Resumo de Ajustes de Severidade

| Tipo | Contagem | Detalhes |
|------|----------|---------|
| Severidade mantida | 30 | Majority confirmed as-is |
| Severidade aumentada | 6 | FE-08 MEDIUM->HIGH, UX-03 MEDIUM->HIGH, FE-17 LOW->MEDIUM, IC-06 LOW->MEDIUM, MF-01 LOW->MEDIUM, A11Y-08 LOW->MEDIUM |
| Severidade reduzida | 3 | A11Y-04 MEDIUM->LOW, UX-05 MEDIUM->LOW, A11Y-02 hours 4h->2h |
| Items a remover | 2 | FE-20 (sr-only is correct Tailwind usage), FE-21 (legitimate FOUC prevention) |
| Items adicionados | 5 | UX-NEW-01 through UX-NEW-05 |
| Contagem FE-04 corrigida | 1 | 22 quarantined files, not 17 |

### Revised Frontend/UX Debt Count

| Severidade | Original (DRAFT) | Ajustado |
|-----------|------------------|----------|
| CRITICAL | 0 | 0 |
| HIGH | 6 | 8 (+FE-08 upgrade, +UX-03 upgrade, +UX-NEW-01, +UX-NEW-02) |
| MEDIUM | 18 | 19 (+FE-17, +IC-06, +MF-01, +A11Y-08, +UX-NEW-03, +UX-NEW-05 upgrades/adds; -A11Y-04, -UX-05 downgrades; -FE-20, -FE-21 removals) |
| LOW | 21 | 18 (-FE-20, -FE-21 removals; +A11Y-04, +UX-05 downgrades; +UX-NEW-04 add) |
| **Total** | **45** | **45** (net zero change after additions and removals) |

### Revised Effort Estimate

| Area | Original (DRAFT) | Ajustado | Nota |
|------|------------------|----------|------|
| FE-01+02+03 (state refactor) | 48h | 32h | Shared work, not additive |
| A11Y-01+02 (dialog primitive) | 8h | 4h | Co-implementation |
| FE-07 (dynamic imports) | 8h | 6h | Mechanical work |
| UX-03 (pricing display) | 4h | 2h | Copy change only |
| IC-06 (error translation) | 8h | 4h | Dictionary pattern |
| FE-05 (icon consolidation) | 8h | 6h | Mechanical migration |
| New items total | 0h | 10h | UX-NEW-01 through UX-NEW-05 |
| Removed items | 0h | -2h | FE-20 + FE-21 |
| **Subtotal Frontend/UX** | **~218h** | **~194h** | 11% reduction from efficiency gains |

---

## 5. Recomendacoes de Design

### 5.1 Immediate Wins (P0, this week, ~8h)

1. **Fix error boundary CTA button** (FE-08): Replace `bg-[var(--brand-green)]` with `bg-[var(--brand-navy)] hover:bg-[var(--brand-blue-hover)]`. Also replace `focus:ring-[var(--brand-green)]` with `focus:ring-[var(--ring)]`. This is a 5-minute fix that resolves an invisible button on the most critical page.

2. **Fix pricing "9.6" display** (UX-03 + UX-NEW-02): Replace all `price_brl * 9.6` instances with `price_brl * 12 * 0.8`. Update display text from "12 meses pelo preco de 9.6" to "2 meses gratis no plano anual". Remove the `9.6` literal from user-visible copy entirely.

3. **Create Dialog primitive** (A11Y-01 + A11Y-02 + UX-NEW-01): Extract from UpgradeModal.tsx pattern. Apply to save search dialog and keyboard help dialog. Add focus trap. 4h total.

### 5.2 Next Sprint (P1, ~20h)

1. **Error message dictionary** (IC-06): Create `lib/error-messages.ts` and apply to all API call sites.
2. **Unsaved search warning** (MF-01): Add `beforeunload` listener when search results are present.
3. **Fix keyboard help Escape conflict** (UX-02): Use capture-phase event listener on the dialog, matching UpgradeModal pattern.
4. **Start icon migration** (FE-05, Phase 1): Replace inline SVGs in top 10 components with lucide-react.

### 5.3 Architecture Sprint (P2, ~50h)

1. **Search state refactor** (FE-01+02+03): React Context + useReducer. See Q2 answer above.
2. **Plan data consolidation** (FE-17): Merge `PLAN_HIERARCHY` and `PLAN_FEATURES` from `planos/page.tsx` into `lib/plans.ts`.
3. **Dynamic imports** (FE-07): recharts, @dnd-kit, shepherd.js.
4. **Search button visibility** (UX-01): Extend mobile sticky behavior to desktop.

### 5.4 Libraries to Adopt

| Library | Purpose | When | Alternative Considered |
|---------|---------|------|----------------------|
| None (custom `<Dialog>`) | Modal primitive | P1 | @radix-ui/react-dialog -- deferred, no Radix ecosystem yet |
| lucide-react (already installed) | Icon standardization | P1-P2 | heroicons -- lucide already in project |
| No new libraries for state | Search state refactor | P2 | Zustand -- overkill for page-scoped state |
| No i18n library | Error messages | P1 | next-intl -- single-language product |

### 5.5 Patterns to Codify

1. **All modals MUST use the shared `<Dialog>` component** -- no more inline `<div>` modals.
2. **All icons MUST use lucide-react** -- no new inline SVGs.
3. **All error messages MUST go through `translateError()`** -- no raw backend errors.
4. **All plan pricing MUST come from a single source** (`lib/plans.ts` or backend API).
5. **All new components MUST NOT receive more than 8 props** -- use Context for anything beyond that.

---

*Review completed by @ux-design-expert (Pixel) on 2026-02-15. All findings verified against codebase at commit `b80e64a`. Previous review by @Uma (2026-02-11) at commit `808cd05` is superseded by this document. Ready for @architect final consolidation into `docs/prd/technical-debt-assessment.md`.*
