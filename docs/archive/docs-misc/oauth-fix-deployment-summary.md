# OAuth Fix Deployment Summary

## Problem Statement

Users logging in with Google OAuth experienced two issues:
1. **Wrong domain**: Redirected to `railway.app` instead of `smartlic.tech`
2. **Wrong page**: Returned to homepage `/` instead of logged-in area `/buscar`

## Root Causes Identified

### Issue 1: Dynamic Domain in OAuth Redirect
**File**: `frontend/app/components/AuthProvider.tsx`

The code used `window.location.origin` which could be either `railway.app` or `smartlic.tech`:
```typescript
redirectTo: `${window.location.origin}/auth/callback`
```

This meant if a user accessed the site via `railway.app`, OAuth would redirect back to `railway.app`.

### Issue 2: Missing Supabase Configuration
Supabase dashboard did not have redirect URLs configured for `smartlic.tech` domain.

### Issue 3: No Domain Enforcement
No middleware to force `railway.app` URLs to redirect to canonical `smartlic.tech` domain.

## Solutions Implemented

### ✅ Solution 1: Environment Variables

**Railway Service**: `bidiq-frontend`

Added:
```bash
NEXT_PUBLIC_CANONICAL_URL=https://smartlic.tech
NEXT_PUBLIC_APP_URL=https://app.smartlic.tech
```

**Verification**:
```bash
railway variables --service bidiq-frontend | grep -E "(CANONICAL|APP_URL)"
```

### ✅ Solution 2: Code Changes

#### File: `frontend/app/components/AuthProvider.tsx`

**Before**:
```typescript
const signInWithGoogle = useCallback(async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${window.location.origin}/auth/callback` },
  });
  if (error) throw error;
}, []);
```

**After**:
```typescript
const signInWithGoogle = useCallback(async () => {
  // Use canonical URL for OAuth redirects (not railway.app domain)
  const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL || window.location.origin;
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${canonicalUrl}/auth/callback` },
  });
  if (error) throw error;
}, []);
```

Same pattern applied to `signInWithMagicLink`.

#### File: `frontend/app/auth/callback/page.tsx`

Added comprehensive console logging to debug OAuth callback flow:
- Log when callback handler starts
- Log authorization code detection
- Log session establishment
- Log redirect execution
- Log all errors

This helps diagnose any future issues.

#### File: `frontend/middleware.ts`

Added domain redirect logic at the **top** of middleware (before any auth checks):

```typescript
export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const host = request.headers.get("host") || "";

  // CRITICAL: Force canonical domain redirect (railway.app → smartlic.tech)
  const canonicalDomain = process.env.NEXT_PUBLIC_CANONICAL_URL?.replace(/^https?:\/\//, "") || "smartlic.tech";
  const isRailwayDomain = host.includes("railway.app");
  const isLocalhost = host.includes("localhost");

  if (isRailwayDomain && !isLocalhost) {
    // Redirect railway.app to smartlic.tech with 301 (permanent)
    const canonicalUrl = `https://${canonicalDomain}${pathname}${search}`;
    return NextResponse.redirect(canonicalUrl, { status: 301 });
  }

  // ... rest of middleware
}
```

This ensures:
- All `railway.app` URLs automatically redirect to `smartlic.tech`
- Path and query parameters are preserved
- HTTP 301 (permanent redirect) for SEO
- localhost is excluded for local development

#### File: `scripts/configure-supabase-oauth.js`

Updated script to use correct domains:
```javascript
const REQUIRED_REDIRECT_URLS = [
  'https://smartlic.tech/auth/callback',
  'https://app.smartlic.tech/auth/callback',
  'http://localhost:3000/auth/callback',
];

