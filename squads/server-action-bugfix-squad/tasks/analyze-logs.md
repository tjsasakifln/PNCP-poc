---
task: "Analyze Logs"
responsavel: "@bug-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - log_source
  - time_range
Saida: |
  - error_patterns
  - frequency
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *analyze-logs

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@bug-investigator
*analyze-logs
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `log_source` | string | Yes | log source |
| `time_range` | string | Yes | time range |

## Output

- **error_patterns**: error patterns
- **frequency**: frequency

## Origin

Confidence: 92%
