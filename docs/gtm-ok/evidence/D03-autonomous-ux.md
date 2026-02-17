# D03+D07+D08: Autonomous UX Assessment (Phase 3 Fresh Audit)

**Audit Date:** 2026-02-17
**Auditor:** @ux-design-expert (GTM-OK v2.0 Phase 3)
**Method:** Full codebase review of every screen in the first-time user journey

---

## SCORES

| Dimension | Score | Verdict |
|-----------|-------|---------|
| **D03 - Autonomous UX** | **6/10** | CONDITIONAL |
| **D07 - Value Before Payment** | **7/10** | Production-ready (minor issues) |
| **D08 - Onboarding Friction** | **5/10** | CONDITIONAL (significant gaps) |

---

## 1. First-Time User Journey Map

### Complete Flow: Landing -> Perceived Value

| # | Screen | Route | Est. Time | Obvious Next Action? | Loading State? | Error State? | Can Go Back? |
|---|--------|-------|-----------|---------------------|---------------|-------------|-------------|
| 1 | Landing Page | `/` | 0s | YES - Primary CTA "Descobrir minhas oportunidades" in hero, secondary "Como funciona" | N/A (static) | N/A | N/A |
| 2 | Signup | `/signup` | 60-120s | YES - Form with "Criar conta" submit + Google OAuth | YES - "Criando conta..." spinner on submit button | YES - `getUserFriendlyError()` + inline error banner | YES - "Ja tem conta? Fazer login" link |
| 3 | Email Confirmation | (same page, success state) | 0-300s | PARTIAL - "Aguardando confirmacao..." poll indicator + resend button with 60s countdown | YES - polling indicator | YES - spam helper section with tips | YES - "Alterar email" button + "Ir para login" link |
| 4 | Login | `/login` | 10-15s | YES - form submit, Google OAuth, Magic Link toggle | YES - "Entrando..." spinner + "Verificando autenticacao..." on auth check | YES - translated Supabase errors (12 mappings), focus-visible error banners | YES - "Ver planos disponiveis" + "Nao tem conta? Criar conta" |
| 5 | Onboarding Wizard | `/onboarding` | 45-120s | YES - "Continuar" button per step, progress bar "1 de 3" | YES - auth loading spinner | YES - toast errors on API failure | YES - "Voltar" on steps 2-3, "Pular por agora" on all steps |
| 6 | Search Page | `/buscar` | 0s (initial), 15-120s (search) | YES - search button "Buscar [sectorName]" is prominent | YES - 5-stage progress + skeleton + UF progress grid + cancel button | YES - error banner with retry (30s cooldown) + quota exceeded with upgrade CTA | YES - header has logo link to `/` |
| 7 | Results | `/buscar` (same page) | 0s after search | YES - "Baixar Excel" primary CTA, save search, sort results | N/A (already loaded) | YES - download error banner | YES - can modify filters and re-search |

### Total Time to Perceived Value

**Best case (Google OAuth):** ~90s
- Landing (3s) -> Click "Criar conta" (1s) -> Google OAuth (5s) -> Onboarding skip (3s) -> Search page (1s) -> Select sector + "Buscar" (5s) -> Wait for results (15-30s) -> **See results with AI summary**

**Best case (email):** ~180-300s
- Landing -> Signup form (60-90s with 8 fields) -> Email confirmation (30-300s external) -> Login (10s) -> Onboarding (45-120s or skip) -> First search (20-60s)

**Verdict: The 2-minute target is achievable only via Google OAuth with onboarding skip. Email signup flow is 3-5 minutes minimum due to email confirmation and form length.**

---

## 2. Detailed Step Analysis

### Step 1: Landing Page (`/page.tsx`)

