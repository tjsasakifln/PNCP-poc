---
task: "Audit Credit Transactions"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - transaction_logs
  - expected_debits
Saida: |
  - discrepancies
  - missing_debits
  - double_charges
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *audit-credit-transactions

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*audit-credit-transactions
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `transaction_logs` | string | Yes | transaction logs |
| `expected_debits` | string | Yes | expected debits |

## Output

- **discrepancies**: discrepancies
- **missing_debits**: missing debits
- **double_charges**: double charges

## Origin

Confidence: 92%
