# Smoke Tests - STORY-165 Plan Restructuring

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Created:** February 3, 2026
**Environment:** Staging (pre-production)

---

## Test Objective

Validate critical user flows for the new 4-tier pricing model (FREE Trial, Consultor Ágil, Máquina, Sala de Guerra) before production deployment.

---

## Critical User Flows

### Flow 1: FREE Trial User - Date Range Restriction

**User Profile:**
- Plan: `free_trial`
- Trial Status: Active (3 days remaining)
- Max History: 7 days

**Test Steps:**
1. Log in as FREE trial user
2. Verify plan badge shows "FREE Trial" with countdown (e.g., "3 dias restantes")
3. Select date range: Last 7 days
4. Execute search
5. **Expected:** Search succeeds, results displayed
6. Attempt date range: Last 30 days
7. **Expected:** Validation error appears: "Seu plano FREE Trial permite buscas de até 7 dias. Faça upgrade para acessar histórico completo."
8. Verify search button is disabled until valid range selected
9. Verify upgrade CTA displayed with suggestion to "Consultor Ágil"

**Pass Criteria:**
- ✅ Plan badge displays correctly with trial countdown
- ✅ 7-day search succeeds
- ✅ 30-day search blocked with user-friendly error
- ✅ Upgrade suggestion points to Consultor Ágil plan

---

### Flow 2: Consultor Ágil - Excel Locked, Quota Counter

**User Profile:**
- Plan: `consultor_agil` (R$ 297/mês)
- Monthly Quota: 50 searches
- Quota Used: 23/50
- Max History: 30 days
- Excel Export: DISABLED

**Test Steps:**
1. Log in as Consultor Ágil user
2. Verify plan badge shows "Consultor Ágil" (blue color)
3. Verify quota counter displays: "Buscas este mês: 23/50" with green progress bar
4. Select date range: Last 30 days
5. Execute search
6. **Expected:** Search succeeds, results displayed on screen
7. Observe Excel export button
8. **Expected:** Button shows lock icon 🔒
9. Hover over Excel button
10. **Expected:** Tooltip: "Exportar Excel disponível no plano Máquina (R$ 597/mês)"
11. Click locked Excel button
12. **Expected:** Upgrade modal opens with Máquina plan pre-selected
13. Execute search again (quota now 24/50)
14. **Expected:** Quota counter updates to 24/50

**Pass Criteria:**
- ✅ Plan badge correct (blue Consultor Ágil)
- ✅ Quota counter accurate and updates after search
- ✅ 30-day search succeeds
- ✅ Excel button locked with upgrade tooltip
- ✅ Click opens upgrade modal targeting Máquina

---

### Flow 3: Máquina - Excel Unlocked, Larger History

**User Profile:**
- Plan: `maquina` (R$ 597/mês)
- Monthly Quota: 300 searches
- Quota Used: 150/300
- Max History: 365 days (1 year)
- Excel Export: ENABLED

**Test Steps:**
1. Log in as Máquina user
2. Verify plan badge shows "Máquina" (green color)
3. Verify quota counter: "Buscas este mês: 150/300" with yellow progress bar (50% used)
4. Select date range: Last 365 days (1 year)
5. Execute search
6. **Expected:** Search succeeds, results displayed
7. Observe Excel export button
8. **Expected:** Button is functional (no lock icon)
9. Click Excel export button
10. **Expected:** Excel file downloads successfully
11. Verify quota counter updates to 151/300
12. Attempt date range: Last 730 days (2 years)
13. **Expected:** Validation error: "Seu plano Máquina permite buscas de até 365 dias. Faça upgrade para acessar histórico completo."
14. Verify upgrade suggestion points to "Sala de Guerra"

**Pass Criteria:**
- ✅ Plan badge correct (green Máquina)
- ✅ Quota counter at 50% shows yellow
- ✅ 1-year search succeeds
- ✅ Excel export functional and downloads file
- ✅ 2-year search blocked with upgrade suggestion to Sala de Guerra

---

### Flow 4: Sala de Guerra - Full Capabilities

**User Profile:**
- Plan: `sala_guerra` (R$ 1497/mês)
- Monthly Quota: 1000 searches
- Quota Used: 50/1000
- Max History: 1825 days (5 years)
- Excel Export: ENABLED
- Priority: CRITICAL

