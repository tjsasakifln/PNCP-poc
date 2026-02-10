# Backend Debug Summary: Free User Search Failures
**Date:** 2026-02-10
**Status:** 🔴 ROOT CAUSE IDENTIFIED → ✅ FIX READY

---

## Quick Summary

**Problem:** Free users' searches execute successfully but are NOT saved to search history.

**Root Cause:** Missing Row Level Security (RLS) policy for backend service role on `search_sessions` table.

**Impact:**
- ✅ Balance consumption: **WORKING** (quota tracked)
- ❌ Search history: **FAILING** (writes blocked by RLS)
- ✅ Auth/Plans APIs: **WORKING**

**Fix:** Add service role RLS policy (1 SQL file, 5-minute deployment)

---

## Root Causes Identified

### 1. Missing RLS Policy for Service Role ⭐ PRIMARY ISSUE

**Location:** `supabase/migrations/001_profiles_and_sessions.sql`

**Problem:**
```sql
-- search_sessions table
ALTER TABLE public.search_sessions ENABLE ROW LEVEL SECURITY;

-- ✅ Has user policies
CREATE POLICY "sessions_select_own" ...
CREATE POLICY "sessions_insert_own" ...

-- ❌ MISSING: Service role policy
-- Backend uses service role key but no policy allows it!
```

**Comparison - What Works (monthly_quota):**
```sql
-- From backend/migrations/002_monthly_quota.sql
CREATE POLICY "Service role can manage quota" ON monthly_quota
    FOR ALL
    USING (true);  -- ✅ Allows service role full access
```

**Why This Breaks:**
1. Backend uses `SUPABASE_SERVICE_ROLE_KEY` for all DB operations
2. Service role bypasses auth context (`auth.uid()` = NULL)
3. Existing policies only check `auth.uid() = user_id`
4. PostgreSQL RLS blocks the INSERT
5. Exception caught but not raised (silent failure)

---

### 2. Silent Failure Design

**Location:** `backend/main.py` (lines 1696-1720)

```python
# After successful search...
try:
    save_search_session(user_id, ...)  # ❌ INSERT blocked by RLS
except Exception as e:
    logger.error(f"Failed to save: {e}")  # Logged but not raised
    # ⚠️ Request continues, returns 200 OK
```

**Result:** User gets 200 OK response but search NOT in history.

---

## File References

### Critical Files

| File | Issue | Line |
|------|-------|------|
| `supabase/migrations/001_profiles_and_sessions.sql` | Missing service role policy | 104-128 |
| `backend/main.py` | Silent failure on history save | 1696-1720 |
| `backend/quota.py` | save_search_session() throws exception | 521-571 |
| `backend/migrations/002_monthly_quota.sql` | Working example (has policy) | 29-33 |

### Supporting Files

- `backend/supabase_client.py` - Service role client initialization
- `backend/auth.py` - Token validation (working correctly)
- `frontend/app/api/me/route.ts` - Profile API (working)
- `frontend/lib/plans.ts` - Plan configs (working)

---

## The Fix

### Migration File Created

**File:** `supabase/migrations/006_search_sessions_service_role_policy.sql`

```sql
-- Add service role policy
DROP POLICY IF EXISTS "Service role can manage search sessions" ON public.search_sessions;
CREATE POLICY "Service role can manage search sessions" ON public.search_sessions
    FOR ALL
    USING (true);
```

**Location:** `/t/GERAL/SASAKI/Licitações/supabase/migrations/006_search_sessions_service_role_policy.sql`

---

## Deployment Steps

### 1. Apply Migration to Supabase

**Option A: Supabase Dashboard (Recommended)**
```
1. Open Supabase Dashboard
2. Navigate to: SQL Editor
3. Copy contents of 006_search_sessions_service_role_policy.sql
4. Run SQL
5. Verify: Check Policies tab for search_sessions table
```

**Option B: Supabase CLI**
```bash
cd /t/GERAL/SASAKI/Licitações
supabase db push
```

---

### 2. Verify Fix

