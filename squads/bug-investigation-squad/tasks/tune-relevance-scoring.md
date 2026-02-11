---
task: "Tune Relevance Scoring"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - scoring_weights
  - training_data
Saida: |
  - optimized_weights
  - precision_improvement
  - recall_improvement
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *tune-relevance-scoring

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*tune-relevance-scoring
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scoring_weights` | string | Yes | scoring weights |
| `training_data` | string | Yes | training data |

## Output

- **optimized_weights**: optimized weights
- **precision_improvement**: precision improvement
- **recall_improvement**: recall improvement

## Origin

Confidence: 84%
