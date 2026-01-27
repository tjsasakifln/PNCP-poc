# BidIQ Development Acceleration Guide

**Status:** MVP v0.1 (Week 1)
**Framework:** Synkra AIOS v2.0
**Last Updated:** 2026-01-26

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Development Squads](#development-squads)
3. [Typical Workflows](#typical-workflows)
4. [Quality Standards](#quality-standards)
5. [Troubleshooting](#troubleshooting)
6. [Resources](#resources)

---

## Quick Start

### For Backend Development (FastAPI)

**Start development in 3 commands:**
```bash
# 1. Activate backend squad
/bidiq backend

# 2. In squad, create or select story
*create-story
  Title: "Add PNCP pagination support"
  Acceptance Criteria: "Users can paginate through >500 results"

# 3. Start implementation
*develop
  → Implement in pncp_client.py
  → Add tests for pagination
  → Validate coverage ≥70%
```

**What you get:**
- 4 agents: architect, dev, data-engineer, qa
- Automatic quality gate checking
- Test coverage validation
- Ready to deploy

---

### For Frontend Development (React/Next.js)

**Start development in 3 commands:**
```bash
# 1. Activate frontend squad
/bidiq frontend

# 2. Start implementation
*develop
  → Create UF selector component
  → Add date range picker
  → Style with Tailwind CSS

# 3. Run tests
*run-tests
  → Jest unit tests
  → Integration tests
  → Validate coverage ≥60%
```

**What you get:**
- 3 agents: ux-design-expert, dev, qa
- UI/UX design review
- Component best practices
- Test coverage validation

---

### For Complete Features (Backend + Frontend)

**Build end-to-end features in one squad:**
```bash
# 1. Activate complete feature squad
/bidiq feature

# 2. Create story with acceptance criteria
*create-story
  Title: "Add AI-powered bid analysis"
  Acceptance Criteria:
    - Backend: Generate summaries via GPT-4.1-nano
    - Frontend: Display summaries with bid cards
    - Both: Validate quality gates

# 3. Implementation phase
*develop backend    → Implement LLM integration
*develop frontend   → Display AI summaries

# 4. Testing phase
*run-tests          → Backend: ≥70% coverage
                    → Frontend: ≥60% coverage

# 5. Deployment
*create-pr          → Automated code review
                    → Auto-merge if checks pass
                    → Deploy to production
```

**What you get:**
- 5 agents: pm, architect, dev, qa, devops
- Story-driven development
- Architectural review
- Full quality gates
- Automated deployment

---

## Development Squads

### 1. Team BidIQ Backend

**When to use:** Building backend features, API changes, database work

**Agents:**
- `@architect` - API design and system architecture
- `@dev` - FastAPI implementation
- `@data-engineer` - Database and query optimization
- `@qa` - Testing and coverage validation

**Key modules:**
- `pncp_client.py` - PNCP API integration with resilience
- `filter.py` - Keyword-based procurement filtering
- `excel.py` - Excel report generation
- `llm.py` - GPT-4.1-nano integration
- `schemas.py` - Pydantic validation models

**Example workflow:**

```bash
# Step 1: Activate squad
/bidiq backend

# Step 2: Ask architect to review design
@architect: "Design rate limiting improvements for PNCP client"
→ Review current circuit breaker pattern
→ Propose enhancements

# Step 3: Implement
@dev: "*develop"
→ Modify pncp_client.py with new rate limiting
→ Write tests for edge cases

# Step 4: Test
@qa: "*run-tests"
→ pytest --cov --cov-report=html
→ Validate 70% coverage threshold
→ ✅ 96.69% coverage achieved

# Step 5: Deploy
Create PR → Auto-merge → Deploy to main
```

**Quality gates:**
- Coverage: ≥70% (currently 96.69%)
- Type checking: mypy passing
- Tests: 82+ tests all passing

---

### 2. Team BidIQ Frontend

**When to use:** Building frontend features, UI components, user interactions

**Agents:**
- `@ux-design-expert` - UI/UX design and accessibility
- `@dev` - React/TypeScript implementation
- `@qa` - Testing and validation

**Key modules:**
- `app/page.tsx` - Main SPA with UF selector
- `app/api/buscar/route.ts` - Backend proxy endpoint
- `app/api/download/route.ts` - Excel download handler
- Components directory - Reusable React components
- Styles - Tailwind CSS configuration

**Example workflow:**

```bash
# Step 1: Activate squad
/bidiq frontend

# Step 2: Design UI
@ux-design-expert: "Design new filtering interface"
→ Create wireframes
→ Review accessibility (WCAG)
→ Design tokens and colors

# Step 3: Implement
@dev: "*develop"
→ Create React components
→ TypeScript type definitions
→ Tailwind CSS styling
→ API integration

# Step 4: Test
@qa: "*run-tests"
→ npm test --coverage
→ Component tests
→ Integration tests
→ Validate 60% coverage threshold

# Step 5: Deploy
Create PR → Code review → Auto-merge → Deploy
```

**Quality gates:**
- Coverage: ≥60%
- Linting: 0 errors (npm run lint)
- Type checking: 0 errors (npm run typecheck)
- Build: Successful (npm run build)

---

### 3. Team BidIQ Feature Complete

**When to use:** Building complete features requiring backend + frontend + coordination

**Agents:**
- `@pm` - Story creation and project management
- `@architect` - Architecture review and impact analysis
- `@dev` - Full-stack implementation
- `@qa` - Testing and quality validation
- `@devops` - PR automation and deployment

**Example workflow:**

```bash
# Step 1: Activate squad
/bidiq feature

# Step 2: Create story
@pm: "*create-story"
Title: "Add advanced PNCP filtering"
Acceptance Criteria:
  - Backend: Filter by UF, date, keyword, value range
  - Frontend: Multi-select UF, date picker, keyword input
  - Both: <2s response time, ≥70%/≥60% coverage

# Step 3: Architecture review
@architect: "*analyze-impact"
→ Impact on pncp_client.py
→ Frontend state management changes
→ Database query optimization
→ Performance implications

# Step 4: Backend implementation
@dev: "*develop backend"
→ Implement filters in filter.py
→ Add database indexes
→ Write tests

# Step 5: Frontend implementation
@dev: "*develop frontend"
→ Build UF selector component
→ Date range picker
→ API integration
→ Styling with Tailwind

# Step 6: Complete testing
@qa: "*run-tests"
→ Backend: pytest --cov (≥70%)
→ Frontend: npm test --coverage (≥60%)
→ Integration tests
→ Acceptance criteria validation

# Step 7: Deploy
@devops: "*create-pr"
→ PR created with full context
→ Automated code review
→ CI/CD pipeline runs
→ Auto-merge if checks pass
→ Deploy to production
```

**Timeline:** 5-6 days per complete feature
- Story & planning: 0.5 days
- Architecture review: 1 day
- Implementation: 2-3 days
- Testing: 1 day
- Deployment: 0.5 days

---

## Typical Workflows

### Workflow 1: Quick Bugfix (2-4 hours)

```bash
# Scenario: Production bug in PNCP client timeout

# 1. Activate backend squad
/bidiq backend

# 2. Create bugfix branch and story
*create-story
  Type: Bug Fix
  Title: "PNCP client timeout on large queries"
  Issue: #42
  Priority: CRITICAL

# 3. Implement fix
@dev: "*develop"
  → Increase timeout in pncp_client.py:127
  → Add test case for large queries
  → Verify fix resolves issue

# 4. Validate coverage
@qa: "*run-tests"
  → All tests passing (84 passed)
  → Coverage: 96.69% (≥70% ✅)

# 5. Deploy hotfix
@devops: Create PR → Auto-merge → Deploy
```

**Output:**
```
✅ Bugfix complete in 2h 15m
- Branch: fix/issue-42-pncp-timeout
- Tests: 84 passed, 96.69% coverage
- Deploy: Production v0.2.1
```

---

### Workflow 2: Backend Feature (3-4 days)

```bash
# Scenario: Add PNCP pagination for >500 result sets

# 1. Activate backend squad
/bidiq backend

# 2. Architecture review
@architect: "Design pagination strategy"
  → Review current pagination approach (PNCP API max 500/page)
  → Design frontend/backend contract
  → Propose caching strategy

# 3. Implementation
@dev: "*develop"
  → Modify pncp_client.py for pagination
  → Add limit/offset parameters to API
  → Implement page cache (5min TTL)
  → Write integration tests

# 4. Database optimization
@data-engineer: "Review query performance"
  → Add database indexes if needed
  → Review query execution plans
  → Recommend caching strategy

# 5. Testing
@qa: "*run-tests"
  → New tests: pagination, edge cases
  → Coverage: 96.69% (≥70% ✅)
  → Performance: <2s response ✅

# 6. Deploy
Create PR → Code review → Auto-merge → Production
```

**Output:**
```
✅ Feature complete in 3d 6h
- Backend: 8 new tests, 96.69% coverage
- Performance: <2s response (target met)
- Deploy: Production v0.2.1
- Story: Story 2.4 marked complete
```

---

### Workflow 3: Frontend Feature (2-3 days)

```bash
# Scenario: Improve UF selector UI/UX

# 1. Activate frontend squad
/bidiq frontend

# 2. Design new interface
@ux-design-expert: "Design UF selector improvements"
  → Wireframes for improved multi-select
  → Accessibility review (WCAG)
  → Color and spacing tokens

# 3. Implementation
@dev: "*develop"
  → Create improved UF selector component
  → Add search/filter for UF list
  → Tailwind CSS styling
  → Keyboard navigation

# 4. Testing
@qa: "*run-tests"
  → Component tests: selector behavior
  → Integration tests: search flow
  → Accessibility tests: keyboard, screen reader
  → Coverage: ≥60% ✅

# 5. Deploy
Create PR → Code review → Auto-merge → Production
```

**Output:**
```
✅ Feature complete in 2d 8h
- Frontend: UF selector improved
- Coverage: 62% (≥60% ✅)
- Accessibility: WCAG AA compliant ✅
- Deploy: Production v0.2.1
```

---

### Workflow 4: Complete Feature (5-6 days)

```bash
# Scenario: Full AI-powered bid analysis feature

# 1. Activate complete feature squad
/bidiq feature

# 2. Create story with all acceptance criteria
@pm: "*create-story"
  Story 3.5: "AI-Powered Bid Analysis"

  Acceptance Criteria:
    Backend:
      - Generate GPT-4.1-nano summaries
      - Store summaries in cache (5min TTL)
      - Return summary with bid data

    Frontend:
      - Display AI summary in bid card
      - Show summary loading state
      - Format summary with highlights

    Quality:
      - Backend: ≥70% coverage
      - Frontend: ≥60% coverage
      - Response time: <3s
      - Summary tokens: <500

# 3. Architecture review
@architect: "*analyze-impact"
  → Impact on llm.py
  → Cache architecture
  → Frontend state management
  → Token usage implications

# 4. Backend implementation
@dev: "*develop backend"
  → Enhance llm.py for batch processing
  → Add caching strategy
  → Implement fallback without LLM
  → Write comprehensive tests

# 5. Frontend implementation
@dev: "*develop frontend"
  → Create SummaryCard component
  → Add loading skeleton
  → Integration with /api/buscar
  → Styling and animations

# 6. Complete testing
@qa: "*run-tests"
  → Backend: pytest --cov (96.69% ✅)
  → Frontend: npm test --coverage (≥60% ✅)
  → Integration tests: E2E flow
  → Performance validation: <3s ✅

# 7. Deployment
@devops: "*create-pr"
  → PR created with full context
  → Automated code review
  → CI/CD: All checks PASS
  → Auto-merge
  → Deploy to production

# 8. Post-deployment
  → Monitor summary quality
  → Track token usage
  → Validate performance SLO
```

**Output:**
```
✅ Feature complete in 5d 6h
- Backend: AI integration with 96.69% coverage
- Frontend: Summary display with 62% coverage
- Quality: All acceptance criteria met ✅
- Performance: <3s response time ✅
- Deploy: Production v0.3.0
- Story: Story 3.5 marked complete
```

---

## Quality Standards

### Backend (Python/FastAPI)

**Coverage Target:** ≥70%
```bash
cd backend
pytest --cov --cov-report=html
# Current: 96.69% (82 tests)
```

**Type Checking:**
```bash
mypy .
# 0 errors required
```

**Code Quality:**
```bash
ruff check .
# 0 high-severity issues
```

**Testing Pattern:**
```python
def test_pncp_client_retry_logic():
    """Test exponential backoff retry mechanism."""
    # Arrange
    client = PNCPClient()

    # Act
    result = await client.fetch_all(ufs=['SP'])

    # Assert
    assert result.total_registros > 0
    assert all(bid['uf'] == 'SP' for bid in result.data)
```

---

### Frontend (TypeScript/React)

**Coverage Target:** ≥60%
```bash
cd frontend
npm test --coverage
# Threshold: 60.0%
```

**Linting:**
```bash
npm run lint
# 0 errors required
```

**Type Checking:**
```bash
npm run typecheck
# 0 type errors required (strict mode)
```

**Testing Pattern:**
```typescript
describe('UF Selector', () => {
  test('should select multiple UFs', async () => {
    // Arrange
    const { getByRole } = render(<UFSelector />);

    // Act
    fireEvent.click(getByRole('button', { name: /SP/i }));

    // Assert
    expect(getByRole('button', { name: /SP/i })).toHaveClass('selected');
  });
});
```

---

### Quality Gate Timeline

| Stage | Checks | Enforcer |
|-------|--------|----------|
| Pre-commit | mypy, ruff (backend) / lint, typecheck (frontend) | Developer |
| Pre-PR | pytest --cov (≥70%), npm test --coverage (≥60%) | CI/CD |
| Pre-merge | All checks + code review approval | @devops |
| Pre-deploy | Smoke tests + security scan | @devops |

---

## Troubleshooting

### Tests Failing?

**Backend (pytest):**
```bash
# Run with verbose output
pytest -v

# Run specific test
pytest -k "test_pncp_client_retry"

# Generate HTML coverage report
pytest --cov --cov-report=html
# View: backend/htmlcov/index.html
```

**Frontend (jest):**
```bash
# Run with verbose output
npm test -- --verbose

# Run specific test
npm test -- --testNamePattern="UF Selector"

# Generate coverage report
npm test -- --coverage
# View: frontend/coverage/
```

---

### Coverage Below Threshold?

**Backend (<70%):**
```bash
# 1. Check current coverage
pytest --cov

# 2. Identify uncovered lines
pytest --cov-report=html
open backend/htmlcov/index.html

# 3. Write tests for gaps
# Add test case for missing branch

# 4. Verify coverage
pytest --cov
```

**Frontend (<60%):**
```bash
# 1. Check coverage
npm test -- --coverage

# 2. View uncovered code
open frontend/coverage/lcov-report/index.html

# 3. Write tests
npm test -- --watch

# 4. Verify
npm test -- --coverage
```

---

### Squad Not Activating?

**Check prerequisites:**
```bash
# 1. Verify squad file exists
ls .aios-core/development/agent-teams/team-bidiq-*.yaml

# 2. Check YAML syntax
cat .aios-core/development/agent-teams/team-bidiq-backend.yaml

# 3. Try manual squad activation
/squad-creator
→ "Load existing squad"
→ "team-bidiq-backend"
```

---

### Performance Issues?

**Backend optimization:**
```bash
# Profile PNCP API calls
cd backend
PNCP_DEBUG=true uvicorn main:app --reload

# Check database query performance
# Use database profiling tools
```

**Frontend optimization:**
```bash
# Check bundle size
npm run build
# View: frontend/.next/

# Use React DevTools Profiler
# Check component render performance
```

---

## Resources

### Documentation Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project conventions and standards |
| `PRD.md` | Complete technical specification |
| `docs/stories/story-*.md` | Development stories and tasks |
| `.env.example` | Environment variable reference |

### Important Directories

| Directory | Purpose |
|-----------|---------|
| `backend/` | FastAPI application |
| `frontend/` | Next.js React application |
| `docs/` | Documentation and guides |
| `.aios-core/development/` | AIOS framework resources |
| `.claude/commands/` | Command definitions |

### Key Commands

| Command | Purpose |
|---------|---------|
| `/bidiq backend` | Activate backend squad |
| `/bidiq frontend` | Activate frontend squad |
| `/bidiq feature` | Activate complete feature squad |
| `/bidiq status` | Project status (coming Week 2) |
| `/bidiq help` | Command reference (coming Week 2) |

### Quick Links

- **Backend specs:** See `backend/pncp_client.py` and `backend/filter.py`
- **Frontend specs:** See `frontend/app/page.tsx`
- **Testing:** Run `cd backend && pytest` or `cd frontend && npm test`
- **Deployment:** See `ROADMAP.md` Issue #31

---

## Common Questions

### Q: How do I start a new feature?
**A:** Use `/bidiq feature` then `*create-story` to define acceptance criteria.

### Q: What coverage do I need?
**A:** Backend ≥70% (currently 96.69%), Frontend ≥60%

### Q: How do I run tests?
**A:** `pytest --cov` (backend) or `npm test --coverage` (frontend)

### Q: Who do I ask for help?
**A:** Activate appropriate squad: `/bidiq backend`, `/bidiq frontend`, or `/bidiq feature`

### Q: Can I deploy without tests?
**A:** No, quality gates require ≥70% coverage (backend) and all tests passing.

---

**For more help:**
- Type `/bidiq help` for command reference
- Review `CLAUDE.md` for project standards
- Check `PRD.md` for technical details
- Ask @dev, @qa, or @architect in appropriate squad

---

**Version:** 1.0 (MVP)
**Framework:** Synkra AIOS v2.0
**Status:** ✅ Ready for use
