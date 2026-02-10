---
task: "Trace Database Writes"
responsavel: "@backend-debugger"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - transaction_logs: Database transaction logs
  - table_names: List of tables to investigate
Saida: |
  - write_trace: Trace of all write operations
  - missing_writes: List of expected writes that didn't occur
Checklist:
  - "[ ] Review transaction logs"
  - "[ ] Trace BEGIN statements"
  - "[ ] Trace INSERT/UPDATE operations"
  - "[ ] Trace COMMIT/ROLLBACK statements"
  - "[ ] Identify missing commits"
  - "[ ] Check constraint violations"
  - "[ ] Document missing writes"
  - "[ ] Suggest transaction improvements"
---

# *trace-database-writes

**Task**: Trace Database Writes
**Agent**: @backend-debugger
**Confidence**: 88%

## Overview

Traces database write operations to identify missing commits, rollbacks, or failed inserts.

## Input

### transaction_logs (array)
Database transaction logs with BEGIN, INSERT, COMMIT, ROLLBACK statements.

### table_names (array)
List of tables to focus investigation on.

## Output

### write_trace (object)
Complete trace of write operations with transaction boundaries.

### missing_writes (array)
List of expected writes that didn't occur or weren't committed.

## Origin

Confidence: 88%
