# Incident Response Plan - STORY-165

**Feature:** Plan Restructuring & Quota Enforcement
**Story ID:** STORY-165
**Version:** 1.0
**Created:** February 4, 2026
**Owner:** @oncall-dev (on-call rotation)

---

## Overview

This document defines incident response procedures for STORY-165 production deployment, including severity classification, rollback decision trees, communication templates, and escalation paths.

**Purpose:** Enable rapid response (5-minute rollback SLA) to production incidents

**Scope:** Issues related to:
- Quota enforcement failures
- Excel export blocking errors
- Date range validation bugs
- Rate limiting malfunctions
- Trial expiration enforcement
- Performance degradation

---

## Incident Severity Classification

### P0 (Critical) - IMMEDIATE ACTION REQUIRED
**Definition:** System down, data loss, security breach
**SLA:** Rollback within 5 minutes, no approval needed
**Examples:**
- Backend health check failing (all users affected)
- Database connection pool exhausted (503 errors)
- Quota system allowing unlimited searches (revenue loss)
- Excel exports leaking data across users (security breach)
- Authentication broken (users locked out)

**Response:**
1. **Execute immediate rollback** (see Section: Emergency Rollback)
2. **Notify CTO + @devops-lead** (Slack + phone)
3. **Post-mortem within 24 hours** (root cause, prevention)

### P1 (High) - URGENT
**Definition:** Major feature broken, affecting >10% of users
**SLA:** Fix or rollback within 1 hour
**Examples:**
- Quota exhaustion not triggering (users exceed limits)
- Excel export completely broken (500 errors)
- Date range validation failing (allows invalid ranges)
- Rate limiting not enforcing (users bypass limits)
- Upgrade modal not opening (lost conversion opportunity)

**Response:**
1. **Investigate root cause** (logs, metrics, reproduction)
2. **Decision:** Fix forward OR rollback
3. **Notify @devops-lead + @pm** (Slack war room)
4. **Implement fix or rollback within 1 hour**

### P2 (Medium) - HIGH PRIORITY
**Definition:** Feature degraded, affecting <10% of users
**SLA:** Fix within 4 hours
**Examples:**
- Quota counter showing incorrect values (visual bug)
- Excel export slow but working (>30s generation time)
- Upgrade modal opening incorrectly (false positives)
- Trial countdown showing wrong days remaining
- Error messages poorly worded (confusing to users)

**Response:**
1. **Create incident ticket** (GitHub issue with P2 label)
2. **Investigate within 1 hour** (assign to @dev)
3. **Fix within 4 hours** (deploy via normal process)
4. **No rollback unless** >20% of users affected

### P3 (Low) - NORMAL PRIORITY
**Definition:** Cosmetic issues, minor UX friction
**SLA:** Fix within 1 week (backlog)
**Examples:**
- Plan badge color slightly off (CSS issue)
- Tooltip text typos (spelling errors)
- Analytics event not firing (tracking gap)
- Slow page load (but <15s P95)

**Response:**
1. **Create backlog ticket** (GitHub issue with P3 label)
2. **Triage in next sprint planning**
3. **No immediate action required**

---

## What Constitutes a Production Incident?

### ✅ IS an Incident (Requires Response)
- [ ] **Quota enforcement failure:** Users exceed monthly limits without 429 error
- [ ] **Excel blocking failure:** FREE users download Excel successfully
- [ ] **Date range validation bypass:** Users search 90-day range on 30-day plan
- [ ] **Rate limiting bypass:** Users exceed req/min without throttling
- [ ] **Trial expiration bypass:** Expired trial users still accessing system
- [ ] **Error rate spike:** >1% errors (P1 if >2%, P0 if >5%)
- [ ] **Performance degradation:** P95 latency >15s (P1 if >20s)
- [ ] **Database issues:** Connection pool exhausted, deadlocks, timeouts
- [ ] **Security breach:** Data leakage, unauthorized access, SQL injection

### ❌ NOT an Incident (Document & Defer)
- [ ] **User confusion:** "I don't understand quota limits" → FAQ update
- [ ] **Feature request:** "I want 60-day range on Consultor" → Product backlog
- [ ] **Expected behavior:** "I got 403 error for 90-day search on 30-day plan" → Working as intended
- [ ] **Cosmetic issue:** Plan badge color wrong → P3 backlog
- [ ] **Analytics gap:** Event not tracked → P3 backlog