**STRENGTHS:**
- Clean section hierarchy: Hero -> ValueProp -> OpportunityCost -> BeforeAfter -> ComparisonTable -> DifferentialsGrid -> HowItWorks -> Stats -> DataSources -> SectorsGrid -> AnalysisExamples -> FinalCTA
- Primary CTA uses `GradientButton` with glow effect - visually prominent
- Counter animations on stats badges (15 sectors, 1000+ rules, 27 states)
- `<a href="#main-content">` skip-to-content link for accessibility (WCAG 2.4.1)
- `lang="pt-BR"` on html tag
- Sticky navbar with scroll detection (`isScrolled` opacity transition)

**WEAKNESSES:**
- 11 sections is a lot of content before the final CTA. Users may not scroll that far.
- The primary CTA "Descobrir minhas oportunidades" navigates to `/signup?source=landing-cta`. This means the user must create an account before seeing ANY value. No preview mode, no sample results, no guest access.
- Secondary CTA "Como funciona" scrolls to `#como-funciona` which may not exist if the section id is different (HowItWorks component must set this id)

**COPY QUALITY:**
- Headline: "Saiba Onde Investir para Ganhar Mais Licitacoes" - clear, benefit-focused
- Subhead: "Inteligencia que avalia oportunidades, prioriza o que importa e guia suas decisoes" - clear value proposition

### Step 2: Signup (`/signup/page.tsx`)

**STRENGTHS:**
- Google OAuth as first option (reduces form friction)
- "OU" divider between Google and email form is standard pattern
- InstitutionalSidebar provides social proof during signup
- Password policy with real-time feedback (checkmark/cross per rule)
- Phone masking for Brazilian format `(XX) XXXXX-XXXX`
- Sector dropdown with 16 options + "Outro" freetext
- Clear trial value proposition: "Experimente o SmartLic completo por 7 dias" with feature list

**WEAKNESSES:**
- **8 mandatory fields** for email signup: fullName, company, sector, email, phone, password, confirmPassword, whatsappConsent. This is HEAVY friction.
- **Consent scroll requirement**: User must scroll to bottom of 400-word legal text before checkbox becomes enabled. This is an unusual and frustrating pattern.
- WhatsApp consent is MANDATORY (`isFormValid` requires `whatsappConsent`). Users who do not want promotional WhatsApp messages cannot sign up. This is a conversion killer and possibly LGPD-questionable (consent should be freely given).
- No autocomplete attributes on form fields (missing `autocomplete="name"`, `autocomplete="organization"`, `autocomplete="email"`, `autocomplete="tel"`, `autocomplete="new-password"`)
- Form inputs use `py-3` (12px padding) which provides adequate touch targets, but no explicit `min-h-[44px]` constraint

**FRICTION SCORE:** HIGH (8 fields + consent scroll = ~60-90 seconds minimum)

### Step 3: Email Confirmation (signup success state)

**STRENGTHS:**
- Auto-polling every 5s (`useEffect` interval checking `/api/auth/status`)
- "Aguardando confirmacao..." indicator shows the system is working
- Resend button with 60-second countdown prevents abuse
- Spam helper section with practical tips (check spam, wait 5 minutes, confirm email)
- "Alterar email" button to go back and correct email
- Auto-redirect to `/onboarding` on confirmation detected

**WEAKNESSES:**
- User must leave the app entirely to check email. This is a standard pattern but still a friction point.
- No deep-link guidance (e.g., "Open Gmail" button for Gmail users)
- If user closes browser during this step, they must manually navigate back to `/login`
- Polling interval of 5s creates up to 5s delay between actual confirmation and redirect

### Step 4: Login (`/login/page.tsx`)

**STRENGTHS:**
- Three auth methods: Google OAuth, Email+Password, Magic Link
- Mode toggle between Password and Magic Link is clean
- Error messages translated to Portuguese (12 Supabase error mappings)
- Already-authenticated detection with auto-redirect to `/buscar`
- "Esqueci minha senha" link for password mode
- Suspense boundary with loading fallback
- `?redirect=` parameter support for post-auth routing
- Login attempt/success/failure analytics tracking

