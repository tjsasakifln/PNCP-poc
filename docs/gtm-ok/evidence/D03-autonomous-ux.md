# D03+D07+D08: Autonomous UX Assessment

## Verdict: CONDITIONAL
## Score: D03 (Autonomous UX): 6/10
## Score: D07 (Value Before Payment): 7/10
## Score: D08 (Onboarding Friction): 5/10

---

## First-Time User Journey Map

| Step | Screen | Est. Time | Friction Points | Dead Ends | Evidence |
|------|--------|-----------|-----------------|-----------|----------|
| 1 | Landing Page (`/`) | 0s | None -- clear CTA "Descobrir minhas oportunidades" | None | `page.tsx:18-45` -- 11 sections render sequentially |
| 2 | Signup (`/signup`) | 30-90s | **HIGH**: 8 mandatory fields, forced consent scroll-to-bottom, password policy (8 chars + uppercase + digit), confirm password | None (has "Ja tem conta? Fazer login" + Google OAuth) | `signup/page.tsx:119-133` -- `isFormValid` requires ALL: fullName, company, sector, email, passwordsMatch, isValidPhone, whatsappConsent |
| 3 | Email Confirmation | 0-300s (external) | **CRITICAL DEAD END**: User must leave app to confirm email. No in-app guidance on what to do while waiting. Success screen (L183-200) shows checkmark + "Verifique seu email" + link "Ir para login" -- but no auto-redirect, no timer, no "resend" button | YES: user may close browser, forget, or not find confirmation email | `signup/page.tsx:183-200` |
| 4 | Login (`/login`) | 10-15s | Low -- clean form, Google OAuth, Magic Link option. Translated Supabase errors (L27-58). Already-logged-in detection with auto-redirect. | None | `login/page.tsx:92-476` |
| 5 | Auth Callback (`/auth/callback`) | 1-30s | Medium -- 30s timeout with retry logic (3 retries, exponential backoff). Error state shows "Tentar novamente" button linking to `/login`. | Potential: if callback times out, user sees error screen with only one escape path | `auth/callback/page.tsx:28-32, 242-257` |
| 6 | Protected Layout Check | 0.5-2s | **INVISIBLE FRICTION**: `(protected)/layout.tsx:37-67` checks if user has completed onboarding. Makes API call to `/api/profile-context`. If `res.completed === false`, redirects to `/onboarding`. But: a) 10s auth timeout before any check (L57-73 of AuthProvider); b) profile-context API failure silently falls through (L65-67: `catch(() => {})`) | None -- graceful degradation on error | `(protected)/layout.tsx:36-67` |
| 7 | Onboarding Wizard (`/onboarding`) | 45-120s | **HIGH FRICTION**: 3-step wizard, but Step 1 requires BOTH CNAE and objective text (mandatory). Step 2 requires selecting at least 1 UF and validates value range. Step 3 is confirmation. "Pular por agora" skip option available on all steps. | None -- skip option on every step | `onboarding/page.tsx:508-511, 586-588, 646-660` |
| 8 | First Search (auto) | 15-30s | **LOW if onboarding completed**: Auto-search fires via `/buscar?auto=true&search_id=xxx` (L578-579). OnboardingBanner shows with spinner. If 0 results, OnboardingEmptyState shows with suggestions. | None | `buscar/page.tsx:174-177, 374-394` |
| 8b | First Search (skip) | 30-60s | **MEDIUM if skipped**: User lands on `/buscar` with no pre-selected filters. Must pick a sector, then search. UF defaults are empty (all 27 selected via default). Date is auto-set. Search button is prominent. | None -- clear search form | `buscar/page.tsx:359-372` |
| 9 | Results Display | 0s | **LOW**: Executive summary card, recommendations, licitacoes preview, download button. Clear value delivery. | None | `SearchResults.tsx:467-558` |
| 10 | Download Excel | 2-5s | Low -- prominent button, loading state, error state. Trial users get Excel access (quota.py:65). | None | `SearchResults.tsx:588-629` |

### Total Estimated Time: Landing to First Value

