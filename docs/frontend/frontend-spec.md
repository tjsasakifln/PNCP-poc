# Frontend Specification -- SmartLic/BidIQ

> **Generated:** 2026-02-15 | **Auditor:** @ux-design-expert (Pixel)
> **Codebase Path:** `D:\pncp-poc\frontend\`
> **Production URL:** `https://smartlic.tech/` (canonical), `https://bidiq-frontend-production.up.railway.app/` (origin)
> **Framework Version:** Next.js 16.1.6

---

## 1. Technology Stack

### Core Framework
| Technology | Version | Purpose |
|---|---|---|
| Next.js | ^16.1.6 | App Router, SSR, API routes |
| React | ^18.3.1 | UI rendering |
| TypeScript | ^5.9.3 | Type safety (strict mode) |
| Tailwind CSS | ^3.4.19 | Utility-first styling |

### Key Dependencies
| Library | Version | Purpose |
|---|---|---|
| @supabase/ssr | ^0.8.0 | Server-side auth (middleware) |
| @supabase/supabase-js | ^2.93.3 | Client-side auth |
| @sentry/nextjs | ^10.38.0 | Error tracking, source maps |
| framer-motion | ^12.33.0 | Landing page animations |
| recharts | ^3.7.0 | Dashboard charts |
| @dnd-kit/core | ^6.3.1 | Pipeline drag-and-drop |
| lucide-react | ^0.563.0 | Icon library |
| sonner | ^2.0.7 | Toast notifications |
| react-day-picker | ^9.13.0 | Date picker |
| shepherd.js | ^14.5.1 | Interactive onboarding tour |
| mixpanel-browser | ^2.74.0 | Product analytics |
| nprogress | ^0.2.0 | Page transition loading bar |
| react-simple-pull-to-refresh | ^1.3.4 | Mobile pull-to-refresh |
| use-debounce | ^10.1.0 | Input debouncing |
| date-fns | ^4.1.0 | Date manipulation |
| uuid | ^13.0.0 | UUID generation |

### Build & Testing
| Tool | Version | Purpose |
|---|---|---|
| Jest | ^29.7.0 | Unit tests |
| @testing-library/react | ^14.1.2 | Component testing |
| @swc/jest | ^0.2.29 | Fast TS transform |
| Playwright | ^1.58.1 | E2E tests |
| @axe-core/playwright | ^4.11.0 | Accessibility E2E |
| @lhci/cli | ^0.15.0 | Lighthouse CI |
| openapi-typescript | ^7.13.0 | API type generation |

### Build Configuration
- **Output:** `standalone` (for Railway container deployment)
- **Build ID:** Timestamp + random (forces cache invalidation per deploy)
- **Sentry integration:** Source map upload, tunnel route `/monitoring`, debug statements tree-shaken
- **Security headers:** CSP, HSTS, X-Frame-Options DENY, Permissions-Policy

---

## 2. Application Architecture

### App Router Structure

```
frontend/
  middleware.ts                       # Auth guard + canonical domain redirect
  app/
    layout.tsx                        # Root: fonts, providers, skip-nav, toaster
    page.tsx                          # Landing page (public)
    globals.css                       # Design tokens, animations, vendor overrides
    error.tsx                         # Global error boundary (Sentry)
    global-error.tsx                  # Root-level error boundary
    sitemap.ts                        # Dynamic sitemap
    types.ts                          # Shared frontend types
    api-types.generated.ts            # Auto-generated from backend OpenAPI
    login/page.tsx                    # Login (email, magic link, Google OAuth)
    signup/page.tsx                   # Registration (multi-field)
    auth/callback/page.tsx            # OAuth/magic link callback handler
    recuperar-senha/page.tsx          # Password recovery request
    redefinir-senha/page.tsx          # Password reset form
    planos/page.tsx                   # Pricing page with ROI calculator
    planos/obrigado/page.tsx          # Post-purchase thank you
    features/page.tsx                 # Features marketing page
    privacidade/page.tsx              # Privacy policy
    termos/page.tsx                   # Terms of service
    ajuda/page.tsx                    # FAQ / Help center
    buscar/page.tsx                   # Core search SPA (authenticated)
    buscar/components/                # Search sub-components (4 files)
    buscar/hooks/                     # Search hooks (3 files)
    pipeline/page.tsx                 # Kanban pipeline (drag-and-drop)
    pipeline/PipelineColumn.tsx       # Pipeline column component
    pipeline/PipelineCard.tsx         # Pipeline card component
    pipeline/types.ts                 # Pipeline type definitions
    onboarding/page.tsx               # First-time user onboarding wizard
    (protected)/layout.tsx            # Auth guard layout for protected pages
    dashboard/page.tsx                # Personal analytics dashboard
    historico/page.tsx                # Search history
    conta/page.tsx                    # Account settings (password, delete, export)
    admin/page.tsx                    # Admin user management
    mensagens/page.tsx                # InMail messaging center
    components/                       # ~40 shared components
    hooks/useInView.ts                # Intersection observer hook
    api/                              # 19 API proxy routes
  hooks/                              # 11 shared hooks
  lib/                                # Utilities, constants, config
  components/                         # Cross-page components (12 files)
```

### Provider Hierarchy (Root Layout)

```
<html lang="pt-BR" suppressHydrationWarning>
  <head>
    <script> // Inline theme flash prevention (localStorage 'bidiq-theme')
  </head>
  <body>
    <a href="#main-content"> // Skip navigation (WCAG 2.4.1)
    <AnalyticsProvider>      // Mixpanel tracking
      <AuthProvider>         // Supabase auth context (session, user, admin)
        <ThemeProvider>      // Dark mode management
          <NProgressProvider> // Page transition loading bar
            <SessionExpiredBanner /> // Proactive session expiry warning
            {children}
            <Toaster />      // sonner toast notifications
            <CookieConsentBanner />  // LGPD compliance
          </NProgressProvider>
        </ThemeProvider>
      </AuthProvider>
    </AnalyticsProvider>
  </body>
</html>
```

### Data Flow Diagram