**WEAKNESSES:**
- Password mode `minLength={6}` on login but signup requires 8 - inconsistency
- No "remember me" checkbox
- No rate limiting feedback (Supabase handles it, but user sees generic error)

### Step 5: Onboarding Wizard (`/onboarding/page.tsx`)

**STRENGTHS:**
- 3-step progressive disclosure: Business -> Location/Value -> Confirmation
- Progress bar with "X de 3" indicator
- "Pular por agora" (Skip for now) on every step - crucial escape valve
- CNAE autocomplete with 10 suggestions filtered as user types
- Region-based UF selection (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) with "Todos"/"Limpar" shortcuts
- Value range presets (R$ 50k to R$ 5M) as dropdowns
- Value validation (max must be > min)
- Confirmation summary on Step 3 shows all selections
- Auto-analysis with spinner: "Analisando oportunidades... ~15 segundos"
- Graceful degradation: if first-analysis API fails, redirects to `/buscar` with UF presets
- All buttons have `min-h-[44px]` for touch targets
- Existing context re-loading for returning users

**WEAKNESSES:**
- Step 1 requires BOTH CNAE and objective text (`canProceed` checks both `cnae.trim().length > 0` AND `objetivo_principal.trim().length > 0`). For a user who just wants to search, this is unnecessary friction.
- CNAE autocomplete only has 10 hardcoded suggestions. If user's business does not match these, they must type freetext with no validation that it will map to useful results.
- No indication of what the onboarding data will be used for. Users may not understand why they need to provide CNAE/objective.
- The auto-analysis call to `/api/first-analysis` maps CNAE to sector and runs a background search. If the CNAE mapping fails, the user gets redirected to `/buscar` with no pre-selected sector.
- Profile context save (`PUT /api/profile-context`) failure shows generic toast error

### Step 6: Search Page (`/buscar/page.tsx`)

**STRENGTHS:**
- Auth loading state with centered spinner + "Carregando..."
- Search mode toggle: "Setor" (dropdown) vs "Termos Especificos" (tag input)
- Search button is sticky on mobile (`sticky bottom-4`)
- "Personalizar busca" accordion hides advanced filters by default (reduces cognitive load)
- Collapsed state shows summary badge: "Buscando em todo o Brasil / X estados"
- Default is all 27 UFs selected - user gets maximum coverage immediately
- Search button label is dynamic: "Buscar [sectorName]" or "Buscar X termos"
- 5-stage loading progress with percentage bar, stage indicators, elapsed/remaining time
- "Voce sabia?" curiosity cards during loading (engagement while waiting)
- UF progress grid showing per-state status during search
- Cancel button available during search
- Partial results prompt after 15 seconds
- Pull-to-refresh on mobile (`react-simple-pull-to-refresh`)
- Keyboard shortcuts (Ctrl+K search, Ctrl+A select all, Esc clear)
- Navigation guard warns before leaving with unsaved results

**WEAKNESSES:**
- The `/buscar` page requires authentication (the `HomePageContent` component uses `useAuth()` and the page wrapper shows "Carregando..." until auth resolves). No guest/preview mode available.
- Sector selector loads asynchronously with fallback mode. If backend is down, user sees "Usando lista offline de setores" warning.
- The search can take 15-120+ seconds (estimated 15s base + 20s per UF). For 27 UFs, that is ~555 seconds estimated. The loading progress uses asymptotic function capping at 95% - user may feel stuck.
- Term validation warnings use technical language: "muito curto (minimo 4 caracteres)", "stopword"
- Date range validation warns about plan limits but the user hasn't searched yet - premature friction

### Step 7: Results Display (`SearchResults.tsx`)

