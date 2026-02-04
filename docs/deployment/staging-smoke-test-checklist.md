# Staging Smoke Test Checklist - STORY-165

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Created:** February 4, 2026
**Environment:** Staging
**Feature Flag:** `ENABLE_NEW_PRICING=true`

---

## Pre-Test Setup

- [ ] Staging environment accessible at: `_______________`
- [ ] Feature flag `ENABLE_NEW_PRICING=true` enabled
- [ ] Test users created (see staging-test-data-setup.md)
- [ ] Browser DevTools open for network inspection
- [ ] Screenshot tool ready for evidence collection
- [ ] Test data spreadsheet ready for recording results

---

## Priority P0 - CRITICAL (Must Pass 100%)

These tests MUST pass for production deployment approval.

### P0-1: Authentication & Health Check

**Objective:** Verify basic system availability

- [ ] **Step 1:** Navigate to staging URL
- [ ] **Step 2:** Verify login page loads within 3 seconds
- [ ] **Step 3:** Log in with test user (any plan)
- [ ] **Expected:** Redirect to dashboard, no console errors
- [ ] **Step 4:** Call `GET /api/me`
- [ ] **Expected:** HTTP 200, valid JSON response with user profile
- [ ] **Screenshot:** Save response showing `plan_id`, `capabilities` object

**Pass Criteria:**
- Login succeeds within 5 seconds
- `/api/me` returns all required fields
- No 500 errors in network tab

---

### P0-2: FREE Trial - 7-Day Date Range (Success Case)

**Test User:** FREE trial (3 days remaining)
**Objective:** Verify FREE users can search within allowed range

- [ ] **Step 1:** Log in as FREE trial user
- [ ] **Step 2:** Verify plan badge displays: "FREE Trial" with countdown (e.g., "3 dias restantes")
- [ ] **Expected:** Badge color gray, countdown accurate
- [ ] **Step 3:** Select UF: "SP"
- [ ] **Step 4:** Select date range: Last 7 days
- [ ] **Expected:** No validation error displayed
- [ ] **Step 5:** Click "Buscar"
- [ ] **Step 6:** Wait for results to load
- [ ] **Expected:** HTTP 200, results displayed on screen
- [ ] **Step 7:** Verify Excel button shows lock icon 🔒
- [ ] **Expected:** Button disabled with tooltip
- [ ] **Screenshot:** Save results page showing plan badge, locked Excel button

**Pass Criteria:**
- Search completes successfully
- Results displayed (even if empty)
- Excel button locked
- No 403 errors

---

### P0-3: FREE Trial - 30-Day Date Range (Block Case)

**Test User:** FREE trial (same as P0-2)
**Objective:** Verify date range restriction enforcement

- [ ] **Step 1:** Select date range: Last 30 days
- [ ] **Expected:** Client-side validation error appears BEFORE clicking search
- [ ] **Error Message:** "⚠️ Seu plano permite buscas de até 7 dias. Ajuste as datas ou faça upgrade."
- [ ] **Step 2:** Verify search button is disabled
- [ ] **Expected:** Button grayed out, not clickable
- [ ] **Step 3:** Verify upgrade suggestion displayed
- [ ] **Expected:** CTA points to "Consultor Ágil" plan
- [ ] **Screenshot:** Save error state with disabled button

**Pass Criteria:**
- Validation blocks search BEFORE API call
- User-friendly error message
- Search button disabled until valid range selected

---

### P0-4: Consultor Ágil - Quota Counter Display

**Test User:** Consultor Ágil (23/50 searches used)
**Objective:** Verify quota tracking and display

- [ ] **Step 1:** Log in as Consultor Ágil user
- [ ] **Step 2:** Verify plan badge shows "Consultor Ágil" (blue color)
- [ ] **Expected:** Badge color blue, clickable
- [ ] **Step 3:** Locate quota counter
- [ ] **Expected:** Displays "Buscas este mês: 23/50"
- [ ] **Step 4:** Verify progress bar color is green (<70% used)
- [ ] **Expected:** Green progress bar at 46%
- [ ] **Step 5:** Hover over quota counter
- [ ] **Expected:** Tooltip shows reset date: "Renovação em: 01/03/2026"
- [ ] **Screenshot:** Save quota counter display

**Pass Criteria:**
- Quota counter accurate (23/50)
- Progress bar green
- Reset date visible

---

### P0-5: Consultor Ágil - Excel Export Locked

**Test User:** Consultor Ágil (same as P0-4)
**Objective:** Verify Excel gating for non-eligible plans

