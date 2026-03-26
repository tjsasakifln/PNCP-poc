# SmartLic Frontend Specification & UX Audit

**Date:** 2026-03-23 (updated from 2026-03-21 audit)
**Auditor:** @ux-design-expert (Uma) -- Brownfield Discovery Phase 3
**Stack:** Next.js 16, React 18, TypeScript 5.9, Tailwind CSS 3, Framer Motion, Recharts, Supabase SSR, @dnd-kit, Shepherd.js
**Language:** pt-BR (user-facing), English (code/docs)

---

## 1. Architecture Overview

### 1.1 Rendering Strategy

All pages use **client-side rendering** (`"use client"` directive). Zero Server Components found (`"use server"` not present in any file). The root layout (`app/layout.tsx`) is async only to read the CSP nonce header from middleware. This is a significant optimization opportunity: landing, blog, legal, and pricing pages could use RSC for better TTFB and SEO.

### 1.2 Provider Hierarchy (app/layout.tsx)

```
<html lang="pt-BR" suppressHydrationWarning>
  <body>
    <AnalyticsProvider>             -- Mixpanel + GA4 event tracking
      <AuthProvider>                -- Supabase auth session management
        <SWRProvider>               -- SWR global configuration
          <UserProvider>            -- Unified user context (auth + plan + quota + trial)
            <ThemeProvider>         -- Dark/light mode (localStorage-persisted)
              <NProgressProvider>   -- Page transition progress bar
                <BackendStatusProvider>   -- Backend health polling (30s interval)
                  <SessionExpiredBanner />
                  <PaymentFailedBanner />
                  <NavigationShell>       -- Sidebar + BottomNav (protected routes only)
                    {children}
                  </NavigationShell>
                  <Toaster position="bottom-center" richColors closeButton />
                  <CookieConsentBanner />
```

Provider nesting depth is **9 levels**. Each provider serves a distinct purpose. `UserContext` (DEBT-011 FE-006) consolidates 4 hooks (auth + plan + quota + trial) into one context.

Additional root-level elements:
- Skip navigation link (`Pular para conteudo principal`) targeting `#main-content` (WCAG 2.4.1)
- Google Analytics 4 with nonce-based CSP compliance
- Microsoft Clarity for heatmaps/session recordings
- Schema.org structured data
- RSS feed discovery link
- Theme initialization script (nonce-based, migrates legacy `bidiq-theme` key)

### 1.3 Navigation Architecture

`NavigationShell` (`components/NavigationShell.tsx`) conditionally renders navigation chrome:

- **Public routes** (`/`, `/login`, `/signup`, `/planos`, `/ajuda`, etc.): No sidebar or bottom nav.
- **Protected routes** (`/buscar`, `/dashboard`, `/pipeline`, `/historico`, `/conta`, `/admin`): Desktop sidebar + mobile bottom nav.
- Feature-gated routes (`/alertas`, `/mensagens`) removed from nav (SHIP-002 AC9) but still accessible via direct URL.

The protected layout (`app/(protected)/layout.tsx`) provides: auth guard (redirect to `/` if unauthenticated), `AppHeader` with Breadcrumbs, first-time onboarding redirect to `/onboarding`.

**Architecture note:** The `/buscar` page bypasses the `(protected)` route group and implements its own header and auth guard directly. This creates a dual-header pattern inconsistency.

### 1.4 Security (middleware.ts)

- **CSP enforcement** with per-request nonce (`'nonce-{uuid}'` + `'strict-dynamic'`)
- **Route protection** via `supabase.auth.getUser()` (server-validated, not `getSession()`)
- **Security headers:** HSTS preload, X-Frame-Options DENY, COOP same-origin, X-DNS-Prefetch-Control off, Permissions-Policy
- **CSP violation reporting** to `/api/csp-report` endpoint
- **Canonical domain redirect:** `*.railway.app` -> `smartlic.tech` (301)
- Distinguishes "never logged in" vs "session expired" via cookie inspection
- Accepted risk: `style-src 'unsafe-inline'` required by Tailwind/Next.js runtime (DEBT-116)

---

## 2. Page Inventory

### 2.1 Public Pages (15+)

| Route | Purpose | Notable |
|-------|---------|---------|
| `/` | Landing page | 13 landing components (HeroSection, HowItWorks, SectorsGrid, etc.) |
| `/login` | Authentication | Password + magic link + TOTP MFA, react-hook-form + zod |
| `/signup` | Registration | react-hook-form + zod, InstitutionalSidebar |
| `/auth/callback` | OAuth callback | Supabase auth code exchange |
| `/recuperar-senha` | Password recovery | Email form |
| `/redefinir-senha` | Password reset | New password form |
| `/planos` | Pricing | PlanCard, billing period selector (monthly/semiannual/annual) |
| `/planos/obrigado` | Post-checkout | Thank you page |
| `/pricing` | Alternative pricing | Marketing layout |
| `/features` | Feature showcase | FeaturesContent with Framer Motion |
| `/sobre` | About page | Company info |
| `/termos` | Terms of service | Legal text |
| `/privacidade` | Privacy policy | Legal text |
| `/ajuda` | Help center | FAQ with structured data |
| `/status` | System status | Backend health + source availability |