**Best case (Google OAuth + skip onboarding):** ~45 seconds
- Landing -> Signup via Google (5s) -> Auto-redirect to /buscar (5s) -> First search (15-20s) -> Results visible

**Typical case (email signup + onboarding):** ~3-5 minutes
- Landing (10s) -> Signup form (60-90s) -> Email confirmation (60-300s!!) -> Login (15s) -> Onboarding (60-120s) -> First auto-search (15s) -> Results

**Worst case (email signup + slow email + onboarding):** 5-10+ minutes

### VERDICT on "Under 2 Minutes Without Tutorial"
**FAIL** for email signup path due to email confirmation requirement. Email confirmation is an external dependency that can take 30 seconds to 5+ minutes. Google OAuth path can achieve ~45s.

---

## Value Delivery Timeline

### What does the trial include?
- **3 complete analyses** per month (`quota.py:67` -- `max_requests_per_month: 3`)
- **Full product access**: Excel export, pipeline, AI analysis with 10,000 tokens, 1 year history (`quota.py:63-70`)
- **7-day duration** (confirmed by `signup/page.tsx:215` -- "Experimente o SmartLic completo por 7 dias")
- **No credit card required** (`InstitutionalSidebar.tsx:157` -- "Sem necessidade de cartao de credito")

### Value-Before-Payment Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Trial searches available before payment | YES (3 searches) | `quota.py:67` |
| User sees tangible results before paywall | YES -- full summary, recommendations, licitacoes preview | `SearchResults.tsx:467-558` |
| "Aha moment" is clear | PARTIAL -- depends on whether search returns results for user's sector. Zero-result scenario is well-handled with suggestions but no immediate value. | `EmptyState.tsx:53-141`, `OnboardingEmptyState` (L82-109) |
| Trial limitations are transparent | YES -- signup page lists "3 analises incluidas" | `signup/page.tsx:218-225` |
| No bait-and-switch | YES -- trial gives full product, not stripped version | `quota.py:63-70` -- all capabilities match smartlic_pro |

### Trial Expiry UX

| Component | Trigger | Behavior | Evidence |
|-----------|---------|----------|----------|
| `TrialCountdown` badge | Days 1-7 of trial, shown in header | Color-coded: green (5-7d), yellow (3-4d), red (1-2d). Links to /planos. Pulse animation at <=2 days. | `TrialCountdown.tsx:17-58` |
| `TrialExpiringBanner` | Day 6 (1 day remaining) | Amber banner with "Seu acesso ao SmartLic expira amanha" + CTA "Continuar tendo vantagem". Dismissable. | `TrialExpiringBanner.tsx:21, 36-84` |
| `TrialConversionScreen` | Trial expired (subscription_status === "expired") | Full-screen overlay showing trial analytics (opportunities found, total value, searches executed). Billing period selector with pricing. CTA goes to /planos. Close button also goes to /planos. Escape key goes to /planos. | `TrialConversionScreen.tsx:32-187`, `buscar/page.tsx:141-170` |

### Critical Gap: No "Soft Wall" Between Trial Expiry and Complete Block
When trial expires, `check_quota` in `quota.py` blocks ALL searches. The user sees the TrialConversionScreen overlay but CANNOT dismiss it to use any remaining functionality. The close button (L49-52) and Escape key (L56-62) both redirect to `/planos`. This is aggressive -- there is no "read-only" mode or "view previous results" fallback. The user goes from full access to complete lockout.

---

## Error Recovery Matrix

### a) Search Returns 0 Results

| Context | What User Sees | Can Recover? | Evidence |
|---------|----------------|--------------|----------|
| Normal search, 0 filtered results, raw > 0 | `EmptyState` with filter breakdown showing WHY results were rejected (keyword mismatch, value range, UF not selected). Actionable suggestions: "Amplie o periodo", "Selecione mais estados", "Ajuste os filtros". Prominent "Ajustar criterios de busca" button scrolls to top. | YES | `EmptyState.tsx:28-141` |
| Normal search, 0 raw results | `EmptyState` with generic "Nenhuma oportunidade encontrada para o periodo e estados selecionados. Tente ampliar a busca." + suggestions. | YES | `EmptyState.tsx:92-95` |
| Auto-search from onboarding, 0 results | `OnboardingEmptyState` with "Nenhuma oportunidade encontrada para seu perfil" + specific suggestions + "Ajustar Filtros" button. | YES | `buscar/page.tsx:82-109` |
| Partial results, all filtered out | `DegradationBanner` (yellow) + `EmptyState` with full filter breakdown. | YES | `SearchResults.tsx:278-294` |

