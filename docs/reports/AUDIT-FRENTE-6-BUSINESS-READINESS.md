# FRENTE 6: Business Readiness & Analytics Audit

**Date:** 2026-02-12
**Auditor:** @analyst (Business Analyst Agent)
**Scope:** Full codebase — frontend/, backend/, supabase/, configuration files
**Product:** SmartLic (formerly BidIQ Uniformes)

---

## Executive Summary

SmartLic has a surprisingly mature analytics foundation for a POC, with Mixpanel instrumented across core search workflows. However, it has **critical gaps that block a responsible GTM launch**: the analytics tool is not configured (no Mixpanel token in production), there is no cookie consent banner (LGPD violation), user identity is never linked to analytics events, and the entire checkout/billing funnel has zero tracking. Without fixing these, the product cannot legally launch in Brazil, and the team will be flying blind on conversion metrics.

**Overall Business Readiness Score: 4.5/10**

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Analytics Instrumentation | 5/10 | 25% | 1.25 |
| Conversion Funnel Measurability | 2/10 | 20% | 0.40 |
| LGPD Compliance | 4/10 | 20% | 0.80 |
| Onboarding Experience | 7/10 | 10% | 0.70 |
| Legal Pages | 8/10 | 5% | 0.40 |
| Error Communication | 8/10 | 5% | 0.40 |
| Email & Notifications | 1/10 | 10% | 0.10 |
| Support Infrastructure | 6/10 | 5% | 0.30 |
| **TOTAL** | | | **4.35/10** |

---

## 1. Analytics Instrumentation Scorecard

### Tool & Configuration Status

| Item | Status | Detail |
|------|--------|--------|
| Analytics Library | Installed | `mixpanel-browser ^2.74.0` in `package.json` |
| AnalyticsProvider | Implemented | `frontend/app/components/AnalyticsProvider.tsx` wraps entire app |
| useAnalytics Hook | Implemented | `frontend/hooks/useAnalytics.ts` with `trackEvent`, `identifyUser`, `trackPageView` |
| Mixpanel Token (dev) | NOT CONFIGURED | `.env.local` has no `NEXT_PUBLIC_MIXPANEL_TOKEN` set |
| Mixpanel Token (prod) | UNKNOWN | Not visible in env files; likely missing from Railway deployment |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | COMMENTED OUT | Line 23 in `.env.local` is `# NEXT_PUBLIC_ENABLE_ANALYTICS=true` |
| Error Monitoring (Sentry/etc.) | NOT INSTALLED | No Sentry, Datadog, LogRocket, or similar found in dependencies |

**Impact:** Even though event calls exist in code, if no Mixpanel token is set, all tracking silently fails. The product is effectively blind to user behavior.

### Event Tracking Coverage

| Event | Tracked? | Location | Quality |
|-------|----------|----------|---------|
| Page Load | YES | `AnalyticsProvider.tsx:32` | Good - includes path, referrer, UA |
| Page Exit | YES | `AnalyticsProvider.tsx:61` | Good - includes session duration |
| Page View (route change) | PARTIAL | `AnalyticsProvider` re-renders on `pathname` but only fires `page_load` | Missing: dedicated page_view per navigation |
| User Signup | NO | `signup/page.tsx` - no trackEvent call | CRITICAL GAP |
| Login Success | NO | `login/page.tsx` - no trackEvent call | CRITICAL GAP |
| Login Failure | NO | `login/page.tsx` - no trackEvent call | CRITICAL GAP |
| User Identity Link | NO | `identifyUser()` defined but NEVER called | CRITICAL GAP - events are anonymous |
| Search Started | YES | `useSearch.ts:224` | Good - includes UFs, sector, mode, dates |
| Search Completed | YES | `useSearch.ts:338` | Good - includes result count, duration, download_id |
| Search Failed | YES | `useSearch.ts:349` | Good - includes error message, search mode |
| Custom Term Search | YES | `useSearch.ts:327` | Good - includes term count, validation status |
| Download Started | YES | `useSearch.ts:368` | Good - includes download_id, has_url |
| Download Completed | YES | `useSearch.ts:410` | Good - includes source, method |
| Saved Search Created | YES | `useSearch.ts:444` | Good - includes name, search mode |
| Search Rerun (History) | YES | `historico/page.tsx:38` | Good |
| Onboarding Completed | YES | `buscar/page.tsx:46` | OK |
| Onboarding Dismissed | YES | `buscar/page.tsx:47` | OK |
| Onboarding Step Change | YES | `buscar/page.tsx:48` | OK |
| Loading Stage Reached | YES | `LoadingProgress.tsx:155` | Good |
| Loading Abandoned | YES | `LoadingProgress.tsx:169` | Good |
| Dashboard Viewed | YES | `dashboard/page.tsx:238` | OK |
| Analytics Exported | YES | `dashboard/page.tsx:288` | OK |
| Pull to Refresh | YES | `useSearch.ts:488` | OK |
| Search State Auto-Restored | YES | `useSearch.ts:503` | OK |
| Search Progress Stage | YES | `buscar/page.tsx:168` | OK |
| URL Params Loaded | YES | `useSearchFilters.ts:229` | OK |
| Plan Upgrade Initiated | NO | `planos/page.tsx` - no trackEvent | CRITICAL GAP |
| Checkout Started | NO | `planos/page.tsx:handleCheckout` - console.log only | CRITICAL GAP |
| Checkout Completed | NO | No callback/success tracking | CRITICAL GAP |
| Checkout Abandoned | NO | No tracking | CRITICAL GAP |
| Payment Failed | NO | `planos/page.tsx:408` uses `alert()` only | CRITICAL GAP |
| Upgrade Modal Opened | PARTIAL | `UpgradeModal.tsx:82` - `console.log` only, not `trackEvent` | Should use analytics |
| Upgrade Modal Plan Click | PARTIAL | `UpgradeModal.tsx:89` - `console.log` only | Should use analytics |
| Feature Flag Usage | NO | No tracking | Low priority |
| Error Encountered by User | NO | Error pages show errors but don't track | MEDIUM GAP |
| Session Duration | YES | `AnalyticsProvider.tsx:59` | Good via beforeunload |

