# STORY-165 Staging Deployment Announcement

**Feature:** Plan Restructuring - 3 Paid Tiers + FREE Trial
**Story ID:** STORY-165
**Version:** 1.0
**Deployment Date:** February 4, 2026
**Staging URL:** https://bidiq-frontend-staging.railway.app
**Backend API:** https://bidiq-uniformes-staging.railway.app

---

## 🎯 What's Being Deployed

### New Pricing Model
Transition from 6 plans to **3 paid tiers + FREE trial**:

| Plan | Price | Max History | Excel Export | Monthly Quota |
|------|-------|-------------|--------------|---------------|
| **FREE Trial** | R$ 0 (7 days) | 7 days | ❌ Blocked | Unlimited during trial |
| **Consultor Ágil** | R$ 297/month | 30 days | ❌ Blocked | 50 searches/month |
| **Máquina** | R$ 597/month | 1 year | ✅ Enabled | 300 searches/month |
| **Sala de Guerra** | R$ 1497/month | 5 years | ✅ Enabled | 1000 searches/month |

### Key Features

1. **Quota Enforcement System**
   - Monthly quota tracking per user per plan
   - Automatic reset on 1st day of month
   - Real-time quota counter in UI ("23/50 buscas este mês")
   - HTTP 429 error when quota exhausted with upgrade CTA

2. **Excel Export Restrictions**
   - FREE Trial & Consultor Ágil: Export button shows lock icon 🔒
   - Tooltip: "Exportar Excel disponível no plano Máquina (R$ 597/mês)"
   - Máquina & Sala de Guerra: Full Excel export enabled

3. **Date Range Validation**
   - Enforced server-side (prevents API tampering)
   - Visual indicator in date picker showing max allowed range
   - HTTP 403 error if range exceeds plan limit with upgrade suggestion
   - Real-time validation (disable search button until valid)

4. **Rate Limiting**
   - FREE Trial: 2 requests/minute
   - Consultor Ágil: 10 requests/minute
   - Máquina: 30 requests/minute
   - Sala de Guerra: 60 requests/minute

5. **Trial Expiration Enforcement**
   - FREE Trial expires after 7 days
   - Forced upgrade to continue using system
   - Trial countdown in UI: "Trial: 3 dias restantes"

6. **AI Summary Token Control**
   - Consultor Ágil: 200 tokens (basic summary)
   - Máquina: 500 tokens (detailed summary)
   - Sala de Guerra: 1000 tokens (comprehensive summary)

---

## 🧪 Testing Instructions for Internal Team

### Access Credentials

**Staging Environment:**
- URL: https://bidiq-frontend-staging.railway.app
- Backend: https://bidiq-uniformes-staging.railway.app/docs

**Test Users:**
| Email | Password | Plan | Purpose |
|-------|----------|------|---------|
| free@test.com | Test123! | FREE Trial | Test trial expiration, Excel blocking |
| consultor@test.com | Test123! | Consultor Ágil | Test 30-day limit, quota exhaustion |
| maquina@test.com | Test123! | Máquina | Test Excel export, 1-year range |
| sala@test.com | Test123! | Sala de Guerra | Test all features unlocked |

### Test Scenarios

#### Scenario 1: FREE Trial User (Day 1)
**User:** free@test.com
**Expected Behavior:**
- [ ] Plan badge shows "FREE Trial (6 dias restantes)"
- [ ] Date range picker allows max 7 days
- [ ] Selecting 8+ days shows warning: "⚠️ Seu plano permite buscas de até 7 dias. Ajuste as datas ou faça upgrade."
- [ ] Search button disabled until range is valid
- [ ] Excel button shows lock icon 🔒
- [ ] Clicking locked Excel button opens upgrade modal with Máquina pre-selected
- [ ] Search completes successfully (no quota limit during trial)
- [ ] Quota counter shows "Buscas este mês: 1/∞ (Trial)"

#### Scenario 2: Consultor Ágil (Quota at 48/50)
**User:** consultor@test.com (manual setup: set quota to 48)
**Expected Behavior:**
- [ ] Plan badge shows "Consultor Ágil"
- [ ] Quota counter shows "Buscas este mês: 48/50" (yellow warning color)
- [ ] Date range picker allows max 30 days
- [ ] Excel button locked 🔒
- [ ] First search: Success, quota counter → 49/50 (red)
- [ ] Second search: Success, quota counter → 50/50 (red)
- [ ] Third search: HTTP 429 error with message: "Você atingiu o limite de 50 buscas mensais do plano Consultor Ágil. Aguarde renovação em 01/03/2026 ou faça upgrade."
- [ ] Error dialog includes "Fazer Upgrade" button

