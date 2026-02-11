---
task: "Monitor Production"
responsavel: "@deployment-validator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - metrics
  - duration
Saida: |
  - status_report
  - alerts
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *monitor-production

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@deployment-validator
*monitor-production
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `metrics` | string | Yes | metrics |
| `duration` | string | Yes | duration |

## Output

- **status_report**: status report
- **alerts**: alerts

## Origin

Confidence: 86%
