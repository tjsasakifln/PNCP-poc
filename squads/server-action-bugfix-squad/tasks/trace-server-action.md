---
task: "Trace Server Action"
responsavel: "@bug-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - action_id
  - request_context
Saida: |
  - action_location
  - trace_data
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *trace-server-action

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@bug-investigator
*trace-server-action
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action_id` | string | Yes | action id |
| `request_context` | string | Yes | request context |

## Output

- **action_location**: action location
- **trace_data**: trace data

## Origin

Confidence: 88%
