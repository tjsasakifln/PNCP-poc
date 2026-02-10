---
task: "Trace Navigation State"
responsavel: "@ux-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - navigation_path: Array of navigation steps
  - state_snapshots: State at each navigation point
Saida: |
  - state_trace: Complete trace of state changes
  - missing_persistence: List of state that failed to persist
Checklist:
  - "[ ] Trace state through navigation flow"
  - "[ ] Document state at each route"
  - "[ ] Identify state loss points"
  - "[ ] Check localStorage writes"
  - "[ ] Verify state restoration"
  - "[ ] Analyze persistence mechanisms"
  - "[ ] Document missing persistence"
  - "[ ] Recommend persistence strategy"
---

# *trace-navigation-state

**Task**: Trace Navigation State
**Agent**: @ux-analyst
**Confidence**: 87%

## Overview

Traces state changes during page navigation to identify where state is lost.

## Input

### navigation_path (array)
Sequence of routes user navigated through.

### state_snapshots (array)
State captured at each navigation point.

## Output

### state_trace (object)
Complete trace showing state evolution through navigation.

### missing_persistence (array)
List of state fields that failed to persist with root causes.

## Origin

Confidence: 87%