**STRENGTHS:**
- Executive summary card with AI-generated text, opportunity count, total value
- "Insight Setorial" banner with sector context
- Urgency alerts for time-sensitive opportunities
- Recommendation cards with urgency badges (alta/media/normal)
- Licitacoes preview cards with top 5 results
- "Baixar Excel" primary download CTA with opportunity count
- Google Sheets export as alternative
- Filter summary badges showing active filters
- Cache banner when results come from stale cache, with refresh button
- Truncation warning banner when results were cut short
- Source badges (PNCP, PCP) toggleable for power users
- Timestamp of last update
- Empty state with detailed rejection breakdown (keyword mismatches, value range, UF) and actionable suggestions

**WEAKNESSES:**
- "Assine para exportar" CTA appears when Excel is not available on free plan - but by this point the user has already seen value. The lock icon may feel punitive.
- Download error display is minimal (just text, no retry button)
- Quota counter shows usage but does not clearly show what happens at quota limit

---

## 3. Value Before Payment (D07)

### Trial Access Details

| Feature | Trial Access | Paid Access |
|---------|-------------|-------------|
| Searches | 3 searches in 7 days | 1000/month |
| History | Full (1825 days) | Same |
| Excel export | YES | YES |
| Pipeline | YES | YES |
| AI summaries | YES | YES |

**The trial is generous.** 3 full searches with Excel export and AI summaries in 7 days gives users enough to evaluate the product. The "Aha moment" occurs when the user sees:
1. The executive summary with opportunity count and total value
2. AI-generated recommendations with urgency badges
3. The downloadable Excel with full details

### "Aha Moment" Clarity

The results summary card (`SearchResults.tsx` L480-572) is the primary value delivery:
- Large numbers for opportunity count and total value (visually prominent, `text-3xl sm:text-4xl font-bold`)
- AI narrative in natural language
- Sector insight provides industry context
- Urgency alerts create FOMO
- Recommendation cards with specific actions

**This is well-designed.** The user immediately sees quantified value.

### Trial Conversion Flow

1. **Day 6 banner** (`TrialExpiringBanner.tsx`): "Seu acesso ao SmartLic expira amanha" with "Continuar tendo vantagem" CTA. Dismissible.
2. **Expired trial overlay** (`TrialConversionScreen.tsx`): Full-screen overlay showing value accumulated during trial (opportunities analyzed, total contract value, searches executed). Billing period toggle (monthly/semiannual/annual) with pricing. "Uma unica licitacao ganha pode pagar o sistema por um ano inteiro." anchor message. Close button redirects to `/planos`.
3. **Quota exceeded state** (`SearchResults.tsx` L243-269): Warning banner with "Ver Planos" CTA.

**STRENGTHS:** The conversion screen personalized with trial data is compelling. The anchor message about ROI is effective.
**WEAKNESSES:** The trial expiring banner only shows on day 6 (1 day remaining). No reminders on days 3-5. No email/WhatsApp reminders (despite collecting consent at signup).

---

## 4. Error Recovery UX

### 0 Results -> Empty State

The `EmptyState` component (`EmptyState.tsx`) handles this well:
- Icon + "Nenhuma Oportunidade Relevante Encontrada" heading
- If `rawCount > 0`: Shows filter rejection breakdown with per-reason counts and tips
- If `rawCount === 0`: Generic "Nenhuma oportunidade encontrada" message
- Suggestions panel: "Amplie o periodo", "Selecione mais estados", "Ajuste os filtros"
- "Ajustar criterios de busca" action button scrolls to top

**Score: 8/10** - Clear, actionable, and informative.

### API Error -> Recovery

Error handling in `SearchResults.tsx` L212-239:
- Error banner with message + "Tentar novamente" button
- 30-second cooldown timer prevents spam-clicking retry
- Cooldown display: "Tentar novamente (0:XX)"
- Cooldown resets when error changes

**Score: 7/10** - Good, but the 30-second forced cooldown may feel excessive for transient errors.

### All Sources Down -> SourcesUnavailable

