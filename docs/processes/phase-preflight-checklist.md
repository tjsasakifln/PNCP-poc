# Phase Pre-Flight Checklist

**Purpose:** Validate dependencies, libraries, base components, and environment configuration before starting a multi-day phase.

**Owner:** @sm (Scrum Master)
**When to Run:** Day 1 of every multi-day phase (Day 8, Day 11, etc.)
**Estimated Time:** 10-15 minutes

---

## 📋 Checklist Instructions

1. **Run this checklist at the START of every multi-day phase** (before first standup)
2. **Check each item** - mark [x] when validated
3. **Log any failures as impediments** immediately in the impediment log
4. **Escalate P0/P1 failures** to @pm and @aios-master
5. **Update this checklist** if new dependencies are added to the project

---

## ✅ Pre-Flight Checklist

### 1. Dependencies Validation

#### Required Components Exist
- [ ] All base components referenced in story exist
  - Check: `frontend/components/` for expected files
  - Example: If story mentions `LoadingProgress.tsx`, verify it exists
  - **If missing:** Create GitHub issue, assign to @dev, priority P1

#### Required Hooks Exist
- [ ] All custom hooks referenced in story exist
  - Check: `frontend/hooks/` for expected files
  - Example: If story mentions `useOnboarding.tsx`, verify it exists
  - **If missing:** Create GitHub issue, assign to @dev, priority P1

#### Required Backend Modules Exist
- [ ] All backend modules referenced in story exist
  - Check: `backend/` for expected files
  - Example: If story mentions `llm.py`, verify it exists
  - **If missing:** Create GitHub issue, assign to @dev, priority P1

#### Required Test Files Exist
- [ ] Test file structure matches implementation files
  - Check: `frontend/__tests__/` and `backend/tests/`
  - Example: If `EnhancedLoadingProgress.tsx` exists, verify `EnhancedLoadingProgress.test.tsx` exists
  - **If missing:** Create skeleton test files, assign to @qa

---

### 2. Libraries & Packages

#### Frontend Dependencies Installed
- [ ] All `package.json` dependencies installed
  - Run: `cd frontend && npm ci`
  - Check: No errors, `node_modules/` populated
  - **If failed:** Run `npm install`, check package-lock.json for conflicts

#### Backend Dependencies Installed
- [ ] All `requirements.txt` dependencies installed
  - Run: `cd backend && source venv/bin/activate && pip install -r requirements.txt`
  - Check: No errors, virtual environment active
  - **If failed:** Check Python version (3.11+), recreate venv if needed

#### Architecture Decision Libraries
- [ ] Libraries mentioned in ADRs are installed
  - Check: Review recent ADR files in `docs/decisions/`
  - Example: ADR-003 mentions Shepherd.js → verify `npm list shepherd.js` succeeds
  - **If missing:** Run `npm install [library]` or `pip install [library]`

#### Verify Library Versions
- [ ] Library versions match ADR specifications
  - Check: `package.json` and `requirements.txt` version numbers
  - Example: ADR-003 specifies Shepherd.js 14.4.0 → verify `"shepherd.js": "^14.4.0"`
  - **If mismatch:** Update to correct version or update ADR

---

### 3. Environment Configuration

#### Frontend Environment Variables
- [ ] `.env.local` file exists (frontend)
  - Check: `frontend/.env.local` exists
  - **If missing:** Copy from `.env.example`, fill in required values

- [ ] Required environment variables set
  - Check: `NEXT_PUBLIC_MIXPANEL_TOKEN` (if analytics enabled)
  - Check: `NEXT_PUBLIC_BACKEND_URL` (API endpoint)
  - **If missing:** Add to `.env.local`, coordinate with team for values

#### Backend Environment Variables
- [ ] `.env` file exists (backend)
  - Check: `backend/.env` exists
  - **If missing:** Copy from `.env.example`, fill in required values

- [ ] Required environment variables set
  - Check: `OPENAI_API_KEY` (if LLM features enabled)
  - Check: `PNCP_TIMEOUT` (optional, default 30s)
  - **If missing:** Add to `.env`, coordinate with team for API keys

