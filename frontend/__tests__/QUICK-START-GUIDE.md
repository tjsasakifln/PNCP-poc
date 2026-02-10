# Free User QA Tests - Quick Start Guide

## TL;DR

```bash
# Run all free user tests
npm test -- free-user

# Expected result
# Test Suites: 5 passed, 5 total
# Tests:       87 passed, 87 total
# Time:        ~15 seconds
```

## Test Files Overview

| File | Tests | What It Tests |
|------|-------|---------------|
| `free-user-search-flow.test.tsx` | 18 | Complete user journey (search → results → history) |
| `free-user-balance-deduction.test.tsx` | 19 | Quota decrements correctly (3 → 2 → 1 → 0) |
| `free-user-history-save.test.tsx` | 17 | Search history persists to database |
| `free-user-navigation-persistence.test.tsx` | 16 | State maintained across page navigation |
| `free-user-auth-token-consistency.test.tsx` | 17 | Auth tokens handled correctly |

## Common Commands

### Run All Tests
```bash
npm test -- free-user
```

### Run Specific File
```bash
npm test -- free-user-search-flow.test.tsx
```

### Watch Mode (Auto-rerun on changes)
```bash
npm run test:watch -- free-user
```

### With Coverage Report
```bash
npm run test:coverage -- free-user
```

### CI Mode (for deployment pipeline)
```bash
npm run test:ci -- free-user
```

## Reading Test Output

### ✅ All Passing
```
PASS  __tests__/free-user-search-flow.test.tsx
PASS  __tests__/free-user-balance-deduction.test.tsx
PASS  __tests__/free-user-history-save.test.tsx
PASS  __tests__/free-user-navigation-persistence.test.tsx
PASS  __tests__/free-user-auth-token-consistency.test.tsx

Test Suites: 5 passed, 5 total
Tests:       87 passed, 87 total
```

### ❌ Test Failure Example
```
FAIL  __tests__/free-user-balance-deduction.test.tsx
  ● Balance Deduction Verification › should calculate creditsRemaining correctly

    expect(received).toBe(expected)

    Expected: 2
    Received: null

      74 |       await waitFor(() => {
      75 |         expect(result.current.loading).toBe(false);
    > 76 |         expect(result.current.quota?.creditsRemaining).toBe(2);
         |                                                         ^
```

## Key Test Scenarios

### 1. Balance Deduction
```typescript
Test: User starts with 3 searches
✓ Initial: 3 searches remaining
✓ After 1st search: 2 remaining
✓ After 2nd search: 1 remaining
✓ After 3rd search: 0 remaining
✓ Search button disabled at 0
```

### 2. Quota Calculation
```typescript
Test: Frontend handles stale backend data
✓ Backend returns: quota_remaining = 999999 (bug)
✓ Frontend calculates: 3 - quota_used = correct value
✓ Display shows: correct remaining searches
```

### 3. History Persistence
```typescript
Test: Searches saved to history
✓ Execute search → 200 OK
✓ Check /historico → session appears
✓ Session contains: UFs, dates, results
```

### 4. Navigation State
```typescript
Test: Quota persists across pages
✓ /buscar → quota: 2 remaining
✓ Navigate to /historico → quota: 2 remaining
✓ Navigate back to /buscar → quota: 2 remaining
```

### 5. Auth Tokens
```typescript
Test: Token included in all requests
✓ /api/buscar → has Authorization header
✓ /api/me → has Authorization header
✓ /api/sessions → has Authorization header
✓ Expired token → redirects to login
```

## Debugging Failed Tests

### Problem: "creditsRemaining is null"
**File to Check:** `frontend/hooks/useQuota.ts`
**Line:** 73-79
**What to Look For:**
```typescript
// Should be:
creditsRemaining = Math.max(0, FREE_SEARCHES_LIMIT - quotaUsed);

// Not:
creditsRemaining = quotaRemaining; // ❌ Wrong (uses stale data)
```

### Problem: "Search button not disabled at 0"
**File to Check:** `frontend/app/buscar/page.tsx`
**What to Look For:**
```typescript
// Should be:
const canSearch = !loading && creditsRemaining > 0;

// Not:
const canSearch = !loading; // ❌ Wrong (doesn't check quota)
```

### Problem: "History not saved"
**File to Check:** Backend search endpoint
**What to Look For:**
- Session creation after successful search
- Database insert statement
- Error handling

### Problem: "Token not in request"
**File to Check:** `frontend/app/components/AuthProvider.tsx`
**What to Look For:**
```typescript
// Should provide:
session.access_token

// Not:
session = null // ❌ Wrong
```