```
[User Browser]
    |
    v
[Next.js Middleware] -- validates auth via Supabase getUser()
    |                   redirects unauthenticated to /login
    |                   redirects railway.app -> smartlic.tech (301)
    v
[Next.js App Router Pages]
    |
    +--> [Client Components] -- useAuth() for session
    |         |
    |         +--> useState/useEffect (local state)
    |         +--> localStorage (saved searches, theme, plan cache)
    |         +--> Mixpanel (analytics)
    |
    +--> [API Routes (/api/*)] -- Proxy layer
              |
              +--> [FastAPI Backend] -- BACKEND_URL env var
              |         |
              |         +--> PNCP API (search)
              |         +--> OpenAI API (summaries)
              |         +--> Supabase DB (profiles, history)
              |         +--> Stripe (checkout)
              |
              +--> [Supabase Direct] -- Auth, storage
```

---

## 3. Pages Inventory

### 3.1 Landing Page (`/`)
- **File:** `app/page.tsx` (46 lines)
- **Type:** Server Component (no `"use client"`)
- **Purpose:** Public marketing/institutional landing page
- **Components:** LandingNavbar, HeroSection, ValuePropSection, OpportunityCost, BeforeAfter, ComparisonTable, DifferentialsGrid, HowItWorks, StatsSection, DataSourcesSection, SectorsGrid, TestimonialsCarousel, FinalCTA, Footer
- **State:** None (purely compositional)
- **API Calls:** None
- **UX Patterns:** Scroll-based section reveals, gradient backgrounds, glassmorphism, premium animations (float, shimmer, scale-in)
- **Anchor sections:** `#sobre`, `#suporte`, `#como-funciona`

### 3.2 Search Page (`/buscar`)
- **File:** `app/buscar/page.tsx` (384 lines)
- **Type:** Client Component (`"use client"`)
- **Purpose:** Core search SPA -- the primary value-delivery page
- **Sub-components:**
  - `SearchForm` -- sector/terms toggle, UF grid, date range, filter panels
  - `SearchResults` -- loading progress, error states, empty state, results display, download
  - `FilterPanel` -- advanced filters accordion (modalidades, valor, esferas, municipios)
  - `CacheBanner`, `UfProgressGrid`, `SourcesUnavailable`, `DegradationBanner`, `PartialResultsPrompt`
- **Hooks:**
  - `useSearchFilters` -- all filter state (UFs, dates, sectors, terms, value range, etc.)
  - `useSearch` -- search execution, SSE progress, download, save, restore
  - `useUfProgress` -- per-UF progress tracking via SSE
- **State Management:** ~30+ useState calls spread across 3 custom hooks
- **API Calls:** POST `/api/buscar`, GET `/api/download`, GET `/api/buscar-progress/{search_id}` (SSE), GET `/api/setores`
- **UX Patterns:**
  - Pull-to-refresh (mobile only)
  - SSE real-time progress with per-UF status grid
  - Keyboard shortcuts (Ctrl+K search, Ctrl+A select all, / shortcuts help)
  - Save/load search workflows
  - Collapsible "Personalizar busca" accordion with localStorage persistence
  - Partial results prompt after 15s
  - Cache banner for stale data
  - Sticky search button on mobile
  - Upgrade modals for plan-gated features

### 3.3 Login Page (`/login`)
- **File:** `app/login/page.tsx` (477 lines)
- **Type:** Client Component
- **Purpose:** Authentication with multiple methods
- **Features:** Email+password, magic link, Google OAuth, error translation (Supabase errors to Portuguese), already-logged-in detection, redirect after login
- **Components:** InstitutionalSidebar (split-screen layout)
- **State:** email, password, mode, loading, error, success, magicSent
- **API Calls:** Supabase Auth SDK (signInWithPassword, signInWithOtp, signInWithOAuth)

### 3.4 Signup Page (`/signup`)
- **File:** `app/signup/page.tsx`
- **Purpose:** User registration with extended profile
- **Fields:** Email, password, full name, company, sector (dropdown), phone/WhatsApp (Brazilian mask), WhatsApp consent
- **Components:** InstitutionalSidebar
- **Validation:** Phone format (10-11 digits), password min 6 chars

### 3.5 Pricing Page (`/planos`)
- **File:** `app/planos/page.tsx` (809 lines)
- **Purpose:** Plan comparison, checkout initiation, ROI calculator
- **Features:**
  - Monthly/annual toggle (PlanToggle component)
  - Dynamic plan cards fetched from backend `/v1/plans`
  - Current plan detection with upgrade/downgrade indicators
  - Admin/master user detection (shows privileged message instead)
  - ROI calculator with real plan prices
  - Stripe redirect with loading overlay
- **State:** plans, billingPeriod, checkoutLoading, stripeRedirecting, roiResult, selectedPlanId
- **API Calls:** GET `/v1/plans`, POST `/v1/checkout`, GET `/v1/me`

### 3.6 Dashboard (`/dashboard`)
- **File:** `app/dashboard/page.tsx`
- **Purpose:** Personal analytics dashboard with charts
- **Protected:** Yes (via `(protected)/layout.tsx`)
- **Components:** recharts (BarChart, LineChart, PieChart)
- **API Calls:** GET `/api/analytics`

### 3.7 Pipeline (`/pipeline`)
- **File:** `app/pipeline/page.tsx`
- **Purpose:** Kanban-style procurement pipeline
- **Features:** Drag-and-drop columns (prospecting -> analyzing -> decided -> won/lost), CEIS/CNEP sanctions badges
- **Libraries:** @dnd-kit/core, @dnd-kit/sortable
- **API Calls:** GET/PUT/DELETE `/api/pipeline`

### 3.8 Search History (`/historico`)
- **File:** `app/historico/page.tsx`
- **Purpose:** List past searches with re-run capability
- **Protected:** Yes
- **API Calls:** GET `/api/search-history`

### 3.9 Account Settings (`/conta`)
- **File:** `app/conta/page.tsx`
- **Purpose:** Password change, data export (LGPD), account deletion
- **Features:** Change password with confirmation, GDPR/LGPD data export (JSON), account deletion with confirmation modal

### 3.10 Admin Panel (`/admin`)
- **File:** `app/admin/page.tsx`
- **Purpose:** User management for administrators
- **Features:** User list with search, plan assignment, user creation
- **Protected:** Admin-only (checked via isAdmin from AuthContext)

### 3.11 Messages (`/mensagens`)
- **File:** `app/mensagens/page.tsx`
- **Purpose:** InMail messaging system (support, suggestions, bugs)
- **Features:** Conversation list with filters, threaded replies, status labels (aberto/respondido/resolvido)

### 3.12 Onboarding (`/onboarding`)
- **File:** `app/onboarding/page.tsx`
- **Purpose:** First-time user onboarding wizard
- **Steps:** Company size, operating UFs, procurement experience, value range, keywords
- **API Calls:** PUT `/api/profile-context`

