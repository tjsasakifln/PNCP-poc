---
task: "Trace Save Flow"
responsavel: "@persistence-detective"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_id
  - search_params
  - session_id
Saida: |
  - persistence_trace
  - database_operations
  - state_changes
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *trace-save-flow

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@persistence-detective
*trace-save-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | user id |
| `search_params` | string | Yes | search params |
| `session_id` | string | Yes | session id |

## Output

- **persistence_trace**: persistence trace
- **database_operations**: database operations
- **state_changes**: state changes

## Origin

Confidence: 91%
