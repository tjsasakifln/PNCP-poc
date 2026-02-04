# STORY-165 Quick Deployment Guide

## Status: READY TO DEPLOY
**Commit:** 51d9d47 | **Tests:** Passing | **Code:** Pushed

---

## Railway (Backend) - 5 minutes

### Step 1: Dashboard
https://railway.app/ → bidiq-uniformes → Create staging env

### Step 2: Deploy
- Source: GitHub main branch
- Commit: 51d9d47
- Wait for build (~3-5 min)

### Step 3: Environment Variables
```
ENABLE_NEW_PRICING=true
SUPABASE_URL=<get-from-devops>
SUPABASE_SERVICE_KEY=<get-from-devops>
OPENAI_API_KEY=<get-from-devops>
PNCP_API_URL=https://pncp.gov.br/api/consulta/v1
ENVIRONMENT=staging
```

### Step 4: Test
```bash
curl <railway-url>/health
```

---

## Vercel (Frontend) - 5 minutes

### Step 1: Dashboard
https://vercel.com/ → pncp-poc → New deployment

### Step 2: Deploy
- Branch: main
- Commit: 51d9d47
- Target: Preview/Staging

### Step 3: Environment Variables
```
NEXT_PUBLIC_ENABLE_NEW_PRICING=true
NEXT_PUBLIC_BACKEND_URL=<railway-url-from-above>
NEXT_PUBLIC_SUPABASE_URL=<get-from-devops>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<get-from-devops>
NEXT_PUBLIC_ENVIRONMENT=staging
```

### Step 4: Test
```bash
curl <vercel-url>
```

---

## Validation - 5 minutes

### Critical Tests
1. Backend health: `curl <railway-url>/health`
2. Frontend loads: `curl <vercel-url>`
3. New /api/me: `curl <railway-url>/api/me -H "Authorization: Bearer <token>"`
4. Feature flag active: Check logs for ENABLE_NEW_PRICING=true

### Success Criteria
- [ ] Backend returns 200
- [ ] Frontend returns 200
- [ ] /api/me returns user with capabilities
- [ ] No errors in Railway logs
- [ ] No errors in Vercel logs

---

## Rollback (if needed)

### Railway
Deployments → Previous (682ca0e) → Redeploy

### Vercel
Deployments → Previous → Promote

---

## Support

**Deployment Docs:** docs/deployment/
**Rollback Plan:** docs/deployment/rollback-plan-story165.md
**Smoke Tests:** docs/deployment/smoke-tests-story165.md
**On-Call:** docs/deployment/oncall-quick-reference-story165.md

