---
task: "Comprehensive Code Review"
responsavel: "@code-reviewer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - implemented-fixes
  - AIOS-coding-standards
  - existing-patterns
Saida: |
  - code-review-report
  - quality-score
  - improvement-recommendations
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *comprehensive-code-review

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@code-reviewer
*comprehensive-code-review
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `implemented-fixes` | string | Yes | implemented-fixes |
| `AIOS-coding-standards` | string | Yes | AIOS-coding-standards |
| `existing-patterns` | string | Yes | existing-patterns |

## Output

- **code-review-report**: code-review-report
- **quality-score**: quality-score
- **improvement-recommendations**: improvement-recommendations

## Origin

Confidence: 97%
