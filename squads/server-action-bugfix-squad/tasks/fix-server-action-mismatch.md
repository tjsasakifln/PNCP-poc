---
task: "Fix Server Action Mismatch"
responsavel: "@hotfix-developer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - action_location
  - fix_strategy
Saida: |
  - updated_code
  - test_plan
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *fix-server-action-mismatch

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@hotfix-developer
*fix-server-action-mismatch
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action_location` | string | Yes | action location |
| `fix_strategy` | string | Yes | fix strategy |

## Output

- **updated_code**: updated code
- **test_plan**: test plan

## Origin

Confidence: 93%