**Check 1: Policy Exists**
```sql
SELECT policyname, cmd
FROM pg_policies
WHERE tablename = 'search_sessions'
AND policyname = 'Service role can manage search sessions';

-- Expected: 1 row returned
-- policyname: Service role can manage search sessions
-- cmd: ALL
```

**Check 2: Backend Logs**
```bash
# Before fix: errors on every search
grep "Failed to save search session" backend/logs/app.log

# After fix: should be empty
```

**Check 3: End-to-End Test**
```bash
# 1. Execute search via API
curl -X POST https://api.example.com/buscar \
  -H "Authorization: Bearer <token>" \
  -d '{"ufs":["SP"],"data_inicial":"2026-02-01","data_final":"2026-02-10","setor_id":"vestuario"}'

# 2. Check history endpoint
curl https://api.example.com/sessions?limit=1 \
  -H "Authorization: Bearer <token>"

# Expected: Search appears in sessions array
```

---

### 3. Monitor (First 24 Hours)

**Critical Metrics:**

✅ **Search session save success rate**
```sql
SELECT
  COUNT(*) as total_saves,
  DATE(created_at) as date
FROM search_sessions
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY DATE(created_at);
```
Expected: Matches number of searches executed

✅ **Error rate**
```bash
tail -f backend/logs/app.log | grep "Failed to save search session"
```
Expected: Zero errors

✅ **User history page engagement**
- Monitor /historico page views
- Expect increased usage after fix

---

## Testing Verification

### Before Fix (Current State)

```
✅ User logs in
✅ Search executes successfully
✅ Results returned (200 OK)
✅ Quota decremented (3 → 2)
❌ /historico page shows "No searches"
❌ /sessions API returns empty array
```

### After Fix (Expected)

```
✅ User logs in
✅ Search executes successfully
✅ Results returned (200 OK)
✅ Quota decremented (3 → 2)
✅ /historico page shows search
✅ /sessions API returns search data
```

---

## API Lifecycle (Simplified)

### Complete Flow for Free User Search

```
1. Frontend → POST /api/buscar
   ↓
2. Next.js API → Forwards to backend
   ↓
3. Backend Auth → ✅ Validates JWT token
   ↓
4. Backend Quota Check → ✅ Reads monthly_quota (service role policy exists)
   ↓
5. Backend Search → ✅ Fetches from PNCP, filters, LLM summary
   ↓
6. Backend Quota Increment → ✅ UPSERT monthly_quota (service role policy exists)
   ↓
7. Backend History Save → ❌ INSERT search_sessions (NO service role policy)
                          ❌ RLS blocks write
                          ❌ Exception caught, logged
   ↓
8. Response → ✅ 200 OK returned
              ❌ But history NOT saved!
```

**After Fix:**
- Step 7 succeeds (✅ INSERT allowed by new policy)
- Search history properly saved

---

## Balance Consumption Trace

### Why Quota Works But History Doesn't

**monthly_quota (✅ Working):**
```sql
-- Has service role policy
CREATE POLICY "Service role can manage quota" ON monthly_quota
    FOR ALL USING (true);

-- Backend operations succeed
sb.table("monthly_quota").upsert({...}).execute()  ✅
```

**search_sessions (❌ Broken):**
```sql
-- Missing service role policy
-- Only has: sessions_insert_own (auth.uid() = user_id)

-- Backend operations fail
sb.table("search_sessions").insert({...}).execute()  ❌ RLS BLOCK
```

---

## Database Write Trace

### Successful Path: Balance Consumption

```
User makes search
   ↓
Backend: check_quota(user_id)
   ↓
Supabase: SELECT * FROM monthly_quota WHERE user_id = ?
   ✅ Service role policy: USING (true)
   ✅ SELECT allowed
   ↓
Backend: increment_monthly_quota(user_id)
   ↓
Supabase: INSERT INTO monthly_quota ... ON CONFLICT DO UPDATE
   ✅ Service role policy: USING (true)
   ✅ UPSERT succeeds
   ✅ Quota tracked!
```

