# Monitoring & Alerting Setup

**Project:** SmartLic (BidIQ)
**Version:** 2.0
**Last Updated:** 2026-02-13
**Owner:** @devops
**Alert Contact:** tiago.sasaki@gmail.com

---

## Overview

This runbook provides the production monitoring and alerting setup for SmartLic. It covers automated uptime monitoring (UptimeRobot), error tracking (Sentry), and platform metrics (Railway).

**Alert Response Time:** <15 minutes for critical, <1 hour for warnings

---

## Section 1: Monitoring Stack

### 1.1 Active Monitoring

| Layer | Tool | What It Monitors | Alert Channel |
|-------|------|------------------|---------------|
| **Uptime** | UptimeRobot (Free) | Backend + Frontend health endpoints, 5-min interval | Email: tiago.sasaki@gmail.com |
| **Errors** | Sentry | Unhandled exceptions, error rate spikes, revenue-critical paths | Email: tiago.sasaki@gmail.com |
| **Infrastructure** | Railway Dashboard | CPU, Memory, Network, Request rate | Railway built-in alerts |
| **Frontend Perf** | Railway (Frontend) | Web Vitals, Build status | Railway built-in alerts |

### 1.2 UptimeRobot Monitors

| Monitor | URL | Interval | Alert Condition |
|---------|-----|----------|-----------------|
| **SmartLic Backend Health** | `https://bidiq-backend-production.up.railway.app/health` | 5 min | HTTP status != 200 |
| **SmartLic Frontend Health** | `https://smartlic.tech/api/health` | 5 min | HTTP status != 200 (returns 503 when backend is down) |

**UptimeRobot Dashboard:** https://dashboard.uptimerobot.com/

**Note:** The frontend health endpoint (`/api/health`) performs a deep check — it fetches the backend `/health` endpoint and returns HTTP 503 if the backend is unreachable. This means UptimeRobot monitoring the frontend health endpoint also implicitly monitors backend availability.

### 1.3 Sentry Projects

| Project | Platform | DSN Env Var | Dashboard |
|---------|----------|-------------|-----------|
| `smartlic-backend` | Python (FastAPI) | `SENTRY_DSN` | https://sentry.io → smartlic-backend |
| `smartlic-frontend` | JavaScript (Next.js) | `NEXT_PUBLIC_SENTRY_DSN` | https://sentry.io → smartlic-frontend |

**Sentry Alert Rules:**

| Rule | Condition | Action | Scope |
|------|-----------|--------|-------|
| New Issue Alert | First occurrence of any new error | Email tiago.sasaki@gmail.com | Both projects |
| Error Rate Spike | Error rate > 5% in 5-minute window | Email tiago.sasaki@gmail.com | Both projects |
| Stripe Webhook Critical | Unhandled exception in `webhooks/stripe.py` | Immediate email tiago.sasaki@gmail.com | smartlic-backend |

### 1.4 Future Enhancements

- Datadog for unified metrics
- PagerDuty for on-call management
- Grafana for custom dashboards
- Slack webhook integration for alerts

---

## Section 2: Key Metrics to Monitor

### 2.1 Backend Metrics (Railway)

**Access:** Railway Dashboard → `bidiq-backend` → Observability → Metrics

| Metric | Target | Warning | Critical | Check Frequency |
|--------|--------|---------|----------|-----------------|
| **Response Time (95th percentile)** | <5s | 5-10s | >10s | Every 5 min |
| **Error Rate** | <1% | 1-5% | >5% | Every 2 min |
| **Memory Usage** | <512MB | 512-768MB | >768MB | Every 10 min |
| **CPU Usage** | <50% | 50-80% | >80% | Every 10 min |
| **Request Rate** | Variable | - | <1 req/min (indicates issue) | Every 5 min |
| **Health Check Status** | 200 OK | - | Non-200 or timeout | Every 1 min |

**Monitoring Commands:**

```bash
# Health Check (run every 5 minutes)
curl -s -o /dev/null -w "%{http_code}" https://bidiq-backend-production.up.railway.app/health
# Expected: 200

# Response Time Test
curl -w "@curl-format.txt" -o /dev/null -s https://bidiq-backend-production.up.railway.app/health
# curl-format.txt:
# time_total: %{time_total}s\n

# Expected: <2s for health endpoint

# API Docs Check
curl -s -o /dev/null -w "%{http_code}" https://bidiq-backend-production.up.railway.app/docs
# Expected: 200
```