- [ ] **Step 1:** Execute search (7-day range, any UF)
- [ ] **Expected:** Search succeeds, results displayed
- [ ] **Step 2:** Locate Excel export button
- [ ] **Expected:** Button shows lock icon 🔒
- [ ] **Step 3:** Hover over Excel button
- [ ] **Expected:** Tooltip: "Exportar Excel disponível no plano Máquina (R$ 597/mês)"
- [ ] **Step 4:** Click locked Excel button
- [ ] **Expected:** Upgrade modal opens
- [ ] **Step 5:** Verify modal pre-selects "Máquina" plan
- [ ] **Expected:** Máquina highlighted with Excel capability shown
- [ ] **Screenshot:** Save upgrade modal with Máquina selected

**Pass Criteria:**
- Excel button locked
- Tooltip explains restriction
- Click opens upgrade modal targeting Máquina

---

### P0-6: Consultor Ágil - 30-Day Search Success

**Test User:** Consultor Ágil (same as P0-4)
**Objective:** Verify 30-day history access

- [ ] **Step 1:** Select date range: Last 30 days
- [ ] **Expected:** No validation error
- [ ] **Step 2:** Click "Buscar"
- [ ] **Expected:** HTTP 200, results displayed
- [ ] **Step 3:** Verify quota counter updates to 24/50
- [ ] **Expected:** Counter increments after successful search
- [ ] **Screenshot:** Save updated quota counter

**Pass Criteria:**
- 30-day search succeeds
- Quota increments correctly
- No errors

---

### P0-7: Máquina - Excel Export Functional

**Test User:** Máquina (150/300 searches used)
**Objective:** Verify Excel generation for eligible plans

- [ ] **Step 1:** Log in as Máquina user
- [ ] **Step 2:** Verify plan badge shows "Máquina" (green color)
- [ ] **Expected:** Badge color green
- [ ] **Step 3:** Execute search (30-day range, any UF)
- [ ] **Expected:** Search succeeds
- [ ] **Step 4:** Locate Excel export button
- [ ] **Expected:** Button is functional (no lock icon)
- [ ] **Step 5:** Click Excel export button
- [ ] **Expected:** Excel file downloads successfully
- [ ] **Step 6:** Open downloaded Excel file
- [ ] **Expected:** File contains search results with proper formatting
- [ ] **Screenshot:** Save Excel file preview

**Pass Criteria:**
- Excel button unlocked
- File downloads without errors
- Excel contains valid data

---

### P0-8: Máquina - 1-Year Search Success

**Test User:** Máquina (same as P0-7)
**Objective:** Verify 365-day history access

- [ ] **Step 1:** Select date range: Last 365 days
- [ ] **Expected:** No validation error
- [ ] **Step 2:** Click "Buscar"
- [ ] **Expected:** HTTP 200, results displayed
- [ ] **Step 3:** Verify quota counter updates to 151/300
- [ ] **Expected:** Progress bar at 50%, color yellow
- [ ] **Screenshot:** Save quota counter at 50% (yellow)

**Pass Criteria:**
- 1-year search succeeds
- Quota tracking accurate
- Progress bar color changes to yellow at 50%

---

### P0-9: Sala de Guerra - Full Capabilities

**Test User:** Sala de Guerra (50/1000 searches used)
**Objective:** Verify top-tier plan has all features

- [ ] **Step 1:** Log in as Sala de Guerra user
- [ ] **Step 2:** Verify plan badge shows "Sala de Guerra" (gold/yellow color)
- [ ] **Expected:** Badge color gold
- [ ] **Step 3:** Verify quota counter: "Buscas este mês: 50/1000"
- [ ] **Expected:** Progress bar green (<70% = 5%)
- [ ] **Step 4:** Select date range: Last 1825 days (5 years)
- [ ] **Expected:** No validation error
- [ ] **Step 5:** Click "Buscar"
- [ ] **Expected:** HTTP 200, results displayed
- [ ] **Step 6:** Click Excel export
- [ ] **Expected:** Excel downloads immediately
- [ ] **Step 7:** Check AI summary length (if displayed)
- [ ] **Expected:** Summary is comprehensive (1000 tokens max)
- [ ] **Screenshot:** Save results with AI summary

**Pass Criteria:**
- 5-year search succeeds
- Excel export functional
- AI summary longer than other plans
- Quota counter green

---

### P0-10: Quota Exhaustion - 429 Error

