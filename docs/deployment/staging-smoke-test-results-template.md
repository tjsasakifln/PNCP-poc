# Staging Smoke Test Results - STORY-165

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Test Date:** ___________________
**Tester:** ___________________
**Environment:** Staging
**Feature Flag:** ENABLE_NEW_PRICING=true

---

## Test Execution Summary

**Start Time:** ___________________
**End Time:** ___________________
**Duration:** ___________________

**Test Environment Details:**
- **Frontend URL:** ___________________
- **Backend URL:** ___________________
- **Database:** Supabase Staging
- **Browser:** ___________________ (version: _______)
- **Device:** ___________________

---

## Priority P0 - CRITICAL (Must Pass 100%)

### P0-1: Authentication & Health Check

**Status:** [ ] PASS / [ ] FAIL

**Execution Details:**
- Login time: _____ seconds
- `/api/me` response time: _____ ms
- HTTP status code: _____

**Evidence:**
- Screenshot: `evidence/P0-1-api-me-response.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-2: FREE Trial - 7-Day Date Range (Success Case)

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `free-trial@smartpncp.test`

**Execution Details:**
- Plan badge displayed: [ ] Yes / [ ] No
- Trial countdown accurate: [ ] Yes / [ ] No
- Search completed: [ ] Yes / [ ] No
- HTTP status code: _____
- Response time: _____ ms
- Results count: _____

**Evidence:**
- Screenshot: `evidence/P0-2-free-trial-7day-success.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-3: FREE Trial - 30-Day Date Range (Block Case)

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `free-trial@smartpncp.test`

**Execution Details:**
- Validation error displayed: [ ] Yes / [ ] No
- Search button disabled: [ ] Yes / [ ] No
- Upgrade CTA shown: [ ] Yes / [ ] No
- Suggested plan: _____

**Evidence:**
- Screenshot: `evidence/P0-3-free-trial-30day-blocked.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-4: Consultor Ágil - Quota Counter Display

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-low@smartpncp.test`

**Execution Details:**
- Plan badge color: _____
- Quota counter text: _____/_____
- Progress bar color: _____
- Reset date displayed: _____

**Evidence:**
- Screenshot: `evidence/P0-4-consultor-quota-counter.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-5: Consultor Ágil - Excel Export Locked

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-low@smartpncp.test`

**Execution Details:**
- Excel button locked: [ ] Yes / [ ] No
- Tooltip displayed: [ ] Yes / [ ] No
- Tooltip text: _____________________________
- Upgrade modal opened: [ ] Yes / [ ] No
- Pre-selected plan: _____

**Evidence:**
- Screenshot: `evidence/P0-5-consultor-excel-locked.png`
- Screenshot: `evidence/P0-5-upgrade-modal.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-6: Consultor Ágil - 30-Day Search Success

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-low@smartpncp.test`

**Execution Details:**
- Search completed: [ ] Yes / [ ] No
- HTTP status code: _____
- Quota before search: _____/_____
- Quota after search: _____/_____
- Quota incremented correctly: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P0-6-consultor-30day-success.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-7: Máquina - Excel Export Functional

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `maquina@smartpncp.test`

**Execution Details:**
- Excel button unlocked: [ ] Yes / [ ] No
- Excel file downloaded: [ ] Yes / [ ] No
- File size: _____ KB
- File opened successfully: [ ] Yes / [ ] No
- Data integrity verified: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P0-7-maquina-excel-export.png`
- Excel file: `evidence/P0-7-sample-export.xlsx`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-8: Máquina - 1-Year Search Success

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `maquina@smartpncp.test`

**Execution Details:**
- Search completed: [ ] Yes / [ ] No
- HTTP status code: _____
- Quota counter at 50%: [ ] Yes / [ ] No
- Progress bar color: _____ (expected: yellow)
- Response time: _____ ms

**Evidence:**
- Screenshot: `evidence/P0-8-maquina-1year-search.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-9: Sala de Guerra - Full Capabilities

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `sala-guerra@smartpncp.test`

**Execution Details:**
- Plan badge color: _____ (expected: gold)
- 5-year search completed: [ ] Yes / [ ] No
- Excel export functional: [ ] Yes / [ ] No
- AI summary length: _____ tokens (expected: ~1000)
- Quota counter color: _____ (expected: green)

**Evidence:**
- Screenshot: `evidence/P0-9-sala-guerra-full-caps.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

### P0-10: Quota Exhaustion - 429 Error

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-exhausted@smartpncp.test`

