# SmartLic Frontend Specification & UX Audit

**Date:** 2026-03-20
**Auditor:** @ux-design-expert (Brownfield Discovery Phase 3)
**Stack:** Next.js 16.1, React 18.3, TypeScript 5.9, Tailwind CSS 3.4, Framer Motion 12
**URL:** https://smartlic.tech
**Test baselines:** 5583 pass / 3 pre-existing fail / 60 documented skip (135 test files)

---

## 1. Frontend Overview

### Architecture Style

SmartLic uses the **Next.js App Router** with a hybrid rendering strategy:

- **Server Components (SSC):** Landing page (`/`), blog pages (`/blog/*`), SEO programmatic pages (`/licitacoes/*`, `/como-*`), status page (`/status`), legal pages (`/termos`, `/privacidade`). These are statically rendered or server-side rendered for SEO.
- **Client Components ("use client"):** All authenticated pages (26 of ~47 page files) are client-rendered. Search, dashboard, pipeline, historico, admin, account, onboarding, login, signup all use `"use client"` directive.
- **Dynamic Imports:** Heavy libraries are code-split: `@dnd-kit` (PipelineKanban), `SearchStateManager`, `TotpVerificationScreen`.

### Routing

App Router with file-based routing. Route groups used for `(protected)` layout. Sub-routes for `/conta/*` (perfil, dados, seguranca, plano, equipe). Dynamic routes for `/blog/[slug]`, `/blog/programmatic/[setor]/[uf]`, `/blog/licitacoes/[setor]/[uf]`, `/licitacoes/[setor]`, `/blog/panorama/[setor]`.

### Provider Hierarchy (layout.tsx)

```
<html lang="pt-BR">
  <body>
    AnalyticsProvider
      AuthProvider
        SWRProvider
          UserProvider
            ThemeProvider
              NProgressProvider
                BackendStatusProvider
                  SessionExpiredBanner
                  PaymentFailedBanner
                  NavigationShell (sidebar + bottom nav)
                    {children}
                  Toaster (sonner)
                  CookieConsentBanner
```

### Security

- CSP with per-request nonce (`middleware.ts`) -- `strict-dynamic` + nonce-based `script-src`
- HSTS with preload, X-Frame-Options: DENY, COOP: same-origin
- Supabase `getUser()` (server-validated, not just `getSession()`)
- Canonical domain redirect (railway.app -> smartlic.tech, 301)

---

## 2. Page Inventory

### Public Pages (no auth required)

| Route | Purpose | Rendering | Key Components |
|-------|---------|-----------|----------------|
| `/` | Landing page | SSC | LandingNavbar, HeroSection, OpportunityCost, BeforeAfter, HowItWorks, StatsSection, TestimonialSection, FinalCTA, Footer |
| `/login` | Email/password + magic link + Google OAuth | CSR | InstitutionalSidebar, TotpVerificationScreen (lazy), Button |
| `/signup` | Registration with Zod validation | CSR | InstitutionalSidebar, Input, Label, react-hook-form + zodResolver |
| `/planos` | Pricing page (Pro + Consultoria) | CSR | PlanToggle, TestimonialSection, Button |
| `/planos/obrigado` | Post-purchase thank you | CSR | ObrigadoContent |
| `/pricing` | Marketing pricing page | CSR | Comparison table |
| `/features` | Feature showcase | CSR | Feature cards |
| `/auth/callback` | OAuth callback handler | CSR | -- |
| `/recuperar-senha` | Password recovery | CSR | Form |
| `/redefinir-senha` | Password reset form | CSR | Form with Zod |
| `/blog` | Blog listing | SSC | BlogListClient (CSR island) |
| `/blog/[slug]` | Individual blog article | SSC | BlogArticleLayout |
| `/blog/programmatic/[setor]` | Programmatic SEO per sector | SSC | -- |
| `/blog/programmatic/[setor]/[uf]` | Programmatic SEO per sector+UF | SSC | -- |
| `/blog/licitacoes` | Licitacoes blog listing | SSC | -- |
| `/blog/licitacoes/[setor]/[uf]` | Licitacoes per sector+UF | SSC | -- |
| `/blog/panorama/[setor]` | Sector panorama | SSC | -- |
| `/licitacoes` | SEO licitacoes landing | SSC | LicitacoesPreview |
| `/licitacoes/[setor]` | SEO per-sector page | SSC | -- |
| `/como-avaliar-licitacao` | Content marketing page | SSC | ContentPageLayout |
| `/como-evitar-prejuizo-licitacao` | Content marketing page | SSC | ContentPageLayout |
| `/como-filtrar-editais` | Content marketing page | SSC | ContentPageLayout |
| `/como-priorizar-oportunidades` | Content marketing page | SSC | ContentPageLayout |
| `/sobre` | About page | CSR | -- |
| `/termos` | Terms of service | SSC | -- |
| `/privacidade` | Privacy policy | SSC | -- |
| `/ajuda` | Help center | CSR | AjudaFaqClient |
| `/status` | System status page | SSC + CSR island | StatusContent |

