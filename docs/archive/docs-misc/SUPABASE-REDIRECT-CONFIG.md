# Supabase Redirect URL Configuration - CRITICAL

**Action Required:** Configure OAuth redirect URLs in Supabase Dashboard

**Severity:** CRITICAL - Required for OAuth Google login to work

---

## 🚨 Problem

OAuth Google login redirects to homepage with `?code=...` instead of `/auth/callback` because the callback URL is not whitelisted in Supabase.

## ✅ Solution

Add the following URLs to Supabase's allowed redirect URLs:

### Steps

1. **Login to Supabase Dashboard:**
   - URL: https://app.supabase.com/project/fqqyovlzdzimiwfofdjk
   - Project: SmartLic (fqqyovlzdzimiwfofdjk)

2. **Navigate to Authentication Settings:**
   - Go to: **Authentication** → **URL Configuration**
   - Section: **Redirect URLs**

3. **Add These Exact URLs:**

   **Production:**
   ```
   https://bidiq-frontend-production.up.railway.app/auth/callback
   ```

   **Development:**
   ```
   http://localhost:3000/auth/callback
   ```

4. **Optional - Remove Homepage Fallback (if present):**
   If you see these URLs, REMOVE them (they cause the bug):
   ```
   https://bidiq-frontend-production.up.railway.app/
   http://localhost:3000/
   ```

5. **Save Changes**

6. **Verify Configuration:**
   After saving, the "Redirect URLs" section should show ONLY:
   - `https://bidiq-frontend-production.up.railway.app/auth/callback`
   - `http://localhost:3000/auth/callback`

---

## 🧪 Testing After Configuration

### Manual Test (Recommended)

1. Open production URL in incognito: https://bidiq-frontend-production.up.railway.app/login
2. Click "Entrar com Google"
3. Authenticate with Google account
4. **Expected Result:**
   - URL should be: `https://.../auth/callback?code=...` (NOT homepage)
   - Should see "Processando autenticação..." spinner
   - Should redirect to `/buscar` (logged area)
   - User should be authenticated ✅

5. **If Still Fails:**
   - Check browser DevTools → Network tab
   - Find the redirect from Google
   - Verify it goes to `/auth/callback` and not `/`
   - Check console for errors

### Automated Test

```bash
cd frontend
npm test -- oauth-google-callback.test.tsx
```

Expected output:
```
PASS  __tests__/auth/oauth-google-callback.test.tsx
  ✓ should exchange authorization code for session (Google OAuth)
  ✓ should handle code exchange error gracefully
  ✓ should redirect to /buscar after successful Google login
```

---

## 📊 Impact

**Before Fix:**
- OAuth Google: ❌ Broken (redirects to homepage)
- Magic Link: ✅ Working
- Email+Password: ✅ Working

**After Fix:**
- OAuth Google: ✅ Fixed
- Magic Link: ✅ Still working
- Email+Password: ✅ Still working

---

## ⏱️ Urgency

**Priority:** P0 - CRITICAL
**Impact:** Blocks ALL Google OAuth logins
**Workaround:** Users must use email+password or magic link
**Time to Fix:** 5 minutes (configuration only)

---

## 🔐 Security Notes

- PKCE flow is more secure than implicit flow
- Authorization codes are single-use and short-lived
- Code exchange happens server-side via Supabase SDK
- No tokens exposed in browser history

---

## 🎯 Who Can Do This

**Required Access:**
- Supabase project admin/owner
- Access to project: fqqyovlzdzimiwfofdjk

**Contacts:**
- Project owner: tiago.sasaki@gmail.com
- DevOps: @devops (Gage)

---

## ✅ Verification Checklist

- [ ] Logged into Supabase Dashboard
- [ ] Navigated to Authentication → URL Configuration
- [ ] Added production callback URL (`/auth/callback`)
- [ ] Added development callback URL (`localhost:3000/auth/callback`)
- [ ] Removed homepage URLs (if present)
- [ ] Saved configuration
- [ ] Tested OAuth Google login in production
- [ ] Verified redirect goes to `/auth/callback`
- [ ] Verified user is authenticated and redirected to `/buscar`
- [ ] Tested on mobile browser (optional but recommended)
- [ ] Confirmed magic link still works (regression check)

---

**Last Updated:** 2026-02-08
**Related:** docs/hotfix-diagnosis.md
**PR:** (pending)