### 2.2 Protected Pages (8 core + sub-routes)

| Route | Purpose | Key Pattern |
|-------|---------|-------------|
| `/buscar` | **Main search** (primary feature) | 44 components, 9 hooks, SSE dual-connection, pull-to-refresh |
| `/dashboard` | Analytics dashboard | useFetchWithBackoff, Recharts (dynamic import), InsightCards |
| `/pipeline` | Opportunity kanban | @dnd-kit (dynamic import), 5-stage drag-and-drop, mobile tabs |
| `/historico` | Search history | Session list, result replay |
| `/onboarding` | 3-step wizard | react-hook-form + zod, auto-search launch |
| `/conta` | Account hub | Tab router: perfil, dados, plano, equipe, seguranca |
| `/conta/plano` | Plan management | Subscription status, AlertPreferences |
| `/conta/seguranca` | Security settings | MFA TOTP setup (MfaSetupWizard) |
| `/mensagens` | Messaging | Feature-gated (hidden in nav, SHIP-002) |
| `/alertas` | Alert management | Feature-gated (hidden in nav, SHIP-002) |

### 2.3 Admin Pages (6)

| Route | Purpose |
|-------|---------|
| `/admin` | Admin dashboard |
| `/admin/cache` | Cache management |
| `/admin/emails` | Email management |
| `/admin/metrics` | System metrics |
| `/admin/partners` | Partner management |
| `/admin/slo` | SLO monitoring |

### 2.4 SEO/Content Pages (12+)

| Route | Type |
|-------|------|
| `/blog`, `/blog/[slug]` | Blog index + 30 articles |
| `/blog/licitacoes`, `/blog/licitacoes/[setor]/[uf]` | Programmatic procurement pages |
| `/blog/panorama/[setor]` | Sector panorama |
| `/blog/programmatic/[setor]`, `/blog/programmatic/[setor]/[uf]` | Programmatic SEO |
| `/licitacoes`, `/licitacoes/[setor]` | Sector listing pages |
| `/como-avaliar-licitacao`, `/como-evitar-prejuizo-licitacao`, `/como-filtrar-editais`, `/como-priorizar-oportunidades` | Content marketing |

**Total: ~47 unique route patterns** across public, protected, admin, and content categories.

---

## 3. Component Architecture

### 3.1 Component Organization

```
app/components/           (49 app-level components)
  landing/                (13 landing-page sections)
  AuthProvider.tsx         Supabase auth context
  BackendStatusIndicator.tsx  Health polling, context provider
  LicitacaoCard.tsx        Search result display
  ...

components/               (35+ shared components)
  ui/                     (6 primitives: Button, Input, Label, CurrencyInput, Pagination, examples)
  auth/                   (3: MfaEnforcementBanner, MfaSetupWizard, TotpVerificationScreen)
  billing/                (4: PaymentFailedBanner, PaymentRecoveryModal, TrialPaywall, TrialUpsellCTA)
  account/                (1: CancelSubscriptionModal)
  reports/                (1: PdfOptionsModal)
  skeletons/              (3: AdminPageSkeleton, ContaPageSkeleton, PlanosPageSkeleton)
  layout/                 (layout primitives)
  blog/                   (blog-specific components)
  org/                    (organization management, InviteMemberModal)
  subscriptions/          (plan cards, toggles)
  Sidebar.tsx             Desktop nav (collapsible, lucide-react icons, state persisted)
  BottomNav.tsx           Mobile nav (5 tabs)
  MobileDrawer.tsx        Slide-over menu
  ErrorBoundary.tsx       Class component with Sentry integration
  PageErrorBoundary.tsx   Page-level error wrapper
  ErrorStateWithRetry.tsx Reusable error display with retry
  EmptyState.tsx          Generic empty state
  FeedbackButtons.tsx     Thumbs up/down per result
  DeepAnalysisModal.tsx   Detailed bid analysis modal
  ProfileCompletionPrompt.tsx  Progressive profiling (21,930 bytes)
  ...

app/buscar/               (LARGEST feature module)
  page.tsx                (270 lines, orchestrator)
  hooks/                  (9 custom hooks, 3,287 LOC total)
  components/             (44 components)
    search-results/       (9 sub-components: ResultCard, ResultsList, etc.)
  types/                  (2 type definition files)
```

**Total estimated: ~240 components across all directories.**

### 3.2 Search Module (app/buscar/) -- Deep Dive

The search page is the core product feature and the most complex module.

**Hook Architecture (9 hooks composing the search lifecycle):**