### Protected Pages (auth required via middleware)

| Route | Purpose | Key Components | Data Fetching |
|-------|---------|----------------|---------------|
| `/buscar` | Main search page | SearchForm, SearchResults, SearchStateManager, UfProgressGrid, 41+ buscar components, 9 custom hooks | POST /buscar, SSE /buscar-progress, SWR /setores |
| `/dashboard` | User analytics | DashboardStatCards, DashboardTimeSeriesChart, InsightCards | useFetchWithBackoff /analytics |
| `/pipeline` | Opportunity kanban | PipelineKanban (dynamic), PipelineMobileTabs | usePipeline SWR |
| `/historico` | Search history | Session list with status badges | useSessions SWR |
| `/mensagens` | Message center | Conversation list + detail | useConversations SWR |
| `/alertas` | Alert management | AlertCard, AlertFormModal | useAlerts SWR |
| `/onboarding` | 3-step wizard | react-hook-form + Zod | POST /first-analysis |
| `/conta` | Redirect to /conta/perfil | -- | -- |
| `/conta/perfil` | Profile settings | Form | SWR /me |
| `/conta/dados` | Company data | Form | SWR /me |
| `/conta/seguranca` | Security (password, MFA) | MfaSetupWizard | SWR /mfa |
| `/conta/plano` | Subscription management | AlertPreferences | SWR /subscription-status |
| `/conta/equipe` | Team/organization | InviteMemberModal | useOrganization SWR |

### Admin Pages (admin role required)

| Route | Purpose |
|-------|---------|
| `/admin` | User management, plan assignment |
| `/admin/cache` | Cache inspection and management |
| `/admin/metrics` | Prometheus metrics viewer |
| `/admin/slo` | SLO monitoring dashboard |
| `/admin/emails` | Email template management |
| `/admin/partners` | Partner management |

**Total: ~47 page.tsx files** (more than the initial 22 estimate, due to sub-routes and SEO programmatic pages).

---

## 3. Component Architecture

### Component Hierarchy (text-based)

```
layout.tsx (RootLayout - SSC)
  NavigationShell
    Sidebar (desktop, lg:)
    BottomNav (mobile, < lg)
    MfaEnforcementBanner
    {page content}
    Footer (minimal, logged area)

/buscar page hierarchy:
  HomePageContent
    header (sticky, custom)
    MobileDrawer
    PullToRefresh
      TrialExpiringBanner
      SearchForm
        SearchFormHeader (sector select, search mode toggle, term input)
        SearchFormActions (search button, save, export)
        SearchCustomizePanel (UF, date, status, modalidade, valor filters)
      OnboardingBanner / OnboardingSuccessBanner / OnboardingEmptyState
      SearchErrorBoundary
        SearchResults
          SearchStateManager (dynamic import)
          ResultsHeader
          ResultsToolbar
          ResultsFilters
          ResultsList -> ResultCard (per item)
          ResultsFooter
    BuscarModals (save, keyboard, upgrade, PDF, trial, payment recovery)
    footer (feature-rich, buscar-specific)
```

### Shared Components (`components/`)

