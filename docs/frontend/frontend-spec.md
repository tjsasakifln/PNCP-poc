# Frontend Specification — SmartLic v0.5

> Generated: 2026-03-04 | Audit by @ux-design-expert (Pixel)
> Codebase snapshot: commit `4da1d98` (main)

---

## 1. Overview

### Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js | 16.1.6 |
| UI Library | React | 18.3.1 |
| Language | TypeScript | 5.9.3 |
| Styling | Tailwind CSS | 3.4.19 |
| Animation | Framer Motion | 12.33.0 |
| Charts | Recharts | 3.7.0 |
| Auth | Supabase SSR | 0.8.0 |
| DnD | @dnd-kit/core | 6.3.1 |
| Onboarding | Shepherd.js | 14.5.1 |
| Notifications | Sonner | 2.0.7 |
| Error Tracking | Sentry | 10.38.0 |
| Analytics | Mixpanel | 2.74.0 |
| Icons | Lucide React | 0.563.0 |
| Date Utils | date-fns | 4.1.0 |

### Architecture Approach

- **App Router** (Next.js 14+ directory-based routing in `app/`)
- **Standalone output** (`output: 'standalone'`) for Railway deployment
- All pages are **client components** (`"use client"`) -- no Server Components used for pages
- Landing page (`/`) is the only server component page (static, no `"use client"`)
- **API proxy pattern**: All backend calls routed through `app/api/` Next.js routes to avoid CORS and add auth headers
- **SSE dual-connection**: Real-time search progress via Server-Sent Events with time-based fallback simulation
- **Feature-flag gating**: Some features (alerts, messages, orgs) behind `NEXT_PUBLIC_*` env vars or `SHIP-*` flags

### Key Patterns

1. **Auth-gated navigation**: `NavigationShell` conditionally renders `Sidebar` + `BottomNav` only on protected routes
2. **Plan-aware UI**: `usePlan()` hook drives feature gating, quota badges, upsell CTAs, and trial conversion flows
3. **Error resilience**: Structured error objects (`SearchError`), error boundaries, transient error detection, auto-retry with exponential backoff
4. **Progressive disclosure**: First-time users see collapsed filters; returning users see persisted state from localStorage
5. **Onboarding tours**: Shepherd.js-powered guided tours (search, results, pipeline) with analytics tracking

---

## 2. Design System

### 2.1 Colors & Theme

The design system uses CSS custom properties (variables) defined in `globals.css`, referenced via Tailwind config. This enables runtime dark mode switching without Tailwind class duplication.

**Light Mode Palette:**

| Token | Value | Purpose | WCAG vs Canvas |
|-------|-------|---------|----------------|
| `--canvas` | `#ffffff` | Base background | - |
| `--ink` | `#1e2d3b` | Primary text | 12.6:1 (AAA) |
| `--ink-secondary` | `#3d5975` | Secondary text | 5.5:1 (AA) |
| `--ink-muted` | `#6b7a8a` | Muted text/labels | 5.1:1 (AA) |
| `--ink-faint` | `#c0d2e5` | Decorative borders | 1.9:1 (decorative) |
| `--brand-navy` | `#0a1e3f` | Primary brand | 14.8:1 (AAA) |
| `--brand-blue` | `#116dff` | Accent/CTA | 4.8:1 (AA) |
| `--brand-blue-hover` | `#0d5ad4` | Hover state | 6.2:1 (AA+) |
| `--success` | `#16a34a` | Success | 4.7:1 (AA) |
| `--error` | `#dc2626` | Error | 5.9:1 (AA) |
| `--warning` | `#ca8a04` | Warning | 5.2:1 (AA) |

**Dark Mode:** Full override set in `.dark` selector with WCAG-documented contrast ratios. All semantic colors adjusted for dark backgrounds (e.g., `--ink` becomes `#e8eaed` at 11.8:1 vs `--canvas` `#121212`).

**Surface Hierarchy:** 4 levels (`surface-0` through `surface-elevated`) for depth perception.

**Gem Palette (GTM-006):** Translucent gemstone colors (sapphire, emerald, amethyst, ruby) with matching shadows for accent cards.

**WCAG Compliance Status:** All text colors documented with contrast ratios. Dark mode received dedicated fix (SAB-003) for timestamps/labels. `--ink-muted` was adjusted from 4.48:1 to 5.1:1 to meet AA.

### 2.2 Typography

| Family | Variable | Font | Purpose |
|--------|----------|------|---------|
| Body | `--font-body` | DM Sans | All body text, labels, UI |
| Display | `--font-display` | Fahkwang | Headings, hero text |
| Data | `--font-data` | DM Mono | Numbers, code, tabular data |

**Fluid Scale (STORY-174):**
- Hero: `clamp(2.5rem, 5vw + 1rem, 4.5rem)` (40-72px)
- H1: `clamp(2rem, 4vw + 1rem, 3.5rem)` (32-56px)
- H2: `clamp(1.5rem, 3vw + 0.5rem, 2.5rem)` (24-40px)
- H3: `clamp(1.25rem, 2vw + 0.5rem, 1.75rem)` (20-28px)
- Body: `clamp(14px, 1vw + 10px, 16px)` (set on `body`)

