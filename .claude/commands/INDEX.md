# Claude Code Commands Index

**Project:** BidIQ Uniformes (PNCP POC v0.2)
**Framework:** Synkra AIOS v2.0

## Command-Agent Mapping

All commands listed below activate their corresponding agent with full persona and capabilities.

### Master Orchestration

| Command | Agent | File | Purpose |
|---------|-------|------|---------|
| `/AIOS` | @aios-master | `.claude/commands/AIOS.md` | Central AIOS hub and agent selector |
| `/aios-master` | @aios-master | `.claude/commands/aios-master.md` | Master orchestrator and framework developer |

### Core Development Agents

| Command | Agent | File | Purpose |
|---------|-------|------|---------|
| `/dev` | @dev | `.claude/commands/dev.md` | Full-stack developer (James) |
| `/qa` | @qa | `.claude/commands/qa.md` | Quality assurance (Quinn) |
| `/architect` | @architect | `.claude/commands/architect.md` | Technical architect (Aria) |
| `/analyst` | @analyst | `.claude/commands/analyst.md` | Business analyst (Atlas) |

### Product & Project Agents

| Command | Agent | File | Purpose |
|---------|-------|------|---------|
| `/pm` | @pm | `.claude/commands/pm.md` | Engineering manager (Morgan) |
| `/po` | @po | `.claude/commands/po.md` | Product owner (Sarah) |
| `/sm` | @sm | `.claude/commands/sm.md` | Scrum master (River) |

### Specialized Agents

| Command | Agent | File | Purpose |
|---------|-------|------|---------|
| `/data-engineer` | @data-engineer | `.claude/commands/data-engineer.md` | Database architect (Dara) |
| `/devops` | @devops | `.claude/commands/devops.md` | GitHub DevOps manager (Gage) |
| `/squad-creator` | @squad-creator | `.claude/commands/squad-creator.md` | Agent team assembler |
| `/ux-design-expert` | @ux-design-expert | `.claude/commands/ux-design-expert.md` | UX designer (Uma) |

### BidIQ Project Commands

| Command | File | Purpose |
|---------|------|---------|
| `/bidiq` | `.claude/commands/bidiq.md` | BidIQ development command hub (squads, quick actions) |

**BidIQ Squads (Agent Teams):**
- `team-bidiq-backend` - FastAPI backend development (architect, dev, data-engineer, qa)
- `team-bidiq-frontend` - React/Next.js frontend (ux-design-expert, dev, qa)
- `team-bidiq-feature` - Complete features (pm, architect, dev, qa, devops)

**Activation:**
```
/bidiq backend      → Backend development squad
/bidiq frontend     → Frontend development squad
/bidiq feature      → Complete feature squad (backend + frontend)
```

### Governance & Automation

| Command | File | Purpose |
|---------|------|---------|
| `/review-pr` | `.claude/commands/review-pr.md` | Universal automated PR governance & merge |
| `/audit-roadmap` | `.claude/commands/audit-roadmap.md` | Roadmap integrity audit |
| `/pick-next-issue` | `.claude/commands/pick-next-issue.md` | Select next issue from backlog |

## Agent Locations

All agent definitions are located in: `.claude/commands/AIOS/agents/`

```
.claude/commands/AIOS/agents/
├── _README.md                    # Agent system documentation
├── aios-master.md               # Orchestrator & Framework Developer
├── analyst.md                   # Business Analyst
├── architect.md                 # Technical Architect
├── data-engineer.md             # Database Architect
├── dev.md                       # Full Stack Developer
├── devops.md                    # GitHub DevOps Manager
├── pm.md                        # Engineering Manager
├── po.md                        # Product Owner
├── qa.md                        # Quality Assurance
├── sm.md                        # Scrum Master
├── squad-creator.md             # Agent Team Creator
└── ux-design-expert.md          # UX Designer
```

## Quick Reference: When to Use Each Agent

### By Task Type