| Category | Components |
|----------|-----------|
| **UI Primitives** | `button.tsx` (CVA variants), `Input.tsx`, `Label.tsx`, `Pagination.tsx`, `CurrencyInput.tsx` |
| **Layout** | `NavigationShell`, `Sidebar`, `BottomNav`, `MobileDrawer`, `PageHeader`, `PageErrorBoundary` |
| **Auth** | `AuthLoadingScreen`, `TotpVerificationScreen`, `MfaSetupWizard`, `MfaEnforcementBanner` |
| **Billing** | `PaymentFailedBanner`, `TrialUpsellCTA`, `TrialPaywall`, `CancelSubscriptionModal`, `PlanToggle`, `TrustSignals` |
| **Feedback** | `ErrorBoundary`, `ErrorStateWithRetry`, `EmptyState`, `FeedbackButtons` |
| **Display** | `ViabilityBadge`, `CompatibilityBadge`, `OnboardingTourButton`, `ProfileCompletionPrompt`, `ProfileProgressBar`, `ProfileCongratulations` |
| **Data Viz** | `SWRProvider`, `TestimonialSection` |

### Page-Specific Components

- **`app/buscar/components/`**: 41 files -- the most complex page by far
- **`app/buscar/hooks/`**: 9 hooks (useSearch, useSearchOrchestration, useSearchExecution, useSearchExport, useSearchFilters, useSearchPersistence, useSearchRetry, useSearchSSEHandler, useUfProgress)
- **`app/dashboard/components/`**: 10+ files (stat cards, charts, error states, view toggle)
- **`app/pipeline/`**: PipelineKanban, PipelineCard, PipelineColumn, PipelineMobileTabs
- **`app/alertas/components/`**: AlertCard, AlertFormModal, AlertsEmptyState, UFMultiSelect, KeywordsInput
- **`app/components/landing/`**: HeroSection, OpportunityCost, BeforeAfter, HowItWorks, StatsSection, SectorsGrid, LandingNavbar, etc.

### Component Patterns

- **Controlled components**: All form inputs are controlled (state lifted to parent or react-hook-form)
- **CVA (class-variance-authority)**: Used for `Button` component variants (primary, secondary, destructive, ghost, link, outline)
- **Dynamic imports**: Pipeline kanban, SearchStateManager, TotpVerification (lazy-loaded to reduce bundle)
- **Error boundaries**: Global `error.tsx`, `global-error.tsx`, per-route `error.tsx`, `SearchErrorBoundary`, `PageErrorBoundary`
- **Loading states**: `loading.tsx` files for buscar, dashboard, historico, pipeline, (protected) group

### Design System Assessment

**Status: Emerging but incomplete.**

Strengths:
- Well-defined CSS custom properties (50+ variables in globals.css) with WCAG contrast documentation
- Semantic Tailwind tokens mapped to CSS vars (canvas, ink, brand-*, surface-*, success, error, warning)
- `Button` component using CVA with 6 variants and 4 sizes
- Framer Motion animation library (`lib/animations/`) with 12+ reusable variants
- Dark mode support via `.dark` class with full variable overrides
- Gem palette for premium UI elements
- Chart palette (10 colors) for data visualization

Gaps:
- Only 6 UI primitive components (button, input, label, pagination, currency input, slot)
- No Card, Badge, Tabs, Select, Modal, or Dropdown primitives -- these are built inline per page
- 1,417+ occurrences of `bg-[var(--` and `text-[var(--` across 100+ files instead of using semantic Tailwind classes
- Missing component documentation / Storybook

---

## 4. State Management

### Architecture

SmartLic uses a **hook-based state architecture** without a global store (no Redux/Zustand):

| Layer | Tool | Purpose |
|-------|------|---------|
| **Server state** | SWR v2.4 | API data caching, revalidation, error retry |
| **Auth state** | Supabase SSR + React Context (AuthProvider) | Session, user, signIn/signOut |
| **User composite** | UserContext | Composes auth + plan + quota + trial into single context |
| **Local UI state** | useState/useReducer | Form inputs, toggles, modals |
| **URL state** | useSearchParams | Search mode, auto-search flag |
| **Persistent state** | localStorage (via `lib/storage.ts` safe wrappers) | Theme, sidebar collapsed, plan cache, search cache |
| **Real-time** | SSE (EventSource) | Search progress, live updates |

