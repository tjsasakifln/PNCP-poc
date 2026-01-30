# AIOS Workflows

This directory contains workflow definitions for the Synkra AIOS framework. Workflows define multi-step processes that can be executed by AIOS agents.

## Available Workflows

### Generic Development Workflows
- **brownfield-fullstack.yaml** - Workflow for existing full-stack projects
- **brownfield-service.yaml** - Workflow for existing service/backend projects
- **brownfield-ui.yaml** - Workflow for existing UI/frontend projects
- **greenfield-fullstack.yaml** - Workflow for new full-stack projects
- **greenfield-service.yaml** - Workflow for new service/backend projects
- **greenfield-ui.yaml** - Workflow for new UI/frontend projects

### Discovery & Audit Workflows
- **brownfield-discovery.yaml** - Comprehensive technical debt assessment with multi-agent validation cycles

### BidIQ-Specific Workflows

| Workflow | ID | Purpose | Agents |
|----------|----|---------|--------|
| **bidiq-api-integration.yaml** | `bidiq-api-integration` | Integrate external API with PNCP resilience pattern (retry, rate-limit, circuit breaker) | architect → dev → qa |
| **bidiq-feature-e2e.yaml** | `bidiq-feature-e2e` | Complete end-to-end feature (backend + frontend + tests + PR) | pm → architect → dev → qa → devops |
| **bidiq-hotfix.yaml** | `bidiq-hotfix` | Fast diagnosis and fix cycle for production issues | dev → qa → devops |
| **bidiq-data-pipeline.yaml** | `bidiq-data-pipeline` | Data pipeline: filtering, transformation, Excel/report generation | data-engineer → architect → dev → qa |
| **bidiq-llm-prompt.yaml** | `bidiq-llm-prompt` | LLM prompt engineering cycle (design → test → evaluate → refine) | analyst → dev → qa |
| **bidiq-deploy-release.yaml** | `bidiq-deploy-release` | Release process: tests → build → deploy → smoke test | qa → devops |
| **bidiq-sprint-kickoff.yaml** | `bidiq-sprint-kickoff` | Sprint planning ceremony | pm → po → sm → architect → dev |
| **bidiq-performance-audit.yaml** | `bidiq-performance-audit` | Performance audit: profiling → bottlenecks → optimization → validation | architect → dev → qa |

### Configuration Workflows
- **setup-environment.yaml** - Configure IDE (Windsurf/Cursor/Claude Code) with AIOS development rules

## Proactive Workflow Selection

Workflows should be invoked **proactively** based on context. Use this decision matrix:

| User Says / Context | Workflow |
|---------------------|----------|
| "integrate X API" / "connect to external service" | `bidiq-api-integration` |
| "add feature X" / "implement X with backend and frontend" | `bidiq-feature-e2e` |
| "bug in X" / "X is broken" / "fix X" | `bidiq-hotfix` |
| "add filter" / "new report" / "Excel changes" / "data pipeline" | `bidiq-data-pipeline` |
| "improve prompt" / "LLM output is wrong" / "add AI summary" | `bidiq-llm-prompt` |
| "deploy" / "release" / "push to production" | `bidiq-deploy-release` |
| "start sprint" / "what should we work on next" / "plan work" | `bidiq-sprint-kickoff` |
| "slow" / "performance" / "timeout" / "optimize" | `bidiq-performance-audit` |
| "audit codebase" / "technical debt" / "migration" | `brownfield-discovery` |
| Major enhancement needing planning | `brownfield-fullstack` |

## Creating New Workflows

Workflows can be defined in YAML or Markdown format with YAML frontmatter. See existing workflows for examples.

### Workflow Structure
```yaml
workflow:
  id: unique-workflow-id
  name: Human-readable name
  description: What this workflow does
  type: configuration|development|deployment
  project_types: [feature-addition, bug-fix, etc.]
  sequence:
    - step: step_name
      phase: 1
      phase_name: "Display Name"
      agent: agent-id
      action: what to do
      creates: output file(s)
      notes: detailed instructions
  decision_guidance:
    when_to_use:
      - condition 1
      - condition 2
  handoff_prompts:
    step_complete: "Next step instructions"
```

## Best Practices
1. Keep workflows focused on a single objective
2. Include error handling for each step
3. Provide clear user feedback
4. Make workflows idempotent when possible
5. Document prerequisites and outcomes
6. Use `decision_guidance.when_to_use` for proactive invocation
7. Include `handoff_prompts` for agent transitions
