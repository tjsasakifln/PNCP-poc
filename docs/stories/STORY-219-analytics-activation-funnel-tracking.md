# STORY-219: Analytics Activation — Mixpanel Config + Identity Linking + Revenue Funnel

**Status:** In Progress (code complete, AC1-3/5-6 require ops deployment)
**Priority:** P1 — Week 1 Post-Launch
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 3 days
**Source:** AUDIT-FRENTE-6-BUSINESS (GAP-02, GAP-03, GAP-04, GAP-07), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-frontend (dev, analyst)

---

## Context

SmartLic has **20+ analytics events** coded in the frontend, but they produce **zero data** because:
1. `NEXT_PUBLIC_MIXPANEL_TOKEN` is not set in any environment
2. `identifyUser()` is defined but **never called** — all events are anonymous
3. The revenue funnel (signup → checkout → payment) has **zero tracking**
4. `UpgradeModal.tsx` uses `console.log` instead of `trackEvent`

The search workflow is well-instrumented (20 events), but the team cannot answer basic business questions: What is the signup-to-first-search conversion rate? What percentage of free users convert to paid? Where do users drop off in checkout?

## Acceptance Criteria

### Track 1: Activate Mixpanel (0.5 day)

- [ ] AC1: Create Mixpanel project (production + development environments) *(ops — manual)*
- [ ] AC2: Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway production env vars *(ops — manual)*
- [ ] AC3: Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in `.env.local` for development *(ops — manual)*
- [x] AC4: Document variable in `.env.example` with description
- [ ] AC5: Enable `NEXT_PUBLIC_ENABLE_ANALYTICS=true` (currently commented out in `.env.local`) *(ops — manual)*
- [ ] AC6: Verify events appear in Mixpanel dashboard after deployment *(ops — post-deploy)*

### Track 2: Link User Identity (1 day)

- [x] AC7: Call `identifyUser(userId)` after successful email login in `login/page.tsx`
- [x] AC8: Call `identifyUser(userId)` after successful Google OAuth in `auth/callback/page.tsx`
- [x] AC9: Call `identifyUser(userId)` after successful signup in `signup/page.tsx` *(deferred to first login — signup requires email confirmation)*
- [x] AC10: Set Mixpanel user properties: `plan_type`, `company`, `sector`, `signup_date`, `signup_method` (google/email)
- [x] AC11: Call `mixpanel.reset()` on logout (in `UserMenu.tsx` logout handler)
- [x] AC12: Respect cookie consent: only call `identifyUser` after analytics consent (depends on STORY-213 AC8)

### Track 3: Revenue Funnel Events (1 day)

- [x] AC13: Track `signup_attempted` on form submit in `signup/page.tsx` (with method: google/email)
- [x] AC14: Track `signup_completed` after successful signup (with method)
- [x] AC15: Track `login_attempted` on form submit in `login/page.tsx` (with method)
- [x] AC16: Track `login_completed` after successful login (with method)
- [x] AC17: Track `login_failed` with error category (wrong_creds, not_registered, rate_limited, network)
- [x] AC18: Track `plan_page_viewed` on `/planos` page mount (with `source` parameter: url, upgrade_modal, menu)
- [x] AC19: Track `checkout_initiated` in `handleCheckout()` with `plan_id`, `billing_period`, `source`
- [x] AC20: Track `checkout_completed` on Stripe success redirect callback
- [x] AC21: Track `checkout_failed` when checkout API returns error
- [x] AC22: Replace `console.log` in `UpgradeModal.tsx:82,89` with `trackEvent("upgrade_modal_opened")` and `trackEvent("upgrade_modal_plan_clicked")`
- [x] AC23: Track `error_encountered` in `error.tsx` error boundary (with error type, page)

### Track 4: UTM Parameter Capture (0.5 day)

- [x] AC24: Capture `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` from URL on landing
- [x] AC25: Store UTM params in `sessionStorage` on first page load
- [x] AC26: Include UTM params in `signup_completed` event properties
- [x] AC27: Set UTM params as Mixpanel super properties (persist across session)

### Testing

- [x] AC28: Test: `identifyUser` called after successful login (mock Mixpanel)
- [x] AC29: Test: `trackEvent` called with correct properties for checkout events
- [x] AC30: Test: UTM params captured from URL and included in events

## Validation Metric

- 5+ distinct events visible in Mixpanel within 24h of deployment
- 90%+ of tracked events have an identified user_id within 1 week
- Complete funnel visible: Visit → Signup → Login → Search → Plan Page → Checkout → Payment

## Risk Mitigated

- P1: Complete blindness to user behavior
- P1: Cannot measure conversion rates
- P1: Anonymous analytics cannot drive product decisions

## File References

| File | Change |
|------|--------|
| `frontend/hooks/useAnalytics.ts` | Added `resetUser()`, `captureUTMParams()`, `getStoredUTMParams()` |
| `frontend/app/components/AnalyticsProvider.tsx` | Added UTM capture on init |
| `frontend/app/login/page.tsx` | Added identifyUser, login_attempted/completed/failed tracking |
| `frontend/app/signup/page.tsx` | Added signup_attempted/completed tracking with UTM |
| `frontend/app/auth/callback/page.tsx` | Added identifyUser after Google OAuth |
| `frontend/app/planos/page.tsx` | Added plan_page_viewed, checkout_initiated, checkout_failed |
| `frontend/app/planos/obrigado/page.tsx` | Added checkout_completed tracking |
| `frontend/app/components/UpgradeModal.tsx` | Replaced console.log with trackEvent |
| `frontend/app/error.tsx` | Added error_encountered tracking |
| `frontend/app/components/UserMenu.tsx` | Added mixpanel.reset() on logout |
| `.env.example` | Documented MIXPANEL_TOKEN and ENABLE_ANALYTICS |
| `frontend/__tests__/hooks/useAnalytics-story219.test.ts` | 21 tests for AC28-AC30 |
