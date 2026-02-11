---
task: "Implement Cache Bust"
responsavel: "@hotfix-developer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - cache_strategy
Saida: |
  - cache_config
  - invalidation_logic
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *implement-cache-bust

Task generated from squad design blueprint for server-action-bugfix-squad.

## Usage

```
@hotfix-developer
*implement-cache-bust
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cache_strategy` | string | Yes | cache strategy |

## Output

- **cache_config**: cache config
- **invalidation_logic**: invalidation logic

## Origin

Confidence: 82%
