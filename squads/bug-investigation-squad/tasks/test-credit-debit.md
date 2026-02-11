---
task: "Test Credit Debit"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - test_scenarios
  - concurrent_users
Saida: |
  - debit_accuracy
  - race_condition_check
  - consistency_verification
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *test-credit-debit

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*test-credit-debit
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_scenarios` | string | Yes | test scenarios |
| `concurrent_users` | string | Yes | concurrent users |

## Output

- **debit_accuracy**: debit accuracy
- **race_condition_check**: race condition check
- **consistency_verification**: consistency verification

## Origin

Confidence: 85%