---

## Incident Response Workflow

### Phase 1: Detection (0-2 minutes)

#### Monitoring Alerts
**Primary Channels:**
1. **Railway Alerts:** Email + Slack #smart-pncp-alerts
   - Error rate >1% (5-minute window)
   - P95 latency >15s (5-minute window)
   - CPU >80% (sustained 10 minutes)
   - Memory >80% (sustained 10 minutes)

2. **Supabase Alerts:** Email + Slack #smart-pncp-db-alerts
   - Connection pool >20 connections
   - Database CPU >70%
   - Slow query >500ms (sustained)

3. **Custom Business Alerts:** (If implemented)
   - Quota exhaustion events >50/hour (anomaly detection)
   - Excel blocking failure >1 event (security alert)
   - Trial bypass detected >1 event (revenue loss)

#### Manual Detection
- **Customer complaints:** Support tickets, Slack mentions, emails
- **On-call observations:** Dashboard review, log monitoring

### Phase 2: Triage (2-5 minutes)

#### Severity Assessment
**On-call engineer asks:**
1. **Is system down?** → P0 (immediate rollback)
2. **Can users complete core flows?** (search, download) → If NO: P1
3. **Is revenue at risk?** (quota bypass, trial bypass) → If YES: P1
4. **How many users affected?** >10% → P1, <10% → P2, <1% → P3

#### Impact Analysis
```bash
# Check error rate (Railway CLI)
railway logs --project bidiq-uniformes-production --filter "500\|429\|403" --since 10m | wc -l

# Check active users affected (if possible)
# Estimate: Total errors / Avg requests per user

# Check Supabase connection pool
# Navigate to Supabase dashboard → Database → Connections
```

#### Initial Communication
```
🚨 INCIDENT DETECTED - STORY-165

**Severity:** P{0/1/2/3}
**Summary:** {Brief description, e.g., "Quota exhaustion not triggering 429 errors"}
**Impact:** {X users affected, Y% of traffic}
**On-Call:** @oncall-dev (investigating)

**Next Update:** {5 minutes / 15 minutes}
**War Room:** #smart-pncp-war-room
```

### Phase 3: Investigation (5-15 minutes)

#### Data Collection
**Logs Analysis:**
```bash
# Backend logs (last 30 minutes)
railway logs --project bidiq-uniformes-production --since 30m > incident-logs.txt

# Search for quota-related errors
grep -E "quota|429|403|check_quota" incident-logs.txt

# Search for Excel blocking errors
grep -E "excel|download|export" incident-logs.txt

# Search for database errors
grep -E "database|connection|timeout|deadlock" incident-logs.txt
```

**Metrics Review:**
- **Railway Dashboard:** Error rate, latency, CPU, memory (last 1 hour)
- **Supabase Dashboard:** Query performance, connection pool, slow queries
- **Custom Metrics:** Quota exhaustion events, upgrade modal CTR (if available)

**Reproduction Attempt:**
```bash
# Test quota exhaustion flow
# 1. Login as consultor@test.com (50 quota limit)
# 2. Manually set quota to 50 in database
# 3. Execute search
# Expected: 429 error
# Actual: _______________

# Test Excel blocking flow
# 1. Login as free@test.com
# 2. Execute search
# 3. Click Excel button
# Expected: Locked button, upgrade modal
# Actual: _______________
```

#### Root Cause Hypothesis
**Common Causes:**
1. **Database query failure:** Index missing, timeout, deadlock
2. **Feature flag misconfiguration:** `ENABLE_NEW_PRICING` set incorrectly
3. **Code bug:** Logic error in quota check, Excel gating
4. **Infrastructure issue:** Supabase down, Railway restart
5. **Race condition:** Concurrent requests bypassing quota

### Phase 4: Decision (15-20 minutes)

#### Rollback Decision Tree
```
Is P0 severity? (system down, data loss, security breach)
    ↓ YES
    → IMMEDIATE ROLLBACK (no approval needed)
    ↓ NO

Is P1 severity? (major feature broken, >10% users)
    ↓ YES
    → ROLLBACK OR FIX within 1 hour
       └─ Can fix in <30 min? → FIX FORWARD
       └─ Uncertain root cause? → ROLLBACK
    ↓ NO

Is P2 severity? (<10% users, feature degraded)
    ↓ YES
    → FIX FORWARD (no rollback unless worsens)
    ↓ NO

Is P3 severity? (cosmetic, low impact)
    ↓ YES
    → CREATE BACKLOG TICKET (no immediate action)
```

