# AIOS Framework Integration

This project uses the AIOS Framework for AI-orchestrated development.

## Available Agents

- `@dev` - Development and implementation
- `@qa` - Quality assurance and testing
- `@architect` - Architectural decisions
- `@pm` - Story management
- `@devops` - Infrastructure and GitHub operations
- `@data-engineer` - Database and data pipeline
- `@ux-design-expert` - UX/UI design
- `@analyst` - Business requirements
- `@sm` - Scrum ceremonies
- `@po` - Product ownership
- `@aios-master` - Multi-agent orchestration

## AIOS Commands

- `/AIOS/story` - Create new story
- `/AIOS/review` - Code review
- `/AIOS/docs` - Generate documentation
- See `.aios-core/user-guide.md` for complete command list

## MCP Usage Rules

- Native Claude Code tools (Read, Write, Edit, Bash, Glob, Grep) take priority
- Docker gateway (desktop-commander) only for Docker operations
- Playwright for browser automation only
- See `.claude/rules/mcp-usage.md` for detailed rules

## Proactive Agent & Script Invocation

**CRITICAL:** Claude should PROACTIVELY invoke appropriate agents, tasks, and scripts from `.aios-core/development/` based on the user's context and needs. Do NOT wait for explicit user requests.

### When to Invoke Agents Proactively

| Situation | Agent(s) | Action |
|-----------|----------|--------|
| User describes new feature/requirement | `@pm` or `@po` | Create story with proper acceptance criteria |
| User asks architectural questions | `@architect` | Analyze design patterns, provide technical guidance |
| Code implementation needed | `@dev` | Implement features following project standards |
| Tests needed or test failures | `@qa` | Create test suites, debug failures |
| Docker/CI/CD/GitHub operations | `@devops` | Handle infrastructure tasks |
| Data modeling or database work | `@data-engineer` | Design schemas, migrations, queries |
| UX/UI design questions | `@ux-design-expert` | Design patterns, accessibility, user flows |
| Process/workflow questions | `@sm` | Scrum ceremonies, sprint planning |
| Business requirements analysis | `@analyst` | Requirements elicitation, feasibility |
| Complex multi-agent tasks | `@aios-master` | Orchestrate multiple agents |

**Invocation Method:** Use the `Skill` tool with the agent name:
```
Skill(skill: "dev", args: "implement PNCP client retry logic")
```

### When to Invoke Tasks Proactively

| Situation | Task | Location |
|-----------|------|----------|
| Creating new story | `create-story.md` or `create-next-story.md` | `.aios-core/development/tasks/` |
| Brownfield analysis needed | `analyze-brownfield.md` | `.aios-core/development/tasks/` |
| Code review requested | `review-code.md` | Available via `/AIOS/review` |
| Component creation | `build-component.md` | `.aios-core/development/tasks/` |
| Database migration | `db-apply-migration.md` | `.aios-core/development/tasks/` |
| Performance analysis | `analyze-performance.md` | `.aios-core/development/tasks/` |
| Codebase audit | `audit-codebase.md` | `.aios-core/development/tasks/` |
| CI/CD setup | `ci-cd-configuration.md` | `.aios-core/development/tasks/` |
| Documentation needed | `create-doc.md` | `.aios-core/development/tasks/` |
| Architectural impact analysis | `architect-analyze-impact.md` | `.aios-core/development/tasks/` |

**Task Execution:** Load the task Markdown file and follow its workflow instructions:
```bash
node .aios-core/development/scripts/story-manager.js create-story --title "Feature X"
```

### When to Invoke Scripts Proactively

| Situation | Script | Purpose |
|-----------|--------|---------|
| Loading agent configuration | `agent-config-loader.js` | Parse agent definitions |
| Story management operations | `story-manager.js` | Create, update, sync stories |
| Recording architectural decisions | `decision-recorder.js` | Log ADRs and decisions |
| Building agent greetings | `greeting-builder.js` | Context-aware agent initialization |
| Workflow navigation | `workflow-navigator.js` | Multi-step process guidance |
| Task validation | `validate-task-v2.js` | Validate story/task structure |
| Backlog management | `backlog-manager.js` | Prioritize and organize work |
| Squad operations | `squad/squad-generator.js` | Create multi-agent teams |

### When to Invoke Workflows Proactively

