---
task: "Verify Search Quality"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - test_queries
  - quality_metrics
Saida: |
  - quality_report
  - precision_recall_f1
  - user_satisfaction
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *verify-search-quality

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*verify-search-quality
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_queries` | string | Yes | test queries |
| `quality_metrics` | string | Yes | quality metrics |

## Output

- **quality_report**: quality report
- **precision_recall_f1**: precision recall f1
- **user_satisfaction**: user satisfaction

## Origin

Confidence: 87%