**Summary:** 20 events tracked, 12 critical events missing. The search workflow is well-instrumented but the revenue funnel (signup -> checkout -> payment) has zero coverage.

---

## 2. Conversion Funnel Measurability

| Funnel Step | Measurable? | Gap |
|-------------|-------------|-----|
| Visit -> Landing Page View | PARTIAL | `page_load` fires but user is unidentified. No UTM parameter capture. |
| Landing -> Signup Page | NO | No `page_view` tracking on `/signup` |
| Signup Page -> Signup Submit | NO | No `signup_attempted` event |
| Signup Submit -> Signup Success | NO | No `signup_completed` event with method (Google vs email) |
| Signup -> Email Confirmed | NO | Supabase handles confirmation; no webhook/event |
| First Login -> First Search | NO | Cannot correlate because `identifyUser` is never called |
| Search -> Download | YES | `download_started` + `download_completed` are tracked |
| Free -> Plan Page Visit | NO | No tracking on `/planos` page view |
| Plan Page -> Checkout Click | NO | Only `console.log` in `handleCheckout` |
| Checkout -> Payment Success | NO | Stripe redirect; no success callback tracking |
| Checkout -> Payment Failure | NO | No error tracking |
| Trial -> Paid | NO | No conversion event; could compute server-side from Stripe webhooks |
| Paid -> Churn | NO | No cancellation tracking |
| Paid -> Renewal | NO | Stripe manages, but no internal analytics event |
| Monthly -> Annual Upgrade | NO | No plan upgrade tracking |

**Funnel Health Assessment:** The team CANNOT answer fundamental business questions:
- What is the signup-to-first-search conversion rate?
- What percentage of free users convert to paid?
- Where do users drop off in the checkout flow?
- What is the average time from signup to first payment?
- Which signup source (Google vs email) converts better?

---

## 3. LGPD Compliance Checklist

| Requirement | Status | Gap |
|-------------|--------|-----|
| Privacy Policy Page (`/privacidade`) | PRESENT | Comprehensive, updated 2026-02-07. Covers LGPD Articles 7-10. |
| Terms of Service Page (`/termos`) | PRESENT | Comprehensive, updated 2026-02-07. Brazilian law, Sao Paulo forum. |
| Cookie Consent Banner | NOT PRESENT | **CRITICAL VIOLATION.** Mixpanel initializes on page load without consent. `AnalyticsProvider.tsx` calls `mixpanel.init()` immediately with `persistence: 'localStorage'`. No consent check. |
| Consent Before Analytics Tracking | NOT PRESENT | `AnalyticsProvider` wraps entire app in `layout.tsx:100` and fires `page_load` event before any user interaction or consent collection. |
| Marketing Communication Consent | PRESENT | Signup form has scroll-to-read consent terms with LGPD reference. `whatsapp_consent` + timestamp stored in DB (`007_add_whatsapp_consent.sql`). |
| Data Deletion Request Mechanism | NOT PRESENT | Privacy policy says "entre em contato" but no actual mechanism, button, or API endpoint exists. No `delete_account`, `excluir_conta`, or `anonymize` code found. |
| Data Portability Mechanism | NOT PRESENT | Privacy policy promises data portability (LGPD Art. 18 V) but no export feature exists. |
| DPO (Data Protection Officer) Contact | PARTIAL | Privacy policy mentions DPO but provides no name, email, or direct contact - just "secao de suporte." |
| PII Minimization in Storage | GOOD | DB stores: email, name, company, phone, sector. Reasonable for service operation. |
| PII in Logs | GOOD | `backend/log_sanitizer.py` is comprehensive: masks emails, phones, IPs, tokens, passwords, user IDs. `SanitizedLogAdapter` class wraps standard logger. |
| Data Retention Policy | GOOD | Privacy policy states 24-month inactive account cleanup. `022_retention_cleanup.sql` implements pg_cron jobs for `monthly_quota` (24mo) and `stripe_webhook_events` (90d). |
| Row Level Security | PRESENT | All tables have RLS enabled (`001_profiles_and_sessions.sql:104-107`). Users can only read/write own data. |
| Consent Audit Trail | PRESENT | `whatsapp_consent_at` timestamp recorded (`007_add_whatsapp_consent.sql:13`). |
| International Data Transfer Disclosure | PRESENT | Privacy policy Section 9 discloses US/EU transfers. |
| Minor's Data Protection | PRESENT | Privacy policy Section 10 states service is for adults/businesses. |

