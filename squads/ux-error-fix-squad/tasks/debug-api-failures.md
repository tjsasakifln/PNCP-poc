---
task: "Debug API Failures"
responsavel: "@backend-debugger"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - api_logs: API request and response logs
  - failed_requests: List of failed API requests
Saida: |
  - failure_root_causes: Root causes of API failures
  - fix_suggestions: Suggested fixes for each failure type
Checklist:
  - "[ ] Review failed API requests"
  - "[ ] Analyze error responses"
  - "[ ] Trace request flow"
  - "[ ] Check error handling"
  - "[ ] Identify common patterns"
  - "[ ] Test reproduction"
  - "[ ] Document root causes"
  - "[ ] Suggest fixes"
---

# *debug-api-failures

**Task**: Debug API Failures
**Agent**: @backend-debugger
**Confidence**: 89%

## Overview

Debugs API failures to identify root causes and suggest fixes.

## Input

### api_logs (array)
API request and response logs with errors.

### failed_requests (array)
List of specific failed requests to investigate.

## Output

### failure_root_causes (array)
Root causes of API failures with evidence.

### fix_suggestions (array)
Specific suggestions for fixing each failure type.

## Origin

Confidence: 89%
