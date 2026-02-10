---
task: "Validate Acceptance Criteria"
responsavel: "@pm-coordinator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - story-183-acceptance-criteria
  - implementation-results
  - test-reports
Saida: |
  - criteria-validation-report
  - stakeholder-approval
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-acceptance-criteria

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@pm-coordinator
*validate-acceptance-criteria
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `story-183-acceptance-criteria` | string | Yes | story-183-acceptance-criteria |
| `implementation-results` | string | Yes | implementation-results |
| `test-reports` | string | Yes | test-reports |

## Output

- **criteria-validation-report**: criteria-validation-report
- **stakeholder-approval**: stakeholder-approval

## Origin

Confidence: 96%
