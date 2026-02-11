# UX Specialist Review

**Reviewer:** @ux-design-expert (Uma)
**Date:** 2026-02-11
**Reviewed Document:** `docs/prd/technical-debt-DRAFT.md` (Section 4: Frontend/UX Debts + Section 8: Questions)
**Reference Document:** `docs/frontend/frontend-spec.md`
**Codebase Commit:** `808cd05` (branch `main`)

---

## 1. Debts Validated

All 25 frontend debts from the DRAFT were individually verified against the codebase. Below is the validation with adjusted severities and UX-specific effort estimates where my assessment differs from the architect's.

| ID | Debt | Original Severity | Validated Severity | Hours | UX Impact | Notes |
|----|------|-------------------|-------------------|-------|-----------|-------|
| FE-C01 | Monolithic buscar/page.tsx (~1100 lines, 30+ useState) | CRITICAL | **CRITICAL** (confirmed) | 16-24h | **High** -- prevents iterative UX improvement; single change risks regressions across all search features | Confirmed: file has 30+ hooks, inline business logic, all filter/results/header in one component. Decomposition is prerequisite for any meaningful UX iteration. |
| FE-C02 | Fallback localhost in analytics route | CRITICAL | **HIGH** (downgraded) | 1h | **Low** -- analytics proxy, not user-facing. No data leaks to browser. Server-side only env var. | The `BACKEND_URL` in `api/analytics/route.ts:4` is server-only (not `NEXT_PUBLIC_`). Risk is misconfigured deployment hitting localhost, not client-side exposure. Still wrong, but not CRITICAL from UX perspective. |
| FE-C03 | Mixed API patterns (proxy vs direct) | CRITICAL | **CRITICAL** (confirmed) | 8-12h | **Medium-High** -- direct calls expose backend URL to client; `historico/page.tsx:76-79` falls back to `/api` which masks the inconsistency but creates unpredictable behavior | Confirmed: `historico`, `conta`, `admin` call `NEXT_PUBLIC_BACKEND_URL` directly. This creates inconsistent error handling and auth forwarding, which surfaces as unpredictable failures for the user. |
| FE-H01 | Duplicate filter components (EsferaFilter, MunicipioFilter) | HIGH | **HIGH** (confirmed) | 3-4h | **Medium** -- the two versions have DIFFERENT implementations: `app/components/EsferaFilter.tsx` uses `<button>` with `aria-pressed`; `components/EsferaFilter.tsx` uses `<div role="checkbox">` with `aria-checked`. Different ARIA patterns, different icon SVG paths, different stroke widths. The `app/` version is used in production. | `app/components/` version is "correct" -- it uses native `<button>`, which provides keyboard interaction for free. The `components/` version uses `<div>` with manual `onKeyDown`, which is fragile. |
| FE-H02 | Direct DOM manipulation for search state restoration | HIGH | **HIGH** (confirmed) | 2-3h | **Medium** -- creates a success banner via `document.createElement` at lines 285-293. Bypasses React rendering, toast system, and is invisible to screen readers (no `role="status"` or `aria-live`). | Should use the existing `sonner` toast system. The banner also uses a hardcoded animation (`fadeIn`/`fadeOut`) that may not be defined and does not respect `prefers-reduced-motion`. |
| FE-H03 | Error boundary ignores design system | HIGH | **HIGH** (confirmed) | 1-2h | **High** -- completely white background in dark mode. `bg-gray-50`, `text-gray-900`, `bg-green-600` are all hardcoded. Error page is the worst place for UX breakage because the user is already frustrated. | Confirmed by reading `app/error.tsx`: zero CSS custom properties, fully hardcoded colors. SVG also has conflicting `role="img" aria-label="Icone"` AND `aria-hidden="true"` on the same element. |
| FE-H04 | Native `alert()` for user feedback | HIGH | **HIGH** (confirmed) | 1h | **High** -- `window.alert()` at line 1080 (save search success) and line 1087 (save search error). Blocks main thread. Disrupts flow. Inconsistent with the rest of the app which uses toast. Particularly jarring because the save dialog itself is a well-designed inline UI. | Two occurrences confirmed. `sonner` is already imported in the app layout. This is a 15-minute fix per call site. |
| FE-H05 | UF_NAMES duplicated in multiple files | HIGH | **MEDIUM** (downgraded) | 1-2h | **Low** -- maintenance debt, not user-facing. Both copies appear identical. Risk is drift, not current UX issue. | Extract to `lib/constants.ts` during buscar decomposition. Low standalone urgency. |
| FE-H06 | Excel storage in tmpdir() | HIGH | **HIGH** (confirmed) | 6-8h | **High** -- if the server restarts between search completion and download click, user loses their results. No error message explains what happened; the download just fails. This is the most confusing failure mode for users. | Cross-cutting debt (CROSS-C02). UX mitigation: add clear error message with "re-run search" CTA when download file is missing. |
| FE-M01 | No shared app shell for protected pages | MEDIUM | **HIGH** (upgraded) | 6-8h | **High** -- every protected page builds its own header. Navigation between pages feels disjointed. No persistent sidebar or breadcrumbs. Users on `historico`, `conta`, `mensagens` have inconsistent nav patterns. | This is more impactful than MEDIUM. The buscar page has a full header with PlanBadge, QuotaBadge, MessageBadge, ThemeToggle, UserMenu. Other pages have minimal or no header. The app feels like separate apps stitched together. |
| FE-M02 | Feature flags underused | MEDIUM | **MEDIUM** (confirmed) | 2-3h | **Low** -- developer experience debt, not user-facing. | Low UX priority. |
| FE-M03 | No form validation library | MEDIUM | **MEDIUM** (confirmed) | 8-12h | **Medium** -- validation timing is inconsistent. Signup validates on submit; search validates in real-time; password change validates on submit. Users learn different patterns per form. | Recommend zod + react-hook-form (see Q7 below). Effort is high because 3+ forms need migration. |
| FE-M04 | STOPWORDS_PT duplicated from backend | MEDIUM | **LOW** (downgraded) | 1-2h | **None** -- internal optimization data. Users never see stopwords. Drift risk is minimal because the list is stable Portuguese function words. | Move to P3 backlog. |
| FE-M05 | SETORES_FALLBACK manual sync | MEDIUM | **MEDIUM** (confirmed) | 1h | **Low** -- sync script already exists (`scripts/sync-setores-fallback.js`). Just needs to be run periodically. Risk: user sees stale sector names. | Automate in CI/CD rather than treating as tech debt. |
| FE-M06 | Stale file: dashboard-old.tsx | MEDIUM | **LOW** (downgraded) | 0.5h | **None** -- dead code, not imported anywhere. No user impact. | Delete in next cleanup sweep. |
| FE-M07 | Stale file: landing-layout-backup.tsx | MEDIUM | **LOW** (downgraded) | 0.5h | **None** -- dead code, not imported anywhere. No user impact. | Delete in next cleanup sweep. |
| FE-M08 | No middleware auth guards (flash of unprotected content) | MEDIUM | **REMOVED** (see Section 2) | 0h | N/A | **Middleware EXISTS.** See Section 2. |
| FE-M09 | `performance.timing` deprecated | MEDIUM | **LOW** (downgraded) | 1h | **None** -- internal analytics data collection. Users never see this value. Browser deprecation warnings only visible in dev tools. | Low urgency. Replace `performance.timing.navigationStart` with `performance.timeOrigin` in AnalyticsProvider.tsx:53. |
| FE-L01 | SVG icons with generic aria-label="Icone" | LOW | **MEDIUM** (upgraded) | 3-4h | **Medium** -- screen reader users hear "Icone" for every SVG, providing zero information. The `app/components/EsferaFilter.tsx` has BOTH `role="img" aria-label="Icone"` AND `aria-hidden="true"` on the same element, which is contradictory. | WCAG 1.1.1 violation. Upgrade to MEDIUM because it directly affects assistive technology users. Fix: remove `role="img" aria-label` from decorative SVGs (keep `aria-hidden="true"`), add descriptive `aria-label` to meaningful SVGs. |
| FE-L02 | useEffect with serialized Set dependency | LOW | **LOW** (confirmed) | 1h | **None** -- internal implementation. May cause unnecessary re-renders but no visible UX impact at current scale. | Low priority. |
| FE-L03 | Divergent plan prices between pages | LOW | **CRITICAL** (upgraded) | 2h | **Critical** -- users see R$149/349/997 on `pricing/page.tsx` but R$297/597/1497 in `lib/plans.ts` and on `planos/page.tsx`. This directly undermines trust. A user comparing prices before signing up will see one set, then see different prices on the upgrade page. | See Q6 below for which prices are correct. This MUST be P0. |
| FE-L04 | Unused barrel file | LOW | **LOW** (confirmed) | 0.5h | **None** | Cleanup. |
| FE-L05 | No robots.txt or sitemap | LOW | **LOW** (confirmed) | 2-3h | **Low** -- affects SEO discoverability, not in-app UX. | Important for growth but not UX debt per se. |
| FE-L06 | No OpenGraph images | LOW | **LOW** (confirmed) | 2-3h | **Low** -- affects social sharing previews. No impact on logged-in users. | Marketing debt. |
| FE-L07 | Test coverage ~49.46% (70 pre-existing failures) | LOW | **MEDIUM** (upgraded) | 12-16h | **Medium** -- low coverage means UX regressions ship undetected. The 70 failing tests are a broken safety net. | Upgrade because it affects the team's ability to ship UX improvements confidently. |

