---
task: "Monitor Production Health"
responsavel: "@devops-engineer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - deployment-complete
  - monitoring-dashboards
Saida: |
  - health-report
  - metrics-baseline
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *monitor-production-health

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@devops-engineer
*monitor-production-health
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `deployment-complete` | string | Yes | deployment-complete |
| `monitoring-dashboards` | string | Yes | monitoring-dashboards |

## Output

- **health-report**: health-report
- **metrics-baseline**: metrics-baseline

## Origin

Confidence: 95%
