---
task: "Validate Auth Security"
responsavel: "@auth-security-fixer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - modified_files
Saida: |
  - validation_results
  - remaining_issues
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-auth-security

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@auth-security-fixer
*validate-auth-security
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `modified_files` | string | Yes | modified files |

## Output

- **validation_results**: validation results
- **remaining_issues**: remaining issues

## Origin

Confidence: 90%
