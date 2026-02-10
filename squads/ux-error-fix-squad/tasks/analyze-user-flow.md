---
task: "Analyze User Flow"
responsavel: "@ux-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_scenario: Detailed user scenario with steps
  - ui_logs: Frontend logs and console output
Saida: |
  - flow_diagram: Visual representation of user flow
  - breakpoints: List of points where UX breaks
Checklist:
  - "[ ] Map complete user journey"
  - "[ ] Document each interaction step"
  - "[ ] Identify expected vs actual behavior"
  - "[ ] Pinpoint exact breakpoints"
  - "[ ] Analyze state at each step"
  - "[ ] Create flow diagram"
  - "[ ] Document UX impact"
  - "[ ] Provide recommendations"
---

# *analyze-user-flow

**Task**: Analyze User Flow
**Agent**: @ux-analyst
**Confidence**: 85%

## Overview

Maps the complete user journey and identifies where the user experience breaks down.

## Input

### user_scenario (object)
Complete user scenario with reproduction steps.

### ui_logs (array)
Frontend logs showing user interactions and state changes.

## Output

### flow_diagram (object)
Visual representation of user flow with breakpoints marked.

### breakpoints (array)
List of specific points where UX fails with severity and impact.

## Origin

Confidence: 85%
