---
task: "Audit Llm Decisions"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - llm_prompts
  - decision_logs
  - ground_truth
Saida: |
  - decision_accuracy
  - prompt_issues
  - model_drift
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *audit-llm-decisions

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*audit-llm-decisions
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `llm_prompts` | string | Yes | llm prompts |
| `decision_logs` | string | Yes | decision logs |
| `ground_truth` | string | Yes | ground truth |

## Output

- **decision_accuracy**: decision accuracy
- **prompt_issues**: prompt issues
- **model_drift**: model drift

## Origin

Confidence: 86%