| Task | Agent(s) |
|------|----------|
| Write code | `@dev` |
| Test code | `@qa` |
| Design system | `@architect` |
| Create story | `@pm` or `@sm` |
| Manage backlog | `@po` |
| Refine requirements | `@analyst` |
| Database work | `@data-engineer` |
| Push to remote | `@devops` |
| UX/UI design | `@ux-design-expert` |
| Multi-agent tasks | `@aios-master` |

### By Department/Role

| Department | Primary Agent | Secondary Agents |
|-----------|--------------|------------------|
| **Engineering** | @dev | @qa, @architect |
| **QA/Testing** | @qa | @dev |
| **Database** | @data-engineer | @architect, @qa |
| **DevOps/Infra** | @devops | @architect |
| **Product** | @po | @pm, @analyst |
| **Project Mgmt** | @pm | @sm, @po |
| **Design** | @ux-design-expert | @architect, @po |
| **Executive** | @aios-master | All agents |

## Command Activation Flow

```
1. Type command (e.g., /dev)
2. Agent command file loads (e.g., dev.md)
3. Agent definition file loads (e.g., .claude/commands/AIOS/agents/dev.md)
4. Agent persona activates with complete YAML configuration
5. Greeting displayed with adaptive context
6. Agent awaits commands with * prefix (e.g., *help, *develop, *run-tests)
```

## Proactive Agent Invocation

According to `CLAUDE.md`, agents should be **proactively invoked** based on context:

### Trigger → Agent Mapping

| Situation | Trigger → Agent |
|-----------|-----------------|
| User: "Implement feature X" | → `/dev` |
| User: "Write tests for Y" | → `/qa` |
| User: "New story needed" | → `/sm` or `/pm` |
| User: "Architecture question" | → `/architect` |
| User: "Database schema" | → `/data-engineer` |
| User: "How do we ship this?" | → `/devops` |
| User: "What should users see?" | → `/ux-design-expert` |
| User: "Business requirements?" | → `/analyst` |
| User: "Backlog priority?" | → `/po` |
| User: Complex multi-domain task | → `/AIOS` |

## Configuration Files

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Development rules and guidelines |
| `.claude/rules/mcp-usage.md` | MCP server governance rules |
| `.claude/commands/INDEX.md` | This file - command reference |

## Agent System Documentation

- **Overview:** See `CLAUDE.md` for development methodology
- **Agent Details:** See `.claude/commands/AIOS/agents/_README.md`
- **Integration Standards:** See `docs/architecture/agent-tool-integration-guide.md`
- **Framework Guide:** See `.aios-core/user-guide.md`

## Troubleshooting

### Command not recognized
- Ensure command starts with `/` (e.g., `/dev`)
- Check agent file exists in `.claude/commands/AIOS/agents/`
- Try `/AIOS` to access master selector

### Agent not activating properly
- Verify `.claude/commands/AIOS/agents/{agent-id}.md` exists
- Check agent file contains valid YAML block
- Ensure activation-instructions are present

### Command within agent not working
- Commands within agents use `*` prefix (e.g., `*help`)
- Verify command is listed in agent's commands section
- Check agent file for dependency availability

## BidIQ Development Resources

- **Development Guide:** `docs/guides/bidiq-development-guide.md` (comprehensive with examples)
- **Backend Squad:** `.aios-core/development/agent-teams/team-bidiq-backend.yaml`
- **Frontend Squad:** `.aios-core/development/agent-teams/team-bidiq-frontend.yaml`
- **Feature Squad:** `.aios-core/development/agent-teams/team-bidiq-feature.yaml`

## More Information

- **AIOS Framework:** `.aios-core/user-guide.md` (1200+ lines)
- **Task Catalog:** `.aios-core/development/tasks/` (115+ tasks)
- **Workflow Definitions:** `.aios-core/development/workflows/` (7 workflows)
- **Project Setup:** `CLAUDE.md` in root directory
- **BidIQ Quick Start:** `/bidiq` command hub

---

**Last Updated:** 2026-01-26
**Status:** ✅ All 12 agents + 3 governance commands + BidIQ MVP configured
**Framework Version:** Synkra AIOS v2.0
**BidIQ MVP:** ✅ 3 squads + meta-command + development guide (Week 1)
