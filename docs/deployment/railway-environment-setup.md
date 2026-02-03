# Railway Environment Setup Guide

This document lists all required environment variables for deploying Smart PNCP to Railway.

## Critical Issue: Authentication Not Working in Production

If authentication is not working after deployment, the most common cause is **missing environment variables** in Railway.

---

## Backend Service (bidiq-backend)

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | `https://yourproject.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (admin access) | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `SUPABASE_ANON_KEY` | Supabase anonymous key (public) | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `OPENAI_API_KEY` | OpenAI API key for LLM summaries | `sk-...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_USER_IDS` | (none) | Comma-separated list of admin user UUIDs |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PNCP_TIMEOUT` | `30` | PNCP API timeout in seconds |
| `PNCP_MAX_RETRIES` | `5` | Max retries for PNCP API |
| `STRIPE_SECRET_KEY` | (none) | Stripe API key for billing |
| `STRIPE_WEBHOOK_SECRET` | (none) | Stripe webhook signing secret |

### Setting Variables in Railway

```bash
# Using Railway CLI
railway variables set SUPABASE_URL="https://yourproject.supabase.co"
railway variables set SUPABASE_SERVICE_ROLE_KEY="eyJ..."
railway variables set SUPABASE_ANON_KEY="eyJ..."
railway variables set OPENAI_API_KEY="sk-..."
railway variables set ADMIN_USER_IDS="uuid1,uuid2"
```

Or via Railway Dashboard:
1. Go to your project → bidiq-backend service
2. Click "Variables" tab
3. Add each variable

---

## Frontend Service (bidiq-frontend)

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BACKEND_URL` | URL of the backend service | `https://bidiq-backend.up.railway.app` |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | `https://yourproject.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | `eyJ...` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_APP_NAME` | `Smart PNCP` | Application display name |
| `NEXT_PUBLIC_LOGO_URL` | `/logo.svg` | Logo URL |
| `NEXT_PUBLIC_MIXPANEL_TOKEN` | (none) | Mixpanel analytics token |

### Important Notes

1. **`BACKEND_URL` is critical** - Without this, the frontend will try to reach `http://localhost:8000` which doesn't exist in production.

2. **Use Railway's internal networking** if both services are in the same project:
   ```
   BACKEND_URL=http://bidiq-backend.railway.internal:8000
   ```
   Or use the public URL:
   ```
   BACKEND_URL=https://bidiq-backend.up.railway.app
   ```

3. **`NEXT_PUBLIC_*` variables** are embedded at build time, so you need to redeploy after changing them.

### Setting Variables in Railway

```bash
# Using Railway CLI
railway variables set BACKEND_URL="https://bidiq-backend.up.railway.app"
railway variables set NEXT_PUBLIC_SUPABASE_URL="https://yourproject.supabase.co"
railway variables set NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJ..."
```

---

## Getting Supabase Keys

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (backend only, keep secret!)

---

## Verification Checklist

After setting variables, verify:

### Backend Health Check
```bash
curl https://bidiq-backend.up.railway.app/health
# Should return: {"status": "healthy", ...}
```

### Frontend Connectivity
```bash
curl -X POST https://bidiq-frontend.up.railway.app/api/buscar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_VALID_JWT" \
  -d '{"ufs":["SP"],"data_inicial":"2026-01-01","data_final":"2026-01-31"}'
```

### Authentication Test
```bash
curl https://bidiq-backend.up.railway.app/me \
  -H "Authorization: Bearer YOUR_VALID_JWT"
# Should return user profile, NOT 401
```

---

## Common Issues

### Issue: "Backend indisponivel em http://localhost:8000"
**Cause:** `BACKEND_URL` not set in frontend service
**Fix:** Set `BACKEND_URL` to the actual Railway backend URL

### Issue: 401 on all authenticated requests
**Cause:** `SUPABASE_SERVICE_ROLE_KEY` not set in backend
**Fix:** Add the service role key from Supabase dashboard

### Issue: "Token invalido ou expirado" on valid tokens
**Cause:** Backend using wrong Supabase URL or key
**Fix:** Verify `SUPABASE_URL` and keys match your Supabase project

### Issue: OAuth callback fails
**Cause:** Supabase redirect URL not configured
**Fix:** In Supabase Dashboard → Authentication → URL Configuration, add:
```
https://bidiq-frontend.up.railway.app/auth/callback
```

---

## Security Notes

1. **Never commit `.env` files** to git
2. **Rotate keys** if they were ever exposed
3. **Use Railway's secrets management** instead of hardcoding values
4. **Restrict `SUPABASE_SERVICE_ROLE_KEY`** to backend only - never expose to frontend

---

## Quick Setup Script

Create a `.env.railway` file locally (DO NOT COMMIT):

```bash
# Backend
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
OPENAI_API_KEY=sk-...
ADMIN_USER_IDS=

# Frontend
BACKEND_URL=https://bidiq-backend.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://yourproject.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_APP_NAME=Smart PNCP
```

Then use Railway CLI to set all at once:
```bash
# For backend
cd backend
railway link
cat ../.env.railway | grep -E '^(SUPABASE|OPENAI|ADMIN)' | while read line; do
  railway variables set "$line"
done

# For frontend
cd ../frontend
railway link
cat ../.env.railway | grep -E '^(BACKEND|NEXT_PUBLIC)' | while read line; do
  railway variables set "$line"
done
```
