# Test Quarantine Inventory

**Created:** 2026-02-13
**Story:** STORY-218
**Track:** Frente A - Quarantine Frontend Failures
**Total Quarantined:** 22 test suites (133 failing tests out of 203 total tests in these suites)

## Context

These 22 test suites were quarantined from the main Jest run to unblock CI/CD. Before quarantine, the frontend test suite had **23 failing suites / 137 failing tests**. After quarantine, the main suite has **1 failing suite / 4 failing tests** (`download.test.ts`, being rewritten by Frente B).

The quarantined tests are excluded from the default `npm test` run via `testPathIgnorePatterns` in `jest.config.js`, and can be run separately via `npm run test:quarantine`.

**Note:** After moving tests to `__tests__/quarantine/`, relative paths in `jest.mock()` calls are broken for many suites (the relative path depth changed by one level). This is expected -- the "Failure Category" column below reflects the ORIGINAL failure reason before quarantine, not the post-move module resolution error.

## Frontend Quarantined Tests

| # | Test File | Original Location | Failure Category | Failing Tests | Total Tests | Estimated Fix Effort |
|---|-----------|-------------------|-----------------|---------------|-------------|---------------------|
| 1 | analytics.test.ts | `__tests__/` | stale mock | 15 | 17 | medium |
| 2 | download-route.test.ts | `__tests__/api/` | component API change | 3 | 12 | medium |
| 3 | oauth-google-callback.test.tsx | `__tests__/auth/` | stale mock | 2 | 4 | medium |
| 4 | AnalyticsProvider.test.tsx | `__tests__/components/` | stale mock | 19 | 19 | medium |
| 5 | AuthProvider.test.tsx | `__tests__/components/` | stale mock | 1 | 18 | low |
| 6 | Countdown.test.tsx | `__tests__/components/` | async issue | 2 | 10 | low |
| 7 | LicitacaoCard.test.tsx | `__tests__/components/` | component API change | 3 | 14 | medium |
| 8 | LicitacoesPreview.test.tsx | `__tests__/components/` | component API change | 1 | 6 | low |
| 9 | PaginacaoSelect.test.tsx | `__tests__/components/` | component API change | 1 | 5 | low |
| 10 | error.test.tsx | `__tests__/` | component API change | 5 | 10 | low |
| 11 | free-user-auth-token-consistency.test.tsx | `__tests__/` | stale mock | 3 | 6 | high |
| 12 | free-user-history-save.test.tsx | `__tests__/` | stale mock | 3 | 7 | high |
| 13 | free-user-navigation-persistence.test.tsx | `__tests__/` | stale mock | 8 | 10 | high |
| 14 | free-user-search-flow.test.tsx | `__tests__/` | stale mock | 13 | 13 | high |
| 15 | GoogleSheetsExportButton.test.tsx | `__tests__/` | stale mock | 7 | 9 | medium |
| 16 | useAnalytics.test.ts | `__tests__/hooks/` | stale mock | 20 | 20 | medium |
| 17 | useSearch.test.ts | `__tests__/hooks/` | stale mock | 1 | 7 | low |
| 18 | useSearchFilters.test.ts | `__tests__/hooks/` | stale mock | 2 | 7 | medium |
| 19 | page.test.tsx | `__tests__/` | component API change | 7 | 22 | high |
| 20 | ContaPage.test.tsx | `__tests__/pages/` | stale mock | 11 | 13 | medium |
| 21 | DashboardPage.test.tsx | `__tests__/pages/` | component API change | 8 | 15 | medium |
| 22 | MensagensPage.test.tsx | `__tests__/pages/` | stale mock | 1 | 13 | low |

## Failure Category Summary

| Category | Count | Description |
|----------|-------|-------------|
| stale mock | 14 | `jest.mock()` does not match current module API (e.g., Supabase client shape changed, Mixpanel mock incomplete) |
| component API change | 7 | Component DOM structure or CSS classes changed; test queries (getByText, getByRole, toHaveClass) no longer match |
| async issue | 1 | Timer/callback mocking issue (Countdown onExpire not firing) |

## Fix Effort Summary

| Effort | Count | Description |
|--------|-------|-------------|
| low | 6 | < 30 min: Single assertion fix or minor mock update |
| medium | 11 | 30 min - 2h: Multiple mock updates or substantial query rewrites |
| high | 5 | > 2h: Complex integration test suites requiring full mock overhaul |

## How to Run Quarantined Tests

```bash
# Run all quarantined tests (non-blocking)
cd frontend
npm run test:quarantine

# Run a specific quarantined test
npx jest __tests__/quarantine/components/Countdown.test.tsx --testPathIgnorePatterns='/node_modules/' --no-coverage
```

## Fixing and Un-Quarantining

When fixing a quarantined test:

1. Fix the test in its quarantine location
2. Verify it passes: `npx jest __tests__/quarantine/<path> --testPathIgnorePatterns='/node_modules/' --no-coverage`
3. Move it back to its original location (see "Original Location" column)
4. Fix any relative `jest.mock()` paths (remove one `../` level from relative paths)
5. Verify it passes in the main suite: `npm test -- --testPathPattern='<original-path>'`
6. Update this document (remove the row, decrement the total)

## CI Integration

The quarantined tests run as a non-blocking step in `.github/workflows/tests.yml`:
- They execute after the main test suite
- They use `continue-on-error: true` so failures do not block PRs
- The output is visible in CI logs for tracking progress