### 2.2 Frontend Metrics (Vercel)

**Access:** Vercel Dashboard → `bidiq-uniformes` → Analytics

| Metric | Target | Warning | Critical | Check Frequency |
|--------|--------|---------|----------|-----------------|
| **Largest Contentful Paint (LCP)** | <2.5s | 2.5-4s | >4s | Every 10 min |
| **First Input Delay (FID)** | <100ms | 100-300ms | >300ms | Every 10 min |
| **Cumulative Layout Shift (CLS)** | <0.1 | 0.1-0.25 | >0.25 | Every 10 min |
| **Error Rate** | <1% | 1-5% | >5% | Every 2 min |
| **Page Views** | Variable | - | <10/hour (indicates issue) | Every 30 min |
| **Build Status** | Success | - | Failed | On every build |

**Web Vitals Interpretation:**

- **Good:** LCP <2.5s, FID <100ms, CLS <0.1
- **Needs Improvement:** LCP 2.5-4s, FID 100-300ms, CLS 0.1-0.25
- **Poor:** LCP >4s, FID >300ms, CLS >0.25

### 2.3 Analytics Metrics (Mixpanel)

**Access:** Mixpanel Dashboard → Real-Time View

| Metric | Target | Warning | Check Frequency |
|--------|--------|---------|-----------------|
| **search_started events** | Variable | <5 events/hour (off-hours) | Every 30 min |
| **search_completed events** | >80% of search_started | 60-80% | Every 30 min |
| **search_failed events** | <5% of search_started | 5-20% | Every 15 min |
| **download_started events** | >50% of search_completed | 30-50% | Every 30 min |
| **download_completed events** | >90% of download_started | 70-90% | Every 30 min |
| **Event property errors** | 0 | >0 | Every 1 hour |

**Critical Events to Track:**

1. **search_started** - User initiates search
2. **search_completed** - Search returns results
3. **search_failed** - Search encounters error
4. **download_started** - User clicks download button
5. **download_completed** - Excel file downloaded
6. **download_failed** - Download error
7. **onboarding_completed** - User completes onboarding
8. **onboarding_dismissed** - User skips onboarding

### 2.4 Integration Metrics

| Metric | Target | Warning | Critical | Check Frequency |
|--------|--------|---------|----------|-----------------|
| **PNCP API Availability** | 100% | 95-100% | <95% | Every 15 min |
| **PNCP API Response Time** | <120s (27 states) | 120-180s | >180s | Every 30 min |
| **OpenAI API Availability** | 100% | 95-100% | <95% | Every 15 min |
| **OpenAI API Response Time** | <5s | 5-10s | >10s | Every 30 min |
| **Fallback Invocations** | <10% | 10-30% | >30% | Every 1 hour |

**Testing Commands:**

```bash
# PNCP API Test (1 state search)
curl -X POST https://bidiq-backend-production.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -d '{
    "ufs": ["SC"],
    "dataInicial": "2026-01-23",
    "dataFinal": "2026-01-30"
  }' -w "\nResponse time: %{time_total}s\n"
# Expected: 200 OK, <10s response time

# OpenAI API Test (via backend logs)
# Check Railway logs for "LLM summary generated" or "Using fallback summary"
# High fallback rate (>30%) indicates OpenAI API issues
```

---

## Section 3: Alert Configuration

### 3.1 Railway Alerts

**Access:** Railway Dashboard → Settings → Alerts → Add Alert

**Critical Alerts (Immediate Response Required):**

1. **CPU Usage >80%**
   - Condition: CPU usage sustained above 80% for 5 minutes
   - Action: Alert DevOps (email + SMS)
   - Response: Investigate resource leak, consider scaling

2. **Memory Usage >90%**
   - Condition: Memory usage sustained above 90% for 5 minutes
   - Action: Alert DevOps (email + SMS)
   - Response: Check for memory leak, restart service if needed

