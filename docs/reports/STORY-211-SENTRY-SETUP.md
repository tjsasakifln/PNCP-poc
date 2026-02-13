# STORY-211: Sentry Setup Guide

## Status: Code Complete — Awaiting Sentry Project Creation

All code changes are in place. The following steps require Sentry dashboard access.

## Step 1: Create Sentry Projects

1. Go to [sentry.io](https://sentry.io/) and create an organization (or use existing)
2. Create **two projects**:
   - `smartlic-backend` — Platform: **Python** (FastAPI)
   - `smartlic-frontend` — Platform: **JavaScript** (Next.js)
3. Copy the DSN from each project

## Step 2: Set Environment Variables

### Backend (Railway)

```bash
railway variables set SENTRY_DSN=https://xxxxx@oXXXXXX.ingest.sentry.io/XXXXXXX
railway variables set ENVIRONMENT=production
```

### Frontend (Railway)

```bash
railway variables set SENTRY_DSN=https://xxxxx@oXXXXXX.ingest.sentry.io/XXXXXXX
railway variables set NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@oXXXXXX.ingest.sentry.io/XXXXXXX
railway variables set SENTRY_AUTH_TOKEN=sntrys_XXXXXXXXXXXX
railway variables set SENTRY_ORG=your-org-slug
railway variables set SENTRY_PROJECT=smartlic-frontend
railway variables set NEXT_PUBLIC_ENVIRONMENT=production
```

## Step 3: Verify Integration (AC5, AC11)

### Backend Verification

```bash
# SSH into Railway or use railway run
railway run python -c "
import sentry_sdk
sentry_sdk.capture_message('Test from smartlic-backend')
print('Sent test message to Sentry')
"
```

Check Sentry dashboard — message should appear within 60 seconds.

### Frontend Verification

Add temporarily to any page:
```tsx
throw new Error("Sentry frontend test");
```
Deploy, trigger the error, check Sentry dashboard for the error with readable stack traces (source maps working).

## Step 4: Configure Alert Rules (AC12-AC14)

### Alert 1: New Issue (AC12)

1. Go to **Alerts** > **Create Alert Rule**
2. Select project: `smartlic-backend` (repeat for `smartlic-frontend`)
3. Conditions:
   - **When**: A new issue is created
   - **Then**: Send email to `tiago.sasaki@gmail.com`
4. Name: "New Issue Alert"

### Alert 2: Error Rate Spike (AC13)

1. Go to **Alerts** > **Create Alert Rule**
2. Select both projects
3. Conditions:
   - **When**: Error rate > 5% in 5-minute window
   - **Then**: Send email to `tiago.sasaki@gmail.com`
4. Name: "Error Rate Spike Alert"

### Environment Tags (AC14)

Already configured in code:
- Backend: `environment` param in `sentry_sdk.init()` reads from `ENVIRONMENT` env var
- Frontend: `environment` param reads from `NEXT_PUBLIC_ENVIRONMENT` env var
- Values: `production`, `development`

## Files Changed

| File | Change | AC |
|------|--------|----|
| `backend/requirements.txt` | Added `sentry-sdk[fastapi]>=2.0.0` | AC1 |
| `backend/main.py` | Sentry init + `scrub_pii()` before app creation | AC2, AC3 |
| `frontend/package.json` | Added `@sentry/nextjs@^10.38.0` | AC6 |
| `frontend/sentry.client.config.ts` | NEW — client-side Sentry init | AC6 |
| `frontend/sentry.server.config.ts` | NEW — server-side Sentry init | AC6 |
| `frontend/sentry.edge.config.ts` | NEW — edge runtime Sentry init | AC6 |
| `frontend/instrumentation.ts` | NEW — Next.js instrumentation hook | AC6 |
| `frontend/next.config.js` | Wrapped with `withSentryConfig`, CSP updated | AC8 |
| `frontend/app/global-error.tsx` | NEW — root layout error boundary | AC9 |
| `frontend/app/error.tsx` | Added `Sentry.captureException()` | AC10 |
| `frontend/app/auth/callback/page.tsx` | Gated sensitive logs behind NODE_ENV | AC15 |
| `frontend/__mocks__/@sentry/nextjs.js` | Jest mock for test compatibility | AC16 |
| `.env.example` | Enhanced Sentry documentation | — |

## Validation Results

| Check | Result |
|-------|--------|
| Backend import + init | PASS — sentry_sdk v2.52.0 |
| Backend no-op (no DSN) | PASS — "error tracking disabled" log |
| Backend tests (AC16) | PASS — 44 pass, same pre-existing failures |
| Frontend TypeScript | PASS — 0 errors |
| Frontend compilation | PASS — 16.3s |
| Frontend tests (AC16) | PASS — 20 failing suites (same as baseline) |
| Token leak fix (AC15) | PASS — console.logs gated behind dev check |