---

## 2. Debts Removed/Downgraded

### FE-M08: "No middleware auth guards" -- REMOVED

**Reason:** The middleware EXISTS at `frontend/middleware.ts`. It is a fully implemented Supabase SSR auth guard that:
- Defines `PROTECTED_ROUTES` including `/buscar`, `/historico`, `/conta`, `/admin`, `/dashboard`
- Uses `supabase.auth.getUser()` (server-side validation, not just `getSession()`)
- Redirects to `/login?redirect=<path>` with session expiry reason
- Handles canonical domain redirect (railway.app to smartlic.tech)

**However**, the middleware is INCOMPLETE -- it is missing two protected routes:
- `/mensagens` -- not in `PROTECTED_ROUTES` array
- `/planos/obrigado` -- not in `PROTECTED_ROUTES` array

**Recommendation:** Replace FE-M08 with a narrower debt: "Middleware PROTECTED_ROUTES list incomplete -- add `/mensagens` and `/planos/obrigado`." Effort: 0.5h. Severity: LOW.

### Downgraded Items

| ID | Original | New | Reason |
|----|----------|-----|--------|
| FE-C02 | CRITICAL | HIGH | Server-side only; no browser data leak. Still wrong but not user-facing. |
| FE-H05 | HIGH | MEDIUM | Maintenance issue, not user-facing. Both copies are identical. |
| FE-M04 | MEDIUM | LOW | Stable data, no user impact. |
| FE-M06 | MEDIUM | LOW | Dead code, zero user impact. |
| FE-M07 | MEDIUM | LOW | Dead code, zero user impact. |
| FE-M09 | MEDIUM | LOW | Internal analytics, no user impact. |