3. **Health Check Failures**
   - Condition: 3 consecutive health check failures
   - Action: Alert DevOps (email + SMS)
   - Response: Investigate backend crash, check logs, rollback if needed

4. **Deployment Failed**
   - Condition: Any deployment fails
   - Action: Alert DevOps (email)
   - Response: Review build logs, fix errors, retry deployment

**Warning Alerts (Response within 30 minutes):**

1. **CPU Usage 50-80%**
   - Condition: CPU usage sustained above 50% for 10 minutes
   - Action: Email DevOps
   - Response: Monitor trend, prepare for scaling if needed

2. **Memory Usage 70-90%**
   - Condition: Memory usage sustained above 70% for 10 minutes
   - Action: Email DevOps
   - Response: Monitor trend, investigate potential leak

**Configuration Example:**

```yaml
# Railway Alert Configuration (via dashboard)
Alert Name: High CPU Usage (Critical)
Metric: CPU Usage
Condition: Greater than 80%
Duration: 5 minutes
Notification: Email + Webhook
Recipients: tiago.sasaki@gmail.com
```

### 3.2 Vercel Alerts

**Access:** Vercel Dashboard → Settings → Notifications

**Critical Alerts:**

1. **Build Failures**
   - Condition: Any production build fails
   - Action: Email DevOps
   - Response: Review build logs, fix errors

2. **Deployment Errors**
   - Condition: Deployment fails or errors
   - Action: Email DevOps
   - Response: Check Vercel logs, rollback if needed

**Warning Alerts:**

1. **Performance Degradation**
   - Condition: Web Vitals drop below "Good" threshold
   - Action: Email DevOps
   - Response: Investigate performance issues

**Configuration Example:**

```
Settings → Notifications
☑ Build Failures
☑ Deployment Errors
☑ Performance Degradation
Email: tiago.sasaki@gmail.com
```

### 3.3 Mixpanel Alerts (Manual Monitoring)

**Note:** Mixpanel alerts require paid plan. Use manual monitoring for 48-hour window.

**Manual Check Every 30 Minutes:**

1. Open Mixpanel → Real-Time → Events
2. Verify events flowing (search_started, search_completed, etc.)
3. Check event rate (compare to expected baseline)
4. Investigate anomalies (sudden drop/spike)

**Create Dashboard:**

1. **Mixpanel Dashboard:** "Production Health (48h)"
2. **Widgets:**
   - Event count (last 1 hour): search_started, search_completed, download_started
   - Conversion funnel: search_started → search_completed → download_completed
   - Error rate: search_failed / search_started
   - Onboarding completion rate

**Alert Triggers (Manual):**

- Event rate drops >50% (unexpected low traffic)
- Error rate >10% (search_failed)
- Conversion rate drops >30% (search_started → download_completed)

### 3.4 UptimeRobot Alerts

**Active Monitors:**

| Monitor | URL | Interval | Status |
|---------|-----|----------|--------|
| SmartLic Backend Health | `https://bidiq-backend-production.up.railway.app/health` | 5 min | Active |
| SmartLic Frontend Health | `https://smartlic.tech/api/health` | 5 min | Active |

**Alert Contact:** tiago.sasaki@gmail.com (email)

**Alert Behavior (Free Plan):**
- Alerts on first detected failure (no consecutive failure threshold on free plan)
- Email notification sent immediately
- Recovery notification sent when service comes back up

### 3.5 Sentry Alerts

**Active Alert Rules:**

1. **New Issue Alert** — Fires on first occurrence of any new error in either project
2. **Error Rate Spike** — Fires when error rate exceeds 5% in a 5-minute window
3. **Stripe Webhook Critical** — Fires on any unhandled exception in `webhooks/stripe.py` (revenue-critical)

**Alert Contact:** tiago.sasaki@gmail.com (email)

### 3.6 What to Do When UptimeRobot Alerts

**You receive an email: "Monitor is DOWN"**

**Step 1: Identify which monitor (< 1 min)**

| Alert says... | Meaning |
|---------------|---------|
| "SmartLic Backend Health is DOWN" | Backend server is not responding |
| "SmartLic Frontend Health is DOWN" | Frontend server OR backend is not responding |

