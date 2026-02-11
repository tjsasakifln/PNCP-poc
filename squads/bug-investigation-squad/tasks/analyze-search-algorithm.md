---
task: "Analyze Search Algorithm"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - algorithm_code
  - test_queries
  - expected_results
Saida: |
  - algorithm_analysis
  - bottlenecks
  - quality_metrics
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *analyze-search-algorithm

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*analyze-search-algorithm
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `algorithm_code` | string | Yes | algorithm code |
| `test_queries` | string | Yes | test queries |
| `expected_results` | string | Yes | expected results |

## Output

- **algorithm_analysis**: algorithm analysis
- **bottlenecks**: bottlenecks
- **quality_metrics**: quality metrics

## Origin

Confidence: 88%
