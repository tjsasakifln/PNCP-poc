# 🔥 Production Hotfix Squad

**Domain**: Production Quality & Security
**Version**: 1.0.0
**AIOS**: 2.1.0+
**Blueprint Confidence**: 91%

## 🎯 Mission

Fix critical production issues that impact security and user experience:
1. **Security**: Replace insecure Supabase auth patterns
2. **UX**: Fix misleading error messages that confuse users

## 📊 Squad Composition

### Agents (2)

| Agent | Role | Confidence | Commands |
|-------|------|------------|----------|
| **auth-security-fixer** | Fixes Supabase auth security issues | 95% | audit-auth-calls, replace-getsession, validate-auth-security |
| **error-message-improver** | Improves error message clarity | 92% | audit-error-messages, map-backend-to-frontend, fix-generic-errors, test-error-scenarios |

### Tasks (7)

#### Auth Security Tasks (3)
1. **audit-auth-calls** - Scan codebase for insecure getSession() usage
2. **replace-getsession** - Replace with secure getUser() pattern
3. **validate-auth-security** - Verify security fixes are complete

#### Error Message Tasks (4)
4. **audit-error-messages** - Map backend errors to frontend handlers
5. **map-backend-to-frontend** - Create error mapping table
6. **fix-generic-errors** - Replace generic messages with specific ones
7. **test-error-scenarios** - Validate all error scenarios

## 🚨 Production Issues

### Issue #1: Insecure Auth Pattern

**Severity**: CRITICAL (Security)
**Status**: Active in production

**Problem**:
```
Using the user object as returned from supabase.auth.getSession() or from some
supabase.auth.onAuthStateChange() events could be insecure! This value comes
directly from the storage medium (usually cookies on the server) and may not be
authentic. Use supabase.auth.getUser() instead which authenticates the data by
contacting the Supabase Auth server.
```

**Affected Files**:
- `frontend/middleware.ts`
- `frontend/app/components/AuthProvider.tsx`
- `frontend/app/auth/callback/page.tsx`

**Fix Pattern**:
```typescript
// BEFORE (INSECURE):
const { data: { session } } = await supabase.auth.getSession()
if (session?.user) {
  // Using user from session is INSECURE
}

// AFTER (SECURE):
const { data: { user }, error } = await supabase.auth.getUser()
if (user) {
  // User is authenticated by Supabase
}
```

**Impact**:
- 🔴 Security vulnerability
- 🔴 User data may not be authentic
- 🔴 Potential session hijacking

---

### Issue #2: Misleading Error Messages

**Severity**: CRITICAL (UX)
**Status**: Active in production

**Problem**:
Backend returns date range validation error, but frontend shows rate limit error.

**User Experience**:
1. User selects 8-day date range (plan allows 7 days)
2. Backend logs: `Date range validation failed: requested=8 days, max_allowed=7 days`
3. Frontend shows: "Limite de requisições excedido (2/min). Aguarde 49 segundos."
4. User sees: "Algo deu errado. Tente novamente em instantes."

**The Lie**: User thinks they hit rate limit, but actually exceeded date range.

**Backend Location**: `backend/main.py:964`
```python
logger.warning(
    f"Date range validation failed for user {mask_user_id(user['id'])}: "
    f"requested={date_range_days} days, max_allowed={max_history_days} days"
)
raise HTTPException(status_code=400, detail=error_msg)
```

**Frontend Impact**: Generic error toast instead of specific message

**Fix Required**:
- Backend: Add structured error codes (`DATE_RANGE_EXCEEDED`)
- Frontend: Handle error codes specifically
- Message: "O período de busca não pode exceder 7 dias. Você tentou buscar 8 dias. Reduza o período e tente novamente."

**Impact**:
- 🔴 User confusion
- 🔴 Support tickets
- 🔴 Bad UX ("vergonhoso" - shameful)

## 🎬 Execution Flow

### Phase 1: Auth Security (P0)

