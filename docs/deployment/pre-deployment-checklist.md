# Pre-Deployment Checklist - Phase 4 Production Deployment

**Project:** BidIQ Uniformes - Value Sprint 01
**Target Date:** Day 13 (2026-01-30)
**Deployment Type:** Blue-Green Deployment to Production
**Platforms:** Vercel (Frontend) + Railway (Backend)
**DevOps Lead:** @devops

---

## Executive Summary

This checklist ensures all pre-deployment requirements are met before executing the blue-green production deployment. It consolidates validation from QA testing, infrastructure readiness, environment configuration, and rollback preparedness.

**Status:** ⏳ **PENDING** - Awaiting completion of Tasks #2-4
- Task #2: Run smoke tests in staging ⏳
- Task #3: Fix final bugs and polish features ⏳
- Task #4: Update final documentation ⏳

---

## Section 1: QA Sign-off Validation

### 1.1 Test Results Review

- [ ] **Phase 3 Test Report reviewed**
  - Document: `docs/testing/phase3-test-report.md`
  - Status: ✅ QA APPROVED FOR STAGING DEPLOYMENT
  - Overall test pass rate: 98% (346/353 tests passing)

- [ ] **P0/P1 Bugs Status**
  - P0 Bugs (Critical): **0** ✅
  - P1 Bugs (High): **0** ✅
  - P2 Bugs (Medium): **7** (deferred to Week 2)
  - **Decision:** ✅ No blocking bugs

- [ ] **Code Coverage Validation**
  - Backend Coverage: **96.69%** ✅ (Target: ≥70%)
  - Frontend Coverage: **49.61%** ⚠️ (Target: ≥60%)
  - **Decision:** ✅ Accepted with justification (all critical paths tested)

### 1.2 Feature Completeness

- [ ] **MUST HAVE Features (Phase 3)**
  - ✅ Feature #2: EnhancedLoadingProgress (76% test coverage, manual validation ✅)
  - ✅ Feature #3: Interactive Onboarding (90% test coverage, core functional ✅)
  - ✅ Feature #1: Analytics (100% test coverage, completed Phase 2 ✅)
  - ✅ Saved Searches (100% test coverage, completed Phase 2 ✅)

- [ ] **Regression Testing**
  - ✅ All Phase 1-2 features working (no regressions)
  - ✅ Search flow validated
  - ✅ Results display functional
  - ✅ Excel download operational

### 1.3 Performance Benchmarks

- [ ] **Lighthouse CI Benchmarks**
  - Desktop Performance: **92/100** ✅ (Target: ≥70)
  - Mobile Performance: **78/100** ✅ (Target: ≥70)
  - Accessibility: **95/100** ✅ (Target: ≥90)
  - Best Practices: **88/100** ✅ (Target: ≥80)
  - SEO: **91-92/100** ✅ (Target: ≥70)

- [ ] **Search Performance**
  - 1 state: 5.8s ✅ (Target: ~6s)
  - 3 states: 17.2s ✅ (Target: ~18s)
  - 10 states: 58.4s ✅ (Target: ~60s)
  - 27 states: 165.1s ✅ (Target: ~162s, +1.9% tolerance)

### 1.4 Accessibility & Compatibility

- [ ] **WCAG 2.1 AA Compliance**
  - axe-core violations: **0 critical** ✅
  - Warnings: **2 minor** (non-blocking)
  - Keyboard navigation: ✅ Full support
  - Screen reader testing: ✅ NVDA + VoiceOver validated

- [ ] **Cross-Browser Testing**
  - ✅ Chrome 131 (Windows)
  - ✅ Firefox 115 (Windows)
  - ✅ Safari 17 (macOS)
  - ✅ Edge 131 (Windows)
  - ✅ Chrome Mobile 96 (Android)
  - ✅ Safari Mobile 15 (iOS)

**Section 1 Status:** ⏳ PENDING QA Final Approval

---

## Section 2: Infrastructure Readiness

### 2.1 Backend (Railway)

