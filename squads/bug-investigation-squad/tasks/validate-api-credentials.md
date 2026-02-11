---
task: "Validate Api Credentials"
responsavel: "@export-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - google_sheets_config
  - oauth_tokens
Saida: |
  - validation_result
  - token_status
  - expiration_info
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *validate-api-credentials

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@export-investigator
*validate-api-credentials
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `google_sheets_config` | string | Yes | google sheets config |
| `oauth_tokens` | string | Yes | oauth tokens |

## Output

- **validation_result**: validation result
- **token_status**: token status
- **expiration_info**: expiration info

## Origin

Confidence: 90%