#### Rollback Approval Matrix
| Severity | Approver | Approval Time | Rollback Command |
|----------|----------|---------------|------------------|
| **P0** | @oncall-dev (solo) | Immediate | `./rollback-emergency.sh` |
| **P1** | @oncall-dev + @devops-lead | <15 min | `railway variables --set ENABLE_NEW_PRICING={lower %}` |
| **P2** | @devops-lead + @pm | <1 hour | Discuss (usually fix forward) |
| **P3** | N/A | N/A | No rollback |

### Phase 5: Response (20-60 minutes)

#### Option A: Emergency Rollback (P0)
**SLA:** 5 minutes from decision to traffic restored

```bash
#!/bin/bash
# rollback-emergency.sh

echo "🚨 EMERGENCY ROLLBACK - STORY-165"
echo "Incident: {Brief description}"
echo "Severity: P0"
echo "On-Call: @oncall-dev"

# Step 1: Set feature flag to 0% (disable new pricing)
railway variables --set ENABLE_NEW_PRICING=0

# Step 2: Wait for deployment
echo "Waiting 30s for rollout..."
sleep 30

# Step 3: Verify health
echo "Verifying health..."
curl https://bidiq-uniformes-production.up.railway.app/health

# Step 4: Test old pricing active
echo "Testing old pricing..."
curl https://bidiq-uniformes-production.up.railway.app/api/me \
  -H "Authorization: Bearer {test-token}" | jq '.plan_id'
# Expected: Old pricing structure (6-plan system)

# Step 5: Monitor error rate
echo "Monitoring error rate for 5 minutes..."
for i in {1..5}; do
  ERROR_COUNT=$(railway logs --since 1m --filter "500" | wc -l)
  echo "Minute $i: $ERROR_COUNT errors"
  sleep 60
done

echo "✅ Rollback complete."
echo "Expected: Error rate <0.5%, old pricing active"
echo "Next: Post-mortem within 24 hours"
```

**Post-Rollback Communication:**
```
✅ ROLLBACK COMPLETE - STORY-165

**Incident:** {Brief description}
**Severity:** P0
**Status:** Traffic restored (old pricing active)
**Rollback Time:** {X minutes}
**Current State:** Feature flag at 0%

**Impact:**
- All users reverted to old pricing (6-plan system)
- New pricing disabled until root cause fixed

**Next Steps:**
1. Root cause analysis (assign to @architect)
2. Post-mortem meeting (within 24 hours)
3. Fix implementation timeline (TBD)
4. Re-deployment plan (TBD)

**Questions?** Contact @oncall-dev or @devops-lead
```

#### Option B: Partial Rollback (P1)
**SLA:** 10 minutes from decision

```bash
# Rollback from 100% to 50% (or 50% to 10%)
railway variables --set ENABLE_NEW_PRICING=50
sleep 30
curl .../health

# Monitor for 10 minutes
# If issue persists → Full rollback to 0%
# If issue resolved → Extended monitoring at 50%
```

**Use Cases:**
- Issue only affects high-traffic periods (scale problem)
- Issue is rare (<5% reproduction rate)
- Business metrics acceptable at lower %

#### Option C: Fix Forward (P1/P2)
**SLA:** 30-60 minutes from decision

**When to Fix Forward:**
- Root cause identified and fix is simple (<30 min)
- Hotfix can be deployed safely (tested in staging)
- Issue affects <10% of users (P2 severity)
- Rollback would cause more disruption than fix

**Fix Forward Process:**
1. **Implement fix** (local development, test)
2. **Deploy to staging** (verify fix works)
3. **Deploy to production** (Railway deployment)
4. **Monitor for 30 minutes** (verify fix effective)
5. **Document in post-mortem**

**Example Fix Forward Scenarios:**
- **Bug:** Quota counter off by 1 → Fix logic, deploy
- **Performance:** Slow query → Add index, deploy
- **UX:** Error message confusing → Update text, deploy