**Test User:** Consultor Ágil (50/50 searches used - EXHAUSTED)
**Objective:** Verify quota enforcement blocks searches

- [ ] **Step 1:** Log in as user with exhausted quota
- [ ] **Step 2:** Verify quota counter shows: "Buscas este mês: 50/50"
- [ ] **Expected:** Progress bar red at 100%
- [ ] **Step 3:** Attempt to execute search
- [ ] **Expected:** HTTP 429 error returned
- [ ] **Step 4:** Verify error dialog displays
- [ ] **Error Message:** "Você atingiu o limite de 50 buscas mensais do plano Consultor Ágil. Aguarde renovação em 01/03/2026 ou faça upgrade."
- [ ] **Step 5:** Verify upgrade button displayed
- [ ] **Expected:** Button labeled "Fazer Upgrade"
- [ ] **Step 6:** Click upgrade button
- [ ] **Expected:** Upgrade modal opens with Máquina or Sala de Guerra recommended
- [ ] **Screenshot:** Save 429 error dialog and upgrade modal

**Pass Criteria:**
- Search blocked with 429 error
- User-friendly error message with reset date
- Upgrade CTA functional

---

## Priority P1 - HIGH (Should Pass ≥90%)

These tests are important but not blockers for deployment.

### P1-1: Trial Expiration - Forced Upgrade

**Test User:** FREE trial (EXPIRED - trial_expires_at in past)
**Objective:** Verify expired trials cannot search

- [ ] **Step 1:** Log in as user with expired trial
- [ ] **Expected:** Plan badge shows "Trial Expirado" or warning indicator
- [ ] **Step 2:** Attempt to execute search
- [ ] **Expected:** HTTP 403 error returned
- [ ] **Step 3:** Verify error message
- [ ] **Error Message:** "Trial expirado. Faça upgrade para continuar usando o Smart PNCP."
- [ ] **Step 4:** Verify upgrade modal displayed automatically or via CTA
- [ ] **Expected:** Modal shows plan comparison
- [ ] **Screenshot:** Save expired trial error

**Pass Criteria:**
- Expired trial detected
- Search blocked with 403 error
- Clear upgrade prompt displayed

---

### P1-2: Plan Badge Clickable - Upgrade Modal

**Test User:** Any non-Sala de Guerra user
**Objective:** Verify upgrade flow accessibility

- [ ] **Step 1:** Click on plan badge in header
- [ ] **Expected:** Upgrade modal opens
- [ ] **Step 2:** Verify modal displays plan comparison table
- [ ] **Expected:** All 4 plans listed with features
- [ ] **Step 3:** Verify current plan highlighted
- [ ] **Expected:** User's current plan visually distinct
- [ ] **Step 4:** Verify pricing displayed for each tier
- [ ] **Expected:** R$ 297, R$ 597, R$ 1497
- [ ] **Step 5:** Verify key differentiators shown
- [ ] **Expected:** History limits, Excel availability, quota limits
- [ ] **Step 6:** Click CTA for a higher plan
- [ ] **Expected:** Redirected to payment/checkout (or placeholder message)
- [ ] **Screenshot:** Save upgrade modal

**Pass Criteria:**
- Badge is clickable
- Modal displays complete comparison
- CTAs functional

---

### P1-3: Date Range Edge Case - Exact Limit

**Test User:** Consultor Ágil
**Objective:** Verify exact date range limits work correctly

- [ ] **Step 1:** Select date range: Exactly 30 days
- [ ] **Expected:** Validation passes
- [ ] **Step 2:** Execute search
- [ ] **Expected:** HTTP 200, search succeeds
- [ ] **Step 3:** Select date range: 31 days
- [ ] **Expected:** Validation error appears
- [ ] **Screenshot:** Save both scenarios

**Pass Criteria:**
- 30 days succeeds
- 31 days fails with validation error

---

### P1-4: Date Range Edge Case - Leap Year

**Test User:** Máquina
**Objective:** Verify leap year date calculations work

- [ ] **Step 1:** Select date range: Feb 28, 2024 to Feb 29, 2025 (366 days)
- [ ] **Expected:** Validation error (exceeds 365-day limit)
- [ ] **Step 2:** Select date range: Mar 1, 2024 to Feb 29, 2025 (365 days)
- [ ] **Expected:** Validation passes
- [ ] **Screenshot:** Save leap year validation

**Pass Criteria:**
- 366 days blocked
- 365 days allowed
- Leap year handled correctly

---

### P1-5: Rate Limiting - Burst Protection

