---
task: "Replace Getsession"
responsavel: "@auth-security-fixer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - file_paths
  - auth_call_locations
Saida: |
  - modified_files
  - security_improvements
  - test_results
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *replace-getsession

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@auth-security-fixer
*replace-getsession
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_paths` | string | Yes | file paths |
| `auth_call_locations` | string | Yes | auth call locations |

## Output

- **modified_files**: modified files
- **security_improvements**: security improvements
- **test_results**: test results

## Origin

Confidence: 93%
