# ✅ OAuth Verification Checklist - Google Login Fix

**Date:** 2026-02-11
**Issue:** Google OAuth fails, Email/Password works
**Railway Env Vars:** ✅ All configured correctly

---

## Railway Environment Variables ✅

```
✅ NEXT_PUBLIC_CANONICAL_URL          = https://smartlic.tech
✅ NEXT_PUBLIC_SUPABASE_URL           = https://fqqyovlzdzimiwfofdjk.supabase.co
✅ NEXT_PUBLIC_SUPABASE_ANON_KEY      = Configured
✅ NEXT_PUBLIC_BACKEND_URL            = https://api.smartlic.tech
```

**OAuth Redirect URL:** `https://smartlic.tech/auth/callback`

---

## 🔍 Next Steps - Verify External Services

### 1️⃣ Google Cloud Console

**URL:** https://console.cloud.google.com/apis/credentials

**Steps:**
1. Select your OAuth 2.0 Client ID
2. Check **"Authorized redirect URIs"**
3. **MUST include EXACTLY:**
   ```
   https://smartlic.tech/auth/callback
   ```
4. Also check if it includes:
   ```
   https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback
   ```

**Common Issues:**
- ❌ Missing `https://smartlic.tech/auth/callback`
- ❌ Has `https://app.smartlic.tech/auth/callback` instead (wrong subdomain)
- ❌ Has old Railway URL (e.g., `bidiq-frontend.up.railway.app`)
- ❌ Missing trailing `/callback`

---

### 2️⃣ Supabase Dashboard

**URL:** https://supabase.com/dashboard/project/fqqyovlzdzimiwfofdjk

**Steps:**
1. Go to **Authentication → URL Configuration**
2. Check **"Site URL"**:
   ```
   https://smartlic.tech
   ```
3. Check **"Redirect URLs"** (allowed list):
   ```
   https://smartlic.tech/auth/callback
   https://smartlic.tech/**
   ```

**Steps for Google Provider:**
1. Go to **Authentication → Providers → Google**
2. Verify **"Authorized Client IDs"** is set
3. Check **"Skip nonce check"** setting (try enabling if failing)

**Common Issues:**
- ❌ Site URL is wrong (e.g., `https://app.smartlic.tech`)
- ❌ Redirect URLs don't include `https://smartlic.tech/auth/callback`
- ❌ Google provider not enabled
- ❌ Missing Google OAuth credentials

---

## 🧪 Test OAuth Flow with Logs

**Browser Console Logs to Collect:**

After deploying the logging changes (commit 2c8fd8d), try Google OAuth and collect:

1. **Before OAuth redirect:**
   ```
   [AuthProvider] Google OAuth Login Starting
   [AuthProvider] NEXT_PUBLIC_CANONICAL_URL: https://smartlic.tech
   [AuthProvider] window.location.origin: https://smartlic.tech
   [AuthProvider] Final redirect URL: https://smartlic.tech/auth/callback
   [AuthProvider] OAuth redirect initiated
   ```

2. **On OAuth callback page:**
   ```
   [OAuth Callback] ===== STARTING OAUTH CALLBACK =====
   [OAuth Callback] Full URL: https://smartlic.tech/auth/callback?code=...
   [OAuth Callback] Query params: { code: "...", ... }
   [OAuth Callback] Authorization code found, length: 180
   [OAuth Callback] Exchanging code for session...
   [OAuth Callback] Code exchange took: 1234 ms
   ```

3. **Look for errors:**
   ```
   [OAuth Callback] OAuth error parameter found: ...
   [OAuth Callback] Code exchange FAILED: ...
   [OAuth Callback] Error details: ...
   [OAuth Callback] TIMEOUT after 15 seconds
   ```

---

## 🎯 Most Likely Fix

Based on the evidence:
- ✅ Railway env vars are correct
- ✅ Email/password login works (Supabase connection OK)
- ❌ Google OAuth fails

**Most likely cause:** Google Cloud Console is missing `https://smartlic.tech/auth/callback` in Authorized redirect URIs.

**Fix:**
1. Go to Google Cloud Console
2. Add `https://smartlic.tech/auth/callback` to Authorized redirect URIs
3. Save
4. Wait 5 minutes for changes to propagate
5. Test Google OAuth again

---

## 📝 Alternative: Use Supabase-Hosted OAuth (Recommended)

Instead of direct OAuth, use Supabase's built-in OAuth redirect:

**In Google Cloud Console, set redirect URI to:**
```
https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback
```

**Then in code (already configured in Supabase), it will redirect to:**
```
https://smartlic.tech/auth/callback
```

This is more reliable as Supabase handles the OAuth flow.

---

## ✅ Verification After Fix

After making changes:

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Open incognito window**
3. Go to `https://smartlic.tech/login`
4. Click "Entrar com Google"
5. **Check browser console** for logs
6. **Should succeed** within 3-5 seconds

---

## 🚨 If Still Failing

If OAuth still fails after verifying Google Cloud Console and Supabase:

1. **Share the browser console logs** (see "Test OAuth Flow with Logs" section)
2. **Check Network tab** for failed requests
3. **Verify Google OAuth credentials** are correct in Supabase
4. **Try revoking** Supabase access in Google Account settings and re-auth

---

**Last Updated:** 2026-02-11
**Status:** Ready for external verification
