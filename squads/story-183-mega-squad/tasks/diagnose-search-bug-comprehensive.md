---
task: "Diagnose Search Bug Comprehensive"
responsavel: "@backend-dev-1"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - story-183-docs
  - pncp_client.py-source
  - recent-logs
Saida: |
  - root-cause-confirmed
  - fix-plan
  - performance-baseline
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *diagnose-search-bug-comprehensive

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@backend-dev-1
*diagnose-search-bug-comprehensive
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `story-183-docs` | string | Yes | story-183-docs |
| `pncp_client.py-source` | string | Yes | pncp client.py-source |
| `recent-logs` | string | Yes | recent-logs |

## Output

- **root-cause-confirmed**: root-cause-confirmed
- **fix-plan**: fix-plan
- **performance-baseline**: performance-baseline

## Origin

Confidence: 98%
