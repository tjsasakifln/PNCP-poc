# Staging Smoke Test Execution Plan - STORY-165

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Created:** February 4, 2026

---

## Overview

This document provides a comprehensive execution plan for staging smoke tests for STORY-165. It coordinates all test documentation and ensures systematic validation before production deployment.

---

## Pre-Execution Checklist

### 1. Environment Readiness

- [ ] Staging environment accessible
- [ ] Feature flag `ENABLE_NEW_PRICING=true` enabled
- [ ] Backend deployed to staging (Railway/hosting platform)
- [ ] Frontend deployed to staging (Vercel/hosting platform)
- [ ] Supabase staging database accessible
- [ ] API endpoints responding (health check)

### 2. Test Data Preparation

- [ ] Follow `staging-test-data-setup.md`
- [ ] Create all 8 test users in Supabase
- [ ] Set up quota records
- [ ] Verify authentication works
- [ ] Test users can log in to staging frontend

### 3. Testing Tools

- [ ] Browser with DevTools (Chrome/Firefox recommended)
- [ ] Screenshot tool ready (Snagit, Greenshot, or built-in)
- [ ] Network monitoring enabled
- [ ] Text editor for notes
- [ ] API testing tool (Postman/cURL) for `/api/me` checks

### 4. Documentation

- [ ] Print or open `staging-smoke-test-checklist.md`
- [ ] Open `staging-smoke-test-results-template.md` for recording
- [ ] Create evidence folder: `docs/deployment/evidence/STORY-165-staging-[DATE]/`

---

## Test Execution Order

Execute tests in this specific order to maximize efficiency and dependency management.

### Phase 1: Sanity Checks (15 minutes)

**Purpose:** Verify basic system health before detailed testing

#### 1.1 Environment Health
- [ ] Navigate to staging URL
- [ ] Verify frontend loads (no 500 errors)
- [ ] Check feature flag status in DevTools console
- [ ] Test backend health endpoint (if available)

#### 1.2 Authentication
- [ ] Test login with any user
- [ ] Verify redirect to dashboard
- [ ] Check browser console for errors
- [ ] Verify session persistence

#### 1.3 API Baseline
- [ ] Call `GET /api/me` for each plan type
- [ ] Verify all capabilities fields present
- [ ] Save JSON responses for P1-6 test

**Deliverable:** Phase 1 sign-off (all sanity checks pass)

---

### Phase 2: FREE Trial Flow (20 minutes)

**Purpose:** Validate FREE trial restrictions and upgrade prompts

**Test User:** `free-trial@smartpncp.test`

#### 2.1 Success Case (P0-2)
1. Log in as FREE trial user
2. Verify plan badge: "FREE Trial" + countdown
3. Select UF: SP, Date range: Last 7 days
4. Execute search
5. Verify results displayed
6. Verify Excel button locked
7. **Screenshot:** Save results page

#### 2.2 Block Case (P0-3)
1. Select date range: Last 30 days
2. Verify validation error appears
3. Verify search button disabled
4. Verify upgrade CTA points to "Consultor Ágil"
5. **Screenshot:** Save error state

#### 2.3 Trial Expiration (P1-1)
1. Log out and log in as `free-expired@smartpncp.test`
2. Verify expired trial indicator
3. Attempt search
4. Verify 403 error with upgrade prompt
5. **Screenshot:** Save error dialog

**Deliverable:** FREE trial tests complete (3 tests: P0-2, P0-3, P1-1)

---

### Phase 3: Consultor Ágil Flow (30 minutes)

**Purpose:** Validate mid-tier plan with quota tracking and Excel restrictions

**Test User:** `consultor-low@smartpncp.test` (23/50 quota)

#### 3.1 Quota Counter (P0-4)
1. Log in as Consultor Ágil user
2. Verify plan badge: "Consultor Ágil" (blue)
3. Verify quota counter: "23/50"
4. Verify progress bar color: green
5. Hover for reset date tooltip
6. **Screenshot:** Save quota counter

#### 3.2 Excel Locked (P0-5)
1. Execute search (7-day range, UF: SP)
2. Verify results displayed
3. Verify Excel button locked
4. Hover for tooltip: "Exportar Excel disponível no plano Máquina"
5. Click locked button
6. Verify upgrade modal opens with Máquina pre-selected
7. **Screenshot:** Save upgrade modal

#### 3.3 30-Day Search (P0-6)
1. Select date range: Last 30 days
2. Execute search
3. Verify search succeeds (HTTP 200)
4. Verify quota counter updates to 24/50
5. **Screenshot:** Save updated quota

