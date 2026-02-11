---
task: "Validate Auth Flow"
responsavel: "@deployment-validator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - auth_scenarios
Saida: |
  - validation_report
  - issues_found
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-auth-flow

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@deployment-validator
*validate-auth-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `auth_scenarios` | string | Yes | auth scenarios |

## Output

- **validation_report**: validation report
- **issues_found**: issues found

## Origin

Confidence: 88%