### b) Search Fails (API Error)

| Scenario | What User Sees | Can Recover? | Evidence |
|----------|----------------|--------------|----------|
| Backend returns error | Red error card with translated message + "Tentar novamente" button with 30-second cooldown timer. Loading spinner while retrying. | YES | `SearchResults.tsx:209-236, 139-164` |
| Network error / timeout | Same error display with user-friendly translated message (e.g., "Erro de conexao. Verifique sua internet." from `error-messages.ts`) | YES | `SearchResults.tsx:209-236` |
| All data sources down | `SourcesUnavailable` component with retry button + option to load last cached search. | YES | `SearchResults.tsx:268-275` |

### c) Search Times Out

| Scenario | What User Sees | Can Recover? | Evidence |
|----------|----------------|--------------|----------|
| >15s elapsed with partial data | `PartialResultsPrompt` appears showing "X resultados ja encontrados em Y estados" with "Ver resultados parciais" + "Aguardar" buttons. | YES | `SearchResults.tsx:193-204` |
| Cancel button during search | Cancel button available in `EnhancedLoadingProgress` component. | YES | `SearchResults.tsx:186` |
| SSE timeout fallback | If SSE fails, frontend uses calibrated time-based simulation. `sseAvailable` flag controls display. | YES (graceful) | `buscar/page.tsx:404-405` |

### d) Stripe Checkout Fails

| Scenario | What User Sees | Can Recover? | Evidence |
|----------|----------------|--------------|----------|
| Checkout API error | Toast error with user-friendly message via `getUserFriendlyError()`. `checkoutLoading` and `stripeRedirecting` reset to false. User stays on /planos. | YES | `planos/page.tsx:176-186` |
| User cancels Stripe checkout | Redirected back to `/planos?cancelled`. Status message "Processo cancelado." shown. | YES | `planos/page.tsx:83` |
| Stripe redirect loading | Full-screen overlay with spinner + "Redirecionando para o checkout" message. Prevents double-clicks. | YES (informational) | `planos/page.tsx:193-199` |

### e) Session Expires

| Scenario | What User Sees | Can Recover? | Evidence |
|----------|----------------|--------------|----------|
| Session expires mid-use | `SessionExpiredBanner` appears as fixed top banner: "Sua sessao expirou. Faca login novamente para continuar." + "Fazer login" button. Login URL includes `redirect` param to return user to current page. Non-dismissable (no close button). | YES | `SessionExpiredBanner.tsx:11-53` |
| Middleware catches expired session | Redirect to `/login?reason=session_expired&redirect=/buscar`. Login page shows "Sua sessao expirou. Faca login novamente." toast. | YES | `middleware.ts:139-141`, `login/page.tsx:117-126` |
| Auth timeout (10s) in AuthProvider | Falls back to `getSession()` (local cookies, no network). If that also fails, `loading` set to false, user sees unauthenticated state. | PARTIAL -- no error shown, user may be confused | `AuthProvider.tsx:57-73` |

---

## Mobile & Accessibility

### Responsive Breakpoints

| Breakpoint | Usage | Evidence |
|------------|-------|----------|
| `sm:` (640px) | Text size scaling, padding adjustments, layout switches | Used extensively throughout all components |
| `md:` (768px) | Login/signup split layout (sidebar + form), footer grid, pull-to-refresh disabled | `login/page.tsx:280`, `globals.css:425-443` |
| `lg:` (1024px) | Hero text scaling, landing page padding | `HeroSection.tsx:68` |
| `max-w-4xl` | Main content area (buscar page) | `buscar/page.tsx:290, 327` |
| `max-w-2xl` | Onboarding wizard card | `onboarding/page.tsx:615` |

