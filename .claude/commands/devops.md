# /devops — Activate GitHub DevOps Agent

**Agent:** @devops (Gage)

**File:** `.claude/commands/AIOS/agents/devops.md`

This command activates the GitHub DevOps agent for repository operations and CI/CD management.

## Quick Start

```
/devops
```

## Available Commands (In DevOps Mode)

- `*push-changes` - Push commits to remote
- `*create-pr` - Create pull request
- `*merge-pr` - Merge approved PR
- `*ci-cd-config` - Configure CI/CD
- `*release-management` - Manage releases
- `*help` - Show all devops commands
- `*exit` - Exit devops mode

## When to Use DevOps Agent

- Pushing code to remote repository
- Creating and merging pull requests
- CI/CD pipeline setup
- Release management
- Version control operations
- GitHub Actions configuration

## Important Restrictions

- **ONLY @devops can push to remote** (not other agents)
- **ONLY @devops can create PRs** (use for story handoff)
- Developers use **@dev** for local commits only

## Related Agents

- **@dev** - Creates local commits
- **@qa** - Quality gate validation before merge

---

See `.claude/commands/AIOS/agents/devops.md` for complete agent configuration.
