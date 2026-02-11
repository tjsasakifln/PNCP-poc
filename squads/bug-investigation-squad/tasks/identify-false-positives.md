---
task: "Identify False Positives"
responsavel: "@search-quality-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - search_results
  - relevance_labels
Saida: |
  - false_positive_list
  - patterns
  - root_causes
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *identify-false-positives

Task generated from squad design blueprint for bug-investigation-squad.

## Usage

```
@search-quality-analyst
*identify-false-positives
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_results` | string | Yes | search results |
| `relevance_labels` | string | Yes | relevance labels |

## Output

- **false_positive_list**: false positive list
- **patterns**: patterns
- **root_causes**: root causes

## Origin

Confidence: 90%
