# Free User Search Bug Fix - QA Validation Test Suite

## Overview

This comprehensive test suite validates the fix for the free user search bug, ensuring that free users can successfully execute searches with proper balance deduction, history tracking, and state management.

## Test Files

### 1. **free-user-search-flow.test.tsx**
**Purpose:** End-to-end free user search journey validation

**Scenarios Covered:**
- AC1: Initial state with 3 free searches
- AC2: Execute first search
- AC3: Balance deduction (3 → 2 → 1 → 0)
- AC4: Zero balance scenario (blocks search)
- AC5: Navigation persistence
- AC6: Regression prevention

**Edge Cases:**
- Zero balance blocks search
- Last search shows upgrade prompt
- Navigation preserves quota state
- Correct calculation: `creditsRemaining = 3 - totalSearches`

**Key Assertions:**
```typescript
// Initial state
expect(screen.getByText(/3.*buscas.*restantes/i)).toBeInTheDocument();

// After first search
expect(screen.getByText(/2.*buscas.*restantes/i)).toBeInTheDocument();

// Zero balance
expect(searchButton).toBeDisabled();
```

### 2. **free-user-balance-deduction.test.tsx**
**Purpose:** Validates quota deduction mechanism

**Scenarios Covered:**
- AC1: Backend /api/me returns correct quota_remaining
- AC2: Frontend useQuota calculates creditsRemaining correctly
- AC3: QuotaBadge displays correct values
- AC4: Server-side quota validation (403 when quota = 0)
- AC5: Concurrent search prevention
- AC6: Failed searches don't deduct quota
- AC7: Quota refresh mechanism

**Edge Cases:**
- Stale backend data (frontend calculates: 3 - quota_used)
- Concurrent searches (race condition)
- Network failures during quota update
- Quota exceeds limit (cap at 0)

**Key Assertions:**
```typescript
// Frontend calculation handles stale data
expect(result.current.quota?.creditsRemaining).toBe(2); // 3 - 1, ignoring stale quota_remaining

// Failed search doesn't deduct
expect(data2.quota_used).toBe(1); // Unchanged after failure
```

### 3. **free-user-history-save.test.tsx**
**Purpose:** Validates search history persistence

**Scenarios Covered:**
- AC1: Search session saved to database
- AC2: History page displays saved searches
- AC3: Failed searches don't create history
- AC4: History pagination
- AC5: History ordering (newest first)
- AC6: Re-run search from history
- AC7: Free user history limit

**Edge Cases:**
- Empty results (0 filtrado) still create history
- Pagination with limit/offset
- Custom keyword searches saved correctly
- Re-run reconstructs search params

**Key Assertions:**
```typescript
// Session saved
expect(historyData.sessions).toHaveLength(1);
expect(historyData.sessions[0].total_filtered).toBe(15);

// Ordered by created_at DESC
expect(data.sessions[0].id).toBe('session-3'); // Newest
```

### 4. **free-user-navigation-persistence.test.tsx**
**Purpose:** Validates state persistence across navigation

**Scenarios Covered:**
- AC1: Quota state persists across navigation
- AC2: Session persistence
- AC3: Page refresh behavior
- AC4: Browser back/forward buttons
- AC5: Deep linking with auth state
- AC6: Upgrade modal state persistence
- AC7: LocalStorage persistence

**Edge Cases:**
- Page refresh clears results but preserves quota
- Navigation after quota exhaustion
- Deep links require authentication
- LocalStorage saved searches persist

**Key Assertions:**
```typescript
// Quota persists across pages
expect(mockUseQuota).toHaveBeenCalled();

// Results cleared after refresh
expect(screen.queryByText(/Test results/i)).not.toBeInTheDocument();
```

### 5. **free-user-auth-token-consistency.test.tsx**
**Purpose:** Validates authentication token handling

**Scenarios Covered:**
- AC1: Token sent with every API request
- AC2: Expired token handling
- AC3: Invalid token handling
- AC4: Token consistency across parallel requests
- AC5: Logout clears token
- AC6: Token validation on protected routes
- AC7: Network errors during auth
- AC8: Regression - Token always included

**Edge Cases:**
- Expired token triggers re-authentication
- Token refresh race condition
- Invalid token (401 Unauthorized)
- Concurrent requests use same token