**Test Steps:**
1. Log in as Sala de Guerra user
2. Verify plan badge shows "Sala de Guerra" (gold/yellow color)
3. Verify quota counter: "Buscas este mês: 50/1000" with green progress bar (<10% used)
4. Select date range: Last 1825 days (5 years)
5. Execute search
6. **Expected:** Search succeeds, results displayed
7. Click Excel export
8. **Expected:** Excel downloads immediately
9. Verify quota counter updates to 51/1000
10. Check AI summary length (should be longer than other plans)
11. **Expected:** Summary uses 1000 tokens (comprehensive)

**Pass Criteria:**
- ✅ Plan badge correct (gold Sala de Guerra)
- ✅ Quota counter shows green (<70% threshold)
- ✅ 5-year search succeeds
- ✅ Excel export functional
- ✅ AI summary is comprehensive (1000 tokens)

---

### Flow 5: Quota Exhaustion - Upgrade CTA

**User Profile:**
- Plan: `consultor_agil`
- Monthly Quota: 50 searches
- Quota Used: 50/50 (EXHAUSTED)

**Test Steps:**
1. Log in as user with exhausted quota
2. Verify quota counter: "Buscas este mês: 50/50" with red progress bar
3. Attempt to execute search
4. **Expected:** HTTP 429 error returned
5. Verify error dialog displays:
   - Message: "Você atingiu o limite de 50 buscas mensais do plano Consultor Ágil. Aguarde renovação em 01/03/2026 ou faça upgrade."
   - Upgrade button displayed
6. Click upgrade button
7. **Expected:** Upgrade modal opens with Máquina or Sala de Guerra recommended

**Pass Criteria:**
- ✅ Quota counter red at 100%
- ✅ Search blocked with 429 error
- ✅ User-friendly error message with reset date
- ✅ Upgrade CTA functional

---

### Flow 6: Trial Expiration - Forced Upgrade

**User Profile:**
- Plan: `free_trial`
- Trial Status: EXPIRED (trial_expires_at in past)

**Test Steps:**
1. Log in as user with expired trial
2. **Expected:** Plan badge shows "Trial Expirado" or similar
3. Attempt to execute search
4. **Expected:** HTTP 403 error returned
5. Verify error message: "Trial expirado. Faça upgrade para continuar usando o SmartLic."
6. Verify upgrade modal displayed automatically or via CTA

**Pass Criteria:**
- ✅ Expired trial detected
- ✅ Search blocked with 403 error
- ✅ Clear upgrade prompt displayed

---

### Flow 7: Rate Limiting - Burst Protection

**User Profile:**
- Plan: `consultor_agil`
- Rate Limit: 10 requests/minute

**Test Steps:**
1. Log in as Consultor Ágil user
2. Execute 10 searches in rapid succession (<60 seconds)
3. **Expected:** All 10 searches succeed
4. Execute 11th search immediately
5. **Expected:** HTTP 429 error with `Retry-After` header
6. Verify error message: "Limite de requisições excedido (10 req/min). Aguarde X segundos."
7. Wait for retry period (e.g., 60 seconds)
8. Execute search again
9. **Expected:** Search succeeds

**Pass Criteria:**
- ✅ First 10 requests succeed
- ✅ 11th request blocked with 429
- ✅ Retry-After header present
- ✅ Search succeeds after waiting

---

### Flow 8: Plan Badge Clickable - Upgrade Modal

**Test Steps:**
1. Log in as any non-Sala de Guerra user
2. Click on plan badge in header/sidebar
3. **Expected:** Upgrade modal opens
4. Verify modal displays:
   - Plan comparison table
   - Current plan highlighted
   - Pricing for each tier
   - Key differentiators (history, Excel, quota)
   - CTAs for each higher tier
5. Click CTA for a higher plan
6. **Expected:** Redirected to payment/checkout (or placeholder)

**Pass Criteria:**
- ✅ Badge is clickable
- ✅ Modal displays plan comparison
- ✅ CTAs functional

---

## Data Validation Tests

### Test 9: Capabilities API Response

**Endpoint:** `GET /api/me`

**Test Steps:**
1. Call `/api/me` as each plan type
2. Verify response includes `capabilities` object with:
   - `max_history_days`
   - `allow_excel`
   - `max_requests_per_month`
   - `max_requests_per_min`
   - `max_summary_tokens`
   - `priority`
3. Verify `quota_used`, `quota_remaining`, `quota_reset_date` present
4. For FREE trial, verify `trial_expires_at` present

