---
task: "Verify Header Display"
responsavel: "@persistence-detective"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - ui_snapshots
  - user_feedback
Saida: |
  - display_verification
  - browser_compatibility
  - accessibility_check
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *verify-header-display

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@persistence-detective
*verify-header-display
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ui_snapshots` | string | Yes | ui snapshots |
| `user_feedback` | string | Yes | user feedback |

## Output

- **display_verification**: display verification
- **browser_compatibility**: browser compatibility
- **accessibility_check**: accessibility check

## Origin

Confidence: 88%
