---
task: "Consolidate Findings"
responsavel: "@lead-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - ux_findings: Findings from UX analyst
  - backend_findings: Findings from backend debugger
  - qa_findings: Findings from QA validator
Saida: |
  - consolidated_report: Combined analysis of all findings
  - root_causes: List of identified root causes
Checklist:
  - "[ ] Collect findings from all specialist agents"
  - "[ ] Identify common patterns across findings"
  - "[ ] Connect related issues"
  - "[ ] Identify root causes"
  - "[ ] Validate hypotheses against evidence"
  - "[ ] Create consolidated report"
  - "[ ] Document cause-effect relationships"
  - "[ ] Prepare for fix planning"
---

# *consolidate-findings

**Task**: Consolidate Findings
**Agent**: @lead-investigator
**Confidence**: 92%

## Overview

Consolidates findings from UX, backend, and QA investigations into a unified root cause analysis.

## Input Parameters

### ux_findings (object)
```json
{
  "breakpoints": [
    "State cleared on route change",
    "localStorage not persisted"
  ],
  "flow_diagram": "...",
  "recommendations": ["Implement state persistence hook"]
}
```

### backend_findings (object)
```json
{
  "issues": [
    "Missing db.commit() in save_history",
    "Transaction not wrapped properly",
    "Auth token expired causing 401"
  ],
  "trace": "...",
  "recommendations": ["Use transaction context manager"]
}
```

### qa_findings (object)
```json
{
  "test_results": {
    "passed": 5,
    "failed": 3
  },
  "failures": [
    "search_history empty after search",
    "balance deducted but search failed",
    "state lost after navigation"
  ]
}
```

## Output

### consolidated_report (object)
```json
{
  "summary": "Search results not persisted due to missing transaction commit and frontend state loss",
  "affected_systems": ["backend/search", "frontend/state", "database/transactions"],
  "severity": "CRITICAL",
  "root_causes": ["..."]
}
```

### root_causes (array)
```json
[
  {
    "cause": "Missing transaction commit",
    "evidence": ["Backend trace shows no COMMIT", "Database has no records"],
    "impact": "Search history never saved",
    "fix": "Add explicit commit or use context manager"
  }
]
```

## Origin

Confidence: 92%
