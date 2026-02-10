---
task: "Security Audit Comprehensive"
responsavel: "@security-auditor"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - implemented-fixes
  - oauth-flow
  - api-endpoints
Saida: |
  - security-audit-report
  - vulnerability-assessment
  - compliance-check
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *security-audit-comprehensive

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@security-auditor
*security-audit-comprehensive
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `implemented-fixes` | string | Yes | implemented-fixes |
| `oauth-flow` | string | Yes | oauth-flow |
| `api-endpoints` | string | Yes | api-endpoints |

## Output

- **security-audit-report**: security-audit-report
- **vulnerability-assessment**: vulnerability-assessment
- **compliance-check**: compliance-check

## Origin

Confidence: 94%
