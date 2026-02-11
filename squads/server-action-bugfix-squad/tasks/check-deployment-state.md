---
task: "Check Deployment State"
responsavel: "@bug-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - deployment_id
Saida: |
  - build_info
  - mismatch_detected
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *check-deployment-state

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@bug-investigator
*check-deployment-state
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment_id` | string | Yes | deployment id |

## Output

- **build_info**: build info
- **mismatch_detected**: mismatch detected

## Origin

Confidence: 85%
