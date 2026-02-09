# STORY-176: Production Hotfix - Auth Security & Error Messages

**Squad**: prod-hotfix-squad
**Priority**: P0 (CRITICAL)
**Type**: Hotfix
**Created**: 2026-02-09
**Status**: Ready to Start

## Context

Two critical issues were identified in production logs on 2026-02-09:

### Issue 1: Insecure Auth Pattern (Security Risk)
Multiple Supabase warnings appearing in production:
```
Using the user object as returned from supabase.auth.getSession() or from some
supabase.auth.onAuthStateChange() events could be insecure! This value comes
directly from the storage medium (usually cookies on the server) and may not be
authentic. Use supabase.auth.getUser() instead which authenticates the data by
contacting the Supabase Auth server.
```

### Issue 2: Misleading Error Messages (UX Failure)
Backend logs show date range validation failures, but frontend displays generic errors:
- **Backend log**: `Date range validation failed for user *: requested=8 days, max_allowed=7 days`
- **Frontend shows**: "Limite de requisições excedido (2/min)" and "Algo deu errado. Tente novamente"
- **User impact**: Confusion - user thinks it's rate limiting when it's actually date range

## Acceptance Criteria

### Phase 1: Auth Security Fix ✅
- [ ] Audit all `getSession()` calls that access user object
- [ ] Replace insecure patterns with `getUser()`
- [ ] Validate no security warnings remain in logs
- [ ] All auth-related tests pass
- [ ] Document the secure pattern

### Phase 2: Error Message Clarity ✅
- [ ] Audit backend-to-frontend error flow
- [ ] Map backend HTTPException codes to frontend handlers
- [ ] Fix date range error to show actual issue
- [ ] Fix rate limit error to show actual limit
- [ ] Test all error scenarios with screenshots
- [ ] Validate error messages are user-actionable

## Implementation Plan

### Step 1: Auth Security Audit
**Agent**: @auth-security-fixer
**Task**: `*audit-auth-calls`

```bash
# Files to check:
frontend/middleware.ts
frontend/app/components/AuthProvider.tsx
frontend/app/auth/callback/page.tsx
```

**Expected Output**:
- List of all insecure getSession() usages
- Count of security issues
- Recommended fix for each location

### Step 2: Replace Insecure Auth Calls
**Agent**: @auth-security-fixer
**Task**: `*replace-getsession`

**Pattern**:
```typescript
// BEFORE (INSECURE):
const { data: { session } } = await supabase.auth.getSession()
if (session?.user) { ... }

// AFTER (SECURE):
const { data: { user }, error } = await supabase.auth.getUser()
if (user) { ... }
```

**Files to Modify**:
- frontend/middleware.ts
- frontend/app/components/AuthProvider.tsx
- frontend/app/auth/callback/page.tsx

### Step 3: Validate Auth Security
**Agent**: @auth-security-fixer
**Task**: `*validate-auth-security`

**Validation**:
- [ ] Run all auth tests: `npm test -- auth`
- [ ] Check production logs for warnings
- [ ] Verify OAuth flow still works
- [ ] Test session refresh behavior

### Step 4: Error Message Audit
**Agent**: @error-message-improver
**Task**: `*audit-error-messages`

**Backend Location**: `backend/main.py:964`
```python
# Current error handling:
logger.warning(
    f"Date range validation failed for user {mask_user_id(user['id'])}: "
    f"requested={date_range_days} days, max_allowed={max_history_days} days"
)
raise HTTPException(status_code=400, detail=error_msg)
```

**Frontend Impact**: Investigate how 400 errors are handled

### Step 5: Map Backend to Frontend
**Agent**: @error-message-improver
**Task**: `*map-backend-to-frontend`