### 3.13 Help Center (`/ajuda`)
- **File:** `app/ajuda/page.tsx`
- **Purpose:** Searchable FAQ with accordion categories

### 3.14 Institutional Pages
- `/privacidade` -- Privacy policy (static)
- `/termos` -- Terms of service (static)
- `/features` -- Feature marketing page
- `/recuperar-senha` -- Password recovery
- `/redefinir-senha` -- Password reset
- `/auth/callback` -- OAuth callback handler
- `/planos/obrigado` -- Post-purchase thank you

---

## 4. Component Inventory

### 4.1 Layout & Navigation Components

| Component | File | Purpose | Props | Reusability |
|---|---|---|---|---|
| `LandingNavbar` | `app/components/landing/LandingNavbar.tsx` | Navigation for public pages | None | Medium -- landing-specific |
| `AppHeader` | `app/components/AppHeader.tsx` | Navigation for authenticated pages | None | High |
| `UserMenu` | `app/components/UserMenu.tsx` | User dropdown with plan/quota status | onRestartTour, statusSlot | High |
| `Footer` | `app/components/Footer.tsx` | Site-wide footer | None | High |
| `Breadcrumbs` | `app/components/Breadcrumbs.tsx` | Page breadcrumb navigation | None | High |
| `InstitutionalSidebar` | `app/components/InstitutionalSidebar.tsx` | Split-screen auth layout sidebar | variant, className | Medium |

### 4.2 Search Components

| Component | File | Purpose | Props | Reusability |
|---|---|---|---|---|
| `SearchForm` | `buscar/components/SearchForm.tsx` | Main search form composite | ~40 props via SearchFormProps | Low -- tightly coupled |
| `SearchResults` | `buscar/components/SearchResults.tsx` | Results display composite | ~35 props via SearchResultsProps | Low -- tightly coupled |
| `FilterPanel` | `buscar/components/FilterPanel.tsx` | Advanced filters accordion | filter state + setters | Medium |
| `RegionSelector` | `app/components/RegionSelector.tsx` | Region-based UF group selection | selected, onToggleRegion | High |
| `CustomSelect` | `app/components/CustomSelect.tsx` | Searchable dropdown | id, value, options, onChange | High |
| `CustomDateInput` | `app/components/CustomDateInput.tsx` | Date input with calendar popup | id, value, onChange, label | High |
| `EsferaFilter` | `app/components/EsferaFilter.tsx` | Government sphere filter | value, onChange | High |
| `MunicipioFilter` | `app/components/MunicipioFilter.tsx` | Municipality autocomplete | ufsSelecionadas, value, onChange | Medium |
| `OrgaoFilter` | `app/components/OrgaoFilter.tsx` | Agency filter | value, onChange | Medium |
| `OrdenacaoSelect` | `app/components/OrdenacaoSelect.tsx` | Sort order dropdown | value, onChange | High |
| `PaginacaoSelect` | `app/components/PaginacaoSelect.tsx` | Items per page selector | value, onChange | High |
| `StatusBadge` | `app/components/StatusBadge.tsx` | Status indicator badge | status | High |
| `SavedSearchesDropdown` | `app/components/SavedSearchesDropdown.tsx` | Saved searches loader | onLoadSearch, onAnalyticsEvent | Medium |

### 4.3 Results & Display Components

| Component | File | Purpose | Props | Reusability |
|---|---|---|---|---|
| `LicitacaoCard` | `app/components/LicitacaoCard.tsx` | Individual bid result card | licitacao, searchTerms, etc. | High |
| `LicitacoesPreview` | `app/components/LicitacoesPreview.tsx` | Results list with preview limit | licitacoes, previewCount | Medium |
| `EmptyState` | `app/components/EmptyState.tsx` | No results display | onAdjustSearch, rawCount, filterStats | High |
| `LoadingResultsSkeleton` | `app/components/LoadingResultsSkeleton.tsx` | Skeleton loading state | count | High |
| `LoadingProgress` | `app/components/LoadingProgress.tsx` | Progress indicator | step, total, etc. | High |
| `EnhancedLoadingProgress` | `components/EnhancedLoadingProgress.tsx` | SSE-aware progress bar | sseEvent, useRealProgress | Medium |
| `AddToPipelineButton` | `app/components/AddToPipelineButton.tsx` | Add bid to pipeline | licitacao | High |

### 4.4 STORY-257B Resilience Components

| Component | File | Purpose |
|---|---|---|
| `UfProgressGrid` | `buscar/components/UfProgressGrid.tsx` | Per-UF status grid during search |
| `DegradationBanner` | `buscar/components/DegradationBanner.tsx` | Partial results warning |
| `CacheBanner` | `buscar/components/CacheBanner.tsx` | Stale cache notification |
| `PartialResultsPrompt` | `buscar/components/PartialResultsPrompt.tsx` | View partial results early |
| `SourcesUnavailable` | `buscar/components/SourcesUnavailable.tsx` | All sources down fallback |

### 4.5 Plan & Billing Components

| Component | File | Purpose |
|---|---|---|
| `PlanBadge` | `app/components/PlanBadge.tsx` | Current plan indicator |
| `QuotaBadge` | `app/components/QuotaBadge.tsx` | Quota usage indicator |
| `QuotaCounter` | `app/components/QuotaCounter.tsx` | Detailed quota display |
| `UpgradeModal` | `app/components/UpgradeModal.tsx` | Plan upgrade prompt modal |
| `Countdown` | `app/components/Countdown.tsx` | Trial countdown timer |
| `PlanToggle` | `components/subscriptions/PlanToggle.tsx` | Monthly/annual toggle |
| `PlanCard` | `components/subscriptions/PlanCard.tsx` | Plan feature card |
| `DowngradeModal` | `components/subscriptions/DowngradeModal.tsx` | Downgrade confirmation |

### 4.6 UI Primitives

| Component | File | Purpose |
|---|---|---|
| `GlassCard` | `app/components/ui/GlassCard.tsx` | Glassmorphism card |
| `GradientButton` | `app/components/ui/GradientButton.tsx` | Gradient CTA button |
| `BentoGrid` | `app/components/ui/BentoGrid.tsx` | Bento-style layout grid |
| `Tooltip` | `app/components/ui/Tooltip.tsx` | Informational tooltip |