#### 3.4 Edge Case - Exact Limit (P1-3)
1. Test 30-day search (should succeed)
2. Test 31-day search (should fail with validation error)
3. **Screenshot:** Save both scenarios

#### 3.5 Quota Exhaustion (P0-10)
1. Log out and log in as `consultor-exhausted@smartpncp.test`
2. Verify quota counter: "50/50" (red)
3. Attempt search
4. Verify 429 error with reset date
5. Click upgrade button
6. Verify upgrade modal opens
7. **Screenshot:** Save error dialog

#### 3.6 Rate Limiting (P1-5)
1. Log out and log in as `consultor-rate@smartpncp.test`
2. Execute 10 searches rapidly (<60 seconds)
3. Verify all 10 succeed
4. Execute 11th search immediately
5. Verify 429 error with `Retry-After` header
6. Wait 60 seconds, retry
7. Verify search succeeds after waiting
8. **Screenshot:** Save rate limit error

**Deliverable:** Consultor Ágil tests complete (6 tests: P0-4, P0-5, P0-6, P0-10, P1-3, P1-5)

---

### Phase 4: Máquina Flow (25 minutes)

**Purpose:** Validate Excel export functionality and extended history

**Test User:** `maquina@smartpncp.test` (150/300 quota)

#### 4.1 Excel Export (P0-7)
1. Log in as Máquina user
2. Verify plan badge: "Máquina" (green)
3. Execute search (30-day range, UF: SP)
4. Verify Excel button unlocked (no lock icon)
5. Click Excel export
6. Verify Excel file downloads
7. Open Excel file and verify data
8. **Screenshot:** Save Excel preview
9. **Save file:** evidence/P0-7-sample-export.xlsx

#### 4.2 1-Year Search (P0-8)
1. Select date range: Last 365 days
2. Execute search
3. Verify search succeeds
4. Verify quota counter: "151/300" (yellow at 50%)
5. **Screenshot:** Save quota counter at 50%

#### 4.3 2-Year Block (P1-7)
1. Select date range: Last 730 days (2 years)
2. Verify validation error
3. Verify upgrade suggestion: "Sala de Guerra"
4. **Screenshot:** Save validation error

#### 4.4 Leap Year Edge Case (P1-4)
1. Select date range: Feb 28, 2024 to Feb 29, 2025 (366 days)
2. Verify validation error (exceeds 365-day limit)
3. Select date range: Mar 1, 2024 to Feb 29, 2025 (365 days)
4. Verify validation passes
5. **Screenshot:** Save both tests

**Deliverable:** Máquina tests complete (4 tests: P0-7, P0-8, P1-7, P1-4)

---

### Phase 5: Sala de Guerra Flow (15 minutes)

**Purpose:** Validate top-tier plan with full capabilities

**Test User:** `sala-guerra@smartpncp.test` (50/1000 quota)

#### 5.1 Full Capabilities (P0-9)
1. Log in as Sala de Guerra user
2. Verify plan badge: "Sala de Guerra" (gold)
3. Verify quota counter: "50/1000" (green, 5%)
4. Select date range: Last 1825 days (5 years)
5. Execute search
6. Verify search succeeds
7. Click Excel export
8. Verify Excel downloads
9. Check AI summary length (should be comprehensive)
10. **Screenshot:** Save results with AI summary

**Deliverable:** Sala de Guerra test complete (1 test: P0-9)

---

### Phase 6: UX & Integration Tests (20 minutes)

**Purpose:** Validate upgrade flows and plan comparison UI

#### 6.1 Plan Badge Click (P1-2)
1. Log in as any non-Sala de Guerra user
2. Click plan badge in header
3. Verify upgrade modal opens
4. Verify all 4 plans displayed
5. Verify current plan highlighted
6. Verify pricing shown (R$ 297, R$ 597, R$ 1497)
7. Verify key differentiators (history, Excel, quota)
8. Click CTA for higher plan
9. Verify redirect to payment/checkout
10. **Screenshot:** Save upgrade modal

#### 6.2 Capabilities API (P1-6)
1. Already completed in Phase 1 (API Baseline)
2. Verify all JSON responses saved
3. Validate all fields match `PLAN_CAPABILITIES`

**Deliverable:** UX tests complete (2 tests: P1-2, P1-6)

---

### Phase 7: Edge Cases & Error Handling (30 minutes)

**Purpose:** Validate graceful degradation and edge cases