---

## 3. NEW Debts Added

These UX-relevant issues were found during code review but were NOT identified in the DRAFT.

| ID | Debt | Severity | File(s) | Hours | UX Impact |
|----|------|----------|---------|-------|-----------|
| FE-NEW-01 | **Contradictory ARIA on error boundary SVG** -- `app/error.tsx` line 26-28 has both `role="img" aria-label="Icone"` AND `aria-hidden="true"`. These contradict: `aria-hidden` hides from AT, but `role="img"` exposes it. Screen readers may behave unpredictably. | MEDIUM | `app/error.tsx:26-28` | 0.5h | Medium -- affects AT users hitting the error page |
| FE-NEW-02 | **Advanced filters toggle lacks aria-expanded** -- The "Filtros Avancados" collapsible section (`buscar/page.tsx:1627-1639`) uses a `<button>` that toggles `advancedFiltersOpen` but does NOT have `aria-expanded={advancedFiltersOpen}`. Screen readers cannot determine panel state. | HIGH | `app/buscar/page.tsx:1627-1639` | 0.5h | High -- WCAG 4.1.2 violation (name, role, value) |
| FE-NEW-03 | **No aria-describedby on search term validation errors** -- The term validation feedback (stopword warnings, min-length errors) in buscar/page.tsx is displayed visually but not linked to the input via `aria-describedby`. Screen readers miss validation feedback. | MEDIUM | `app/buscar/page.tsx` (term validation section) | 1h | Medium -- WCAG 3.3.1 violation |
| FE-NEW-04 | **No page transition indicators** -- Navigating between protected pages (buscar to historico to conta) shows no loading indicator. On slow connections, the user stares at a blank screen. No NProgress bar or similar. | MEDIUM | All page navigations | 3-4h | Medium -- perceived performance |
| FE-NEW-05 | **No breadcrumbs on any protected page** -- Users lose context of where they are in the app. Combined with the lack of shared app shell (FE-M01), navigation feels rootless. | LOW | All protected pages | 2-3h | Low-Medium -- wayfinding |
| FE-NEW-06 | **framer-motion does not check prefers-reduced-motion** -- 9 files import framer-motion. CSS `globals.css:281` disables CSS animations for `prefers-reduced-motion`, but framer-motion uses JS animations that bypass CSS media queries. Only `SectorsGrid.tsx` comments about respecting it. | MEDIUM | 9 files using framer-motion | 2-3h | Medium -- accessibility for vestibular/motion sensitivity disorders |
| FE-NEW-07 | **UF grid has no roving tabindex** -- The 27-state UF selection grid in RegionSelector creates 27 individual tab stops. Users who navigate by keyboard must press Tab 27 times to pass through it. Should use roving tabindex (arrow keys within group, single Tab stop). | MEDIUM | `app/components/RegionSelector.tsx` | 3-4h | Medium -- keyboard usability |
| FE-NEW-08 | **Sector list not cached client-side** -- Every visit to `/buscar` fetches the sector list from the backend. On slow connections, the dropdown shows a loading state each time. Should cache in memory or localStorage with short TTL. | LOW | `app/buscar/page.tsx` (sector fetch effect) | 1-2h | Low -- minor perceived performance |
| FE-NEW-09 | **`/mensagens` and `/planos/obrigado` missing from middleware PROTECTED_ROUTES** -- These routes require auth but are not in the middleware list. Flash of content possible on these two routes specifically. | LOW | `frontend/middleware.ts:15-21` | 0.5h | Low -- narrow scope |