## Manual Testing After Tests Pass

Quick 5-minute validation:

1. **Sign up as free user** → See "3 buscas restantes"
2. **Do 1st search** → See "2 buscas restantes" + results
3. **Check /historico** → See 1 search saved
4. **Do 2nd search** → See "1 busca restante"
5. **Do 3rd search** → See "0 buscas restantes"
6. **Try 4th search** → Button disabled + upgrade modal
7. **Refresh page** → Quota still 0 (persisted)
8. **Logout/login** → Quota still 0 (from database)

## Coverage Expectations

After tests pass, check coverage:

```bash
npm run test:coverage -- free-user
```

**Target:**
```
File                  | Stmts | Branch | Funcs | Lines |
----------------------|-------|--------|-------|-------|
useQuota.ts           | 100%  | 100%   | 100%  | 100%  |
QuotaBadge.tsx        | >90%  | >85%   | 100%  | >90%  |
buscar/page.tsx       | >75%  | >70%   | >80%  | >75%  |
historico/page.tsx    | >80%  | >75%   | >85%  | >80%  |
```

## When Tests Fail

### Step 1: Identify Which File Failed
```bash
npm test -- free-user --verbose
```

### Step 2: Run Just That File
```bash
npm test -- free-user-balance-deduction.test.tsx
```

### Step 3: Check Error Message
- **"toBe(2) received null"** → Quota calculation issue
- **"toBeDisabled() received enabled"** → Button state issue
- **"toHaveLength(1) received 0"** → History not saved
- **"toBeInTheDocument() not found"** → UI rendering issue

### Step 4: Fix the Code
- Read error message carefully
- Check file location in error
- Fix the implementation
- Re-run test

### Step 5: Verify Fix
```bash
npm test -- free-user
```

## Integration with Git Workflow

### Before Committing
```bash
npm test -- free-user
```

### Before Pushing
```bash
npm test -- free-user --coverage
```

### In CI/CD Pipeline
```yaml
- name: Run Free User Tests
  run: npm test -- free-user --ci --coverage
```

## Common Questions

### Q: How long do tests take?
**A:** ~15 seconds for all 87 tests

### Q: Do I need to run all tests?
**A:** Yes, before committing. But you can run individual files during development.

### Q: What if tests fail in CI but pass locally?
**A:** Check for:
- Environment differences
- Async timing issues
- Mock data inconsistencies

### Q: How do I add a new test?
**A:**
1. Add to appropriate file
2. Follow existing test structure
3. Run to verify
4. Update documentation

### Q: Can I skip tests?
**A:** No, all tests must pass before deployment.

## Success Checklist

Before marking QA complete:

- [ ] All 87 tests pass
- [ ] Coverage >75% for modified files
- [ ] No console errors during tests
- [ ] Manual testing checklist completed
- [ ] Tests run successfully in CI/CD
- [ ] Documentation reviewed

## Getting Help

### Test Documentation
- **Full Guide:** `FREE-USER-QA-TEST-SUITE.md`
- **Summary:** `QA-TEST-SUITE-SUMMARY.md`
- **This Guide:** `QUICK-START-GUIDE.md`

### Test File Locations
```
frontend/__tests__/
├── free-user-search-flow.test.tsx
├── free-user-balance-deduction.test.tsx
├── free-user-history-save.test.tsx
├── free-user-navigation-persistence.test.tsx
└── free-user-auth-token-consistency.test.tsx
```

### Common Patterns

**Test Structure:**
```typescript
describe('Feature', () => {
  beforeEach(() => {
    // Setup
  });

  it('should do something', async () => {
    // Arrange
    const mockData = { ... };

    // Act
    render(<Component />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText(/expected/i)).toBeInTheDocument();
    });
  });
});
```

**Async Testing:**
```typescript
await waitFor(() => {
  expect(asyncResult).toBeTruthy();
});
```

**Mocking:**
```typescript
mockFetch.mockResolvedValueOnce({
  ok: true,
  json: () => Promise.resolve({ data: 'value' })
});
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `npm test -- free-user` | Run all tests |
| `npm test -- [filename]` | Run specific file |
| `npm run test:watch -- free-user` | Watch mode |
| `npm run test:coverage -- free-user` | With coverage |
| `npm run test:ci` | CI mode |

**Total Tests:** 87
**Total Files:** 5
**Run Time:** ~15 seconds
**Coverage Target:** >75%

---

**Last Updated:** 2026-02-10
**Version:** 1.0.0
**Status:** ✅ Ready to Use