**Issue:** Font loading uses `display: "swap"` (good), but Fahkwang is a decorative Thai-Latin font with limited weight coverage. Only loaded weights: 400, 500, 600, 700.

### 2.3 Spacing & Layout

- **Base grid:** 4px (Tailwind default, commented in config as `// Enforce 4px base`)
- **Border radius tokens:** `input: 4px`, `button: 6px`, `card: 8px`, `modal: 12px`
- **Max content width:** `max-w-5xl` (1024px) for main content, `max-w-landing` (1200px) for landing
- **Section spacing (8pt grid):** `--section-padding-sm: 4rem` (mobile), `--section-padding-lg: 6rem` (desktop)
- **Touch targets:** Global `button { min-height: 44px }` in CSS -- meets WCAG 2.5.8 (AAA)

### 2.4 Component Patterns

**Consistent patterns found:**
- `PageHeader` reusable component for protected page titles
- `EmptyState` and `ErrorStateWithRetry` for consistent empty/error UI
- `AuthLoadingScreen` for auth-gate loading states
- `Dialog` component for modals (custom, not a library)
- Design tokens via CSS variables + Tailwind extension (not raw hex values)

**Inconsistent patterns found:**
- Some components use `var(--brand-blue)` directly, others use Tailwind `text-brand-blue`
- Inline SVG icons in `Sidebar.tsx` (75 lines of SVGs) instead of lucide-react icons used elsewhere
- Some pages build their own loading spinners; others use `AuthLoadingScreen`
- No shared Button component -- each page implements its own button styles

### 2.5 Dark Mode Support

