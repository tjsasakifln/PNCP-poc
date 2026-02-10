---
task: "Validate Export Fix Comprehensive"
responsavel: "@qa-export"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - implemented-fix
  - oauth-scenarios
Saida: |
  - validation-report
  - oauth-flow-tested
  - edge-cases-covered
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-export-fix-comprehensive

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@qa-export
*validate-export-fix-comprehensive
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `implemented-fix` | string | Yes | implemented-fix |
| `oauth-scenarios` | string | Yes | oauth-scenarios |

## Output

- **validation-report**: validation-report
- **oauth-flow-tested**: oauth-flow-tested
- **edge-cases-covered**: edge-cases-covered

## Origin

Confidence: 95%