**Pass Criteria:**
- ✅ All fields present for all plans
- ✅ Values match `PLAN_CAPABILITIES` in backend

---

### Test 10: Date Range Validation Edge Cases

**Test Steps:**
1. FREE trial user: Test exactly 7 days (should succeed)
2. FREE trial user: Test 8 days (should fail)
3. Consultor Ágil: Test 30 days (succeed), 31 days (fail)
4. Máquina: Test 365 days (succeed), 366 days (fail)
5. Sala de Guerra: Test 1825 days (succeed), 1826 days (fail)
6. Test leap year scenarios (Feb 29)

**Pass Criteria:**
- ✅ Exact limits succeed
- ✅ One day over limits fail
- ✅ Leap year handled correctly

---

## Rollback Test

### Test 11: Feature Flag Disable

**Test Steps:**
1. Set `ENABLE_NEW_PRICING=false` in environment
2. Restart application
3. Verify old behavior (if applicable) or graceful degradation
4. Re-enable flag: `ENABLE_NEW_PRICING=true`
5. Verify new behavior returns

**Pass Criteria:**
- ✅ Flag disable works without errors
- ✅ Flag enable restores functionality

---

## Performance Tests

### Test 12: Quota Check Performance

**Test Steps:**
1. Measure `/api/buscar` response time with quota check
2. Target: <200ms overhead for quota validation
3. Execute 100 sequential searches (within quota)
4. Verify no performance degradation

**Pass Criteria:**
- ✅ Quota check adds <200ms
- ✅ No memory leaks or degradation over 100 requests

---

## Error Handling Tests

### Test 13: Supabase Quota Failure

**Test Steps:**
1. Simulate Supabase quota table unavailable (mock or disconnect)
2. Execute search
3. **Expected:** Search proceeds with fallback behavior (log warning, allow request)
4. Verify no user-facing error

**Pass Criteria:**
- ✅ Graceful degradation on quota failure
- ✅ User experience not disrupted

---

### Test 14: Invalid Plan ID

**Test Steps:**
1. User with invalid `plan_id` in database (e.g., "unknown_plan")
2. Execute search
3. **Expected:** Defaults to `free_trial` capabilities
4. Log warning for admin review

**Pass Criteria:**
- ✅ Fallback to free_trial
- ✅ No application crash

---

## Manual Testing Checklist

**Tester:** ___________
**Date:** ___________
**Environment:** Staging

| Flow # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | FREE Trial - Date Restriction | ⬜ PASS / ⬜ FAIL | |
| 2 | Consultor Ágil - Excel Locked | ⬜ PASS / ⬜ FAIL | |
| 3 | Máquina - Excel Unlocked | ⬜ PASS / ⬜ FAIL | |
| 4 | Sala de Guerra - Full Caps | ⬜ PASS / ⬜ FAIL | |
| 5 | Quota Exhaustion | ⬜ PASS / ⬜ FAIL | |
| 6 | Trial Expiration | ⬜ PASS / ⬜ FAIL | |
| 7 | Rate Limiting | ⬜ PASS / ⬜ FAIL | |
| 8 | Plan Badge Upgrade | ⬜ PASS / ⬜ FAIL | |
| 9 | Capabilities API | ⬜ PASS / ⬜ FAIL | |
| 10 | Date Edge Cases | ⬜ PASS / ⬜ FAIL | |
| 11 | Feature Flag Rollback | ⬜ PASS / ⬜ FAIL | |
| 12 | Quota Performance | ⬜ PASS / ⬜ FAIL | |
| 13 | Supabase Failure | ⬜ PASS / ⬜ FAIL | |
| 14 | Invalid Plan ID | ⬜ PASS / ⬜ FAIL | |

**Overall Result:** ⬜ GO FOR PRODUCTION / ⬜ NO-GO (Blockers: ____________)

---

## Automated Test Coverage

Refer to:
- Backend: `pytest --cov` (target: ≥70%)
- Frontend: `npm test -- --coverage` (target: ≥60%)

---

## Sign-Off

**QA Lead:** ___________  **Date:** ___________
**Product Owner:** ___________  **Date:** ___________
**DevOps:** ___________  **Date:** ___________

---

**Next Steps:**
1. Execute all smoke tests on staging
2. Document any failures in quality gate report
3. Fix blockers if any
4. Re-test after fixes
5. Proceed to production deployment with phased rollout (10% → 50% → 100%)