**LGPD Verdict:** The legal documents are good, but the technical implementation has a critical gap: **analytics tracking fires before consent.** This is a violation of LGPD Article 7, which requires prior consent for processing personal data for purposes beyond service operation. Mixpanel tracks IP, user agent, and browsing behavior - all considered personal data under LGPD.

---

## 4. Onboarding Assessment

| Element | Status | Quality |
|---------|--------|---------|
| Guided Tour (Shepherd.js) | IMPLEMENTED | `useOnboarding.tsx` - 3-step tour: Welcome, Demo Search, Your Turn |
| Auto-start for new users | YES | Checks `localStorage` flag `bidiq_onboarding_completed` |
| Dismissible | YES | Cancel button + localStorage persistence of dismissed state |
| Restartable | YES | `restartTour()` function available |
| Analytics Integration | YES | `onComplete`, `onDismiss`, `onStepChange` callbacks fire `trackEvent` |
| Value Proposition Communication | YES | Step 1 lists key features: multi-state search, AI summary, Excel reports |
| Clear CTAs | YES | "Comecar", "Fazer Busca Demo", "Entendi, vamos la!" |
| Signup Success Page | YES | Shows confirmation and directs to check email |
| First Search Guidance | YES | Step 3 provides numbered instructions |
| Contextual Tooltips | PRESENT | `ContextualTutorialTooltip.tsx` exists for additional guidance |
| Progressive Disclosure | NO | All features visible at once; no staged feature reveal |
| Empty State Guidance | YES | `EmptyState` component with adjustment suggestions |

**Assessment:** Onboarding is surprisingly good for a POC. The Shepherd.js tour provides a structured introduction. The main gap is no welcome email after signup (relying only on in-app guidance) and no user-specific customization based on declared sector.

**Score: 7/10**

---

## 5. Legal Pages Assessment

| Page | Route | Status | Quality |
|------|-------|--------|---------|
| Privacy Policy | `/privacidade` | PRESENT | 12-section comprehensive policy. LGPD-aware. Lists all data processors (Supabase, Railway, OpenAI, Stripe). Updated 2026-02-07. |
| Terms of Service | `/termos` | PRESENT | 13-section comprehensive terms. Covers plan tiers, rate limits, cancellation/refund, IP, forum (SP). Updated 2026-02-07. |
| Footer Links | Footer component | PRESENT | Links to both `/privacidade` and `/termos`. LGPD Compliant badge displayed. |
| Cross-references | Both pages | PRESENT | ToS links to Privacy Policy (Section 9). Privacy links to ANPD. |
| Signup Consent | `/signup` | PRESENT | Scroll-to-read consent terms box with checkbox. Must scroll to bottom before checking. |

**Discrepancies Found:**
1. Privacy policy Section 7 mentions "Google Analytics (anonimizado)" for analytics cookies, but the actual implementation uses Mixpanel, not Google Analytics.
2. Privacy policy does not mention Mixpanel by name as a data processor.
3. Terms mention "notificacoes por e-mail" as a feature, but no email notification system exists.

**Score: 8/10** (solid foundation, needs accuracy fixes)

---

## 6. Error Communication Assessment

