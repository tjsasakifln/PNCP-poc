# STORY-165 Staging Smoke Test Documentation

**Story:** PNCP-165 - Plan Restructuring - 3 Paid Tiers + FREE Trial
**Version:** 1.0
**Created:** February 4, 2026
**Status:** Ready for Execution

---

## Overview

This directory contains comprehensive staging smoke test documentation for STORY-165. These tests validate the new 4-tier pricing model (FREE Trial, Consultor Ágil, Máquina, Sala de Guerra) before production deployment.

**Test Scope:** 22 tests across 3 priority levels (P0, P1, P2)
**Estimated Duration:** 2.5 hours
**Environment:** Staging
**Feature Flag:** `ENABLE_NEW_PRICING=true`

---

## Documentation Index

### 1. Execution Plan (START HERE)

**File:** `staging-smoke-test-execution-plan.md`

**Purpose:** Master execution plan coordinating all test activities

**Contains:**
- Pre-execution checklist
- Test execution order (7 phases)
- Test execution matrix
- Pass criteria and GO/NO-GO decision matrix
- Roles and responsibilities
- Communication plan
- Risk mitigation strategies

**Who uses this:** QA Lead, Test Coordinator

---

### 2. Test Data Setup Guide

**File:** `staging-test-data-setup.md`

**Purpose:** Step-by-step guide to create test users and data in Supabase staging

**Contains:**
- 8 test user specifications
- SQL scripts for user creation
- SQL scripts for quota records
- Authentication setup (Supabase Auth)
- Verification queries
- Sample search parameters
- Cleanup procedures

**Who uses this:** DevOps, QA Tester (before testing)

---

### 3. Smoke Test Checklist

**File:** `staging-smoke-test-checklist.md`

**Purpose:** Detailed test cases with step-by-step instructions

**Contains:**
- 22 executable test cases with checkboxes
- Test steps with expected results
- Evidence collection points (screenshots, logs)
- Pass criteria for each test
- Sign-off section

**Who uses this:** QA Tester (during testing)

---

### 4. Smoke Test Results Template

**File:** `staging-smoke-test-results-template.md`

**Purpose:** Template for recording test results and evidence

**Contains:**
- Test execution summary
- Results recording for all 22 tests
- Issue tracking section
- GO/NO-GO decision matrix
- Sign-off section
- Evidence archive checklist

**Who uses this:** QA Tester (during/after testing), QA Lead (sign-off)

---

### 5. Original Smoke Test Specification

**File:** `smoke-tests-story165.md`

**Purpose:** Original test specification defining critical user flows

**Contains:**
- 14 original test flows
- Data validation tests
- Performance tests
- Error handling tests
- Manual testing checklist

**Who uses this:** Reference document (basis for other docs)

---

## Quick Start Guide

### For QA Lead

1. **Pre-Test (1 day before):**
   - [ ] Review `staging-smoke-test-execution-plan.md`
   - [ ] Assign tester and backup tester
   - [ ] Coordinate with DevOps for environment setup
   - [ ] Verify staging deployment complete
   - [ ] Create evidence folder: `evidence/STORY-165-staging-[DATE]/`

2. **Test Day:**
   - [ ] Verify environment health (Phase 1)
   - [ ] Monitor tester progress (check-in every hour)
   - [ ] Review issues as they're found
   - [ ] Escalate blockers immediately

3. **Post-Test (same day):**
   - [ ] Review completed `staging-smoke-test-results-template.md`
   - [ ] Verify evidence collected
   - [ ] Calculate pass rates
   - [ ] Make GO/NO-GO decision
   - [ ] Sign off on results

---

### For QA Tester

1. **Setup (1-2 hours before testing):**
   - [ ] Follow `staging-test-data-setup.md` to create test users
   - [ ] Verify all 8 test users can log in
   - [ ] Open `staging-smoke-test-checklist.md` for execution
   - [ ] Open `staging-smoke-test-results-template.md` for recording
   - [ ] Set up screenshot tool
   - [ ] Create evidence folder

2. **Testing (2.5 hours):**
   - [ ] Follow `staging-smoke-test-execution-plan.md` phases 1-7
   - [ ] Check boxes in `staging-smoke-test-checklist.md` as you go
   - [ ] Record results in `staging-smoke-test-results-template.md`
   - [ ] Collect screenshots for every test
   - [ ] Note any issues immediately

3. **Wrap-Up (30 minutes):**
   - [ ] Complete results template
   - [ ] Archive all evidence
   - [ ] Calculate pass rates
   - [ ] Recommend GO/NO-GO decision
   - [ ] Submit to QA Lead for sign-off

---

### For DevOps

1. **Environment Preparation:**
   - [ ] Deploy backend to staging (Railway/hosting)
   - [ ] Deploy frontend to staging (Vercel/hosting)
   - [ ] Set `ENABLE_NEW_PRICING=true` in environment
   - [ ] Verify Supabase staging database accessible
   - [ ] Provide staging URLs to QA team

2. **Test Data Setup:**
   - [ ] Follow `staging-test-data-setup.md` SQL scripts
   - [ ] Create 8 test users in Supabase
   - [ ] Verify authentication works