**Error Mapping Table**:
| Backend Exception | HTTP Code | Frontend Handler | User Message |
|------------------|-----------|------------------|--------------|
| Date range > max | 400 | Generic toast | ❌ Wrong message |
| Rate limit hit | 429 | Rate limit toast | ❌ Shows for date error |
| Auth invalid | 401 | Redirect to login | ✅ Correct |

### Step 6: Fix Generic Errors
**Agent**: @error-message-improver
**Task**: `*fix-generic-errors`

**Changes Required**:

**Backend** (`backend/main.py`):
```python
# Add structured error response:
raise HTTPException(
    status_code=400,
    detail={
        "error_code": "DATE_RANGE_EXCEEDED",
        "message": f"O período de busca não pode exceder {max_history_days} dias. Você tentou buscar {date_range_days} dias.",
        "max_allowed": max_history_days,
        "requested": date_range_days,
        "plan": quota_info.plan_name
    }
)
```

**Frontend** (error handler):
```typescript
// Add specific error code handling:
if (error.error_code === 'DATE_RANGE_EXCEEDED') {
  toast.error(
    `O período de busca não pode exceder ${error.max_allowed} dias. ` +
    `Você tentou buscar ${error.requested} dias. ` +
    `Reduza o período e tente novamente.`,
    { duration: 6000 }
  )
}
```

### Step 7: Test Error Scenarios
**Agent**: @error-message-improver
**Task**: `*test-error-scenarios`

**Test Cases**:
1. Date range exceeds plan limit (8 days on 7-day plan)
2. Actual rate limit hit (3 requests in 1 minute)
3. Invalid auth token
4. Network error
5. Server error (500)

**Validation**:
- [ ] Screenshot each error message
- [ ] Verify user understands the problem
- [ ] Verify user knows how to fix it
- [ ] No generic "Algo deu errado" messages

## File List

### Modified Files
- [ ] `frontend/middleware.ts` - Replace getSession
- [ ] `frontend/app/components/AuthProvider.tsx` - Replace getSession
- [ ] `frontend/app/auth/callback/page.tsx` - Replace getSession
- [ ] `backend/main.py` - Structured error responses
- [ ] `frontend/lib/api-client.ts` (or error handler) - Error code handling
- [ ] `frontend/components/ui/toast.tsx` (if needed) - Error display

### Test Files
- [ ] `frontend/__tests__/auth/*.test.tsx` - Auth security tests
- [ ] `frontend/__tests__/errors/*.test.tsx` - Error message tests (new)

### Documentation
- [ ] `docs/sessions/2026-02/session-2026-02-09-prod-hotfix.md` - Session notes
- [ ] `docs/architecture/error-handling.md` - Error handling patterns

## Success Metrics

### Before Fix
- ❌ 5+ Supabase security warnings per minute in logs
- ❌ 100% of date range errors show as "Rate limit exceeded"
- ❌ Users confused about what went wrong

### After Fix
- ✅ Zero Supabase security warnings
- ✅ 100% of date range errors show actual issue
- ✅ Clear, actionable error messages
- ✅ User knows exactly what to change

## Rollback Plan

If issues occur after deployment:

**Phase 1 (Auth)**:
```bash
git revert <commit-hash>
npm run build
npm run deploy
```

**Phase 2 (Errors)**:
```bash
git revert <commit-hash>
# No critical impact, can roll back anytime
```

## Dependencies

- Supabase Auth SDK knowledge
- FastAPI HTTPException handling
- Next.js error boundary patterns
- Toast notification system

## Related Issues

- Original auth fix: Commit `2514b2b` (Google OAuth double login)
- Rate limiting implementation: Backend `main.py` lines 940-970
- Frontend error handling: Needs investigation

## Notes

- Both issues are P0 because they impact production UX and security
- Auth fix is higher priority (security risk)
- Error message fix prevents user confusion and support tickets
- Must test thoroughly before deploying to production

---

**Agents**: @auth-security-fixer, @error-message-improver
**Story ID**: STORY-176
**Epic**: Technical Debt / Production Quality
