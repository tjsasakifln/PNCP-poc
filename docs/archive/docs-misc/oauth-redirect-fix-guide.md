# OAuth Redirect Fix Guide - SmartLic

## Problem

Users logging in with Google OAuth are redirected to:
1. ❌ `railway.app` domain instead of `smartlic.tech`
2. ❌ Homepage `/` instead of `/buscar` (logged-in area)

## Root Cause

1. **Domain Issue**: Frontend code was using `window.location.origin` for OAuth redirects, which could be either `railway.app` or `smartlic.tech` depending on which URL the user accessed
2. **Supabase Configuration**: Redirect URLs in Supabase dashboard were not configured for the correct domains

## Solution Implemented

### 1. ✅ Environment Variables (Completed)

Added to Railway (`bidiq-frontend` service):
```bash
NEXT_PUBLIC_CANONICAL_URL=https://smartlic.tech
NEXT_PUBLIC_APP_URL=https://app.smartlic.tech
```

### 2. ✅ Code Changes (Completed)

**File: `frontend/app/components/AuthProvider.tsx`**

Changed from:
```typescript
redirectTo: `${window.location.origin}/auth/callback`
```

To:
```typescript
const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;
redirectTo: `${canonicalUrl}/auth/callback`
```

This ensures OAuth redirects ALWAYS go to `smartlic.tech`, not `railway.app`.

### 3. ⚠️ Supabase Dashboard Configuration (Manual Step Required)

**IMPORTANT**: The Supabase Management API does not reliably persist redirect URLs. You must configure this manually in the Supabase Dashboard.

#### Steps:

1. Go to: https://app.supabase.com/project/fqqyovlzdzimiwfofdjk/auth/url-configuration

2. Under **"Redirect URLs"** section, add these URLs (one per line):
   ```
   https://smartlic.tech/auth/callback
   https://app.smartlic.tech/auth/callback
   http://localhost:3000/auth/callback
   ```

3. **Remove** any URLs with `railway.app` domain (if present)

4. Click **"Save"**

5. Wait ~30 seconds for changes to propagate

#### Verification:

After configuration, test:
- Visit https://smartlic.tech/login
- Click "Entrar com Google"
- You should be redirected to `/auth/callback` (not homepage)
- After authentication, you should land on `/buscar`

### 4. Domain Redirect Middleware (Next Step)

See Task #3 - Will implement middleware to automatically redirect `railway.app` URLs to `smartlic.tech`.

## Testing Checklist

- [ ] Supabase redirect URLs configured in dashboard
- [ ] Railway environment variables set
- [ ] Frontend code deployed with changes
- [ ] Test Google OAuth from https://smartlic.tech/login
- [ ] Verify redirect goes to `/auth/callback`
- [ ] Verify final landing page is `/buscar`
- [ ] Test from mobile device
- [ ] Test from different browser/incognito mode

## Rollback Plan

If issues occur:
1. Revert AuthProvider.tsx changes
2. Remove environment variables from Railway
3. Restore old Supabase redirect URLs

## Related Files

- `frontend/app/components/AuthProvider.tsx` - OAuth redirect logic
- `frontend/app/auth/callback/page.tsx` - Callback handler
- `scripts/configure-supabase-oauth.js` - Automation script (API not working reliably)
- `scripts/check-supabase-config.js` - Check current configuration

## Next Steps

1. **Immediate**: Configure Supabase redirect URLs manually (see Step 3)
2. **Deploy**: Push code changes to production
3. **Test**: Complete testing checklist above
4. **Implement**: Domain redirect middleware (Task #3)
5. **Monitor**: Watch for any auth errors in production logs