**Step 2: Verify manually (< 2 min)**

```bash
# Check backend directly
curl -s -o /dev/null -w "%{http_code}" https://bidiq-backend-production.up.railway.app/health
# Expected: 200

# Check frontend health (includes backend check)
curl -s https://smartlic.tech/api/health
# Expected: {"status":"healthy"}
# If degraded: {"status":"degraded","details":{"backend":"unreachable"}}
```

**Step 3: Diagnose (< 5 min)**

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Backend returns non-200 | Backend crashed or overloaded | Check Railway logs: `railway logs --tail` |
| Backend timeout | Railway service stopped | Check Railway dashboard for deployment status |
| Frontend returns 503, backend OK | Frontend can't reach backend | Check frontend env vars (BACKEND_URL) |
| Both down | Railway platform issue | Check https://status.railway.app |

**Step 4: Resolve**

| Issue | Resolution |
|-------|-----------|
| Backend crash-loop | Railway auto-restarts (3 retries). If persistent: `railway up` to redeploy |
| Memory/CPU spike | Check for expensive queries. Consider scaling Railway instance |
| Bad deployment | Rollback: see `docs/runbooks/rollback-procedure.md` |
| Railway outage | Wait for Railway to resolve. Monitor https://status.railway.app |

**Step 5: Verify recovery**
- UptimeRobot will send "Monitor is UP" email when service recovers
- Confirm manually with curl commands above
- Check Sentry for any errors that occurred during downtime

---

## Section 4: Monitoring Dashboard Setup

### 4.1 Railway Dashboard Configuration

**Steps:**

1. Open Railway Dashboard: https://railway.app/dashboard
2. Select Project: `bidiq-backend`
3. Click "Observability" tab
4. Enable all metrics:
   - ☑ CPU Usage
   - ☑ Memory Usage
   - ☑ Network I/O
   - ☑ Request Rate
   - ☑ Response Time
5. Set time range: Last 1 hour (for 48h window)
6. Keep dashboard open in dedicated browser tab

**Recommended View:**

- **Tab 1:** Railway Observability (Metrics)
- **Tab 2:** Railway Logs (Real-time tail)
- **Tab 3:** Railway Deployments (Rollback ready)

### 4.2 Vercel Dashboard Configuration

**Steps:**

1. Open Vercel Dashboard: https://vercel.com/dashboard
2. Select Project: `bidiq-uniformes`
3. Click "Analytics" tab
4. Enable Web Vitals:
   - ☑ Largest Contentful Paint (LCP)
   - ☑ First Input Delay (FID)
   - ☑ Cumulative Layout Shift (CLS)
5. Set time range: Last 1 hour
6. Keep dashboard open in dedicated browser tab

**Recommended View:**

- **Tab 1:** Vercel Analytics (Web Vitals)
- **Tab 2:** Vercel Functions (Error logs)
- **Tab 3:** Vercel Deployments (Rollback ready)

### 4.3 Mixpanel Dashboard Configuration

**Steps:**

1. Open Mixpanel: https://mixpanel.com/
2. Select Project: `BidIQ Uniformes`
3. Create Dashboard: "Production Health (48h)"
4. Add Reports:

   **Report 1: Event Volume (Last 1 Hour)**
   - Type: Insights → Segmentation
   - Event: All events
   - Breakdown: Event name
   - Time range: Last 1 hour

   **Report 2: Search Funnel**
   - Type: Insights → Funnels
   - Steps:
     1. search_started
     2. search_completed
     3. download_started
     4. download_completed
   - Time range: Last 24 hours

   **Report 3: Error Rate**
   - Type: Insights → Formula
   - Formula: (search_failed / search_started) * 100
   - Time range: Last 1 hour

   **Report 4: Onboarding Completion**
   - Type: Insights → Formula
   - Formula: (onboarding_completed / (onboarding_completed + onboarding_dismissed)) * 100
   - Time range: Last 24 hours

5. Save dashboard
6. Keep open in dedicated browser tab

**Recommended View:**

- **Tab 1:** Mixpanel Dashboard (Production Health)
- **Tab 2:** Mixpanel Real-Time (Event stream)

---

## Section 5: 48-Hour Monitoring Schedule