| Scenario | User Message | Quality | File |
|----------|-------------|---------|------|
| Search fails (general) | "Nao foi possivel processar sua busca. Tente novamente em instantes." | Good | `error-messages.ts` |
| Network error | "Erro de conexao. Verifique sua internet." | Good | `error-messages.ts` |
| PNCP timeout | "A busca demorou demais. Tente com menos estados ou um periodo menor." | Excellent - actionable | `error-messages.ts` |
| PNCP unavailable | "O portal PNCP esta temporariamente fora do ar." | Good | `error-messages.ts` |
| Session expired (401) | "Sessao expirada. Faca login novamente." | Good | `error-messages.ts` |
| Rate limited (429) | "Muitas requisicoes. Aguarde um momento e tente novamente." | Good | `error-messages.ts` |
| Quota exceeded | "Limite de X buscas mensais atingido. Renovacao em DD/MM/YYYY ou faca upgrade." | Excellent - actionable + specific | `quota.py:717` |
| Login failure (wrong creds) | "Email ou senha incorretos." | Good | `login/page.tsx:27` |
| Login failure (not registered) | "Este email ainda nao esta cadastrado. Crie sua conta gratuitamente." | Excellent - guides to signup | `login/page.tsx:24` |
| Login failure (rate limited) | "Muitas tentativas. Aguarde alguns minutos." | Good | `login/page.tsx:28` |
| Login failure (network) | "Erro de conexao. Verifique sua internet." | Good | `login/page.tsx:36` |
| Password mismatch (signup) | "As senhas nao coincidem" | Good | `signup/page.tsx:133` |
| Invalid phone (signup) | "Telefone invalido. Use o formato (XX) XXXXX-XXXX" | Good - shows format | `signup/page.tsx:129` |
| Payment error (checkout) | Raw error via `alert()` | POOR - uses `alert()`, not toast | `planos/page.tsx:408` |
| Global unhandled error | "Ops! Algo deu errado. Ocorreu um erro inesperado." with retry button | Good | `error.tsx` |
| Technical jargon filter | Strips TypeError, ReferenceError, stack traces | Excellent | `error-messages.ts:122-134` |
| `[object Object]` prevention | Structured extraction from API responses | Excellent - HOTFIX applied | `error-messages.ts:57-98` |

**Assessment:** Error communication is a strong point. The `getUserFriendlyError()` function in `error-messages.ts` is well-designed: it maps technical errors to Portuguese user-friendly messages, strips URLs and stack traces, and has a maximum length check. The login page has its own Supabase error translation layer. The only weak spot is checkout error handling using `alert()`.

**Score: 8/10**

---

## 7. Email & Notification Assessment

| Capability | Status | Detail |
|-----------|--------|--------|
| Email Service Provider | NOT CONFIGURED | No SendGrid, Resend, Postmark, Mailgun, or SES found in backend dependencies or code. |
| Welcome Email after Signup | NOT IMPLEMENTED | Only Supabase's built-in email confirmation. No custom welcome template. |
| Search Completion Notification | NOT IMPLEMENTED | Results only shown in-app. |
| Payment Confirmation Email | NOT IMPLEMENTED | Stripe sends receipt, but no custom confirmation. |
| Quota Warning Email | NOT IMPLEMENTED | Quota shown in-app via `QuotaCounter`, but no proactive email. |
| Subscription Expiration Warning | NOT IMPLEMENTED | No reminder before expiration. |
| Cancellation Confirmation | NOT IMPLEMENTED | Stripe handles, no custom email. |
| New Opportunities Alert (promised) | NOT IMPLEMENTED | Terms of Service Section 2 promises "notificacoes por e-mail sobre novas oportunidades." Not built. |
| In-App Notifications | PARTIAL | Toast notifications via `sonner` library for immediate feedback (login, errors). No persistent notification center. |
| Message Center | IMPLEMENTED | `frontend/app/mensagens/page.tsx` - conversation-based support messaging with categories (suporte, sugestao, bug, etc.) |

**Assessment:** This is the weakest area. The product promises email notifications in its Terms of Service but has zero email infrastructure. Supabase handles the bare minimum (email confirmation, password recovery). For a paid SaaS, transactional emails are essential for customer lifecycle management.

**Score: 1/10**

---

## 8. Support Infrastructure Assessment

| Element | Status | Detail |
|---------|--------|--------|
| In-App Message Center | IMPLEMENTED | `/mensagens` page with conversation threading, categories (suporte, sugestao, funcionalidade, bug, outro), status tracking (aberto, respondido, resolvido) |
| Backend Messages API | IMPLEMENTED | `backend/routes/messages.py` |
| Help/FAQ Page | NOT PRESENT | No dedicated FAQ or knowledge base |
| Live Chat Widget | NOT PRESENT | No Intercom, Crisp, Zendesk, Freshdesk, or Drift |
| Error Page Support Link | PARTIAL | `error.tsx:60` says "entre em contato com o suporte" but doesn't link to `/mensagens` |
| Footer Support Links | PRESENT | Links to `/mensagens` as "Central de Ajuda" and "Contato" |
| Admin Panel | IMPLEMENTED | `/admin` page for user management |
| Contextual Help | PRESENT | `ContextualTutorialTooltip.tsx` for in-context guidance |
| Contact Email | NOT VISIBLE | No email address published anywhere. Privacy policy just says "secao de suporte." |

