---
task: "Diagnose 404 Root Cause"
responsavel: "@export-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - error_logs
  - api_response
  - request_payload
Saida: |
  - root_cause_analysis
  - affected_endpoints
  - fix_recommendations
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *diagnose-404-root-cause

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@export-investigator
*diagnose-404-root-cause
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `error_logs` | string | Yes | error logs |
| `api_response` | string | Yes | api response |
| `request_payload` | string | Yes | request payload |

## Output

- **root_cause_analysis**: root cause analysis
- **affected_endpoints**: affected endpoints
- **fix_recommendations**: fix recommendations

## Origin

Confidence: 94%