| Situation | Workflow | Location |
|-----------|----------|----------|
| New full-stack project | `greenfield-fullstack.yaml` | `.aios-core/development/workflows/` |
| New backend service | `greenfield-service.yaml` | `.aios-core/development/workflows/` |
| New frontend project | `greenfield-ui.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing full-stack | `brownfield-fullstack.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing backend | `brownfield-service.yaml` | `.aios-core/development/workflows/` |
| Enhancing existing frontend | `brownfield-ui.yaml` | `.aios-core/development/workflows/` |

### BidIQ-Specific Workflows (PREFER THESE for this project)

| User Says / Context | Workflow | Agents |
|---------------------|----------|--------|
| "integrate X API" / new API client | `bidiq-api-integration.yaml` | architect -> dev -> qa |
| "add feature X" / full-stack feature | `bidiq-feature-e2e.yaml` | pm -> architect -> dev -> qa -> devops |
| "bug in X" / "fix X" / production issue | `bidiq-hotfix.yaml` | dev -> qa -> devops |
| "add filter" / "new report" / data pipeline | `bidiq-data-pipeline.yaml` | data-engineer -> architect -> dev -> qa |
| "improve prompt" / "LLM output is wrong" | `bidiq-llm-prompt.yaml` | analyst -> dev -> qa |
| "deploy" / "release" / "push to production" | `bidiq-deploy-release.yaml` | qa -> devops |
| "start sprint" / "plan work" | `bidiq-sprint-kickoff.yaml` | pm -> po -> sm -> architect -> dev |
| "slow" / "performance" / "timeout" | `bidiq-performance-audit.yaml` | architect -> dev -> qa |
| "audit codebase" / "technical debt" | `brownfield-discovery.yaml` | architect -> data-engineer -> ux -> qa -> analyst -> pm |

**This project is BROWNFIELD** - use brownfield and BidIQ-specific workflows for enhancements.

**PROACTIVE RULE:** When the user describes a task, AUTOMATICALLY select and follow the matching BidIQ workflow without waiting for explicit invocation.

### Agent Team Configurations

Pre-configured teams from `.aios-core/development/agent-teams/`:

| Team | Use Case | File |
|------|----------|------|
| Full Team | Complex features requiring all roles | `team-all.yaml` |
| Full-Stack | Backend + Frontend + QA + DevOps | `team-fullstack.yaml` |
| Backend Only | API/service development | `team-no-ui.yaml` |
| Quality Focus | Bug fixes, testing, refactoring | `team-qa-focused.yaml` |
| Minimal | Quick fixes, single-component work | `team-ide-minimal.yaml` |

### Script Usage Patterns

```bash
# Story Management
node .aios-core/development/scripts/story-manager.js create --title "Add pagination"
node .aios-core/development/scripts/story-manager.js update --id STORY-001 --status completed

# Decision Recording
node .aios-core/development/scripts/decision-recorder.js \
  --type architecture \
  --title "Use Redis for caching" \
  --rationale "Improve response time for frequently accessed data"

# Squad Management
node .aios-core/development/scripts/squad/squad-generator.js \
  --agents dev,qa,architect \
  --task "Implement PNCP client resilience"
```

### Key Principles

1. **Anticipate Needs:** Don't wait for explicit agent requests - invoke based on context
2. **Use Right Tool:** Choose agent/task/script based on specific need
3. **Chain Operations:** Multiple agents may be needed sequentially
4. **Document Decisions:** Use decision-recorder.js for architectural choices
5. **Follow Workflows:** Use brownfield workflows for this existing project
6. **Validate Work:** Always involve @qa for quality assurance
7. **Team Collaboration:** Use team configs for complex multi-role tasks

### Task Categories Reference

**Story Management:** create-story, create-next-story, validate-story, sync-story
**Code Operations:** review-code, refactor, audit-codebase, cleanup-utilities
**Component Building:** build-component, compose-molecule, bootstrap-shadcn-library
**Database:** db-apply-migration, db-domain-modeling, db-schema-audit, db-rollback
**Testing:** apply-qa-fixes, create-suite, analyze-framework
**Documentation:** create-doc, update-readme, document-api
**Architecture:** architect-analyze-impact, analyze-brownfield, consolidate-patterns
**DevOps:** ci-cd-configuration, add-mcp, db-env-check
**Performance:** analyze-performance, db-analyze-hotpaths, db-explain
**Process:** correct-course, collaborative-edit, handoff, execute-checklist

See `.aios-core/development/tasks/` for complete list (115+ tasks available).
