---
task: "Test Error Scenarios"
responsavel: "@error-message-improver"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - test_scenarios
  - error_conditions
Saida: |
  - test_results
  - screenshots
  - validation_report
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *test-error-scenarios

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@error-message-improver
*test-error-scenarios
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_scenarios` | string | Yes | test scenarios |
| `error_conditions` | string | Yes | error conditions |

## Output

- **test_results**: test results
- **screenshots**: screenshots
- **validation_report**: validation report

## Origin

Confidence: 87%