---

## 4. Answers to Architect Questions

### Q1: buscar decomposition -- will it maintain current UX or require changes?

The decomposition I proposed (SearchForm, FilterPanel, SearchResults, useSearch, useSearchFilters) is a **pure refactoring** that should produce zero visible UX changes. The component boundaries I identified follow natural visual boundaries already present in the page:

- **SearchForm**: The top section (UF selector, date range, sector/terms mode toggle, search button). This is visually a single card.
- **FilterPanel**: The collapsible "Filtros Avancados" section. Already has a distinct visual boundary (bg-surface-1, border, rounded-card).
- **SearchResults**: Everything below the search button (AI summary, LicitacaoCards list, download/export buttons, pagination).
- **useSearch**: Pure logic hook (no visual changes). Manages search execution, retry, SSE progress, abort controller, error translation.
- **useSearchFilters**: Pure logic hook. Manages all useState for filters plus localStorage persistence.

**Risk areas during decomposition:**
1. The search state restoration flow (lines 262-300) touches both filter state and result state. The `useSearch` and `useSearchFilters` hooks need careful coordination here.
2. The keyboard shortcut handler (Ctrl+K triggers search) references both filter state and the `buscar()` function. The shortcut registration should live in the parent component that composes all sub-components.
3. The `canSearch` computed property depends on filter state AND loading state. This must be lifted to the parent or computed from both hooks.

**Recommendation:** Do not introduce any visual changes during the decomposition sprint. Use visual regression tests (Playwright screenshots) to verify pixel-perfect match before and after.

### Q2: Mixed API patterns -- perceptible user impact of unification?

**Yes, there will be a perceptible (positive) improvement:**

1. **Consistent error handling:** Currently, direct-call pages (`historico`, `conta`, `admin`) handle errors differently from proxy pages (`buscar`). On `buscar`, a 502 becomes "Portal PNCP temporariamente indisponivel." On `historico`, a 502 shows the raw error. After unification, all pages benefit from the proxy's error translation.

2. **Consistent auth expiry behavior:** The proxy routes forward auth headers server-side. Direct calls send the token from the browser. When a token expires, proxy routes can refresh silently (middleware handles cookie refresh); direct calls get a raw 401 that each page handles differently.

3. **Minor latency change:** Adding a proxy hop adds ~5-20ms per request. For the pages involved (historico, conta, admin), these are low-frequency API calls. The latency increase is imperceptible.

4. **Security improvement invisible to users:** The backend URL disappears from browser network tab. Users do not see this, but security audits will.

**Net UX impact: slightly positive (better error messages), zero negative.**

### Q3: Duplicate components -- which version is "correct"?

**The `app/components/` versions are correct.** Here is the detailed comparison:

| Aspect | `app/components/EsferaFilter.tsx` (P1) | `components/EsferaFilter.tsx` (P0) |
|--------|----------------------------------------|-------------------------------------|
| Element | `<button>` (native) | `<div>` (custom) |
| ARIA pattern | `aria-pressed` (toggle button) | `role="checkbox" aria-checked` |
| Keyboard | Built-in (native button) | Manual `onKeyDown` handler |
| Focus ring | `focus:ring-2 focus:ring-brand-blue focus:ring-offset-2` | `focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 focus:ring-offset-[var(--canvas)]` |
| Icon stroke | `strokeWidth={1.5}` | `strokeWidth={2}` |
| Disabled state | `disabled` attribute (native) | `aria-disabled` + manual check |
| SVG paths | Heroicons v2 (24px outline) | Heroicons v1 (different paths) |
| Currently imported by | `buscar/page.tsx` (production) | Not imported by any page |

