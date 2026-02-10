---
task: "Run Regression Suite Complete"
responsavel: "@test-automation-engineer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - all-tests
  - codebase
Saida: |
  - regression-report
  - coverage-report-100-percent
  - performance-metrics
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *run-regression-suite-complete

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@test-automation-engineer
*run-regression-suite-complete
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `all-tests` | string | Yes | all-tests |
| `codebase` | string | Yes | codebase |

## Output

- **regression-report**: regression-report
- **coverage-report-100-percent**: coverage-report-100-percent
- **performance-metrics**: performance-metrics

## Origin

Confidence: 95%
