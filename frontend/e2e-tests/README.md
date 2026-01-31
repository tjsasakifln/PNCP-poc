# E2E Test Suite - BidIQ Uniformes

Comprehensive end-to-end test suite using Playwright for critical user flows.

## Test Coverage

### 1. Search Flow (`search-flow.spec.ts`)
Complete search and download journey:
- ✅ Select UF (SC, PR)
- ✅ Choose date range
- ✅ Click search
- ✅ Verify results displayed
- ✅ Download Excel file
- ✅ Verify filename format

**Tests:** 9 test cases covering happy path, validation, statistics display, and performance.

### 2. Theme Switching (`theme.spec.ts`)
Theme selection and persistence:
- ✅ Click theme toggle
- ✅ Verify CSS variables applied
- ✅ Check localStorage persistence
- ✅ Reload page → theme persists

**Tests:** 12 test cases covering theme switching, persistence, accessibility, and edge cases.

### 3. Saved Searches (`saved-searches.spec.ts`)
Search persistence and reload:
- ✅ Execute search
- ✅ Verify auto-save to localStorage
- ✅ Reload page
- ✅ Load saved search
- ✅ Verify form populated

**Tests:** 12 test cases covering save, load, delete, limit enforcement, and sorting.

### 4. Empty State (`empty-state.spec.ts`)
Handling no results scenario:
- ✅ Search with no results
- ✅ Verify empty state component
- ✅ Click "Adjust search"
- ✅ Verify form focus

**Tests:** 12 test cases covering empty state display, filter statistics, and user actions.

### 5. Error Handling (`error-handling.spec.ts`)
Network and API error scenarios:
- ✅ Mock network failure
- ✅ Execute search
- ✅ Verify error message
- ✅ Verify retry button

**Tests:** 15 test cases covering API errors, network failures, download errors, and validation.

## Running Tests

### Prerequisites
```bash
cd frontend
npm install
```

### Run All E2E Tests
```bash
npm run test:e2e
```

### Run Tests in Headed Mode (with browser visible)
```bash
npm run test:e2e:headed
```

### Run Tests in Debug Mode
```bash
npm run test:e2e:debug
```

### Run Tests in UI Mode (interactive)
```bash
npm run test:e2e:ui
```

### Run Specific Test File
```bash
npx playwright test e2e-tests/search-flow.spec.ts
```

### Run Tests for Specific Project (browser)
```bash
npx playwright test --project=chromium
npx playwright test --project="Mobile Safari"
```

### View Test Report
```bash
npm run test:e2e:report
```

## Test Architecture

### Page Object Model
Tests use the **Page Object pattern** for maintainability:

- **SearchPage**: Main page interactions (UF selection, search, results)
- **ThemeSelector**: Theme dropdown interactions
- **SavedSearchesDropdown**: Saved searches management

**Location:** `helpers/page-objects.ts`

### Test Utilities
Reusable mock data and helper functions:

- `mockSearchAPI()`: Mock search endpoint responses
- `mockDownloadAPI()`: Mock Excel download
- `mockSetoresAPI()`: Mock sectors endpoint
- `clearTestData()`: Clean localStorage/cookies
- `getCSSVariable()`: Read CSS custom properties
- `getLocalStorageItem()`: Access localStorage

**Location:** `helpers/test-utils.ts`

## Configuration

### Playwright Config (`playwright.config.ts`)
- **Test directory:** `./e2e-tests`
- **Timeout:** 60 seconds per test
- **Expect timeout:** 10 seconds for assertions
- **Projects:** Desktop Chrome, Mobile Safari
- **Screenshots:** On failure only
- **Video:** Retained on failure
- **Trace:** On first retry

### CI/CD Integration
Tests run automatically in GitHub Actions:
- **Trigger:** On push to main, PRs
- **Reports:** HTML report uploaded as artifact
- **JUnit:** XML report for integration

## Writing New Tests

### Example Test Structure
```typescript
import { test, expect } from '@playwright/test';
import { SearchPage } from './helpers/page-objects';
import { mockSearchAPI, clearTestData } from './helpers/test-utils';

test.describe('Feature Name', () => {
  let searchPage: SearchPage;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    await clearTestData(page);
    await mockSearchAPI(page, 'success');
    await searchPage.goto();
  });

  test('AC1: should do something', async () => {
    // Arrange
    await searchPage.selectUF('SC');

    // Act
    await searchPage.executeSearch();

    // Assert
    await expect(searchPage.resultsSection).toBeVisible();
  });
});
```

### Best Practices
1. **Use Page Objects**: Don't use raw selectors in tests
2. **Explicit Waits**: Use `waitFor()` or `expect()` with timeout
3. **Clean State**: Clear test data in `beforeEach`
4. **Mock APIs**: Use test utilities for consistent responses
5. **Descriptive Names**: Use AC (Acceptance Criteria) numbering
6. **Screenshots**: Automatically captured on failure
7. **Assertions**: Use Playwright's `expect()` for auto-retrying

## Debugging

### Debug Specific Test
```bash
npx playwright test --debug e2e-tests/search-flow.spec.ts
```

### Show Browser Traces
```bash
npx playwright show-trace trace.zip
```

### Generate Code
```bash
npx playwright codegen http://localhost:3000
```

## Performance

### Test Execution Time
- **Search Flow:** ~15-20 seconds (9 tests)
- **Theme Switching:** ~20-25 seconds (12 tests)
- **Saved Searches:** ~25-30 seconds (12 tests)
- **Empty State:** ~18-22 seconds (12 tests)
- **Error Handling:** ~30-35 seconds (15 tests)

**Total:** ~2-3 minutes for full suite (60 tests)

### Optimization
- Tests run sequentially (not parallel) for stability
- API mocking eliminates external dependencies
- Explicit waits prevent flakiness
- Shared page objects reduce duplication

## Test Data

### Mock Responses
All tests use mocked API responses for consistency:

- **Success:** 15 opportunities, R$ 750,000
- **Empty:** 0 opportunities, filter statistics
- **Error:** Network/API failure messages

### localStorage Test Data
Saved searches and theme preferences use controlled test data:
- Max 10 saved searches enforced
- Timestamps for relative date display
- Theme persistence verified across reloads

## Coverage

**Total Tests:** 60 E2E tests
**Critical Flows:** 5 major user journeys
**Browsers:** Desktop Chrome, Mobile Safari
**Assertions:** ~200+ assertions across all tests

## Maintenance

### When to Update Tests
- **New Features:** Add new test specs
- **UI Changes:** Update page objects
- **API Changes:** Update mock data in test-utils
- **Bug Fixes:** Add regression tests

### Test Health
- All tests should pass consistently
- Zero flaky tests (non-deterministic failures)
- Fast feedback (<5 minutes total)

## Troubleshooting

### Tests Timing Out
- Check if dev server is running (`npm run dev`)
- Increase timeout in test if needed
- Verify API mocks are set up correctly

### Flaky Tests
- Add explicit waits for animations
- Use `waitForLoadState('networkidle')`
- Check for race conditions

### Selector Not Found
- Update page objects if UI changed
- Use Playwright Inspector: `npx playwright test --debug`

## References

- **Playwright Docs:** https://playwright.dev
- **QA Analysis:** `docs/reviews/qa-testing-analysis.md`
- **Task Definition:** Task #2 (QA-7)
- **Config:** `frontend/playwright.config.ts`
