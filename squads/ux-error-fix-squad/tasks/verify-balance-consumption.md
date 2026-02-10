---
task: "Verify Balance Consumption"
responsavel: "@backend-debugger"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_id: User identifier to trace
  - search_event: Search event to analyze
Saida: |
  - balance_trace: Complete trace of balance deduction flow
  - consumption_status: Status of balance consumption (success/partial/failed)
Checklist:
  - "[ ] Query user balance history"
  - "[ ] Trace balance deduction call"
  - "[ ] Check transaction status"
  - "[ ] Verify commit/rollback"
  - "[ ] Check for double deduction"
  - "[ ] Verify refund logic"
  - "[ ] Document atomicity issues"
  - "[ ] Suggest transaction improvements"
---

# *verify-balance-consumption

**Task**: Verify Balance Consumption
**Agent**: @backend-debugger
**Confidence**: 90%

## Overview

Traces balance deduction flow to verify correct implementation and identify issues.

## Input

### user_id (string)
User identifier to trace balance operations.

### search_event (object)
Specific search event to analyze balance deduction.

## Output

### balance_trace (object)
Complete trace of balance deduction from call to database commit.

### consumption_status (string)
Status: "SUCCESS", "PARTIAL", "FAILED", "DOUBLE_DEDUCTED"

## Origin

Confidence: 90%