### Phase 6: Post-Incident (1-24 hours)

#### Immediate Follow-Up (Within 1 Hour)
- [ ] **Incident resolved:** Verify error rate back to normal (<0.5%)
- [ ] **Root cause documented:** Create GitHub issue with RCA
- [ ] **Communication sent:** Update stakeholders (Slack, email)
- [ ] **Monitoring extended:** 2x normal watch period

#### Post-Mortem (Within 24 Hours)
**Attendees:** @oncall-dev, @devops-lead, @pm, @architect, @qa

**Agenda:**
1. **Timeline:** What happened, when, how detected
2. **Root Cause:** Why did it happen (technical, process)
3. **Impact:** Users affected, revenue lost, reputation damage
4. **Response:** What went well, what could improve
5. **Prevention:** How to prevent recurrence (code, monitoring, process)
6. **Action Items:** Owner, deadline, priority

**Template:** `docs/retrospectives/incident-story165-{date}.md`

---

## Escalation Paths

### Technical Escalation (Infrastructure Issues)

```
Incident Detected (monitoring alert)
    ↓
@oncall-dev (first responder, 5 min SLA)
    ↓
    ├─ P3 → Create ticket (backlog)
    ├─ P2 → Investigate (4-hour SLA) + notify @devops-lead
    ├─ P1 → Escalate to @devops-lead + war room (1-hour SLA)
    └─ P0 → IMMEDIATE ROLLBACK + notify @devops-lead + CTO

@devops-lead (infrastructure decisions)
    ↓
    ├─ P1 → Fix or rollback decision
    ├─ P0 → Coordinate rollback, notify CTO
    └─ If unresolvable → Escalate to CTO + external support

CTO (strategic decisions)
    ↓
    ├─ P0 → Public communication (if major outage)
    ├─ Revenue impact → Consult with CFO
    └─ If vendor issue → Escalate to Railway/Supabase support
```

### Business Escalation (Revenue/Conversion Issues)

```
Conversion Metrics Weak (<5% CTR, no conversions)
    ↓
@pm monitors for 24 hours (data collection)
    ↓
If trend continues (48 hours) + P1 severity
    ↓
Discuss with @devops-lead:
    ├─ Technical issue? → Fix (e.g., analytics broken)
    └─ Product/UX issue? → Escalate to CTO

CTO (product decision)
    ↓
Options:
    ├─ Rollback (abort pricing change)
    ├─ A/B test (improve messaging, pricing)
    └─ Extend monitoring (wait for more data)
```

### Customer Escalation (Complaints/Support)

```
Customer Complaint Received (support ticket)
    ↓
Support categorizes:
    ├─ P0 (security, data loss) → Immediate escalation to @oncall-dev
    ├─ P1 (feature broken) → Escalate to @oncall-dev (1-hour SLA)
    ├─ P2 (UX friction) → Document, escalate to @pm (4-hour SLA)
    └─ P3 (feature request, FAQ) → Backlog

>10 complaints in 24 hours (any severity)
    ↓
@pm reviews (categorization, pattern detection)
    ↓
    ├─ Valid bugs? → Create P1/P2 tickets, fix
    ├─ UX friction? → Improve messaging, update FAQ
    └─ Expected behavior? → Document FAQ, train support

>20 complaints in 24 hours OR revenue loss
    ↓
Escalate to CTO:
    ├─ Rollback decision (if severe backlash)
    └─ Public communication (if reputational risk)
```

---

## Communication Templates

### P0 Incident Alert (Slack #smart-pncp-incidents)
```
🚨 P0 INCIDENT - STORY-165

**Summary:** {System down / Data loss / Security breach}
**Impact:** {All users / X% of users}
**Detection:** {Monitoring alert / Customer report}
**Status:** INVESTIGATING ⏳

**On-Call:** @oncall-dev
**War Room:** #smart-pncp-war-room
**Rollback:** Executing in 5 minutes

**Next Update:** 5 minutes
**CTO Notified:** ☐ YES ☐ NO (if system-wide outage)
```