**Verdict:** The `app/components/` versions are actively used, use native HTML semantics (better for accessibility), and follow the design system more closely. The `components/` versions should be deleted. Same applies to `MunicipioFilter`.

**Action:** Delete `components/EsferaFilter.tsx` and `components/MunicipioFilter.tsx`. Verify no imports reference them first.

### Q4: ARIA accessibility -- which 6 issues to prioritize for next sprint?

Ordered by WCAG impact and effort, here are the 6 to tackle in the next sprint:

1. **Add `aria-expanded` to advanced filters toggle** (FE-NEW-02) -- 0.5h. WCAG 4.1.2 violation. One-line fix: add `aria-expanded={advancedFiltersOpen}` to the button at buscar/page.tsx:1627. Also add `id="advanced-filters-panel"` to the content div and `aria-controls="advanced-filters-panel"` to the button.

2. **Fix contradictory ARIA on error boundary SVG** (FE-NEW-01) -- 0.5h. Remove `role="img" aria-label="Icone"` from the SVG in error.tsx since it already has `aria-hidden="true"`. The icon is decorative.

3. **Fix contradictory ARIA on EsferaFilter SVGs** (part of FE-L01) -- 1h. All three icon components in `app/components/EsferaFilter.tsx` have both `role="img" aria-label="Icone"` and `aria-hidden="true"`. Remove the `role` and `aria-label` since `aria-hidden="true"` correctly marks them as decorative.

4. **Add `aria-describedby` for search term validation** (FE-NEW-03) -- 1h. Link validation error messages to the search input via `aria-describedby`. This ensures screen readers announce "Term too short" or "Stopword removed" feedback.

5. **Add `aria-live="polite"` to search results region** -- 1h. The results area at buscar/page.tsx:1717 already has `aria-live="polite"`, but the empty state and error state containers do not. Ensure all three result states (results, empty, error) are inside the live region.

6. **Implement framer-motion reduced motion check** (FE-NEW-06) -- 2h. Add `useReducedMotion()` hook from framer-motion and conditionally disable animations. Apply in the 9 files that import framer-motion.

**Total sprint effort: ~6h**

### Q5: Shared app shell -- wireframe or spec for how it should look?

**Recommendation: Top-nav only (no sidebar).** Here is the specification:

```
+------------------------------------------------------------------+
| [Logo]  Buscar  Historico  Dashboard  |  [Msgs(3)] [Plan] [User] |
+------------------------------------------------------------------+
|                                                                    |
|                    Page Content Area                               |
|                                                                    |
+------------------------------------------------------------------+
|                    Footer (public pages only)                      |
+------------------------------------------------------------------+
```

**Rationale for top-nav over sidebar:**
1. The app has only 5-6 protected routes. A sidebar is overkill for this count.
2. The buscar page needs maximum horizontal space for the 27-state UF grid and result cards.
3. The current user base (Brazilian procurement professionals) uses desktop primarily. Top-nav is the expected pattern for SaaS dashboards in this market.
4. Mobile: top-nav collapses to hamburger menu naturally. Sidebar on mobile requires overlay/drawer complexity.

**Component structure:**
```
app/(protected)/layout.tsx    -- shared layout for all auth'd pages
  +-- AppHeader.tsx           -- persistent top nav
  |    +-- Logo (links to /buscar)
  |    +-- NavLinks (Buscar, Historico, Dashboard)
  |    +-- MessageBadge
  |    +-- PlanBadge + QuotaBadge
  |    +-- ThemeToggle
  |    +-- UserMenu (dropdown: Conta, Planos, Admin*, Sair)
  +-- <main id="main-content"> {children} </main>
```

**Key design decisions:**
- Active nav link gets `border-b-2 border-brand-blue text-brand-blue` (underline indicator)
- Compact height: `h-14` (56px) to maximize content area
- Sticky top: `sticky top-0 z-40 bg-[var(--surface-0)] border-b border-[var(--border)]`
- Admin link only visible when `isAdmin === true`
- Mobile: hamburger menu at `md` breakpoint (768px)

### Q6: Divergent prices -- which are CORRECT?

**This requires clarification from the product owner**, but based on code analysis:

