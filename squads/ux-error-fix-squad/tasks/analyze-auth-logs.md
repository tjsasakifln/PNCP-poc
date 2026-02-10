---
task: "Analyze Auth Logs"
responsavel: "@backend-debugger"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - auth_logs: Authentication and authorization logs
  - timestamp_range: Time range to analyze
Saida: |
  - auth_issues: List of authentication issues found
  - token_lifecycle: Analysis of token creation, validation, expiration
Checklist:
  - "[ ] Filter logs by timestamp range"
  - "[ ] Identify auth failures (401, 403)"
  - "[ ] Trace token lifecycle"
  - "[ ] Check token expiration patterns"
  - "[ ] Analyze refresh token usage"
  - "[ ] Identify session inconsistencies"
  - "[ ] Document auth flow issues"
  - "[ ] Provide fix recommendations"
---

# *analyze-auth-logs

**Task**: Analyze Auth Logs
**Agent**: @backend-debugger
**Confidence**: 91%

## Overview

Analyzes authentication logs to identify token issues, auth failures, and session inconsistencies.

## Input

### auth_logs (array)
Authentication and authorization log entries.

### timestamp_range (object)
Start and end timestamps for analysis period.

## Output

### auth_issues (array)
List of authentication issues with severity and frequency.

### token_lifecycle (object)
Analysis of token creation, validation, refresh, and expiration patterns.

## Origin

Confidence: 91%