### 4.7 Infrastructure Components

| Component | File | Purpose |
|---|---|---|
| `ThemeProvider` | `app/components/ThemeProvider.tsx` | Dark mode context |
| `ThemeToggle` | `app/components/ThemeToggle.tsx` | Light/dark mode toggle |
| `AuthProvider` | `app/components/AuthProvider.tsx` | Supabase auth context |
| `AnalyticsProvider` | `app/components/AnalyticsProvider.tsx` | Mixpanel provider |
| `NProgressProvider` | `app/components/NProgressProvider.tsx` | Page transition bar |
| `SessionExpiredBanner` | `app/components/SessionExpiredBanner.tsx` | Token expiry warning |
| `CookieConsentBanner` | `app/components/CookieConsentBanner.tsx` | LGPD cookie consent |
| `ContextualTutorialTooltip` | `app/components/ContextualTutorialTooltip.tsx` | Contextual help tips |
| `PipelineAlerts` | `app/components/PipelineAlerts.tsx` | Pipeline notifications |
| `MessageBadge` | `app/components/MessageBadge.tsx` | Unread message counter |

---

## 5. Design System

### 5.1 Color Palette

**Light Mode (`:root`)**

| Token | Value | WCAG vs Canvas | Usage |
|---|---|---|---|
| `--canvas` | `#ffffff` | -- | Base background |
| `--ink` | `#1e2d3b` | 12.6:1 (AAA) | Primary text |
| `--ink-secondary` | `#3d5975` | 5.5:1 (AA) | Secondary text |
| `--ink-muted` | `#6b7a8a` | 5.1:1 (AA) | Muted text |
| `--ink-faint` | `#c0d2e5` | 1.9:1 (decorative) | Faint borders |
| `--brand-navy` | `#0a1e3f` | 14.8:1 (AAA) | Primary brand |
| `--brand-blue` | `#116dff` | 4.8:1 (AA) | Accent |
| `--brand-blue-hover` | `#0d5ad4` | 6.2:1 (AA+) | Hover accent |
| `--brand-blue-subtle` | `#e8f0ff` | -- | Subtle background |
| `--surface-0` | `#ffffff` | -- | Base surface |
| `--surface-1` | `#f7f8fa` | 12.3:1 (AAA) | Elevated surface |
| `--surface-2` | `#f0f2f5` | 11.8:1 (AAA) | Card background |
| `--success` | `#16a34a` | 4.7:1 (AA) | Success state |
| `--error` | `#dc2626` | 5.9:1 (AA) | Error state |
| `--warning` | `#ca8a04` | 5.2:1 (AA) | Warning state |

**Dark Mode (`.dark`)**

| Token | Value | WCAG vs Canvas | Usage |
|---|---|---|---|
| `--canvas` | `#121212` | -- | Dark background |
| `--ink` | `#e8eaed` | 11.8:1 (AAA) | Primary text |
| `--ink-secondary` | `#a8b4c0` | 7.2:1 (AAA) | Secondary text |
| `--surface-1` | `#1a1d22` | 11.2:1 (AAA) | Elevated surface |
| `--surface-2` | `#242830` | 10.5:1 (AAA) | Card background |
| `--error` | `#f87171` | 5.1:1 (AA) | Error (lighter for dark bg) |
| `--warning` | `#facc15` | 12.1:1 (AAA) | Warning |

### 5.2 Typography

| Font | CSS Variable | Usage | Weights |
|---|---|---|---|
| DM Sans | `--font-body` | Body text | auto (variable) |
| Fahkwang | `--font-display` | Headings, titles | 400, 500, 600, 700 |
| DM Mono | `--font-data` | Numbers, data, code | 400, 500 |

**Fluid Typography Scale:**
- Hero: `clamp(2.5rem, 5vw + 1rem, 4.5rem)` (40-72px)
- H1: `clamp(2rem, 4vw + 1rem, 3.5rem)` (32-56px)
- H2: `clamp(1.5rem, 3vw + 0.5rem, 2.5rem)` (24-40px)
- H3: `clamp(1.25rem, 2vw + 0.5rem, 1.75rem)` (20-28px)
- Body: `clamp(14px, 1vw + 10px, 16px)` (base)
- Line-height: 1.6 (body)

### 5.3 Spacing System

4px base grid enforced via Tailwind spacing scale (1=4px, 2=8px, 3=12px, etc.). Section spacing uses 8pt grid:
- Mobile sections: 4rem (64px)
- Desktop sections: 6rem (96px)
- Section gap: 8rem (128px)

### 5.4 Border Radius

| Token | Value | Usage |
|---|---|---|
| `rounded-input` | 4px | Form inputs |
| `rounded-button` | 6px | Buttons |
| `rounded-card` | 8px | Cards, containers |
| `rounded-modal` | 12px | Modals, dialogs |

### 5.5 Shadows

Layered shadow system with CSS custom properties:
- `shadow-sm` through `shadow-2xl` for depth hierarchy
- `shadow-glow` / `shadow-glow-lg` for brand glow effects
- `shadow-glass` for glassmorphism

### 5.6 Animations

| Animation | Duration | Easing | Usage |
|---|---|---|---|
| `fade-in-up` | 0.4s | ease-out | Component entrance |
| `slide-up` | 0.6s | cubic-bezier(0.4,0,0.2,1) | Section reveals |
| `scale-in` | 0.4s | cubic-bezier(0.4,0,0.2,1) | Modal entrance |
| `shimmer` | 2s linear infinite | linear | Skeleton loading |
| `float` | 3s ease-in-out infinite | -- | Landing decorations |
| `gradient` | 8s linear infinite | linear | Background gradients |

All animations respect `prefers-reduced-motion: reduce` with near-zero durations.

### 5.7 Component Patterns

- **Buttons:** Min-height 44px (WCAG touch target), brand-navy bg with brand-blue-hover, disabled states with `ink-faint` bg
- **Inputs:** Min-height 44px, border border-strong, focus ring brand-blue, rounded-input
- **Cards:** bg-surface-0, border, rounded-card, optional shadow elevation
- **Modals:** Fixed inset-0, z-50, bg-black/50 backdrop, animate-fade-in-up content
- **Badges:** Inline-flex, rounded-full, px-2 py-0.5, semantic colors
- **Loading spinners:** border-b-2 border-brand-blue, animate-spin

---

## 6. State Management Patterns

### 6.1 Auth State (Global Context)

