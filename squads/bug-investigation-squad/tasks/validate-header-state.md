---
task: "Validate Header State"
responsavel: "@persistence-detective"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_session
  - frontend_state
  - backend_state
Saida: |
  - state_comparison
  - sync_issues
  - missing_data
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-header-state

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@persistence-detective
*validate-header-state
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_session` | string | Yes | user session |
| `frontend_state` | string | Yes | frontend state |
| `backend_state` | string | Yes | backend state |

## Output

- **state_comparison**: state comparison
- **sync_issues**: sync issues
- **missing_data**: missing data

## Origin

Confidence: 89%
