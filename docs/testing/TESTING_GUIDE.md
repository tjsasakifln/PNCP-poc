# Testing Guide - BidIQ Uniformes

## Overview

This guide covers testing strategies, best practices, and CI/CD integration for the BidIQ Uniformes project.

## Test Categories

### 1. Unit Tests
Test individual functions and components in isolation.

**Backend (Python/pytest):**
- Location: `backend/tests/`
- Run: `cd backend && pytest`
- Coverage: `pytest --cov --cov-report=html`
- Threshold: 70% minimum

**Frontend (TypeScript/Jest):**
- Location: `frontend/__tests__/`
- Run: `cd frontend && npm test`
- Coverage: `npm test -- --coverage`
- Threshold: 60% minimum

### 2. Integration Tests
Test interactions between modules with some real components.

**Backend Integration Tests:**
```bash
cd backend
pytest -m integration
```

**Marked with:** `@pytest.mark.integration`

**Current Integration Tests:**
- `test_pncp_integration.py` - PNCP client API structure validation
- `test_main.py::TestBuscarIntegration` - Full search flow with real filter/Excel

### 3. End-to-End (E2E) Tests
Test complete user workflows in a real browser.

**Frontend E2E (Playwright):**
```bash
cd frontend
npm run test:e2e          # Headless mode
npm run test:e2e:headed   # See browser
npm run test:e2e:ui       # Interactive UI mode
npm run test:e2e:debug    # Step through tests
```

**Test Coverage:**
- Search flow (UF selection → Results → Download)
- Theme switching and persistence
- Saved searches functionality
- Empty state handling
- Error handling and timeouts

## Running Tests Locally

### Backend Tests

```bash
cd backend

# All tests
pytest

# With coverage report
pytest --cov --cov-report=html
# Open: backend/htmlcov/index.html

# Specific test file
pytest tests/test_pncp_client.py

# Specific test
pytest tests/test_filter.py::test_keyword_matching

# Verbose output
pytest -v

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

### Frontend Tests

```bash
cd frontend

# All tests
npm test

# Watch mode (interactive)
npm run test:watch

# Coverage report
npm run test:coverage
# Open: frontend/coverage/lcov-report/index.html

# CI mode (non-interactive)
npm run test:ci

# Update snapshots
npm test -- -u

# Specific test file
npm test -- LoadingProgress.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"
```

### E2E Tests

```bash
cd frontend

# Run all E2E tests (starts dev server automatically)
npm run test:e2e

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug specific test
npm run test:e2e:debug -- search-flow.spec.ts

# Interactive UI mode
npm run test:e2e:ui

# View last test report
npm run test:e2e:report
```

## CI/CD Integration

### GitHub Actions Workflows

#### 1. Backend CI (`.github/workflows/backend-ci.yml`)
**Triggers:** PR/Push affecting backend files

**Steps:**
1. Checkout code
2. Set up Python 3.12
3. Install dependencies
4. Run linting (`ruff check`)
5. **Run security vulnerability scan (Safety)**
6. Run tests with coverage (70% threshold)
7. Upload coverage to Codecov

**Security Scanning:**
```yaml
- name: Run security vulnerability scan
  run: |
    cd backend
    pip install safety
    safety check --json || echo "⚠️ Vulnerabilities found"
```

#### 2. Frontend Tests (`.github/workflows/tests.yml`)
**Triggers:** PR/Push to main/master

**Steps:**
1. Checkout code (with cache enabled)
2. Set up Node.js 20 with npm cache
3. Install dependencies
4. **Run npm audit for vulnerabilities**
5. Clear caches (Jest, node_modules/.cache)
6. Run tests with coverage (60% threshold)
7. Publish test results
8. Upload coverage to Codecov

**Security Scanning:**
```yaml
- name: Run security vulnerability audit
  run: |
    cd frontend
    npm audit --audit-level=moderate --json > audit-report.json
    npm audit || true
