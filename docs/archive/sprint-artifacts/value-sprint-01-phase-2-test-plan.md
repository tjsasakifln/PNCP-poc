# Value Sprint 01 - Phase 2 Test Plan

**Date:** 2026-01-29
**Owner:** @qa (Quinn - Guardian)
**Phase:** 2 of 4 (Design & Implementation Wave 1)
**Related Issue:** [#95](https://github.com/tjsasakifln/PNCP-poc/issues/95)

---

## 📋 Executive Summary

This test plan covers comprehensive testing for Value Sprint 01 Phase 2 features:
- ✅ **Analytics Tracking** (COMPLETE)
- 🔄 **Saved Searches** (In Progress)
- 🔄 **Enhanced Loading Progress** (In Progress)
- ⏳ **Interactive Onboarding** (Pending)

**Test Objectives:**
1. Validate all acceptance criteria for Phase 2 features
2. Maintain backend coverage at 70%+ and achieve frontend coverage at 60%+
3. Ensure zero regression in existing functionality
4. Verify analytics tracking accuracy and completeness
5. Validate accessibility compliance (WCAG 2.1 AA)

---

## 🎯 Test Scope

### In Scope

#### Features to Test
1. **Analytics Tracking (Priority #0)**
   - Mixpanel initialization
   - All 8 event types tracking correctly
   - Event properties accuracy
   - Silent failure when token missing
   - No console errors

2. **Saved Searches & History (Feature #1)**
   - Save search with custom name
   - Load saved search (auto-fill form)
   - Delete saved search
   - Maximum 10 searches enforcement
   - localStorage persistence
   - Analytics integration
   - Mobile responsiveness

3. **Enhanced Loading Progress (Feature #2)**
   - 5-stage progress display
   - Progress bar animation (0-100%)
   - Dynamic stage messages
   - Estimated time accuracy
   - Loading abandoned event
   - Mobile responsiveness

4. **Regression Testing**
   - Existing search flow
   - Download functionality
   - Theme toggle
   - Error handling
   - Empty states
   - Region selector

#### Test Levels
- **Unit Tests:** Individual components and hooks
- **Integration Tests:** Component interactions, API routes
- **Visual Regression:** Loading states, saved searches UI
- **Accessibility Tests:** WCAG 2.1 AA compliance
- **Performance Tests:** Page load, animation smoothness

### Out of Scope (Deferred to Phase 3/4)
- E2E testing with real PNCP API (will use mocks)
- Load testing (deferred to performance sprint)
- Cross-browser testing beyond Chrome/Firefox (MVP focus)
- Interactive Onboarding tests (pending Phase 3 implementation)

---

## 🛠 Test Environment

### Tools & Frameworks

#### Frontend Testing
- **Test Framework:** Jest 29+ with Next.js support
- **Component Testing:** React Testing Library (@testing-library/react)
- **DOM Assertions:** @testing-library/jest-dom
- **User Interactions:** @testing-library/user-event
- **Coverage Tool:** Istanbul (via Jest --coverage)
- **Mocking:** jest.mock() for Mixpanel, localStorage

#### Backend Testing
- **Test Framework:** pytest 7+
- **Coverage Tool:** coverage.py
- **Mocking:** unittest.mock, pytest fixtures
- **HTTP Testing:** FastAPI TestClient

#### E2E Testing (Future)
- **Tool:** Playwright (recommended based on MCP availability)
- **Alternative:** Cypress (if Playwright unavailable)

### Test Environment Configuration

#### Development Environment
```bash
# Frontend
cd frontend
npm install
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # Coverage report

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest --cov         # Run with coverage
```

#### Environment Variables (Testing)
```env
# Frontend (.env.test.local)
NEXT_PUBLIC_MIXPANEL_TOKEN=test_token_12345
BACKEND_URL=http://localhost:8000

# Backend (.env.test)
OPENAI_API_KEY=test_key_mock
PNCP_API_URL=http://mock-pncp-api
```

### Test Data Management

#### Mock Data Sources
- **Mixpanel Mock:** Mock mixpanel-browser module
- **localStorage Mock:** jest.mock('localStorage')
- **PNCP API Mock:** Mock responses in `backend/tests/fixtures/pncp_responses.json`
- **Sample Searches:** Predefined saved search objects

---

## 📊 Coverage Targets

### Overall Coverage Goals

| Component | Current | Target | Strategy |
|-----------|---------|--------|----------|
| **Backend** | 96.69% | 70%+ ✅ | Maintain current high coverage |
| **Frontend** | ~10% | 60%+ | Add component tests for new features |
| **Analytics Module** | 0% | 80%+ | High priority - critical path |
| **Saved Searches** | 0% | 75%+ | Core feature testing |
| **Loading Progress** | 0% | 70%+ | Visual + logic testing |

### Coverage Breakdown by File

#### Frontend Critical Files
```
frontend/app/
├── components/
│   ├── AnalyticsProvider.tsx     → 80%+ (critical)
│   ├── LoadingProgress.tsx       → 70%+ (visual + logic)
│   └── [SavedSearches.tsx]       → 75%+ (pending implementation)
├── hooks/
│   ├── useAnalytics.ts           → 85%+ (critical)
│   └── [useSavedSearches.ts]     → 75%+ (pending)
└── page.tsx                       → 60%+ (integration)
```

#### Backend Critical Files
```
backend/
├── main.py                        → 90%+ (API routes)
├── filter.py                      → 95%+ (already high)
├── pncp_client.py                 → 95%+ (already high)
└── tests/                         → 100% (all tests pass)
```

### Quality Gates

**Build will FAIL if:**
- Backend coverage < 70%
- Frontend coverage < 60%
- Any test fails
- Linting errors present
- TypeScript errors exist

---

## 🧪 Test Strategy

### Test Pyramid Distribution

```
        /\
       /  \  E2E Tests (10%)
      /    \  - Critical user paths
     /------\  Integration Tests (30%)
    /        \ - Component interactions
   /          \ - API route tests
  /------------\ Unit Tests (60%)
 /              \ - Pure functions
/________________\ - Component logic
                   - Hook behavior
```

### Testing Approach by Feature

#### 1. Analytics Tracking

**Testing Philosophy:** Analytics must be invisible and reliable

**Test Types:**
- **Unit Tests:** `useAnalytics` hook logic
- **Integration Tests:** Event firing in real components
- **Isolation Tests:** Mixpanel SDK mocked to prevent external calls
- **Error Handling:** Graceful degradation when token missing

**Key Scenarios:**
- ✅ Mixpanel initializes on app load
- ✅ page_load event fires with correct properties
- ✅ page_exit event fires on beforeunload
- ✅ search_started fires with UF count, date range, search mode
- ✅ search_completed fires with timing, totals, filter ratio
- ✅ search_failed fires with error details
- ✅ download_started fires with download ID
- ✅ download_completed fires with file size, timing
- ✅ download_failed fires with error message
- ✅ No errors when NEXT_PUBLIC_MIXPANEL_TOKEN missing

#### 2. Saved Searches

**Testing Philosophy:** Data integrity and UX consistency

**Test Types:**
- **Unit Tests:** `useSavedSearches` hook (CRUD operations)
- **Component Tests:** `<SavedSearchesDropdown>` rendering and interactions
- **localStorage Tests:** Persistence across sessions
- **Validation Tests:** Max 10 searches, name validation

**Key Scenarios:**
- Save search with valid name → appears in list
- Load saved search → form auto-fills correctly
- Delete search → removed from list
- Max 10 enforcement → oldest removed when saving 11th
- localStorage persistence → survives page reload
- Analytics events → created, loaded, deleted fire
- Mobile UI → dropdown accessible on small screens
- Edge cases → empty names, special characters, duplicates

#### 3. Enhanced Loading Progress

**Testing Philosophy:** Perceived performance and user engagement

**Test Types:**
- **Component Tests:** `<LoadingProgress>` rendering
- **Animation Tests:** Progress bar 0→100% animation
- **Timing Tests:** Stage transitions at correct intervals
- **Content Tests:** Dynamic messages with state counts

**Key Scenarios:**
- All 5 stages display in correct order
- Progress bar animates from 0% to 95% (asymptotic)
- Stage 1 (Conectando) shows first 5 seconds
- Stage 2 (Consultando) shows state count dynamically
- Stage 3 (Filtrando) after fetch completes
- Stage 4 (Gerando) near completion
- Estimated time remaining updates every second
- Elapsed time formatted correctly (1min 23s)
- Curiosidades rotate every 5 seconds
- Mobile responsive layout

#### 4. Regression Testing

**Testing Philosophy:** Never break what works

**Test Approach:**
- Run existing test suite before and after changes
- Add new regression tests for bugs found
- Visual snapshot testing for UI changes

**Critical User Paths:**
1. **Search Flow:** UF selection → date range → buscar → results → download
2. **Error Handling:** Invalid dates → error message → retry
3. **Empty State:** No results → helpful message → adjust search
4. **Theme Toggle:** Light/dark mode persists
5. **Region Selector:** Select region → all UFs in region selected

---

## 📝 Test Case Organization

### Test Case Numbering Convention

```
TC-{FEATURE}-{CATEGORY}-{NUMBER}

Examples:
TC-ANALYTICS-INIT-001    → Analytics initialization test #1
TC-SAVED-CRUD-005        → Saved searches CRUD test #5
TC-LOADING-UI-012        → Loading progress UI test #12
TC-REGRESSION-SEARCH-001 → Regression test for search #1
```

### Test Case Template

Each test case follows this structure:

```markdown
#### TC-{ID}: {Title}

**Priority:** High/Medium/Low
**Type:** Unit/Integration/E2E
**Preconditions:** Setup required before test
**Test Steps:**
1. Action 1
2. Action 2
3. Expected result

**Expected Result:** What should happen
**Actual Result:** (to be filled during testing)
**Status:** ⏳ Pending | ✅ Pass | ❌ Fail | ⚠️ Blocked
**Notes:** Additional context
```

---

## 🔄 Test Execution Strategy

### Test Execution Phases

#### Phase 2A: Analytics Testing (Day 3-4)
**Status:** ✅ Analytics implemented, tests pending

**Execution:**
1. Create `frontend/__tests__/analytics.test.ts` (skeleton provided)
2. Run tests: `npm run test:coverage`
3. Verify 8 events fire correctly
4. Check error handling (missing token)
5. Sign off on analytics before continuing

**Exit Criteria:**
- ✅ All analytics tests pass
- ✅ Coverage for `useAnalytics.ts` ≥ 85%
- ✅ Coverage for `AnalyticsProvider.tsx` ≥ 80%
- ✅ No console errors in manual testing

#### Phase 2B: Saved Searches Testing (Day 5-6)
**Status:** 🔄 Implementation in progress

**Execution:**
1. Create `frontend/__tests__/savedSearches.test.ts` (skeleton provided)
2. Test localStorage CRUD operations
3. Test component rendering and interactions
4. Test analytics integration
5. Manual mobile testing
6. Accessibility audit (keyboard navigation)

**Exit Criteria:**
- ✅ All saved searches tests pass
- ✅ Coverage for `useSavedSearches.ts` ≥ 75%
- ✅ Max 10 searches enforced
- ✅ Mobile responsive verified
- ✅ Analytics events fire correctly

#### Phase 2C: Loading Progress Testing (Day 6-7)
**Status:** 🔄 Implementation in progress

**Execution:**
1. Test stage progression logic
2. Test progress bar animation (visual verification)
3. Test dynamic message updates
4. Test elapsed/remaining time formatting
5. Test curiosidades rotation
6. Mobile responsive testing

**Exit Criteria:**
- ✅ All loading tests pass
- ✅ Coverage for `LoadingProgress.tsx` ≥ 70%
- ✅ Stage transitions smooth (manual verification)
- ✅ No flicker or layout shift

#### Phase 2D: Regression Testing (Day 7)
**Status:** ⏳ Pending Phase 2A-C completion

**Execution:**
1. Run full test suite (backend + frontend)
2. Manual smoke testing of existing features
3. Cross-browser testing (Chrome, Firefox)
4. Accessibility audit (aXe DevTools)
5. Performance profiling (Lighthouse)

**Exit Criteria:**
- ✅ Zero regression failures
- ✅ All existing tests pass
- ✅ Lighthouse score ≥ 90
- ✅ WCAG 2.1 AA compliance

---

## 🐛 Defect Management

### Bug Severity Classification

| Severity | Definition | Response Time | Examples |
|----------|------------|---------------|----------|
| **Critical** | Blocks core functionality | Immediate fix | Search completely broken |
| **High** | Major feature broken | Fix within 24h | Analytics not tracking |
| **Medium** | Feature degraded | Fix within 48h | Loading bar flickers |
| **Low** | Cosmetic issue | Fix when time permits | Button alignment off by 2px |

### Bug Reporting Template

```markdown
**Bug ID:** BUG-{PHASE}-{NUMBER}
**Severity:** Critical/High/Medium/Low
**Component:** Analytics/Saved Searches/Loading/Regression
**Environment:** Dev/Staging/Production

**Description:** What is broken

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Observe error

**Expected Behavior:** What should happen
**Actual Behavior:** What actually happens
**Screenshots:** [Attach if applicable]

**Impact:** How many users affected / which workflows blocked

**Suggested Fix:** (if known)
**Assigned To:** @dev/@architect
**Status:** Open/In Progress/Fixed/Verified/Closed
```

### Bug Tracking Workflow

```
[Open] → [Triaged] → [Assigned] → [In Progress] → [Fixed] → [Verified] → [Closed]
   ↓         ↓            ↓             ↓             ↓           ↓
 @qa       @pm          @dev          @dev          @dev        @qa
```

---

## 📈 Test Metrics & Reporting

### Daily Test Metrics (Track in Spreadsheet)

| Metric | Formula | Target | Owner |
|--------|---------|--------|-------|
| **Test Pass Rate** | (Passed / Total) × 100 | ≥ 95% | @qa |
| **Code Coverage** | Lines covered / Total lines | ≥ 60% (FE), ≥ 70% (BE) | @qa |
| **Defect Detection Rate** | Bugs found / Test cases | Track trend | @qa |
| **Defect Fix Rate** | Bugs fixed / Bugs found | ≥ 90% by Phase end | @dev |
| **Test Execution Time** | Time to run full suite | < 5 min | @qa/@devops |

### Test Summary Report Template

```markdown
## Phase 2 Test Summary Report

**Date:** {Date}
**Prepared By:** @qa

### Test Execution Summary
- Total Test Cases: {X}
- Passed: {Y} ({Y/X}%)
- Failed: {Z} ({Z/X}%)
- Blocked: {W}

### Coverage Summary
- Backend: {X}% (Target: 70%+)
- Frontend: {Y}% (Target: 60%+)
- Analytics Module: {Z}%

### Defects Summary
| Severity | Open | Fixed | Total |
|----------|------|-------|-------|
| Critical | X | Y | Z |
| High | X | Y | Z |
| Medium | X | Y | Z |
| Low | X | Y | Z |

### Risk Assessment
- 🟢 **LOW RISK:** All critical/high bugs fixed
- 🟡 **MEDIUM RISK:** Some medium bugs remain
- 🔴 **HIGH RISK:** Critical/high bugs unresolved

### Recommendation
✅ **READY FOR PHASE 3** | ⚠️ **NEEDS WORK** | ❌ **NOT READY**

**Blockers:** {List any blocking issues}
**Next Steps:** {Actions required before Phase 3}
```

---

## ✅ Acceptance Criteria Checklist

### Analytics Tracking
- [ ] Mixpanel initializes successfully on page load
- [ ] `page_load` event fires with path, timestamp, environment, referrer
- [ ] `page_exit` event fires on beforeunload with session duration
- [ ] `search_started` event fires with UFs, date range, search mode
- [ ] `search_completed` event fires with timing, totals, filter ratio
- [ ] `search_failed` event fires with error message and type
- [ ] `download_started` event fires with download ID and totals
- [ ] `download_completed` event fires with file size and timing
- [ ] `download_failed` event fires with error details
- [ ] No errors when NEXT_PUBLIC_MIXPANEL_TOKEN is missing
- [ ] Analytics tests achieve ≥80% coverage
- [ ] Manual verification in Mixpanel dashboard (dev environment)

### Saved Searches (Pending Implementation)
- [ ] User can save search with custom name
- [ ] Saved search appears in dropdown immediately
- [ ] Loading saved search auto-fills all form fields (UFs, dates, sector/terms)
- [ ] User can delete saved search
- [ ] Maximum 10 searches enforced (oldest removed when saving 11th)
- [ ] Searches persist in localStorage across sessions
- [ ] `saved_search_created` event fires with search details
- [ ] `saved_search_loaded` event fires with search ID
- [ ] `saved_search_deleted` event fires with search ID
- [ ] Edge cases handled: empty name, duplicate name, special characters
- [ ] Mobile responsive: dropdown accessible on small screens
- [ ] Saved searches tests achieve ≥75% coverage

### Enhanced Loading Progress (Pending Implementation)
- [ ] All 5 stages display in correct order
- [ ] Progress bar animates smoothly from 0% to 95%
- [ ] Stage 1 "Conectando ao PNCP" shows first 5 seconds
- [ ] Stage 2 "Consultando X estado(s)" shows dynamic count
- [ ] Stage 3 "Filtrando e analisando" after fetching
- [ ] Stage 4 "Gerando relatório" near completion
- [ ] Elapsed time updates every second
- [ ] Estimated time remaining shows "~Xmin Ys restantes"
- [ ] Curiosidades rotate every 5 seconds
- [ ] Mobile responsive: all elements visible on small screens
- [ ] `loading_abandoned` event fires when user navigates away
- [ ] Loading progress tests achieve ≥70% coverage

### Regression Tests
- [ ] All existing backend tests pass (96.69% coverage maintained)
- [ ] All existing frontend tests pass
- [ ] Search flow works: UF selection → date range → buscar → results
- [ ] Download flow works: results → download button → Excel file
- [ ] Theme toggle works: light/dark mode persists
- [ ] Error handling works: invalid dates → error message
- [ ] Empty state works: no results → helpful message
- [ ] Region selector works: select region → all UFs selected
- [ ] No visual regressions (screenshot comparison)
- [ ] Lighthouse score ≥ 90 (performance, accessibility, best practices)

---

## 🔐 Security & Privacy Testing

### Analytics Privacy
- [ ] No PII (Personally Identifiable Information) sent to Mixpanel
- [ ] Search terms are sent (user consent assumed for product analytics)
- [ ] UF selections sent (aggregate data, not PII)
- [ ] No email, name, IP tracking (Mixpanel default disabled)

### localStorage Security
- [ ] No sensitive data stored in localStorage
- [ ] Saved searches contain only search criteria (public data)
- [ ] localStorage data does not exceed 5MB limit

---

## ♿ Accessibility Testing

### WCAG 2.1 AA Compliance Checklist

#### Perceivable
- [ ] All images have alt text
- [ ] Color contrast ratio ≥ 4.5:1 for text
- [ ] Color not sole indicator of state
- [ ] Text resizable to 200% without loss of function

#### Operable
- [ ] All functionality keyboard accessible
- [ ] No keyboard traps
- [ ] Skip navigation links present
- [ ] Focus indicators visible
- [ ] No time limits on interactions (or can be extended)

#### Understandable
- [ ] Language attribute set (lang="pt-BR")
- [ ] Error messages clear and actionable
- [ ] Labels present for all form inputs
- [ ] Consistent navigation

#### Robust
- [ ] Valid HTML5
- [ ] ARIA attributes used correctly
- [ ] Compatible with screen readers (NVDA, JAWS)

### Accessibility Testing Tools
- **Automated:** aXe DevTools browser extension
- **Manual:** Keyboard navigation testing
- **Screen Reader:** NVDA (Windows) or VoiceOver (Mac)

---

## 🚀 Performance Testing

### Performance Benchmarks

| Metric | Target | Tool |
|--------|--------|------|
| **First Contentful Paint (FCP)** | < 1.5s | Lighthouse |
| **Time to Interactive (TTI)** | < 3s | Lighthouse |
| **Total Blocking Time (TBT)** | < 300ms | Lighthouse |
| **Cumulative Layout Shift (CLS)** | < 0.1 | Lighthouse |
| **Test Suite Execution** | < 5 min | Jest/pytest |

### Performance Test Scenarios
- Page load with analytics initialization
- Saved searches dropdown rendering (10 items)
- Loading progress animation smoothness
- Large result set rendering (100+ items)

---

## 📚 Test Deliverables

### Documents
1. ✅ **This Test Plan** (`value-sprint-01-phase-2-test-plan.md`)
2. ✅ **Test Cases Document** (`value-sprint-01-phase-2-test-cases.md`)
3. ⏳ **Test Summary Report** (created after test execution)
4. ⏳ **Bug Reports** (created as needed)

### Code Artifacts
1. ✅ **Analytics Test Skeleton** (`frontend/__tests__/analytics.test.ts`)
2. ✅ **Saved Searches Test Skeleton** (`frontend/__tests__/savedSearches.test.ts`)
3. ⏳ **Loading Progress Tests** (to be created)
4. ⏳ **Regression Test Suite** (augmented)

### Test Data
1. ✅ **Mock Mixpanel Module** (in test files)
2. ✅ **Sample Saved Searches** (in test files)
3. ⏳ **PNCP Mock Responses** (backend/tests/fixtures/)

---

## 🤝 Roles & Responsibilities

| Role | Responsibility | Agent |
|------|----------------|-------|
| **Test Planning** | Create test plan and test cases | @qa |
| **Unit Testing** | Write component and hook tests | @dev + @qa |
| **Integration Testing** | Write API route and flow tests | @dev + @qa |
| **Manual Testing** | Exploratory testing, mobile testing | @qa |
| **Bug Triage** | Prioritize and assign bugs | @pm + @qa |
| **Bug Fixing** | Resolve defects | @dev |
| **Test Automation** | Set up CI/CD test execution | @devops |
| **Sign-Off** | Approve quality gate | @qa + @po |

---

## 🔄 Continuous Integration

### CI/CD Test Execution

**GitHub Actions Workflow (.github/workflows/test.yml):**

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov --cov-fail-under=70

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests with coverage
        run: |
          cd frontend
          npm run test:coverage
```

**Quality Gates:**
- Backend coverage < 70% → Build FAILS
- Frontend coverage < 60% → Build FAILS
- Any test fails → Build FAILS
- Linting errors → Build FAILS

---

## 📞 Communication Plan

### Daily Standup (15 min, 9:00 AM)
**Facilitator:** @sm

**Format:**
- @qa: Test progress update
- @dev: Implementation status
- @pm: Blockers and priorities

### Test Status Updates
**Frequency:** Daily (end of day)
**Channel:** GitHub Issue comments
**Format:** Brief summary + link to detailed report

**Template:**
```markdown
**Test Status Update - Day {X}**

✅ Completed Today:
- {Test area 1}
- {Test area 2}

🔄 In Progress:
- {Test area 3}

🐛 Bugs Found:
- BUG-P2-001 (High): {Description}

📊 Coverage:
- Backend: {X}%
- Frontend: {Y}%

⏭️ Tomorrow:
- {Planned test area}
```

---

## 🎓 Lessons Learned & Best Practices

### Testing Best Practices
1. **Write tests alongside code** - Don't defer testing to end
2. **Test behavior, not implementation** - Focus on what, not how
3. **Keep tests isolated** - No shared state between tests
4. **Mock external dependencies** - Mixpanel, PNCP API, localStorage
5. **Use descriptive test names** - Test should read like documentation
6. **Test edge cases** - Empty arrays, null values, max limits
7. **Visual verification** - Some things need human eyes (animations)

### Common Pitfalls to Avoid
- ❌ Testing implementation details (class names, internal state)
- ❌ Overmocking (makes tests brittle and meaningless)
- ❌ Not cleaning up after tests (localStorage, timers)
- ❌ Ignoring async behavior (use waitFor, findBy)
- ❌ Writing flaky tests (time-dependent, race conditions)

---

## 📖 References

### Documentation
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [pytest Documentation](https://docs.pytest.org/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Project Documentation
- `CLAUDE.md` - Project overview and testing requirements
- `PRD.md` - Product requirements
- `value-sprint-01.md` - Sprint overview
- `value-sprint-01-baseline-analysis.md` - Baseline metrics
- `value-sprint-01-ux-design-concepts.md` - UX designs

### Related Issues
- [#95 Phase 2: Design & Implementation Wave 1](https://github.com/tjsasakifln/PNCP-poc/issues/95)
- [#96 Phase 3: Implementation Wave 2 & Testing](https://github.com/tjsasakifln/PNCP-poc/issues/96)
- [#97 Phase 4: Polish, Deploy & Validation](https://github.com/tjsasakifln/PNCP-poc/issues/97)

---

**Test Plan Status:** ✅ APPROVED
**Next Step:** Execute Phase 2A (Analytics Testing)
**Owner:** @qa (Quinn - Guardian)
**Date:** 2026-01-29
