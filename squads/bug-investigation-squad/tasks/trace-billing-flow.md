---
task: "Trace Billing Flow"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_id
  - search_count
  - current_balance
Saida: |
  - billing_trace
  - debit_operations
  - balance_changes
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *trace-billing-flow

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*trace-billing-flow
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | Yes | user id |
| `search_count` | string | Yes | search count |
| `current_balance` | string | Yes | current balance |

## Output

- **billing_trace**: billing trace
- **debit_operations**: debit operations
- **balance_changes**: balance changes

## Origin

Confidence: 90%