### SWR Configuration

```typescript
// Global config (SWRProvider):
revalidateOnFocus: false
dedupingInterval: 5000
errorRetryCount: 3
```

Fetcher: Custom `fetcher.ts` with `FetchError` class (status + info).

### Custom Hooks (28 hooks total)

| Hook | Source | Purpose |
|------|--------|---------|
| useSearchOrchestration | buscar/hooks/ | Master orchestrator for search page -- composes 8+ sub-hooks |
| useSearch | buscar/hooks/ | Core search state (result, loading, error) |
| useSearchExecution | buscar/hooks/ | API call orchestration |
| useSearchSSEHandler | buscar/hooks/ | SSE connection management |
| useSearchFilters | buscar/hooks/ | Sector fetching with SWR + fallback chain |
| useSearchPersistence | buscar/hooks/ | localStorage persistence of search state |
| useSearchRetry | buscar/hooks/ | Auto-retry with exponential backoff |
| useSearchExport | buscar/hooks/ | Excel/Google Sheets export |
| useUfProgress | buscar/hooks/ | Per-UF progress tracking |
| usePlan | hooks/ | Plan info with localStorage cache (1hr TTL) |
| useQuota | hooks/ | Usage quota tracking |
| useTrialPhase | hooks/ | Trial lifecycle (active/expiring/limited/expired) |
| usePipeline | hooks/ | Pipeline CRUD with SWR |
| useSessions | hooks/ | Search history with SWR |
| useConversations | hooks/ | Messaging with SWR |
| useAlerts | hooks/ | Alert management with SWR |
| useAnalytics | hooks/ | Mixpanel event tracking |
| useFetchWithBackoff | hooks/ | Generic fetch with exponential backoff (2s-30s cap, max 5 retries) |
| useIsMobile | hooks/ | Media query hook (768px breakpoint) |
| useFeatureFlags | hooks/ | Feature flag checking |
| useProfileCompleteness | hooks/ | Profile completion % |
| useProfileContext | hooks/ | Profile context (sector, UFs) |
| useShepherdTour | hooks/ | Onboarding tour management |
| useKeyboardShortcuts | hooks/ | Keyboard shortcut handling |
| useNavigationGuard | hooks/ | Unsaved changes warning |
| useBroadcastChannel | hooks/ | Cross-tab communication |
| useServiceWorker | hooks/ | SW registration |
| usePublicMetrics | hooks/ | Public metrics fetching |

### Data Flow Pattern