#### 7.1 Quota Color Transitions (P2-1)
1. Log in as `consultor-edge@smartpncp.test` (30/50 = 60%)
2. Verify progress bar green
3. Create users for 80% and 96% quota (or use SQL to update)
4. Verify progress bar yellow at 80%
5. Verify progress bar red at 96%
6. **Screenshot:** Save all 3 color states

#### 7.2 Supabase Quota Failure (P2-2) [OPTIONAL]
1. Simulate Supabase quota table unavailable
2. Execute search
3. Verify search proceeds with fallback
4. Check backend logs for warning
5. **Screenshot:** Save successful search
6. **Save logs:** evidence/P2-2-backend-logs.txt

#### 7.3 Invalid Plan ID (P2-3) [OPTIONAL]
1. Create user with invalid plan_id in database
2. Execute search
3. Verify system defaults to free_trial
4. Verify 7-day limit enforced
5. Check logs for warning
6. **Screenshot:** Save behavior

#### 7.4 Feature Flag Rollback (P2-4) [OPTIONAL]
1. Set `ENABLE_NEW_PRICING=false`
2. Restart application
3. Verify old behavior or graceful degradation
4. Re-enable flag
5. Restart application
6. Verify new behavior returns
7. **Screenshot:** Save both states

#### 7.5 Performance Test (P2-5) [OPTIONAL]
1. Execute search and measure response time
2. Verify total time <3 seconds
3. Check backend logs for quota check duration (<200ms)
4. Execute 100 sequential searches
5. Verify no performance degradation
6. **Save logs:** evidence/P2-5-performance-metrics.txt

**Deliverable:** Edge case tests complete (5 tests: P2-1 through P2-5)

---

## Test Execution Matrix

| Phase | Tests | Priority | Estimated Time | Tester | Status |
|-------|-------|----------|----------------|--------|--------|
| 1. Sanity Checks | Environment + Auth + API | P0 | 15 min | _____ | [ ] |
| 2. FREE Trial | P0-2, P0-3, P1-1 | P0, P1 | 20 min | _____ | [ ] |
| 3. Consultor Ágil | P0-4, P0-5, P0-6, P0-10, P1-3, P1-5 | P0, P1 | 30 min | _____ | [ ] |
| 4. Máquina | P0-7, P0-8, P1-7, P1-4 | P0, P1 | 25 min | _____ | [ ] |
| 5. Sala de Guerra | P0-9 | P0 | 15 min | _____ | [ ] |
| 6. UX & Integration | P1-2, P1-6 | P1 | 20 min | _____ | [ ] |
| 7. Edge Cases | P2-1 through P2-5 | P2 | 30 min | _____ | [ ] |
| **TOTAL** | **22 tests** | - | **~2.5 hours** | - | - |

---

## Pass Criteria

### Go/No-Go Decision Matrix

| Condition | Threshold | Status | GO/NO-GO |
|-----------|-----------|--------|----------|
| **P0 Tests (Critical)** | 100% pass (10/10) | _____% | [ ] GO / [ ] NO-GO |
| **P1 Tests (High)** | ≥90% pass (≥6/7) | _____% | [ ] GO / [ ] NO-GO |
| **P2 Tests (Medium)** | ≥70% pass (≥4/5) | _____% | [ ] GO / [ ] NO-GO |
| **No BLOCKER issues** | 0 blockers | _____ blockers | [ ] GO / [ ] NO-GO |
| **Evidence collected** | 100% complete | _____% | [ ] GO / [ ] NO-GO |

**Final Decision:** [ ] **GO FOR PRODUCTION** / [ ] **NO-GO - FIX BLOCKERS**

---

## Roles & Responsibilities

| Role | Responsibility | Name | Contact |
|------|----------------|------|---------|
| **QA Lead** | Overall test coordination, sign-off | _____ | _____ |
| **Tester** | Execute smoke tests, collect evidence | _____ | _____ |
| **Product Owner** | Acceptance criteria validation | _____ | _____ |
| **Backend Dev** | Fix backend issues if found | _____ | _____ |
| **Frontend Dev** | Fix frontend issues if found | _____ | _____ |
| **DevOps** | Environment setup, deployment | _____ | _____ |

---

## Communication Plan

### Daily Standup (During Testing)

**Time:** _____
**Platform:** Slack / Teams / Email
**Updates:**
- Tests completed today
- Tests planned for today
- Blockers found
- ETA for completion

### Issue Escalation

**BLOCKER issues:**
1. Immediately notify Product Owner + DevOps
2. Create GitHub issue with label `blocker`
3. Assign to responsible developer
4. Pause testing until resolved