### Touch Target Sizes (44x44px minimum)

| Element | Meets 44px? | Evidence |
|---------|-------------|----------|
| UF buttons in SearchForm | YES -- `min-h-[44px]` explicit | `SearchForm.tsx:461` |
| UF buttons in Onboarding StepTwo | NO -- `px-2 py-1 text-xs` (~28px height) | `onboarding/page.tsx:351` |
| Region toggle buttons (Onboarding) | NO -- `text-xs px-2 py-0.5` (~20px height) | `onboarding/page.tsx:336-345` |
| Search button | YES -- `py-3.5 sm:py-4 min-h-[48px] sm:min-h-[52px]` | `SearchForm.tsx:352-356` |
| Login submit button | YES -- `py-3` (~48px) | `login/page.tsx:440` |
| Signup submit button | YES -- `py-3` (~48px) | `signup/page.tsx:552-558` |
| Navigation links (LandingNavbar) | BORDERLINE -- `px-2 py-1` text links (~32px height) | `LandingNavbar.tsx:53-70` -- hidden on mobile anyway (`hidden md:flex`) |
| Save search button | YES -- `py-2.5 sm:py-3` (~44px) | `SearchForm.tsx:380-381` |
| CNAE suggestion items | BORDERLINE -- `px-3 py-2` (~36px) | `onboarding/page.tsx:144-156` |
| Dialog close button | BORDERLINE -- `p-1` with 20px icon (~28px) | `Dialog.tsx:148` |
| TrialConversionScreen close button | YES -- `p-2` with 24px icon (~40px) + positioned at top-right | `TrialConversionScreen.tsx:71-78` |

### Mobile-Specific Issues

1. **Onboarding wizard UF buttons too small for touch** -- `px-2 py-1 text-xs` produces ~28px tall targets on the state selection in Step 2. This is a premium R$1,999/month product; every touch target on mobile must be at least 44x44px.
   - File: `onboarding/page.tsx:351`

2. **InstitutionalSidebar on mobile** -- The login/signup sidebar takes `min-h-screen` on mobile (`min-h-screen md:min-h-0`), meaning users must scroll past a full-screen institutional panel before seeing the form. This doubles the perceived time to start.
   - File: `InstitutionalSidebar.tsx:179`

3. **Landing page navigation hidden on mobile** -- Nav links (Planos, Como Funciona, Suporte) are `hidden md:flex`. No hamburger menu. Mobile users have no way to navigate to these sections from the navbar.
   - File: `LandingNavbar.tsx:52`

4. **Consent scroll box in signup** -- `h-36` (~144px) scroll box with terms text. On small screens this is a significant portion of viewport. The forced scroll-to-bottom pattern is hostile UX.
   - File: `signup/page.tsx:510-519`

### Accessibility Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Skip navigation link | YES -- "Pular para conteudo principal" with focus styling | `layout.tsx:100-107` |
| ARIA roles on dialogs | YES -- `role="dialog"`, `aria-modal="true"`, `aria-labelledby` | `Dialog.tsx:130-132` |
| Focus trap in dialogs | YES -- Tab/Shift+Tab cycling, focus restoration on close | `Dialog.tsx:91-120, 42-61` |
| Escape key closes dialogs | YES -- capture phase listener | `Dialog.tsx:64-77` |
| Error alerts use role="alert" | YES -- consistently applied | `SearchResults.tsx:210`, `SearchForm.tsx:127`, etc. |
| Form labels present | YES -- all inputs have labels | `login/page.tsx:364`, `signup/page.tsx:260-275` |
| aria-pressed on UF toggles | YES | `SearchForm.tsx:460` |
| aria-busy on search button | YES | `SearchForm.tsx:351` |
| Color-only indicators | RISK -- TrialCountdown uses green/yellow/red only. Text label "X dias restantes" mitigates this partially. | `TrialCountdown.tsx:17-40` |
| Loading states announced | YES -- `aria-live="polite"` on loading container | `SearchResults.tsx:180` |
| SVG icons have aria-label/aria-hidden | MOSTLY -- most icons have `aria-hidden="true"` or `role="img" aria-label="..."` | Throughout codebase |
| Keyboard navigation of critical flows | PARTIAL -- Dialog has focus trap. But TrialConversionScreen (z-60 overlay) does NOT have focus trap; it only handles Escape. Tab could escape the overlay into the background. | `TrialConversionScreen.tsx:55-63` -- only Escape, no focus trap |