`AuthProvider` provides session state via React Context:
- `user: User | null` -- validated Supabase user
- `session: Session | null` -- includes `access_token`
- `isAdmin: boolean` -- fetched from backend `/v1/me`
- `sessionExpired: boolean` -- proactive refresh failure detection
- 10-minute proactive token refresh interval
- Fallback chain: `getUser()` -> `getSession()` -> `refreshSession()` -> timeout (10s)

### 6.2 Search State (Custom Hooks)

**`useSearchFilters`** (525 lines) -- manages all filter state:
- UF selection (Set of 27 state codes)
- Date range (default: last 180 days in Sao Paulo timezone)
- Search mode (sector vs. custom terms)
- Sector ID and sector list (fetched with 5-min localStorage cache)
- Custom term tags with client-side validation (min 4 chars, stopword detection)
- Advanced filters: status, modalidades, valor range, esferas, municipios, ordenacao
- URL params parsing for deep-linking
- Profile context pre-selection (STORY-247)
- Collapsible panel states persisted to localStorage

**`useSearch`** (545 lines) -- manages search execution:
- Loading with step tracking and state count simulation
- SSE progress via `useSearchProgress` hook
- Client-side retry (2 retries with 3s/8s delays)
- Result storage and raw count
- Download flow (signed URL or filesystem fallback)
- Save/load search functionality
- Search state persistence for auth recovery
- Cancel via AbortController
- Comprehensive analytics tracking

**`useUfProgress`** -- per-UF status tracking via SSE:
- Maps UF codes to status (pending/fetching/retrying/success/recovered/error)
- Aggregates total found count
- Tracks all-complete state

### 6.3 Plan/Quota State

**`usePlan`** hook -- fetches and caches plan info (1hr localStorage TTL):
- `plan_id`, `plan_name`, `quota_used`, `quota_reset_date`
- `capabilities` object (max_history_days, max_requests_per_month, allow_excel)
- Trial expiration tracking

**`useQuota`** hook -- quota tracking with auto-refresh after search

### 6.4 Analytics State

**`useAnalytics`** hook -- Mixpanel integration:
- `trackEvent(name, data)` -- fire-and-forget event tracking
- `identifyUser(id, traits)` -- link user identity
- Cookie consent check before tracking

### 6.5 Pipeline State

**`usePipeline`** hook -- Kanban pipeline CRUD:
- Items list with optimistic updates
- Stage management (prospecting -> analyzing -> decided -> won/lost)
- Drag-and-drop coordination

### 6.6 localStorage Keys

| Key | Purpose | TTL |
|---|---|---|
| `bidiq-theme` | Dark mode preference | Permanent |
| `smartlic-customize-open` | Filter accordion state | Permanent |
| `smartlic-location-filters` | Location filter open state | Permanent |
| `smartlic-advanced-filters` | Advanced filter open state | Permanent |
| `smartlic-sectors-cache-v2` | Sector list cache | 5 minutes |
| `smartlic-profile-context` | User profile context | Permanent |
| `smartlic-onboarding-completed` | Onboarding flag | Permanent |
| `bidiq-saved-searches` | Saved search list | Permanent |
| `smartlic-plan-*` | Plan info cache | 1 hour |
| `bidiq-search-state` | Search state for auth recovery | Session |
| `cookie-consent-*` | LGPD consent | Permanent |
| `mixpanel-*` | Analytics persistence | Managed by Mixpanel |

---

## 7. API Integration Layer

### 7.1 Proxy Routes

All backend calls go through Next.js API routes (same-origin proxy pattern):

| Route | Method | Backend Endpoint | Purpose |
|---|---|---|---|
| `/api/buscar` | POST | `/v1/buscar` | Search with filters |
| `/api/download` | GET | Supabase Storage / filesystem | Excel download |
| `/api/buscar-progress` | GET | `/buscar-progress/{search_id}` | SSE progress stream |
| `/api/setores` | GET | `/setores` | Sector list |
| `/api/me` | GET | `/v1/me` | User profile |
| `/api/me/export` | GET | `/v1/me/export` | LGPD data export |
| `/api/health` | GET | -- | Health check (Railway) |
| `/api/analytics` | GET | `/v1/analytics` | Dashboard data |
| `/api/search-history` | GET | `/v1/search-history` | Past searches |
| `/api/pipeline` | GET/POST/PUT/DELETE | `/v1/pipeline` | Pipeline CRUD |
| `/api/change-password` | POST | -- | Password change |
| `/api/sessions` | GET/DELETE | `/v1/sessions` | Active sessions |
| `/api/profile-context` | GET/PUT | `/v1/profile-context` | Onboarding data |
| `/api/messages/*` | Various | `/v1/messages/*` | InMail messaging |
| `/api/admin/[...path]` | Various | `/v1/admin/*` | Admin proxy (catch-all) |

### 7.2 Auth Token Handling

1. **Server-side refresh (STORY-253):** `getRefreshedToken()` from `lib/serverAuth.ts` attempts server-side token refresh before falling back to header
2. **Client-side:** Bearer token from `session.access_token` sent in Authorization header
3. **Correlation IDs:** `X-Request-ID` (proxy) and `X-Correlation-ID` (client) for distributed tracing

### 7.3 Error Handling Patterns

**Proxy route (`/api/buscar`):**
- 2 retries with [0ms, 3000ms] delays
- Only retries HTTP 503 (rate limit)
- 5-minute timeout (AbortController)
- JSON parse fallback for non-JSON responses
- Explicit 401/503/504 error messages in Portuguese

**Client-side (`useSearch`):**
- 2 additional client-side retries with [3s, 8s] delays
- Only retries 500/502/503
- Error code detection: `DATE_RANGE_EXCEEDED`, `RATE_LIMIT`
- User-friendly error translation via `getUserFriendlyError()`
- AbortError silently ignored (user cancel)
- Force-fresh fallback: on error, keep previous cached result visible

### 7.4 Loading States

Multi-layer loading indication:
1. **NProgress bar** -- top-of-page progress bar for page transitions
2. **EnhancedLoadingProgress** -- calibrated multi-step progress (fetching -> filtering -> summarizing -> generating)
3. **UfProgressGrid** -- per-UF status tiles showing fetching/retrying/success/error per state
4. **LoadingResultsSkeleton** -- content placeholder while results load
5. **PartialResultsPrompt** -- after 15s, offer to view partial results
6. **Spinner on buttons** -- inline spinners on search/download buttons