| Hook | LOC | Responsibility |
|------|-----|---------------|
| `useSearchOrchestration` | ~600 | Top-level orchestrator: composes all other hooks + trial/tour/keyboard state |
| `useSearchExecution` | ~770 | Core search logic: API call, SSE, retry, error handling |
| `useSearchFilters` | ~600 | Filter state: sector, UF, value, modalidade, date range, sector fetch |
| `useSearch` | ~398 | Composes execution + SSE + retry + export |
| `useSearchExport` | ~304 | Excel download + Google Sheets export |
| `useSearchSSEHandler` | ~229 | SSE event parsing, state machine updates |
| `useSearchPersistence` | ~193 | localStorage save/restore of search state |
| `useSearchRetry` | ~144 | Auto-retry with countdown timer (3 attempts: 10s, 20s, 30s) |
| `useUfProgress` | ~49 | Per-UF progress tracking from SSE events |

**Component Decomposition (TD-007):**
`SearchResults` (259 lines) delegates to well-structured sub-components: ResultsHeader, ResultsToolbar, ResultsFilters, ResultCard, ResultsList, ResultsLoadingSection, ResultsFooter, ResultsPagination.

**Large components (potential refactoring targets):**
- `ValorFilter.tsx` (478 lines) -- dual-slider with currency formatting, presets, validation
- `EnhancedLoadingProgress.tsx` (391 lines) -- multi-phase loading with SSE progress visualization
- `SearchFormHeader.tsx` (294 lines) -- form header with filter toggles and search configuration

### 3.3 Dashboard Module (app/dashboard/)

8 sub-components with clear separation:
- `DashboardStatCards` -- KPI cards (searches, pipeline items, value analyzed)
- `DashboardTimeSeriesChart` -- Recharts time series (dynamic import)
- `DashboardDimensionsWidget` -- Recharts bar/pie charts (dynamic import)
- `DashboardProfileSection` -- Profile completion with Framer Motion (dynamic import)
- `DashboardQuickLinks` -- Action shortcuts
- `InsightCards` -- Pipeline alerts + new opportunities
- `DashboardErrorStates` -- 6 exported state components (full error, retrying, skeleton, not auth, empty, stale banner)
- `DashboardViewToggle` -- Period selector (week/month/quarter)

Uses `useFetchWithBackoff` for resilient data fetching with exponential backoff.

### 3.4 Pipeline Module (app/pipeline/)

- `@dnd-kit` code-split via `next/dynamic` to reduce initial bundle
- Two variants: `PipelineKanban` (full drag-and-drop) and `ReadOnlyKanban` (trial expired)
- `PipelineMobileTabs` for mobile-friendly stage navigation
- 5-stage workflow: Novas > Em Analise > Preparando > Submetidas > Arquivadas
- `usePipeline` hook uses SWR with optimistic updates
- Shepherd.js tour (3 steps) for first-time users
- Pipeline limit (5 items) for `limited_access` trial phase

---

## 4. State Management

### 4.1 Strategy Summary

| Layer | Tool | Usage |
|-------|------|-------|
| **Global Auth** | React Context (`AuthProvider`) | Session, user, isAdmin, signOut, sessionExpired |
| **Global User** | React Context (`UserContext`) | Unified auth + plan + quota + trial (composes 4 hooks) |
| **Global Theme** | React Context (`ThemeProvider`) | Dark/light mode with localStorage |
| **Global Backend Health** | React Context (`BackendStatusProvider`) | Polls `/api/health` every 30s (visibility-gated) |
| **Server Data** | SWR (`useSWR`) | Pipeline, dashboard, plan info, quota, profile |
| **Feature Flags** | Custom hook (`useFeatureFlags`) | In-memory cache (5min TTL), manual fetch |
| **Search State** | 9 custom hooks | Complex composition via `useSearchOrchestration` |
| **SSE Progress** | Custom hook (`useSearchSSE`) | EventSource with reconnect backoff |
| **Form State** | react-hook-form + zod | Onboarding (2 steps), login, signup |
| **Persistent State** | localStorage (via `safeSetItem/safeGetItem`) | Theme, sidebar, onboarding, plan cache, saved searches, last search, feedback |
| **URL State** | `useSearchParams` | Search params (auto=true, search_id) |
| **Cross-Tab** | `useBroadcastChannel` | Auth state sync between tabs |

### 4.2 Custom Hooks (29 global + 9 search-specific = 38 total)

**Global hooks (hooks/):**