| Source | Consultor Agil | Maquina | Sala de Guerra | Context |
|--------|---------------|---------|----------------|---------|
| `lib/plans.ts:46-68` | R$ 297/mes | R$ 597/mes | R$ 1.497/mes | Used in PlanBadge display across the app |
| `pricing/page.tsx:129-131` | R$ 149 | R$ 349 | R$ 997 | Used in public pricing page + ROI calculator |
| `planos/page.tsx` | Dynamic from backend | Dynamic from backend | Dynamic from backend | Fetches from `/plans` API endpoint |

**Analysis:**
- The `pricing/page.tsx` prices (149/349/997) look like promotional or introductory prices.
- The `lib/plans.ts` prices (297/597/1497) look like standard list prices.
- The `planos/page.tsx` fetches dynamically from the backend, which is the source of truth for actual Stripe checkout.

**UX recommendation:**
1. **Immediately** make `pricing/page.tsx` fetch prices from the same backend endpoint that `planos/page.tsx` uses. Single source of truth.
2. If the 149/349/997 prices are promotional, display them WITH the original price struck through (e.g., ~~R$297~~ R$149/mes) to build credibility.
3. If the 149/349/997 prices ARE the current prices, update `lib/plans.ts` to match.

**The worst outcome is the current state where users see two different price sets.** This is a trust-destroying UX failure. I am upgrading FE-L03 to CRITICAL.

### Q7: Form validation -- recommend zod + react-hook-form or alternative?

**Yes, I recommend zod + react-hook-form.** Here is the justification:

| Criterion | zod + react-hook-form | Alternatives |
|-----------|----------------------|-------------|
| Bundle size | ~8KB + ~13KB gzipped | formik: ~45KB; native: 0KB |
| TypeScript integration | Excellent (zod infers types) | formik: good; native: manual |
| Validation timing | Configurable (onChange, onBlur, onSubmit) | Consistent across forms |
| Error message rendering | Built-in `errors` object | Manual per-field |
| Design system integration | `register()` spreads props on any input | Works with any component |
| Already in ecosystem | zod is standard for TypeScript validation | N/A |
| Learning curve | Low for team already using TypeScript | N/A |

**Migration plan:**
1. Start with the simplest form: `conta/page.tsx` (password change -- 2 fields)
2. Then `login/page.tsx` (email + password + mode toggle)
3. Then `signup/page.tsx` (7 fields, most complex validation)
4. Finally, search form in `buscar/page.tsx` (during decomposition sprint)

**Pattern to adopt:**
```typescript
// Example: password change form schema
const passwordSchema = z.object({
  newPassword: z.string().min(6, "Senha deve ter no minimo 6 caracteres"),
  confirmPassword: z.string(),
}).refine(data => data.newPassword === data.confirmPassword, {
  message: "As senhas nao coincidem",
  path: ["confirmPassword"],
});
```

**Important:** Do NOT adopt a form library for the search page filters. Filters are not a "form" in the traditional sense -- they are interactive controls that update results in real-time. The current useState approach is appropriate for filters. Only traditional submit-based forms (login, signup, password change, admin user creation) should use react-hook-form.

### Q8: framer-motion -- worth dynamic import or acceptable impact?

**Yes, implement dynamic import. Here is why:**

- framer-motion is ~40KB gzipped
- It is used in 9 files, ALL of which are landing page components or shared UI primitives (Footer, GlassCard, GradientButton)
- The landing page (`/`) is the ENTRY POINT for unauthenticated users. First Contentful Paint matters most here.
- Logged-in users go directly to `/buscar`, which does NOT use framer-motion
- Next.js App Router already code-splits by route, so framer-motion should NOT be in the buscar bundle

**However**, even with route splitting, the shared components (Footer, GlassCard, GradientButton) that import framer-motion may pull it into other routes' bundles if those components are used elsewhere.

**Recommended approach:**
1. Verify via `next build` + bundle analyzer that framer-motion is NOT in the `/buscar` chunk. If it is not, no action needed beyond monitoring.
2. If it IS leaking into non-landing bundles, wrap the landing page sections that use framer-motion with `next/dynamic`:
   ```typescript
   const HeroSection = dynamic(() => import('./components/landing/HeroSection'), {
     loading: () => <HeroSectionSkeleton />,
     ssr: true, // keep SSR for SEO
   });
   ```
3. For Footer (used on multiple pages): create a `FooterStatic` variant without animations for non-landing pages, or use `next/dynamic` with SSR.

**Estimated effort:** 2-3h to analyze bundles + implement dynamic imports if needed.

