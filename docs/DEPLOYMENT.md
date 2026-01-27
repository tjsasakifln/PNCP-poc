# 🚀 BidIQ Uniformes - Production Deployment Guide

**Version:** 1.0
**Last Updated:** 2026-01-25
**Target Platforms:** Vercel (Frontend) + Railway (Backend)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Backend Deployment (Railway)](#phase-1-backend-deployment-railway)
4. [Phase 2: Frontend Deployment (Vercel)](#phase-2-frontend-deployment-vercel)
5. [Phase 3: Integration & Validation](#phase-3-integration--validation)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)
8. [Cost Estimates](#cost-estimates)
9. [Monitoring & Observability](#monitoring--observability)

---

## Overview

This guide provides step-by-step instructions for deploying the BidIQ Uniformes POC to production using:

- **Frontend:** Vercel (Next.js optimized platform)
- **Backend:** Railway (Python/FastAPI containerized deployment)

**Architecture:**
```
[User Browser]
      ↓
[Vercel - Next.js App] ← (HTTPS) → [Railway - FastAPI Backend] → [PNCP API]
      ↓                                    ↓
  Static Assets                      [OpenAI API]
```

**Expected Deployment Time:** ~30 minutes (excluding account setup)

---

## Prerequisites

### Required Accounts
- ✅ GitHub account (for code access)
- ✅ Railway account (https://railway.app - sign up with GitHub)
- ✅ Vercel account (https://vercel.com - sign up with GitHub)
- ✅ OpenAI account with API key (https://platform.openai.com)

### Required Tools
```bash
# Node.js 18+ and npm 9+
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 9.0.0

# Railway CLI
npm install -g @railway/cli

# Vercel CLI (optional - can deploy via web UI)
npm install -g vercel

# Git
git --version
```

### Repository Access
Clone the repository if not already done:
```bash
git clone https://github.com/tjsasakifln/PNCP-poc.git
cd PNCP-poc
git checkout main
git pull origin main
```

---

## Phase 1: Backend Deployment (Railway)

**Estimated Time:** 15 minutes

### Step 1.1: Create Railway Project

1. **Login to Railway:**
   ```bash
   railway login
   ```
   - Opens browser for GitHub authentication
   - Click "Authorize Railway"

2. **Initialize Project:**
   ```bash
   railway init
   ```
   - Select "Create new project"
   - Project name: `bidiq-backend` (or your preference)
   - Region: Select closest to your users (e.g., `us-west1`)

3. **Link to Repository (Optional):**
   ```bash
   railway link
   ```
   - Select the created project
   - This enables automatic deployments on git push

### Step 1.2: Configure Environment Variables

1. **Access Railway Dashboard:**
   - Go to https://railway.app/dashboard
   - Select your `bidiq-backend` project
   - Click "Variables" tab

2. **Add Required Variables:**
   ```env
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   PORT=8000
   LOG_LEVEL=INFO
   PNCP_TIMEOUT=30
   PNCP_MAX_RETRIES=5
   PNCP_BACKOFF_BASE=2
   PNCP_BACKOFF_MAX=60
   LLM_MODEL=gpt-4o-mini
   LLM_TEMPERATURE=0.3
   LLM_MAX_TOKENS=500
   ```

   **⚠️ CRITICAL:** Use a production OpenAI API key (not the same as development)

3. **Verify Variables:**
   - Click "Raw Editor" to see all variables
   - Ensure no typos in `OPENAI_API_KEY`

### Step 1.3: Deploy Backend

1. **Deploy from Local:**
   ```bash
   cd backend
   railway up
   ```

   Or deploy via GitHub integration:
   ```bash
   git push origin main  # Triggers automatic deployment
   ```

2. **Monitor Deployment:**
   - Watch logs in Railway dashboard under "Deployments" tab
   - Look for: `Application startup complete` and `Uvicorn running on http://0.0.0.0:8000`

3. **Get Deployment URL:**
   - Railway dashboard → "Settings" → "Domains"
   - Default format: `https://<project-name>-production.up.railway.app`
   - Example: `https://bidiq-backend-production.up.railway.app`

### Step 1.4: Verify Backend Health

```bash
# Replace with your actual Railway URL
export BACKEND_URL=https://bidiq-backend-production.up.railway.app

# Test health endpoint
curl $BACKEND_URL/health

# Expected response:
# {"status":"healthy","timestamp":"2026-01-25T..."}

# Test API docs (should load in browser)
open $BACKEND_URL/docs
```

**✅ Phase 1 Complete:** Backend is deployed and accessible.

---

## Phase 2: Frontend Deployment (Vercel)

**Estimated Time:** 10 minutes

### Step 2.1: Prepare Vercel Configuration

1. **Ensure `vercel.json` exists:**
   ```bash
   cat vercel.json  # Should show Vercel configuration
   ```

2. **Update Environment Variable Placeholder:**
   - Note your Railway backend URL from Phase 1
   - You'll set this in Vercel dashboard next

### Step 2.2: Deploy to Vercel

**Option A: Vercel CLI (Recommended)**

1. **Login:**
   ```bash
   vercel login
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel --prod
   ```

   - Select "Link to existing project" or "Create new project"
   - Project name: `bidiq-uniformes` (or your preference)
   - Framework: Next.js (auto-detected)
   - Build command: `npm run build` (default)
   - Output directory: `.next` (default)

3. **Get Deployment URL:**
   - Output will show: `Production: https://bidiq-uniformes.vercel.app`

**Option B: Vercel Web UI**

1. Go to https://vercel.com/new
2. Import Git Repository → Select `PNCP-poc`
3. Configure Project:
   - Root Directory: `frontend`
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`
4. Click "Deploy"

### Step 2.3: Configure Frontend Environment Variables

1. **Access Vercel Dashboard:**
   - Go to https://vercel.com/dashboard
   - Select `bidiq-uniformes` project
   - Settings → Environment Variables

2. **Add Backend URL:**
   ```env
   NEXT_PUBLIC_BACKEND_URL=https://bidiq-backend-production.up.railway.app
   ```

   - Environment: Production
   - Click "Save"

3. **Redeploy (Required):**
   ```bash
   vercel --prod
   ```
   - Environment variables only apply to new deployments

### Step 2.4: Verify Frontend

1. **Open in Browser:**
   ```bash
   open https://bidiq-uniformes.vercel.app
   ```

2. **Visual Check:**
   - ✅ Page loads without errors
   - ✅ UF selection buttons render
   - ✅ Date range picker shows default 7-day range
   - ✅ "Buscar Licitações" button visible

**✅ Phase 2 Complete:** Frontend is deployed and accessible.

---

## Phase 3: Integration & Validation

**Estimated Time:** 10 minutes

### Step 3.1: Update Backend CORS

Railway backend must allow requests from Vercel frontend.

1. **Edit `backend/main.py`:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",  # Keep for local dev
           "https://bidiq-uniformes.vercel.app",  # ADD THIS
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Commit and Deploy:**
   ```bash
   git add backend/main.py
   git commit -m "feat(backend): add Vercel domain to CORS allow_origins"
   git push origin main
   ```

3. **Wait for Railway Redeployment:**
   - Railway dashboard shows new deployment (auto-triggered by git push)
   - Wait ~2-3 minutes for build + deploy

### Step 3.2: End-to-End Smoke Test

**Test Scenario: Search for Licitações**

1. Open frontend: https://bidiq-uniformes.vercel.app

2. **Select UFs:**
   - Click "SP" (São Paulo)
   - Click "RJ" (Rio de Janeiro)

3. **Set Date Range:**
   - Start: 7 days ago (default)
   - End: Today (default)

4. **Submit Search:**
   - Click "Buscar Licitações"
   - Loading indicator should appear

5. **Verify Results:**
   - ✅ Results section appears after 5-15 seconds
   - ✅ Executive summary displays (if OpenAI key valid)
   - ✅ Statistics show: X oportunidades, R$ Y valor total
   - ✅ Download button appears
   - ✅ Clicking download triggers Excel file download

6. **Verify Excel:**
   - Open downloaded `.xlsx` file
   - ✅ Data sheet has columns: Código, Objeto, Órgão, UF, etc.
   - ✅ Metadata sheet shows generation timestamp
   - ✅ Green header formatting applied

**⚠️ If Errors Occur:** See [Troubleshooting](#troubleshooting)

### Step 3.3: Monitoring Setup

**Railway (Backend):**
1. Dashboard → "Observability" tab
2. Enable metrics:
   - ✅ CPU Usage
   - ✅ Memory Usage
   - ✅ Network I/O
   - ✅ Request Rate

**Vercel (Frontend):**
1. Dashboard → "Analytics" tab
2. Enable:
   - ✅ Web Vitals (LCP, FID, CLS)
   - ✅ Page Views
   - ✅ Visitor Count

**✅ Phase 3 Complete:** Full-stack integration validated.

---

## Troubleshooting

### Issue: CORS Error (Blocked by Browser)

**Symptom:**
```
Access to fetch at 'https://railway.app' from origin 'https://vercel.app'
has been blocked by CORS policy
```

**Solution:**
1. Verify `backend/main.py` includes Vercel domain in `allow_origins`
2. Redeploy backend: `git push origin main`
3. Clear browser cache: Ctrl+Shift+R (hard refresh)

---

### Issue: OpenAI API Error (401 Unauthorized)

**Symptom:**
- Results load but "Resumo Executivo" shows generic fallback text
- Backend logs show: `openai.AuthenticationError`

**Solution:**
1. Verify `OPENAI_API_KEY` in Railway dashboard:
   - Settings → Variables → Check key format: `sk-proj-...`
2. Test key validity:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer sk-proj-YOUR-KEY"
   ```
3. Ensure key has sufficient quota (https://platform.openai.com/usage)

---

### Issue: Railway Build Fails

**Symptom:**
- Deployment fails with "Build error" in Railway dashboard
- Logs show: `ModuleNotFoundError` or `pip install failed`

**Solution:**
1. Check `backend/requirements.txt` is committed to git
2. Verify Dockerfile syntax:
   ```bash
   docker build -t test-backend -f backend/Dockerfile backend/
   ```
3. Check Railway builder setting: Settings → Build → Builder = `DOCKERFILE`

---

### Issue: Vercel Build Fails

**Symptom:**
- Deployment fails with "Build failed" in Vercel dashboard
- Logs show: `npm ERR!` or `Module not found`

**Solution:**
1. Verify `frontend/package.json` has correct dependencies
2. Test build locally:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
3. Check Vercel root directory: Settings → General → Root Directory = `frontend`

---

### Issue: PNCP API Timeout

**Symptom:**
- Search takes >30 seconds
- Backend logs: `httpx.ReadTimeout`

**Solution:**
1. Increase timeout in Railway variables: `PNCP_TIMEOUT=60`
2. Check PNCP API status: https://pncp.gov.br
3. Retry with smaller date range (< 7 days)

---

### Issue: High Railway Costs

**Symptom:**
- Railway usage exceeds free tier ($5 credit)
- Bill shows unexpected charges

**Solution:**
1. Review usage: Dashboard → "Usage" tab
2. Optimize:
   - Reduce `uvicorn --workers` from 2 to 1
   - Enable sleep mode: Settings → Sleep after inactivity = 15 minutes
3. Upgrade to Hobby plan ($5/month flat rate) if POC goes to production

---

## Rollback Procedures

### Backend Rollback (Railway)

1. **Rollback to Previous Deployment:**
   - Railway Dashboard → "Deployments" tab
   - Find last stable deployment (green checkmark)
   - Click "•••" → "Redeploy"

2. **Rollback via CLI:**
   ```bash
   railway rollback
   ```

### Frontend Rollback (Vercel)

1. **Rollback to Previous Deployment:**
   - Vercel Dashboard → "Deployments" tab
   - Find last stable deployment
   - Click "•••" → "Promote to Production"

2. **Rollback via CLI:**
   ```bash
   vercel rollback
   ```

### Emergency Localhost Fallback

If both platforms fail:

1. **Point frontend to localhost backend:**
   - Vercel Dashboard → Environment Variables
   - Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`
   - Redeploy Vercel

2. **Run backend locally:**
   ```bash
   docker-compose up backend
   ```

3. **Notify stakeholders:** "Production deployment experiencing issues, using local fallback"

---

## Cost Estimates

### Monthly Costs (Estimated)

| Platform | Tier | Cost | Usage Included |
|----------|------|------|----------------|
| **Railway** (Backend) | Free Trial | $0 | $5 credit (then $0.20/GB RAM/month) |
| **Railway** (Backend) | Hobby | $5/month | Flat rate, no usage limits |
| **Vercel** (Frontend) | Free | $0 | 100GB bandwidth, 6000 build minutes |
| **OpenAI API** | Pay-as-you-go | ~$1-5/month | gpt-4o-mini: $0.150/1M input tokens |

**Total Estimated Cost (POC):** $5-10/month

**Optimization Tips:**
- Use Railway free tier ($5 credit) for initial testing
- Upgrade to Hobby plan ($5/month) once credit depletes
- Monitor OpenAI usage to avoid unexpected bills
- Vercel Free tier is sufficient for POC (low traffic)

---

## Monitoring & Observability

### Key Metrics to Track

**Backend (Railway):**
- Response time: Target < 5 seconds (95th percentile)
- Error rate: Target < 1%
- Memory usage: Target < 512MB
- CPU usage: Target < 50%

**Frontend (Vercel):**
- Largest Contentful Paint (LCP): Target < 2.5s
- First Input Delay (FID): Target < 100ms
- Cumulative Layout Shift (CLS): Target < 0.1
- Page views per day

### Alerting (Optional)

**Railway:**
- Settings → Alerts → Add alert
  - CPU > 80% for 5 minutes
  - Memory > 90% for 5 minutes
  - Health check failures > 3 consecutive

**Vercel:**
- Settings → Notifications
  - Build failures
  - Deployment errors

---

## Appendix: Useful Commands

### Railway CLI Commands
```bash
railway login              # Authenticate with Railway
railway init               # Create new project
railway link               # Link to existing project
railway up                 # Deploy current directory
railway logs               # Stream application logs
railway run <command>      # Run command in Railway environment
railway rollback           # Rollback to previous deployment
railway status             # Show project status
```

### Vercel CLI Commands
```bash
vercel login               # Authenticate with Vercel
vercel                     # Deploy to preview environment
vercel --prod              # Deploy to production
vercel logs                # View deployment logs
vercel rollback            # Rollback to previous deployment
vercel env ls              # List environment variables
vercel env add             # Add environment variable
```

### Health Check Commands
```bash
# Backend health check
curl https://bidiq-backend-production.up.railway.app/health

# Frontend health check (should return HTML)
curl https://bidiq-uniformes.vercel.app

# API docs
open https://bidiq-backend-production.up.railway.app/docs
```

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **Next.js Deployment:** https://nextjs.org/docs/deployment
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **GitHub Issues:** https://github.com/tjsasakifln/PNCP-poc/issues

---

**Document Version:** 1.0
**Maintained By:** BidIQ Engineering Team
**Last Review:** 2026-01-25