**Key Assertions:**
```typescript
// Token included
expect(mockFetch).toHaveBeenCalledWith(
  '/api/buscar',
  expect.objectContaining({
    headers: expect.objectContaining({
      Authorization: `Bearer ${validToken}`,
    }),
  })
);

// Expired token rejected
expect(response.status).toBe(401);
```

## Running the Tests

### Run All Free User Tests
```bash
npm test -- free-user
```

### Run Individual Test Files
```bash
# Search flow
npm test -- free-user-search-flow.test.tsx

# Balance deduction
npm test -- free-user-balance-deduction.test.tsx

# History save
npm test -- free-user-history-save.test.tsx

# Navigation persistence
npm test -- free-user-navigation-persistence.test.tsx

# Auth token consistency
npm test -- free-user-auth-token-consistency.test.tsx
```

### Run with Coverage
```bash
npm run test:coverage -- free-user
```

### Watch Mode (for development)
```bash
npm run test:watch -- free-user
```

## Expected Results

### All Tests Passing (Post-Fix)
```
Test Suites: 5 passed, 5 total
Tests:       87 passed, 87 total
Snapshots:   0 total
Time:        12.456 s
```

### Test Coverage Target
```
File                  | Stmts | Branch | Funcs | Lines |
----------------------|-------|--------|-------|-------|
useQuota.ts           | 100%  | 100%   | 100%  | 100%  |
QuotaBadge.tsx        | 95%   | 90%    | 100%  | 95%   |
buscar/page.tsx       | 75%   | 70%    | 80%   | 75%   |
historico/page.tsx    | 80%   | 75%    | 85%   | 80%   |
AuthProvider.tsx      | 90%   | 85%    | 90%   | 90%   |
```

## Test Matrix

| Scenario | Test File | AC Count | Edge Cases | Status |
|----------|-----------|----------|------------|--------|
| Complete Flow | free-user-search-flow.test.tsx | 6 | 4 | ✅ Ready |
| Balance Deduction | free-user-balance-deduction.test.tsx | 7 | 4 | ✅ Ready |
| History Save | free-user-history-save.test.tsx | 7 | 4 | ✅ Ready |
| Navigation | free-user-navigation-persistence.test.tsx | 7 | 4 | ✅ Ready |
| Auth Tokens | free-user-auth-token-consistency.test.tsx | 8 | 4 | ✅ Ready |
| **TOTAL** | **5 files** | **35 ACs** | **20 edge cases** | **87 tests** |

## Critical Test Scenarios

### 1. Balance Deduction Flow
```typescript
// Free user starts with 3 searches
quota.creditsRemaining = 3
quota.totalSearches = 0

// After first search
quota.creditsRemaining = 2  // 3 - 1
quota.totalSearches = 1

// After second search
quota.creditsRemaining = 1  // 3 - 2
quota.totalSearches = 2

// After third search
quota.creditsRemaining = 0  // 3 - 3
quota.totalSearches = 3

// Fourth search blocked
searchButton.disabled = true
```

### 2. Frontend Calculation (Handles Stale Backend)
```typescript
// Backend bug scenario (stale quota_remaining = 999999)
backend_response = {
  quota_remaining: 999999,  // Bug: not updated
  quota_used: 1
}

// Frontend calculates correctly
creditsRemaining = Math.max(0, 3 - quota_used)
creditsRemaining = Math.max(0, 3 - 1)
creditsRemaining = 2  // ✅ Correct!
```

### 3. Search Authorization Flow
```typescript
// Request
POST /api/buscar
Headers: { Authorization: 'Bearer token-123' }

// Backend validates
if quota_remaining <= 0:
  return 403 Forbidden { code: 'QUOTA_EXCEEDED' }

// Frontend blocks
if creditsRemaining <= 0:
  searchButton.disabled = true
  showUpgradeModal()
```

### 4. History Persistence
```typescript
// Successful search
POST /api/buscar -> 200 OK
Backend: save_search_session(user_id, params, results)

// Failed search
POST /api/buscar -> 500 Error
Backend: NO session created

// View history
GET /api/sessions -> { sessions: [...], total: N }
```

## Debugging Failed Tests

