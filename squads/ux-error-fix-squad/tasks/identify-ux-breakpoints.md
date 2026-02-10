---
task: "Identify UX Breakpoints"
responsavel: "@ux-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - user_journey: Complete user journey map
  - session_data: Session and storage data
Saida: |
  - breakpoint_list: List of UX breakpoints with severity
  - ux_issues: Detailed description of each UX issue
Checklist:
  - "[ ] Review user journey"
  - "[ ] Identify friction points"
  - "[ ] Classify issue severity"
  - "[ ] Document user impact"
  - "[ ] Analyze root causes"
  - "[ ] Create breakpoint list"
  - "[ ] Prioritize by user impact"
  - "[ ] Provide fix recommendations"
---

# *identify-ux-breakpoints

**Task**: Identify UX Breakpoints
**Agent**: @ux-analyst
**Confidence**: 86%

## Overview

Identifies specific points where the user experience breaks and classifies by severity.

## Input

### user_journey (object)
Mapped user journey with all interactions.

### session_data (object)
Session storage, localStorage, and cookie data.

## Output

### breakpoint_list (array)
List of UX breakpoints with location and severity.

### ux_issues (array)
Detailed description of each UX issue with user impact.

## Origin

Confidence: 86%
