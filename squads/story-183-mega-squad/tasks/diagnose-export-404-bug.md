---
task: "Diagnose Export 404 Bug"
responsavel: "@fullstack-dev-1"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - story-183-docs
  - export-route-source
  - backend-logs
Saida: |
  - root-cause-identified
  - fix-strategy
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *diagnose-export-404-bug

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@fullstack-dev-1
*diagnose-export-404-bug
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `story-183-docs` | string | Yes | story-183-docs |
| `export-route-source` | string | Yes | export-route-source |
| `backend-logs` | string | Yes | backend-logs |

## Output

- **root-cause-identified**: root-cause-identified
- **fix-strategy**: fix-strategy

## Origin

Confidence: 96%
