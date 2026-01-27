# /bidiq — BidIQ Development Command Hub

## Purpose

Central hub for all BidIQ Uniformes development operations. Provides quick access to squads, commands, and development workflows optimized for the PNCP procurement system.

**Status:** MVP v0.1 (Week 1 - Essential features)

---

## Quick Start

### For Backend Development
```
Type: /bidiq backend
→ Activates: team-bidiq-backend
→ Ready to: Implement FastAPI endpoints, PNCP client, database changes
```

### For Frontend Development
```
Type: /bidiq frontend
→ Activates: team-bidiq-frontend
→ Ready to: Build React components, Next.js pages, UI features
```

### For Complete Features
```
Type: /bidiq feature
→ Activates: team-bidiq-feature
→ Ready to: End-to-end feature from story through deployment
```

---

## Available Options

### Development Squads

| Command | Squad | Purpose | When to Use |
|---------|-------|---------|------------|
| `/bidiq backend` | team-bidiq-backend | FastAPI backend development | Building API endpoints, PNCP client, database changes |
| `/bidiq frontend` | team-bidiq-frontend | React/Next.js frontend | Building UI components, pages, user interactions |
| `/bidiq feature` | team-bidiq-feature | End-to-end feature squad | Complete features requiring backend + frontend |

### Status & Information

| Command | Purpose |
|---------|---------|
| `/bidiq status` | Project status dashboard (git, tests, stories, deployment) |
| `/bidiq help` | Show all BidIQ commands and options |
| `/bidiq guide` | Open development guide with examples |

### Quick Actions (Coming Week 2)

| Command | Purpose | Status |
|---------|---------|--------|
| `/bidiq setup-backend` | Setup FastAPI environment | Coming Week 3 |
| `/bidiq setup-frontend` | Setup Next.js environment | Coming Week 4 |
| `/bidiq run-tests` | Execute all tests | Coming Week 2 |
| `/bidiq generate-report` | Generate PNCP reports | Coming Week 3 |
| `/bidiq deploy` | Production deployment | Coming Week 4 |

---

## Command Flow

### Option 1: Activate Backend Squad
```
You: /bidiq backend

System:
  ✅ Team BidIQ Backend activated

  Agents available:
  - @architect     (API design, system architecture)
  - @dev           (FastAPI implementation)
  - @data-engineer (Database design)
  - @qa            (Testing)

  Next step: Type *develop to start implementation
```

### Option 2: Activate Frontend Squad
```
You: /bidiq frontend

System:
  ✅ Team BidIQ Frontend activated

  Agents available:
  - @ux-design-expert  (UI/UX design)
  - @dev               (React implementation)
  - @qa                (Testing)

  Next step: Type *develop to start implementation
```

### Option 3: Activate Complete Feature Squad
```
You: /bidiq feature

System:
  ✅ Team BidIQ Feature Complete activated

  Agents available:
  - @pm              (Story management)
  - @architect       (Design review)
  - @dev             (Implementation)
  - @qa              (Testing)
  - @devops          (Deployment)

  Next step: Type *create-story to start new feature
```

---

## Development Workflows

### Backend Development Typical Flow

1. **Choose squad**: `/bidiq backend`
2. **Create/select story**: Ask @pm to create story or select existing
3. **Implement**: `*develop` command to start coding
4. **Test**: `*run-tests` to validate coverage (≥70%)
5. **Deploy**: Create PR for code review

### Frontend Development Typical Flow

1. **Choose squad**: `/bidiq frontend`
2. **Design**: @ux-design-expert creates wireframes
3. **Implement**: `*develop` to build React components
4. **Test**: `*run-tests` to validate coverage (≥60%)
5. **Deploy**: Create PR for code review

### Full Feature Development Typical Flow

1. **Choose squad**: `/bidiq feature`
2. **Create story**: `*create-story` with acceptance criteria
3. **Architecture review**: @architect reviews design
4. **Implement backend**: `*develop backend`
5. **Implement frontend**: `*develop frontend`
6. **Test all**: `*run-tests` (backend + frontend)
7. **Deploy**: @devops creates PR and deploys

---

## Quality Gates

All BidIQ squads enforce quality gates:

### Backend Quality Gates
- **Pre-commit**: pytest coverage ≥70%, mypy type checking
- **Pre-merge**: All tests passing, coverage ≥70%
- **Testing**: 82+ tests, 96%+ coverage

### Frontend Quality Gates
- **Pre-commit**: npm lint (0 errors), typecheck (0 errors)
- **Pre-merge**: npm test coverage ≥60%, build succeeds
- **Testing**: Jest tests, accessibility checks

---

## Project Status Integration

Get real-time project status:

```
/bidiq status

📊 BidIQ Project Status

🌿 Git:
  Branch: feature/issue-31-production-deployment
  Behind main: 2 commits
  Modified files: 127

🧪 Tests:
  Backend: ✅ 96.69% coverage (82 tests)
  Frontend: ⚠️  Not configured (Issue #21)
  Last run: 23 minutes ago

📖 Stories:
  In Progress: 2 (Story 2.1, Story 3.4)
  Blocked: 0
  Completed: 8
```

---

## File Structure

### Squads (Agent Teams)
- `.aios-core/development/agent-teams/team-bidiq-backend.yaml` - Backend squad
- `.aios-core/development/agent-teams/team-bidiq-frontend.yaml` - Frontend squad
- `.aios-core/development/agent-teams/team-bidiq-feature.yaml` - Complete feature squad

### Development Guide
- `docs/guides/bidiq-development-guide.md` - Comprehensive guide with examples

### Commands
- `.claude/commands/bidiq.md` - This file (meta-command hub)
- Coming Week 2: Individual command files (status, help, run-tests)
- Coming Week 3: Setup and reporting commands
- Coming Week 4: Deployment and automation commands

---

## Key Concepts

### Squads vs Commands

**Squads (Agent Teams):**
- Multiple agents working together
- Structured workflow with quality gates
- Used for complex, multi-step work
- Example: `team-bidiq-backend` (architect + dev + data-engineer + qa)

**Commands (Quick Actions):**
- Single execution, focused purpose
- Minimal setup required
- Used for quick checks and reports
- Example: `/status` (shows project health)

### Stories & Issues

All development starts with stories in `docs/stories/`:
- Story number (e.g., Story 2.1)
- Title and description
- Acceptance criteria
- Task checklist
- Team assignment

### Quality Gates

Automated checks at multiple stages:
- **Pre-commit**: Local checks before staging
- **Pre-merge**: Final validation before PR merge
- **Pre-deployment**: Production readiness check

---

## MVP Phase (Week 1) ✅

**Completed:**
- ✅ Team BidIQ Backend squad
- ✅ Team BidIQ Frontend squad
- ✅ Team BidIQ Feature Complete squad
- ✅ /bidiq meta-command hub
- ✅ Development guide

**What's working now:**
- Squad activation and agent coordination
- Quality gates enforcement
- Task tracking in stories
- Test coverage validation

---

## Coming Soon (Week 2-4)

### Week 2: Basic Commands
- `/bidiq status` - Real-time project health
- `/bidiq run-tests` - Execute all tests
- `/bidiq help` - Command reference

### Week 3: Setup & Reporting (After Issue #17)
- `/bidiq setup-backend` - FastAPI environment setup
- `/bidiq generate-report` - PNCP procurement reports

### Week 4: Advanced Automation (After Issue #21)
- `/bidiq setup-frontend` - Next.js environment setup
- `/bidiq deploy` - Production deployment workflow
- `/bidiq dev-cycle` - Automated development cycle

---

## Troubleshooting

### Squad not activating?
1. Verify squad file exists: `.aios-core/development/agent-teams/team-bidiq-*.yaml`
2. Check agent dependencies are available
3. Try: `/squad-creator` → "Load existing squad"

### Tests failing?
1. Check quality gate thresholds (70% backend, 60% frontend)
2. Run with: `/bidiq run-tests` (coming Week 2)
3. View coverage: `backend/htmlcov/index.html` or `frontend/coverage/`

### Story not visible?
1. Stories located in: `docs/stories/`
2. Story format: `story-{number}-{title}.md`
3. Ask @pm or @sm to create new story

---

## Key Files & Resources

**Development Guide:**
- `docs/guides/bidiq-development-guide.md` (comprehensive, with examples)

**Squad Definitions:**
- `.aios-core/development/agent-teams/team-bidiq-backend.yaml`
- `.aios-core/development/agent-teams/team-bidiq-frontend.yaml`
- `.aios-core/development/agent-teams/team-bidiq-feature.yaml`

**Project Specifications:**
- `CLAUDE.md` - Project standards and conventions
- `PRD.md` - Product requirements and technical specs
- `.env.example` - Environment variable reference

**Quality Standards:**
- Backend: 70% minimum coverage (pytest)
- Frontend: 60% minimum coverage (jest)
- All: 0 CRITICAL linting/type errors

---

## For More Information

- **Full development guide:** `docs/guides/bidiq-development-guide.md`
- **Backend details:** Read squad file `team-bidiq-backend.yaml`
- **Frontend details:** Read squad file `team-bidiq-frontend.yaml`
- **Feature workflow:** Read squad file `team-bidiq-feature.yaml`
- **Project specs:** See `CLAUDE.md` and `PRD.md`

---

**Status:** MVP v0.1 Ready for Use ✅
**Last Updated:** 2026-01-26
**Framework:** Synkra AIOS v2.0