| Hook | Purpose | Data Source |
|------|---------|-------------|
| `useSearchSSE` | SSE with backoff [1s, 2s, 4s], max 3 retries, polling fallback, 120s inactivity timeout | EventSource |
| `useFetchWithBackoff` | Generic fetch: backoff [2s, 4s, 8s, 16s, 30s cap], max 5 retries, abort on unmount | Custom fetch |
| `usePipeline` | SWR-based CRUD for pipeline items (optimistic updates) | `/api/pipeline` |
| `usePlan` | Plan info with localStorage cache (1hr TTL) | `/api/subscription-status` |
| `useQuota` | Search quota remaining | `/api/me` |
| `useTrialPhase` | Trial lifecycle phase detection (active/limited/expired) | Derived from plan |
| `useAnalytics` | Mixpanel event tracking | Mixpanel SDK |
| `useFeatureFlags` | Feature flags with in-memory cache (5min TTL) | Local config |
| `useOnboarding` | Onboarding wizard state + Shepherd.js | Local state |
| `useShepherdTour` | Tour step management | Shepherd.js |
| `useKeyboardShortcuts` | Global keyboard shortcuts | Event listeners |
| `useNavigationGuard` | Warn on unsaved changes before navigation | beforeunload |
| `useIsMobile` | Media query responsive breakpoint | Window resize |
| `useBroadcastChannel` | Cross-tab communication | BroadcastChannel API |
| `useSavedSearches` | Saved search CRUD | localStorage |
| `useSearchPolling` | Polling fallback for SSE failures | `/api/search-status` |
| `useServiceWorker` | Service worker registration | ServiceWorker API |
| `useSessions` | Session history | `/api/sessions` |
| `useUserProfile` | User profile data | `/api/me` |
| `useProfileCompleteness` | Profile completion percentage | `/api/profile-completeness` |
| `useProfileContext` | User profile context data | `/api/profile-context` |
| `useAlertPreferences` | Alert configuration | `/api/alert-preferences` |
| `useAlerts` | Alert notifications | `/api/alerts` |
| `useConversations` | Message conversations | `/api/messages/conversations` |
| `useUnreadCount` | Unread message count | `/api/messages/unread-count` |
| `useOrganization` | Organization management | `/api/organizations` |
| `usePlans` | Plan listing | `/api/plans` |
| `usePublicMetrics` | Public landing page metrics | `/api/metrics/*` |

### 4.3 localStorage Usage

87 occurrences across 20 files, all through `safeSetItem`/`safeGetItem`/`safeRemoveItem` wrappers from `lib/storage.ts`. Key patterns:

| Key | Purpose | TTL |
|-----|---------|-----|
| `smartlic-theme` | Theme preference | Permanent |
| `smartlic-sidebar-collapsed` | Sidebar state | Permanent |
| `smartlic-onboarding-completed` | Onboarding flag | Permanent |
| `smartlic-profile-context` | Cached profile context | Permanent |
| Plan cache | Subscription status | 1hr |
| Last search result cache | Search results | Session |
| Saved searches | User-saved search configurations | Permanent |
| Feedback state | Per-item thumbs up/down | Permanent |
| Tour completion | Shepherd tour completion flags | Permanent |

No centralized key registry exists -- risk of key collisions.

---

## 5. API Integration

### 5.1 Proxy Architecture

All backend calls go through Next.js API routes (`app/api/`) which proxy to `BACKEND_URL`. This pattern hides the backend URL from clients, injects Supabase auth tokens server-side, enables structured error handling, and adds correlation IDs.

**58 API proxy routes organized by domain:**

| Category | Count | Key Endpoints |
|----------|-------|---------------|
| **Search** | 6 | `POST /api/buscar`, `GET /api/buscar-progress` (SSE), `/api/buscar-results/[searchId]`, `/api/search-status`, `/api/search-history`, `/api/search-zero-match/[searchId]` |
| **Auth** | 8 | `/api/auth/login`, `/api/auth/signup`, `/api/auth/google(+callback)`, `/api/auth/check-email`, `/api/auth/check-phone`, `/api/auth/resend-confirmation`, `/api/auth/status`, `/api/mfa` |
| **Billing** | 6 | `/api/plans`, `/api/billing-portal`, `/api/subscription-status`, `/api/subscriptions/cancel(+feedback)`, `/api/trial-status` |
| **Pipeline** | 1 | `/api/pipeline` (GET/POST/PATCH/DELETE) |
| **Analytics** | 1 | `/api/analytics` (multiplexed via `endpoint` param) |
| **User** | 5 | `/api/me(+export)`, `/api/profile-context`, `/api/profile-completeness`, `/api/onboarding`, `/api/change-password` |
| **Messages** | 5 | `/api/messages/conversations(+[id]+reply+status)`, `unread-count` |
| **Alerts** | 4 | `/api/alerts(+[id]+preview)`, `/api/alert-preferences` |
| **Export** | 3 | `/api/download`, `/api/export/google-sheets`, `/api/regenerate-excel/[searchId]` |
| **Admin** | 3 | `/api/admin/[...path]`, `/api/admin/metrics`, `/api/health/cache` |
| **Misc** | 12 | `/api/health`, `/api/setores`, `/api/sessions`, `/api/feedback`, `/api/first-analysis`, `/api/bid-analysis/[bidId]`, `/api/organizations(+[id])`, `/api/status`, `/api/reports/diagnostico` |
| **Observability** | 4 | `/api/csp-report`, `/api/metrics/daily-volume`, `/api/metrics/discard-rate`, `/api/metrics/sse-fallback` |

### 5.2 SSE Dual-Connection Pattern

The search flow uses a dual-connection architecture:

1. `POST /api/buscar` -- Initiates search, returns `search_id` (202 Accepted)
2. `GET /api/buscar-progress?search_id=X` -- SSE stream for real-time progress

**SSE resilience (useSearchSSE hook):**

| Parameter | Value | Source |
|-----------|-------|--------|
| Reconnect backoff | [1s, 2s, 4s] | STORY-365 |
| Max retries | 3 | STAB-006 |
| Polling fallback | Every 5s via GET `/v1/search/{id}/status` | STORY-365 |
| Last-Event-ID | Forwarded on reconnect | STORY-297 |
| High-water mark | Progress never decreases (monotonic) | CRIT-052 |
| Inactivity timeout | 120s | CRIT-072 |
| Terminal stages | complete, error, degraded, refresh_available, search_complete | -- |

**Frontend proxy:** Uses `undici.Agent({ bodyTimeout: 0 })` via dynamic import to prevent SSE timeout. AbortController linked to `request.signal` for client disconnect cleanup.

### 5.3 Error Handling Patterns

- `proxy-error-handler.ts` -- Centralized proxy error formatting
- `error-messages.ts` -- User-friendly message mapping + `getUserFriendlyError()` + `getMessageFromErrorCode()`
- Structured `SearchError` interface with `error_code`, `correlation_id`, `search_id` fields
- ErrorDetail component renders 7 conditional fields based on error metadata
- `isTransientError()` detects 502/503/504 + network errors for auto-retry

---

## 6. Design System

### 6.1 Color System (globals.css, 615 lines)

CSS custom properties with WCAG contrast ratios documented inline:

