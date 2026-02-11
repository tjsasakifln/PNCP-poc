---
task: "Identify False Negatives"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - missed_results
  - expected_matches
Saida: |
  - false_negative_list
  - recall_issues
  - filtering_bugs
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *identify-false-negatives

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*identify-false-negatives
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `missed_results` | string | Yes | missed results |
| `expected_matches` | string | Yes | expected matches |

## Output

- **false_negative_list**: false negative list
- **recall_issues**: recall issues
- **filtering_bugs**: filtering bugs

## Origin

Confidence: 89%