**Execution Details:**
- Quota counter at 100%: [ ] Yes / [ ] No
- Progress bar color: _____ (expected: red)
- HTTP status code: _____ (expected: 429)
- Error message displayed: [ ] Yes / [ ] No
- Reset date shown: _____
- Upgrade button functional: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P0-10-quota-exhausted.png`
- Screenshot: `evidence/P0-10-error-dialog.png`

**Notes:**
_____________________________________________________________________________
_____________________________________________________________________________

---

## P0 Results Summary

**Total P0 Tests:** 10
**Passed:** _____
**Failed:** _____
**Pass Rate:** _____% (Must be 100% for GO decision)

**P0 Blockers (if any):**
1. _____________________________________________________________________________
2. _____________________________________________________________________________
3. _____________________________________________________________________________

---

## Priority P1 - HIGH (Should Pass ≥90%)

### P1-1: Trial Expiration - Forced Upgrade

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `free-expired@smartpncp.test`

**Execution Details:**
- Expired trial detected: [ ] Yes / [ ] No
- HTTP status code: _____ (expected: 403)
- Error message displayed: [ ] Yes / [ ] No
- Upgrade modal shown: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P1-1-trial-expired.png`

**Notes:**
_____________________________________________________________________________

---

### P1-2: Plan Badge Clickable - Upgrade Modal

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-low@smartpncp.test`

**Execution Details:**
- Badge clickable: [ ] Yes / [ ] No
- Modal opened: [ ] Yes / [ ] No
- All 4 plans displayed: [ ] Yes / [ ] No
- Current plan highlighted: [ ] Yes / [ ] No
- Pricing shown: [ ] Yes / [ ] No
- CTAs functional: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P1-2-upgrade-modal.png`

**Notes:**
_____________________________________________________________________________

---

### P1-3: Date Range Edge Case - Exact Limit

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-edge@smartpncp.test`

**Execution Details:**
- 30-day search: [ ] PASS / [ ] FAIL (expected: PASS)
- 31-day search: [ ] PASS / [ ] FAIL (expected: FAIL with validation error)

**Evidence:**
- Screenshot: `evidence/P1-3-30day-success.png`
- Screenshot: `evidence/P1-3-31day-blocked.png`

**Notes:**
_____________________________________________________________________________

---

### P1-4: Date Range Edge Case - Leap Year

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `maquina@smartpncp.test`

**Execution Details:**
- 366-day search blocked: [ ] Yes / [ ] No
- 365-day search allowed: [ ] Yes / [ ] No
- Leap year calculation correct: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P1-4-leap-year-test.png`

**Notes:**
_____________________________________________________________________________

---

### P1-5: Rate Limiting - Burst Protection

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `consultor-rate@smartpncp.test`