---

## Critical Gaps

### P0 (Blockers for Autonomous Onboarding)

1. **Email confirmation dead end (signup/page.tsx:183-200)**
   - After email signup, user sees a static screen with "Verifique seu email" and a link to login.
   - No "Resend email" button.
   - No polling/auto-detection of confirmed email.
   - No timer or expectation-setting ("Usually arrives within 1-2 minutes").
   - For a R$1,999/month product, losing users at email confirmation is unacceptable.
   - **Impact**: Estimated 20-40% of email signups may abandon here.

2. **No mobile navigation on landing page (LandingNavbar.tsx:52)**
   - `hidden md:flex` hides all nav links on mobile. No hamburger menu.
   - Mobile users see only the logo and Login/Signup buttons.
   - "Planos", "Como Funciona", "Suporte" are invisible on mobile.
   - **Impact**: Mobile users cannot access key decision-making pages from the landing page.

3. **Onboarding touch targets too small (onboarding/page.tsx:336-358)**
   - UF buttons: `px-2 py-1 text-xs` = ~28px height (should be 44px).
   - Region toggle buttons: `px-2 py-0.5 text-xs` = ~20px height.
   - On a 375px screen, users will struggle to accurately tap Brazilian state abbreviations.

### P1 (Significant Friction)

4. **Signup form is too long (signup/page.tsx:257-561)**
   - 8 fields: Name, Company, Sector, Email, WhatsApp, Password, Confirm Password + consent scroll box.
   - Password policy: 8+ chars, 1 uppercase, 1 digit -- with real-time validation but still adds friction.
   - Consent scroll-to-bottom is a dark pattern that adds ~10-15s.
   - **Recommendation**: Remove WhatsApp requirement from signup (collect later). Remove forced consent scroll. Reduce to 4 fields: Name, Email, Password, Sector.

5. **InstitutionalSidebar takes full screen on mobile (InstitutionalSidebar.tsx:179)**
   - `min-h-screen` means mobile users scroll through an entire screen of marketing copy before reaching the actual login/signup form.
   - This adds 3-5 seconds of scrolling friction on EVERY authentication attempt.
   - **Recommendation**: Hide sidebar on mobile or collapse to a compact header.

6. **Onboarding is mandatory on first login (protected/layout.tsx:61-62)**
   - Even with "Pular por agora" option, the redirect to `/onboarding` adds one navigation hop.
   - The skip lands at `/buscar` without any pre-selected context, making first search harder.
   - CNAE requirement on Step 1 uses jargon ("CNAE") that non-technical business owners may not understand.
   - **Recommendation**: Make the CNAE field optional. Auto-detect sector from company name if possible.

7. **TrialConversionScreen has no focus trap (TrialConversionScreen.tsx)**
   - Full-screen overlay at z-60 with no focus trap. Keyboard users can tab behind it.
   - No `aria-modal="true"` attribute.
   - Close and Escape both redirect to `/planos` rather than dismissing -- no way to access the underlying search page.
   - **Impact**: Trial-expired users have zero access to their previous data or the search interface.

### P2 (Polish Issues)

8. **Accent/diacritics missing in several UI strings**
   - `SessionExpiredBanner.tsx:41`: "Sua sessao expirou. Faca login novamente" -- missing accents on "sessao" and "Faca".
   - `signup/page.tsx:145`: "A senha deve ter pelo menos 8 caracteres, 1 letra maiuscula e 1 numero" -- missing accents.
   - `signup/page.tsx:150`: "As senhas nao coincidem" -- missing accent.
   - `signup/page.tsx:506`: "role ate o final para aceitar" -- missing accents.
   - **Impact**: For a premium Brazilian product, missing Portuguese diacritics signals lack of polish.