### 5.1 On-Call Rotation

**Primary On-Call:** @devops
**Backup On-Call:** @architect or @pm

**Schedule:**

| Time Window | Primary | Backup | Notes |
|-------------|---------|--------|-------|
| Day 1 (00:00-23:59) | @devops | @architect | Critical 24h |
| Day 2 (00:00-23:59) | @devops | @pm | Extended watch |
| Day 3+ (handoff) | Regular rotation | - | Resume normal operations |

**Availability Requirements:**

- **Primary:** Available 24/7, respond <15 min
- **Backup:** Available for escalation, respond <30 min
- **Tools Required:** Laptop, internet, Railway/Vercel access

### 5.2 Monitoring Checklist (Every 30 Minutes)

**Quick Health Check (5 minutes):**

- [ ] **Backend Health:**
  ```bash
  curl https://bidiq-backend-production.up.railway.app/health
  # Expected: 200 OK
  ```

- [ ] **Frontend Health:**
  - Open: https://bidiq-uniformes.vercel.app
  - Page loads <2s
  - No JavaScript errors in console

- [ ] **Railway Metrics:**
  - CPU: <50%
  - Memory: <512MB
  - Error rate: <1%
  - Response time: <5s (95th percentile)

- [ ] **Vercel Metrics:**
  - LCP: <2.5s
  - FID: <100ms
  - CLS: <0.1
  - Error rate: <1%

- [ ] **Mixpanel Events:**
  - Events flowing (>0 events/hour)
  - Error rate: <5%

**Document Results:**

Create monitoring log: `docs/monitoring/monitoring-log-YYYY-MM-DD.md`

**Template:**
```markdown
# Monitoring Log - YYYY-MM-DD

## HH:00 Check
- Backend Health: ✅ 200 OK
- Frontend Health: ✅ Page loads
- Railway CPU: 35% ✅
- Railway Memory: 420MB ✅
- Railway Error Rate: 0.2% ✅
- Vercel LCP: 1.8s ✅
- Mixpanel Events: 45 events/hour ✅
- **Status:** ✅ ALL GREEN

## HH:30 Check
- Backend Health: ✅ 200 OK
- Frontend Health: ✅ Page loads
- Railway CPU: 42% ✅
- Railway Memory: 438MB ✅
- Railway Error Rate: 0.5% ✅
- Vercel LCP: 2.1s ✅
- Mixpanel Events: 52 events/hour ✅
- **Status:** ✅ ALL GREEN
```

### 5.3 Detailed Monitoring (Every 2 Hours)

**Integration Test (15 minutes):**

1. **Search Flow Test:**
   - Open: https://bidiq-uniformes.vercel.app
   - Select UF: SP
   - Date range: Last 7 days
   - Click "Buscar Licitações"
   - Verify:
     - ✅ Loading progress displays
     - ✅ Results appear (if data exists)
     - ✅ Executive summary generated
     - ✅ Download button functional
     - ✅ Excel file downloads correctly

2. **Analytics Validation:**
   - Open Mixpanel → Real-Time
   - Verify events fired:
     - ✅ search_started
     - ✅ search_completed (or search_failed)
     - ✅ download_started
     - ✅ download_completed

3. **Error Log Review:**
   - Railway Logs: Check for errors/warnings
   - Vercel Logs: Check for errors/warnings
   - Browser Console: Check for JavaScript errors

**Document Results:**

Append to monitoring log:
```markdown
## HH:00 Integration Test
- Search Flow: ✅ Completed successfully
- Loading Progress: ✅ All 5 stages displayed
- Results: ✅ 47 licitações found (SP, last 7 days)
- Executive Summary: ✅ GPT-4 generated
- Download: ✅ Excel file downloaded (1.2 MB)
- Analytics: ✅ All events fired correctly
- Error Logs: ✅ No errors
- **Status:** ✅ PASS
```

### 5.4 Performance Baseline (Every 4 Hours)

**Lighthouse CI Test:**

```bash
# Install Lighthouse CI (if not installed)
npm install -g @lhci/cli

# Run Lighthouse on production
lhci autorun --collect.url=https://bidiq-uniformes.vercel.app

# Expected output:
# Performance: ≥70
# Accessibility: ≥90
# Best Practices: ≥80
# SEO: ≥70
```

