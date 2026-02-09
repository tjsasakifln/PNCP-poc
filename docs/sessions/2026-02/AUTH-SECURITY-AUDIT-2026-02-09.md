# Auth Security Audit - 2026-02-09

**Agent**: @auth-security-fixer
**Task**: audit-auth-calls
**Status**: ✅ COMPLETED

---

## 🔴 CRITICAL SECURITY ISSUES FOUND

### Issue #1: Insecure getSession() in Middleware
**File**: `frontend/middleware.ts:124`
**Severity**: HIGH
**Pattern**: Accessing `session.user` from `getSession()`

```typescript
// Line 124 - INSECURE
const { data: { session }, error } = await supabase.auth.getSession();

// Lines 126-139 - Using session.user without validation
if (error || !session) {
  // redirect...
}

const user = session.user; // ❌ INSECURE - user may not be authentic
```

**Why it's insecure**:
- `getSession()` returns data from storage (cookies) WITHOUT server validation
- User object may be tampered with or outdated
- No guarantee the session is still valid on Supabase server

**Impact**:
- Potential session hijacking
- User data may not be authentic
- Security vulnerability in auth middleware

**Fix Required**:
- Replace with `getUser()` which validates against Supabase server
- Handle token refresh properly

---

### Issue #2: Insecure getSession() in AuthProvider
**File**: `frontend/app/components/AuthProvider.tsx:56-63`
**Severity**: HIGH
**Pattern**: Using `session?.user` from `getSession()` and `onAuthStateChange`

```typescript
// Line 56 - INSECURE
supabase.auth.getSession().then(({ data: { session } }) => {
  setSession(session);
  setUser(session?.user ?? null); // ❌ INSECURE
  setLoading(false);
  if (session?.access_token) {
    fetchAdminStatus(session.access_token);
  }
});

// Line 66-77 - INSECURE
supabase.auth.onAuthStateChange((_event, session) => {
  setSession(session);
  setUser(session?.user ?? null); // ❌ INSECURE
  setLoading(false);
  if (session?.access_token) {
    fetchAdminStatus(session.access_token);
  } else {
    setIsAdmin(false);
  }
});
```

**Why it's insecure**:
- Using user object from unvalidated session
- `onAuthStateChange` can emit unvalidated session from storage
- App-wide auth context built on potentially stale data

**Impact**:
- Entire app trusts potentially invalid user data
- Admin status check uses unvalidated token
- Security vulnerability across all protected pages

**Fix Required**:
- Use `getUser()` instead of `getSession()` for initial load
- Validate user on auth state changes

---

### Issue #3: Potentially Insecure getSession() in Callback
**File**: `frontend/app/auth/callback/page.tsx:55`
**Severity**: MEDIUM
**Pattern**: Fallback getSession() usage

```typescript
// Line 55 - POTENTIALLY INSECURE
const { data: { session }, error: sessionError } = await supabase.auth.getSession();

if (sessionError) {
  // handle error
}

if (session) {
  setStatus("success");
  window.location.href = "/buscar";
}
```

**Context**:
- Used as fallback after code exchange
- Immediately redirects on success
- Does NOT access `session.user` directly

**Why it's medium severity**:
- Doesn't directly use user object
- Only checks if session exists
- Could still accept invalid session

**Impact**:
- Less critical than other issues
- Could allow login with stale session
- Should still be fixed for consistency

**Fix Required**:
- Use `getUser()` as fallback instead
- Ensure consistent validation across callback

---

## 📊 SUMMARY

### Total Issues: 3
- **HIGH Severity**: 2 (middleware, AuthProvider)
- **MEDIUM Severity**: 1 (callback)

### Affected Files: 3
1. `frontend/middleware.ts` - Route protection
2. `frontend/app/components/AuthProvider.tsx` - Global auth context
3. `frontend/app/auth/callback/page.tsx` - OAuth callback handler

### Security Risk: CRITICAL
- User authentication relies on unvalidated sessions
- Potential for session hijacking
- Data tampering possible

---

## ✅ RECOMMENDED FIXES

### Fix #1: Middleware (HIGH PRIORITY)

**Replace**:
```typescript
const { data: { session }, error } = await supabase.auth.getSession();
if (error || !session) {
  // redirect to login
}
const user = session.user;
```

**With**:
```typescript
const { data: { user }, error } = await supabase.auth.getUser();
if (error || !user) {
  // redirect to login
}
// user is now validated by Supabase server
```

---

### Fix #2: AuthProvider (HIGH PRIORITY)

**Replace**:
```typescript
// Initial session check
supabase.auth.getSession().then(({ data: { session } }) => {
  setUser(session?.user ?? null);
});

// Auth state listener
supabase.auth.onAuthStateChange((_event, session) => {
  setUser(session?.user ?? null);
});
```

**With**:
```typescript
// Initial user check (validated)
supabase.auth.getUser().then(({ data: { user } }) => {
  setUser(user);
});

// Auth state listener - validate on change
supabase.auth.onAuthStateChange(async (_event, session) => {
  if (session) {
    // Revalidate user on auth events
    const { data: { user } } = await supabase.auth.getUser();
    setUser(user);
  } else {
    setUser(null);
  }
});
```

---

### Fix #3: Callback (MEDIUM PRIORITY)

**Replace**:
```typescript
const { data: { session }, error: sessionError } = await supabase.auth.getSession();
if (session) {
  // redirect
}
```

**With**:
```typescript
const { data: { user }, error: userError } = await supabase.auth.getUser();
if (user) {
  // redirect
}
```

---

## 🧪 VALIDATION PLAN

After fixes are applied:

1. **Run Auth Tests**:
   ```bash
   npm test -- auth
   ```

2. **Check Production Logs**:
   - Verify no more Supabase warnings
   - Monitor for 5 minutes post-deployment

3. **Manual Testing**:
   - Login with email/password
   - Login with Google OAuth
   - Refresh page when logged in
   - Session expiration handling
   - Protected route access

4. **Verify Middleware**:
   - Access protected route while logged out
   - Access protected route while logged in
   - Check X-User-ID header is set

5. **Verify AuthProvider**:
   - User state updates on login
   - Admin status fetched correctly
   - User state clears on logout

---

## 📋 NEXT STEPS

1. ✅ Apply Fix #1 (middleware.ts)
2. ✅ Apply Fix #2 (AuthProvider.tsx)
3. ✅ Apply Fix #3 (callback/page.tsx)
4. ✅ Run all tests
5. ✅ Deploy to staging
6. ✅ Verify production logs

---

**Audited by**: @auth-security-fixer
**Date**: 2026-02-09
**Confidence**: 95%
