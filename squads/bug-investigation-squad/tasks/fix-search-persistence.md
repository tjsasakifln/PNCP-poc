---
task: "Fix Search Persistence"
responsavel: "@persistence-detective"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - debug_analysis
  - fix_strategy
Saida: |
  - patched_code
  - migration_script
  - test_results
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *fix-search-persistence

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@persistence-detective
*fix-search-persistence
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `debug_analysis` | string | Yes | debug analysis |
| `fix_strategy` | string | Yes | fix strategy |

## Output

- **patched_code**: patched code
- **migration_script**: migration script
- **test_results**: test results

## Origin

Confidence: 86%