- **Strategy:** `darkMode: "class"` with localStorage persistence (`smartlic-theme` key)
- **Anti-flash script:** Inline `<script>` in `<head>` reads theme before paint
- **System preference:** `prefers-color-scheme: dark` respected when theme is "system"
- **Coverage:** All CSS variables have dark overrides. WCAG contrast verified for dark mode.
- **Shepherd.js:** Custom dark mode styles via `.dark .shepherd-theme-custom` overrides
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` kills all animations globally

---

## 3. Page Inventory

| Route | Page | Lines | Complexity | Auth | Key Components |
|-------|------|-------|-----------|------|----------------|
| `/` | Landing | 33 | Low | No | HeroSection, OpportunityCost, BeforeAfter, HowItWorks, StatsSection, FinalCTA |
| `/login` | Login | 510 | Medium | No | InstitutionalSidebar, TotpVerificationScreen (lazy) |
| `/signup` | Signup | 770 | High | No | InstitutionalSidebar, email/phone validation, confirmation polling |
| `/auth/callback` | OAuth Callback | ~50 | Low | No | PKCE verifier handling |
| `/recuperar-senha` | Password Recovery | ~100 | Low | No | - |
| `/redefinir-senha` | Password Reset | ~100 | Low | No | - |
| `/onboarding` | Onboarding Wizard | 688 | High | Yes | 3-step wizard (CNAE, UFs, Confirmation) |
| `/buscar` | **Search** | 1019 | **Very High** | Yes | SearchForm, SearchResults, SSE progress, 29 sub-components |
| `/dashboard` | Dashboard | 1038 | High | Yes | Recharts (Bar, Line, Pie), analytics cards |
| `/pipeline` | Pipeline Kanban | 480 | High | Yes | @dnd-kit DnD, PipelineColumn, PipelineCard |
| `/historico` | Search History | 466 | Medium | Yes | Session list, status badges |
| `/alertas` | Alerts | 1068 | High | Yes | Alert CRUD, sector/UF/value filters |
| `/mensagens` | Messages | 568 | Medium | Yes | Conversation list + detail, threaded replies |
| `/conta` | Account | 1420 | **Very High** | Yes | Profile context, plan info, password change, MFA, cancel |
| `/conta/seguranca` | Security | ~200 | Medium | Yes | MFA setup wizard |
| `/conta/equipe` | Team | ~300 | Medium | Yes | Organization members (feature-gated) |
| `/planos` | Pricing | 675 | High | No* | PlanToggle, FAQ accordion, Stripe checkout |
| `/planos/obrigado` | Thank You | ~80 | Low | Yes | Post-checkout confirmation |
| `/pricing` | Marketing Pricing | ~200 | Medium | No | Alternative pricing page |
| `/features` | Features | ~200 | Medium | No | Feature showcase |
| `/admin` | Admin Users | 764 | High | Admin | User management, credit editing |
| `/admin/cache` | Admin Cache | ~300 | Medium | Admin | Cache stats, invalidation |
| `/admin/slo` | Admin SLO | ~200 | Medium | Admin | SLO metrics dashboard |
| `/admin/metrics` | Admin Metrics | ~200 | Medium | Admin | System metrics |
| `/admin/emails` | Admin Emails | ~200 | Medium | Admin | Email management |
| `/admin/partners` | Admin Partners | ~200 | Medium | Admin | Partner management |
| `/status` | Public Status | 251 | Medium | No | UptimeChart, IncidentList |
| `/ajuda` | Help Center | ~200 | Medium | No | FAQ, contact |
| `/sobre` | About | ~100 | Low | No | Company info |
| `/termos` | Terms | ~100 | Low | No | Legal text |
| `/privacidade` | Privacy | ~100 | Low | No | Legal text |
| `/blog` | Blog Index | ~200 | Medium | No | Article list |
| `/blog/[slug]` | Blog Article | ~200 | Medium | No | MDX content |
| `/blog/programmatic/[setor]` | Programmatic SEO | ~200 | Low | No | Auto-generated sector pages |
| `/blog/programmatic/[setor]/[uf]` | Programmatic SEO | ~200 | Low | No | Auto-generated sector+UF pages |
| `/blog/panorama/[setor]` | Sector Panorama | ~200 | Low | No | Auto-generated panorama |
| `/blog/licitacoes/*` | SEO Licitacoes | ~200 | Low | No | Programmatic SEO |
| `/licitacoes` | SEO Licitacoes | ~200 | Low | No | Sector directory |
| `/licitacoes/[setor]` | SEO Sector | ~200 | Low | No | Sector-specific |
| `/como-avaliar-licitacao` | Content Page | ~100 | Low | No | Educational article |
| `/como-evitar-prejuizo-licitacao` | Content Page | ~100 | Low | No | Educational article |
| `/como-filtrar-editais` | Content Page | ~100 | Low | No | Educational article |
| `/como-priorizar-oportunidades` | Content Page | ~100 | Low | No | Educational article |

**Total: 44 page files** (22 noted in CLAUDE.md, actual count is higher due to blog, SEO, and admin sub-pages).

---

## 4. Component Inventory

### 4.1 Search Components (buscar/components/) -- 29 files

| Component | Purpose | Lines (est.) |
|-----------|---------|-------------|
| `SearchForm.tsx` | Main search form with sectors, UFs, dates, filters | 707 |
| `SearchResults.tsx` | Results display, sorting, export, pagination | 1,581 |
| `FilterPanel.tsx` | Advanced filters (modalidade, status, valor, esfera) | ~200 |
| `SearchErrorBoundary.tsx` | React error boundary for search area | ~60 |
| `SearchStateManager.tsx` | Search lifecycle state visualization | ~150 |
| `UfProgressGrid.tsx` | Per-UF SSE progress indicators | ~120 |
| `SourceStatusGrid.tsx` | Data source status badges | ~100 |
| `EnhancedLoadingProgress` (shared) | Educational carousel loading with SSE | ~250 |
| `ErrorDetail.tsx` | Structured error display (7 conditional fields) | ~120 |
| `LlmSourceBadge.tsx` | LLM classification source indicator | ~40 |
| `ViabilityBadge.tsx` | 4-factor viability score badge | ~60 |
| `FeedbackButtons.tsx` | User relevance feedback (thumbs up/down) | ~80 |
| `ReliabilityBadge.tsx` | Data reliability indicator | ~40 |
| `CompatibilityBadge.tsx` | Profile compatibility indicator | ~40 |
| `FreshnessIndicator.tsx` | Cache age indicator | ~40 |
| `ActionLabel.tsx` | Recommended action label | ~30 |
| `DeepAnalysisModal.tsx` | Deep analysis modal for individual bid | ~150 |
| `ZeroResultsSuggestions.tsx` | Empty state with actionable suggestions | ~100 |
| `FilterRelaxedBanner.tsx` | Banner when filters auto-relaxed | ~40 |
| `FilterStatsBreakdown.tsx` | Filtering pipeline stats visualization | ~80 |
| `CoverageBar.tsx` | UF coverage progress bar | ~40 |
| `PartialResultsPrompt.tsx` | Prompt to view partial results mid-search | ~60 |
| `PartialTimeoutBanner.tsx` | Timeout warning with partial data | ~60 |
| `RefreshBanner.tsx` | Stale data refresh prompt | ~60 |
| `SourcesUnavailable.tsx` | All sources down fallback UI | ~80 |
| `SearchErrorBanner.tsx` | Inline error banner | ~40 |
| `ExpiredCacheBanner.tsx` | Expired cache warning | ~40 |
| `DataQualityBanner.tsx` | Data quality/degradation indicator | ~80 |
| `TruncationWarningBanner.tsx` | PNCP 50-item truncation warning | ~40 |

### 4.2 Shared Components

**App Components (`app/components/`) -- 66 files:**

| Category | Components |
|----------|-----------|
| **Auth** | AuthProvider, ThemeProvider, ThemeToggle, UserMenu, SessionExpiredBanner, InstitutionalSidebar |
| **Navigation** | LandingNavbar, Breadcrumbs, SavedSearchesDropdown |
| **Billing/Trial** | QuotaBadge, QuotaCounter, PlanBadge, UpgradeModal, TrialConversionScreen, TrialExpiringBanner, TrialCountdown, Countdown |
| **Landing** | HeroSection, OpportunityCost, BeforeAfter, HowItWorks, StatsSection, FinalCTA, SectorsGrid, ProofOfValue, DataSourcesSection, DifferentialsGrid, TrustCriteria, AnalysisExamplesCarousel |
| **Data Display** | LicitacaoCard, LicitacoesPreview, StatusBadge, ComparisonTable, ValuePropSection |
| **Forms/UI** | Dialog, CustomSelect, CustomDateInput, RegionSelector, EsferaFilter, MunicipioFilter, OrgaoFilter, OrdenacaoSelect, PaginacaoSelect |
| **UI Primitives** | Tooltip, GradientButton, GlassCard, BentoGrid, CategoryBadge, ScoreBar |
| **Feedback** | EmptyState, LoadingProgress, LoadingResultsSkeleton, ContextualTutorialTooltip |
| **Blog** | BlogArticleLayout, ContentPageLayout |
| **Analytics** | AnalyticsProvider, GoogleAnalytics, ClarityAnalytics, StructuredData, CookieConsentBanner |
| **Pipeline** | AddToPipelineButton, PipelineAlerts |

**Root Components (`components/`) -- 43 files:**

| Category | Components |
|----------|-----------|
| **Layout** | NavigationShell, Sidebar, BottomNav, MobileDrawer, MobileMenu, PageHeader |
| **Loading** | EnhancedLoadingProgress, LoadingProgress, AuthLoadingScreen |
| **Error** | ErrorStateWithRetry, BackendStatusIndicator |
| **Billing** | PaymentFailedBanner, PaymentRecoveryModal, TrialUpsellCTA, TrialPaywall |
| **Subscriptions** | PlanCard, PlanToggle, FeatureBadge, AnnualBenefits, DowngradeModal, TrustSignals |
| **Account** | CancelSubscriptionModal, ProfileCompletionPrompt, ProfileProgressBar, ProfileCongratulations |
| **Auth** | MfaSetupWizard, TotpVerificationScreen, MfaEnforcementBanner |
| **Search Filters** | ValorFilter, StatusFilter, ModalidadeFilter |
| **Export** | GoogleSheetsExportButton |
| **Reports** | PdfOptionsModal |
| **Blog** | BlogCTA, SchemaMarkup, RelatedPages |
| **Organizations** | InviteMemberModal |
| **UI** | Pagination, CurrencyInput |
| **Onboarding** | OnboardingTourButton |
| **Other** | AlertNotificationBell, TestimonialSection |

### 4.3 Component Dependencies

**Fragmented component locations are a significant issue.** Components are split across three directories:
1. `app/components/` -- 66 files (page-specific + shared)
2. `components/` -- 43 files (truly shared)
3. `app/buscar/components/` -- 29 files (search-specific)

There is no clear convention for which directory gets new components. For example:
- `EmptyState` exists in both `app/components/EmptyState.tsx` AND `components/EmptyState.tsx`
- `LoadingProgress` exists in both `app/components/LoadingProgress.tsx` AND `components/LoadingProgress.tsx`
- Billing components are split between `components/billing/` and `components/subscriptions/`

---

## 5. State Management

### 5.1 Server State (API calls)

- **No data fetching library** (no SWR, TanStack Query, or similar)
- All API calls use raw `fetch()` with manual state management (`useState` + `useEffect`)
- `useFetchWithBackoff` hook provides exponential retry (2s to 30s cap, max 5 retries)
- Plan data cached in localStorage (`smartlic_cached_plan`, 1hr TTL) via `usePlan()`
- Sectors cached in localStorage with SWR-style stale serving via `useSearchFilters()`

### 5.2 Client State (React state, localStorage)

**Heavy localStorage usage (13+ keys identified):**

| Key | Purpose | TTL |
|-----|---------|-----|
| `smartlic-theme` | Dark/light mode | Permanent |
| `smartlic_cached_plan` | Plan info cache | 1 hour |
| `smartlic-has-searched` | First-search flag | Permanent |
| `smartlic-first-tip-dismissed` | First-use tip state | Permanent |
| `smartlic:buscar:filters-expanded` | Filter panel state | Permanent |
| `smartlic_onboarding_completed` | Welcome tour state | Permanent |
| `smartlic_onboarding_dismissed` | Welcome tour dismissed | Permanent |
| `smartlic_tour_*_completed` | Per-tour completion state | Permanent |
| `smartlic-sidebar-collapsed` | Sidebar collapse state | Permanent |
| `smartlic-search-state` | Search form persistence | Per-session |
| `smartlic-last-search` | Last search results cache | Per-session |
| `smartlic-partial-*` | Partial search results | 30 min |
| `profileContext` | User profile context | Permanent |
| `smartlic_setores_*` | Sectors fallback cache | 30 min |

**Issue:** No centralized localStorage abstraction. Each feature directly calls `localStorage.getItem/setItem`. No storage quota management.

### 5.3 Auth State (Supabase)

- `AuthProvider` context wraps entire app
- Auth state from `supabase.auth.onAuthStateChange()` listener
- 10-second timeout fallback to `getSession()` (cookie-based, no network)
- `isMountedRef` prevents setState after unmount (UX-408)
- Admin status fetched separately via `/v1/me` backend call
- PKCE verifier guard for OAuth callbacks

### 5.4 SSE/Real-time State

- `useSearchSSE` hook manages EventSource connection to `/api/buscar-progress`
- Events: `progress`, `uf_complete`, `source_status`, `filter_summary`, `partial`, `degraded`, `refresh_available`, `llm_ready`, `excel_ready`, `pending_review`, `error`, `complete`
- Fallback: Time-based simulation when SSE unavailable
- Reconnection logic with `isReconnecting` state
- `useSearchPolling` as secondary fallback for search status

---

## 6. API Integration

### 6.1 Proxy Pattern (app/api/) -- 57 routes

All backend API calls are proxied through Next.js API routes to:
1. Add `Authorization` header from Supabase session
2. Avoid CORS issues (same-origin)
3. Add structured logging and error transformation
4. Hide backend URL from client

**Key proxies:**

| Frontend Route | Backend Endpoint | Method |
|---------------|-----------------|--------|
| `/api/buscar` | `/buscar` | POST |
| `/api/buscar-progress` | `/buscar-progress/{id}` | GET (SSE) |
| `/api/download` | `/download/{id}` | GET |
| `/api/analytics` | `/v1/analytics/*` | GET |
| `/api/pipeline` | `/v1/pipeline/*` | GET/POST/PATCH/DELETE |
| `/api/plans` | `/v1/plans` | GET |
| `/api/me` | `/v1/me` | GET |
| `/api/subscription-status` | `/v1/subscription/status` | GET |
| `/api/admin/[...path]` | `/v1/admin/*` | Dynamic |
| `/api/feedback` | `/v1/feedback` | POST/DELETE |

### 6.2 Error Handling

**Multi-layer error handling:**

1. **Proxy layer** (`proxy-error-handler.ts`): Extracts `error_code`, `correlation_id`, `search_id` from backend responses. Maps HTTP status to user-friendly messages.
2. **Hook layer** (`useSearch.ts`): `SearchError` interface with `message`, `rawMessage`, `errorCode`, `correlationId`, `requestId`, `httpStatus`, `timestamp`
3. **UI layer**: `ErrorDetail.tsx` renders up to 7 conditional fields. `ErrorStateWithRetry` provides retry button.
4. **Error boundary**: `SearchErrorBoundary` wraps search results area only (not the form)

**Error message mapping** (`error-messages.ts`):
- `getUserFriendlyError()` -- HTTP status to Portuguese message
- `getMessageFromErrorCode()` -- Backend error codes to messages
- `isTransientError()` -- 502/503/504 + network errors
- `translateAuthError()` -- Supabase auth errors to Portuguese
- `getHumanizedError()` -- Structured error with title + suggestion

### 6.3 Loading States

| Pattern | Usage |
|---------|-------|
| Spinner (`animate-spin`) | Auth loading, inline operations |
| `AuthLoadingScreen` | Full-page auth gate |
| `EnhancedLoadingProgress` | Search progress with educational carousel |
| `LoadingResultsSkeleton` | Search results skeleton |
| NProgress bar | Page navigation transitions |
| `useFetchWithBackoff` | Exponential retry with countdown |
| Pull-to-refresh | Mobile search page refresh |

**Issue:** Multiple loading spinner implementations. At least 4 different inline spinner patterns found across pages (different sizes, border styles). No shared `Spinner` component.

### 6.4 Cache Strategy (frontend)

- **Plan cache:** localStorage, 1hr TTL, used as fallback during API failures
- **Sectors cache:** localStorage, 30min TTL, SWR-style (serve stale, revalidate in background)
- **Last search cache:** localStorage, session-scoped, stores full search results
- **Partial search cache:** localStorage, 30min TTL, stores mid-search partial results
- **Search state persistence:** localStorage, persists form inputs across page navigations
- **No HTTP cache headers** managed on proxy level (relies on backend Cache-Control)

---

## 7. UX Patterns

### 7.1 Navigation Flow

**Desktop:** Left sidebar (collapsible, state persisted in localStorage) + main content area.

**Mobile:** Bottom navigation bar (5 items) + hamburger menu drawer.

**Protected routes:** `/buscar`, `/dashboard`, `/pipeline`, `/historico`, `/conta`, `/admin`

**Public routes:** `/`, `/login`, `/signup`, `/planos`, `/pricing`, `/features`, `/ajuda`, `/status`, `/termos`, `/privacidade`, `/blog/*`, `/licitacoes/*`, content pages

**Navigation items:** Buscar, Dashboard, Pipeline, Historico, Conta (primary) + Ajuda, Sair (secondary). Alerts and Messages are feature-gated (removed from nav in SHIP-002).

**Issue:** The search page (`/buscar`) renders its own header with logo, theme toggle, user menu, and backend status -- duplicating functionality from the sidebar. This creates two competing navigation paradigms on the same page.

### 7.2 Search Experience

The search flow is the core UX, spanning ~4,000 lines across 3 hooks + 30 components:

1. **Form setup:** Sector selection OR custom terms, UF multi-select, date range, advanced filters (modalidade, status, valor, esfera, municipio)
2. **Execution:** POST to `/api/buscar`, SSE progress stream via `/api/buscar-progress`
3. **Progress:** Educational B2G carousel (replaces technical stage indicators), UF progress grid, source status badges
4. **Results:** Paginated cards with viability badge, LLM source badge, feedback buttons, deep analysis modal
5. **Actions:** Excel export, PDF diagnostico report, Google Sheets export, add to pipeline, save search

**Progressive disclosure (UX-346):** First-time users see minimal form. Returning users see expanded filters based on localStorage state.

**Keyboard shortcuts:** `Ctrl+K` (search), `Ctrl+A` (select all UFs), `Escape` (clear), `/` (show shortcuts).

### 7.3 Onboarding Flow

**3-tier onboarding system:**

1. **Welcome tour** (Shepherd.js): Auto-starts on first visit, introduces the platform
2. **Search tour** (Shepherd.js): 4 steps teaching search form usage
3. **Results tour** (Shepherd.js): 4 steps teaching results interpretation
4. **Pipeline tour** (Shepherd.js): 3 steps teaching kanban usage

**Strategic onboarding (`/onboarding`):** 3-step wizard:
- Step 1: CNAE code + primary objective
- Step 2: UFs + value range
- Step 3: Confirmation + auto-search redirect

**Tour analytics:** All tour events (start, complete, skip, step count) tracked via analytics and backend API.

### 7.4 Error Recovery

| Scenario | Recovery |
|----------|---------|
| Backend offline | `BackendStatusIndicator` polls `/api/health` every 30s. Queues search, auto-executes on recovery. |
| Transient error (502/503/504) | Auto-retry with countdown [10s, 20s, 30s], max 3 attempts |
| Search timeout | Partial results prompt after 30s. Full timeout shows structured error with retry. |
| SSE disconnect | Falls back to time-based simulation. Shows "Reconnecting..." indicator. |
| All sources down | `SourcesUnavailable` component with last search recovery option |
| Expired cache | `ExpiredCacheBanner` with refresh action |
| Quota exceeded | `TrialPaywall` or `UpgradeModal` depending on plan |
| Payment failed | `PaymentFailedBanner` (global) + `PaymentRecoveryModal` (grace period) |

### 7.5 Loading/Progress Feedback

**Search progress is the most sophisticated loading pattern:**
- SSE-driven real-time progress with asymptotic cap at 95%
- Educational B2G carousel (UX-411) showing industry facts during wait
- Per-UF status grid showing completion state per Brazilian state
- Per-source status showing PNCP/PCP/ComprasGov status
- Filter summary showing how many items filtered at each pipeline stage
- Overtime messaging when search exceeds estimated time
- Cancel button for user control

### 7.6 Responsive Design

**Breakpoints:** Tailwind defaults (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`).

**Mobile-specific features:**
- Bottom navigation bar (`BottomNav`)
- Mobile drawer menu (`MobileDrawer`)
- Pull-to-refresh on search page
- Pipeline mobile tabs (`PipelineMobileTabs`) replacing kanban columns
- React Day Picker with 44px touch targets
- Hamburger menu with "Menu" label (AC8: 44px touch target)

**Desktop-specific features:**
- Collapsible sidebar with persistence
- Keyboard shortcuts
- Full kanban board view

**Issue:** `useIsMobile()` hook checks `window.innerWidth < 768` -- this is a JS-based check that causes layout shift. CSS-only approach with `hidden lg:block` is used inconsistently alongside this hook.

### 7.7 Accessibility (WCAG)

**Implemented:**
- Skip navigation link (`<a href="#main-content">Pular para conteudo principal</a>`)
- `lang="pt-BR"` on `<html>`
- WCAG AAA focus indicators (3px outline, 2px offset)
- 44px minimum touch targets (global CSS rule)
- WCAG contrast ratios documented and verified for all colors
- `prefers-reduced-motion` respected (kills all animations)
- `role="alert"` on error messages
- `role="status"` on status banners
- `role="contentinfo"` on footer
- `aria-label` on hamburger menu button
- `data-testid` attributes for E2E testing
- Keyboard sensor for DnD (@dnd-kit)

**Issues found:**

1. **Missing aria-labels on icon-only buttons:** Sidebar collapse button has no label. Some filter toggle buttons lack labels.
2. **SVG icons lack `aria-hidden="true"`:** The 75+ inline SVGs in `Sidebar.tsx` are announced by screen readers without meaningful context.
3. **Form labels:** Some inputs use `<label htmlFor>` correctly (save search dialog), but others rely on placeholder text only (onboarding CNAE input).
4. **Live regions:** `role="alert"` is used on some errors but missing on toast notifications (Sonner handles this internally).
5. **Color-only information:** Viability scores use color gradients (green-to-red) without text alternatives. Pipeline deadline proximity uses red borders without text explanation.
6. **No heading hierarchy audit:** Multiple pages start with `<h3>` without `<h1>` or `<h2>` parents.

---

## 8. Performance

### 8.1 Bundle Size Concerns

**Heavy dependencies:**
- `framer-motion` (~30KB gzipped) -- used across many pages
- `recharts` (~50KB gzipped) -- only used on dashboard
- `shepherd.js` (~25KB gzipped) -- only used on buscar/pipeline
- `@dnd-kit` suite (~15KB gzipped) -- only used on pipeline
- `react-day-picker` (~10KB gzipped) -- only used on date inputs
- `mixpanel-browser` (~15KB gzipped) -- loaded globally

**Issue:** No dynamic imports for heavy page-specific dependencies. Recharts, Shepherd.js, and @dnd-kit are imported at module level, likely included in the main bundle or page chunks without explicit `next/dynamic` splitting. Exception: `TotpVerificationScreen` correctly uses `next/dynamic` with `ssr: false`.

### 8.2 Rendering Patterns (SSR, CSR)

- **All pages are CSR** (`"use client"`) except the landing page (`/`)
- The landing page is the only Server Component -- it imports client components but itself is server-rendered
- Blog pages and SEO pages could benefit from SSG/ISR but are currently CSR
- `output: 'standalone'` with custom `generateBuildId` for cache-busting

**Issue:** Blog and programmatic SEO pages (`/blog/*`, `/licitacoes/*`, `/como-*`) are `"use client"` despite being mostly static content. These should be Server Components or statically generated for SEO and performance.

### 8.3 Image Optimization

- `next/image` `remotePatterns` configured for `static.wixstatic.com` only
- No other image optimization configuration found
- OG image via `/api/og` route
- No explicit image lazy loading beyond Next.js defaults

### 8.4 Code Splitting

- Standalone output with webpack
- Sentry `widenClientFileUpload` + `hideSourceMaps` + `bundleSizeOptimizations`
- `next/dynamic` used sparingly (only `TotpVerificationScreen`)
- Route-based splitting is automatic via Next.js app router
- No explicit `React.lazy` usage found

---

## 9. Testing

### 9.1 Unit Test Coverage

**128 test files** in `frontend/__tests__/` with subcategories:

| Category | Files | Focus |
|----------|-------|-------|
| Root | ~55 | Feature-specific tests (accessibility, billing, auth, crit, copy) |
| `buscar/` | 13 | Search components, error handling, state management |
| `components/` | 40 | Shared component tests |
| `api/` | 12 | API route handler tests |
| `auth/` | ~5 | Auth flow tests |
| `billing/` | ~5 | Billing component tests |
| `admin/` | ~3 | Admin page tests |
| `account/` | ~3 | Account page tests |
| `alerts/` | ~2 | Alert component tests |

**Baseline: 2,681 passing, 0 failures**

**Test infrastructure:**
- Jest 29 with @swc/jest transformer
- @testing-library/react + @testing-library/user-event
- jest-environment-jsdom
- Polyfills: `crypto.randomUUID`, `EventSource` (jsdom lacks both)
- Quarantine directory for flaky tests

### 9.2 E2E Test Coverage

**22 E2E test files** in `frontend/e2e-tests/`:

| Test File | Coverage |
|-----------|---------|
| `search-flow.spec.ts` | Core search flow |
| `auth-ux.spec.ts` | Login/signup/logout |
| `landing-page.spec.ts` | Landing page rendering |
| `plan-display.spec.ts` | Pricing page |
| `saved-searches.spec.ts` | Search persistence |
| `admin-users.spec.ts` | Admin user management |
| `dialog-accessibility.spec.ts` | Dialog WCAG compliance |
| `error-handling.spec.ts` | Error scenarios |
| `failure-scenarios.spec.ts` | Backend failure simulation |
| `empty-state.spec.ts` | Zero results handling |
| `performance.spec.ts` | Core Web Vitals |
| `signup-consent.spec.ts` | Signup flow |
| `institutional-pages.spec.ts` | Static pages |
| `mkt-*` | SEO/marketing validation |

**Infrastructure:** Playwright 1.58.2, @axe-core/playwright for accessibility checks.

### 9.3 Testing Gaps

1. **No hook unit tests:** Custom hooks (`usePlan`, `useSearch`, `useSearchSSE`, `usePipeline`, `useAnalytics`, etc.) are tested indirectly through component tests but lack isolated hook tests
2. **No snapshot tests for visual regression:** No visual comparison testing
3. **Missing E2E for pipeline DnD:** Drag-and-drop kanban flow not covered
4. **Missing E2E for onboarding wizard:** 3-step wizard flow not covered
5. **Missing E2E for dark mode:** No dark mode rendering tests
6. **No performance budget tests:** Lighthouse CI configured (`@lhci/cli`) but not integrated into CI pipeline
7. **No accessibility CI gate:** axe-core available in E2E but no automated WCAG compliance checks in CI

---

## 10. Technical Debt Identified

### 10.1 Component Architecture Issues

| Issue | Severity | Location | Impact |
|-------|----------|----------|--------|
| **Mega-component: SearchResults.tsx** (1,581 lines) | High | `buscar/components/SearchResults.tsx` | Extremely difficult to maintain, test, and review. Should be split into ResultCard, ResultsList, ResultsToolbar, ResultsHeader, etc. |
| **Mega-component: conta/page.tsx** (1,420 lines) | High | `app/conta/page.tsx` | Mixes profile editing, password change, plan management, MFA setup, and cancellation in one file. Should be split into sub-pages or tabbed components. |
| **Mega-hook: useSearch.ts** (1,510 lines) | High | `buscar/hooks/useSearch.ts` | Single hook manages search execution, SSE, retry, error handling, save, download, Excel, partial results, polling. Should be decomposed. |
| **Mega-component: buscar/page.tsx** (1,019 lines) | Medium | `app/buscar/page.tsx` | Page component handles too many concerns (tours, trials, auto-search, keyboard shortcuts, queuing). |
| **Three component directories** | Medium | `app/components/`, `components/`, `buscar/components/` | No clear convention. Duplicate component names (`EmptyState`, `LoadingProgress`). |
| **No shared Button component** | Medium | Everywhere | Every page re-implements button styles. ~15 different button style patterns found. |
| **Inline SVG icons in Sidebar** | Low | `components/Sidebar.tsx` | 75 lines of SVGs instead of using lucide-react (already a dependency). |

### 10.2 State Management Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| **No data fetching library** | High | Manual `useState` + `useEffect` + `fetch` patterns everywhere. No deduplication, no request caching, no automatic revalidation. SWR or TanStack Query would eliminate ~500 lines of boilerplate. |
| **13+ localStorage keys** without abstraction | Medium | Direct `localStorage.getItem/setItem` calls scattered across 20+ files. No centralized storage layer, no migration strategy, no quota awareness. |
| **Prop drilling on SearchResults** | High | `SearchResults` receives 50+ props from `buscar/page.tsx`. This is a clear signal for context or state composition. |
| **Ref-based circular dependency workaround** | Medium | `clearResultRef` in buscar/page.tsx breaks circular dependency between `useSearchFilters` and `useSearch`. Indicates coupling. |

### 10.3 Accessibility Gaps

| Issue | WCAG Criterion | Severity |
|-------|---------------|----------|
| Missing aria-labels on icon-only sidebar buttons | 1.1.1 Non-text Content | High |
| SVG icons not marked `aria-hidden` | 1.1.1 | Medium |
| Color-only viability score communication | 1.4.1 Use of Color | Medium |
| Missing form labels on some inputs (placeholders only) | 1.3.1 Info and Relationships | Medium |
| No heading hierarchy audit | 1.3.1 | Low |
| No ARIA live regions for dynamic search progress updates | 4.1.3 Status Messages | Medium |

### 10.4 Performance Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| Blog/SEO pages are CSR instead of SSG/ISR | High | SEO pages rendered client-side defeat the purpose. Should be statically generated. |
| No dynamic imports for heavy dependencies | Medium | Recharts (~50KB), Shepherd.js (~25KB), @dnd-kit (~15KB) loaded on pages that use them but not split from main bundle. |
| `useIsMobile()` causes hydration mismatch risk | Low | JS-based check runs after hydration, may cause layout shift. |
| No Lighthouse CI in pipeline | Medium | `@lhci/cli` configured but not gated in CI. Performance regressions can ship undetected. |

### 10.5 Code Quality Issues

| Issue | Severity | Location |
|-------|----------|----------|
| `// eslint-disable-next-line react-hooks/exhaustive-deps` in 3+ locations | Medium | buscar/page.tsx, useSearch.ts |
| Hardcoded Portuguese strings everywhere | High | All 44 pages. No i18n abstraction. Adding English or Spanish support would require touching every file. |
| `APP_NAME` constant redeclared in 5+ files | Low | login, signup, buscar, dashboard, historico |
| Mixed import patterns for constants | Low | Some files import from `lib/constants/`, others redeclare `ALL_UFS` inline (conta, historico) |
| No strict TypeScript paths configured | Low | Relative imports like `../../../hooks/` go 3+ levels deep |

### 10.6 Missing Design System

| Gap | Impact |
|-----|--------|
| **No shared Button component** | 15+ button style variants implemented inline across pages |
| **No shared Input component** | Each form builds its own input styling |
| **No shared Card component** | Card patterns (border, shadow, padding) vary across pages |
| **No shared Badge component** | Multiple badge implementations (status, plan, viability, LLM) |
| **No component library/storybook** | No visual documentation of available components |
| **Design tokens partially adopted** | CSS variables defined but not all components use Tailwind tokens consistently. Mix of `var(--brand-blue)` and `text-brand-blue` and raw hex values |

### 10.7 Responsive Design Gaps

| Gap | Severity |
|-----|----------|
| Dashboard charts (Recharts) have no mobile-specific layout | Medium |
| Admin pages have no mobile optimization | Low (admin-only) |
| Alert creation form not tested at mobile breakpoints | Medium |
| No tablet-specific breakpoint considerations | Low |

### 10.8 UX Inconsistencies

| Issue | Location |
|-------|----------|
| Search page has its own header + footer, while other protected pages use NavigationShell sidebar | buscar/page.tsx vs NavigationShell |
| Two different empty state patterns: `EmptyState` component vs inline empty state JSX | Multiple pages |
| Toast notifications use `sonner` but some errors show inline banners instead | Inconsistent error display |
| Loading spinner size/style varies: `h-8 w-8`, `h-6 w-6`, `w-5 h-5` with different border styles | Multiple pages |
| Date formatting: Some use `date-fns`, some use `Intl.DateTimeFormat`, some use `toLocaleDateString` | dashboard, historico, pipeline |
| Currency formatting: `formatCurrencyBR` utility exists but some pages format currency inline | dashboard vs historico |

---

## Appendix: File Counts Summary

| Category | Count |
|----------|-------|
| Page files (`page.tsx`) | 44 |
| App components (`app/components/`) | 66 |
| Root components (`components/`) | 43 |
| Search components (`buscar/components/`) | 29 |
| Custom hooks | 19 (16 root + 3 buscar-specific) |
| API proxy routes | 57 |
| Lib/utils modules | 31 |
| Unit test files | 128 |
| E2E test files | 22 |
| Total frontend TypeScript files | ~400+ |
