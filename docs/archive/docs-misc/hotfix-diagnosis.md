# Hotfix Diagnosis: OAuth Google Callback Failure

**Date:** 2026-02-08
**Reported by:** User
**Severity:** CRITICAL (blocks login)

---

## Problem Statement

**Symptom:** User clicks "Login with Google", authenticates successfully with Google, but gets redirected to homepage with `?code=...` parameter instead of being authenticated and redirected to `/buscar`.

**URL observed:**
```
https://bidiq-frontend-production.up.railway.app/?code=0c41d9e0-6801-4bc3-8675-d26713161840
```

**Expected behavior:**
1. User clicks "Login with Google"
2. Google OAuth popup/redirect
3. User authenticates with Google
4. Redirect to `/auth/callback` with authorization code
5. Callback page exchanges code for session
6. Redirect to `/buscar` (logged area)

**Actual behavior:**
1-3. Same ✅
4. Redirect to `/?code=...` (WRONG - should be `/auth/callback`) ❌
5. No callback processing ❌
6. User remains on homepage, not authenticated ❌

---

## Root Cause Analysis

### Investigation Results

#### 1. **OAuth Flow Configuration Mismatch**

**File:** `frontend/lib/supabase.ts` (lines 13-16)
```typescript
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    flowType: "implicit",  // ⚠️ IMPLICIT FLOW
  },
});
```

**File:** `frontend/app/components/AuthProvider.tsx` (lines 122-128)
```typescript
const signInWithGoogle = useCallback(async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${window.location.origin}/auth/callback` },  // ⚠️ PKCE flow callback
  });
  if (error) throw error;
}, []);
```

**CONFLICT IDENTIFIED:**
- Supabase client configured with `flowType: "implicit"` (tokens in URL hash `#access_token=...`)
- OAuth redirect configured for `/auth/callback` (expects PKCE flow with `?code=...`)
- Google returning `?code=...` (authorization code) instead of `#access_token=...` (implicit tokens)

#### 2. **Supabase Dashboard Configuration Issue**

The Supabase project's **Redirect URLs** configuration likely includes:
- ❌ `https://bidiq-frontend-production.up.railway.app/` (homepage - WRONG)
- ✅ `https://bidiq-frontend-production.up.railway.app/auth/callback` (correct)

**Why `?code=` goes to homepage:**
When Supabase cannot match the `redirectTo` parameter with allowed URLs, it falls back to the FIRST configured redirect URL (homepage).

#### 3. **Callback Handler Incompatibility**

**File:** `frontend/app/auth/callback/page.tsx` (lines 32-41)
```typescript
// For implicit flow, Supabase automatically handles the hash fragment
// and sets the session. We just need to check if we have a session.
const { data: { session }, error: sessionError } = await supabase.auth.getSession();
```

**PROBLEM:**
- Comment says "implicit flow" with hash fragments
- But Google OAuth is sending `?code=...` (authorization code from PKCE flow)
- Callback expects implicit flow (`#access_token=...`)
- No code exchange logic for PKCE flow

---

## Technical Deep Dive

### OAuth Flow Types Comparison

| Flow Type | Redirect Format | Processing | Use Case |
|-----------|----------------|------------|----------|
| **Implicit** | `#access_token=xyz&refresh_token=abc` | Client-side only, no server exchange | SPA, no backend |
| **PKCE** | `?code=xyz` | Client exchanges code for tokens via Supabase API | Secure, recommended |

### Current Misconfiguration

```
User clicks "Login with Google"
  ↓
signInWithGoogle() → supabase.auth.signInWithOAuth({
  provider: "google",
  options: { redirectTo: "/auth/callback" }  // Expects PKCE
})
  ↓
Supabase initiates OAuth with Google (PKCE flow because provider="google")
  ↓
Google authenticates user, generates authorization code
  ↓
Google redirects: "https://.../?code=0c41d9e0-..." ❌
  (Should be: "https://.../auth/callback?code=...")
  ↓
Homepage loads with ?code parameter (ignored)
  ↓
User not authenticated ❌
```

### Why Redirect Goes to Homepage

**Hypothesis:** Supabase's redirect URL whitelist check fails.

Possible causes:
1. `/auth/callback` not whitelisted in Supabase dashboard
2. Protocol mismatch (http vs https)
3. Trailing slash mismatch (`/auth/callback` vs `/auth/callback/`)
4. Wildcard pattern not configured

When redirect fails validation, Supabase uses the FIRST URL in the whitelist (likely the homepage `/`).

---

## Files Affected

1. `frontend/lib/supabase.ts` - Client configuration (flowType)
2. `frontend/app/components/AuthProvider.tsx` - signInWithGoogle implementation
3. `frontend/app/auth/callback/page.tsx` - Callback handler
4. **Supabase Dashboard** - Authentication → Redirect URLs config (external)