9. **Google OAuth callback has excessive console logging in production**
   - `auth/callback/page.tsx:88-89, 131, 147, 152, 167`: Console.log statements leak session info like access token prefix and user email.
   - Guarded by `process.env.NODE_ENV === 'development'` at L70/L133 but not for all log lines (L88, 131, 147 are unguarded).

10. **AuthProvider 10-second timeout is aggressive**
    - `AuthProvider.tsx:57`: 10s timeout on initial auth check means on slow 3G connections, users may see a loading spinner for 10 full seconds before being able to interact.

11. **No "remember me" or persistent session indication**
    - No visible indicator of session duration or auto-logout timing.
    - Users discover session expiry only when it happens.

---

## Summary Scores Breakdown

### D03 (Autonomous UX): 6/10

| Factor | Score | Notes |
|--------|-------|-------|
| Self-explanatory flows | 7/10 | Generally clear CTAs, good copy. CNAE jargon is an issue. |
| No dead ends | 5/10 | Email confirmation is a dead end. Trial expiry is a hard wall. |
| Loading states | 9/10 | Excellent -- spinners, skeletons, progress bars everywhere. |
| Error states | 8/10 | Comprehensive error handling with user-friendly Portuguese translations. |
| Back navigation | 7/10 | Onboarding has back/skip. But TrialConversionScreen traps you. |
| No tutorial needed | 5/10 | Onboarding wizard is a tutorial. Search form is intuitive but "Personalizar busca" accordion hides important controls. |

### D07 (Value Before Payment): 7/10

| Factor | Score | Notes |
|--------|-------|-------|
| Trial generosity | 8/10 | Full product for 7 days, 3 searches. No credit card. |
| Aha moment clarity | 6/10 | Depends on whether PNCP has results for user's sector. Empty state is handled but no guaranteed value. |
| Paywall transparency | 8/10 | Clear "3 analises incluidas" on signup. Countdown badge. Expiry banner. |
| Post-trial grace | 4/10 | No grace. Hard wall at expiry. No read-only mode. |
| Upgrade path smoothness | 8/10 | TrialConversionScreen shows what they discovered. Pricing cards. Direct Stripe checkout. |

### D08 (Onboarding Friction): 5/10

| Factor | Score | Notes |
|--------|-------|-------|
| Steps to first value | 4/10 | Email path: 6+ steps, 3-5 minutes. Google path: 3 steps, 45s. |
| Form field count | 3/10 | 8 mandatory fields at signup is excessive for a SaaS trial. |
| Mandatory vs optional | 5/10 | Onboarding has skip option. But signup has no optional fields. |
| Mobile friction | 4/10 | Sidebar scroll, small touch targets, no hamburger menu. |
| Progressive disclosure | 7/10 | Search form uses accordion for advanced filters. Onboarding uses steps. |
| Time to value (measured) | 5/10 | Google OAuth: ~45s (PASS). Email: ~3-5min (FAIL for 2-min target). |

---

## Recommendations (Priority Order)

1. **Add Google OAuth prominence** -- Make Google signup the primary CTA on signup page. Move email form below/into accordion. This is the only path that can achieve <2 min time-to-value.

2. **Add email resend + auto-detect** -- After email signup, show a countdown, "Resend email" button, and poll for confirmation status.

3. **Add mobile hamburger menu** -- Replace `hidden md:flex` with a responsive hamburger navigation.

4. **Fix onboarding touch targets** -- Increase UF buttons to `min-h-[44px]` in onboarding wizard.

5. **Reduce signup fields** -- Move WhatsApp and consent to post-signup profile completion. Minimum viable signup: Name, Email, Password.

6. **Add trial grace period** -- When trial expires, allow read-only access to previous search results for 3 days.

7. **Add focus trap to TrialConversionScreen** -- Use Dialog pattern with `aria-modal="true"` and Tab cycling.

8. **Fix Portuguese diacritics** -- Audit all user-facing strings for missing accents.

9. **Hide InstitutionalSidebar on mobile** -- Or collapse to a compact trust-badge header.

10. **Make CNAE optional in onboarding** -- Accept text-only description without CNAE code requirement.
