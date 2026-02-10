---
task: "Prepare Deployment Package"
responsavel: "@devops-engineer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - validated-fixes
  - qa-approval
  - security-approval
Saida: |
  - deployment-plan
  - rollback-procedure
  - monitoring-config
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *prepare-deployment-package

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@devops-engineer
*prepare-deployment-package
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `validated-fixes` | string | Yes | validated-fixes |
| `qa-approval` | string | Yes | qa-approval |
| `security-approval` | string | Yes | security-approval |

## Output

- **deployment-plan**: deployment-plan
- **rollback-procedure**: rollback-procedure
- **monitoring-config**: monitoring-config

## Origin

Confidence: 98%