`SourcesUnavailable.tsx`:
- Friendly refresh icon
- "Nossas fontes de dados governamentais estao temporariamente indisponiveis"
- "Isso geralmente se resolve em poucos minutos"
- Retry button with 30-second cooldown
- "Ver ultima busca salva" button (disabled if no saved search)

**Score: 8/10** - Honest, non-technical messaging. Good escape hatch with saved searches.

### Search Timeout -> Cancel

During loading, `onCancel={search.cancelSearch}` is passed to `EnhancedLoadingProgress`. The partial results prompt appears after 15 seconds offering to show what was found so far.

**Score: 7/10** - Cancel is available. Partial results are a good pattern.

### Quota Exceeded -> Upgrade

`quotaError` displays a warning banner with "Escolha um plano para continuar buscando" and "Ver Planos" button.

**Score: 6/10** - Functional but could be more specific about what the quota limit is and when it resets.

### Page-Level Error Boundary

`/buscar/error.tsx` catches unhandled errors:
- Sentry error reporting
- "Erro na busca" heading
- "Seus filtros foram preservados" reassurance
- "Tentar busca novamente" reset button
- "Precisa de ajuda?" support link

**Score: 8/10** - Solid error boundary with user reassurance.

---

## 5. Mobile Responsiveness

### Touch Targets

All interactive elements in the onboarding wizard use `min-h-[44px] min-w-[44px]` - compliant with Apple HIG 44x44pt minimum.

The search form UF buttons use `min-h-[44px]` with appropriate padding.

Mobile menu buttons use `min-h-[44px] min-w-[44px]`.

**Score: 9/10** - Consistently applied across critical interactions.

### CSS Responsive Breakpoints

From `globals.css` and Tailwind usage:
- Base: mobile-first (no prefix)
- `sm:` (640px): Tablet portrait
- `md:` (768px): Tablet landscape
- `lg:` (1024px): Desktop
- `xl:` (1280px): Large desktop

Evidence of responsive patterns:
- Landing navbar: `hidden md:flex` for desktop nav, hamburger on mobile
- Hero: `text-4xl sm:text-5xl lg:text-6xl` fluid typography
- Search form: `grid grid-cols-4 xs:grid-cols-5 sm:grid-cols-7 md:grid-cols-9` UF grid
- Results: `flex flex-col sm:flex-row` for stat badges
- Signup: `flex flex-col md:flex-row` for sidebar + form layout
- Search button: `sticky bottom-4 sm:bottom-auto` for mobile sticky positioning
- Loading stages: `hidden sm:block` for stage labels (icons-only on mobile with detail card below)

**Score: 7/10** - Good responsive patterns throughout. The UF selector in the accordion may be cramped on small screens with 4-column grid.

### Mobile Menu

`MobileMenu.tsx`:
- Slide-in panel from right (280px, max 80vw)
- Backdrop overlay with blur
- Body scroll lock when open
- Escape key to close
- `role="dialog"` + `aria-modal="true"` + `aria-label="Menu de navegacao"`
- Focus-visible rings on all items
- Auth state awareness (shows "Ir para Busca" if logged in, Login/Criar conta if not)

**Score: 8/10** - Well-implemented mobile menu with proper ARIA attributes.

### Pull-to-Refresh

The search page implements `PullToRefresh` from `react-simple-pull-to-refresh` with resistance=3 and custom spinner.

**Score: 7/10** - Good native-feel interaction.

---

## 6. Accessibility

### Skip Navigation

`layout.tsx` L146-152: `<a href="#main-content" className="sr-only focus:not-sr-only ...">Pular para conteudo principal</a>` - WCAG 2.4.1 compliant.

### Keyboard Navigation

- Tab order follows visual order (no `tabindex` manipulation found)
- Focus-visible rings on all buttons and links (`focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-[var(--ring)]`)
- Keyboard shortcuts on search page (Ctrl+K, Ctrl+A, Enter, Esc, /)
- Escape closes mobile menu, trial conversion screen, keyboard help dialog
- `Dialog` component likely manages focus trapping (used for save search and keyboard help)