### Test Fails: "creditsRemaining is null"
**Cause:** useQuota hook not calculating correctly
**Fix:** Check `frontend/hooks/useQuota.ts` lines 73-79

### Test Fails: "Search button not disabled at quota 0"
**Cause:** Form validation not checking quota
**Fix:** Check `frontend/app/buscar/page.tsx` canSearch logic

### Test Fails: "History not saved"
**Cause:** Backend not creating session
**Fix:** Check backend search endpoint session creation

### Test Fails: "Token not included in request"
**Cause:** useAuth hook not providing session
**Fix:** Check AuthProvider session state

## Regression Tests

These tests MUST pass to prevent the bug from recurring:

### RT1: Free user can search (creditsRemaining > 0)
```typescript
it('should allow search when creditsRemaining > 0', async () => {
  mockUseQuota.mockReturnValue({
    quota: { creditsRemaining: 1, isFreeUser: true }
  });

  expect(searchButton).toBeEnabled(); // ✅
});
```

### RT2: Free user blocked at quota 0
```typescript
it('should block search when creditsRemaining = 0', async () => {
  mockUseQuota.mockReturnValue({
    quota: { creditsRemaining: 0, isFreeUser: true }
  });

  expect(searchButton).toBeDisabled(); // ✅
});
```

### RT3: Frontend calculates quota correctly
```typescript
it('should calculate creditsRemaining = 3 - quota_used', async () => {
  // Backend returns quota_used = 1
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ quota_used: 1 })
  });

  const { result } = renderHook(() => useQuota());

  expect(result.current.quota.creditsRemaining).toBe(2); // ✅
});
```

### RT4: Search history saved on success
```typescript
it('should save search to history on 200 OK', async () => {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ total_filtrado: 10 })
  });

  await executeSearch();

  const history = await fetchHistory();
  expect(history.sessions).toHaveLength(1); // ✅
});
```

## Manual Testing Checklist

After all automated tests pass, perform manual validation:

- [ ] 1. Create new free user account
- [ ] 2. Verify 3 free searches shown in UI
- [ ] 3. Execute first search (quota: 3 → 2)
- [ ] 4. Verify search appears in history
- [ ] 5. Execute second search (quota: 2 → 1)
- [ ] 6. Execute third search (quota: 1 → 0)
- [ ] 7. Verify search button disabled
- [ ] 8. Verify upgrade modal shown
- [ ] 9. Navigate to /historico
- [ ] 10. Verify all 3 searches in history
- [ ] 11. Navigate back to /buscar
- [ ] 12. Verify quota still 0 (persisted)
- [ ] 13. Refresh page
- [ ] 14. Verify quota still 0 (from backend)
- [ ] 15. Logout and login
- [ ] 16. Verify quota still 0 (database persisted)

## Success Criteria

**Test suite is successful when:**
1. ✅ All 87 tests pass
2. ✅ Coverage meets targets (>75% for modified files)
3. ✅ No console errors during test execution
4. ✅ Manual testing checklist completed
5. ✅ Regression tests prevent bug recurrence

## Integration with CI/CD

### Pre-deployment Checks
```yaml
# .github/workflows/test.yml
- name: Run Free User QA Tests
  run: npm test -- free-user --ci --coverage

- name: Check Coverage
  run: |
    if [ "$(cat coverage/coverage-summary.json | jq '.total.lines.pct')" -lt "75" ]; then
      echo "Coverage too low"
      exit 1
    fi
```

### Test Execution Timeline
- **Pre-commit:** Run affected tests (~5s)
- **Pre-push:** Run full suite (~15s)
- **CI/CD:** Run all tests + coverage (~30s)
- **Pre-deploy:** Run integration tests (~60s)

## Maintenance

### Adding New Tests
1. Follow existing file structure
2. Use descriptive test names (AC1, AC2, etc.)
3. Document edge cases
4. Update this README

### Updating Tests After Code Changes
1. Run `npm test -- free-user` to identify failures
2. Update test expectations if behavior intentionally changed
3. Add regression test if fixing new bug
4. Maintain coverage levels

---

**Last Updated:** 2026-02-10
**Test Suite Version:** 1.0.0
**Total Tests:** 87 across 5 files
**Estimated Run Time:** ~15 seconds
