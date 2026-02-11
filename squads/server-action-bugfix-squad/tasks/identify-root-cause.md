---
task: "Identify Root Cause"
responsavel: "@bug-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - analysis_data
Saida: |
  - root_cause
  - fix_recommendations
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *identify-root-cause

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@bug-investigator
*identify-root-cause
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_data` | string | Yes | analysis data |

## Output

- **root_cause**: root cause
- **fix_recommendations**: fix recommendations

## Origin

Confidence: 90%
