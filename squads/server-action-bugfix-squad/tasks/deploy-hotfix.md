---
task: "Deploy Hotfix"
responsavel: "@deployment-validator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - build_id
  - deployment_target
Saida: |
  - deployment_url
  - rollback_plan
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *deploy-hotfix

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@deployment-validator
*deploy-hotfix
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `build_id` | string | Yes | build id |
| `deployment_target` | string | Yes | deployment target |

## Output

- **deployment_url**: deployment url
- **rollback_plan**: rollback plan

## Origin

Confidence: 90%