---

## 8. Accessibility Assessment

### 8.1 Strengths

- **Skip navigation link** (WCAG 2.4.1) -- implemented in root layout with keyboard-only visibility
- **Language attribute** -- `lang="pt-BR"` on `<html>`
- **Focus visible** -- 3px solid ring (WCAG 2.2 AAA, 2.4.13 Focus Appearance) with 2px offset
- **Touch targets** -- Global `button { min-height: 44px }`, inputs min-height 44px (WCAG 2.5.8)
- **Color contrast** -- All text colors documented with WCAG ratios; AA minimum met for all functional text
- **`prefers-reduced-motion`** -- Respected globally with near-zero animation durations
- **ARIA attributes** -- `role="alert"` on error messages, `aria-busy` on search button, `aria-pressed` on toggle buttons, `aria-expanded` on accordions, `aria-label` on icon buttons
- **Semantic HTML** -- `<main>`, `<header>`, `<footer role="contentinfo">`, `<nav>`, `<section>` used throughout
- **Form labels** -- All inputs have `<label>` with `htmlFor` or `id` associations
- **`aria-hidden="true"`** on decorative SVGs
- **`role="img" aria-label="..."` on informational SVGs**
- **Live regions** -- `aria-live="polite"` on loading progress area
- **axe-core integration** -- Playwright E2E tests include `@axe-core/playwright`

### 8.2 Weaknesses & Issues

| ID | Issue | Severity | Impact |
|---|---|---|---|
| A-01 | Modal dialogs (save search, keyboard help) lack focus trap | High | Keyboard users can Tab behind modal |
| A-02 | Modals do not use `role="dialog"` or `aria-modal="true"` | High | Screen readers don't announce dialog context |
| A-03 | Custom dropdowns (CustomSelect) may not announce selection changes to screen readers | Medium | AT users miss selection feedback |
| A-04 | UF buttons grid uses `title` attribute for full state name but no `aria-label` -- relying on visual tooltip only | Low | Most AT reads title, but inconsistent |
| A-05 | Keyboard shortcuts (Ctrl+K, etc.) have no way to disable or customize -- conflict risk with browser/OS shortcuts | Low | Power user feature, acceptable |
| A-06 | Pull-to-refresh has no keyboard alternative | Medium | Desktop OK (disabled), but mobile-only swipe is not accessible |
| A-07 | Shepherd.js onboarding tour may block underlying content without proper inert attribute | Medium | During tour, background is interactive |
| A-08 | Some SVG icons use `role="img" aria-label="Icone"` with generic label -- should be descriptive or decorative | Low | Generic label provides no useful info |
| A-09 | Dark mode `--ink-muted` at 4.9:1 is borderline AA (needs 4.5:1 for text, passes barely) | Low | Very close to threshold; meets AA |
| A-10 | Error boundary button uses `--brand-green` color which is not defined in the design tokens | Medium | Button may render with no visible background in some themes |

---

## 9. Performance Analysis

### 9.1 Bundle Concerns

| Concern | Severity | Details |
|---|---|---|
| **recharts (3.7.0)** | High | Full charting library (~200KB gzipped) imported on dashboard page. Only used on one page but may affect initial bundle if not properly code-split. |
| **@dnd-kit suite** | Medium | Three packages imported for pipeline page drag-and-drop. Dynamic import recommended. |
| **framer-motion (12.33.0)** | Medium | Full animation library. Only used on landing page components. LazyMotion with `domAnimation` features would reduce bundle. |
| **shepherd.js** | Low | Onboarding library loaded on all search pages via `useOnboarding`. Should be lazy-loaded. |
| **@sentry/nextjs** | Low | Tree-shaking configured (`excludeDebugStatements: true`), but still adds ~30KB baseline. |
| **Inline SVGs** | Low | Many SVG icons are inline rather than from lucide-react. Inconsistent icon approach increases bundle slightly. |

### 9.2 Lazy Loading

- **Suspense boundary** on `/buscar` page (wraps `HomePageContent` in Suspense)
- **No dynamic imports** found for heavy components (recharts, dnd-kit, shepherd). All are static imports.
- **`output: 'standalone'`** enables per-page code splitting via Next.js automatic splitting

### 9.3 Image Optimization

- **next/image** not widely used. `remotePatterns` configured for `static.wixstatic.com` only.
- Landing page components use inline SVGs and CSS gradients rather than images.
- No `<Image>` component usage detected in page components.

### 9.4 SSR vs CSR

- **Landing page (`/`)** -- Server Component (static generation possible)
- **All other pages** -- Client Components (`"use client"`) due to auth state dependency
- **Middleware** -- Server-side auth validation on every request to protected routes
- **API routes** -- Server-side proxy (no browser-visible API keys)
- **Anti-pattern:** The `(protected)/layout.tsx` duplicates auth guard logic that middleware already handles. Both redirect to login on unauthenticated access.

### 9.5 Caching Strategy

| Cache | Location | TTL | Purpose |
|---|---|---|---|
| Sector list | localStorage | 5 min | Avoid re-fetching sector dropdown options |
| Plan info | localStorage | 1 hour | Prevent instant plan downgrade on transient errors |
| Profile context | localStorage | Permanent (until onboarding redo) | Pre-fill search defaults |
| Saved searches | localStorage | Permanent | User-curated search list (max 10) |
| Excel downloads | tmpdir filesystem | 60 min (setTimeout cleanup) | Legacy download fallback |
| Search results (backend) | Backend Redis cache | Configurable | Avoid re-querying PNCP |

---

## 10. Test Coverage

### 10.1 Unit Tests (Jest)

**Total test files:** ~90 (excluding quarantine)
**Quarantined tests:** ~17 files in `__tests__/quarantine/`

**Coverage thresholds (jest.config.js):**
- Branches: 50%
- Functions: 55%
- Lines: 55%
- Statements: 55%

**Active test categories:**

