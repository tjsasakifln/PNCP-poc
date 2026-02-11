---
task: "Verify Balance Accuracy"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_balances
  - transaction_history
Saida: |
  - accuracy_report
  - correction_needed
  - audit_trail
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *verify-balance-accuracy

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*verify-balance-accuracy
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_balances` | string | Yes | user balances |
| `transaction_history` | string | Yes | transaction history |

## Output

- **accuracy_report**: accuracy report
- **correction_needed**: correction needed
- **audit_trail**: audit trail

## Origin

Confidence: 89%