**Assessment:** The in-app messaging system is a good foundation. However, there is no FAQ for self-service, no contact email for users who can't log in, and error pages don't link to actual support channels. For a paid product, users expect at least a contact email and some form of self-service documentation.

**Score: 6/10**

---

## CRITICAL GAPS (Block GTM Launch)

### GAP-01: No Cookie Consent Banner (LGPD Violation)

- **Context:** LGPD Article 7 requires prior consent for personal data processing for analytics purposes.
- **Problem:** `AnalyticsProvider.tsx` initializes Mixpanel and fires `page_load` event immediately on every page render, BEFORE any consent is collected. Mixpanel with `persistence: 'localStorage'` stores a distinct_id and device data.
- **Impact:** Legal liability under LGPD. Fines up to 2% of revenue (capped at R$50M per infraction).
- **Evidence:** `frontend/app/layout.tsx:100` - `<AnalyticsProvider>` wraps children unconditionally. `AnalyticsProvider.tsx:25-28` - `mixpanel.init()` called in useEffect without consent check.

### GAP-02: Mixpanel Token Not Configured

- **Context:** The entire analytics system depends on `NEXT_PUBLIC_MIXPANEL_TOKEN` being set.
- **Problem:** `.env.local` has no `NEXT_PUBLIC_MIXPANEL_TOKEN`. The variable is not documented in `.env.example`. Unknown if it is set in Railway production environment.
- **Impact:** All 20+ analytics events silently fail. The team has zero visibility into user behavior.
- **Evidence:** `frontend/.env.local` - token absent. `AnalyticsProvider.tsx:21-23` - conditional on token existence.

### GAP-03: User Identity Never Linked to Events

- **Context:** `useAnalytics.ts` defines `identifyUser()` which calls `mixpanel.identify()`.
- **Problem:** `identifyUser()` is NEVER called anywhere in the application code. All tracked events are anonymous with no user association.
- **Impact:** Cannot correlate behavior across sessions. Cannot build user cohorts. Cannot answer "which users convert?" or segment by plan type.
- **Evidence:** `grep identifyUser frontend/app/` returns zero results.

### GAP-04: Zero Revenue Funnel Tracking

- **Context:** The `/planos` page handles checkout redirection to Stripe.
- **Problem:** No analytics events fire for: plan page view, plan comparison, checkout click, checkout completion, payment success/failure. The `UpgradeModal.tsx` uses `console.log` instead of `trackEvent`.
- **Impact:** Cannot measure conversion rates, cannot identify checkout friction, cannot calculate CAC or LTV.
- **Evidence:** `planos/page.tsx:handleCheckout` - no `trackEvent`. `UpgradeModal.tsx:82,89` - `console.log` only.

### GAP-05: No Data Deletion Mechanism

- **Context:** LGPD Article 18 grants users the right to data deletion.
- **Problem:** No account deletion feature exists. No "delete my data" button, no API endpoint, no admin tool for data deletion requests. The privacy policy instructs users to "contact support" but the support system has no workflow for data deletion.
- **Impact:** LGPD violation. Users cannot exercise their right to data erasure.
- **Evidence:** `grep -ri "delete.*account\|excluir.*conta\|data.*deletion" --include="*.{py,ts,tsx}"` returns zero results.

---

## HIGH GAPS

### GAP-06: No Error Monitoring Service

- **Context:** Production applications need automated error detection and alerting.
- **Problem:** No Sentry, Datadog, LogRocket, Bugsnag, or New Relic installed. Frontend errors are logged to `console.error` only. Backend errors are logged to stdout/stderr.
- **Impact:** The team will not know when production errors occur unless users report them. Silent failures will degrade trust.
- **Evidence:** `grep -ri "sentry\|bugsnag\|datadog\|logrocket\|newrelic" --include="*.{ts,tsx,py,json}"` returns only `package-lock.json` (false positive).

### GAP-07: No Signup/Login Event Tracking

- **Context:** Signup and login are the top-of-funnel conversion events.
- **Problem:** Neither `signup/page.tsx` nor `login/page.tsx` call `trackEvent`. Cannot measure: signup rate by source, Google vs email signup split, login success/failure ratio, time-to-first-login.
- **Impact:** Cannot optimize acquisition funnel.

### GAP-08: No Email Infrastructure