**Test User:** Consultor Ágil
**Objective:** Verify rate limiting prevents abuse

- [ ] **Step 1:** Execute 10 searches in rapid succession (<60 seconds)
- [ ] **Expected:** All 10 searches succeed
- [ ] **Step 2:** Execute 11th search immediately
- [ ] **Expected:** HTTP 429 error with `Retry-After` header
- [ ] **Step 3:** Verify error message
- [ ] **Error Message:** "Limite de requisições excedido (10 req/min). Aguarde X segundos."
- [ ] **Step 4:** Wait for retry period (60 seconds)
- [ ] **Step 5:** Execute search again
- [ ] **Expected:** Search succeeds
- [ ] **Screenshot:** Save 429 rate limit error

**Pass Criteria:**
- First 10 requests succeed
- 11th request blocked with 429
- `Retry-After` header present
- Search succeeds after waiting

---

### P1-6: Capabilities API Response Validation

**Test User:** All 4 plan types
**Objective:** Verify `/api/me` returns correct capabilities for each plan

**FREE Trial User:**
- [ ] **Step 1:** Call `GET /api/me`
- [ ] **Step 2:** Verify response contains:
  - `capabilities.max_history_days: 7`
  - `capabilities.allow_excel: false`
  - `capabilities.max_requests_per_month: 999999`
  - `capabilities.max_requests_per_min: 2`
  - `capabilities.max_summary_tokens: 200`
  - `capabilities.priority: "low"`
  - `trial_expires_at: [valid ISO timestamp]`

**Consultor Ágil User:**
- [ ] **Step 3:** Call `GET /api/me`
- [ ] **Step 4:** Verify response contains:
  - `capabilities.max_history_days: 30`
  - `capabilities.allow_excel: false`
  - `capabilities.max_requests_per_month: 50`
  - `capabilities.max_requests_per_min: 10`
  - `capabilities.max_summary_tokens: 200`
  - `capabilities.priority: "normal"`

**Máquina User:**
- [ ] **Step 5:** Call `GET /api/me`
- [ ] **Step 6:** Verify response contains:
  - `capabilities.max_history_days: 365`
  - `capabilities.allow_excel: true`
  - `capabilities.max_requests_per_month: 300`
  - `capabilities.max_requests_per_min: 30`
  - `capabilities.max_summary_tokens: 500`
  - `capabilities.priority: "high"`

**Sala de Guerra User:**
- [ ] **Step 7:** Call `GET /api/me`
- [ ] **Step 8:** Verify response contains:
  - `capabilities.max_history_days: 1825`
  - `capabilities.allow_excel: true`
  - `capabilities.max_requests_per_month: 1000`
  - `capabilities.max_requests_per_min: 60`
  - `capabilities.max_summary_tokens: 1000`
  - `capabilities.priority: "critical"`

- [ ] **Screenshot:** Save all 4 API responses

**Pass Criteria:**
- All fields present for all plans
- Values match `PLAN_CAPABILITIES` in backend

---

### P1-7: Máquina - 2-Year Search Blocked

**Test User:** Máquina
**Objective:** Verify upper limit enforcement

- [ ] **Step 1:** Select date range: Last 730 days (2 years)
- [ ] **Expected:** Validation error appears
- [ ] **Error Message:** "Seu plano Máquina permite buscas de até 365 dias. Faça upgrade para acessar histórico completo."
- [ ] **Step 2:** Verify upgrade suggestion points to "Sala de Guerra"
- [ ] **Expected:** CTA suggests next tier
- [ ] **Screenshot:** Save validation error

**Pass Criteria:**
- 2-year search blocked
- Upgrade suggestion correct

---

## Priority P2 - MEDIUM (Should Pass ≥70%)

These tests validate polish and edge cases but are not deployment blockers.

### P2-1: Quota Counter Color Transitions

**Test User:** Consultor Ágil with varying quota levels
**Objective:** Verify color coding logic

- [ ] **Step 1:** User with 30/50 searches (60%)
- [ ] **Expected:** Progress bar green
- [ ] **Step 2:** User with 40/50 searches (80%)
- [ ] **Expected:** Progress bar yellow
- [ ] **Step 3:** User with 48/50 searches (96%)
- [ ] **Expected:** Progress bar red
- [ ] **Screenshot:** Save all 3 color states

**Pass Criteria:**
- Green: <70%
- Yellow: 70-90%
- Red: >90%

---

### P2-2: Supabase Quota Failure - Graceful Degradation

**Objective:** Verify system continues if quota check fails