- [ ] **Railway Project Configuration**
  - [ ] Project created: `bidiq-backend`
  - [ ] Region selected: `us-west1` (or closest to users)
  - [ ] Root directory configured: `/backend`
  - [ ] Service type: Dockerfile deployment
  - [ ] Builder setting: `DOCKERFILE`

- [ ] **Environment Variables Configured**
  ```
  Required Variables:
  - OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx (Production key, NOT dev key)
  - PORT=8000
  - LOG_LEVEL=INFO
  - PNCP_TIMEOUT=30
  - PNCP_MAX_RETRIES=5
  - PNCP_BACKOFF_BASE=2
  - PNCP_BACKOFF_MAX=60
  - LLM_MODEL=gpt-4o-mini
  - LLM_TEMPERATURE=0.3
  - LLM_MAX_TOKENS=500
  ```
  - [ ] All variables set in Railway dashboard
  - [ ] OPENAI_API_KEY is **production** key (not dev)
  - [ ] No typos in variable names
  - [ ] No trailing spaces in values

- [ ] **Railway Health Check**
  - [ ] Health endpoint configured: `/health`
  - [ ] Expected response: `{"status":"healthy","timestamp":"..."}`
  - [ ] Timeout: 30 seconds
  - [ ] Interval: 60 seconds
  - [ ] Retries: 3

- [ ] **Railway Deployment URL**
  - [ ] Domain generated: `https://bidiq-backend-production.up.railway.app`
  - [ ] Custom domain (if any): ___________________
  - [ ] HTTPS certificate valid

### 2.2 Frontend (Vercel)

- [ ] **Vercel Project Configuration**
  - [ ] Project created: `bidiq-uniformes`
  - [ ] Framework: Next.js (auto-detected)
  - [ ] Root directory: `/frontend`
  - [ ] Build command: `npm run build`
  - [ ] Output directory: `.next`
  - [ ] Node.js version: 18.x (or latest LTS)

- [ ] **Environment Variables Configured**
  ```
  Required Variables:
  - NEXT_PUBLIC_BACKEND_URL=https://bidiq-backend-production.up.railway.app
  - NEXT_PUBLIC_MIXPANEL_TOKEN=<production-token> (if different from dev)
  ```
  - [ ] NEXT_PUBLIC_BACKEND_URL points to **Railway production URL**
  - [ ] Variables set for **Production** environment
  - [ ] Redeployment triggered after variable changes

- [ ] **Vercel Deployment URL**
  - [ ] Domain generated: `https://bidiq-uniformes.vercel.app`
  - [ ] Custom domain (if any): ___________________
  - [ ] HTTPS certificate valid

### 2.3 CORS Configuration

- [ ] **Backend CORS Settings**
  - File: `backend/main.py`
  - [ ] Vercel domain added to `allow_origins`:
    ```python
    allow_origins=[
        "http://localhost:3000",  # Local dev
        "https://bidiq-uniformes.vercel.app",  # Production
    ]
    ```
  - [ ] Wildcard NOT used (`allow_origins=["*"]` is insecure)
  - [ ] `allow_credentials=True` (for cookies if needed)
  - [ ] `allow_methods=["*"]`
  - [ ] `allow_headers=["*"]`

**Section 2 Status:** ⏳ PENDING Infrastructure Setup

---

## Section 3: Staging Environment Validation

### 3.1 Staging Deployment

- [ ] **Staging Backend Deployed**
  - [ ] Railway staging service exists (or preview environment)
  - [ ] Staging URL: _______________________________
  - [ ] Health check passing: `curl <staging-url>/health`
  - [ ] API docs accessible: `<staging-url>/docs`

- [ ] **Staging Frontend Deployed**
  - [ ] Vercel preview deployment exists
  - [ ] Preview URL: _______________________________
  - [ ] Page loads without errors
  - [ ] Backend connection configured correctly

### 3.2 Staging Smoke Tests (Task #2)

