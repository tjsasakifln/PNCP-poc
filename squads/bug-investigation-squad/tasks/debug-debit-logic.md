---
task: "Debug Debit Logic"
responsavel: "@billing-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - code_analysis
  - edge_cases
Saida: |
  - logic_bugs
  - race_conditions
  - timing_issues
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *debug-debit-logic

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@billing-auditor
*debug-debit-logic
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code_analysis` | string | Yes | code analysis |
| `edge_cases` | string | Yes | edge cases |

## Output

- **logic_bugs**: logic bugs
- **race_conditions**: race conditions
- **timing_issues**: timing issues

## Origin

Confidence: 91%