```

**Cache Management:**
```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json
```

#### 3. E2E Tests (`.github/workflows/tests.yml`)
**Triggers:** After backend and frontend tests pass

**Steps:**
1. Start backend server (uvicorn)
2. Build and start frontend (Next.js)
3. Run Playwright E2E tests
4. Upload test reports and logs
5. Comment PR with results

**Browser Configuration:**
- Chromium (Desktop Chrome)
- WebKit (Mobile Safari)

## Security Vulnerability Scanning

### Backend (Python - Safety)

**Tool:** [Safety](https://pyup.io/safety/)

**Local Scan:**
```bash
cd backend
pip install safety
safety check
```

**CI Integration:** Runs on every PR/push to backend files

**False Positives:** Can be suppressed with `.safety-policy.yml`

### Frontend (JavaScript - npm audit)

**Tool:** npm audit (built-in)

**Local Scan:**
```bash
cd frontend
npm audit
npm audit --audit-level=moderate
npm audit fix  # Auto-fix if possible
```

**CI Integration:** Runs on every PR/push

**Severity Levels:**
- `critical` - Must fix immediately
- `high` - Fix in next sprint
- `moderate` - Review and plan fix
- `low` - Informational

## Coverage Thresholds

### Backend (70% minimum)
```ini
# backend/pyproject.toml
[tool.coverage.report]
fail_under = 70.0
show_missing = true
```

**Enforcement:**
- Pytest fails if coverage < 70%
- CI workflow enforces threshold
- HTML reports show uncovered lines

### Frontend (60% minimum)
```javascript
// frontend/jest.config.js
coverageThreshold: {
  global: {
    branches: 60,
    functions: 60,
    lines: 60,
    statements: 60,
  },
}
```

**Enforcement:**
- Jest exits with code 1 if coverage < 60%
- CI workflow fails build automatically
- No manual checks needed

## Test Timing Issues (Fixed)

### Problem
Tests using fake timers had cleanup issues causing warnings.

### Solution
Proper timer cleanup in `beforeEach`/`afterEach`:

```typescript
beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.clearAllTimers();  // Clear before switching
  jest.useRealTimers();
});
```

**Wrap timer advances in `act()`:**
```typescript
act(() => {
  jest.advanceTimersByTime(5000);
});
```

**Files Fixed:**
- `frontend/__tests__/components/LoadingProgress.test.tsx`
- `frontend/__tests__/EnhancedLoadingProgress.test.tsx`

## Integration Test Strategy

### Mocked vs. Real API

**Decision:** Use mocked PNCP API responses for reliability

**Rationale:**
- Avoid rate limiting (PNCP API is unstable)
- Consistent test results
- Fast execution
- No network dependencies

**Implementation:**
```python
from unittest.mock import Mock, patch

mock_response = Mock()
mock_response.status_code = 200
mock_response.json.return_value = {
    "data": [...],
    "totalRegistros": 1,
}

with patch("httpx.Client.get", return_value=mock_response):
    # Test code
```

## CI Cache Strategy

### Problem
GitHub Actions cache was disabled, causing slow builds.

### Solution
Re-enabled npm cache with proper keys:

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json
```

**Cache Keys:**
- `node-modules-${{ hashFiles('**/package-lock.json') }}`
- Auto-invalidates when dependencies change

## Best Practices

### 1. Test Naming
```python
# Backend
def test_keyword_matching_with_unicode():
    """Test that filter handles accented characters correctly."""
```

```typescript
// Frontend
it('should handle state count of 0', () => {
  // Test edge case
});
```

### 2. Test Organization
```
backend/tests/
├── test_pncp_client.py      # 32 tests - HTTP client
├── test_filter.py            # 48 tests - Filtering logic
├── test_excel.py             # Pending (#13)
├── test_llm.py               # Pending (#14)
├── test_main.py              # 85+ tests - API endpoints
└── test_pncp_integration.py  # 2 integration tests

frontend/__tests__/
├── components/
│   ├── LoadingProgress.test.tsx      # 45 tests
│   └── EnhancedLoadingProgress.test.tsx  # 24 tests
└── hooks/
    └── useSavedSearches.test.tsx
```

### 3. Mocking Strategy
```typescript
// Mock external dependencies
jest.mock('../../hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackEvent: jest.fn(),
  }),
}));
```

```python
# Mock PNCP API
monkeypatch.setattr("main.PNCPClient", lambda: mock_client)
```

### 4. Async Testing
```typescript
// Frontend - use waitFor for async state changes
await waitFor(() => {
  expect(screen.getByText(/Conectando/)).toBeInTheDocument();
});
```

```python
# Backend - use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_call()
    assert result == expected
```

## Debugging Failed Tests

### CI Failures

**Backend:**
```bash
# Download logs from GitHub Actions
gh run view <run-id> --log

# Reproduce locally
cd backend
pytest tests/test_name.py -v
```

**Frontend:**
```bash
# Check test report artifact
gh run view <run-id> --log

# Run in watch mode
cd frontend
npm run test:watch -- LoadingProgress
```

**E2E Failures:**
```bash
# Download Playwright report artifact
gh run download <run-id> -n playwright-report

# Debug locally
cd frontend
npm run test:e2e:debug -- search-flow.spec.ts
```

### Common Issues

**1. Timer-related warnings:**
- Ensure `jest.clearAllTimers()` in `afterEach`
- Wrap `jest.advanceTimersByTime()` in `act()`

**2. Flaky E2E tests:**
- Increase timeout in `playwright.config.ts`
- Add explicit `waitFor` conditions
- Check for race conditions

**3. Coverage drops:**
- Add tests for new features
- Remove dead code
- Check coverage report for uncovered lines

## Continuous Improvement

### Weekly Review
- Monitor test execution time
- Review flaky tests
- Update snapshots as needed
- Address TODO comments

### Quarterly Audit
- Update testing libraries
- Review mocking strategy
- Optimize slow tests
- Improve coverage gaps

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library](https://testing-library.com/)
- [Python Safety](https://pyup.io/safety/)
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)

## Issues Resolved

- ✅ #125 - Integration tests unskipped and fixed (mocked API)
- ✅ #127 - Vulnerability scanning added (Safety + npm audit)
- ✅ #131 - GitHub Actions cache re-enabled
- ✅ #132 - LoadingProgress timing tests fixed (proper cleanup)

---

**Last Updated:** 2026-01-31
**Team:** Squad 4 (QA + DevOps)