#### Scenario 3: Máquina User (Excel Export)
**User:** maquina@test.com
**Expected Behavior:**
- [ ] Plan badge shows "Máquina"
- [ ] Date range picker allows up to 365 days (1 year)
- [ ] Excel button enabled ✅ (no lock icon)
- [ ] Search with 90-day range succeeds
- [ ] Excel download works (generates .xlsx file)
- [ ] Quota counter shows "Buscas este mês: 1/300" (green)

#### Scenario 4: Date Range Violation
**User:** consultor@test.com (30-day limit)
**Steps:**
1. Select date range: 2025-12-01 to 2026-01-31 (62 days)
2. Click "Buscar Licitações"

**Expected Behavior:**
- [ ] Real-time validation warns BEFORE clicking search
- [ ] Search button disabled (greyed out)
- [ ] Warning message: "⚠️ Seu plano Consultor Ágil permite buscas de até 30 dias. Você selecionou 62 dias."
- [ ] Clicking disabled button shows tooltip: "Ajuste as datas ou faça upgrade para Máquina"

#### Scenario 5: Rate Limiting
**User:** consultor@test.com (10 req/min limit)
**Steps:**
1. Execute 11 rapid searches (< 1 minute)

**Expected Behavior:**
- [ ] First 10 searches succeed
- [ ] 11th search returns HTTP 429 error
- [ ] Error message: "Limite de requisições excedido (10 req/min). Aguarde 60 segundos."
- [ ] Response includes `Retry-After: 60` header

#### Scenario 6: Upgrade Flow
**User:** free@test.com
**Steps:**
1. Click locked Excel button

**Expected Behavior:**
- [ ] Upgrade modal opens
- [ ] Modal shows plan comparison table (all 4 plans)
- [ ] Máquina plan is pre-selected/highlighted
- [ ] Benefits of each tier clearly displayed
- [ ] CTAs for each plan visible
- [ ] Clicking "Escolher Máquina" triggers analytics event (check console)

---

## 📊 Feedback Collection

### How to Report Issues

**Priority Levels:**
- **P0 (Critical):** System down, data loss, security breach
- **P1 (High):** Major feature broken, quota not enforcing correctly
- **P2 (Medium):** UI glitch, incorrect error message
- **P3 (Low):** Cosmetic issues, typos

**Reporting Methods:**

1. **Slack:** #smart-pncp-staging (fastest response)
   - Tag @oncall-dev for urgent issues (P0/P1)
   - Include: User email, scenario, expected vs. actual behavior

2. **GitHub Issues:** https://github.com/tjsasakifln/PNCP-poc/issues
   - Use label: `STORY-165`, `staging`, priority label
   - Template:
     ```markdown
     ## Issue Summary
     [Brief description]

     ## Steps to Reproduce
     1. Login as free@test.com
     2. Select 10-day date range
     3. Click search

     ## Expected Behavior
     [What should happen]

     ## Actual Behavior
     [What happened]

     ## Environment
     - URL: https://bidiq-frontend-staging.railway.app
     - Browser: Chrome 120
     - User: free@test.com
     ```

3. **Internal Testing Spreadsheet:**
   - Link: [Google Sheets - STORY-165 Testing Tracker]
   - Document: Test scenario, result (✅/❌), notes

### What to Test

**Critical Validation (Must Test):**
- [ ] Quota enforcement (exhaust monthly quota)
- [ ] Excel export blocking (FREE/Consultor vs. Máquina/Sala)
- [ ] Date range validation (exceed plan limit)
- [ ] Trial expiration (set trial_expires_at to yesterday)
- [ ] Rate limiting (burst testing)
- [ ] Upgrade modal triggers (locked features)

**Optional Validation (Nice to Test):**
- [ ] Quota counter accuracy (increment after each search)
- [ ] Plan badge display (correct colors, trial countdown)
- [ ] Error messages (user-friendly, actionable)
- [ ] Analytics events (upgrade clicks tracked in console)

