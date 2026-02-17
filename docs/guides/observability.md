# Observability Setup Guide

## Overview

SmartLic uses two observability tools:
- **Sentry** — Error tracking and performance monitoring (backend + frontend)
- **Mixpanel** — Product analytics and user behavior tracking (frontend only)

## Sentry

### Architecture

| Component | Config File | DSN Variable |
|-----------|-------------|-------------|
| Backend (FastAPI) | `backend/main.py` | `SENTRY_DSN` |
| Frontend Client | `frontend/app/components/AnalyticsProvider.tsx` | `NEXT_PUBLIC_SENTRY_DSN` |
| Frontend Server | `frontend/sentry.server.config.ts` | `SENTRY_DSN` |
| Frontend Edge | `frontend/sentry.edge.config.ts` | `SENTRY_DSN` |

### Environment Variables

```bash
# Backend
SENTRY_DSN=https://...@....ingest.us.sentry.io/...

# Frontend (build-time — must be set before `next build`)
NEXT_PUBLIC_SENTRY_DSN=https://...@....ingest.us.sentry.io/...
SENTRY_AUTH_TOKEN=sntrys_...    # For source map uploads
SENTRY_ORG=confenge
SENTRY_PROJECT=smartlic-frontend
```

### Features Enabled
- PII scrubbing (`before_send` callback in backend)
- Error boundaries (`app/error.tsx`, `app/global-error.tsx`)
- Source map uploads via `withSentryConfig` webpack plugin
- Tunnel route (`/monitoring`) to bypass ad-blockers
- `tracesSampleRate: 0.1` (10% of transactions)

### Alerts (configure in Sentry dashboard)
1. **New Issue Alert** — Email on every new error type
2. **Error Rate Spike** — Alert when error rate exceeds 5% in 5-minute window
3. **PCP API errors > 10/hour** — Monitor new data source stability (post GTM-FIX-011)

### Verification
```bash
# Backend: trigger test error
curl -X POST https://api.smartlic.tech/v1/sentry-test

# Frontend: browser console
Sentry.captureMessage('Test from observability guide');
```

## Mixpanel

### Architecture
- Initialized in `AnalyticsProvider.tsx` (client-side only)
- Respects LGPD cookie consent — no tracking without user opt-in
- Token: `NEXT_PUBLIC_MIXPANEL_TOKEN`

### Key Events Tracked
| Event | Trigger |
|-------|---------|
| `page_load` | Every page navigation |
| `page_exit` | Browser unload (with session duration) |
| `search_completed` | After search finishes |
| `checkout_initiated` | User starts checkout |
| `error_encountered` | Client-side error |

### UTM Tracking
Captures `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` from URL parameters and stores as Mixpanel super properties.

### Dashboards
See `docs/analytics/mixpanel-dashboard-configuration.md` for 4 pre-configured dashboards:
1. User Engagement
2. Feature Usage
3. Performance
4. Business Metrics

## CSP Configuration

Both Sentry and Mixpanel domains must be in the Content-Security-Policy `connect-src` directive in `frontend/next.config.js`:

```
connect-src 'self' ... https://*.ingest.sentry.io https://api-js.mixpanel.com https://api.mixpanel.com
```

## Related Documentation
- `docs/reports/STORY-211-SENTRY-SETUP.md` — Sentry setup steps
- `docs/analytics/` — Mixpanel dashboards, event dictionary, alert runbook
- `docs/gtm-ok/stories/GTM-FIX-002.md` — Observability remediation story