- [ ] **Backend Smoke Tests**
  - [ ] Health endpoint returns 200 OK
  - [ ] API docs load successfully
  - [ ] PNCP API connectivity test (1 state search)
  - [ ] OpenAI API connectivity test (summary generation)
  - [ ] Excel generation functional
  - [ ] Error handling validates (e.g., invalid UF)

- [ ] **Frontend Smoke Tests**
  - [ ] Page loads in <2 seconds
  - [ ] All UI components render
  - [ ] No JavaScript errors in console
  - [ ] Backend API requests successful

- [ ] **Integration Smoke Tests**
  - [ ] End-to-end search flow:
    1. Select UF (e.g., SP)
    2. Click "Buscar Licitações"
    3. Loading progress displays (5 stages)
    4. Results appear with summary
    5. Download button functional
    6. Excel file downloads correctly
  - [ ] Analytics events fire (Mixpanel)
  - [ ] Saved Searches save/load/delete
  - [ ] Onboarding wizard displays for new users

### 3.3 Staging Performance Tests

- [ ] **Lighthouse CI Benchmarks (Staging)**
  - [ ] Desktop Performance: ≥70
  - [ ] Mobile Performance: ≥70
  - [ ] Accessibility: ≥90
  - [ ] Best Practices: ≥80
  - [ ] SEO: ≥70

- [ ] **Load Testing (Optional)**
  - [ ] Concurrent users test: 10 users searching simultaneously
  - [ ] Backend response time: <5s (95th percentile)
  - [ ] Error rate: <1%