3. **Post-Test:**
   - [ ] Clean up test users (if GO decision made)
   - [ ] Prepare for production deployment
   - [ ] Set up monitoring for phased rollout

---

## Test Coverage Summary

### Priority P0 - CRITICAL (10 tests)

**Must pass 100% for production deployment approval**

| Test ID | Test Name | User | Focus Area |
|---------|-----------|------|------------|
| P0-1 | Authentication & Health Check | Any | System availability |
| P0-2 | FREE Trial - 7-Day Success | free-trial | Basic functionality |
| P0-3 | FREE Trial - 30-Day Block | free-trial | Date range validation |
| P0-4 | Consultor Ágil - Quota Counter | consultor-low | Quota display |
| P0-5 | Consultor Ágil - Excel Locked | consultor-low | Excel gating |
| P0-6 | Consultor Ágil - 30-Day Success | consultor-low | Mid-tier history |
| P0-7 | Máquina - Excel Export | maquina | Excel generation |
| P0-8 | Máquina - 1-Year Search | maquina | Extended history |
| P0-9 | Sala de Guerra - Full Caps | sala-guerra | Top-tier features |
| P0-10 | Quota Exhaustion - 429 Error | consultor-exhausted | Quota enforcement |

---

### Priority P1 - HIGH (7 tests)

**Must pass ≥90% (≥6 of 7) for production approval**

| Test ID | Test Name | User | Focus Area |
|---------|-----------|------|------------|
| P1-1 | Trial Expiration | free-expired | Trial enforcement |
| P1-2 | Plan Badge Click - Upgrade Modal | Any | Upgrade flow |
| P1-3 | Date Range Edge Case - Exact Limit | consultor-edge | Boundary validation |
| P1-4 | Leap Year Edge Case | maquina | Date calculation |
| P1-5 | Rate Limiting - Burst Protection | consultor-rate | Rate limiting |
| P1-6 | Capabilities API Validation | All 4 plans | API correctness |
| P1-7 | Máquina - 2-Year Block | maquina | Upper limit enforcement |

---

### Priority P2 - MEDIUM (5 tests)

**Must pass ≥70% (≥4 of 5) for production approval**

| Test ID | Test Name | Focus Area |
|---------|-----------|------------|
| P2-1 | Quota Counter Color Transitions | UI polish |
| P2-2 | Supabase Quota Failure | Error resilience |
| P2-3 | Invalid Plan ID - Fallback | Edge case handling |
| P2-4 | Feature Flag Disable - Rollback | Deployment safety |
| P2-5 | Quota Check Performance | Performance |

---

## GO/NO-GO Decision Criteria

### GO Decision (Production Deployment Approved)

All of the following must be true:

1. ✅ **P0 Tests:** 10/10 passed (100%)
2. ✅ **P1 Tests:** ≥6/7 passed (≥90%)
3. ✅ **P2 Tests:** ≥4/5 passed (≥70%)
4. ✅ **No BLOCKER issues** found
5. ✅ **All evidence collected** and archived
6. ✅ **Sign-off** from QA Lead, Product Owner, DevOps

**Next Steps:**
- Update STORY-165 status: "Ready for Production"
- Schedule production deployment (phased rollout: 10% → 50% → 100%)
- Prepare production smoke tests (subset of staging tests)
- Set up monitoring and alerting

---

### NO-GO Decision (Fix Blockers First)

If any of the following are true:

1. ❌ **P0 Tests:** <10/10 passed
2. ❌ **P1 Tests:** <6/7 passed
3. ❌ **Any BLOCKER issues** found
4. ❌ **Missing critical evidence**

**Next Steps:**
- Create GitHub issues for all blockers
- Assign to responsible developers
- Set target fix dates
- Re-run smoke tests after fixes
- Update stakeholders with new timeline

---

## Evidence Collection Requirements

For each test, collect and archive:

### Screenshots (PNG format)

**P0 Tests (10 screenshots minimum):**
- P0-1: `/api/me` response
- P0-2: FREE trial 7-day success
- P0-3: FREE trial 30-day blocked
- P0-4: Consultor quota counter
- P0-5: Consultor Excel locked + upgrade modal
- P0-6: Consultor 30-day success
- P0-7: Máquina Excel export
- P0-8: Máquina 1-year search
- P0-9: Sala de Guerra full capabilities
- P0-10: Quota exhausted error

**P1 Tests (7 screenshots minimum)**
**P2 Tests (5 screenshots minimum)**

### API Responses (JSON format)

- `/api/me` for all 4 plan types
- Search responses (success and error cases)

### Logs (TXT format)

- Backend logs (quota checks, validation errors)
- Performance metrics (if P2-5 executed)

### Excel Files

- Sample export from Máquina user (P0-7)

**Archive Location:** `docs/deployment/evidence/STORY-165-staging-[DATE]/`

---

## Issue Tracking

### Severity Definitions

**BLOCKER:**
- Prevents testing from continuing
- Prevents production deployment
- Examples: System crash, authentication broken, all searches fail

**CRITICAL:**
- Major functionality broken
- Affects multiple users/flows
- Examples: Quota not enforcing, Excel not generating, wrong plan displayed