---

## Blast Radius

- **Users affected:** ALL users trying to login with Google OAuth
- **Impact:** Cannot authenticate via Google (critical login path blocked)
- **Workarounds available:** Email+password login, magic link login
- **Data loss risk:** None (no data corruption)
- **Backward compatibility:** Fix will not break existing users

---

## Proposed Solutions

### Option 1: Fix Redirect URL Configuration (RECOMMENDED - LOWEST RISK)

**Action:** Add correct redirect URL to Supabase dashboard whitelist

**Steps:**
1. Login to Supabase Dashboard: https://app.supabase.com/project/fqqyovlzdzimiwfofdjk
2. Go to Authentication → URL Configuration → Redirect URLs
3. Add EXACT URLs:
   - `https://bidiq-frontend-production.up.railway.app/auth/callback`
   - `http://localhost:3000/auth/callback` (for local development)
4. Remove homepage URL (`/`) if present
5. Save changes
6. Test OAuth flow

**Pros:**
- No code changes needed
- Instant fix (no deployment)
- Zero risk to existing functionality

**Cons:**
- Requires Supabase dashboard access
- Manual configuration step

---

### Option 2: Use PKCE Flow Explicitly (RECOMMENDED - BEST PRACTICE)

**Action:** Change flowType from `implicit` to `pkce` and ensure callback handles code exchange

**Code Changes:**

**File:** `frontend/lib/supabase.ts`
```typescript
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    flowType: "pkce",  // ✅ Change from "implicit" to "pkce"
  },
});
```

**File:** `frontend/app/auth/callback/page.tsx` - Add explicit code exchange:
```typescript
// Check for authorization code (PKCE flow)
const params = new URLSearchParams(window.location.search);
const code = params.get("code");

if (code) {
  // Exchange code for session (Supabase SDK handles this automatically with PKCE)
  const { data: { session }, error } = await supabase.auth.exchangeCodeForSession(code);

  if (error) {
    console.error("Code exchange error:", error);
    setStatus("error");
    setErrorMessage(error.message);
    return;
  }

  if (session) {
    setStatus("success");
    router.push("/buscar");
    return;
  }
}
```

**Pros:**
- Fixes root cause (flow type mismatch)
- More secure than implicit flow
- Aligns with modern OAuth best practices
- Self-contained fix (no external config)

**Cons:**
- Requires code deployment
- Needs testing across all OAuth providers
- May affect magic link flow (needs verification)

---

### Option 3: Use Implicit Flow Correctly (NOT RECOMMENDED)

**Action:** Keep `flowType: "implicit"` but change redirectTo to use hash fragments

**Why NOT recommended:**
- Implicit flow is deprecated for security reasons
- Less secure than PKCE
- Not suitable for production environments
- Google OAuth may not support implicit flow properly

---

## Recommended Fix: OPTION 1 + OPTION 2 (Hybrid Approach)

1. **Immediate fix (OPTION 1):** Configure Supabase redirect URLs to unblock users NOW
2. **Proper fix (OPTION 2):** Deploy PKCE flow change for long-term security

**Implementation Plan:**
1. @devops configures Supabase dashboard redirect URLs (5 min)
2. Verify OAuth works (test with real Google account)
3. @dev implements PKCE flow change (15 min)
4. @qa creates regression test
5. @devops deploys to production

---

## Testing Checklist

- [ ] Google OAuth login from desktop browser
- [ ] Google OAuth login from mobile browser
- [ ] Callback redirect to `/buscar` after login
- [ ] Session persists after page reload
- [ ] Magic link still works (verify no regression)
- [ ] Email+password login still works
- [ ] Logout and re-login with Google
- [ ] Test with multiple Google accounts
- [ ] Verify redirect URL in browser DevTools Network tab

---

## Monitoring & Rollback Plan

**Monitoring:**
- Check Supabase Auth logs for failed OAuth attempts
- Monitor frontend error logs for callback errors
- Track login success rate (Google OAuth vs total logins)

**Rollback Plan:**
If OPTION 2 breaks anything:
1. Revert `frontend/lib/supabase.ts` to `flowType: "implicit"`
2. Revert callback handler changes
3. Keep OPTION 1 redirect URL config (safe to keep)
4. Re-deploy previous version

---

## Next Steps

**Immediate Actions (Squad Handoff):**
1. @devops: Configure Supabase redirect URLs (OPTION 1)
2. @dev: Implement PKCE flow (OPTION 2) after OPTION 1 is verified
3. @qa: Create regression test for OAuth flow
4. @qa: Run full test suite
5. @devops: Deploy and monitor production

**ETA:** 1-2 hours for complete fix and deployment

---

**Diagnosis completed by:** @dev (James)
**Status:** Ready for fix implementation (FASE 2)
