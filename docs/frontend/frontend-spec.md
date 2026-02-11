# Frontend Specification - SmartLic/BidIQ

> **Generated:** 2026-02-11 | **Auditor:** @ux-design-expert (Uma)
> **Codebase Path:** `D:\pncp-poc\frontend\`
> **Production URL:** `https://bidiq-frontend-production.up.railway.app/`

---

## 1. Executive Summary

SmartLic.tech is a Brazilian SaaS product for automated procurement opportunity discovery from PNCP (Portal Nacional de Contratacoes Publicas). The frontend is a Next.js 16 App Router application with Supabase authentication (PKCE flow with Google OAuth), Tailwind CSS design system, framer-motion animations, Mixpanel analytics, and a tiered subscription model (Stripe billing). The codebase is in Portuguese (pt-BR), targeting Brazilian procurement professionals.

**Key Metrics:**
- **Pages:** 16 distinct routes (8 public, 8 protected)
- **Components:** ~55 React components across `app/components/` and `components/`
- **Hooks:** 10 custom hooks in `hooks/`
- **API Routes:** 10 Next.js API proxy routes
- **Test Files:** 55 test files in `__tests__/`
- **Dependencies:** 14 production, 15 dev dependencies

**Overall Assessment:**
The frontend is feature-rich and reflects rapid iteration. The design system (CSS custom properties + Tailwind) is well-structured with proper WCAG contrast documentation. The main search page (`buscar/page.tsx`) is a monolithic ~1100-line component that concentrates most business logic and represents the single largest source of technical debt. Component duplication exists between `app/components/` and root `components/` directories. Accessibility foundations are solid (skip nav, ARIA labels, focus states, `prefers-reduced-motion`), but several areas lack keyboard operability.

---

## 2. Tech Stack

### 2.1 Framework (Next.js version, app router)

| Aspect | Detail |
|---|---|
| **Framework** | Next.js 16.1.6 (App Router) |
| **React** | 18.3.1 |
| **TypeScript** | 5.9.3, strict mode enabled |
| **Build Output** | Standalone (`output: 'standalone'` in `next.config.js`) |
| **Deployment** | Railway (containerized Node.js standalone server) |
| **Language** | `lang="pt-BR"` on `<html>` |

**next.config.js** (`D:\pncp-poc\frontend\next.config.js`):
- `reactStrictMode: true`
- `output: 'standalone'` (optimized for Docker/Railway)
- Remote image pattern: `static.wixstatic.com` only
- No `i18n` configuration (single-locale app)
- No custom `headers` or `rewrites`

**tsconfig.json** (`D:\pncp-poc\frontend\tsconfig.json`):
- Target: ES2020
- Module: ESNext with bundler resolution
- Strict mode: `true`
- Path alias: `@/*` maps to `./*`
- Test files excluded from compilation

### 2.2 Styling (Tailwind config, design tokens)

**Tailwind CSS 3.4.19** with a comprehensive CSS custom properties design system.

**Design Tokens** (`D:\pncp-poc\frontend\app\globals.css`):

