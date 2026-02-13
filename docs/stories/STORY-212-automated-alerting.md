# STORY-212: Automated Alerting & Uptime Monitoring

**Status:** Pending
**Priority:** P0 — Blocks GTM Launch (Observability GTM Blocker)
**Sprint:** Sprint 1 (Week 1)
**Estimated Effort:** 0.5 day
**Source:** AUDIT-FRENTE-4-OBSERVABILITY (Risk #2), AUDIT-CONSOLIDATED (Tier 1)
**Squad:** devops

---

## Context

The observability audit rated Alerting as **ABSENT** and flagged it as a **GTM blocker**. The monitoring runbook (`docs/runbooks/monitoring-alerting-setup.md`, 817 lines) describes an elaborate monitoring setup, but **none of it is implemented**:
- Slack webhook URL is placeholder: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
- Contact information is blank
- No Railway alert configurations exist in the repo
- No PagerDuty, OpsGenie, or incident management integration
- Railway `restartPolicyMaxRetries = 3` restarts on failure but **nobody is notified** if it crash-loops

## Problem

Zero automated alerts exist. The service could crash-loop 3 times and stop with nobody knowing. Auth failures, payment webhook rejections, PNCP API degradation, and error rate spikes are all invisible.

## Acceptance Criteria

### UptimeRobot (Free Tier)

- [ ] AC1: Create UptimeRobot account with real email (not placeholder)
- [ ] AC2: Add monitor: `GET https://bidiq-backend-production.up.railway.app/health` every 5 min, alert after 2 consecutive failures
- [ ] AC3: Add monitor: `GET https://smartlic.tech/api/health` every 5 min, alert after 2 consecutive failures
- [ ] AC4: Configure email alerts to `tiago.sasaki@gmail.com` for both monitors
- [ ] AC5: Verify alert fires by temporarily stopping backend service

### Sentry Alerting (Depends on STORY-211)

- [ ] AC6: Sentry alert rule: first occurrence of any new error → email notification
- [ ] AC7: Sentry alert rule: error rate > 5% in 5-minute window → email notification
- [ ] AC8: Sentry alert rule: unhandled exception in `webhooks/stripe.py` → immediate email (revenue-critical)

### Frontend Health Check Improvement

- [ ] AC9: Upgrade `frontend/app/api/health/route.ts` from trivial `{"status":"ok"}` to check:
  - Backend connectivity: `fetch(BACKEND_URL + "/health")`
  - Return `degraded` if backend unreachable, `healthy` if all ok
  - Return HTTP 503 if backend is down (so UptimeRobot catches it)

### Documentation

- [ ] AC10: Update `docs/runbooks/monitoring-alerting-setup.md` with actual monitor URLs, actual contact emails, and remove placeholder values
- [ ] AC11: Add runbook section: "What to do when UptimeRobot alerts"

## Validation Metric

- Backend health check failure triggers email within 10 minutes
- Frontend health check failure triggers email within 10 minutes
- Sentry error in `stripe.py` triggers email within 5 minutes

## Risk Mitigated

- P0: Service could be down for hours/days with nobody knowing
- P0: Payment webhook failures invisible
- P1: PNCP API degradation undetected

## File References

| File | Change |
|------|--------|
| `frontend/app/api/health/route.ts` | Upgrade to deep health check |
| `docs/runbooks/monitoring-alerting-setup.md` | Update with real values |
