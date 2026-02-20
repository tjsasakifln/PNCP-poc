# STORY-228: Fix CSP to Allow api.smartlic.tech and Cloudflare Insights

**Status:** Completed
**Priority:** P0 — EMERGENCY
**Sprint:** Immediate (Sprint 3 — Hotfix)
**Estimated Effort:** XS (1h)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (CRIT-2, CRIT-3, MIN-1)
**Squad:** team-bidiq-frontend (dev)

---

## Context

The Content Security Policy (CSP) `connect-src` directive does **not** include `https://api.smartlic.tech`, blocking all frontend-to-backend API calls via the custom domain. Additionally, `script-src` does not include Cloudflare Insights, blocking analytics.

Console errors:
```
Connecting to 'https://api.smartlic.tech/me' violates CSP directive: "connect-src 'self' ..."
Connecting to 'https://api.smartlic.tech/plans' violates CSP directive: "connect-src 'self' ..."
Loading script 'https://static.cloudflareinsights.com/beacon.min.js/...' violates CSP directive: "script-src ..."
```

**Impact:** Plans page shows no plan cards (CRIT-3), `/me` call fails, analytics not loading.

## Acceptance Criteria

### CSP connect-src Fix

- [x] AC1: `connect-src` directive includes `https://api.smartlic.tech` (via wildcard `*.smartlic.tech`)
- [x] AC2: `connect-src` directive includes `https://*.smartlic.tech` (wildcard for future subdomains)
- [x] AC3: `/planos` page renders plan cards — `GET /plans` returns 200 from `api.smartlic.tech`
- [x] AC4: `GET /me` call from frontend to `api.smartlic.tech` returns 200, no longer blocked by CSP

### CSP script-src Fix

- [x] AC5: `script-src` directive includes `https://static.cloudflareinsights.com`
- [x] AC6: Cloudflare Insights beacon loads without CSP errors in browser console

### Verification

- [x] AC7: No CSP violation errors in browser console on `/`, `/buscar`, `/planos`, `/ajuda` (verified via Playwright)
- [x] AC8: Network tab shows successful requests to `api.smartlic.tech` (`/plans` 200, `/me` 200)

### Deployment

- [x] AC9: Deployed to production via Railway auto-deploy (commit fc3669c pushed to main)
- [x] AC10: Verified CSP headers in production via `curl -I https://smartlic.tech` — confirmed `*.smartlic.tech` in `connect-src` and `cloudflareinsights.com` in `script-src`

## Technical Notes

- CSP is likely configured in `next.config.js` or `middleware.ts`
- Current `connect-src`: `'self' https://*.supabase.co https://*.supabase.in https://api.stripe.com https://*.railway.app https://*.ingest.sentry.io`
- Need to add: `https://api.smartlic.tech` (or `https://*.smartlic.tech`)
- Current `script-src`: `'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com`
- Need to add: `https://static.cloudflareinsights.com`

## Dependencies

- None (standalone fix)

## Blocks

- STORY-231 (header auth state — needs both CSP fix + JWT fix)
- CRIT-3 (plans page rendering)

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/next.config.js` | Modified | Added `https://*.smartlic.tech` to `connect-src` and `https://static.cloudflareinsights.com` to `script-src` |
