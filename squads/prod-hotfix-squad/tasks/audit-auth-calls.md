---
task: "Audit Auth Calls"
responsavel: "@auth-security-fixer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - codebase_paths
  - search_patterns
Saida: |
  - auth_call_locations
  - security_issues_count
  - recommended_fixes
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *audit-auth-calls

Task generated from squad design blueprint for prod-hotfix-squad.

## Usage

```
@auth-security-fixer
*audit-auth-calls
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `codebase_paths` | string | Yes | codebase paths |
| `search_patterns` | string | Yes | search patterns |

## Output

- **auth_call_locations**: auth call locations
- **security_issues_count**: security issues count
- **recommended_fixes**: recommended fixes

## Origin

Confidence: 95%