```
@auth-security-fixer
*audit-auth-calls
  ↓
  Scan frontend/ for getSession() + user access
  ↓
  Output: List of insecure locations

@auth-security-fixer
*replace-getsession
  ↓
  Replace all insecure patterns with getUser()
  ↓
  Output: Modified files

@auth-security-fixer
*validate-auth-security
  ↓
  Run tests, check logs
  ↓
  Output: Validation report
```

### Phase 2: Error Messages (P0)

```
@error-message-improver
*audit-error-messages
  ↓
  Map backend exceptions to frontend handlers
  ↓
  Output: Error flow diagram

@error-message-improver
*map-backend-to-frontend
  ↓
  Create error code mapping table
  ↓
  Output: Mapping table + missing handlers

@error-message-improver
*fix-generic-errors
  ↓
  Add error codes to backend
  Add handlers to frontend
  ↓
  Output: Improved error messages

@error-message-improver
*test-error-scenarios
  ↓
  Test all error conditions
  Take screenshots
  ↓
  Output: Validation report
```

## ✅ Success Criteria

### Auth Security
- ✅ Zero `getSession()` calls accessing user object
- ✅ All auth checks use `getUser()`
- ✅ Zero Supabase security warnings in logs
- ✅ All auth tests pass

### Error Messages
- ✅ Date range errors show actual issue
- ✅ Rate limit errors show actual limit
- ✅ No more "Algo deu errado" generic messages
- ✅ User knows exactly what to fix

## 🔧 Usage

### Activate Squad
```bash
# Option 1: Activate agent directly
@auth-security-fixer
*help

# Option 2: Activate via squad
/load-squad prod-hotfix
@auth-security-fixer
*audit-auth-calls
```

### Run Full Workflow
```bash
# Phase 1: Security
@auth-security-fixer
*audit-auth-calls
*replace-getsession
*validate-auth-security

# Phase 2: UX
@error-message-improver
*audit-error-messages
*map-backend-to-frontend
*fix-generic-errors
*test-error-scenarios
```

## 📦 Configuration

This squad extends project-level AIOS configuration:
- **Coding Standards**: `docs/framework/CODING-STANDARDS.md`
- **Tech Stack**: `docs/framework/TECH-STACK.md`
- **Source Tree**: `docs/framework/SOURCE-TREE.md`

## 📋 Story

**Story ID**: STORY-176
**File**: `docs/stories/STORY-176-prod-hotfix-auth-errors.md`
**Priority**: P0 (CRITICAL)
**Type**: Hotfix

## 🚀 Deployment Plan

### Phase 1: Auth Security Fix
1. Run audit
2. Apply fixes
3. Run tests
4. Deploy to staging
5. Verify logs
6. Deploy to production

**Rollback**: `git revert <commit-hash>`

### Phase 2: Error Message Clarity
1. Audit errors
2. Add backend error codes
3. Add frontend handlers
4. Test all scenarios
5. Deploy to staging
6. Deploy to production

**Rollback**: `git revert <commit-hash>` (non-critical)

## 📊 Metrics

### Before Fix
- ❌ 5+ Supabase warnings/min
- ❌ 100% date errors shown as rate limit
- ❌ User confusion HIGH

### After Fix
- ✅ 0 Supabase warnings
- ✅ 100% errors show actual issue
- ✅ User confusion LOW

## 🔗 Related Documentation

- [Supabase Auth Security Best Practices](https://supabase.com/docs/guides/auth/server-side/overview)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [Next.js Error Handling](https://nextjs.org/docs/advanced-features/error-handling)

## 📝 Blueprint Source

Generated from:
- Production logs (2026-02-09 16:24:24)
- Supabase security warnings (multiple instances)
- Date range validation errors (backend/main.py:964)

## 🏗️ Generated by

Squad Creator Agent (@craft)
- Task-first architecture
- AIOS 2.1 compliant
- 91% blueprint confidence
- 2 agents, 7 tasks, 0 workflows

---

**Author**: Tiago Sasaki
**License**: MIT
**Created**: 2026-02-09
