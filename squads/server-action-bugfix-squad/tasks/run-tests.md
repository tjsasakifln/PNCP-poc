---
task: "Run Tests"
responsavel: "@deployment-validator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - test_suite
Saida: |
  - test_results
  - coverage
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *run-tests

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@deployment-validator
*run-tests
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_suite` | string | Yes | test suite |

## Output

- **test_results**: test results
- **coverage**: coverage

## Origin

Confidence: 91%
