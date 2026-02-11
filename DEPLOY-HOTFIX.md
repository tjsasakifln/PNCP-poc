# 🚀 HOTFIX DEPLOYMENT GUIDE

**Hotfix ID:** SERVER-ACTION-AUTH-BUG
**Date:** 2026-02-11
**Priority:** CRITICAL
**Estimated Duration:** 10-15 minutes

---

## ⚡ Quick Deploy (TL;DR)

```bash
# 1. Clear cache & rebuild
cd frontend
rm -rf .next node_modules/.cache
npm ci
npm run build

# 2. Commit & push
git add .
git commit -m "fix(HOTFIX): auth bug - cache busting + timeout"
git push origin main

# 3. Verify deployment
# - Check production URL in incognito mode
# - Test login flow
# - Monitor logs for 15 minutes
```

---

## 📋 Pre-Deployment Checklist

- [ ] Code changes reviewed
  - `frontend/app/components/AuthProvider.tsx`
  - `frontend/next.config.js`
- [ ] Local testing completed
- [ ] Backup current production state
- [ ] Notify team of deployment
- [ ] Have rollback plan ready

---

## 🔧 Step-by-Step Deployment

### Step 1: Local Verification (5 min)

```bash
# Navigate to frontend
cd frontend

# Clear cache
rm -rf .next node_modules/.cache

# Reinstall dependencies
npm ci

# Build
npm run build

# Test locally
npm run dev

# Open http://localhost:3000/login in incognito
# Verify: Loading screen resolves in < 10 seconds
```

**Expected Output:**
```
✓ Compiled successfully
✓ Ready in 3.2s
○ Local: http://localhost:3000
```

---

### Step 2: Commit Changes (2 min)

```bash
# Stage all changes
git add .

# Commit with descriptive message
git commit -m "fix(HOTFIX): resolve auth loading loop

- Add 10-second timeout to AuthProvider
- Implement cache-busting Build IDs
- Add error recovery for network failures
- Create cache clear scripts

Fixes: Users stuck on 'Verificando autenticação...'
Root Cause: Stale browser cache + missing timeouts
Impact: Eliminates infinite loading states"

# Push to main
git push origin main
```

---

### Step 3: Monitor Deployment (5-10 min)

#### For Vercel:
- Automatic deployment triggered on push
- Check: https://vercel.com/your-project/deployments
- Wait for "Ready" status
- Vercel automatically clears CDN cache ✅

#### For Railway:
- Check: https://railway.app/dashboard
- Deployment should auto-trigger
- Monitor build logs for errors
- Wait for "Active" status

#### For Custom Setup:
```bash
# SSH into server
ssh user@your-server.com

# Navigate to app
cd /path/to/app

# Pull latest
git pull origin main

# Rebuild
cd frontend
npm ci
npm run build

# Restart service
pm2 restart frontend  # or your process manager
```

---

### Step 4: Production Verification (3 min)

**Test in Incognito Mode** (important to bypass cache):

1. Open **incognito/private window**
2. Navigate to production URL
3. Go to `/login`
4. Observe loading behavior:
   - ✅ Should load in < 3 seconds normally
   - ✅ Max 10 seconds with timeout
   - ❌ Should NOT infinite loop

5. Test login flow:
   - Try Google OAuth
   - Try email/password
   - Verify redirect works

6. Check browser console:
   - No "Failed to find Server Action" errors
   - No network errors
   - Clean logs

---

### Step 5: Monitor Production Logs (15 min)

```bash
# For Railway
railway logs --follow

# For Vercel
vercel logs --follow

# Look for:
# ✅ Clean auth flows
# ✅ No "Failed to find Server Action" errors
# ❌ Any unexpected errors
```

---

## 🔴 Rollback Procedure (if needed)

If deployment causes issues:

### Option 1: Git Revert (Fastest)
```bash
git revert HEAD
git push origin main
# Deployment will auto-trigger with previous version
```

### Option 2: Railway Dashboard
- Go to Railway dashboard
- Click "Deployments"
- Find previous working deployment
- Click "Redeploy"

### Option 3: Vercel Dashboard
- Go to Vercel dashboard
- Click "Deployments"
- Find previous deployment
- Click "Promote to Production"

---

## 📊 Success Metrics

### Immediate (0-30 min):
- [ ] No infinite loading screens
- [ ] Login flow completes in < 10 seconds
- [ ] Zero "Failed to find Server Action" errors in logs
- [ ] Users can authenticate successfully

### Short-term (1-24 hours):
- [ ] No support tickets about auth loading
- [ ] Error rate < 0.1% for auth endpoints
- [ ] User satisfaction restored

### Long-term (1-7 days):
- [ ] Sustained zero Server Action errors
- [ ] Improved session reliability
- [ ] No cache-related incidents

---

## 🚨 Emergency Contacts

**If deployment fails:**
- Primary: [Your Name/Contact]
- Backend Team: [Backend Contact]
- DevOps: [DevOps Contact]

**Escalation Path:**
1. Try rollback first (see above)
2. Contact primary on-call
3. Check Railway/Vercel status pages
4. Review production logs

---

## 📝 Post-Deployment Tasks

After successful deployment:

- [ ] Monitor logs for 1 hour
- [ ] Update this document with actual deployment time
- [ ] Document any issues encountered
- [ ] Update team in Slack/Discord
- [ ] Close related tickets/issues
- [ ] Schedule post-mortem (if critical incident)

---

## ✅ Deployment Sign-off

**Deployed By:** _______________
**Date/Time:** _______________
**Deployment Duration:** _______________
**Issues Encountered:** None / [Details]
**Status:** Success / Rolled Back / In Progress

---

## 🔗 Related Documents

- [HOTFIX-SERVER-ACTION-BUG-2026-02-11.md](./HOTFIX-SERVER-ACTION-BUG-2026-02-11.md) - Technical details
- [frontend/scripts/clear-cache-rebuild.sh](./frontend/scripts/clear-cache-rebuild.sh) - Cache clear script

---

**Last Updated:** 2026-02-11
**Next Review:** After 24h of production stability