**Section 3 Status:** ⏳ PENDING Staging Tests (Task #2)

---

## Section 4: Bug & Polish Validation (Task #3)

### 4.1 Final Bug Fixes

- [ ] **P0 Bugs (Critical - Must Fix)**
  - Current count: **0** ✅
  - [ ] All P0 bugs resolved and tested

- [ ] **P1 Bugs (High - Must Fix)**
  - Current count: **0** ✅
  - [ ] All P1 bugs resolved and tested

- [ ] **P2 Bugs (Medium - Defer to Week 2)**
  - Current count: **7**
  - [ ] P2 bugs documented in backlog
  - [ ] Decision made: Defer to Week 2 cleanup
  - Known P2 bugs:
    1. EnhancedLoadingProgress: Very short time (<1s) flicker
    2. EnhancedLoadingProgress: Very long time (>5min) UI overflow
    3. EnhancedLoadingProgress: State count = 0 displays "0 estados"
    4. useOnboarding: Rapid mount/unmount edge case
    5. useOnboarding: Auto-start fires when dismissed (race condition)
    6. Color contrast warning (4.48:1 on secondary text)
    7. Missing landmark role on footer

### 4.2 Polish & UX Refinements

- [ ] **UI/UX Polish**
  - [ ] Loading states smooth and responsive
  - [ ] Error messages user-friendly
  - [ ] Success messages clear
  - [ ] Animations smooth (no jank)
  - [ ] Dark mode consistent (if applicable)

- [ ] **Content Polish**
  - [ ] All text in Portuguese (BR)
  - [ ] No placeholder text (e.g., "Lorem ipsum")
  - [ ] Help text clear and actionable
  - [ ] Error messages specific and helpful

**Section 4 Status:** ⏳ PENDING Bug Fixes (Task #3)

---

## Section 5: Documentation Validation (Task #4)

### 5.1 User-Facing Documentation

- [ ] **README.md**
  - [ ] Installation instructions accurate
  - [ ] Environment variables documented
  - [ ] Usage examples up-to-date
  - [ ] Links functional (no 404s)

- [ ] **Deployment Guide**
  - File: `docs/DEPLOYMENT.md`
  - [ ] Railway deployment steps accurate
  - [ ] Vercel deployment steps accurate
  - [ ] Environment variables list complete
  - [ ] Troubleshooting section helpful

### 5.2 Developer Documentation

- [ ] **PRD.md**
  - [ ] Feature descriptions match implementation
  - [ ] API contracts accurate
  - [ ] Architecture diagrams current

- [ ] **CLAUDE.md**
  - [ ] Development commands accurate
  - [ ] Testing guidelines updated
  - [ ] Coverage thresholds documented

### 5.3 Operational Documentation

- [ ] **Runbooks Created**
  - [ ] `docs/runbooks/staging-deployment.md`
  - [ ] `docs/runbooks/production-deployment.md`
  - [ ] `docs/runbooks/rollback-procedure.md`
  - [ ] `docs/runbooks/incident-response.md` (optional)

- [ ] **Monitoring Dashboards**
  - [ ] Railway monitoring configured
  - [ ] Vercel analytics enabled
  - [ ] Mixpanel dashboards created (Task #8)
  - [ ] Alert thresholds defined

**Section 5 Status:** ⏳ PENDING Documentation Updates (Task #4)

---

## Section 6: Rollback Preparedness

### 6.1 Rollback Plan

- [ ] **Rollback Procedure Documented**
  - File: `docs/runbooks/rollback-procedure.md`
  - [ ] Railway rollback steps (`railway rollback`)
  - [ ] Vercel rollback steps (`vercel rollback`)
  - [ ] Estimated rollback time: <5 minutes
  - [ ] Rollback success criteria defined

- [ ] **Rollback Dry-Run Tested**
  - [ ] Backend rollback tested in staging
  - [ ] Frontend rollback tested in staging
  - [ ] Full rollback executed successfully (both platforms)
  - [ ] Time to complete rollback: _______ minutes

### 6.2 Rollback Triggers

- [ ] **Automatic Rollback Conditions Defined**
  - [ ] Error rate >5% for 5 minutes
  - [ ] Health check failures >3 consecutive
  - [ ] Response time >10s (95th percentile)
  - [ ] Critical feature unavailable (search, download)

- [ ] **Manual Rollback Decision Authority**
  - Primary: @devops
  - Secondary: @pm or @architect (if @devops unavailable)
  - Communication channel: ___________________

**Section 6 Status:** ⏳ PENDING Rollback Testing

---

## Section 7: Production Readiness

### 7.1 Deployment Window

- [ ] **Deployment Timing**
  - Scheduled date: **Day 13** (2026-01-30)
  - Scheduled time: __________ (low-traffic window recommended)
  - Duration estimate: **30 minutes** (normal) / **90 minutes** (with issues)
  - Rollback window: **2 hours** after deployment

- [ ] **Stakeholder Notification**
  - [ ] Team notified of deployment window
  - [ ] Stakeholders informed (if any)
  - [ ] Support team on standby (if applicable)

### 7.2 Blue-Green Deployment Strategy

- [ ] **Green Environment Prepared**
  - [ ] Railway: New deployment created (green)
  - [ ] Vercel: New deployment created (green)
  - [ ] Green environment health checks passing
  - [ ] Green environment smoke tests passing

- [ ] **Traffic Cutover Plan**
  - [ ] Initial: 0% traffic to green (100% to blue/current)
  - [ ] Step 1: 10% traffic to green (monitor 5 min)
  - [ ] Step 2: 50% traffic to green (monitor 10 min)
  - [ ] Step 3: 100% traffic to green (monitor 30 min)
  - [ ] Rollback trigger: Error rate >5% at any step

### 7.3 Monitoring & Alerting (Task #10)

- [ ] **Real-Time Monitoring Active**
  - [ ] Railway dashboard open (logs + metrics)
  - [ ] Vercel dashboard open (analytics + errors)
  - [ ] Mixpanel real-time view open (analytics)
  - [ ] Browser console monitoring (manual)

- [ ] **Alert Channels Configured**
  - [ ] Email alerts: _______________________
  - [ ] Slack/Discord alerts: _______________
  - [ ] SMS alerts (critical only): __________

**Section 7 Status:** ⏳ PENDING Production Setup

---

## Section 8: Go/No-Go Decision

### 8.1 Go/No-Go Criteria

**GO Criteria (ALL must be TRUE):**

- [ ] ✅ All P0/P1 bugs fixed (0 bugs)
- [ ] ✅ QA sign-off obtained
- [ ] ✅ Backend coverage ≥70% (96.69%)
- [ ] ✅ Frontend coverage ≥60% (49.61% accepted with justification)
- [ ] ✅ All staging smoke tests passing
- [ ] ✅ Performance benchmarks met
- [ ] ✅ Accessibility validated (WCAG 2.1 AA)
- [ ] ✅ Cross-browser testing complete
- [ ] ✅ Rollback plan tested
- [ ] ✅ Documentation updated
- [ ] ✅ Environment variables configured (production keys)
- [ ] ✅ CORS configured correctly
- [ ] ✅ Monitoring & alerting active

**NO-GO Criteria (ANY triggers delay):**

- [ ] ❌ P0/P1 bugs exist
- [ ] ❌ QA sign-off not obtained
- [ ] ❌ Staging smoke tests failing
- [ ] ❌ Performance benchmarks not met
- [ ] ❌ Rollback plan not tested
- [ ] ❌ Production environment variables missing/incorrect
- [ ] ❌ CORS not configured (frontend-backend communication broken)

### 8.2 Decision

**Decision Maker:** @devops (with @pm consultation)

**Decision:**
- [ ] **GO** - Proceed with production deployment
- [ ] **NO-GO** - Delay deployment, address blockers

**Reason (if NO-GO):** ___________________________________________

**Next Review Time (if NO-GO):** ___________________________________________

**Section 8 Status:** ⏳ PENDING Prerequisites

---

## Section 9: Checklist Summary

### Completion Status

| Section | Status | Blocker? |
|---------|--------|----------|
| 1. QA Sign-off Validation | ⏳ Pending | ❌ No |
| 2. Infrastructure Readiness | ⏳ Pending | ✅ **YES** |
| 3. Staging Environment Validation | ⏳ Pending Task #2 | ✅ **YES** |
| 4. Bug & Polish Validation | ⏳ Pending Task #3 | ✅ **YES** |
| 5. Documentation Validation | ⏳ Pending Task #4 | ❌ No |
| 6. Rollback Preparedness | ⏳ Pending | ✅ **YES** |
| 7. Production Readiness | ⏳ Pending | ✅ **YES** |
| 8. Go/No-Go Decision | ⏳ Pending | ✅ **YES** |

**Overall Status:** ⏳ **NOT READY** - Blockers exist

**Blocking Items:**
1. Task #2: Staging smoke tests not complete
2. Task #3: Final bug fixes not complete
3. Task #4: Documentation not updated
4. Infrastructure not configured (Railway + Vercel)
5. Rollback plan not tested

**Estimated Time to Ready:** 4-6 hours (assuming Tasks #2-4 complete)

---

## Section 10: Post-Checklist Actions

Once this checklist is 100% complete:

1. **Execute Task #6: Blue-Green Production Deployment**
   - Deploy to green environment
   - Run green smoke tests
   - Gradual traffic cutover (10% → 50% → 100%)
   - Monitor error rates (<5% threshold)

2. **Execute Task #7: Post-Deployment Smoke Tests**
   - Run critical path tests in production
   - Validate performance targets
   - Check data integrity
   - Verify error handling

3. **Execute Task #10: Monitoring & Alerting (48h watch)**
   - Configure all monitors
   - Setup alert channels
   - Define on-call rotation
   - Create runbooks
   - Execute 48-hour watch

---

## Appendix: Contact Information

| Role | Name | Contact |
|------|------|---------|
| DevOps Lead | @devops | _______________ |
| QA Lead | @qa (Quinn) | _______________ |
| Project Manager | @pm | _______________ |
| Architect | @architect | _______________ |
| On-Call Engineer | ________ | _______________ |

---

**Document Version:** 1.0
**Created:** 2026-01-30
**Last Updated:** 2026-01-30
**Owner:** @devops
**Status:** ⏳ **DRAFT** - Awaiting Tasks #2-4 completion
