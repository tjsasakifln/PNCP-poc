---
task: "Test Export Flow"
responsavel: "@export-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - test_scenarios
  - sample_data
Saida: |
  - test_results
  - success_rate
  - regression_check
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *test-export-flow

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@export-investigator
*test-export-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_scenarios` | string | Yes | test scenarios |
| `sample_data` | string | Yes | sample data |

## Output

- **test_results**: test results
- **success_rate**: success rate
- **regression_check**: regression check

## Origin

Confidence: 85%