### Failed Path: Search History

```
User search completes
   ↓
Backend: save_search_session(user_id, ...)
   ↓
Supabase: INSERT INTO search_sessions ...
   ❌ RLS checks policies:
      - sessions_insert_own: auth.uid() = user_id
      - auth.uid() = NULL (service role context)
      - NULL = user_id → FALSE
   ❌ No service role policy exists
   ❌ RLS BLOCKS INSERT
   ↓
PostgreSQL: Raises RLS violation exception
   ↓
Backend: except Exception as e: logger.error(...)
   ↓
Request: Returns 200 OK anyway
   ❌ Search NOT in history!
```

---

## Rollback Plan

### If Issues Occur

**Rollback Trigger:**
- Database errors increase
- Performance degradation
- RLS policy conflicts

**Rollback Steps:**
```sql
-- Remove the policy
DROP POLICY IF EXISTS "Service role can manage search sessions"
ON public.search_sessions;
```

**Note:** Rollback returns to current (broken) state where history isn't saved.

---

## Success Criteria

### Immediate (First Hour)

- [ ] Migration applied successfully
- [ ] Policy visible in pg_policies table
- [ ] No backend errors in logs
- [ ] Test search appears in history

### Short-term (First 24 Hours)

- [ ] All user searches saved to history
- [ ] /historico page shows searches
- [ ] Zero "Failed to save search session" errors
- [ ] User engagement on history page increases

### Long-term (First Week)

- [ ] System stability maintained
- [ ] No RLS policy conflicts
- [ ] User satisfaction improves
- [ ] Support tickets about "missing searches" decrease

---

## Priority & Impact

**Priority:** 🔴 P0-CRITICAL

**User Impact:**
- **ALL users affected** (free, paid, all tiers)
- Users lose trust in platform
- Cannot review past searches
- Reduced product value
- Confusion: "Did my search work?"

**Business Impact:**
- Lost user confidence
- Reduced feature value (/historico page useless)
- Support ticket volume (users asking about history)
- Potential churn (paying users expect full functionality)

**Technical Impact:**
- Silent data loss (searches not recorded)
- Misleading UX (200 OK but data not saved)
- Quota works but history doesn't (inconsistent)

---

## Recommendations

### Immediate Actions (Today)

1. ✅ **Deploy migration 006** to production
2. ✅ **Monitor logs** for errors
3. ✅ **Test user flow** (search → verify in /historico)
4. ✅ **Communicate fix** to affected users

### Follow-Up Actions (This Week)

1. **Add Integration Test**
   - End-to-end: search → verify history saved
   - Prevent regression

2. **Audit Other Tables**
   - Check all RLS-enabled tables
   - Ensure service role policies exist where needed

3. **Document Pattern**
   - RLS policy requirements
   - Service role best practices
   - Add to developer onboarding

4. **Improve Error Handling**
   - Consider failing request if history save fails
   - OR improve logging/alerting for silent failures

---

## Related Documentation

**Files Created:**
- ✅ `BACKEND-DEBUG-REPORT-2026-02-10.md` - Comprehensive analysis
- ✅ `supabase/migrations/006_search_sessions_service_role_policy.sql` - Fix migration
- ✅ `BACKEND-FIX-SUMMARY.md` - This document

**Key References:**
- `supabase/migrations/001_profiles_and_sessions.sql` - Original schema
- `backend/migrations/002_monthly_quota.sql` - Working example
- `backend/quota.py` - save_search_session() implementation
- `backend/main.py` - Search execution flow

---

## Contact & Support

**Issue Tracking:**
- Report ID: BACKEND-DEBUG-2026-02-10
- Priority: P0-CRITICAL
- Status: FIX READY FOR DEPLOYMENT

**Prepared By:** Claude Sonnet 4.5 (Backend Architect)
**Date:** 2026-02-10
**Review Status:** Ready for Implementation

---

**🚀 READY TO DEPLOY - APPLY MIGRATION 006 TO FIX ISSUE**

