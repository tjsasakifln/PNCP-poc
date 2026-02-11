---
task: "Debug Database Writes"
responsavel: "@persistence-detective"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - query_logs
  - transaction_history
Saida: |
  - write_failures
  - constraint_violations
  - deadlock_analysis
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *debug-database-writes

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@persistence-detective
*debug-database-writes
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_logs` | string | Yes | query logs |
| `transaction_history` | string | Yes | transaction history |

## Output

- **write_failures**: write failures
- **constraint_violations**: constraint violations
- **deadlock_analysis**: deadlock analysis

## Origin

Confidence: 93%