**Core palette:**
- `--brand-navy: #0a1e3f` (14.8:1 vs white -- AAA)
- `--brand-blue: #116dff` (4.8:1 vs white -- AA)
- Ink hierarchy: `--ink` (12.6:1), `--ink-secondary` (5.5:1), `--ink-muted` (5.1:1), `--ink-faint` (1.9:1, decorative)
- Surface hierarchy: `--surface-0` (base), `--surface-1`, `--surface-2`, `--surface-elevated`
- Semantic: success (#16a34a), error (#dc2626), warning (#ca8a04) -- all AA compliant
- Gem palette: sapphire, emerald, amethyst, ruby (translucent overlays with dedicated shadows)
- Chart palette: 10 colors for Recharts data visualization
- WhatsApp brand color

**Dark mode:** Full `:root` / `.dark` dual token system. Theme toggled via class on `<html>`, persisted in localStorage.

### 6.2 Typography

| Token | Font | Weights | Preload | Usage |
|-------|------|---------|---------|-------|
| `--font-body` | DM Sans | Variable | Yes | Body text, primary font |
| `--font-display` | Fahkwang | 400-700 | No (FE-020) | Headings, display text |
| `--font-data` | DM Mono | 400-500 | No (FE-020) | Data tables, code |

All fonts use `display: "swap"` to prevent FOIT.

Fluid typography scale via `clamp()`:
- Hero: 40-72px
- H1: 32-56px
- H2: 24-40px
- H3: 20-28px
- Body-lg: 18-20px

### 6.3 Tailwind Configuration (tailwind.config.ts)

- Custom border-radius: input (4px), button (6px), card (8px), modal (12px)
- 3 font families mapped to CSS vars
- 8 custom keyframe animations: fade-in-up, gradient, shimmer, float, slide-up, scale-in, slide-in-right, bounce-gentle
- `darkMode: "class"` with manual toggle
- `@tailwindcss/typography` plugin for blog content
- Semantic aliases: primary, secondary, accent mapped to brand tokens
- Max-width: `landing: 1200px`

### 6.4 Component Primitives (components/ui/)

6 primitives built with `class-variance-authority` (cva) and `@radix-ui/react-slot`:

| Component | Details |
|-----------|---------|
| `Button` | 6 variants (primary, secondary, destructive, ghost, link, outline), 4 sizes (sm, default, lg, icon). Icon-only buttons enforce `aria-label` via TypeScript discriminated union. Loading state with spinner. |
| `Input` | Standard text input |
| `Label` | Form label |
| `CurrencyInput` | Brazilian Real formatting |
| `Pagination` | Page navigation |

### 6.5 Responsive Design

- Mobile-first with Tailwind breakpoints (sm:640, md:768, lg:1024, xl:1280)
- `useIsMobile` hook for JavaScript-level breakpoint detection
- Mobile: BottomNav (5 tabs) + MobileDrawer (hamburger menu)
- Desktop: Collapsible Sidebar (state persisted in localStorage)
- Touch targets: `min-w-[44px] min-h-[44px]` on mobile interactive elements
- `react-simple-pull-to-refresh` for mobile pull-to-refresh on search page
- Content widths: `max-w-5xl` (search), `max-w-7xl` (protected pages), `max-w-landing` (landing)

### 6.6 Animation

**Framer Motion (framer-motion):** Used in 6 production components:
- `SearchStateManager` -- Search state transitions
- `HeroSection`, `SectorsGrid`, `AnalysisExamplesCarousel`, `ComparisonTable`, `ValuePropSection` -- Landing page
- `DashboardProfileSection` -- Profile completion
- `FeaturesContent` -- Features page
- `lib/icons/` -- Animated icon components

**CSS animations (Tailwind):** 8 keyframe animations for lighter use cases (skeleton loading, shimmer, gentle bouncing).

**NProgress:** Route transition progress bar at page top.

---

## 7. UX Patterns Analysis

### 7.1 Loading States

**Comprehensive coverage with 8 loading.tsx files:**
- Route-level suspense: `(protected)`, admin, buscar, conta, dashboard, historico, pipeline, planos
- 3 dedicated skeleton components: AdminPageSkeleton, ContaPageSkeleton, PlanosPageSkeleton
- `EnhancedLoadingProgress` (391 lines) -- Multi-phase search progress with UF grid
- `AuthLoadingScreen` -- Full-page spinner during auth verification
- `LoadingResultsSkeleton` -- Search results placeholder
- Pipeline kanban skeleton during @dnd-kit dynamic import load
- `DashboardLoadingSkeleton` + `DashboardRetryingState` for dashboard states
- 10-second loading timeout on dashboard (`LOADING_TIMEOUT_MS`)

### 7.2 Error States

**Multi-layer error handling:**

| Layer | Component | Coverage |
|-------|-----------|----------|
| Root | `global-error.tsx` | Layout crashes (standalone HTML, no Tailwind) |
| App | `error.tsx` | App-level errors (Sentry + analytics tracking) |
| Page | `PageErrorBoundary` | Per-page wrapping |
| Search | `SearchErrorBoundary` | Search-specific recovery |
| Reusable | `ErrorStateWithRetry` | Generic retry UI |
| Dashboard | `DashboardErrorStates` | 6 state variants |
| Results | `EmptyResults`, `ZeroResultsSuggestions`, `SearchEmptyState` | Zero/pre-search states |
| Banner | `SearchErrorBanner`, `ExpiredCacheBanner`, `PartialResultsPrompt`, `SourcesUnavailable` | Degraded operation states |

### 7.3 Form Patterns

- **react-hook-form + zod:** Used in onboarding (2 step forms) and login/signup
- **Schemas:** Centralized in `lib/schemas/forms.ts` (onboardingStep1Schema, onboardingStep2Schema, loginSchema, loginPasswordSchema)
- **Specialized inputs:** CurrencyInput (Brazilian Real), CustomSelect, CustomDateInput, RegionSelector, EsferaFilter, MunicipioFilter, OrgaoFilter
- **Toast notifications:** Sonner (bottom-center, rich colors, close button)
- **Confirmation modals:** CancelSubscriptionModal, Dialog component

### 7.4 Onboarding

**3-step wizard (`/onboarding`):**
1. CNAE + Objective selection (react-hook-form + zod)
2. UFs + Value range (react-hook-form + zod)
3. Confirmation + auto-search launch via `POST /v1/first-analysis`

**Guided tours (Shepherd.js):**
- Search page tour: SEARCH_TOUR_STEPS + RESULTS_TOUR_STEPS
- Pipeline page tour: 3 steps (kanban columns, card details, alerts/deadlines)
- `TourInviteBanner`: Appears on first results view, auto-dismiss after 10s or scroll
- `OnboardingTourButton` for manual tour restart (in UserMenu)
- `ContextualTutorialTooltip` for contextual help

### 7.5 Navigation and Information Architecture

**Primary nav (desktop sidebar + mobile bottom nav):**
Buscar > Dashboard > Pipeline > Historico

**Secondary nav (sidebar only):**
Minha Conta > Ajuda > Sair (logout)

**Feature-gated (hidden from nav):** Alertas, Mensagens (SHIP-002 AC9)

**Breadcrumbs:** Shown on all protected pages via `(protected)/layout.tsx`.

### 7.6 Accessibility

**Strengths:**
- Skip navigation link targeting `#main-content` (WCAG 2.4.1)
- `aria-label` enforced at TypeScript level for icon-only buttons
- `aria-hidden="true"` on decorative icons (Sidebar uses lucide-react with aria-hidden)
- `role="status"` on loading/tour banners
- WCAG contrast ratios documented inline in CSS (all text colors AA or better)
- Focus ring (`focus-visible:ring-2`) on interactive elements
- `lang="pt-BR"` on html element
- `aria-label` on footer landmark
- 83 `aria-*` attribute usages across shared components

**Gaps identified:**
- No `aria-live` regions for dynamic search results updates (SSE progress, new results count) -- WCAG 4.1.3
- `SearchForm` wrapper lacks `role="search"` and form-level `aria-label`
- Pipeline kanban: no keyboard-accessible drag, no screen reader announcements for item moves
- `(protected)/layout.tsx` has `<main id="main-content">` but `/buscar` has its own `<main id="main-content">` -- duplicate ID when both render
- Color-only indicators (viability badges) may need text alternatives
- No automated a11y testing (jest-axe or similar) in unit test suite (Playwright has 2 axe-core specs)

---

## 8. Performance Assessment

### 8.1 Code Splitting (Dynamic Imports)

9 dynamic import occurrences across 7 files:

| Component | Reason | SSR |
|-----------|--------|-----|
| `PipelineKanban` / `ReadOnlyKanban` | Heavy @dnd-kit | No |
| `SearchStateManager` | Framer Motion | No |
| `TotpVerificationScreen` | Supabase import isolation | No |
| `DashboardDimensionsWidget` | Recharts | No |
| `DashboardTimeSeriesChart` | Recharts | No |
| `DashboardProfileSection` | Framer Motion | No |
| Blog content (`blog/[slug]`) | Article content | -- |

### 8.2 Font Optimization

- DM Sans preloaded (primary, critical path)
- Fahkwang and DM Mono deferred (`preload: false`) -- correct prioritization
- All use `display: "swap"` to prevent FOIT

### 8.3 Static Asset Caching (next.config.js)

| Path | Cache-Control |
|------|--------------|
| `/_next/static/*` | `public, max-age=2592000, immutable` (30 days) |
| `/images/*` | `public, max-age=604800` (7 days) |
| `/fonts/*` | `public, max-age=31536000, immutable` (1 year) |

Standalone output mode for Railway deployment. Unique build ID generated per deploy to force cache invalidation.

### 8.4 Bundle Size Concerns

| Concern | Size Impact | Mitigation |
|---------|------------|------------|
| `framer-motion` | ~32-50KB gzipped | Used in 6 prod files; not code-split at import level for landing |
| `recharts` | ~80KB gzipped | Dynamic imported in dashboard (good) |
| `@dnd-kit` | ~20KB gzipped | Dynamic imported in pipeline (good) |
| `shepherd.js` | ~15KB | Loaded on protected pages regardless of tour usage |
| `lucide-react` | Tree-shakeable | Individual icons imported (good) |
| `api-types.generated.ts` | 163KB source | Compile-time only, zero runtime cost |
| `globals.css` | 615 lines | Moderate, includes full design system |

### 8.5 Missed Optimizations

- All pages use `"use client"` -- static/marketing pages should be Server Components
- Landing page (13 components) is fully client-rendered including static marketing content
- Framer Motion forces client rendering of entire component tree (should be isolated to `motion.div` islands)
- `useFeatureFlags` implements its own cache instead of using SWR (already available)

---

## 9. Technical Debt Inventory

### HIGH Severity

| ID | Issue | Files | Est. Hours |
|----|-------|-------|------------|
| **TD-H01** | **Zero Server Components.** Every page uses `"use client"`. Landing, blog, legal, pricing pages should be RSC for better TTFB/SEO. ~40% TTFB improvement expected for landing page. | All `page.tsx` files | 16h |
| **TD-H02** | **Dual header/auth pattern.** `/buscar` bypasses `(protected)/layout.tsx` and implements its own header+auth guard. Duplicated logic, inconsistent UI. | `app/buscar/page.tsx`, `app/(protected)/layout.tsx` | 4h |
| **TD-H03** | **No `aria-live` for dynamic content.** SSE search progress and results updates invisible to screen readers. WCAG 4.1.3 violation. | `useSearchSSE.ts`, search components | 6h |
| **TD-H04** | **Missing a11y for drag-and-drop.** Pipeline kanban has no keyboard drag, no screen reader announcements. | `PipelineKanban.tsx` | 8h |

### MEDIUM Severity

| ID | Issue | Files | Est. Hours |
|----|-------|-------|------------|
| **TD-M01** | **22 `any` type occurrences** across 15 files (excluding generated). SavedSearchesDropdown, OrgaoFilter, MunicipioFilter, AnalyticsProvider, LoginForm, ErrorDetail. | Multiple | 4h |
| **TD-M02** | **ValorFilter.tsx (478 lines).** Mixing currency formatting, dual-slider logic, and preset buttons in one file. | `buscar/components/ValorFilter.tsx` | 3h |
| **TD-M03** | **EnhancedLoadingProgress.tsx (391 lines).** Multi-phase loading + UF grid + fallback simulation in one component. | `buscar/components/EnhancedLoadingProgress.tsx` | 3h |
| **TD-M04** | **useFeatureFlags has custom cache instead of SWR.** Implements its own in-memory cache + manual TTL despite SWR being globally available. Comment in file acknowledges this. | `hooks/useFeatureFlags.ts` | 2h |
| **TD-M05** | **Raw CSS var usage in classNames.** ~40+ instances of `bg-[var(--surface-0)]` instead of `bg-surface-0`. DEBT-012 in tailwind.config.ts notes this. Breaks Tailwind intellisense. | Multiple components | 3h |
| **TD-M06** | **87 localStorage usages with no key registry.** Safe wrappers exist but no centralized key constants -- risk of collisions or stale orphan data. | 20 files | 2h |
| **TD-M07** | **Landing page fully client-rendered.** 13 static marketing components forced to client by Framer Motion in HeroSection. Could isolate motion to client islands. | `app/components/landing/` | 8h |
| **TD-M08** | **ProfileCompletionPrompt.tsx (21,930 bytes).** Very large single component needing decomposition. | `components/ProfileCompletionPrompt.tsx` | 3h |
| **TD-M09** | **Feature-gated pages still routable.** `/alertas` and `/mensagens` hidden from nav but accessible via direct URL. API returns 404, showing confusing error states. | `app/alertas/`, `app/mensagens/` | 2h |

### LOW Severity

| ID | Issue | Files | Est. Hours |
|----|-------|-------|------------|
| **TD-L01** | **No automated a11y unit tests.** Neither jest-axe nor similar in Jest suite. Only 2 Playwright axe-core E2E specs. | Test infrastructure | 4h |
| **TD-L02** | **Skeleton coverage gaps.** Admin sub-pages, alertas, mensagens show generic spinner instead of content-shaped skeletons. | Various loading.tsx | 4h |
| **TD-L03** | **useOnboarding.tsx has .tsx extension.** File is a hook with no JSX; should be `.ts`. | `hooks/useOnboarding.tsx` | 0.5h |
| **TD-L04** | **Missing error.tsx in onboarding, signup, login.** Errors fall through to root boundary, losing navigation context. | Missing files | 3h |
| **TD-L05** | **TourInviteBanner defined inside SearchResults.tsx** (line 53). Should be its own file. | `buscar/components/SearchResults.tsx` | 0.5h |
| **TD-L06** | **Blog TODO placeholders.** 60+ identical TODO comments for internal linking across 30 articles (MKT-003/MKT-005). | Blog article files | 4h |
| **TD-L07** | **Search hooks complexity (3,287 LOC in 9 hooks).** Deep composition tree makes debugging difficult. Needs at minimum a documented dependency graph. | `app/buscar/hooks/` | 4h (docs) |

---

## 10. Recommendations

### 10.1 Critical Path (Next Sprint)

1. **Adopt Server Components for static pages** (TD-H01, TD-M07). Convert landing, blog, legal, pricing to RSC. Extract Framer Motion into isolated client component islands. Expected: ~40% TTFB improvement for landing, better SEO.

2. **Add `aria-live` regions for search** (TD-H03). Add `aria-live="polite"` to results container and progress area. Add `role="search"` to SearchForm wrapper. Low effort, high a11y impact.

3. **Unify /buscar auth pattern** (TD-H02). Move `/buscar` into the `(protected)` route group. Extract the custom header into a shared component.

### 10.2 Near-Term (1-2 Sprints)

4. **Migrate useFeatureFlags to SWR** (TD-M04). Eliminate custom cache, leverage SWR deduplication.

5. **Enforce Tailwind tokens** (TD-M05). Run codemod to replace `bg-[var(--X)]` with `bg-X`. Consider `eslint-plugin-tailwindcss` to prevent regression.

6. **Add jest-axe for a11y testing** (TD-L01). Install `jest-axe`, add render+axe assertion to existing component tests.

7. **Decompose large components** (TD-M02, TD-M03, TD-M08). Extract sub-components from ValorFilter, EnhancedLoadingProgress, ProfileCompletionPrompt.

8. **Feature-gate URLs** (TD-M09). Wrap `/alertas` and `/mensagens` pages with a feature flag check that renders "Em breve" instead of broken API errors.

### 10.3 Design System Evolution

9. **Expand ui/ primitives.** Currently 6 primitives. Many components (Select, Checkbox, Modal, Tooltip, Badge, Dropdown) exist as ad-hoc implementations. Consolidate into `components/ui/`.

10. **Create localStorage key registry.** Centralize all keys as constants in `lib/storage.ts` with typed getters/setters.

### 10.4 Performance

11. **Lazy-load Shepherd.js.** Currently loaded on all protected pages. Use `next/dynamic` to load only when tour is triggered.

12. **Audit Framer Motion.** Consider `motion/react` (lighter build) or CSS-only alternatives for simple transitions. The full `framer-motion` package is 32-50KB gzipped.

13. **Document search hook dependency graph** (TD-L07). The 9-hook composition in `/buscar` is the application's most complex state management. A visual dependency graph would significantly reduce developer onboarding time.

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Total page routes | ~47 |
| Total components | ~240 |
| Total custom hooks | 38 (29 global + 9 search) |
| API proxy routes | 58 |
| Unit test files | ~306 |
| E2E test files | ~31 |
| globals.css lines | 615 |
| Design tokens (CSS vars) | ~80 |
| Custom animations | 8 Tailwind + Framer Motion |
| Technical debt items | 20 |
| High severity debt | 4 |
| Medium severity debt | 9 |
| Low severity debt | 7 |
| Estimated total fix effort | ~88h |