**Execution Details:**
- First 10 requests succeeded: [ ] Yes / [ ] No
- 11th request blocked: [ ] Yes / [ ] No
- HTTP status code: _____ (expected: 429)
- `Retry-After` header present: [ ] Yes / [ ] No
- Retry-After value: _____ seconds
- Request succeeded after waiting: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P1-5-rate-limit-error.png`

**Notes:**
_____________________________________________________________________________

---

### P1-6: Capabilities API Response Validation

**Status:** [ ] PASS / [ ] FAIL

**Test Details:**

**FREE Trial:**
- `max_history_days`: _____ (expected: 7)
- `allow_excel`: _____ (expected: false)
- `max_requests_per_month`: _____ (expected: 999999)
- `max_summary_tokens`: _____ (expected: 200)

**Consultor Ágil:**
- `max_history_days`: _____ (expected: 30)
- `allow_excel`: _____ (expected: false)
- `max_requests_per_month`: _____ (expected: 50)
- `max_summary_tokens`: _____ (expected: 200)

**Máquina:**
- `max_history_days`: _____ (expected: 365)
- `allow_excel`: _____ (expected: true)
- `max_requests_per_month`: _____ (expected: 300)
- `max_summary_tokens`: _____ (expected: 500)

**Sala de Guerra:**
- `max_history_days`: _____ (expected: 1825)
- `allow_excel`: _____ (expected: true)
- `max_requests_per_month`: _____ (expected: 1000)
- `max_summary_tokens`: _____ (expected: 1000)

**Evidence:**
- JSON file: `evidence/P1-6-api-responses.json`

**Notes:**
_____________________________________________________________________________

---

### P1-7: Máquina - 2-Year Search Blocked

**Status:** [ ] PASS / [ ] FAIL

**Test User:** `maquina@smartpncp.test`

**Execution Details:**
- 2-year search blocked: [ ] Yes / [ ] No
- Validation error displayed: [ ] Yes / [ ] No
- Suggested plan: _____ (expected: Sala de Guerra)

**Evidence:**
- Screenshot: `evidence/P1-7-maquina-2year-blocked.png`

**Notes:**
_____________________________________________________________________________

---

## P1 Results Summary

**Total P1 Tests:** 7
**Passed:** _____
**Failed:** _____
**Pass Rate:** _____% (Must be ≥90% for GO decision)

**P1 Issues (if any):**
1. _____________________________________________________________________________
2. _____________________________________________________________________________

---

## Priority P2 - MEDIUM (Should Pass ≥70%)

### P2-1: Quota Counter Color Transitions

**Status:** [ ] PASS / [ ] FAIL

**Execution Details:**
- 60% quota (green): [ ] PASS / [ ] FAIL
- 80% quota (yellow): [ ] PASS / [ ] FAIL
- 96% quota (red): [ ] PASS / [ ] FAIL

**Evidence:**
- Screenshot: `evidence/P2-1-quota-colors.png`

**Notes:**
_____________________________________________________________________________

---

### P2-2: Supabase Quota Failure - Graceful Degradation

**Status:** [ ] PASS / [ ] FAIL / [ ] SKIPPED

**Execution Details:**
- Quota table disconnected: [ ] Yes / [ ] No
- Search still proceeded: [ ] Yes / [ ] No
- Warning logged: [ ] Yes / [ ] No
- User experience disrupted: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P2-2-quota-failure-test.png`
- Logs: `evidence/P2-2-backend-logs.txt`

**Notes:**
_____________________________________________________________________________

---

### P2-3: Invalid Plan ID - Fallback to FREE Trial

**Status:** [ ] PASS / [ ] FAIL / [ ] SKIPPED

