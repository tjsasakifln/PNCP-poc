# Hotfix Test Scenarios - 2026-02-09

**Agent**: @auth-security-fixer, @error-message-improver
**Task**: test-error-scenarios
**Status**: ✅ READY FOR MANUAL TESTING

---

## 🧪 TEST PLAN OVERVIEW

All code changes have been applied and validated for syntax correctness.
Manual testing is required to verify the fixes work in production.

---

## 📋 TEST SCENARIOS

### Scenario 1: Auth Security - Login Flow ✅

**Test**: Verify secure getUser() pattern works

**Steps**:
1. Open browser, go to `/login`
2. Enter credentials and login
3. Verify redirect to `/buscar`
4. Check browser DevTools → Network → look for auth requests
5. Open new tab, go directly to `/buscar`
6. Verify user stays logged in

**Expected**:
- ✅ Login successful
- ✅ Redirect works
- ✅ Auth persists across tabs
- ✅ No Supabase warnings in logs

**Current Status**: ⏳ READY TO TEST

---

### Scenario 2: Auth Security - Protected Routes

**Test**: Verify middleware uses secure validation

**Steps**:
1. Logout (clear cookies)
2. Try to access `/buscar` directly
3. Verify redirect to `/login?redirect=/buscar`
4. Login successfully
5. Verify redirect back to `/buscar`

**Expected**:
- ✅ Protected route blocked when logged out
- ✅ Redirect preserves target URL
- ✅ Login completes successfully
- ✅ Redirect back to original page

**Current Status**: ⏳ READY TO TEST

---

### Scenario 3: Auth Security - OAuth Flow

**Test**: Verify Google OAuth callback uses secure validation

**Steps**:
1. Logout
2. Click "Login with Google"
3. Complete Google authentication
4. Wait for callback redirect
5. Verify successful login

**Expected**:
- ✅ OAuth redirect works
- ✅ Callback processes successfully
- ✅ User logged in with validated data
- ✅ No errors in console

**Current Status**: ⏳ READY TO TEST

---

### Scenario 4: Auth Security - Session Refresh

**Test**: Verify auth state updates correctly

**Steps**:
1. Login successfully
2. Open DevTools → Application → Cookies
3. Note auth cookie values
4. Wait 5 minutes (or manually modify token expiry)
5. Refresh page
6. Verify auth state updates

**Expected**:
- ✅ Auth state persists
- ✅ Session refreshes automatically
- ✅ User stays logged in
- ✅ Admin status fetched correctly

**Current Status**: ⏳ READY TO TEST

---

### Scenario 5: Error Message - Date Range Exceeded ⭐ CRITICAL

**Test**: Verify date range error shows specific message

**Precondition**: User on plan with 7-day limit

**Steps**:
1. Login with account that has 7-day limit
2. Go to `/buscar`
3. Select date range of 8 days (e.g., 2026-02-01 to 2026-02-08)
4. Select any state
5. Click "Buscar"
6. Observe error message

**Expected** (NEW):
```
O período de busca não pode exceder 7 dias (seu plano: [PlanName]).
Você tentou buscar 8 dias.
Reduza o período e tente novamente.
```

**Before Fix** (OLD):
```
Algo deu errado. Tente novamente em instantes.
```

**Validation**:
- ✅ User sees EXACT problem (date range)
- ✅ User sees EXACT limit (7 dias)
- ✅ User sees EXACT attempt (8 dias)
- ✅ User knows HOW TO FIX (reduza o período)
- ❌ No more generic "Algo deu errado"

**Current Status**: ⏳ READY TO TEST (HIGHEST PRIORITY)

---

### Scenario 6: Error Message - Rate Limit

**Test**: Verify rate limit shows countdown

**Steps**:
1. Login
2. Make 3 searches rapidly (within 1 minute)
3. Try 4th search
4. Observe error message

**Expected**:
```
Limite de requisições excedido (2/min).
Aguarde 60 segundos e tente novamente.
```

**Before Fix**:
```
Algo deu errado. Tente novamente em instantes.
```

**Validation**:
- ✅ User knows it's rate limit
- ✅ User sees countdown
- ✅ No confusion with other errors

**Current Status**: ⏳ READY TO TEST

---

### Scenario 7: Error Message - Quota Exceeded

**Test**: Verify quota exceeded still works (should not change)

**Steps**:
1. Use account that exhausted monthly quota
2. Try to search
3. Observe error message

**Expected** (UNCHANGED):
```
Suas buscas acabaram. Faça upgrade para continuar.
```

**Validation**:
- ✅ Works as before
- ✅ Specific quota error shown
- ✅ No regression

**Current Status**: ⏳ READY TO TEST

---

### Scenario 8: Error Message - Network Error

**Test**: Verify network errors still work (should not change)

**Steps**:
1. Disconnect internet
2. Try to search
3. Observe error message

**Expected** (UNCHANGED):
```
Erro de conexão. Verifique sua internet.
```

**Validation**:
- ✅ Works as before
- ✅ Clear message
- ✅ No regression