| Category | Files | Tests Areas |
|---|---|---|
| Components | 25+ | CustomDateInput, CustomSelect, QuotaBadge, RegionSelector, EmptyState, ThemeToggle, SavedSearchesDropdown, Footer, UserMenu, LandingNavbar, InstitutionalSidebar, SearchForm, OrgaoFilter, MunicipioFilter, OrdenacaoSelect, SessionExpiredBanner, LicitacaoCard, PlanToggle, PlanCard, DowngradeModal, AnnualBenefits, TrustSignals |
| Hooks | 4 | useKeyboardShortcuts, useFeatureFlags, useAnalytics, useSearchFilters |
| Pages | 6 | LoginPage, AdminPage, HistoricoPage, BuscarHeader, SignupPage, PlanosPage, AjudaPage |
| API routes | 5 | buscar, download, health, analytics, messages-conversations |
| Library | 6 | savedSearches, searchStatePersistence, error-messages, roi, animations, fetchWithAuth |
| Integration | 5 | termValidation, accessibility, LGPD, modalidadeFilter, sectorSync |
| Story-specific | 2 | STORY-257B UX, EnhancedLoadingProgress |
| Pipeline | 3 | AddToPipelineButton, PipelineCard, PipelineAlerts |

**Quarantined tests (not run in CI):** AuthProvider, AnalyticsProvider, LicitacaoCard, LicitacoesPreview, Countdown, PaginacaoSelect, GoogleSheetsExportButton, DashboardPage, MensagensPage, ContaPage, useSearch, useSearchFilters, useAnalytics, free-user flows

### 10.2 E2E Tests (Playwright)

**Test files:** 14 spec files in `e2e-tests/`

| Spec File | Coverage |
|---|---|
| `search-flow.spec.ts` | Search UX flow |
| `theme.spec.ts` | Dark mode toggle/persistence |
| `saved-searches.spec.ts` | Save/load search |
| `empty-state.spec.ts` | No results display |
| `error-handling.spec.ts` | Error states |
| `admin-users.spec.ts` | Admin panel |
| `auth-ux.spec.ts` | Login/logout flows |
| `performance.spec.ts` | Lighthouse metrics |
| `plan-display.spec.ts` | Pricing page |
| `signup-consent.spec.ts` | Registration with consent |
| `institutional-pages.spec.ts` | Privacy, terms, help |
| `landing-page.spec.ts` | Landing page sections |

**Browsers:** Chromium (Desktop), Mobile Safari (iPhone 13)

### 10.3 Coverage Gaps

| Gap | Severity | Impact |
|---|---|---|
| No tests for SearchResults.tsx (678 lines) | High | Core results display untested |
| No tests for pipeline page drag-and-drop | Medium | Complex interaction untested |
| No tests for onboarding wizard flow | Medium | Multi-step form untested |
| Dashboard page tests quarantined | Medium | Analytics dashboard untested in CI |
| AuthProvider tests quarantined | Medium | Auth flow regressions undetected |
| No tests for middleware.ts | Medium | Route protection logic untested |
| No tests for useUfProgress hook | Low | SSE progress tracking untested |
| Conta page tests quarantined | Low | Account management untested |

---

## 11. Technical Debt

| ID | Description | Severity | Impact | Recommendation |
|---|---|---|---|---|
| TD-01 | **SearchForm receives ~40 props** via prop drilling. SearchFormProps interface is 102 lines. | High | Maintenance burden; any filter change requires updating 4+ layers. | Extract filter state into a Context or use composition with children/slots. |
| TD-02 | **SearchResults receives ~35 props.** Same prop drilling issue. | High | Changes cascade across hook -> page -> component. | Colocate result state in Context or use compound component pattern. |
| TD-03 | **`useSearchFilters` is 528 lines** with 40+ state variables. Single hook doing too much. | High | Difficult to test, debug, or modify individual filter logic. | Split into smaller hooks: `useUfSelection`, `useDateRange`, `useTermSearch`, `useAdvancedFilters`. |
| TD-04 | **17 test files quarantined** in `__tests__/quarantine/`. | High | Reduced test confidence. Quarantine was meant to be temporary (STORY-218). | Fix quarantined tests one by one, starting with AuthProvider and useSearch. |
| TD-05 | **Inline SVGs duplicated** across 20+ files. Same search, close, warning icons repeated verbatim. | Medium | Bundle bloat, inconsistent sizing/styling. | Create an Icon component wrapping lucide-react icons, or create a shared SVG sprite. |
| TD-06 | **Sector list hardcoded** in both `useSearchFilters.ts` (SETORES_FALLBACK) and `signup/page.tsx` (SECTORS). Two separate lists that can drift. | Medium | Signup page sectors may not match search page sectors. | Single source of truth in `lib/constants/sectors.ts`, imported by both. |
| TD-07 | **No dynamic imports** for heavy dependencies (recharts, @dnd-kit, framer-motion, shepherd.js). | Medium | Larger initial JS bundle than necessary. | Use `next/dynamic` with `{ ssr: false }` for these libraries. |
| TD-08 | **Error boundary button uses `--brand-green`** which is not defined in the design tokens. | Medium | Button may be invisible in production. | Replace with `--brand-blue` or `--success` from the existing token set. |
| TD-09 | **Auth guard duplicated** between middleware.ts and `(protected)/layout.tsx`. | Low | Double redirect logic, potential race conditions. | Remove the client-side guard in layout.tsx; rely solely on middleware. |
| TD-10 | **Console.log statements** left in AuthProvider (Google OAuth debug logging, lines 254-258). | Low | Leaks implementation details to production console. | Remove or gate behind `process.env.NODE_ENV === 'development'`. |
| TD-11 | **`useEffect` missing dependencies** -- several `eslint-disable-next-line react-hooks/exhaustive-deps` comments. | Low | Potential stale closure bugs. | Review each disabled warning and add proper dependencies or extract functions. |
| TD-12 | **Search state uses `window.location.href` for auth redirect** instead of Next.js `router.push`. | Low | Loses client-side navigation state, forces full page reload. | Use `router.push("/login")` with `redirect` search param. |
| TD-13 | **PLAN_HIERARCHY and PLAN_FEATURES hardcoded** in `planos/page.tsx`. Same data exists in `lib/plans.ts`. | Low | Multiple sources of truth for plan configuration. | Consolidate into `lib/plans.ts` and import. |
| TD-14 | **`next.config.js` uses CommonJS** (`require`, `module.exports`) while the rest of the codebase is ESM/TypeScript. | Low | Inconsistency. | Migrate to `next.config.mjs` or `next.config.ts`. |
| TD-15 | **Pull-to-refresh CSS hack** disables pointer-events on desktop wrapper then re-enables on children. | Low | Fragile CSS approach that could break with layout changes. | Consider removing PullToRefresh entirely or using a resize observer approach. |
| TD-16 | **`suppressHydrationWarning`** on `<html>` element hides potential SSR/CSR mismatches. | Low | Legitimate use (dark mode flash prevention), but should be documented. | Already documented via inline comment -- acceptable. |

