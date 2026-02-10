---
task: "Qa Lead Final Validation"
responsavel: "@qa-lead"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - all-test-reports
  - code-review-report
  - security-audit
Saida: |
  - quality-gate-decision
  - deployment-approval
  - risk-assessment
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *qa-lead-final-validation

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@qa-lead
*qa-lead-final-validation
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `all-test-reports` | string | Yes | all-test-reports |
| `code-review-report` | string | Yes | code-review-report |
| `security-audit` | string | Yes | security-audit |

## Output

- **quality-gate-decision**: quality-gate-decision
- **deployment-approval**: deployment-approval
- **risk-assessment**: risk-assessment

## Origin

Confidence: 98%