### ARIA Labels

- Landing hamburger: `aria-label="Abrir menu"` + `aria-expanded`
- Mobile menu: `role="dialog"` + `aria-modal="true"` + `aria-label="Menu de navegacao"`
- Close buttons: `aria-label="Fechar"` / `aria-label="Fechar menu"`
- UF buttons: `aria-pressed={ufsSelecionadas.has(uf)}`
- Search button: `aria-busy={loading}`
- Progress bar: `role="progressbar"` + `aria-valuenow` + `aria-valuemin` + `aria-valuemax`
- Error/warning banners: `role="alert"` consistently applied
- Remove term buttons: `aria-label="Remover termo ${termo}"`
- SVG icons: mix of `aria-hidden="true"` (decorative) and `aria-label` (semantic)
- `aria-expanded` on accordion toggles

### Color Contrast

From `globals.css`:
- `--ink` (#1e2d3b) vs `--canvas` (#ffffff): 12.6:1 (AAA)
- `--ink-secondary` (#3d5975) vs `--canvas`: 5.5:1 (AA)
- `--ink-muted` (#6b7a8a) vs `--canvas`: 5.1:1 (AA) - explicitly documented as bug fix
- `--brand-blue` (#116dff) vs `--canvas`: 4.8:1 (AA)
- `--error` (#dc2626) vs `--canvas`: 5.9:1 (AA)
- Dark mode also documented with contrast ratios

**Score: 8/10** - Systematically documented contrast ratios. All meet WCAG AA minimum. The `--brand-blue` at 4.8:1 barely passes AA for normal text but fails AAA. The `--ink-faint` at 1.9:1 is correctly labeled as "decorative only."

### Screen Reader Considerations

- `lang="pt-BR"` on `<html>` enables correct pronunciation
- `<title>` elements on SVG icons where semantic
- `role="contentinfo"` on footer
- Error messages use `role="alert"` for live announcements
- `aria-live="polite"` on loading state container

**MISSING:**
- No `aria-live` on search results container (new results appear silently)
- No `aria-describedby` linking form fields to their validation errors
- Custom `<select>` components may not be fully accessible (need to verify `CustomSelect`)
- No `aria-current="page"` on active navigation items

### Overall Accessibility Score: 7/10

---

## 7. Critical Issues

### Issue 1: Signup Form Length (HIGH)

**Impact:** Conversion rate
**Description:** 8 mandatory fields + forced consent scroll is excessive for initial signup. Industry standard for SaaS is 3-4 fields (name, email, password). The WhatsApp phone + consent requirement alone adds 20-30 seconds.
**File:** `D:\pncp-poc\frontend\app\signup\page.tsx` L189-196

### Issue 2: No Preview/Guest Mode (HIGH)

**Impact:** Value demonstration
**Description:** Users must create an account and confirm their email before seeing ANY search results. There is no sample data, demo mode, or guest access. The landing page describes value but does not show it.
**File:** All search routes are behind auth guard

### Issue 3: Mandatory WhatsApp Consent (MEDIUM)

**Impact:** Conversion rate + LGPD compliance
**Description:** `isFormValid` requires `whatsappConsent === true`. Under LGPD, consent for promotional communications should be freely given and optional. Making it mandatory may be legally questionable and definitely hurts conversion.
**File:** `D:\pncp-poc\frontend\app\signup\page.tsx` L196

### Issue 4: Long Search Wait Times (MEDIUM)

**Impact:** Perceived performance
**Description:** Search for all 27 UFs is estimated at 555 seconds (over 9 minutes). The progress bar caps at 95% asymptotically, so users will see it stall near the end. While the cancel/partial results feature mitigates this, the base wait time is too long for a first impression.
**File:** `D:\pncp-poc\frontend\app\components\LoadingProgress.tsx` L78-86

### Issue 5: Onboarding Step 1 Requires Both CNAE and Objective (LOW-MEDIUM)

**Impact:** Drop-off rate
**Description:** Step 1 of onboarding requires both a CNAE/segment AND a text objective. Many users will not know their CNAE code, and the autocomplete only has 10 options. The "skip" option mitigates this, but the default path is friction-heavy.
**File:** `D:\pncp-poc\frontend\app\onboarding\page.tsx` L510-512

---

## 8. Positive Observations

1. **Error handling is comprehensive.** Every error state has a recovery action (retry, adjust filters, contact support). No dead ends in the core flow.
2. **Loading states are well-designed.** The 5-stage progress indicator with curiosity cards is engaging and informative. The UF progress grid gives granular feedback.
3. **Empty state is excellent.** Filter rejection breakdown with actionable tips is best-in-class for a search product.
4. **Trial value proposition is clear.** 3 searches with full features gives users genuine evaluation capability.
5. **Mobile implementation is solid.** Touch targets are consistently 44px+, mobile menu is properly implemented with ARIA, pull-to-refresh works.
6. **Accessibility fundamentals are in place.** Skip navigation, ARIA labels, focus rings, color contrast documentation, screen reader considerations.
7. **Graceful degradation throughout.** Sector fallback, cache fallback, partial results, API error recovery - the system degrades gracefully rather than breaking.
8. **Auto-analysis from onboarding** (GTM-004) is a strong pattern. Completing onboarding triggers an automatic first search, reducing time-to-value.
9. **Dark mode support** with documented contrast ratios shows attention to visual quality.
10. **Keyboard shortcuts** for power users (Ctrl+K search, /, Esc) show product maturity.

---

## 9. Score Justification

### D03 - Autonomous UX: 6/10 (CONDITIONAL)

**Why not higher:**
- No guest/preview mode means users must commit (account creation) before seeing any value
- Signup form with 8 fields + consent scroll is not "autonomous" - it requires significant user effort
- Search wait times of 15s-500s+ are a friction point that cannot be eliminated purely by UX
- The onboarding wizard adds another 45-120s before first search

**Why not lower:**
- Every screen has clear next actions
- Error recovery is comprehensive with no dead ends
- Skip options are available in onboarding
- The Google OAuth path significantly reduces signup friction
- After signup, the search flow is intuitive (select sector -> click search -> see results)

### D07 - Value Before Payment: 7/10 (Production-ready)

**Why 7:**
- Trial gives 3 full searches with all features (Excel, AI, pipeline)
- Results summary card with AI narrative is immediate "aha moment"
- Trial conversion screen with personalized data is compelling
- Users CAN evaluate the product fully within the trial period
- The only deduction is that users must create an account first (no anonymous value preview)

### D08 - Onboarding Friction: 5/10 (CONDITIONAL)

**Why 5:**
- Best case (Google OAuth + skip onboarding): ~90s to first search - acceptable
- Typical case (email signup + onboarding): 3-5 minutes - too long
- 8-field signup form is the primary bottleneck
- Mandatory WhatsApp consent blocks users who decline
- Email confirmation is a dead-end exit from the app
- Onboarding wizard adds useful personalization but is friction for impatient users
- The "skip" option is crucial but not prominently featured

---

## 10. Recommendations for Improvement (Not Implemented - For Planning)

1. **Reduce signup to 3 fields** (email, password, name) - collect company/sector/phone during onboarding instead
2. **Make WhatsApp consent optional** - promotional consent should not gate account creation
3. **Add a sample/demo search** visible from the landing page without account creation
4. **Set default search to fewer UFs** (e.g., user's region) to reduce first-search wait time
5. **Add `aria-live="polite"` to results container** so screen readers announce new results
6. **Add form autocomplete attributes** to signup fields for faster completion
7. **Add a day 3-4 trial reminder** (banner or notification) instead of only day 6
8. **Consider email-link signup** (passwordless) as the primary flow to eliminate password friction