---

## 📅 Timeline to Production

### Phase 0: Pre-Staging (Current)
**Date:** February 3, 2026
**Status:** ✅ Complete
- [x] Code implementation complete (85.2% of story)
- [x] Backend tests: 106 passing (25 quota tests)
- [x] Frontend tests: 69 passing (63 plan/quota tests)
- [x] Feature flag implemented (`ENABLE_NEW_PRICING`)

### Phase 1: Staging Deployment
**Date:** February 4, 2026 (Today)
**Duration:** 2-3 hours
**Owner:** @devops

**Checklist:**
- [ ] Deploy backend to Railway staging (3 min)
- [ ] Deploy frontend to Railway staging (2 min)
- [ ] Run smoke tests (10 min)
- [ ] Enable feature flag: `ENABLE_NEW_PRICING=10%` (canary rollout)
- [ ] Notify team in #smart-pncp-staging

### Phase 2: Internal Testing
**Date:** February 4-5, 2026
**Duration:** 1-2 days
**Owner:** @qa + @pm

**Success Criteria:**
- [ ] All 6 test scenarios pass (see above)
- [ ] No P0/P1 bugs found
- [ ] Quota enforcement 100% accurate
- [ ] Excel blocking 100% accurate
- [ ] No performance degradation (<15s P95 latency)

**Rollback Trigger:**
- Any P0 bug (system down, data loss)
- >3 P1 bugs (major feature broken)
- >50% of test scenarios fail

### Phase 3: Production 10% Rollout
**Date:** February 6, 2026 (T+2 days)
**Duration:** 24 hours
**Owner:** @devops

**Actions:**
- [ ] Set feature flag: `ENABLE_NEW_PRICING=10%`
- [ ] Monitor error rate (target: <1%)
- [ ] Monitor quota exhaustion events (expected: 5-20/day)
- [ ] Monitor upgrade modal CTR (target: >5%)
- [ ] On-call engineer assigned (24-hour watch)

**Success Criteria:**
- [ ] Error rate <1%
- [ ] No customer complaints
- [ ] Quota exhaustion events logged correctly
- [ ] No rollbacks needed

**Rollback Trigger:**
- Error rate >2%
- P0 incident (critical bug in production)
- >5 customer complaints about plan restrictions

### Phase 4: Production 50% Rollout
**Date:** February 7, 2026 (T+3 days)
**Duration:** 24 hours
**Owner:** @devops

**Actions:**
- [ ] Set feature flag: `ENABLE_NEW_PRICING=50%`
- [ ] Monitor same metrics as 10% rollout
- [ ] Analyze upgrade modal conversion (quota exhaustion → paid plan)

**Success Criteria:**
- [ ] Error rate <1%
- [ ] Upgrade modal CTR >5%
- [ ] P95 latency <15s (acceptable overhead)

**Rollback Trigger:**
- Error rate >1.5%
- P0/P1 incident
- Conversion rate <2% (business decision)

### Phase 5: Production 100% Rollout
**Date:** February 8, 2026 (T+4 days)
**Duration:** Permanent
**Owner:** @devops

**Actions:**
- [ ] Set feature flag: `ENABLE_NEW_PRICING=100%`
- [ ] Remove feature flag code (cleanup)
- [ ] Update documentation (PRD.md, pricing page)
- [ ] Announce GTM readiness to stakeholders

**Success Criteria:**
- [ ] Error rate <0.5% (long-term target)
- [ ] Zero rollbacks executed
- [ ] Customer complaints = 0
- [ ] Upgrade conversion >10% (month 1 target)

---

## 🚨 Rollback Plan

**Decision Authority:**
- **P3 (Low):** @oncall-dev (no rollback, fix forward)
- **P2 (Medium):** @oncall-dev + @devops-lead (rollback if >3 bugs)
- **P1 (High):** @devops-lead + @pm (rollback likely)
- **P0 (Critical):** Immediate rollback, no approval needed

**Rollback SLA:** 5 minutes from decision to traffic restored

**Rollback Procedure:**
1. Set feature flag: `ENABLE_NEW_PRICING=0%`
2. Verify old pricing model active (check /api/me response)
3. Monitor error rate (should return to <0.5%)
4. Notify team in #smart-pncp-incidents