- [ ] **Step 1:** Simulate Supabase quota table unavailable (disconnect or mock)
- [ ] **Step 2:** Execute search as any user
- [ ] **Expected:** Search proceeds with fallback behavior
- [ ] **Step 3:** Check backend logs for warning
- [ ] **Expected:** Warning logged, but no user-facing error
- [ ] **Step 4:** Verify user experience not disrupted
- [ ] **Screenshot:** Save successful search despite quota failure

**Pass Criteria:**
- Graceful degradation on quota failure
- User experience not disrupted
- Warning logged for admin review

---

### P2-3: Invalid Plan ID - Fallback to FREE Trial

**Test User:** User with invalid `plan_id` in database
**Objective:** Verify fallback mechanism

- [ ] **Step 1:** Set user's `plan_id` to "unknown_plan" in database
- [ ] **Step 2:** Execute search
- [ ] **Expected:** System defaults to `free_trial` capabilities
- [ ] **Step 3:** Verify search limited to 7-day range
- [ ] **Expected:** Free trial restrictions apply
- [ ] **Step 4:** Check backend logs for warning
- [ ] **Expected:** Invalid plan ID logged
- [ ] **Screenshot:** Save behavior with invalid plan

**Pass Criteria:**
- Fallback to free_trial capabilities
- No application crash
- Warning logged

---

### P2-4: Feature Flag Disable - Rollback Test

**Objective:** Verify feature flag can disable new pricing

- [ ] **Step 1:** Set `ENABLE_NEW_PRICING=false` in environment
- [ ] **Step 2:** Restart application
- [ ] **Step 3:** Verify old behavior or graceful degradation
- [ ] **Expected:** No errors, system stable
- [ ] **Step 4:** Re-enable flag: `ENABLE_NEW_PRICING=true`
- [ ] **Step 5:** Restart application
- [ ] **Step 6:** Verify new behavior returns
- [ ] **Expected:** All new features functional again
- [ ] **Screenshot:** Save both states

**Pass Criteria:**
- Flag disable works without errors
- Flag enable restores functionality
- No data corruption

---

### P2-5: Quota Check Performance

**Objective:** Verify quota validation doesn't slow down searches

- [ ] **Step 1:** Execute search and measure response time
- [ ] **Expected:** Total response time <3 seconds
- [ ] **Step 2:** Check backend logs for quota check duration
- [ ] **Expected:** Quota validation adds <200ms overhead
- [ ] **Step 3:** Execute 100 sequential searches (within quota)
- [ ] **Expected:** No performance degradation
- [ ] **Screenshot:** Save performance metrics

**Pass Criteria:**
- Quota check adds <200ms
- No memory leaks over 100 requests
- Response time consistent

---

## Evidence Collection

For each test, collect:

1. **Screenshots:**
   - Plan badge display
   - Quota counter states
   - Error dialogs
   - Upgrade modals
   - Excel file previews

2. **Network Logs:**
   - `/api/me` responses (all 4 plans)
   - `/api/buscar` responses (success & errors)
   - HTTP status codes (200, 403, 429)

3. **Browser Console:**
   - JavaScript errors (should be NONE)
   - Warning messages

4. **Backend Logs:**
   - Quota check execution
   - Rate limiting triggers
   - Validation errors

---

## Sign-Off

**Tester Name:** ___________________
**Test Date:** ___________________
**Environment:** Staging
**Feature Flag:** ENABLE_NEW_PRICING=true

**Results Summary:**

| Priority | Total Tests | Passed | Failed | Pass Rate |
|----------|-------------|--------|--------|-----------|
| P0 (Critical) | 10 | ____ | ____ | ___% |
| P1 (High) | 7 | ____ | ____ | ___% |
| P2 (Medium) | 5 | ____ | ____ | ___% |
| **TOTAL** | **22** | ____ | ____ | ___% |

**Go/No-Go Decision:**

- [ ] **GO FOR PRODUCTION** - All P0 pass (100%), P1 ≥90%, P2 ≥70%
- [ ] **NO-GO** - Blockers exist (list below)

**Blockers:**
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

**Tester Signature:** ___________________
**QA Lead Approval:** ___________________
**Product Owner Approval:** ___________________
**Date:** ___________________

---

**Next Steps:**

1. If GO: Proceed to production deployment with phased rollout (10% → 50% → 100%)
2. If NO-GO: Fix blockers, re-test, update this checklist with new results
3. Archive test evidence in: `docs/deployment/evidence/STORY-165-staging-YYYY-MM-DD/`