**CRITICAL issues:**
1. Complete current test phase
2. Document issue in results template
3. Notify QA Lead
4. Continue testing, revisit after fix

**MAJOR/MINOR issues:**
1. Document in results template
2. Continue testing
3. Review in retrospective

---

## Post-Execution Activities

### Immediate (Same Day)

- [ ] Complete `staging-smoke-test-results-template.md`
- [ ] Archive all evidence to `docs/deployment/evidence/STORY-165-staging-[DATE]/`
- [ ] Calculate pass rates (P0, P1, P2)
- [ ] Make GO/NO-GO decision
- [ ] Notify stakeholders of decision

### If GO

- [ ] Update STORY-165 status: "Ready for Production"
- [ ] Schedule production deployment
- [ ] Prepare production smoke test plan (subset of staging tests)
- [ ] Plan phased rollout: 10% → 50% → 100%
- [ ] Set up monitoring alerts for production

### If NO-GO

- [ ] Create GitHub issues for all blockers
- [ ] Assign issues to developers
- [ ] Set target fix dates
- [ ] Schedule re-test after fixes
- [ ] Update stakeholders with new timeline

### Cleanup

- [ ] Delete test users from staging (see `staging-test-data-setup.md` Step 7)
- [ ] Reset feature flag if needed
- [ ] Archive test documentation
- [ ] Document lessons learned

---

## Risk Mitigation

### Risk: Staging environment unstable

**Mitigation:**
- Verify health checks before starting
- Have backup staging environment ready
- Contact DevOps immediately if issues

### Risk: Test data incomplete

**Mitigation:**
- Follow `staging-test-data-setup.md` exactly
- Verify all users created before testing
- Have SQL scripts ready for quick reset

### Risk: Time overrun

**Mitigation:**
- Prioritize P0 tests first
- Skip P2 tests if time constrained
- Focus on GO/NO-GO decision criteria

### Risk: Tester unavailable

**Mitigation:**
- Have backup tester assigned
- Document tests clearly for easy handoff
- Use checklist format (anyone can execute)

---

## Reference Documents

1. **Test Checklist:** `staging-smoke-test-checklist.md`
2. **Test Data Setup:** `staging-test-data-setup.md`
3. **Results Template:** `staging-smoke-test-results-template.md`
4. **Smoke Test Specification:** `smoke-tests-story165.md`
5. **Story:** `docs/stories/STORY-165-plan-restructuring.md`

---

## Appendix: Quick Reference

### Test User Credentials

| Email | Password | Plan | Quota |
|-------|----------|------|-------|
| `free-trial@smartpncp.test` | `TestPass123!` | FREE Trial | N/A |
| `free-expired@smartpncp.test` | `TestPass123!` | FREE (expired) | N/A |
| `consultor-low@smartpncp.test` | `TestPass123!` | Consultor Ágil | 23/50 |
| `consultor-exhausted@smartpncp.test` | `TestPass123!` | Consultor Ágil | 50/50 |
| `maquina@smartpncp.test` | `TestPass123!` | Máquina | 150/300 |
| `sala-guerra@smartpncp.test` | `TestPass123!` | Sala de Guerra | 50/1000 |

### Sample Search Parameters

- **UF:** SP (São Paulo)
- **Date Range (7 days):** Last 7 days from today
- **Date Range (30 days):** Last 30 days from today
- **Date Range (365 days):** Last 365 days from today
- **Date Range (1825 days):** Last 1825 days from today

### Expected HTTP Status Codes

- **200:** Success (search allowed)
- **403:** Forbidden (date range/trial expired)
- **429:** Too Many Requests (quota exhausted or rate limited)

### Plan Capabilities Quick Reference

| Plan | History | Excel | Monthly Quota | Rate Limit | Summary Tokens |
|------|---------|-------|---------------|------------|----------------|
| FREE Trial | 7 days | ❌ | Unlimited | 2 req/min | 200 |
| Consultor Ágil | 30 days | ❌ | 50 | 10 req/min | 200 |
| Máquina | 365 days | ✅ | 300 | 30 req/min | 500 |
| Sala de Guerra | 1825 days | ✅ | 1000 | 60 req/min | 1000 |

---

**Execution Plan Version:** 1.0
**Last Updated:** February 4, 2026
**Owner:** QA Team (@qa / Quincy)
**Approval Required:** Product Owner, QA Lead, DevOps

---

**Sign-Off:**

**QA Lead:** _____________________ **Date:** _____
**Product Owner:** _____________________ **Date:** _____
**DevOps:** _____________________ **Date:** _____
