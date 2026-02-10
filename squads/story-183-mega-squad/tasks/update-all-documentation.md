---
task: "Update All Documentation"
responsavel: "@docs-specialist"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - story-183
  - implementation-details
  - test-results
Saida: |
  - updated-story
  - changelog-entry
  - user-communication
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *update-all-documentation

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@docs-specialist
*update-all-documentation
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `story-183` | string | Yes | story-183 |
| `implementation-details` | string | Yes | implementation-details |
| `test-results` | string | Yes | test-results |

## Output

- **updated-story**: updated-story
- **changelog-entry**: changelog-entry
- **user-communication**: user-communication

## Origin

Confidence: 90%
