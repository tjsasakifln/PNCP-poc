---
task: "Trace Export Path"
responsavel: "@export-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_id
  - export_request_id
  - timestamp
Saida: |
  - execution_trace
  - api_calls_log
  - error_stack
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *trace-export-path

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@export-investigator
*trace-export-path
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | user id |
| `export_request_id` | string | Yes | export request id |
| `timestamp` | string | Yes | timestamp |

## Output

- **execution_trace**: execution trace
- **api_calls_log**: api calls log
- **error_stack**: error stack

## Origin

Confidence: 92%
