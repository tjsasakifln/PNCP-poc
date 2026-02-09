---
task: "Audit Error Messages"
responsavel: "@error-message-improver"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - backend_exceptions
  - frontend_error_handlers
Saida: |
  - error_flow_map
  - ux_issues_list
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *audit-error-messages

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@error-message-improver
*audit-error-messages
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `backend_exceptions` | string | Yes | backend exceptions |
| `frontend_error_handlers` | string | Yes | frontend error handlers |

## Output

- **error_flow_map**: error flow map
- **ux_issues_list**: ux issues list

## Origin

Confidence: 92%