**Current Status**: ⏳ READY TO TEST

---

### Scenario 9: Error Message - PNCP Timeout

**Test**: Verify PNCP timeout errors work (should not change)

**Steps**:
1. Select many states (e.g., all 27 UFs)
2. Select long date range
3. Try to search
4. If timeout occurs, observe message

**Expected** (UNCHANGED):
```
A busca demorou demais. Tente com menos estados ou um período menor.
```

**Validation**:
- ✅ Works as before
- ✅ Helpful suggestion
- ✅ No regression

**Current Status**: ⏳ READY TO TEST

---

### Scenario 10: Production Logs - Auth Warnings

**Test**: Verify Supabase warnings eliminated

**Steps**:
1. Deploy fixes to production
2. Monitor production logs for 10 minutes
3. Check for Supabase auth warnings

**Expected**:
- ✅ ZERO warnings about insecure getSession()
- ✅ Auth flow works smoothly
- ✅ No errors in logs

**Command** (Railway):
```bash
railway logs --environment production | grep -i "insecure"
railway logs --environment production | grep -i "getSession"
railway logs --environment production | grep -i "supabase"
```

**Current Status**: ⏳ READY FOR PRODUCTION TEST

---

### Scenario 11: Production Logs - Date Range Errors

**Test**: Verify date range errors show correctly

**Steps**:
1. Deploy fixes to production
2. Trigger date range error (8 days on 7-day plan)
3. Check backend logs
4. Check frontend behavior

**Expected**:

**Backend Logs**:
```
WARNING: Date range validation failed for user *: requested=8 days, max_allowed=7 days
```

**Frontend Shows**:
```
O período de busca não pode exceder 7 dias (seu plano: [PlanName]).
Você tentou buscar 8 dias.
Reduza o período e tente novamente.
```

**Validation**:
- ✅ Backend logs correct
- ✅ Frontend shows specific message
- ✅ No more confusion

**Current Status**: ⏳ READY FOR PRODUCTION TEST

---

## 📊 TEST SUMMARY

### Total Scenarios: 11
- **Auth Security**: 4 scenarios
- **Error Messages**: 7 scenarios

### Priority Breakdown:
- ⭐ **CRITICAL**: Scenario 5 (Date Range Error)
- 🔴 **HIGH**: Scenarios 1-4 (Auth Security)
- 🟡 **MEDIUM**: Scenarios 6-9 (Error Messages)
- 🟢 **LOW**: Scenarios 10-11 (Production Logs)

---

## ✅ CODE CHANGES SUMMARY

### Files Modified: 7

**Frontend (5 files)**:
1. `frontend/middleware.ts` - Secure getUser() validation
2. `frontend/app/components/AuthProvider.tsx` - Secure auth state management
3. `frontend/app/auth/callback/page.tsx` - Secure OAuth callback
4. `frontend/app/buscar/page.tsx` - Structured error code handling
5. `frontend/lib/error-messages.ts` - Improved error translation

**Backend (1 file)**:
6. `backend/main.py` - Structured error codes + DATE_RANGE_EXCEEDED

**Documentation (1 file)**:
7. `docs/stories/STORY-176-prod-hotfix-auth-errors.md` - Story tracking

---

## 🚀 DEPLOYMENT CHECKLIST

### Pre-Deployment:
- ✅ All code changes applied
- ✅ Syntax validated
- ✅ No merge conflicts
- ⏳ Manual testing completed
- ⏳ Staging deployment verified

### Deployment:
- ⏳ Deploy to staging
- ⏳ Run scenarios 1-9 on staging
- ⏳ Deploy to production
- ⏳ Run scenarios 10-11 on production
- ⏳ Monitor logs for 1 hour

### Post-Deployment:
- ⏳ Verify zero Supabase warnings
- ⏳ Verify date range errors clear
- ⏳ User feedback positive
- ⏳ No support tickets

---

## 🎯 SUCCESS CRITERIA

### Auth Security:
- ✅ Zero Supabase warnings in logs
- ✅ All auth flows work correctly
- ✅ OAuth still functional
- ✅ Session refresh works

### Error Messages:
- ✅ Date range error shows specific message
- ✅ Rate limit error shows countdown
- ✅ No more "Algo deu errado" for known errors
- ✅ User knows how to fix issues

---

## 📋 ROLLBACK PLAN

If critical issues occur:

**Rollback Command**:
```bash
git log --oneline -5  # Find commit hash
git revert <commit-hash>
git push origin main
railway deploy  # Or your deployment method
```

**Rollback Scenarios**:
1. **Auth broken**: Immediate rollback, users can't login
2. **OAuth broken**: Immediate rollback, Google login fails
3. **Error messages worse**: Can wait, not critical
4. **Performance issues**: Monitor, rollback if severe

---

**Created by**: @auth-security-fixer, @error-message-improver
**Date**: 2026-02-09
**Status**: READY FOR MANUAL TESTING
**Next Step**: Deploy to staging and execute test plan
