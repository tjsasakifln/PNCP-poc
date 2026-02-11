# 🔍 OAuth Google Debug Guide

**Issue:** Users stuck on callback after Google OAuth login
**Status:** Added detailed logging for troubleshooting
**Date:** 2026-02-11

---

## 🎯 Problem Summary

**Working:**
- ✅ Login with email/password
- ✅ Timeout prevents infinite loading (returns to login after 15s)

**Not Working:**
- ❌ Login with Google OAuth (gets stuck on callback)

---

## 🔧 Changes Made

### 1. Added Detailed Logging to OAuth Callback
**File:** `frontend/app/auth/callback/page.tsx`

**What it logs:**
- Full callback URL
- Query parameters received
- Authorization code presence/length
- Code exchange duration
- Session creation success/failure
- Any errors with full details

### 2. Added Logging to Google OAuth Initiation
**File:** `frontend/app/components/AuthProvider.tsx`

**What it logs:**
- NEXT_PUBLIC_CANONICAL_URL value
- window.location.origin value
- Final redirect URL being used
- OAuth initiation success/failure

### 3. Increased Callback Timeout
- Changed from 5 seconds to 15 seconds
- Better error message directing to email/password login

---

## 🧪 How to Debug

### Step 1: Test Google OAuth Login

1. Open browser in **incognito mode**
2. Go to production URL: https://your-app.railway.app/login
3. Open **browser console** (F12)
4. Click "Entrar com Google"
5. Authorize in Google
6. Watch console logs during callback

### Step 2: Collect Debug Information

**Look for these logs in browser console:**

```javascript
// When clicking Google login:
[AuthProvider] Google OAuth Login Starting
[AuthProvider] NEXT_PUBLIC_CANONICAL_URL: <value or undefined>
[AuthProvider] window.location.origin: <railway url>
[AuthProvider] Final redirect URL: <callback url>

// When returning from Google:
[OAuth Callback] ===== STARTING OAUTH CALLBACK =====
[OAuth Callback] Full URL: <full url with code>
[OAuth Callback] Query params: { code: "...", ... }
[OAuth Callback] Authorization code found, length: <number>
[OAuth Callback] Exchanging code for session...
[OAuth Callback] Code exchange took: <ms> ms

// Success:
[OAuth Callback] ✅ Session obtained successfully!
[OAuth Callback] User: <email>
[OAuth Callback] Redirecting to /buscar

// OR Failure:
[OAuth Callback] Code exchange FAILED: <error>
[OAuth Callback] Error details: <json>
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Redirect URL Mismatch

**Symptom:** Code exchange fails with "redirect URI mismatch"

**Cause:** Google OAuth configured with different callback URL

**Solution:**
1. Go to Google Cloud Console
2. Navigate to: APIs & Services → Credentials
3. Find your OAuth 2.0 Client ID
4. Check "Authorized redirect URIs"
5. Should include:
   - `https://your-app.railway.app/auth/callback`
   - `https://your-custom-domain.com/auth/callback` (if using custom domain)
   - Your Supabase callback: `https://<project>.supabase.co/auth/v1/callback`

---

### Issue 2: NEXT_PUBLIC_CANONICAL_URL Not Set

**Symptom:** Logs show `NEXT_PUBLIC_CANONICAL_URL: undefined`

**Cause:** Environment variable not configured in Railway

**Solution:**
1. Go to Railway dashboard
2. Select your frontend service
3. Go to Variables tab
4. Add: `NEXT_PUBLIC_CANONICAL_URL` = `https://your-app.railway.app`
5. Or use your custom domain if you have one
6. Redeploy

---

### Issue 3: Supabase Configuration Mismatch

**Symptom:** Code exchange succeeds but no session created

**Cause:** Supabase redirect URL not matching

**Solution:**
1. Go to Supabase Dashboard
2. Project Settings → Authentication → URL Configuration
3. Site URL should match your production URL
4. Redirect URLs should include:
   - `https://your-app.railway.app/auth/callback`
   - `https://your-custom-domain.com/auth/callback`

---

### Issue 4: Code Exchange Timeout

**Symptom:** Logs show "TIMEOUT after 15 seconds"

**Cause:** Supabase API slow or network issues

**Possible solutions:**
- Check Supabase project status
- Check Railway network connectivity
- Verify NEXT_PUBLIC_SUPABASE_URL is correct
- Verify NEXT_PUBLIC_SUPABASE_ANON_KEY is correct

---

## 📋 Checklist: OAuth Configuration

### Google Cloud Console
- [ ] OAuth 2.0 Client ID created
- [ ] Authorized redirect URIs includes Railway URL + `/auth/callback`
- [ ] Authorized redirect URIs includes Supabase callback URL
- [ ] Client ID and Secret match what's in Supabase

### Supabase Dashboard
- [ ] Google OAuth provider enabled
- [ ] Client ID configured
- [ ] Client Secret configured
- [ ] Site URL = production URL
- [ ] Redirect URLs include production callback URL

### Railway Environment Variables
- [ ] `NEXT_PUBLIC_SUPABASE_URL` set correctly
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` set correctly
- [ ] `NEXT_PUBLIC_CANONICAL_URL` set to production URL (optional but recommended)
- [ ] `BACKEND_URL` set correctly

---

## 🔬 Advanced Debugging

### Enable Supabase Debug Logging

Add this to your Supabase client initialization:

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  {
    auth: {
      debug: true, // Enable auth debug logs
      flowType: 'pkce',
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true
    }
  }
)
```

### Test OAuth Flow Manually

1. Get the OAuth URL from console when clicking "Entrar com Google"
2. Copy the full URL
3. Paste in new incognito tab
4. Complete Google authorization
5. Check where you're redirected
6. Verify callback URL matches expected

---

## 📞 Next Steps

### After Deploying These Changes:

1. **Test and collect logs:**
   - Test Google OAuth in incognito
   - Copy ALL console logs
   - Share logs for analysis

2. **Verify configuration:**
   - Check Google Cloud Console redirect URIs
   - Check Supabase redirect URLs
   - Check Railway environment variables

3. **If still failing:**
   - Share the collected logs
   - We'll identify exact failure point
   - Apply targeted fix

---

## 🎯 Expected Outcome

After proper configuration:
- ✅ Google OAuth login completes in < 5 seconds
- ✅ Console shows successful session creation
- ✅ User redirected to /buscar
- ✅ No errors in logs

---

## 📝 Related Files

- `frontend/app/auth/callback/page.tsx` - OAuth callback handler
- `frontend/app/components/AuthProvider.tsx` - OAuth initiation
- `frontend/lib/supabase.ts` - Supabase client configuration

---

**Last Updated:** 2026-02-11
**Status:** Debugging in progress - awaiting log analysis