---

## 12. UX Issues

### 12.1 Usability Problems

| ID | Issue | Severity | Location | Recommendation |
|---|---|---|---|---|
| UX-01 | **Search button is below the fold** on desktop with "Personalizar busca" accordion open. Users must scroll to see results. | Medium | `/buscar` SearchForm | Move search button to sticky position or add a floating action button. |
| UX-02 | **No loading indicator when fetching sectors** for the CustomSelect dropdown, just a spinner with skeleton. User doesn't know what's loading. | Low | `/buscar` SearchForm | Add text: "Carregando setores disponiveis..." |
| UX-03 | **Save search dialog is a custom modal** without focus trap. Users can tab to elements behind the modal. | High | `/buscar` save dialog | Add focus trap or use a library like `@radix-ui/react-dialog`. |
| UX-04 | **Keyboard shortcuts modal** also lacks focus trap and Escape key dismiss (Escape triggers limparSelecao instead). | Medium | `/buscar` keyboard help | Conditionally handle Escape based on modal visibility. |
| UX-05 | **Date range in "abertas" mode is fixed at 180 days** with no way to customize. Users see "Buscando nos ultimos 180 dias" but cannot change it without switching to "publicacao" mode. | Low | `/buscar` SearchForm dates | Allow customization of lookback window, or clearly explain why 180 days is used. |
| UX-06 | **Empty state on first visit** -- user sees all 27 UFs selected and "Buscar Vestuario e Uniformes" button. No explanation of what the tool does. Onboarding tour helps but is dismissable. | Low | `/buscar` initial state | Add a brief intro text or hero section for first-time users. |
| UX-07 | **Download button for non-Excel plans** says "Assine para exportar resultados e acessar funcionalidades premium" -- very long for a button label. | Low | SearchResults download area | Shorten to "Fazer upgrade para exportar" with tooltip for details. |
| UX-08 | **Error retry cooldown of 30 seconds** -- user sees countdown timer on retry button. This feels punitive when the error was server-side. | Low | SearchResults error display | Reduce cooldown to 10s or remove for non-rate-limit errors. |
| UX-09 | **Pricing page annual calculation** shows `plan.price_brl * 9.6` with text "12 meses pelo preco de 9.6" -- the 9.6 multiplier is confusing for users. Should say "20% de desconto". | Medium | `/planos` pricing cards | Display monthly equivalent: "R$ X/mes (cobrado R$ Y/ano, 20% off)". |
| UX-10 | **Footer on search page is duplicated** -- the `/buscar` page has its own inline footer (4-column grid with About/Plans/Support/Legal) while the landing page uses the `<Footer />` component. | Low | `/buscar` footer | Extract to shared Footer component or reuse the existing one. |

### 12.2 Inconsistencies

| ID | Issue | Location |
|---|---|---|
| IC-01 | **Hardcoded brand name "SmartLic"** in header (line 123 of buscar/page.tsx) despite having `APP_NAME` env var elsewhere. | buscar/page.tsx |
| IC-02 | **Mixed color approaches** -- some components use Tailwind tokens (`text-brand-navy`), others use inline CSS vars (`text-[var(--brand-navy)]`). Both produce the same result but codebase is inconsistent. | Multiple files |
| IC-03 | **Icon sources mixed** -- some icons are from lucide-react, others are inline SVGs. No consistent icon system. | Multiple components |
| IC-04 | **Loading spinner styles vary** -- `border-b-2 border-brand-blue` vs `border-4 border-brand-blue border-t-transparent` used in different places. | Multiple components |
| IC-05 | **"Voltar para buscas" link** uses `<Link href="/buscar">` on some pages and `<a href="/buscar">` on others. | Multiple pages |
| IC-06 | **Error message translation** exists in login page but not in other pages. Backend errors on search/download are shown raw. | Login vs other pages |
| IC-07 | **Max-width container** varies: `max-w-4xl` on search page, `max-w-5xl` on pricing, `max-w-7xl` on protected layout, `max-w-landing` (1200px) on landing. | Multiple layouts |

### 12.3 Missing Feedback Patterns

| ID | Missing Pattern | Impact |
|---|---|---|
| MF-01 | **No confirmation when leaving a page with unsaved changes** (e.g., mid-search with results visible). | Users may accidentally lose results. |
| MF-02 | **No "Copied to clipboard" feedback** when copying bid URLs or IDs. | Users don't know if copy succeeded. |
| MF-03 | **Pipeline drag-and-drop has no haptic/audio feedback** on mobile. | Touch users may not feel the drag start. |
| MF-04 | **Sector change doesn't explicitly confirm** the previous results were cleared. | Users may not notice results disappeared after switching sectors. |

### 12.4 Mobile Responsiveness

- **Search page** uses `max-w-4xl` with `px-4 sm:px-6` -- well-adapted
- **UF grid** scales from 4 columns (mobile) to 9 columns (desktop) with responsive breakpoints
- **Search button** becomes sticky on mobile (`sticky bottom-4 sm:bottom-auto`)
- **Pull-to-refresh** only active on mobile (`max-width: 767px`)
- **Date picker** has 44px cell size matching touch targets
- **Footer** switches from 4-column grid to stacked on mobile
- **Landing page** sections use fluid typography and responsive padding

**Mobile Issues:**
- M-01: Pipeline page is not optimized for mobile -- drag-and-drop with columns is difficult on small screens
- M-02: Admin page table is not responsive -- horizontal scrolling needed on mobile
- M-03: Pricing page ROI calculator inputs may be too close together on small screens

---

## Summary Statistics

| Metric | Count |
|---|---|
| Total pages | 21 |
| Total components | ~60 |
| Total hooks | 14 (app/hooks + hooks/) |
| Total API routes | 19 |
| Total test files | ~90 (73 active + 17 quarantined) |
| Total E2E specs | 14 |
| Lines in buscar/page.tsx | 384 |
| Lines in useSearchFilters.ts | 528 |
| Lines in useSearch.ts | 545 |
| Lines in SearchResults.tsx | 678 |
| Lines in SearchForm.tsx | 583 |
| Lines in planos/page.tsx | 809 |
| Lines in AuthProvider.tsx | 311 |
| Lines in middleware.ts | 184 |
| Design tokens (CSS vars) | 40+ |
| localStorage keys | 12+ |
