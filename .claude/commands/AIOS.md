# /AIOS — AIOS Master Agent Orchestrator

**Activation:** `@aios-master` or `/AIOS`

**Purpose:** Unified access point to all AIOS agents, framework resources, and orchestration capabilities.

## Quick Agent Access

Activate any agent directly:

```
/dev              → Full Stack Developer (James)
/qa               → Quality Assurance (Quinn)
/architect        → Technical Architect (Aria)
/analyst          → Business Analyst (Atlas)
/pm               → Engineering Manager (Morgan)
/po               → Product Owner (Sarah)
/sm               → Scrum Master (River)
/data-engineer    → Database Architect (Dara)
/devops           → GitHub DevOps Manager (Gage)
/squad-creator    → Squad Creator (Agent Assembly Specialist)
/ux-design-expert → UX Designer (Uma)
```

## Master Commands

- `*help` - Show all AIOS commands and agents
- `*create-story` - Create new development story
- `*task {name}` - Execute specific task from `.aios-core/development/tasks/`
- `*workflow {name}` - Run workflow from `.aios-core/development/workflows/`
- `*kb` - Access AIOS Knowledge Base (`.aios-core/data/aios-kb.md`)
- `*exit` - Exit agent mode

## Agent System Architecture

All agents share:
- **Location:** `.claude/commands/AIOS/agents/{agent-id}.md`
- **Format:** Markdown with embedded YAML configuration
- **Activation:** Commands automatically load agent persona and guidelines
- **Dependencies:** Tasks, templates, checklists from `.aios-core/development/`

## Available Commands via Agents

| Agent | Primary Commands | Best For |
|-------|-----------------|----------|
| **@dev** | `*develop`, `*create-service`, `*run-tests` | Implementation, debugging, refactoring |
| **@qa** | `*generate-tests`, `*run-tests`, `*qa-gate` | Testing, quality validation |
| **@architect** | `*analyze-impact`, `*design-system` | Architecture decisions, design reviews |
| **@analyst** | `*analyze-brownfield`, `*create-prd` | Requirements, analysis, research |
| **@pm** | `*create-story`, `*sprint-planning` | Project planning, resource allocation |
| **@po** | `*manage-backlog`, `*refine-story` | Product backlog, story refinement |
| **@sm** | `*facilitate-ceremony`, `*create-next-story` | Scrum ceremonies, sprint management |
| **@data-engineer** | `*db-apply-migration`, `*db-schema-audit` | Database design, migrations, optimization |
| **@devops** | `*push-changes`, `*ci-cd-config` | Repository operations, CI/CD setup |
| **@squad-creator** | `*create-squad`, `*analyze-squad` | Multi-agent team assembly |
| **@ux-design-expert** | `*create-wireframe`, `*user-research` | UX/UI design, usability research |

## Global Commands (Available from Any Agent)

- `/AIOS` - Return to master
- `/dev`, `/qa`, `/architect`, etc. - Switch agents
- `*help` - Agent-specific help
- `*exit` - Exit agent mode and return to Claude Code

## Framework Resources

All agents have access to:

**Tasks:** `.aios-core/development/tasks/` (115+ workflow definitions)
**Templates:** `.aios-core/development/templates/` (component, document, architecture templates)
**Checklists:** `.aios-core/product/checklists/` (validation, review, deployment checklists)
**Workflows:** `.aios-core/development/workflows/` (multi-step process orchestrations)
**Data:** `.aios-core/data/` (knowledge base, learned patterns, preferences)

## Proactive Agent Invocation

According to CLAUDE.md, agents should be invoked proactively based on context:

| Situation | Agent(s) |
|-----------|----------|
| Code implementation needed | `@dev` |
| Tests needed or failures | `@qa` |
| Architectural questions | `@architect` |
| New feature/requirement | `@pm` or `@po` |
| Docker/CI/CD/GitHub operations | `@devops` |
| Database work | `@data-engineer` |
| UX/UI design questions | `@ux-design-expert` |
| Process/workflow questions | `@sm` |
| Business analysis | `@analyst` |
| Complex multi-agent tasks | `@aios-master` |

## Example Workflows

### Create and Implement a Story

```
1. Activate @pm: *create-story
2. Activate @dev: *develop story-X.Y.Z
3. Activate @qa: *generate-tests
4. Activate @devops: *push-changes
```

### Database Migration

```
1. Activate @data-engineer: *db-domain-modeling
2. Activate @data-engineer: *db-apply-migration
3. Activate @qa: *db-smoke-test
```

### UX Research → Design → Implementation

```
1. Activate @ux-design-expert: *user-research
2. Activate @ux-design-expert: *create-wireframe
3. Activate @dev: *build-component
4. Activate @qa: *accessibility-audit
```

## Configuration

**Agent Definitions:** `.claude/commands/AIOS/agents/`
**Agent Persona Standards:** `.claude/commands/AIOS/agents/_README.md`
**Tool Integration:** `.claude/rules/mcp-usage.md`
**Development Rules:** `.claude/CLAUDE.md`

---

**Learn More:**
- See `.aios-core/user-guide.md` for complete AIOS documentation
- See `.aios-core/development/README.md` for task and workflow reference
- See `CLAUDE.md` for proactive agent invocation guidelines

