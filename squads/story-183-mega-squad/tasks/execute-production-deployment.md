---
task: "Execute Production Deployment"
responsavel: "@devops-engineer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - deployment-package
  - approval
Saida: |
  - deployed-version
  - deployment-logs
  - smoke-test-results
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *execute-production-deployment

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@devops-engineer
*execute-production-deployment
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment-package` | string | Yes | deployment-package |
| `approval` | string | Yes | approval |

## Output

- **deployed-version**: deployed-version
- **deployment-logs**: deployment-logs
- **smoke-test-results**: smoke-test-results

## Origin

Confidence: 98%