| Category | Tokens |
|---|---|
| **Canvas/Ink** | `--canvas`, `--ink`, `--ink-secondary`, `--ink-muted`, `--ink-faint` |
| **Brand** | `--brand-navy` (#0a1e3f), `--brand-blue` (#116dff), `--brand-blue-hover`, `--brand-blue-subtle` |
| **Surfaces** | `--surface-0`, `--surface-1`, `--surface-2`, `--surface-elevated` |
| **Semantic** | `--success`, `--error`, `--warning` (each with `-subtle` variant) |
| **Borders** | `--border`, `--border-strong`, `--border-accent` |
| **Focus** | `--ring` (#116dff light, #3b8bff dark) |
| **Typography** | `--text-hero` (clamp 40-72px), `--text-h1` through `--text-body-lg` (fluid) |
| **Premium** | Gradients (`--gradient-brand`, `--gradient-hero-bg`), glassmorphism (`--glass-bg`, `--glass-border`, `--glass-shadow`), premium shadows (sm through 2xl + glow) |

**Tailwind Extensions** (`D:\pncp-poc\frontend\tailwind.config.ts`):
- Dark mode: `class` strategy
- Custom font families: `body` (DM Sans), `display` (Fahkwang), `data` (DM Mono)
- Custom border radii: `input` (4px), `button` (6px), `card` (8px), `modal` (12px)
- Custom keyframe animations: `fade-in-up`, `gradient`, `shimmer`, `float`, `slide-up`, `scale-in`
- `maxWidth.landing`: 1200px

**Dark Mode:** Full implementation via CSS custom properties. Theme toggle in header. Flash prevention via inline `<script>` in `layout.tsx` that reads `localStorage('bidiq-theme')` before paint.

**Fonts:**
- DM Sans (body text) - Google Font with `display: swap`
- Fahkwang (display/headings) - Google Font with `display: swap`
- DM Mono (data/numbers) - Google Font with `display: swap`

### 2.3 Dependencies (key packages)

| Package | Version | Purpose |
|---|---|---|
| `@supabase/ssr` | ^0.8.0 | Supabase SSR client (cookie-based auth) |
| `@supabase/supabase-js` | ^2.93.3 | Supabase browser client |
| `framer-motion` | ^12.33.0 | Landing page animations |
| `lucide-react` | ^0.563.0 | Icon library (landing page) |
| `mixpanel-browser` | ^2.74.0 | Product analytics |
| `react-day-picker` | ^9.13.0 | Date picker (mobile-optimized) |
| `react-simple-pull-to-refresh` | ^1.3.4 | Mobile pull-to-refresh |
| `recharts` | ^3.7.0 | Dashboard charts |
| `shepherd.js` | ^14.5.1 | Interactive onboarding tour |
| `sonner` | ^2.0.7 | Toast notifications |
| `use-debounce` | ^10.1.0 | Input debouncing |
| `date-fns` | ^4.1.0 | Date manipulation |
| `uuid` | ^13.0.0 | UUID generation |

**Dev Dependencies of Note:**
- `@axe-core/playwright` (accessibility testing)
- `@lhci/cli` (Lighthouse CI)
- `@playwright/test` ^1.58.1 (E2E testing)
- `jest` + `@testing-library/react` (unit testing)

---

## 3. Page Inventory

### 3.1 Public Pages

| Route | File | Description |
|---|---|---|
| `/` | `app/page.tsx` | Landing page (12 sections: Hero, ValueProp, OpportunityCost, BeforeAfter, ComparisonTable, DifferentialsGrid, HowItWorks, StatsSection, DataSources, SectorsGrid, Testimonials, FinalCTA) |
| `/login` | `app/login/page.tsx` | Login with Google OAuth, email+password, magic link. Suspense boundary for `useSearchParams`. |
| `/signup` | `app/signup/page.tsx` | Registration with name, company, sector, phone, consent scroll box. Google OAuth. |
| `/pricing` | `app/pricing/page.tsx` | ROI calculator, plan comparison table, guarantee section |
| `/features` | `app/features/page.tsx` | Detailed feature descriptions with defensive positioning. Server component with metadata. |
| `/termos` | `app/termos/page.tsx` | Terms of service. Server component with metadata. |
| `/privacidade` | `app/privacidade/page.tsx` | Privacy policy. Server component with metadata. |
| `/auth/callback` | `app/auth/callback/page.tsx` | OAuth PKCE callback handler (code exchange) |

### 3.2 Protected Pages

| Route | File | Description | Auth Check |
|---|---|---|---|
| `/buscar` | `app/buscar/page.tsx` | **Main search page** - UF selector, date range, sector/custom terms, filters, results preview, download. ~1100 lines. | `useAuth()` session check |
| `/dashboard` | `app/dashboard/page.tsx` | Analytics dashboard with Recharts (bar, line, pie charts), summary stats, time series. | `useAuth()` session check |
| `/historico` | `app/historico/page.tsx` | Search history with re-run capability. Paginated list from backend `/sessions`. | `useAuth()` session check |
| `/conta` | `app/conta/page.tsx` | Account management (password change, user info display, logout). | `useAuth()` session check |
| `/planos` | `app/planos/page.tsx` | Plan management with Stripe checkout, monthly/annual toggle, upgrade/downgrade. Dynamic plan fetching from backend. | `useAuth()` session check |
| `/planos/obrigado` | `app/planos/obrigado/page.tsx` | Post-checkout thank-you page | `useAuth()` session check |
| `/mensagens` | `app/mensagens/page.tsx` | InMail messaging system (conversations list + thread view, admin mode). | `useAuth()` session check |
| `/admin` | `app/admin/page.tsx` | Admin panel: user list, plan management, credit editing, user creation. | `useAuth()` + `isAdmin` check |

### 3.3 API Routes

| Route | File | Method | Purpose |
|---|---|---|---|
| `/api/buscar` | `app/api/buscar/route.ts` | POST | Proxy to backend `/buscar`. Auth required. 5-min timeout. Retry on 503. Saves Excel to `tmpdir()`. |
| `/api/download` | `app/api/download/route.ts` | GET | Serves Excel files from temp dir. Auth required. 60-min auto-cleanup. |
| `/api/buscar-progress` | `app/api/buscar-progress/route.ts` | GET | SSE proxy for real-time search progress. `runtime: "nodejs"`, `dynamic: "force-dynamic"`. |
| `/api/setores` | `app/api/setores/route.ts` | GET | Proxy to backend `/setores`. No auth. |
| `/api/me` | `app/api/me/route.ts` | GET | Proxy to backend `/me`. Auth required. |
| `/api/analytics` | `app/api/analytics/route.ts` | GET | Proxy to backend `/analytics/{endpoint}`. Auth required. Supports `summary`, `searches-over-time`, `top-dimensions`. |
| `/api/health` | `app/api/health/route.ts` | GET | Health check (returns `{status: "ok"}`). |
| `/api/messages/conversations` | `app/api/messages/conversations/route.ts` | GET, POST | Conversations list and creation. Auth required. |
| `/api/messages/conversations/[id]` | `app/api/messages/conversations/[id]/route.ts` | GET | Single conversation detail. Auth required. |
| `/api/messages/conversations/[id]/reply` | `app/api/messages/conversations/[id]/reply/route.ts` | POST | Reply to conversation. Auth required. |
| `/api/messages/conversations/[id]/status` | `app/api/messages/conversations/[id]/status/route.ts` | PATCH | Update conversation status. Auth required. |
| `/api/messages/unread-count` | `app/api/messages/unread-count/route.ts` | GET | Unread message count. Auth required. |

**Critical Note:** The `/api/analytics` route uses `http://localhost:8000` as a fallback for `BACKEND_URL`, which is inconsistent with other routes that return 503 when unconfigured. This is a potential security issue (see Section 11).

---

## 4. Component Architecture

### 4.1 Layout Components

| Component | File | Description |
|---|---|---|
| `RootLayout` | `app/layout.tsx` | Root HTML with Google Fonts, skip-nav link, providers (Analytics > Auth > Theme), Toaster |
| `ThemeProvider` | `app/components/ThemeProvider.tsx` | CSS custom property theme switching (light/system/dark) with localStorage persistence |
| `AuthProvider` | `app/components/AuthProvider.tsx` | Supabase auth context (PKCE flow). Provides: `user`, `session`, `loading`, `isAdmin`, sign-in/up/out methods |
| `AnalyticsProvider` | `app/components/AnalyticsProvider.tsx` | Mixpanel initialization, page_load/page_exit tracking |
| `Footer` | `app/components/Footer.tsx` | 4-column grid, transparency disclaimer, LGPD badge, animated links |
| `LandingNavbar` | `app/components/landing/LandingNavbar.tsx` | Landing page navigation bar |
| `InstitutionalSidebar` | `app/components/InstitutionalSidebar.tsx` | Split-screen sidebar for login/signup pages |

### 4.2 Feature Components

**Search Page Components:**

| Component | File | Description |
|---|---|---|
| `RegionSelector` | `app/components/RegionSelector.tsx` | Brazilian region-based state multi-selector |
| `CustomSelect` | `app/components/CustomSelect.tsx` | Custom dropdown select with design system styling |
| `CustomDateInput` | `app/components/CustomDateInput.tsx` | Styled date input with design system tokens |
| `SavedSearchesDropdown` | `app/components/SavedSearchesDropdown.tsx` | Saved search management dropdown |
| `EnhancedLoadingProgress` | `components/EnhancedLoadingProgress.tsx` | 5-stage loading indicator with SSE real-time progress, cancel button |
| `LoadingResultsSkeleton` | `app/components/LoadingResultsSkeleton.tsx` | Animated skeleton placeholder for results |
| `EmptyState` | `app/components/EmptyState.tsx` | Zero-results state with filter breakdown and suggestions |
| `LicitacaoCard` | `app/components/LicitacaoCard.tsx` | Individual bid card with status badge, countdown, value, share, favorite |
| `LicitacoesPreview` | `app/components/LicitacoesPreview.tsx` | Paginated list of LicitacaoCards |
| `StatusBadge` | `app/components/StatusBadge.tsx` | Visual status indicator (green/yellow/red) |
| `Countdown` | `app/components/Countdown.tsx` | Countdown timer to bid deadline |
| `GoogleSheetsExportButton` | `components/GoogleSheetsExportButton.tsx` | Export results to Google Sheets |

**Filter Components (two locations -- duplication exists):**

In `app/components/` (P1 filters):
- `EsferaFilter`, `MunicipioFilter`, `OrgaoFilter`, `OrdenacaoSelect`, `PaginacaoSelect`

In `components/` (P0 filters):
- `StatusFilter`, `ModalidadeFilter`, `ValorFilter`
- `EsferaFilter` (DUPLICATE), `MunicipioFilter` (DUPLICATE)

**Billing & Subscription Components:**

| Component | File |
|---|---|
| `PlanBadge` | `app/components/PlanBadge.tsx` |
| `QuotaBadge` | `app/components/QuotaBadge.tsx` |
| `QuotaCounter` | `app/components/QuotaCounter.tsx` |
| `UpgradeModal` | `app/components/UpgradeModal.tsx` |
| `MessageBadge` | `app/components/MessageBadge.tsx` |
| `PlanToggle` | `components/subscriptions/PlanToggle.tsx` |
| `PlanCard` | `components/subscriptions/PlanCard.tsx` |
| `FeatureBadge` | `components/subscriptions/FeatureBadge.tsx` |
| `TrustSignals` | `components/subscriptions/TrustSignals.tsx` |
| `DowngradeModal` | `components/subscriptions/DowngradeModal.tsx` |
| `AnnualBenefits` | `components/subscriptions/AnnualBenefits.tsx` |

### 4.3 UI Components (reusable)

| Component | File |
|---|---|
| `GlassCard` | `app/components/ui/GlassCard.tsx` |
| `BentoGrid` | `app/components/ui/BentoGrid.tsx` |
| `GradientButton` | `app/components/ui/GradientButton.tsx` |
| `Tooltip` | `app/components/ui/Tooltip.tsx` |

### 4.4 Component Dependency Graph

**Search Page (`buscar/page.tsx`) -- the central component:**

```
buscar/page.tsx (HomePageContent - ~1100 lines)
  +-- AuthProvider (useAuth)
  +-- useAnalytics
  +-- useSavedSearches
  +-- useOnboarding (shepherd.js)
  +-- useKeyboardShortcuts
  +-- useQuota
  +-- usePlan
  +-- useSearchProgress (SSE)
  +-- RegionSelector
  +-- CustomSelect (sector dropdown)
  +-- CustomDateInput (x2)
  +-- SavedSearchesDropdown
  +-- StatusFilter
  +-- ModalidadeFilter
  +-- ValorFilter
  +-- EsferaFilter
  +-- MunicipioFilter
  +-- OrdenacaoSelect
  +-- PlanBadge
  +-- QuotaBadge
  +-- QuotaCounter
  +-- MessageBadge
  +-- ThemeToggle
  +-- UserMenu
  +-- UpgradeModal
  +-- EnhancedLoadingProgress
  +-- LoadingResultsSkeleton
  +-- EmptyState
  +-- LicitacoesPreview
  +--   LicitacaoCard (per item)
  +-- GoogleSheetsExportButton
  +-- Tooltip
```

**Landing Page (`page.tsx`):**

```
page.tsx
  +-- LandingNavbar
  +-- HeroSection (framer-motion, lucide-react, GlassCard, GradientButton)
  +-- ValuePropSection
  +-- OpportunityCost
  +-- BeforeAfter
  +-- ComparisonTable
  +-- DifferentialsGrid
  +-- HowItWorks
  +-- StatsSection
  +-- DataSourcesSection
  +-- SectorsGrid
  +-- TestimonialsCarousel
  +-- FinalCTA
  +-- Footer
```

---

## 5. State Management

**Approach:** React hooks (useState/useEffect/useContext) exclusively. No external state library (Redux, Zustand, Jotai).

### 5.1 Context Providers

| Context | File | State Managed |
|---|---|---|
| `AuthContext` | `app/components/AuthProvider.tsx` | `user`, `session`, `loading`, `isAdmin` |
| `ThemeContext` | `app/components/ThemeProvider.tsx` | `theme` (ThemeId), `config` |

### 5.2 Custom Hooks

| Hook | File | Purpose |
|---|---|---|
| `useAnalytics` | `hooks/useAnalytics.ts` | Mixpanel event tracking wrapper |
| `useOnboarding` | `hooks/useOnboarding.tsx` | Shepherd.js onboarding tour management |
| `useSavedSearches` | `hooks/useSavedSearches.ts` | localStorage-based saved searches CRUD |
| `useServiceWorker` | `hooks/useServiceWorker.ts` | Service worker registration |
| `useKeyboardShortcuts` | `hooks/useKeyboardShortcuts.ts` | Global keyboard shortcut system (Ctrl+K, Ctrl+A, Escape, /) |
| `useFeatureFlags` | `hooks/useFeatureFlags.ts` | Feature flag management |
| `useSearchProgress` | `hooks/useSearchProgress.ts` | SSE connection for real-time search progress |
| `useUnreadCount` | `hooks/useUnreadCount.ts` | Unread message polling |
| `usePlan` | `hooks/usePlan.ts` | Current user plan info fetching |
| `useQuota` | `hooks/useQuota.ts` | Search quota tracking and refresh |

### 5.3 Persistence

| What | Where | TTL |
|---|---|---|
| Theme preference | `localStorage('bidiq-theme')` | Permanent |
| Saved searches | `localStorage` via `useSavedSearches` | Permanent |
| Onboarding step | `localStorage('smartlic-onboarding-step')` | Permanent |
| Filter panel state | `localStorage('smartlic-location-filters')`, `localStorage('smartlic-advanced-filters')` | Permanent |
| Search state (auth redirect) | `sessionStorage` via `searchStatePersistence.ts` | Session |
| Plan cache | `localStorage` (1hr TTL) | 1 hour |
| Excel downloads | Server-side `tmpdir()` filesystem | 60 minutes |

---

## 6. API Integration Patterns

### 6.1 Backend Proxy Routes

All primary backend communication goes through Next.js API routes (`/api/*`), which proxy to the Python FastAPI backend. This pattern:
- Hides `BACKEND_URL` from the browser (server-side only env var)
- Allows auth header forwarding
- Enables retry logic at the proxy layer
- Adds Excel file caching to temp filesystem

**Proxy Pattern:**
```
Browser -> /api/buscar (Next.js route) -> BACKEND_URL/buscar (FastAPI)
```

### 6.2 Direct External Calls

| Destination | From | Purpose |
|---|---|---|
| Supabase Auth | `lib/supabase.ts` (browser client) | Authentication (PKCE), session management |
| `NEXT_PUBLIC_BACKEND_URL/me` | `AuthProvider.tsx` | Admin status check (direct to backend) |
| `NEXT_PUBLIC_BACKEND_URL/change-password` | `conta/page.tsx` | Password change (direct) |
| `NEXT_PUBLIC_BACKEND_URL/sessions` | `historico/page.tsx` | Search history (direct) |
| `NEXT_PUBLIC_BACKEND_URL/admin/*` | `admin/page.tsx` | Admin operations (direct) |

**Inconsistency:** Protected pages like `historico`, `conta`, and `admin` call `NEXT_PUBLIC_BACKEND_URL` directly from the browser, while `buscar` and `setores` use the proxy pattern. This creates two different auth forwarding patterns and exposes the backend URL to the client.

### 6.3 Error Handling

**`lib/error-messages.ts`** (`D:\pncp-poc\frontend\lib\error-messages.ts`):
- Comprehensive `getUserFriendlyError()` function
- Maps technical errors to Portuguese user-friendly messages
- Handles: network errors, SSL errors, HTTP status codes, JSON parse errors, PNCP-specific errors
- Strips URLs and stack traces from messages
- Supports `keep_original` sentinel for plan-limit messages

**Search page error handling:**
- Client-side retry (1 retry, 4s delay) for transient 503 errors
- Quota exceeded (403) handling with dedicated `quotaError` state
- Auth required (401) redirects to `/login` with search state preservation
- Date range exceeded and rate limit with structured error codes
- AbortController for user-initiated search cancellation

**API proxy retry logic** (`app/api/buscar/route.ts`):
- Server-side retry (2 attempts) for 503 status only (502 NOT retried -- backend already retried PNCP)
- 5-minute timeout with AbortController
- Safe JSON parsing with fallback

---

## 7. UX Audit

### 7.1 User Flows

**Primary Flow: Search -> Preview -> Download**
1. User selects states (UF multi-select with region grouping)
2. User selects date range (defaults: last 7 days)
3. User chooses sector or enters custom search terms
4. User optionally sets advanced filters (status, modalidade, valor, esfera, municipio)
5. User clicks "Buscar" (Ctrl+K shortcut available)
6. EnhancedLoadingProgress shows 5-stage progress with SSE real-time updates
7. Results displayed: AI summary card + individual LicitacaoCards
8. User can download Excel, export to Google Sheets, or save search

**Secondary Flows:**
- Login -> Search (with `?redirect=/buscar` support)
- Signup -> Email Verification -> Login
- Search History -> Re-run Search (URL params passed to `/buscar`)
- Plan Upgrade -> Stripe Checkout -> Thank You
- Admin -> User Management -> Plan/Credit editing
- InMail messaging (conversations with admin replies)

### 7.2 Loading States

| Context | Implementation | Quality |
|---|---|---|
| Search execution | `EnhancedLoadingProgress` - 5-stage with SSE + time-based fallback | Excellent - Honest overtime messaging, cancel button, stage descriptions |
| Results rendering | `LoadingResultsSkeleton` - pulse animation, 3 card placeholders | Good - `role="status"`, `aria-label`, sr-only text |
| Auth check | Centered spinner with "Verificando autenticacao..." text | Adequate |
| Sector loading | Retry with exponential backoff (3 attempts), then fallback list | Good - Graceful degradation |
| Page transitions | No loading indicators | Missing - Could benefit from NProgress or similar |
| Modal/dropdown data | Individual loading states per component | Adequate |

### 7.3 Error States

| Context | Implementation | Quality |
|---|---|---|
| Global error boundary | `app/error.tsx` - card with error message + retry button | Good - But uses hardcoded Tailwind colors instead of design system tokens |
| Search errors | Inline error banner with user-friendly translation | Excellent - Comprehensive error mapping |
| Auth errors | Inline alerts with `role="alert"`, Portuguese translations | Good |
| Quota exceeded | Dedicated `quotaError` state with upgrade prompt | Good |
| Download errors | Inline error with retry guidance | Adequate |
| Network errors | Mapped to "Verifique sua internet" | Good |
| API 502/503 | Mapped to "portal PNCP temporariamente indisponivel" | Good - Context-appropriate |

### 7.4 Empty States

**EmptyState component** (`D:\pncp-poc\frontend\app\components\EmptyState.tsx`):
- Icon (document with magnifying glass)
- Title: "Nenhuma Oportunidade Relevante Encontrada"
- Context-aware message with filter rejection breakdown (keyword, value, UF counts)
- Actionable suggestions: expand date range, add states, adjust filters
- "Ajustar criterios de busca" CTA button
- Animation: fade-in-up with staggered items
- **Quality:** Excellent. Informative, actionable, and visually refined.

### 7.5 Form UX

**Login** (`D:\pncp-poc\frontend\app\login\page.tsx`):
- Google OAuth + email/password + magic link toggle
- Password visibility toggle with aria-label
- Disabled state on submit button during loading
- Error/success inline alerts with icons
- `minLength={6}` on password
- "Already logged in" state with redirect

**Signup** (`D:\pncp-poc\frontend\app\signup\page.tsx`):
- Multi-field form (name, company, sector, phone, email, password, confirm)
- Phone input with Brazilian mask formatting (`(XX) XXXXX-XXXX`)
- Consent scroll box requiring scroll-to-bottom before checkbox activation
- Real-time password match validation with visual indicator (border color change)
- Conditional "Outro" sector field
- Comprehensive form-level validation via `isFormValid` computed property

**Search** (`D:\pncp-poc\frontend\app\buscar\page.tsx`):
- Client-side term validation (stopwords, min length 4, special chars) with real-time feedback
- Form validation on date range and UF selection
- `canSearch` computed property prevents submission when invalid
- Keyboard shortcuts (Ctrl+K search, Ctrl+A select all, Escape clear, / help)
- Pull-to-refresh on mobile

**Validation Approach:** Client-side with useState. No form library (react-hook-form). Validation is ad-hoc per form.

### 7.6 Navigation & Wayfinding

- **Header:** Logo + ThemeToggle + UserMenu (with plan badge, quota badge, message badge) -- only on search page
- **Landing navbar:** Separate component with scroll-to-section links + Login/Signup CTAs
- **Footer:** 4-column grid with links to Sobre, Planos, Suporte, Legal sections
- **Skip navigation:** Present in root layout (`<a href="#main-content">`) -- WCAG 2.4.1 compliant
- **Breadcrumbs:** Not implemented
- **No shared app shell:** Protected pages do not share a common sidebar or top-nav. Each manages its own header independently.

---

## 8. Accessibility Audit

### 8.1 Semantic HTML

| Element | Usage | Quality |
|---|---|---|
| `<main id="main-content">` | Landing page, search page | Good |
| `<article>` | LicitacaoCard | Good - with `aria-labelledby` |
| `<nav>` | Not consistently used | Needs improvement |
| `<section>` | Landing page sections | Good |
| `<h1>-<h3>` | Heading hierarchy present | Mostly correct |
| `<form>` | Login, signup, search | Good |
| `<label htmlFor>` | Consistent on form inputs | Good |
| `<footer>` | Footer component | Good |

### 8.2 ARIA Usage

| Pattern | Implementation |
|---|---|
| `role="alert"` | Error messages in login page |
| `role="status"` | Success messages, loading skeleton |
| `role="img" aria-label` | SVG icons throughout |
| `aria-hidden="true"` | Decorative SVGs |
| `aria-label` | Password toggle, share/favorite buttons, loading skeleton |
| `aria-pressed` | Favorite button toggle |
| `aria-labelledby` | LicitacaoCard titles |
| `<title>` | EmptyState SVG icon |

**Issues Found:**
- `role="img"` with `aria-label="Icone"` is overly generic on many SVGs -- should be descriptive
- Missing `aria-live` regions for dynamic content updates (search results, progress)
- No `aria-expanded` on collapsible filter panels
- No `aria-describedby` linking form fields to validation error messages

### 8.3 Keyboard Navigation

**Implemented:**
- Skip navigation link (sr-only, visible on focus)
- Focus-visible outlines (3px solid, WCAG 2.2 Level AAA)
- Keyboard shortcuts: Ctrl+K (search), Ctrl+A (select all), Escape (clear), / (help), Ctrl+Shift+L (clear all), Ctrl+Enter (search)
- Escape closes modals (UpgradeModal, keyboard help dialog)
- Tab navigation through form fields

**Issues Found:**
- No roving tabindex for the 27-state UF grid (each is a separate tab stop)
- Custom dropdown components may not implement full ARIA listbox keyboard pattern
- No visible focus indicator on LicitacaoCard hover-only state transitions

### 8.4 Color Contrast

WCAG compliance is well-documented in `globals.css` with inline contrast ratio comments:

| Token | Contrast vs Canvas | Rating |
|---|---|---|
| `--ink` (#1e2d3b) | 12.6:1 | AAA |
| `--ink-secondary` (#3d5975) | 5.5:1 | AA |
| `--ink-muted` (#6b7a8a) | 5.1:1 | AA (improved from 4.48:1) |
| `--brand-navy` (#0a1e3f) | 14.8:1 | AAA |
| `--brand-blue` (#116dff) | 4.8:1 | AA |
| `--success` (#16a34a) | 4.7:1 | AA |
| `--error` (#dc2626) | 5.9:1 | AA |
| `--warning` (#ca8a04) | 5.2:1 | AA |

Dark mode ratios also documented and pass AA/AAA.

**Issue:** `app/error.tsx` uses hardcoded Tailwind colors (`bg-gray-50`, `text-red-500`, `bg-green-600`) instead of design tokens, breaking dark mode.

**Reduced Motion:** `@media (prefers-reduced-motion: reduce)` in `globals.css` disables all CSS animations. Framer-motion animations may not respect this unless explicitly configured.

---

## 9. Performance Analysis

### 9.1 Bundle Analysis

| Factor | Detail | Bundle Impact |
|---|---|---|
| `framer-motion` | ^12.33.0 (~40KB gzipped) | High - Only used on landing page |
| `recharts` | ^3.7.0 (~70KB gzipped) | High - Only on dashboard (route-split) |
| `shepherd.js` | ^14.5.1 (~30KB gzipped) | Medium - Only on search page |
| `mixpanel-browser` | ^2.74.0 (~20KB gzipped) | Medium - Every page via AnalyticsProvider |
| `react-day-picker` | ^9.13.0 | Low - Tree-shakeable |
| `lucide-react` | ^0.563.0 | Low - Tree-shakeable |

### 9.2 Code Splitting

- Next.js App Router provides automatic route-based splitting
- `'use client'` boundaries placed correctly
- **Issue:** No `next/dynamic` usage for heavy components (EnhancedLoadingProgress, UpgradeModal, framer-motion sections)
- `recharts` is route-split to `/dashboard` (no issue)

### 9.3 Image Optimization

- Next.js `<Image>` used for logo in search page
- Remote pattern: `static.wixstatic.com` only
- Landing page uses SVG icons (lucide-react) -- good
- No lazy loading of below-fold images observed

**Font Optimization:**
- Three Google Fonts loaded via `next/font/google` (self-hosted, optimized)
- `display: "swap"` prevents FOIT
- Fahkwang (specialty display font) could benefit from subsetting

**Caching:**
- Excel files in `tmpdir()` with 60-min setTimeout cleanup (lost on restart)
- No client-side caching for sector list (re-fetched per visit)
- No service worker active caching

---

## 10. Responsive Design

**Approach:** Tailwind responsive prefixes (`sm:`, `md:`, `lg:`) throughout.

**Breakpoints (default Tailwind):** sm=640px, md=768px, lg=1024px, xl=1280px

**Mobile-Specific Features:**
- Pull-to-refresh enabled only below 768px
- Mobile date picker with 44px touch targets
- Login/signup: `flex-col md:flex-row` stacking
- Messages: mobile thread view toggle
- All buttons/inputs: `min-height: 44px` (touch-friendly)
- Landing page: `max-w-landing` (1200px) with responsive padding

**Issues:**
- Admin page responsive behavior not well-defined for small screens
- No specific tablet optimization beyond md breakpoint

---

## 11. Technical Debt Inventory

### 11.1 Critical

| ID | Issue | File(s) |
|---|---|---|
| **TD-C1** | **Monolithic search page** - `buscar/page.tsx` is ~1100 lines with 30+ useState hooks, all business logic inline | `app/buscar/page.tsx` |
| **TD-C2** | **localhost fallback in analytics route** - `http://localhost:8000` as BACKEND_URL fallback | `app/api/analytics/route.ts` line 4 |
| **TD-C3** | **Mixed API patterns** - Some pages use proxy, others call backend directly from browser | `historico/page.tsx`, `conta/page.tsx`, `admin/page.tsx` |

### 11.2 High

| ID | Issue | File(s) |
|---|---|---|
| **TD-H1** | **Duplicated filter components** - EsferaFilter and MunicipioFilter in two directories | `app/components/` + `components/` |
| **TD-H2** | **Direct DOM manipulation** in search state restoration (document.createElement) | `app/buscar/page.tsx` lines 285-293 |
| **TD-H3** | **Error boundary ignores design system** - hardcoded Tailwind colors break dark mode | `app/error.tsx` |
| **TD-H4** | **Native alert() for user feedback** instead of sonner toast system | `app/buscar/page.tsx` line 1080 |
| **TD-H5** | **Duplicate UF_NAMES** mapping in multiple files | `buscar/page.tsx`, `dashboard/page.tsx` |
| **TD-H6** | **Excel storage in tmpdir()** - lost on restart, no horizontal scaling | `app/api/buscar/route.ts`, `app/api/download/route.ts` |

### 11.3 Medium

| ID | Issue | File(s) |
|---|---|---|
| **TD-M1** | No shared app shell for protected pages | All protected pages |
| **TD-M2** | Feature flag system underused | `lib/config.ts` |
| **TD-M3** | No form validation library | Login, signup, search pages |
| **TD-M4** | STOPWORDS_PT list duplicated from backend | `app/buscar/page.tsx` lines 70-82 |
| **TD-M5** | SETORES_FALLBACK must be manually synced | `app/buscar/page.tsx` lines 429-442 |
| **TD-M6** | Stale file: `dashboard-old.tsx` | `app/dashboard-old.tsx` |
| **TD-M7** | Stale file: `landing-layout-backup.tsx` | `app/landing-layout-backup.tsx` |
| **TD-M8** | No middleware-based auth guards (flash of unprotected content) | All protected pages |
| **TD-M9** | Deprecated `performance.timing` usage | `app/components/AnalyticsProvider.tsx` line 53 |

### 11.4 Low

| ID | Issue | File(s) |
|---|---|---|
| **TD-L1** | SVG icons not componentized (generic `aria-label="Icone"`) | Multiple pages |
| **TD-L2** | useEffect with serialized Set dependency | `app/buscar/page.tsx` line 426 |
| **TD-L3** | Hardcoded plan prices differ between pages (149/349/997 vs 297/597/1497) | `pricing/page.tsx`, `lib/plans.ts` |
| **TD-L4** | Unused barrel file `components/filters/index.ts` | `components/filters/index.ts` |
| **TD-L5** | No robots.txt or sitemap | N/A |
| **TD-L6** | No OpenGraph images configured | `app/layout.tsx` |
| **TD-L7** | Test coverage ~49.46% vs 60% threshold (70 pre-existing failures) | `__tests__/` |

---

## 12. Recommendations

### Priority 1: Structural

1. **Decompose `buscar/page.tsx`** into sub-components:
   - `SearchForm` (UF selector, dates, sector, terms)
   - `FilterPanel` (status, modalidade, valor, esfera, municipio, ordenacao)
   - `SearchResults` (summary, cards, download, export)
   - `useSearch` hook (execution, retry, error handling, analytics)
   - `useSearchFilters` hook (all filter state)

2. **Unify API access pattern** -- route all backend calls through `/api/*` proxy. Eliminate direct `NEXT_PUBLIC_BACKEND_URL` browser calls.

3. **Add Next.js middleware auth guard** -- redirect unauthenticated users before page render.

4. **Create shared app layout** -- `(app)/layout.tsx` group with consistent header/nav for all protected pages.

### Priority 2: Quality

5. **Resolve component duplication** -- consolidate EsferaFilter and MunicipioFilter to single locations.

6. **Fix error boundary** -- replace hardcoded colors with design system tokens for dark mode support.

7. **Replace alert() with sonner toast** -- use the existing toast system for all user feedback.

8. **Fix analytics route fallback** -- remove localhost:8000 default, return 503 when unconfigured.

9. **Adopt form validation library** -- zod schemas + react-hook-form for all forms.

### Priority 3: Performance

10. **Dynamic imports** -- use `next/dynamic` for EnhancedLoadingProgress, UpgradeModal, framer-motion landing sections.

11. **Cache sector list client-side** -- prevent redundant fetches.

12. **Move Excel storage to object storage** -- Supabase Storage or S3 for restart persistence and scaling.

### Priority 4: Polish

13. Add breadcrumbs to protected pages.

14. Improve ARIA: `aria-expanded` on filter panels, `aria-live="polite"` on results, `aria-describedby` for validation errors.

15. Remove stale files: `dashboard-old.tsx`, `landing-layout-backup.tsx`.

16. Reconcile plan pricing across `lib/plans.ts` and `pricing/page.tsx`.

17. Add `robots.txt`, sitemap, and OpenGraph images.

18. Increase test coverage to meet 60% threshold.

---

## Appendix A: File Tree Summary

```
frontend/
  app/
    layout.tsx                          # Root layout
    page.tsx                            # Landing page (/)
    globals.css                         # Design system tokens
    error.tsx                           # Global error boundary
    types.ts                            # Shared TypeScript interfaces
    dashboard-old.tsx                   # [DEAD CODE]
    landing-layout-backup.tsx           # [DEAD CODE]
    buscar/page.tsx                     # Main search (~1100 lines)
    login/page.tsx                      # Login
    signup/page.tsx                     # Registration
    dashboard/page.tsx                  # Analytics dashboard
    historico/page.tsx                  # Search history
    conta/page.tsx                      # Account management
    planos/page.tsx                     # Plan management + Stripe
    planos/obrigado/page.tsx            # Post-checkout
    mensagens/page.tsx                  # InMail messaging
    admin/page.tsx                      # Admin panel
    pricing/page.tsx                    # ROI calculator
    features/page.tsx                   # Feature descriptions
    termos/page.tsx                     # Terms of service
    privacidade/page.tsx                # Privacy policy
    auth/callback/page.tsx              # OAuth callback
    api/                                # 10+ proxy routes
    components/                         # ~35 components
      landing/                          # 10 landing sections
      ui/                               # 4 UI primitives
    hooks/
      useInView.ts                      # Scroll visibility
  components/                           # ~15 shared components
    subscriptions/                      # 6 subscription components
    filters/index.ts                    # Barrel file
  hooks/                                # 10 custom hooks
  lib/                                  # Utilities, config, copy
    animations/                         # Animation utilities
    copy/                               # Marketing copy
    icons/                              # Icon components
  __tests__/                            # 55 test files
  e2e-tests/                            # Playwright E2E
  next.config.js
  tailwind.config.ts
  tsconfig.json
  package.json
```

## Appendix B: Environment Variables

| Variable | Side | Required | Purpose |
|---|---|---|---|
| `BACKEND_URL` | Server | Yes | Backend API URL for proxy routes |
| `NEXT_PUBLIC_BACKEND_URL` | Client | No* | Direct backend calls (*should be eliminated) |
| `NEXT_PUBLIC_SUPABASE_URL` | Client | Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Client | Yes | Supabase anonymous key |
| `NEXT_PUBLIC_CANONICAL_URL` | Client | No | Canonical URL for OAuth redirects |
| `NEXT_PUBLIC_APP_NAME` | Client | No | White-label app name (default: SmartLic.tech) |
| `NEXT_PUBLIC_LOGO_URL` | Client | No | White-label logo URL (default: /logo.svg) |
| `NEXT_PUBLIC_API_URL` | Client | No | API URL in config.ts |
| `NEXT_PUBLIC_MIXPANEL_TOKEN` | Client | No | Mixpanel analytics token |
| `NEXT_PUBLIC_ENABLE_NEW_PRICING` | Client | No | Feature flag for pricing UI |