**Execution Details:**
- Invalid plan ID user tested: [ ] Yes / [ ] No
- System defaulted to free_trial: [ ] Yes / [ ] No
- 7-day limit enforced: [ ] Yes / [ ] No
- Warning logged: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P2-3-invalid-plan.png`

**Notes:**
_____________________________________________________________________________

---

### P2-4: Feature Flag Disable - Rollback Test

**Status:** [ ] PASS / [ ] FAIL / [ ] SKIPPED

**Execution Details:**
- Flag disabled successfully: [ ] Yes / [ ] No
- System stable: [ ] Yes / [ ] No
- Flag re-enabled successfully: [ ] Yes / [ ] No
- Features restored: [ ] Yes / [ ] No

**Evidence:**
- Screenshot: `evidence/P2-4-flag-disabled.png`
- Screenshot: `evidence/P2-4-flag-enabled.png`

**Notes:**
_____________________________________________________________________________

---

### P2-5: Quota Check Performance

**Status:** [ ] PASS / [ ] FAIL

**Execution Details:**
- Quota check overhead: _____ ms (must be <200ms)
- 100 sequential searches: [ ] Completed / [ ] Failed
- Performance degradation: [ ] Yes / [ ] No
- Memory leaks detected: [ ] Yes / [ ] No

**Evidence:**
- Performance logs: `evidence/P2-5-performance-metrics.txt`

**Notes:**
_____________________________________________________________________________

---

## P2 Results Summary

**Total P2 Tests:** 5
**Passed:** _____
**Failed:** _____
**Skipped:** _____
**Pass Rate:** _____% (Must be ≥70% for GO decision)

**P2 Issues (if any):**
1. _____________________________________________________________________________
2. _____________________________________________________________________________

---

## Overall Test Results

| Priority | Total | Passed | Failed | Skipped | Pass Rate | Threshold | Status |
|----------|-------|--------|--------|---------|-----------|-----------|--------|
| P0 (Critical) | 10 | _____ | _____ | 0 | _____% | 100% | [ ] PASS / [ ] FAIL |
| P1 (High) | 7 | _____ | _____ | _____ | _____% | 90% | [ ] PASS / [ ] FAIL |
| P2 (Medium) | 5 | _____ | _____ | _____ | _____% | 70% | [ ] PASS / [ ] FAIL |
| **TOTAL** | **22** | _____ | _____ | _____ | _____% | - | - |

---

## Issues Found

### Issue #1

**Severity:** [ ] BLOCKER / [ ] CRITICAL / [ ] MAJOR / [ ] MINOR

**Test ID:** _____

**Description:**
_____________________________________________________________________________
_____________________________________________________________________________

**Steps to Reproduce:**
1. _____________________________________________________________________________
2. _____________________________________________________________________________
3. _____________________________________________________________________________

**Expected Result:**
_____________________________________________________________________________

**Actual Result:**
_____________________________________________________________________________

**Evidence:**
- Screenshot/Log: _____________________________

**Root Cause (if known):**
_____________________________________________________________________________

**Workaround:**
_____________________________________________________________________________

**Assigned To:** _____________________
**Target Fix Date:** _____________________

---

### Issue #2

**Severity:** [ ] BLOCKER / [ ] CRITICAL / [ ] MAJOR / [ ] MINOR

**Test ID:** _____

**Description:**
_____________________________________________________________________________
_____________________________________________________________________________

**Steps to Reproduce:**
1. _____________________________________________________________________________
2. _____________________________________________________________________________
3. _____________________________________________________________________________

**Expected Result:**
_____________________________________________________________________________

**Actual Result:**
_____________________________________________________________________________

**Evidence:**
- Screenshot/Log: _____________________________

**Root Cause (if known):**
_____________________________________________________________________________

**Workaround:**
_____________________________________________________________________________

**Assigned To:** _____________________
**Target Fix Date:** _____________________

---

(Add more issue sections as needed)

---

## Go/No-Go Decision

**Decision:** [ ] GO FOR PRODUCTION / [ ] NO-GO

**Justification:**
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

### Go Criteria Met:

- [ ] All P0 tests passed (100%)
- [ ] P1 tests passed ≥90%
- [ ] P2 tests passed ≥70%
- [ ] No BLOCKER or CRITICAL issues
- [ ] All evidence collected and archived
- [ ] Test users cleaned up from staging

### Blockers (if NO-GO):

1. _____________________________________________________________________________
2. _____________________________________________________________________________
3. _____________________________________________________________________________

### Next Steps:

**If GO:**
- [ ] Archive test evidence in `docs/deployment/evidence/STORY-165-staging-YYYY-MM-DD/`
- [ ] Update STORY-165 status to "Ready for Production"
- [ ] Schedule production deployment (phased rollout: 10% → 50% → 100%)
- [ ] Prepare production smoke test plan
- [ ] Notify stakeholders of GO decision

**If NO-GO:**
- [ ] Create GitHub issues for all blockers
- [ ] Assign blockers to developers
- [ ] Set target fix date
- [ ] Re-run smoke tests after fixes
- [ ] Update this results document with re-test results

---

## Sign-Off

**Tester:** _____________________
**Signature:** _____________________
**Date:** _____________________

**QA Lead:** _____________________
**Signature:** _____________________
**Date:** _____________________

**Product Owner:** _____________________
**Signature:** _____________________
**Date:** _____________________

**DevOps Lead:** _____________________
**Signature:** _____________________
**Date:** _____________________

---

## Evidence Archive

**Archive Location:** `docs/deployment/evidence/STORY-165-staging-YYYY-MM-DD/`

**Files Included:**

### Screenshots (PNG)
- [ ] P0-1-api-me-response.png
- [ ] P0-2-free-trial-7day-success.png
- [ ] P0-3-free-trial-30day-blocked.png
- [ ] P0-4-consultor-quota-counter.png
- [ ] P0-5-consultor-excel-locked.png
- [ ] P0-5-upgrade-modal.png
- [ ] P0-6-consultor-30day-success.png
- [ ] P0-7-maquina-excel-export.png
- [ ] P0-8-maquina-1year-search.png
- [ ] P0-9-sala-guerra-full-caps.png
- [ ] P0-10-quota-exhausted.png
- [ ] P0-10-error-dialog.png
- [ ] (P1 and P2 screenshots)

### Excel Files
- [ ] P0-7-sample-export.xlsx

### API Responses (JSON)
- [ ] P1-6-api-responses.json

### Logs
- [ ] P2-2-backend-logs.txt
- [ ] P2-5-performance-metrics.txt

### Additional
- [ ] This completed results document (PDF export)
- [ ] Test data setup SQL scripts
- [ ] Browser console logs (if errors found)

**Archive Created By:** _____________________
**Date:** _____________________

---

**Document Version:** 1.0
**Last Updated:** February 4, 2026
**Template Source:** `docs/deployment/staging-smoke-test-results-template.md`