### P1 Incident Alert (Slack #smart-pncp-war-room)
```
⚠️ P1 INCIDENT - STORY-165

**Summary:** {Quota enforcement broken / Excel export failing}
**Impact:** {>10% of users / Revenue loss risk}
**Detection:** {Monitoring alert / Customer complaint}
**Status:** INVESTIGATING ⏳

**On-Call:** @oncall-dev
**DevOps:** @devops-lead (notified)
**SLA:** Fix or rollback within 1 hour

**Root Cause Hypothesis:** {Initial assessment}
**Decision Timeline:** 15 minutes

**Next Update:** 10 minutes
```

### Resolution Announcement (Slack #smart-pncp-incidents)
```
✅ INCIDENT RESOLVED - STORY-165

**Incident:** {Brief description}
**Severity:** P{0/1/2}
**Duration:** {X minutes / Y hours}
**Resolution:** {Rollback / Hotfix / Database fix}

**Root Cause:** {Brief explanation}
**Impact:** {X users affected, Y searches failed}
**Revenue Loss:** ${Z} estimated (if applicable)

**Prevention:**
1. {Action item 1, e.g., "Add database index"}
2. {Action item 2, e.g., "Improve monitoring alert"}
3. {Action item 3, e.g., "Update runbook"}

**Post-Mortem:** Scheduled for {Date/Time}
**Owner:** @oncall-dev

**Status:** All systems normal ✅
```

### Customer Communication (Email/Support Ticket)
```
Subject: Service Disruption Resolved - Smart PNCP

Dear [Customer],

We experienced a brief service disruption today affecting [feature/functionality].

**What Happened:**
{User-friendly explanation, e.g., "Some users were unable to download Excel reports for approximately 30 minutes."}

**Resolution:**
The issue has been resolved, and all services are operating normally.

**Impact:**
{Be transparent, e.g., "If you attempted to download an Excel report between 10:00-10:30 AM, please try again now."}

**Prevention:**
We are implementing additional monitoring and safeguards to prevent this from happening again.

**Compensation (if applicable):**
{e.g., "We have extended your trial period by 1 day" or "We have credited your account with 5 additional searches"}

We sincerely apologize for the inconvenience.

**Questions?**
Contact support@smartpncp.com or reply to this email.

Thank you for your patience,
Smart PNCP Team
```

---

## Common Incident Scenarios & Runbooks

### Scenario 1: Quota Exhaustion Not Triggering

**Symptoms:**
- Users exceed monthly quota without 429 error
- No "quota_exhausted" events in logs
- Quota counter shows incorrect values

**Diagnosis:**
```bash
# Check quota enforcement logs
railway logs --filter "check_quota" --since 1h

# Test quota check manually
curl https://bidiq-uniformes-production.up.railway.app/api/buscar \
  -X POST \
  -H "Authorization: Bearer {test-token}" \
  -H "Content-Type: application/json" \
  -d '{"ufs":["SC"],"data_inicial":"2026-02-01","data_final":"2026-02-04"}'

# Check database quota count
# SQL: SELECT * FROM monthly_quota WHERE user_id = '{user-id}';
```

**Root Causes:**
1. **Database query failure:** `monthly_quota` table unreachable
2. **Logic bug:** `check_quota()` returning `allowed=true` incorrectly
3. **Race condition:** Concurrent requests bypassing quota increment

**Resolution:**
- **P0 (quota allowing unlimited searches):** Immediate rollback
- **P1 (quota counter inaccurate but blocking works):** Fix forward (update logic)
- **P2 (visual bug only):** Backlog

### Scenario 2: Excel Export Blocking Failure

**Symptoms:**
- FREE users successfully download Excel
- Máquina users see locked Excel button (false positive)
- Excel blocking events not logged

**Diagnosis:**
```bash
# Check Excel blocking logs
railway logs --filter "excel_blocked\|allow_excel" --since 1h

# Test Excel blocking (FREE user)
# Login as free@test.com, execute search, check Excel button

# Check plan capabilities
# SQL: SELECT * FROM user_subscriptions WHERE user_id = '{user-id}';
```

**Root Causes:**
1. **Feature flag misconfiguration:** `ENABLE_NEW_PRICING` not applied
2. **Logic bug:** `allow_excel` check inverted (if not → if)
3. **Plan ID mismatch:** Database shows `free_trial` but code checks `free`

**Resolution:**
- **P0 (data leakage across users):** Immediate rollback + security audit
- **P1 (FREE users getting Excel):** Immediate rollback (revenue loss)
- **P2 (Máquina users blocked incorrectly):** Fix forward (customer impact low)