**Document Results:**

```markdown
## HH:00 Lighthouse CI Baseline
- Performance (Desktop): 92/100 ✅
- Performance (Mobile): 78/100 ✅
- Accessibility: 95/100 ✅
- Best Practices: 88/100 ✅
- SEO: 91/100 ✅
- **Status:** ✅ ALL TARGETS MET
```

---

## Section 6: Incident Response Playbook

### 6.1 Critical Incident (Immediate Response)

**Triggers:**
- Health check fails (3 consecutive)
- Error rate >5%
- Response time >10s
- CPU >80% (sustained 5 min)
- Memory >90% (sustained 5 min)

**Response Steps:**

1. **Notify Team (Immediately):**
   ```
   🚨 CRITICAL INCIDENT 🚨
   Issue: [Health check failing / Error rate 7% / etc.]
   Detected: HH:mm UTC
   Status: Investigating
   ETA: 15 minutes
   ```

2. **Investigate (5 minutes):**
   - Check Railway logs for errors
   - Check Vercel logs for errors
   - Test health endpoints manually
   - Review recent deployments

3. **Decide (2 minutes):**
   - **If fixable quickly (<10 min):** Fix and monitor
   - **If not fixable quickly:** Execute rollback (see rollback-procedure.md)

4. **Execute (5-10 minutes):**
   - Apply fix OR rollback
   - Verify resolution
   - Monitor for 30 minutes

5. **Document (Post-incident):**
   - Create incident report (see rollback-procedure.md template)
   - Update monitoring checklist if needed

### 6.2 Warning Incident (Response within 30 minutes)

**Triggers:**
- Error rate 1-5%
- Response time 5-10s
- CPU 50-80% (sustained 10 min)
- Memory 70-90% (sustained 10 min)
- Web Vitals degradation

**Response Steps:**

1. **Acknowledge (2 minutes):**
   - Log incident in monitoring log
   - Notify backup on-call

2. **Investigate (15 minutes):**
   - Identify root cause
   - Check for patterns (time of day, specific UF, etc.)
   - Review code for potential issues

3. **Plan Fix (5 minutes):**
   - Quick fix (config change, restart) OR
   - Code fix (PR + staging + deploy) OR
   - Accept risk (monitor for escalation)

4. **Implement Fix (variable):**
   - Apply fix
   - Verify in staging first (if code change)
   - Deploy to production
   - Monitor for 1 hour

5. **Document:**
   - Update monitoring log
   - Create task for permanent fix (if needed)

### 6.3 Information Incident (Response within 2 hours)

**Triggers:**
- Error rate <1% (but >0%)
- Minor performance degradation
- Low event volume (off-hours)
- Non-critical warning logs

**Response Steps:**

1. **Log (5 minutes):**
   - Document in monitoring log
   - Tag for review

2. **Investigate (30 minutes - when convenient):**
   - Reproduce if possible
   - Identify pattern
   - Assess impact

3. **Decide:**
   - Create task for Week 2 cleanup OR
   - Ignore (expected behavior)

---

## Section 7: Post-48h Transition

### 7.1 Handoff from Critical to Normal Monitoring

**At 48 hours post-deployment:**

1. **Review Monitoring Logs:**
   - Calculate uptime percentage (target: >99.9%)
   - Calculate average error rate (target: <1%)
   - Calculate average response time (target: <5s)
   - Document anomalies/incidents

2. **Create Stability Report:**

   **File:** `docs/monitoring/stability-report-48h.md`

   **Template:**
   ```markdown
   # 48-Hour Stability Report

   **Deployment Date:** YYYY-MM-DD HH:mm UTC
   **Report Date:** YYYY-MM-DD HH:mm UTC (48h later)

   ## Summary
   - Uptime: XX.XX%
   - Average Error Rate: X.XX%
   - Average Response Time: X.XXs
   - Incidents: X (P0: X, P1: X, P2: X)
   - Rollbacks: X

   ## Key Metrics
   | Metric | Target | Actual | Status |
   |--------|--------|--------|--------|
   | Uptime | >99.9% | XX.XX% | ✅/⚠️/❌ |
   | Error Rate | <1% | X.XX% | ✅/⚠️/❌ |
   | Response Time | <5s | X.XXs | ✅/⚠️/❌ |
   | CPU Usage | <50% | XX% | ✅/⚠️/❌ |
   | Memory Usage | <512MB | XXXMB | ✅/⚠️/❌ |

   ## Incidents
   [List all incidents with severity, resolution time, root cause]

   ## Lessons Learned
   [What went well, what needs improvement]

   ## Recommendations
   [Action items for Week 2]
   ```

