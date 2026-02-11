---
task: "Verify Export Fix"
responsavel: "@export-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - production_logs
  - user_reports
Saida: |
  - verification_status
  - metrics
  - rollback_needed
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *verify-export-fix

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@export-investigator
*verify-export-fix
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `production_logs` | string | Yes | production logs |
| `user_reports` | string | Yes | user reports |

## Output

- **verification_status**: verification status
- **metrics**: metrics
- **rollback_needed**: rollback needed

## Origin

Confidence: 87%