#### Secrets & API Keys
- [ ] All API keys are valid and not expired
  - Test: Run a simple API call to verify authentication
  - Example: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`
  - **If invalid:** Regenerate keys, update `.env`, update team docs

---

### 4. Base Infrastructure

#### Database (if applicable)
- [ ] Database schema up to date
  - Check: Run `npm run db:migrate` or equivalent
  - Verify: No pending migrations
  - **If failed:** Review migration files, coordinate with @data-engineer

#### CI/CD Pipelines
- [ ] Staging deployment workflow exists
  - Check: `.github/workflows/staging-deploy.yml`
  - **If missing:** Assign to @devops, priority P1

- [ ] Production deployment workflow exists
  - Check: `.github/workflows/production-deploy.yml`
  - **If missing:** Assign to @devops, priority P2 (not needed until Phase 4)

#### Test Infrastructure
- [ ] Frontend test suite runs successfully
  - Run: `cd frontend && npm test`
  - Check: 0 syntax errors (tests may fail, but suite must run)
  - **If failed:** Fix test configuration, coordinate with @qa

- [ ] Backend test suite runs successfully
  - Run: `cd backend && pytest`
  - Check: 0 import errors (tests may fail, but suite must run)
  - **If failed:** Fix test configuration, coordinate with @qa

---

### 5. Documentation

#### Story Documentation
- [ ] Story file exists and is complete
  - Check: `docs/stories/STORY-XXX-*.md` exists
  - Verify: Story has clear acceptance criteria, file list, agent assignments
  - **If incomplete:** Coordinate with @pm or @po to complete story

#### ADR for Architecture Decisions
- [ ] ADRs exist for all major technology choices in this phase
  - Check: `docs/decisions/` for recent ADRs
  - Example: If using new library, verify ADR explaining choice
  - **If missing:** Assign to @architect, priority P1 (before implementation)

#### Test Plan
- [ ] Test plan exists for this phase
  - Check: `docs/testing/phase-X-test-plan.md` (if multi-day phase)
  - **If missing:** Assign to @qa, create from template

#### Burn-Down Chart Template
- [ ] Burn-down chart created for multi-day phase
  - Check: `docs/velocity/burn-down-chart-phase-X.md`
  - **If missing:** @pm creates from template

---

### 6. Code Quality Baselines

#### Coverage Thresholds
- [ ] Backend coverage threshold met (≥70%)
  - Run: `cd backend && pytest --cov`
  - Check: Coverage ≥70%
  - **If below:** Identify uncovered modules, assign to @dev

- [ ] Frontend coverage threshold met (≥60%)
  - Run: `cd frontend && npm run test:coverage`
  - Check: Coverage ≥60%
  - **If below:** Identify uncovered modules, assign to @dev

#### Linting
- [ ] Frontend linting passes
  - Run: `cd frontend && npm run lint`
  - Check: 0 errors (warnings acceptable)
  - **If failed:** Fix critical errors, defer warnings

- [ ] Backend linting passes (if configured)
  - Run: `cd backend && ruff check .` (or equivalent)
  - Check: 0 errors
  - **If failed:** Fix critical errors, defer warnings

---

### 7. Communication & Coordination

#### Team Availability
- [ ] All assigned agents are available for this phase
  - Check: @dev, @qa, @devops, @pm, @architect, @sm
  - Verify: No planned PTO or unavailability
  - **If unavailable:** Assign backup agent or adjust timeline

#### Daily Standup Scheduled
- [ ] Daily standup time confirmed (e.g., 9am)
  - Check: Calendar invites sent to all agents
  - **If not scheduled:** @sm sends calendar invites immediately

#### Communication Channels
- [ ] All agents have access to shared communication channels
  - Check: Slack/Discord/Teams channel exists and all agents added
  - **If missing:** Create channel, add all agents

---

### 8. Risk Assessment

#### Known Blockers
- [ ] No known blockers exist that would prevent phase start
  - Check: Review previous phase retrospective action items
  - Verify: All P0/P1 impediments from last phase resolved
  - **If blockers exist:** Escalate to @pm, delay phase start if needed

#### External Dependencies
- [ ] All external APIs are operational
  - Check: PNCP API status, OpenAI API status
  - Test: Run health check endpoints
  - **If down:** Coordinate with @devops, consider contingency plan

---

## 🚨 Failure Handling

### P0 Failures (Critical - Blocks Phase Start)
- Missing base components referenced in story
- Required libraries not installed
- Invalid API keys (OpenAI, PNCP)
- Test suites completely broken (syntax errors)

**Action:** STOP phase start, escalate to @pm and @aios-master immediately, create impediment log entry

### P1 Failures (High - Requires Same-Day Fix)
- Test files missing
- Environment variables incomplete
- CI/CD workflows missing
- ADRs incomplete

**Action:** Log impediment, assign to appropriate agent, set deadline for same-day resolution

### P2 Failures (Medium - Can Resolve During Phase)
- Linting warnings
- Documentation incomplete (non-blocking)
- Coverage slightly below threshold (59% vs 60%)

**Action:** Log impediment, assign to appropriate agent, resolve during phase execution

---

## 📊 Checklist Completion Report

**Phase:** [Phase Name/Number]
**Date:** [YYYY-MM-DD]
**Checked By:** @sm [Name]

### Summary
- **Total Items:** [Count]
- **Passed:** [Count]
- **Failed:** [Count]
- **P0 Failures:** [Count] (if >0, phase start BLOCKED)
- **P1 Failures:** [Count] (if >0, same-day resolution required)
- **P2 Failures:** [Count] (resolve during phase)

### Status
- [ ] ✅ All checks passed - **CLEARED FOR PHASE START**
- [ ] ⚠️ P1/P2 failures logged - **PROCEED WITH CAUTION**
- [ ] 🚨 P0 failures exist - **PHASE START BLOCKED**

### Impediments Created
| ID | Impediment | Priority | Assigned To | Deadline |
|----|------------|----------|-------------|----------|
| IMP-XXX | [Description] | [P0/P1/P2] | [@agent] | [Date] |

---

**Signature:** @sm [Name] - [Date]

---

## 🔄 Checklist Maintenance

### When to Update This Checklist
- New dependency added to project (library, package, API)
- New phase type introduced (e.g., discovery phase, deployment phase)
- Retrospective identifies new pre-flight item needed
- Tool or process changes (e.g., new linting tool)

### Version History
| Version | Date | Changes | Updated By |
|---------|------|---------|------------|
| 1.0 | 2026-01-30 | Initial checklist created (from AI-002 action item) | @sm (River) |

---

**Template Location:** `docs/processes/phase-preflight-checklist.md`
**Usage:** Copy this file to `docs/ceremonies/phase-X-preflight-report.md` before each phase