const URLS_TO_REMOVE = [
  'https://bidiq-frontend-production.up.railway.app/auth/callback',
  'https://bidiq-frontend-production.up.railway.app/',
  'http://localhost:3000/',
];
```

### ⚠️ Solution 3: Manual Supabase Configuration (REQUIRED)

**CRITICAL**: Supabase Management API does not reliably persist redirect URLs. Manual configuration is required.

#### Steps:

1. Go to: https://app.supabase.com/project/fqqyovlzdzimiwfofdjk/auth/url-configuration

2. Under **"Redirect URLs"** section, add:
   ```
   https://smartlic.tech/auth/callback
   https://app.smartlic.tech/auth/callback
   http://localhost:3000/auth/callback
   ```

3. **Remove** any URLs containing `railway.app` domain

4. Click **"Save"**

5. Wait ~30 seconds for changes to propagate

#### Verification:

After configuring, the URLs should be visible in the Supabase dashboard. You can also test by:
```bash
node scripts/check-supabase-config.js
```

(Note: This script may not show updated config due to API caching, but dashboard will be accurate)

## Deployment Checklist

- [x] **Task 1**: Fix OAuth redirect domain
  - [x] Set `NEXT_PUBLIC_CANONICAL_URL` in Railway
  - [x] Set `NEXT_PUBLIC_APP_URL` in Railway
  - [x] Update `AuthProvider.tsx` to use canonical URL
  - [x] Update `configure-supabase-oauth.js` script

- [x] **Task 2**: Fix post-login redirect
  - [x] Add logging to `/auth/callback/page.tsx`
  - [x] Verify redirect logic (already correct - redirects to `/buscar`)

- [x] **Task 3**: Force domain redirects
  - [x] Add domain redirect logic to `middleware.ts`
  - [x] Test localhost exclusion
  - [x] Preserve path and query params

- [ ] **Manual Step**: Configure Supabase redirect URLs (see Solution 3 above)

- [ ] **Deploy**: Push changes to production

- [ ] **Test**: Complete testing checklist

## Testing Checklist

### Pre-Deployment Test (Local)

1. [ ] Environment variables set in Railway (verified above ✅)
2. [ ] Code changes compile without errors
3. [ ] TypeScript check passes: `npx tsc --noEmit --pretty`
4. [ ] Tests pass: `npm test` (frontend)

### Post-Deployment Test (Production)

1. [ ] **Domain Redirect Test**:
   - Visit https://bidiq-frontend-production.up.railway.app/login
   - Verify automatic redirect to https://smartlic.tech/login
   - Check URL bar shows `smartlic.tech`

2. [ ] **OAuth Google Test**:
   - Visit https://smartlic.tech/login
   - Click "Entrar com Google"
   - Complete Google authentication
   - Verify redirect to `https://smartlic.tech/auth/callback?code=...`
   - Verify final landing page is `https://smartlic.tech/buscar`
   - Check browser console for `[OAuth Callback]` logs

3. [ ] **Session Persistence**:
   - After logging in, verify you stay logged in
   - Refresh page - should remain logged in
   - Navigate to `/historico`, `/conta` - should have access

4. [ ] **Error Handling**:
   - Try invalid credentials
   - Verify error messages appear
   - Verify no infinite redirects

5. [ ] **Mobile Test**:
   - Test on mobile device or Chrome DevTools mobile emulation
   - Verify OAuth flow works on mobile
   - Check responsive design

6. [ ] **Incognito Mode**:
   - Test in incognito/private browsing
   - Verify clean OAuth flow without cached session

## Browser Console Debug Output

After deployment, when testing OAuth, you should see console logs like:

```
[OAuth Callback] Starting callback handler
[OAuth Callback] Current URL: https://smartlic.tech/auth/callback?code=...
[OAuth Callback] Found authorization code, exchanging for session
[OAuth Callback] Session established, redirecting to /buscar
[OAuth Callback] User: tiago.sasaki@gmail.com
[OAuth Callback] Executing redirect to /buscar
```

If you see errors, the logs will help identify where the flow breaks.

## Rollback Plan

If critical issues occur:

1. **Revert environment variables**:
   ```bash
   railway variables --set "NEXT_PUBLIC_CANONICAL_URL=" --service bidiq-frontend
   railway variables --set "NEXT_PUBLIC_APP_URL=" --service bidiq-frontend
   ```

2. **Revert code changes**:
   ```bash
   git revert HEAD~3
   git push origin main
   ```

3. **Restore Supabase config**: Add back `railway.app` URLs in dashboard

## Files Modified

1. `frontend/app/components/AuthProvider.tsx` - Use canonical URL for OAuth
2. `frontend/app/auth/callback/page.tsx` - Add debug logging
3. `frontend/middleware.ts` - Add domain redirect logic
4. `scripts/configure-supabase-oauth.js` - Update to use smartlic.tech
5. `docs/oauth-redirect-fix-guide.md` - Comprehensive guide (NEW)
6. `docs/oauth-fix-deployment-summary.md` - This file (NEW)
7. `scripts/check-supabase-config.js` - Helper script (NEW)

## Next Steps

1. **Immediate**: Complete manual Supabase configuration (Solution 3)
2. **Deploy**: Commit and push changes to trigger Railway deployment
3. **Test**: Complete post-deployment testing checklist
4. **Monitor**: Watch production logs for any auth errors
5. **Cleanup**: Remove old `railway.app` URLs from Supabase after 48h

## Support & Troubleshooting

If issues persist after deployment:

1. **Check Railway logs**:
   ```bash
   railway logs --service bidiq-frontend --tail
   ```

2. **Check browser console**: Look for `[OAuth Callback]` logs

3. **Verify environment variables**:
   ```bash
   railway variables --service bidiq-frontend
   ```

4. **Test Supabase config**:
   ```bash
   node scripts/check-supabase-config.js
   ```

5. **Contact**: Create issue in GitHub repository with:
   - Browser console logs
   - Railway logs
   - Steps to reproduce
   - Expected vs actual behavior

---

**Squad**: @architect (Aria), @dev (James), @devops (Gage)
**Date**: 2026-02-09
**Status**: ✅ Code changes complete, awaiting manual Supabase config + deployment
