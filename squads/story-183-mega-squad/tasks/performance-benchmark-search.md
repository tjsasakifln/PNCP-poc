---
task: "Performance Benchmark Search"
responsavel: "@performance-engineer"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - updated-code
  - test-scenarios
Saida: |
  - performance-report
  - memory-analysis
  - bottleneck-identification
Checklist:
  - "[ ] Validate input parameters"
  - "[ ] Execute main logic"
  - "[ ] Format output"
  - "[ ] Return result"
---

# *performance-benchmark-search

Task generated from squad design blueprint for story-183-mega-squad.

## Usage

```
@performance-engineer
*performance-benchmark-search
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `updated-code` | string | Yes | updated-code |
| `test-scenarios` | string | Yes | test-scenarios |

## Output

- **performance-report**: performance-report
- **memory-analysis**: memory-analysis
- **bottleneck-identification**: bottleneck-identification

## Origin

Confidence: 92%