**Verdict:** Worth doing, but ONLY if bundle analysis confirms framer-motion is leaking beyond the landing page route.

---

## 5. Design Recommendations

### 5.1 Error Boundary Redesign (FE-H03)

Replace all hardcoded colors in `app/error.tsx` with design system tokens:

| Current | Replace With |
|---------|-------------|
| `bg-gray-50` | `bg-[var(--canvas)]` |
| `bg-white` | `bg-[var(--surface-elevated)]` |
| `text-gray-900` | `text-[var(--ink)]` |
| `text-gray-600` | `text-[var(--ink-secondary)]` |
| `text-gray-500` | `text-[var(--ink-muted)]` |
| `text-gray-700` | `text-[var(--ink-secondary)]` |
| `bg-gray-100` | `bg-[var(--surface-1)]` |
| `text-red-500` | `text-[var(--error)]` |
| `bg-green-600` | `bg-[var(--brand-blue)]` (use brand color, not green) |
| `hover:bg-green-700` | `hover:bg-[var(--brand-blue-hover)]` |
| `focus:ring-green-500` | `focus:ring-[var(--ring)]` |

Also fix the SVG: remove `role="img" aria-label="Icone"` (conflicts with `aria-hidden="true"`).

### 5.2 Toast Migration (FE-H04 + FE-H02)

Replace both `window.alert()` calls and the `document.createElement` banner with `sonner` toast:

```typescript
import { toast } from 'sonner';

// Save search success (line 1080)
toast.success(`Busca "${saveSearchName || "Busca sem nome"}" salva com sucesso!`);

// Save search error (line 1087)
toast.error(`Erro ao salvar: ${error instanceof Error ? error.message : "Erro desconhecido"}`);

// Search state restored (lines 285-293)
toast.success('Resultados da busca restaurados! Voce pode fazer o download agora.');
```

### 5.3 App Shell Implementation (FE-M01)

Use Next.js route groups to create a shared layout:

```
app/
  (public)/          -- landing, pricing, features, termos, privacidade
    layout.tsx       -- minimal layout (no auth header)
  (auth)/            -- login, signup, auth/callback
    layout.tsx       -- split-screen with InstitutionalSidebar
  (protected)/       -- buscar, historico, dashboard, conta, planos, mensagens, admin
    layout.tsx       -- AppHeader + main content area
```

### 5.4 Price Reconciliation (FE-L03 upgraded to CRITICAL)

Create a single `PLAN_PRICES` constant fetched from the backend `/plans` endpoint at build time (or with SWR/React Query at runtime). All pages that display prices should reference this single source. If promotional prices exist, model them explicitly:

```typescript
interface PlanPricing {
  id: string;
  name: string;
  basePrice: number;        // Full price (e.g., 297)
  currentPrice: number;     // May be promotional (e.g., 149)
  isPromotional: boolean;
  promotionEnds?: string;   // ISO date
}
```

---

## 6. Accessibility Priority List

Ordered by WCAG conformance impact (Level A violations first, then AA, then AAA enhancements).

| Priority | Issue | WCAG Criterion | Level | Effort | Sprint |
|----------|-------|---------------|-------|--------|--------|
| 1 | Add `aria-expanded` to advanced filters toggle | 4.1.2 Name, Role, Value | A | 0.5h | Next |
| 2 | Fix contradictory ARIA on decorative SVGs (error.tsx + EsferaFilter) | 1.1.1 Non-text Content | A | 1h | Next |
| 3 | Add `aria-describedby` linking inputs to validation errors | 3.3.1 Error Identification | A | 1h | Next |
| 4 | Replace generic `aria-label="Icone"` with descriptive labels on meaningful SVGs | 1.1.1 Non-text Content | A | 2h | Next |
| 5 | framer-motion `prefers-reduced-motion` support | 2.3.3 Animation from Interactions | AAA | 2h | Next |
| 6 | Ensure `aria-live` covers all dynamic result states (empty + error) | 4.1.3 Status Messages | AA | 1h | Next |
| 7 | Roving tabindex for 27-state UF grid | 2.1.1 Keyboard | A | 3-4h | Sprint+1 |
| 8 | ARIA listbox pattern for custom dropdowns | 4.1.2 Name, Role, Value | A | 4-6h | Sprint+1 |
| 9 | Page transition loading indicator | 2.2.2 Pause, Stop, Hide | A | 3-4h | Sprint+1 |
| 10 | Breadcrumbs on protected pages | 2.4.8 Location | AAA | 2-3h | Backlog |