1. Pages fetch data via SWR hooks or useFetchWithBackoff
2. Auth token is passed through API proxy routes (frontend/app/api/*)
3. Proxy routes forward to BACKEND_URL with auth headers
4. SSE uses a separate connection for real-time progress

### Cache Strategy

- **SWR**: In-memory with 5s deduplication, 3 retry attempts
- **localStorage plan cache**: 1hr TTL, prevents UI downgrade flicker
- **localStorage search cache**: Partial results cache for interrupted searches
- **localStorage theme**: Persisted theme preference (smartlic-theme key)
- **localStorage sidebar**: Collapsed state persistence

---

## 5. API Integration

### Proxy Pattern

All API calls go through Next.js API routes (`frontend/app/api/**`), which proxy to `BACKEND_URL`. This is a **security-critical pattern**: the backend URL is never exposed to the client.

**Factory pattern**: `lib/create-proxy-route.ts` provides a declarative config to create route handlers, eliminating boilerplate across 59 API route files. Features:
- Auth header extraction and validation
- Server-side token refresh (`allowRefresh` option)
- X-Correlation-ID forwarding
- Query parameter forwarding with strip list
- Error sanitization (CRIT-017)
- Network error handling

**59 API route files** covering: buscar, buscar-progress, buscar-results, download, feedback, analytics, pipeline, sessions, alerts, conversations, billing, plans, subscriptions, admin, auth, health, status, profile, onboarding, export, mfa, organizations, metrics.

### Error Handling Patterns

- `lib/error-messages.ts`: Centralized user-friendly error mapping + `SearchError` interface with error codes
- `lib/proxy-error-handler.ts`: Sanitizes infrastructure errors (HTML 502s, etc.) before forwarding
- `getUserFriendlyError()`: Maps raw errors to Portuguese messages
- `translateAuthError()`: Maps Supabase auth errors to user-friendly PT-BR messages
- `isTransientError()`: Detects 502/503/504 + network errors for auto-retry
- `getMessageFromErrorCode()`: Maps structured error codes to messages

### Loading States

- Page-level `loading.tsx` files: 5 (buscar, dashboard, historico, pipeline, protected group)
- Component-level: `AuthLoadingScreen`, `EnhancedLoadingProgress`, `LoadingProgress`, `LoadingResultsSkeleton`
- Skeleton patterns: Used in pipeline (5 columns), dashboard (stat cards), loading.tsx files
- Spinner: Consistent `animate-spin` + `border-b-2 border-brand-blue` pattern

---

## 6. Styling & Design System

### Tailwind Usage

- **Configuration**: `tailwind.config.ts` extends default theme with custom colors, fonts, shadows, animations, border-radius
- **Dark mode**: Class-based (`darkMode: "class"`), with full CSS variable overrides in globals.css `.dark {}` block
- **Plugin**: `@tailwindcss/typography` for prose content (blog)

### Color Palette

| Token | Light | Dark | Purpose |
|-------|-------|------|---------|
| canvas | #ffffff | #121212 | Page background |
| ink | #1e2d3b | #e8eaed | Primary text |
| ink-secondary | #3d5975 | #a8b4c0 | Secondary text |
| ink-muted | #6b7a8a | #8494a7 | Muted text |
| brand-navy | #0a1e3f | -- | Primary brand |
| brand-blue | #116dff | -- | Accent/CTA |
| brand-blue-hover | #0d5ad4 | -- | Hover state |
| brand-blue-subtle | #e8f0ff | rgba(17,109,255,0.12) | Subtle backgrounds |
| surface-0 | #ffffff | #121212 | Base surface |
| surface-1 | #f7f8fa | #1a1d22 | Elevated surface |
| surface-2 | #f0f2f5 | #242830 | Card backgrounds |
| success | #16a34a | #22c55e | Success |
| error | #dc2626 | #f87171 | Error |
| warning | #ca8a04 | #facc15 | Warning |

All colors documented with WCAG contrast ratios inline in globals.css.

### Typography

| Font | Variable | Usage |
|------|----------|-------|
| DM Sans | `--font-body` | Body text (preloaded) |
| Fahkwang | `--font-display` | Headings/display (deferred) |
| DM Mono | `--font-data` | Data/code (deferred) |

Fluid typography scale: hero (40-72px), h1 (32-56px), h2 (24-40px), h3 (20-28px), body-lg (18-20px).

### Spacing

4px base grid documented in tailwind.config.ts (1=4px, 2=8px, 3=12px, 4=16px, 6=24px, 8=32px, 16=64px). Section spacing: sm=64px, lg=96px, gap=128px.

### Border Radius System

| Token | Value | Usage |
|-------|-------|-------|
| input | 4px | Form inputs |
| button | 6px | Buttons |
| card | 8px | Cards |
| modal | 12px | Modals/dialogs |

### Animation Patterns

**CSS Keyframes** (globals.css): fadeInUp, fadeIn, gradient, shimmer, float, slideUp, scaleIn, confetti-dot, bounce-gentle, shepherdFadeIn.

**Framer Motion** (`lib/animations/framerVariants.ts`): 12 reusable variants -- fadeInUp, fadeIn, scaleIn, slideInLeft, slideInRight, lift, tilt3D, glow, staggerContainer, counterVariant, rotateIn, bounceIn.

**Tailwind animations** (config): fade-in-up, gradient, shimmer, float, slide-up, scale-in, slide-in-right, bounce-gentle.

**CSS utilities**: `.hover-lift`, `.hover-glow`, `.hover-scale`, `.text-gradient`, stagger delays (1-5).

**Reduced motion**: `@media (prefers-reduced-motion: reduce)` in globals.css zeroes all animation/transition durations. Framer Motion respects this in `SectorsGrid.tsx` and `useInView.ts`.

### Responsive Design

- Breakpoints: default (mobile), `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1280px)
- Mobile-first approach throughout
- `useIsMobile()` hook for JS-based responsive logic (768px breakpoint)
- Bottom navigation for mobile, sidebar for desktop (via NavigationShell)
- PullToRefresh enabled mobile-only (disabled via pointer-events on desktop)
- Mobile date picker with custom rdp styles (44px touch targets)
- Mobile drawer pattern for menu overflow

---

## 7. Accessibility Audit

### Strengths

| Feature | Implementation | WCAG Level |
|---------|---------------|------------|
| Skip navigation link | `<a href="#main-content">` in layout.tsx | 2.4.1 AAA |
| Focus visible | 3px solid ring, 2px offset (globals.css) | 2.4.13 AAA |
| Color contrast | All text tokens documented with ratios (all AA+) | 1.4.3 AA |
| Touch targets | `min-height: 44px` on buttons, date inputs, selects | 2.5.8 AAA |
| Language | `lang="pt-BR"` on html element | 3.1.1 A |
| Reduced motion | `@media (prefers-reduced-motion: reduce)` resets all durations | 2.3.3 AAA |
| Focus trap | BottomNav drawer has full focus trap + Escape | 2.1.2 A |
| Live regions | `aria-live` on 14+ components (search progress, errors, banners) | 4.1.3 AA |
| ARIA labels | 442+ ARIA attributes across 111 files | Various |
| Error identification | Color + icon + text for all error states | 3.3.1 A |
| Form validation | Zod schemas with inline error messages (signup, onboarding) | 3.3.1 A |
| Page titles | Metadata title template: `%s | SmartLic` | 2.4.2 A |
| Landmarks | `main`, `nav`, `header`, `footer` used correctly | 1.3.1 A |
| Icon-only buttons | TypeScript enforces `aria-label` when `size="icon"` on Button | 1.1.1 A |

### Gaps

| Issue | Severity | Details | Estimated Fix |
|-------|----------|---------|---------------|
| Shepherd.js tour arrow hidden | LOW | `.shepherd-arrow { display: none }` removes visual connection to target | 1h |
| Some inline SVG icons lack `aria-hidden="true"` | MEDIUM | Decorative SVGs in some components may be announced by screen readers | 3h |
| Focus management after modal close | MEDIUM | Not all modals return focus to trigger (BottomNav does, BuscarModals unclear) | 4h |
| Dashboard icon duplication in BottomNav | LOW | Dashboard uses Search icon instead of LayoutDashboard in mobile nav | 0.5h |
| No visible focus indicator on PlanToggle radio buttons | MEDIUM | Custom radio group may lack keyboard-visible focus ring | 2h |

---

## 8. Performance Assessment

### Bundle Optimization

| Technique | Status | Details |
|-----------|--------|---------|
| Code splitting (dynamic import) | GOOD | PipelineKanban, SearchStateManager, TotpVerificationScreen |
| Font optimization | GOOD | DM Sans preloaded, Fahkwang/DM Mono deferred (`preload: false`) |
| Image optimization | POOR | Only 1 file uses `next/image` (HeroSection). No Image component in other pages |
| Standalone output | GOOD | `output: "standalone"` for Railway deployment |
| CSS purging | GOOD | Tailwind content paths configured correctly |
| Size limiting | GOOD | `@size-limit/file` configured in devDependencies |
| Lighthouse CI | GOOD | `@lhci/cli` configured with `lhci autorun` script |

### Lazy Loading

- **Pipeline kanban**: Dynamic import with skeleton fallback
- **SearchStateManager**: Dynamic import (SSR: false)
- **TotpVerificationScreen**: Dynamic import (SSR: false)
- **Shepherd.js tour**: Loaded via hook, not in initial bundle
- **Framer Motion**: Used in landing pages primarily, not in critical auth pages

### Concerns

| Issue | Severity | Details | Estimated Fix |
|-------|----------|---------|---------------|
| `next/image` barely used | HIGH | Only HeroSection uses Image component. Blog, landing, about pages likely use raw `<img>` or no images -- missing WebP/AVIF conversion and lazy loading | 8h |
| 59 API route files | MEDIUM | Each creates a serverless function. Most use `createProxyRoute` factory which is efficient, but the sheer number may increase cold start times | 4h (consolidate similar routes) |
| Framer Motion bundle | LOW | framer-motion 12 is ~32KB gzipped. Only used in landing/marketing pages. Could be code-split further | 2h |
| Recharts bundle | LOW | ~45KB gzipped. Only used in dashboard. Already isolated to dashboard page | -- |
| lucide-react tree-shaking | GOOD | Individual icon imports used throughout (tree-shakeable) | -- |

---

## 9. UX Issues & Technical Debt

### CRITICAL

| # | Issue | Location | Details | Estimate |
|---|-------|----------|---------|----------|
| C1 | Inline `var()` instead of semantic Tailwind classes | 100+ files | 1,417+ occurrences of `bg-[var(--*)]` and `text-[var(--*)]`. Should use mapped Tailwind tokens (e.g., `bg-canvas` instead of `bg-[var(--canvas)]`, `text-ink` instead of `text-[var(--ink)]`). DEBT-012 partially addressed this but adoption is incomplete | 40h |

### HIGH

| # | Issue | Location | Details | Estimate |
|---|-------|----------|---------|----------|
| H1 | Missing UI component library | `components/ui/` | Only 6 primitives (Button, Input, Label, Pagination, CurrencyInput, Slot). Missing Card, Badge, Tabs, Select, Modal, Dropdown, Toast wrapper, Dialog, Tooltip (app/components/Dialog.tsx is one-off). Components like modals, selects, and badges are rebuilt per page | 24h |
| H2 | Buscar page complexity | `app/buscar/` | 41 components + 9 hooks + orchestration pattern. useSearchOrchestration alone composes 8+ hooks. While decomposition is good, the sheer prop drilling through SearchForm (30+ props), SearchResults, and BuscarModals is a maintenance burden | 16h (refactor to context) |
| H3 | Inconsistent error page pattern | Various `error.tsx` | Root error.tsx has full UI with Sentry reporting. Per-route error.tsx files vary in quality. Some are minimal, some don't report to Sentry | 4h |
| H4 | Raw hex colors in global-error.tsx and ThemeProvider | `app/global-error.tsx`, `ThemeProvider.tsx` | 5 occurrences of raw hex (#116dff, #0a1e3f) outside the design token system | 1h |
| H5 | Dual footer pattern | `buscar/page.tsx` + `NavigationShell.tsx` | Buscar page has its own feature-rich footer AND NavigationShell has a minimal footer. Intentional (documented as SAB-013/DEBT-105) but confusing for users seeing two footers | 4h |
| H6 | useIsMobile initial false flash | `hooks/useIsMobile.ts` | useState(false) means SSR/initial render always assumes desktop. This causes layout shift when client hydrates on mobile | 2h |
| H7 | No image optimization strategy | Throughout | Only 1 usage of `next/image` in the entire codebase. Marketing pages, blog, about likely have unoptimized images | 8h |

### MEDIUM

| # | Issue | Location | Details | Estimate |
|---|-------|----------|---------|----------|
| M1 | Inconsistent component locations | `app/components/` vs `components/` | Two component directories with no clear boundary. Some shared components are in `app/components/` (Footer, Dialog, CustomSelect) while others are in `components/` (EmptyState, PageHeader). Imports use mixed relative paths | 8h |
| M2 | Blog/SEO pages lack loading states | `/blog/*`, `/licitacoes/*` | Server components have no loading.tsx files for streaming fallback | 2h |
| M3 | Duplicate animation definitions | `globals.css` + `tailwind.config.ts` | fadeInUp/fadeIn defined both as CSS @keyframes and Tailwind keyframes. Shimmer, float also duplicated | 2h |
| M4 | Some pages lack proper PageErrorBoundary | Various | Not all protected pages wrap content in PageErrorBoundary | 3h |
| M5 | Missing aria-current on Sidebar nav items | `Sidebar.tsx` | BottomNav uses `aria-current="page"` but Sidebar does not set it on active links | 1h |
| M6 | Feature-gated pages still routable | `/alertas`, `/mensagens` | SHIP-002 AC9 hides these from navigation but the routes still exist and render. Should show "coming soon" or redirect | 2h |
| M7 | Admin pages lack responsive design | `app/admin/*` | Admin metrics, SLO, partners pages use complex tables that likely overflow on mobile | 8h |
| M8 | No Storybook or component playground | -- | No way to browse, test, or demo components in isolation | 16h initial setup |
| M9 | Pull-to-refresh desktop disabled via pointer-events | `globals.css` | Fragile CSS approach. Better to conditionally render the component | 1h |
| M10 | Shepherd.js custom theme uses raw Tailwind (`bg-white`, `text-gray-700`) | `globals.css` | Not using design token CSS variables, will look wrong in custom themes | 2h |
| M11 | react-hook-form in devDependencies | `package.json` | react-hook-form is listed in devDependencies but used in production pages (signup, onboarding). Should be in dependencies | 0.5h |

### LOW

| # | Issue | Location | Details | Estimate |
|---|-------|----------|---------|----------|
| L1 | No automated accessibility testing in CI | -- | @axe-core/playwright is installed but unclear if integrated into CI pipeline | 4h |
| L2 | Tailwind `content` paths include `pages/` | `tailwind.config.ts` | `pages/` directory does not exist (App Router), unnecessary scan | 0.5h |
| L3 | Some hooks import from app/ into components/ | `BottomNav.tsx`, `Sidebar.tsx` | Components in `components/` import from `app/components/AuthProvider` -- circular dependency risk | 4h |
| L4 | NProgress library for page transitions | `app/components/NProgressProvider.tsx` | Lightweight but could be replaced with Next.js built-in loading indicators | 2h |
| L5 | Multiple date formatting patterns | Various | `timeAgo()` in mensagens, `formatDate()` in dashboard, `toLocaleDateString()` inline. Should consolidate | 3h |
| L6 | Sonner toast + custom error banners | Various | Some errors show via toast, some via inline banners. No consistent strategy | 4h |
| L7 | SearchForm.types.ts has 30+ prop definitions | `buscar/components/SearchForm.types.ts` | Indicates the component needs further decomposition or context-based state | Part of H2 |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total page.tsx files | ~47 |
| Client-rendered pages | 26 |
| Server-rendered pages | ~21 |
| API proxy routes | 59 |
| Custom hooks | 28 |
| Buscar-specific components | 41 |
| Buscar-specific hooks | 9 |
| UI primitive components | 6 |
| CSS custom properties | 50+ |
| ARIA attributes | 442+ across 111 files |
| aria-live regions | 55 across 31 files |
| Test files | 135 (5583 passing) |
| loading.tsx files | 5 |
| error.tsx files | 8+ |
| Framer Motion variants | 12 reusable |
| Total findings | 1 CRITICAL, 7 HIGH, 11 MEDIUM, 7 LOW |
| Estimated total remediation | ~180 hours |

---

## Appendix: Key File Paths

| Category | Path |
|----------|------|
| Root layout | `frontend/app/layout.tsx` |
| Middleware (auth + CSP) | `frontend/middleware.ts` |
| Tailwind config | `frontend/tailwind.config.ts` |
| CSS variables | `frontend/app/globals.css` |
| Proxy factory | `frontend/lib/create-proxy-route.ts` |
| Error messages | `frontend/lib/error-messages.ts` |
| SWR provider | `frontend/components/SWRProvider.tsx` |
| User context | `frontend/contexts/UserContext.tsx` |
| Auth provider | `frontend/app/components/AuthProvider.tsx` |
| Navigation shell | `frontend/components/NavigationShell.tsx` |
| Button (CVA) | `frontend/components/ui/button.tsx` |
| Animation variants | `frontend/lib/animations/framerVariants.ts` |
| Search orchestrator | `frontend/app/buscar/hooks/useSearchOrchestration.ts` |
| Plans config | `frontend/lib/plans.ts` |
| Form schemas (Zod) | `frontend/lib/schemas/forms.ts` |
