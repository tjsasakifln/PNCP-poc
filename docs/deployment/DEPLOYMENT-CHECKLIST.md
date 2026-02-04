# STORY-165 Staging Deployment Checklist

**Date:** 2026-02-04
**Deployer:** _______________
**Start Time:** _______________

---

## Pre-Deployment (COMPLETE)

- [x] Backend tests passing
- [x] Frontend tests passing (69/69)
- [x] Git status clean
- [x] Changes committed (51d9d47)
- [x] Changes pushed to GitHub
- [x] Deployment docs created

---

## Railway Backend Deployment

- [ ] Login to Railway dashboard
- [ ] Navigate to bidiq-uniformes project
- [ ] Create staging environment (if not exists)
- [ ] Configure GitHub integration
- [ ] Deploy commit 51d9d47
- [ ] Set ENABLE_NEW_PRICING=true
- [ ] Set SUPABASE_URL
- [ ] Set SUPABASE_SERVICE_KEY
- [ ] Set OPENAI_API_KEY
- [ ] Set PNCP_API_URL
- [ ] Set ENVIRONMENT=staging
- [ ] Wait for build completion
- [ ] Record staging URL: _______________
- [ ] Test /health endpoint
- [ ] Check logs for errors

**Backend URL:** _______________
**Deploy Time:** _______________
**Status:** _______________

---

## Vercel Frontend Deployment

- [ ] Login to Vercel dashboard
- [ ] Navigate to pncp-poc project
- [ ] Create new deployment
- [ ] Select main branch
- [ ] Select commit 51d9d47
- [ ] Set NEXT_PUBLIC_ENABLE_NEW_PRICING=true
- [ ] Set NEXT_PUBLIC_BACKEND_URL (from Railway)
- [ ] Set NEXT_PUBLIC_SUPABASE_URL
- [ ] Set NEXT_PUBLIC_SUPABASE_ANON_KEY
- [ ] Set NEXT_PUBLIC_ENVIRONMENT=staging
- [ ] Deploy to preview/staging
- [ ] Wait for build completion
- [ ] Record staging URL: _______________
- [ ] Test frontend loads
- [ ] Check logs for errors

**Frontend URL:** _______________
**Deploy Time:** _______________
**Status:** _______________

---

## Post-Deployment Validation

### Health Checks
- [ ] Backend /health returns 200
- [ ] Frontend homepage returns 200
- [ ] No critical errors in Railway logs
- [ ] No critical errors in Vercel logs

### API Endpoint Tests
- [ ] POST /api/buscar works
- [ ] GET /api/me works (NEW - STORY-165)
- [ ] GET /api/setores works
- [ ] Feature flag active (ENABLE_NEW_PRICING=true)

### UI Tests
- [ ] Login page loads
- [ ] Registration page loads
- [ ] Main search page loads
- [ ] Plan upgrade modal appears
- [ ] UF restrictions work
- [ ] AI summary restriction works

**Validation Time:** _______________
**Issues Found:** _______________

---

## Smoke Tests

See: docs/deployment/staging-smoke-test-checklist.md

- [ ] User registration with new plan structure
- [ ] Login and /api/me endpoint
- [ ] Plan upgrade flow (Basico → Avancado)
- [ ] UF limit enforcement (1 UF for Basico)
- [ ] AI summary restriction (disabled for Basico)
- [ ] Multi-sector restriction (disabled for Basico)
- [ ] Search with plan limits
- [ ] Download with capability checks

**Smoke Test Time:** _______________
**Pass Rate:** _____ / 8
**Critical Issues:** _______________

---

## Monitoring Setup

- [ ] Railway logs streaming
- [ ] Vercel logs streaming
- [ ] Error tracking active
- [ ] Performance metrics baseline recorded
- [ ] Alerting configured

**Monitoring Enabled:** _______________

---

## Documentation

- [ ] Update STORY-165 with deployment URLs
- [ ] Record any deployment issues
- [ ] Document environment variable values (secure location)
- [ ] Update rollback plan with specific URLs
- [ ] Notify team in Slack #deployments

**Documentation Complete:** _______________

---

## Sign-Off

**Deployed By:** _______________
**Date/Time:** _______________
**Deployment Status:** [ ] SUCCESS [ ] FAILED [ ] PARTIAL

**Backend Status:** [ ] LIVE [ ] FAILED [ ] ROLLED BACK
**Frontend Status:** [ ] LIVE [ ] FAILED [ ] ROLLED BACK

**Issues:** _______________

**Next Steps:** _______________

---

## Rollback (If Needed)

- [ ] Railway: Revert to commit 682ca0e
- [ ] Vercel: Revert to previous deployment
- [ ] Set ENABLE_NEW_PRICING=false
- [ ] Notify team
- [ ] Document rollback reason

**Rollback Time:** _______________
**Rollback Reason:** _______________