**Total for "Next Sprint" (items 1-6): ~7.5h**
**Total for "Sprint+1" (items 7-9): ~10-14h**

---

## 7. Priority Recommendations

Recommended resolution order from UX perspective, incorporating severity re-assessments:

### P0 -- Immediate (trust-critical, do this week)

| ID | Debt | Hours | Reason |
|----|------|-------|--------|
| FE-L03 (upgraded) | **Divergent plan prices** | 2h | Trust-destroying. Users see different prices on different pages. |
| FE-H04 | **Replace alert() with sonner** | 1h | Trivial fix, high UX improvement. |
| FE-H03 | **Fix error boundary design system** | 1-2h | Dark mode completely broken on error page. |
| FE-NEW-02 | **aria-expanded on advanced filters** | 0.5h | One-line WCAG fix. |
| FE-NEW-01 | **Fix contradictory ARIA on error SVG** | 0.5h | While fixing error boundary anyway. |

**Total P0: ~5-6h**

### P1 -- Next Sprint (structural UX)

| ID | Debt | Hours | Reason |
|----|------|-------|--------|
| FE-M01 (upgraded) | **Shared app shell** | 6-8h | Biggest single UX improvement. Makes app feel cohesive. |
| FE-C03 | **Unify API patterns** | 8-12h | Prerequisite for consistent error handling UX. |
| FE-H01 | **Consolidate duplicate components** | 3-4h | Eliminate confusion, reduce maintenance. |
| FE-H02 | **Replace DOM manipulation with toast** | 2-3h | React anti-pattern with accessibility gap. |
| FE-H06 | **Excel storage resilience** | 6-8h | Users lose downloads on restart. Add clear error + retry. |
| Accessibility items 1-6 | **WCAG sprint** | 7.5h | See Section 6. |

**Total P1: ~33-43h**

### P2 -- Decomposition Sprint (maintainability for future UX work)

| ID | Debt | Hours | Reason |
|----|------|-------|--------|
| FE-C01 | **Decompose buscar monolith** | 16-24h | Prerequisite for iterating on search UX. |
| FE-M03 | **Adopt form validation library** | 8-12h | Consistent validation UX across forms. |
| FE-C02 | **Fix localhost fallback** | 1h | Quick fix during API unification. |
| FE-H05 | **Extract UF_NAMES** | 1-2h | During decomposition. |
| Accessibility items 7-9 | **Keyboard + transitions** | 10-14h | See Section 6. |

**Total P2: ~36-53h**

### P3 -- Backlog (polish)

| ID | Debt | Hours |
|----|------|-------|
| FE-L07 | Test coverage to 60% | 12-16h |
| FE-L01 | Fix all generic aria-labels | 3-4h |
| FE-L05 | robots.txt + sitemap | 2-3h |
| FE-L06 | OpenGraph images | 2-3h |
| FE-L02 | useEffect Set dependency | 1h |
| FE-L04 | Delete unused barrel file | 0.5h |
| FE-M06 | Delete dashboard-old.tsx | 0.5h |
| FE-M07 | Delete landing-layout-backup.tsx | 0.5h |
| FE-M04 | Extract STOPWORDS_PT | 1-2h |
| FE-M05 | Automate SETORES sync | 1h |
| FE-M02 | Expand feature flag usage | 2-3h |
| FE-M09 | Replace performance.timing | 1h |
| FE-NEW-08 | Cache sector list client-side | 1-2h |
| FE-NEW-09 | Add missing middleware routes | 0.5h |
| FE-NEW-05 | Breadcrumbs | 2-3h |

**Total P3: ~31-40h**

---

## Summary of Changes from DRAFT

| Change Type | Count | Details |
|-------------|-------|---------|
| Severity upgrades | 4 | FE-L03 LOW->CRITICAL, FE-M01 MEDIUM->HIGH, FE-L01 LOW->MEDIUM, FE-L07 LOW->MEDIUM |
| Severity downgrades | 6 | FE-C02 CRITICAL->HIGH, FE-H05 HIGH->MEDIUM, FE-M04/M06/M07/M09 MEDIUM->LOW |
| Debts removed | 1 | FE-M08 (middleware exists) |
| New debts added | 9 | FE-NEW-01 through FE-NEW-09 |
| **Revised total** | **33** | Was 25, net +8 after removal and additions |
| **Revised effort** | **~115-162h** | Was 85-120h (increase due to new items + upgraded priorities) |

---

*Review completed by @ux-design-expert (Uma) on 2026-02-11. All findings verified against codebase at commit `808cd05`. Ready for @architect final consolidation.*