### Scenario 3: Date Range Validation Bypass

**Symptoms:**
- Users search 90-day range on 30-day plan (no 403 error)
- PNCP API returning data for invalid ranges
- Date validation events not logged

**Diagnosis:**
```bash
# Check date validation logs
railway logs --filter "date_range\|max_history_days" --since 1h

# Test date range validation
# Login as consultor@test.com (30-day limit)
# Select 60-day range, execute search
# Expected: 403 error
# Actual: _______________
```

**Root Causes:**
1. **Validation skipped:** `if` statement missing or condition inverted
2. **Plan capabilities wrong:** `max_history_days` set incorrectly
3. **Frontend bypassing backend:** Direct API call without validation

**Resolution:**
- **P1 (all users bypass validation):** Immediate rollback
- **P2 (rare bypass, <10% users):** Fix forward (add validation)

### Scenario 4: Rate Limiting Not Enforcing

**Symptoms:**
- Users exceed req/min without 429 error
- No rate limit events in logs
- Backend CPU spikes (burst requests)

**Diagnosis:**
```bash
# Check rate limiting logs
railway logs --filter "rate_limit\|429" --since 1h

# Test rate limiting (Consultor Ágil, 10 req/min limit)
# Execute 15 rapid searches (<1 minute)
# Expected: 11th request returns 429
# Actual: _______________

# Check Redis cache (if deployed)
# redis-cli GET rate_limit:{user-id}
```

**Root Causes:**
1. **Redis not deployed:** In-memory rate limiting ineffective
2. **Logic bug:** Rate limit counter not incrementing
3. **Clock skew:** Timestamp calculation incorrect

**Resolution:**
- **P1 (no rate limiting at all):** Rollback or deploy Redis immediately
- **P2 (rate limiting weak but present):** Fix forward (improve algorithm)

### Scenario 5: Trial Expiration Bypass

**Symptoms:**
- Expired trial users still accessing system
- No trial expiration events in logs
- Trial countdown shows negative days

**Diagnosis:**
```bash
# Check trial expiration logs
railway logs --filter "trial_expir\|FREE" --since 1h

# Test trial expiration
# Manually set trial_expires_at to yesterday in database
# Login, attempt search
# Expected: 403 error "Trial expirado"
# Actual: _______________

# Check database
# SQL: SELECT * FROM users WHERE trial_expires_at < NOW();
```

**Root Causes:**
1. **Validation skipped:** `check_quota()` not checking trial expiration
2. **Timezone issue:** UTC vs. local time mismatch
3. **Database value null:** `trial_expires_at` not set for some users

**Resolution:**
- **P0 (revenue loss, all trials bypassing):** Immediate rollback
- **P1 (some trials bypassing):** Fix forward (add validation)

---

## Rollback Commands Reference

### Full Rollback (100% → 0%)
```bash
# Disable new pricing completely
railway variables --set ENABLE_NEW_PRICING=0
sleep 30
curl .../health
echo "All users reverted to old pricing (6-plan system)"
```

### Partial Rollback (100% → 50%)
```bash
# Reduce exposure to 50%
railway variables --set ENABLE_NEW_PRICING=50
sleep 30
curl .../health
echo "50% of users on new pricing, 50% on old"
```

### Partial Rollback (50% → 10%)
```bash
# Reduce exposure to 10% (canary)
railway variables --set ENABLE_NEW_PRICING=10
sleep 30
curl .../health
echo "10% of users on new pricing, 90% on old"
```

### Verify Rollback
```bash
# Check feature flag value
railway variables --get ENABLE_NEW_PRICING
# Expected: {desired %}

# Test old pricing active
curl .../api/me -H "Authorization: Bearer {test-token}" | jq '.plan_id'
# Expected: Old pricing structure (if 0%)

# Monitor error rate (should decrease)
railway logs --filter "500\|429\|403" --since 5m | wc -l
# Expected: <10 errors in 5 minutes (<0.5% rate)
```

---

## Emergency Contacts

