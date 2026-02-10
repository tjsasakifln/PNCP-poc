---
task: "Checkpoint Diagnostic Complete"
responsavel: "@orchestrator-agent"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - diagnostic-reports
Saida: |
  - go-no-go-decision
  - blocker-resolution
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *checkpoint-diagnostic-complete

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@orchestrator-agent
*checkpoint-diagnostic-complete
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `diagnostic-reports` | string | Yes | diagnostic-reports |

## Output

- **go-no-go-decision**: go-no-go-decision
- **blocker-resolution**: blocker-resolution

## Origin

Confidence: 95%