3. **Transition to Normal Monitoring:**
   - Reduce check frequency: Every 30 min → Every 4 hours
   - Disable 24/7 on-call (resume normal rotation)
   - Keep alerts enabled (Railway, Vercel, Mixpanel)

4. **Update Runbooks:**
   - Document any new issues discovered
   - Update alert thresholds if needed
   - Add new monitoring commands if needed

### 7.2 Ongoing Monitoring (Week 2+)

**Daily Monitoring (10 minutes):**

- [ ] Check Railway dashboard (CPU, Memory, Errors)
- [ ] Check Vercel dashboard (Web Vitals, Errors)
- [ ] Check Mixpanel dashboard (Event volume, Conversion)
- [ ] Review error logs (Railway + Vercel)

**Weekly Monitoring (30 minutes):**

- [ ] Run Lighthouse CI baseline
- [ ] Review performance trends (7-day average)
- [ ] Review cost trends (Railway + Vercel + OpenAI)
- [ ] Update monitoring documentation

**Monthly Monitoring (1 hour):**

- [ ] Comprehensive performance audit
- [ ] Cost optimization review
- [ ] Alert threshold tuning
- [ ] Monitoring runbook updates

---

## Appendix A: Monitoring Tools Quick Reference

### Railway CLI Commands

```bash
# View real-time logs
railway logs --tail

# View metrics
railway status

# View deployments
railway list

# Execute command in production
railway run <command>
```

### Vercel CLI Commands

```bash
# View deployments
vercel ls

# View logs
vercel logs <deployment-url>

# View environment variables
vercel env ls
```

### Mixpanel API (Advanced)

```bash
# Get event count (last 1 hour)
curl "https://mixpanel.com/api/2.0/segmentation?event=search_started&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&unit=hour" \
  -u "API_SECRET:"

# Requires Mixpanel API secret (paid plan)
```

---

## Appendix B: Monitoring Checklist Template

**Copy this for each check:**

```markdown
## YYYY-MM-DD HH:mm Monitoring Check

### Quick Health (5 min)
- [ ] Backend health: `curl /health` → 200 OK
- [ ] Frontend loads: Page <2s
- [ ] Railway CPU: <50%
- [ ] Railway Memory: <512MB
- [ ] Railway Error Rate: <1%
- [ ] Vercel LCP: <2.5s
- [ ] Mixpanel events: >0/hour

### Status
- ✅ ALL GREEN
- ⚠️ WARNINGS: [list]
- ❌ CRITICAL: [list]

### Actions Taken
[None | Investigated X | Restarted Y | Rolled back]

### Next Check
HH:mm UTC (+30 min)
```

---

## Appendix C: Contact Information

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| **Primary On-Call** | Tiago Sasaki | tiago.sasaki@gmail.com | 24/7 |

**External Support:**
- Railway Support: https://railway.app/help
- Railway Status: https://status.railway.app
- Sentry Support: https://sentry.io/support/
- UptimeRobot Dashboard: https://dashboard.uptimerobot.com/

**Alert Destinations:**
- UptimeRobot alerts → tiago.sasaki@gmail.com
- Sentry alerts → tiago.sasaki@gmail.com
- Railway alerts → Railway dashboard notifications

---

**Document Version:** 2.0
**Created:** 2026-01-30
**Last Updated:** 2026-02-13
**Owner:** @devops
**Change Log:**
- v2.0 (2026-02-13): STORY-212 — Added UptimeRobot monitors, Sentry alert rules, UptimeRobot response procedure, replaced all placeholder values
- v1.0 (2026-01-30): Initial 48-hour monitoring plan
