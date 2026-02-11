---
task: "Fix Billing Sync"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - audit_results
  - fix_strategy
Saida: |
  - patched_billing_code
  - reconciliation_script
  - test_results
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *fix-billing-sync

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*fix-billing-sync
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audit_results` | string | Yes | audit results |
| `fix_strategy` | string | Yes | fix strategy |

## Output

- **patched_billing_code**: patched billing code
- **reconciliation_script**: reconciliation script
- **test_results**: test results

## Origin

Confidence: 87%