**See Full Procedure:** `docs/deployment/rollback-plan-story165.md`

---

## 📈 Monitoring & Alerts

### Key Metrics to Watch

**Reliability:**
- Error rate: <1% (P95 latency <15s)
- Health check uptime: 100%
- Quota check success rate: >99%

**Business:**
- Quota exhaustion events: 5-20/day (expected behavior)
- Upgrade modal CTR: >5% (quota exhaustion → upgrade click)
- Excel enforcement accuracy: 100% (FREE blocked, Máquina allowed)

**Performance:**
- check_quota() P95: <200ms
- Supabase connection pool: <15 active connections

### Dashboards

**Railway Metrics (Real-time):**
- URL: https://railway.app/project/{project-id}/metrics
- Watch: Error rate, latency, CPU, memory

**Supabase Metrics:**
- URL: https://app.supabase.com/project/{project-id}/database/query-performance
- Watch: Connection pool usage, slow queries

**Custom Business Metrics:**
- Location: TBD (Analytics dashboard)
- Metrics: Quota exhaustion, upgrade CTR, conversion funnel

---

## 🎓 Training Resources

**For QA Team:**
- Testing Guide: `docs/deployment/smoke-tests-story165.md`
- Test Scenarios: See "Testing Instructions" section above

**For On-Call Engineers:**
- Quick Reference: `docs/deployment/oncall-quick-reference-story165.md`
- Common Issues: Quota exhaustion, rate limiting, trial expiration

**For Product Owners:**
- Business Metrics: `docs/deployment/monitoring-story165.md` (Section 1.3)
- Conversion Funnel: Quota exhaustion → Upgrade modal → Checkout

---

## ✅ Go/No-Go Criteria

**Staging Approval Checklist:**
- [ ] All test scenarios pass (6/6)
- [ ] No P0/P1 bugs found
- [ ] Performance acceptable (P95 <15s)
- [ ] On-call engineer trained
- [ ] Rollback procedure tested (dry run)

**Production 10% Approval:**
- [ ] Staging success (2+ days stable)
- [ ] QA sign-off
- [ ] DevOps sign-off
- [ ] PM sign-off (business readiness)

**Production 100% Approval:**
- [ ] 50% rollout stable (24+ hours)
- [ ] Conversion metrics healthy (CTR >5%)
- [ ] No outstanding P1/P2 bugs

**See Full Decision Matrix:** `docs/deployment/go-no-go-decision-story165.md`

---

## 📞 Support Contacts

| Role | Contact | Use Case |
|------|---------|----------|
| **On-Call Engineer** | @oncall-dev (Slack #smart-pncp-incidents) | First responder for all incidents |
| **DevOps Lead** | @devops-lead (Slack #smart-pncp-dev) | Deployment issues, rollback approval |
| **QA Lead** | @qa (Slack #smart-pncp-staging) | Test coordination, bug triage |
| **Product Owner** | @pm (Slack #smart-pncp-business) | Rollback decision (revenue impact) |

**Office Hours:**
- **Staging Testing:** February 4-5, 2026 (9am-6pm BRT)
- **Production Deployment:** February 6, 2026 (10am BRT)
- **War Room (if needed):** Slack #smart-pncp-war-room

---

## 📝 Next Steps

### For QA Team (Today)
1. Review test scenarios (this document, section "Testing Instructions")
2. Execute all 6 test scenarios on staging
3. Document results in Testing Tracker spreadsheet
4. Report bugs in #smart-pncp-staging (tag @oncall-dev for P1+)

### For DevOps Team (Today)
1. Deploy to staging (follow checklist)
2. Run smoke tests (`docs/deployment/smoke-tests-story165.md`)
3. Enable feature flag at 10% (canary)
4. Monitor metrics for first 2 hours

### For Product Team (Feb 4-5)
1. Review business metrics setup (quota exhaustion tracking)
2. Validate upgrade modal messaging (user-friendly, actionable)
3. Prepare GTM announcement (after 100% rollout)

---

**Questions?**
- **Slack:** #smart-pncp-staging
- **Email:** dev-team@smartpncp.com
- **Emergency:** @oncall-dev (Slack, immediate response)

**Last Updated:** February 4, 2026
**Document Owner:** @pm (Parker)
**Next Review:** February 6, 2026 (post-10% rollout)
