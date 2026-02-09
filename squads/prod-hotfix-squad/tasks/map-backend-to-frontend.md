---
task: "Map Backend To Frontend"
responsavel: "@error-message-improver"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - backend_error_codes
  - frontend_components
Saida: |
  - error_mapping_table
  - missing_handlers
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *map-backend-to-frontend

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@error-message-improver
*map-backend-to-frontend
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `backend_error_codes` | string | Yes | backend error codes |
| `frontend_components` | string | Yes | frontend components |

## Output

- **error_mapping_table**: error mapping table
- **missing_handlers**: missing handlers

## Origin

Confidence: 88%
