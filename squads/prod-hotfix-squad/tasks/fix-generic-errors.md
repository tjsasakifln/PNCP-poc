---
task: "Fix Generic Errors"
responsavel: "@error-message-improver"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - error_mapping_table
  - ux_guidelines
Saida: |
  - improved_messages
  - user_facing_text
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *fix-generic-errors

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@error-message-improver
*fix-generic-errors
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `error_mapping_table` | string | Yes | error mapping table |
| `ux_guidelines` | string | Yes | ux guidelines |

## Output

- **improved_messages**: improved messages
- **user_facing_text**: user facing text

## Origin

Confidence: 90%