- **Context:** Transactional emails are standard for SaaS products.
- **Problem:** No email service configured. No welcome email, no quota warnings, no payment confirmations, no re-engagement emails. The Terms of Service (Section 2) promises email notifications that don't exist.
- **Impact:** Poor customer lifecycle management. Potential legal issue (promising features that don't exist in ToS). Users forget about the product between sessions.

### GAP-09: Privacy Policy Inaccuracies

- **Context:** Privacy policy must accurately describe data processing.
- **Problem:** Section 7 mentions "Google Analytics (anonimizado)" but the actual tool is Mixpanel. Mixpanel is not listed as a data processor in Section 4.
- **Impact:** Privacy policy doesn't match reality. Could undermine legal defense if challenged.

---

## MEDIUM GAPS

### GAP-10: Checkout Error Uses `alert()`

- **Context:** `planos/page.tsx:408` displays payment errors via `alert()`.
- **Problem:** `alert()` is blocking, not styled, breaks the user experience, and is inconsistent with the rest of the app which uses `sonner` toast notifications.
- **Impact:** Poor UX during a critical conversion moment.

### GAP-11: No FAQ or Knowledge Base

- **Context:** Self-service support reduces burden and improves user satisfaction.
- **Problem:** No `/faq`, `/ajuda`, or help center page exists. The footer links "Central de Ajuda" to `/mensagens` which is a contact form, not self-service.
- **Impact:** Users cannot self-serve common questions. Support burden will scale linearly with user growth.

### GAP-12: Error Page Doesn't Link to Support

- **Context:** `frontend/app/error.tsx` shows when unhandled errors occur.
- **Problem:** Line 60 says "entre em contato com o suporte" but provides no link to `/mensagens` or any contact method.
- **Impact:** Dead-end user experience during errors.

### GAP-13: No UTM Parameter Tracking

- **Context:** Marketing attribution requires capturing UTM parameters.
- **Problem:** No UTM capture (`utm_source`, `utm_medium`, `utm_campaign`) at signup or page view. Cannot attribute signups to marketing channels.
- **Impact:** Cannot measure marketing ROI or optimize acquisition spend.

### GAP-14: No Data Portability Feature

- **Context:** LGPD Article 18 V grants users the right to data portability.
- **Problem:** No "export my data" feature exists. Privacy policy promises this right but provides no mechanism.
- **Impact:** LGPD compliance gap (lower priority than deletion since users can ask via support).

### GAP-15: No Contact Email Published

- **Context:** Users who cannot log in need an alternative contact method.
- **Problem:** No email address is published on the privacy policy, terms, error pages, or footer. All say "contact via platform support" which requires being logged in.
- **Impact:** Users locked out of their account have no way to get help.

---

## Proposed Stories

### STORY-GTM-01: Cookie Consent Banner (CRITICAL - Blocks Launch)

**Context:** LGPD requires informed consent before non-essential data processing. Mixpanel tracking is non-essential.

**Problem:** Analytics tracking fires on every page load without consent. This violates LGPD Article 7.

**Impact:** Legal liability (fines up to R$50M), reputational damage, potential ANPD investigation.

**Acceptance Criteria:**
- [ ] Cookie consent banner appears on first visit (before Mixpanel init)
- [ ] Banner explains: essential cookies (always), analytics cookies (opt-in), marketing cookies (opt-in)
- [ ] User can accept all, reject non-essential, or customize
- [ ] Mixpanel ONLY initializes after analytics consent is granted
- [ ] Consent preference is persisted in localStorage
- [ ] Consent can be changed later (link in footer or settings)
- [ ] Consent state is tracked server-side (LGPD audit trail)
- [ ] Banner links to `/privacidade` for full details

**Validation Metric:** 100% of analytics events fire only after consent. Zero Mixpanel calls without consent.

**Risk Mitigated:** LGPD violation, legal liability.

---

### STORY-GTM-02: Configure and Activate Mixpanel (CRITICAL)

**Context:** 20+ analytics events are coded but produce zero data because no token is configured.

**Problem:** `NEXT_PUBLIC_MIXPANEL_TOKEN` is not set in any environment.

**Impact:** Complete blindness to user behavior. All product decisions are gut-feel only.

**Acceptance Criteria:**
- [ ] Mixpanel project created (production + development environments)
- [ ] `NEXT_PUBLIC_MIXPANEL_TOKEN` set in Railway (production)
- [ ] `NEXT_PUBLIC_MIXPANEL_TOKEN` set in `.env.local` (development)
- [ ] Variable documented in `.env.example`
- [ ] Verify events appear in Mixpanel dashboard
- [ ] Set up Mixpanel data governance (PII redaction rules)
- [ ] Create at least 3 key dashboards: Acquisition, Engagement, Revenue

**Validation Metric:** At minimum 5 distinct events visible in Mixpanel within 24h of deployment.

**Risk Mitigated:** Decision-making without data.

---

### STORY-GTM-03: Link User Identity to Analytics (CRITICAL)

**Context:** `identifyUser()` exists in hook but is never called. All events are anonymous.

**Problem:** Cannot correlate behavior across sessions, cannot build cohorts, cannot segment by plan.

**Impact:** Analytics data is 50% less useful without identity. Cannot answer "who converts?"

**Acceptance Criteria:**
- [ ] Call `identifyUser(userId)` after successful login (email + Google OAuth)
- [ ] Call `identifyUser(userId)` after successful signup
- [ ] Set user properties: `plan_type`, `company`, `sector`, `signup_date`, `signup_method`
- [ ] Call `mixpanel.reset()` on logout
- [ ] Respect LGPD: only identify after analytics consent is granted (depends on STORY-GTM-01)

**Validation Metric:** 90%+ of tracked events have an identified user_id within 1 week.

**Risk Mitigated:** Anonymous analytics that cannot drive product decisions.

---

### STORY-GTM-04: Revenue Funnel Analytics (CRITICAL)

**Context:** The checkout flow has zero analytics instrumentation.

**Problem:** Cannot measure conversion rate from free to paid, checkout abandonment, or payment failures.

**Impact:** Cannot optimize the revenue funnel. Cannot calculate CAC, LTV, or payback period.

**Acceptance Criteria:**
- [ ] Track `plan_page_viewed` on `/planos` page mount (with source param)
- [ ] Track `plan_compared` when user scrolls/interacts with plan cards
- [ ] Track `checkout_initiated` in `handleCheckout()` with plan_id, billing_period, source
- [ ] Track `checkout_redirected` when Stripe URL is opened
- [ ] Track `checkout_completed` on Stripe success redirect callback
- [ ] Track `checkout_failed` when checkout API returns error
- [ ] Track `upgrade_modal_opened` with source (replace `console.log`)
- [ ] Track `upgrade_modal_plan_clicked` with plan_id (replace `console.log`)
- [ ] Add signup tracking: `signup_attempted`, `signup_completed` (with method: google/email)
- [ ] Add login tracking: `login_attempted`, `login_completed`, `login_failed` (with method)

**Validation Metric:** Complete funnel visibility: Visit -> Signup -> Login -> Search -> Plan Page -> Checkout -> Payment.

**Risk Mitigated:** Revenue optimization blindness.

---

### STORY-GTM-05: Data Deletion Mechanism (CRITICAL - LGPD)

**Context:** LGPD Article 18 VI grants users the right to data deletion.

**Problem:** No mechanism exists for users to delete their account or data.

**Impact:** LGPD violation. User trust erosion.

**Acceptance Criteria:**
- [ ] "Delete My Account" button in user profile/settings page
- [ ] Confirmation dialog with clear explanation of what will be deleted
- [ ] Backend endpoint `DELETE /api/me` or `POST /api/me/delete`
- [ ] Deletes: profile, search sessions, subscriptions, messages, oauth tokens
- [ ] Calls Supabase `auth.admin.deleteUser()` to remove auth record
- [ ] Sends confirmation email (if email infra exists) or shows final confirmation page
- [ ] Admin can process deletion requests from message center
- [ ] Audit log entry for compliance (anonymized)

**Validation Metric:** Users can fully delete their account in < 3 clicks.

**Risk Mitigated:** LGPD violation, user trust.

---

### STORY-GTM-06: Error Monitoring (Sentry) (HIGH)

**Context:** Production applications need automated error detection.

**Problem:** No error monitoring service. Errors are invisible unless users report them.

**Impact:** Silent failures degrade trust. Debugging production issues requires log access.

**Acceptance Criteria:**
- [ ] Sentry SDK installed in frontend (`@sentry/nextjs`)
- [ ] Sentry SDK installed in backend (`sentry-sdk[fastapi]`)
- [ ] Source maps uploaded for frontend
- [ ] Error boundary component wraps app
- [ ] Performance tracing enabled for key transactions (search, checkout)
- [ ] Alert rules: email on first occurrence of new error
- [ ] PII scrubbing configured (strip emails, tokens)
- [ ] Environment tagging (production, development)

**Validation Metric:** All production errors auto-reported with stack traces within 10 seconds.

**Risk Mitigated:** Invisible production failures.

---

### STORY-GTM-07: Transactional Email Infrastructure (HIGH)

**Context:** SaaS products need email for customer lifecycle management.

**Problem:** No email service. ToS promises notifications that don't exist.

**Impact:** No welcome emails, no quota warnings, no re-engagement. Users forget about the product.

**Acceptance Criteria:**
- [ ] Email service provider configured (Resend recommended for simplicity)
- [ ] Welcome email template: value prop recap, first search CTA, support link
- [ ] Quota warning email: fires at 80% and 100% usage
- [ ] Payment confirmation email: plan name, amount, next renewal date
- [ ] Subscription expiration warning: 7 days and 1 day before
- [ ] Unsubscribe mechanism in all marketing emails (LGPD + CAN-SPAM)
- [ ] Email templates use responsive HTML
- [ ] Backend email service module with queue/retry logic

**Validation Metric:** Welcome email delivered within 5 minutes of signup, 95%+ delivery rate.

**Risk Mitigated:** Customer churn from disengagement, ToS accuracy.

---

### STORY-GTM-08: Fix Privacy Policy Inaccuracies (HIGH)

**Context:** Privacy policy mentions Google Analytics but system uses Mixpanel.

**Problem:** Legal document doesn't match reality.

**Acceptance Criteria:**
- [ ] Section 7: Replace "Google Analytics (anonimizado)" with "Mixpanel" (or current analytics tool)
- [ ] Section 4: Add Mixpanel as a data processor with description
- [ ] Section 2.2: Update "Dados de Uso" to accurately describe what Mixpanel collects
- [ ] Remove mention of features that don't exist (email notifications if not implemented)
- [ ] Add specific DPO contact email (not just "secao de suporte")
- [ ] Review all sections after email infrastructure is built (if applicable)

**Validation Metric:** Legal review confirms policy matches actual data processing.

**Risk Mitigated:** Legal defense undermined by inaccurate documentation.

---

### STORY-GTM-09: UTM Parameter Capture (MEDIUM)

**Context:** Marketing attribution requires UTM tracking.

**Problem:** No UTM parameters captured at any point.

**Acceptance Criteria:**
- [ ] Capture `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` from URL
- [ ] Store in sessionStorage on landing
- [ ] Include in signup event properties
- [ ] Include in `page_load` event
- [ ] Include as Mixpanel super properties (persist across session)

**Validation Metric:** Attribution data available for 90%+ of signups.

**Risk Mitigated:** Marketing spend without attribution.

---

### STORY-GTM-10: FAQ / Knowledge Base (MEDIUM)

**Context:** Self-service support reduces burden.

**Problem:** No FAQ page. "Central de Ajuda" links to contact form.

**Acceptance Criteria:**
- [ ] `/ajuda` or `/faq` page with searchable Q&A
- [ ] Cover at minimum: How to search, plan differences, payment methods, data sources, account management
- [ ] Link from footer "Central de Ajuda" to FAQ (keep contact link separate)
- [ ] Link from error pages to FAQ
- [ ] Structured data (FAQ schema) for SEO

**Validation Metric:** 30%+ of support queries deflected by FAQ within 2 months.

**Risk Mitigated:** Support scalability.

---

## Priority Matrix

| Priority | Story | Effort | Impact |
|----------|-------|--------|--------|
| P0 - Blocks Launch | GTM-01 (Cookie Consent) | 3-5 days | Legal compliance |
| P0 - Blocks Launch | GTM-02 (Activate Mixpanel) | 0.5 day | Analytics activation |
| P0 - Blocks Launch | GTM-05 (Data Deletion) | 3-5 days | Legal compliance |
| P1 - Week 1 Post-Launch | GTM-03 (Identity Linking) | 1 day | Analytics quality |
| P1 - Week 1 Post-Launch | GTM-04 (Revenue Funnel) | 2-3 days | Revenue optimization |
| P1 - Week 1 Post-Launch | GTM-08 (Privacy Policy Fix) | 0.5 day | Legal accuracy |
| P2 - Month 1 | GTM-06 (Sentry) | 2-3 days | Operational maturity |
| P2 - Month 1 | GTM-07 (Email Infrastructure) | 5-7 days | Customer lifecycle |
| P3 - Month 2 | GTM-09 (UTM Tracking) | 1 day | Marketing attribution |
| P3 - Month 2 | GTM-10 (FAQ Page) | 2-3 days | Support scalability |

**Total Estimated Effort for GTM Readiness (P0 + P1): ~10-15 developer-days**

---

## Positive Observations (Preserve These)

1. **Search analytics are thorough.** The `useSearch.ts` hook tracks the complete search lifecycle with rich metadata (UFs, sector, duration, result count). This is best-in-class instrumentation for a POC.

2. **Error message framework is excellent.** The `getUserFriendlyError()` function with its error map, technical jargon detection, and length checks prevents users from ever seeing raw stack traces.

3. **Log sanitization is production-grade.** The `SanitizedLogAdapter` class with field-aware masking (email, phone, IP, token, password, user ID) is a security best practice rarely seen in POCs.

4. **Consent infrastructure exists for marketing.** The signup flow's scroll-to-read consent terms with `whatsapp_consent_at` timestamp is LGPD-compliant and well-implemented.

5. **RLS is properly configured.** All database tables have Row Level Security enabled with appropriate policies.

6. **Data retention is automated.** pg_cron jobs for cleanup of old quota and webhook data show operational maturity.

7. **Onboarding is thoughtful.** The 3-step Shepherd.js tour with analytics callbacks and persistence is a good user experience.

8. **In-app messaging system provides a support foundation.** Categories, status tracking, and conversation threading are already built.

---

*Report generated by @analyst on 2026-02-12. All findings based on static code analysis of the `D:\pncp-poc` repository at commit `f1d7fdb`.*
