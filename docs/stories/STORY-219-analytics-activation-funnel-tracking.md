# STORY-219: Analytics Activation — Mixpanel Config + Identity Linking + Revenue Funnel

**Status:** Pending
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

- [ ] AC1: Create Mixpanel project (production + development environments)
- [ ] AC2: Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in Railway production env vars
- [ ] AC3: Set `NEXT_PUBLIC_MIXPANEL_TOKEN` in `.env.local` for development
- [ ] AC4: Document variable in `.env.example` with description
- [ ] AC5: Enable `NEXT_PUBLIC_ENABLE_ANALYTICS=true` (currently commented out in `.env.local`)
- [ ] AC6: Verify events appear in Mixpanel dashboard after deployment

### Track 2: Link User Identity (1 day)

- [ ] AC7: Call `identifyUser(userId)` after successful email login in `login/page.tsx`
- [ ] AC8: Call `identifyUser(userId)` after successful Google OAuth in `auth/callback/page.tsx`
- [ ] AC9: Call `identifyUser(userId)` after successful signup in `signup/page.tsx`
- [ ] AC10: Set Mixpanel user properties: `plan_type`, `company`, `sector`, `signup_date`, `signup_method` (google/email)
- [ ] AC11: Call `mixpanel.reset()` on logout (in `UserMenu.tsx` logout handler)
- [ ] AC12: Respect cookie consent: only call `identifyUser` after analytics consent (depends on STORY-213 AC8)

### Track 3: Revenue Funnel Events (1 day)

- [ ] AC13: Track `signup_attempted` on form submit in `signup/page.tsx` (with method: google/email)
- [ ] AC14: Track `signup_completed` after successful signup (with method)
- [ ] AC15: Track `login_attempted` on form submit in `login/page.tsx` (with method)
- [ ] AC16: Track `login_completed` after successful login (with method)
- [ ] AC17: Track `login_failed` with error category (wrong_creds, not_registered, rate_limited, network)
- [ ] AC18: Track `plan_page_viewed` on `/planos` page mount (with `source` parameter: url, upgrade_modal, menu)
- [ ] AC19: Track `checkout_initiated` in `handleCheckout()` with `plan_id`, `billing_period`, `source`
- [ ] AC20: Track `checkout_completed` on Stripe success redirect callback
- [ ] AC21: Track `checkout_failed` when checkout API returns error
- [ ] AC22: Replace `console.log` in `UpgradeModal.tsx:82,89` with `trackEvent("upgrade_modal_opened")` and `trackEvent("upgrade_modal_plan_clicked")`
- [ ] AC23: Track `error_encountered` in `error.tsx` error boundary (with error type, page)

### Track 4: UTM Parameter Capture (0.5 day)

- [ ] AC24: Capture `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` from URL on landing
- [ ] AC25: Store UTM params in `sessionStorage` on first page load
- [ ] AC26: Include UTM params in `signup_completed` event properties
- [ ] AC27: Set UTM params as Mixpanel super properties (persist across session)

### Testing

- [ ] AC28: Test: `identifyUser` called after successful login (mock Mixpanel)
- [ ] AC29: Test: `trackEvent` called with correct properties for checkout events
- [ ] AC30: Test: UTM params captured from URL and included in events

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
| `frontend/hooks/useAnalytics.ts` | Already has `identifyUser()` — just needs to be called |
| `frontend/app/(auth)/login/page.tsx` | Add login tracking + identity link |
| `frontend/app/(auth)/signup/page.tsx` | Add signup tracking + identity link |
| `frontend/app/auth/callback/page.tsx` | Add identity link after Google OAuth |
| `frontend/app/planos/page.tsx` | Add revenue funnel events |
| `frontend/app/components/UpgradeModal.tsx` | Replace console.log with trackEvent |
| `frontend/app/error.tsx` | Add error tracking |
| `frontend/app/components/UserMenu.tsx` | Add mixpanel.reset() on logout |
| `.env.example` | Document MIXPANEL_TOKEN |
