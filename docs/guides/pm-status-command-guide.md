# PM Status Command Guide

**Command:** `*status`
**Agent:** @pm (Morgan, Product Manager)
**Purpose:** Display comprehensive project status with recommendations

## Quick Start

When activated as PM agent:

```bash
@pm: *status
```

Or manually:
```bash
node .aios-core/development/scripts/pm-project-status.js
```

## What You Get

The status command provides real-time project intelligence:

### 📊 Project Overview
- **Version:** POC v0.2 (current)
- **Branch:** Automatically detects from git
- **Last Commit:** Recent changes history
- **Overall Status:** Production readiness indicator

### 🎯 Feature Completion
Comprehensive breakdown by area:
- **Backend:** 7 core features (PNCP client, filtering, Excel, LLM, logging, etc.)
- **Frontend:** 6 core features (Next.js, components, API, testing, etc.)
- **DevOps:** 5 infrastructure features (Docker, CI/CD, deployment configs)

All features shown with completion status (✅ done / ⏳ in progress)

### 🧪 Test Coverage & Quality
Real-time metrics:
- **Backend Tests:** 226 passing, 96.69% coverage (threshold: 70%)
- **Frontend Tests:** Jest configured, ready to run (threshold: 60%)
- **E2E Tests:** Playwright configured for integration testing

### 🚀 Deployment Readiness
Checklist verification:
- ✅ Railway configuration (backend hosting)
- ✅ Docker image (containerization)
- ✅ Environment setup (.env.example)
- ✅ Deployment guide (DEPLOYMENT.md)

**Status:** Ready for production deployment

### 📈 Prioritized Recommendations

5 action items ranked by priority:

**HIGH Priority:**
1. Deploy to Production (Railway + Vercel)
2. Create Post-Launch Roadmap (Phase 2: Database, Auth, Caching)

**MEDIUM Priority:**
3. Set Up Monitoring (Sentry, logging, performance)
4. Create User Documentation (Admin guide, API docs)

**LOW Priority:**
5. Performance Optimization (Backend filter optimization)

Each recommendation includes:
- Detailed description
- Suggested PM command or action
- Expected impact

### 📚 Quick Reference

Common commands at a glance:
- Development squads (backend, frontend, feature)
- PM commands (create-prd, create-epic, research)
- Documentation locations
- Test execution commands
- Deployment procedures

## Real-Time Data

The status command gathers live data from:

- **Git History:** Current branch, recent commits
- **Test Coverage:** Actual pytest/Jest reports
- **Configuration Files:** Deployment readiness checks
- **File System:** Verification of critical files
- **Documentation:** Links to key resources

## Use Cases

### 1. Daily Standup
```bash
*status
```
Quick overview for team sync-ups

### 2. Sprint Planning
```bash
*status
→ Review recommendations
→ *create-epic (to plan next sprint)
```

### 3. Pre-Deployment
```bash
*status
→ Verify deployment readiness (✅ all green)
→ Proceed with deployment
```

### 4. Stakeholder Updates
```bash
*status
→ Share feature completion report
→ Present recommended next steps
→ Plan roadmap meeting
```

### 5. Post-Completion
```bash
*status
→ Identify next priority actions
→ Create next epic (*create-epic)
→ Update team on progress
```

## Integration with PM Workflows

### Creating PRDs Based on Status
```bash
*status
→ Review "Create Post-Launch Roadmap" recommendation
→ *create-brownfield-prd
→ Build Phase 2 requirements
```

### Sprint Planning
```bash
*status
→ Review feature completion
→ *create-epic (for next sprint)
→ Delegate to @sm for story creation
```

### Course Correction
```bash
*status
→ If issues detected
→ *correct-course (analyze deviations)
→ Update roadmap accordingly
```

## Sample Output

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    📋 BidIQ PROJECT STATUS REPORT                          ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 PROJECT OVERVIEW
Version:        POC v0.2 (Feature-Complete)
Branch:         feature/issue-31-production-deployment
Status:         ✅ PRODUCTION-READY FOR DEPLOYMENT

🎯 FEATURE COMPLETION: 18/18 COMPLETE ✅
BACKEND: 7 features
FRONTEND: 6 features
DEVOPS: 5 features

🧪 TEST COVERAGE
Backend:        ✅ 96.69% (226 tests passing)
Frontend:       ✅ Ready (Jest configured)

🚀 DEPLOYMENT READINESS: ✅ READY FOR PRODUCTION

📈 RECOMMENDATIONS
1. [HIGH] Deploy to Production → *create-doc
2. [HIGH] Create Phase 2 Roadmap → *create-prd
3. [MEDIUM] Set Up Monitoring → /devops
4. [MEDIUM] Create User Documentation → *create-doc
5. [LOW] Performance Optimization → /dev
```

## Command History

Every time you run `*status`:
- Checks latest git commits
- Reads current test coverage
- Verifies deployment configs
- Generates fresh recommendations
- Provides up-to-date action items

## Related PM Commands

After reviewing status:

- **`*create-prd`** - Create product requirements based on recommendations
- **`*create-epic`** - Define epics for next sprint
- **`*create-story`** - Create detailed user stories
- **`*research {topic}`** - Deep dive on specific areas
- **`*correct-course`** - Analyze deviations from plan
- **`*help`** - See all PM commands

## Tips & Tricks

### Use in Scripts
```bash
# Automatic status check in CI/CD
node .aios-core/development/scripts/pm-project-status.js > status-report.txt
```

### Team Communication
```bash
# Share status with team before standup
*status > status-report.md
# Distribute via Slack/Email
```

### Dashboard Integration
```bash
# Export for monitoring
node .aios-core/development/scripts/pm-project-status.js > /tmp/bidiq-status.json
```

### Custom Filtering
```bash
# Show just deployment status
*status | grep -A 8 "DEPLOYMENT READINESS"
```

## Troubleshooting

**Q: Status shows "unknown" for some metrics**
A: Check if test coverage reports exist. Run tests first:
```bash
cd backend && pytest --cov
cd frontend && npm test:coverage
```

**Q: Git information not showing correctly**
A: Ensure git is configured:
```bash
git config user.email "your@email.com"
git log -1 (should show recent commits)
```

**Q: Deployment status shows incomplete**
A: Verify files exist:
```bash
ls backend/railway.toml        # Should exist
ls docs/DEPLOYMENT.md          # Should exist
```

## Performance

The `*status` command:
- **Execution Time:** <1 second
- **No External Dependencies:** Uses only Node.js + Git
- **Real-time Data:** Always current
- **Safe:** Read-only operations

## Future Enhancements

Planned improvements:
- [ ] Slack webhook integration for daily reports
- [ ] Web dashboard version
- [ ] Metrics trending over time
- [ ] Automated alerts for threshold breaches
- [ ] Custom recommendation engine
- [ ] Performance metrics tracking
- [ ] Burndown chart integration

## Support

Issues with `*status` command?

1. Check file exists: `.aios-core/development/scripts/pm-project-status.js`
2. Run manually: `node pm-project-status.js`
3. Review script logs for errors
4. Verify git is working: `git status`
5. Check test reports exist in coverage folders

---

**Created:** 2026-01-27
**Status:** ✅ Ready for use
**Version:** 1.0

For more PM agent commands, see CLAUDE.md or type `*help` when activated.
