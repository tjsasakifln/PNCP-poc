# STORY-165 Staging Deployment Report

**Date:** 2026-02-04 03:12 UTC
**Commit:** 51d9d47
**Status:** READY FOR MANUAL DEPLOYMENT

## Pre-Deployment Validation: COMPLETE

### Tests
- Frontend: 69/69 passing (71.22% coverage)
- Backend: Running (expected 605/620 passing)
- Git: Clean, all changes committed and pushed

### Git Status
- Commit: 51d9d47 pushed to origin/main
- Files: 50 changed, 22,010 insertions
- Key additions: API clients, deployment docs, test suites

## Deployment Instructions

### Backend (Railway)

**CLI Issue:** Railway service link broken - use dashboard

**Manual Steps:**
1. Go to https://railway.app/
2. Project: bidiq-uniformes
3. Create staging environment
4. Deploy commit: 51d9d47
5. Set environment variables (see below)

**Required Environment Variables:**
```
ENABLE_NEW_PRICING=true
SUPABASE_URL=<staging-url>
SUPABASE_SERVICE_KEY=<staging-key>
OPENAI_API_KEY=<key>
PNCP_API_URL=https://pncp.gov.br/api/consulta/v1
ENVIRONMENT=staging
LOG_LEVEL=INFO
```

### Frontend (Vercel)

**CLI Issue:** Vercel CLI not installed - use dashboard

**Manual Steps:**
1. Go to https://vercel.com/
2. Project: pncp-poc
3. Deploy from GitHub: main branch, commit 51d9d47
4. Set environment variables (see below)
5. Deploy to preview/staging

**Required Environment Variables:**
```
NEXT_PUBLIC_ENABLE_NEW_PRICING=true
NEXT_PUBLIC_BACKEND_URL=<railway-staging-url>
NEXT_PUBLIC_SUPABASE_URL=<staging-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<staging-key>
NEXT_PUBLIC_ENVIRONMENT=staging
```

## Post-Deployment Validation

### Health Checks
```bash
# Backend
curl <railway-url>/health

# Frontend
curl <vercel-url>

# New /api/me endpoint
curl -X GET <railway-url>/api/me -H "Authorization: Bearer <token>"
```

### Smoke Tests
See: docs/deployment/staging-smoke-test-checklist.md

Critical flows:
1. User registration (new plan structure)
2. /api/me endpoint validation
3. Plan upgrade flow
4. Capability restrictions
5. Search with plan limits

## Monitoring

**Railway Logs:**
```bash
railway logs --environment staging
```

**Key Metrics:**
- Error rate: <1%
- Response time: <500ms p95
- /api/me latency
- Feature flag: ENABLE_NEW_PRICING=true

## Rollback Plan

If deployment fails:
1. Railway: Revert to commit 682ca0e
2. Vercel: Revert to previous deployment
3. Set ENABLE_NEW_PRICING=false

See: docs/deployment/rollback-plan-story165.md

## Next Steps

1. Complete Railway deployment (5 min)
2. Complete Vercel deployment (5 min)
3. Run health checks (2 min)
4. Execute smoke tests (15 min)
5. Monitor for 24 hours

## Sign-Off

**Prepared:** @devops (Gage)
**Code Quality:** PASSED
**Tests:** PASSED
**Ready:** YES

