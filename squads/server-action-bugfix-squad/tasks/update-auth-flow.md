---
task: "Update Auth Flow"
responsavel: "@hotfix-developer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - current_flow
  - issues
Saida: |
  - updated_flow
  - migration_notes
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *update-auth-flow

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@hotfix-developer
*update-auth-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_flow` | string | Yes | current flow |
| `issues` | string | Yes | issues |

## Output

- **updated_flow**: updated flow
- **migration_notes**: migration notes

## Origin

Confidence: 87%