| Role | Primary | Backup | Contact Method |
|------|---------|--------|----------------|
| **On-Call Engineer** | @oncall-dev | @devops-lead | Slack (immediate), Phone (P0) |
| **DevOps Lead** | @devops-lead | @architect | Slack (5-min response), Email |
| **Database Admin** | @db-team | @architect | Slack #smart-pncp-db (15-min response) |
| **Product Owner** | @pm | @po | Slack (business decisions), Email |
| **CTO** | @cto | N/A | Slack (P0 only), Phone (emergency) |

**Escalation Path:**
1. **P3:** @oncall-dev → Create ticket (no escalation)
2. **P2:** @oncall-dev → @devops-lead (if unresolved in 4 hours)
3. **P1:** @oncall-dev + @devops-lead + war room (immediate)
4. **P0:** @oncall-dev + @devops-lead + CTO (immediate rollback + notification)

**War Room Activation:**
- **Trigger:** Any P0/P1 incident
- **Channel:** #smart-pncp-war-room
- **Members:** @oncall-dev, @devops-lead, @pm, @architect, @qa
- **Duration:** Until incident resolved + 1 hour stabilization

---

## Monitoring & Alert Thresholds

### Technical Alerts (Railway)
| Metric | Warning | Critical (Alert) | Action |
|--------|---------|------------------|--------|
| Error Rate | >1% (5-min window) | >2% (5-min window) | Investigate (P1 if >2%) |
| P95 Latency | >15s | >20s | Investigate (P2 if >15s, P1 if >20s) |
| CPU Usage | >80% (10-min sustained) | >95% (5-min sustained) | Scale up or rollback |
| Memory Usage | >80% (10-min sustained) | >95% (5-min sustained) | Restart or rollback |

### Database Alerts (Supabase)
| Metric | Warning | Critical (Alert) | Action |
|--------|---------|------------------|--------|
| Connection Pool | >15 connections | >25 connections | Scale pool or rollback |
| Database CPU | >70% | >90% | Optimize queries or scale |
| Slow Queries | >500ms (P95) | >1000ms (P95) | Add indexes or rollback |
| Deadlocks | >1/hour | >5/hour | Investigate concurrency bugs |

### Business Alerts (Custom)
| Metric | Warning | Critical (Alert) | Action |
|--------|---------|------------------|--------|
| Quota Exhaustion Events | >30/hour (anomaly) | >50/hour (spike) | Investigate quota bypass (P1) |
| Excel Blocking Failures | >1 event | >5 events | Immediate rollback (security risk) |
| Trial Bypass Events | >1 event | >5 events | Immediate rollback (revenue loss) |
| Customer Complaints | >5/hour | >10/hour | Escalate to @pm (business decision) |

---

## Post-Incident Checklist

### Immediate (Within 1 Hour)
- [ ] **Incident resolved:** Error rate back to <0.5%
- [ ] **Root cause documented:** GitHub issue created with RCA
- [ ] **Stakeholders notified:** Slack announcement sent
- [ ] **Monitoring extended:** 2x normal watch period (24 hours)
- [ ] **Customer communication:** Email sent (if user-facing impact)

### Short-Term (Within 24 Hours)
- [ ] **Post-mortem scheduled:** Meeting invite sent (attendees: oncall, devops, pm, architect, qa)
- [ ] **Timeline documented:** Incident timeline in `docs/retrospectives/incident-story165-{date}.md`
- [ ] **Impact quantified:** Users affected, revenue lost, reputation damage
- [ ] **Prevention plan:** Action items created with owners + deadlines

### Medium-Term (Within 1 Week)
- [ ] **Action items completed:** Code fixes, monitoring improvements, runbook updates
- [ ] **Testing validated:** Reproduction scenario tested (cannot recur)
- [ ] **Documentation updated:** Runbooks, FAQs, incident response plan
- [ ] **Team training:** Share learnings in team meeting, update on-call guide

### Long-Term (Within 1 Month)
- [ ] **Process improvements:** Update deployment checklist, add validation gates
- [ ] **Monitoring enhancements:** New alerts, dashboard improvements
- [ ] **Architecture changes:** Redundancy, circuit breakers, rate limiting
- [ ] **Retrospective review:** Assess effectiveness of prevention measures

---

**Document Owner:** @oncall-dev (on-call rotation)
**Last Updated:** February 4, 2026
**Next Review:** Post-deployment (February 10, 2026)

**Questions?** Slack #smart-pncp-incidents or email oncall@smartpncp.com