**MAJOR:**
- Important functionality affected
- Workaround available
- Examples: UI glitch, incorrect tooltip, slow response time

**MINOR:**
- Cosmetic or low-impact issue
- Examples: Typo, color mismatch, alignment issue

### Issue Template

**For each issue found:**
1. Record in `staging-smoke-test-results-template.md` Issue section
2. Create GitHub issue with label `story-165`
3. Assign to responsible team (backend/frontend/devops)
4. Set severity and target fix date
5. Link to test evidence (screenshot/log)

---

## Contact Information

### Team Contacts

**QA Lead:** ___________________
**Tester:** ___________________
**Product Owner:** ___________________
**Backend Dev:** ___________________
**Frontend Dev:** ___________________
**DevOps:** ___________________

### Escalation Path

1. **First Contact:** QA Lead
2. **If Blocked:** Product Owner + DevOps
3. **If Critical:** All stakeholders + immediate standup

---

## Timeline

### Test Execution Schedule

**Day 1 (Setup):**
- DevOps deploys to staging
- DevOps creates test users
- QA verifies environment health

**Day 2 (Testing):**
- Morning: Phases 1-3 (P0 tests)
- Afternoon: Phases 4-7 (P1/P2 tests)
- End of day: Results compiled, GO/NO-GO decision

**Day 3 (Follow-Up):**
- If GO: Production deployment planning
- If NO-GO: Issue assignment and re-test scheduling

---

## Lessons Learned (Post-Test)

**Document after testing completes:**

### What Went Well
- _____________________________________________________________________________
- _____________________________________________________________________________

### What Could Be Improved
- _____________________________________________________________________________
- _____________________________________________________________________________

### Blockers Encountered
- _____________________________________________________________________________
- _____________________________________________________________________________

### Recommendations for Production Testing
- _____________________________________________________________________________
- _____________________________________________________________________________

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | @qa (Quincy) | Initial documentation created |

---

## Related Documentation

### Story & Requirements
- `docs/stories/STORY-165-plan-restructuring.md` - Story with acceptance criteria
- `docs/ux/STORY-165-plan-ui-design.md` - UX design specifications

### Architecture
- `backend/quota.py` - Plan capabilities implementation
- `frontend/components/PlanBadge.tsx` - Plan badge component
- `frontend/components/QuotaCounter.tsx` - Quota counter component

### Test Code
- `backend/tests/test_plan_capabilities.py` - Backend plan tests (25 tests)
- `frontend/__tests__/PlanBadge.test.tsx` - Frontend plan badge tests (21 tests)
- `frontend/__tests__/QuotaCounter.test.tsx` - Frontend quota tests (16 tests)
- `frontend/__tests__/UpgradeModal.test.tsx` - Frontend upgrade modal tests (26 tests)

---

## Appendix: Quick Reference

### Test User Matrix

| User Email | Plan | Password | Quota | Trial Status | Use For |
|------------|------|----------|-------|--------------|---------|
| free-trial@smartpncp.test | free_trial | TestPass123! | N/A | 3 days left | P0-2, P0-3 |
| free-expired@smartpncp.test | free_trial | TestPass123! | N/A | EXPIRED | P1-1 |
| consultor-low@smartpncp.test | consultor_agil | TestPass123! | 23/50 | N/A | P0-4, P0-5, P0-6 |
| consultor-exhausted@smartpncp.test | consultor_agil | TestPass123! | 50/50 | N/A | P0-10 |
| consultor-edge@smartpncp.test | consultor_agil | TestPass123! | 30/50 | N/A | P1-3, P2-1 |
| consultor-rate@smartpncp.test | consultor_agil | TestPass123! | 5/50 | N/A | P1-5 |
| maquina@smartpncp.test | maquina | TestPass123! | 150/300 | N/A | P0-7, P0-8, P1-4, P1-7 |
| sala-guerra@smartpncp.test | sala_guerra | TestPass123! | 50/1000 | N/A | P0-9 |

### Plan Capabilities Reference

| Capability | FREE Trial | Consultor Ágil | Máquina | Sala de Guerra |
|------------|------------|----------------|---------|----------------|
| **Max History** | 7 days | 30 days | 365 days | 1825 days (5 years) |
| **Excel Export** | ❌ | ❌ | ✅ | ✅ |
| **Monthly Quota** | Unlimited | 50 | 300 | 1000 |
| **Rate Limit** | 2 req/min | 10 req/min | 30 req/min | 60 req/min |
| **Summary Tokens** | 200 | 200 | 500 | 1000 |
| **Priority** | Low | Normal | High | Critical |
| **Price** | R$ 0 (7 days) | R$ 297/mês | R$ 597/mês | R$ 1497/mês |

---

**Documentation Owner:** @qa (Quincy)
**Last Updated:** February 4, 2026
**Status:** Ready for Execution

---

**Sign-Off:**

I have reviewed this documentation and confirm it is ready for staging smoke test execution:

**QA Lead:** _____________________ **Date:** _____
**Product Owner:** _____________________ **Date:** _____
**DevOps Lead:** _____________________ **Date:** _____
