---
task: "Validate Session Persistence"
responsavel: "@ux-analyst"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - session_config: Configuration for session management
  - test_scenarios: List of scenarios to test
Saida: |
  - persistence_report: Report on persistence behavior
  - recommendations: Recommendations for improvements
Checklist:
  - "[ ] Review session configuration"
  - "[ ] Test localStorage persistence"
  - "[ ] Test sessionStorage persistence"
  - "[ ] Test cookie persistence"
  - "[ ] Test across page refresh"
  - "[ ] Test across navigation"
  - "[ ] Document failures"
  - "[ ] Provide recommendations"
---

# *validate-session-persistence

**Task**: Validate Session Persistence
**Agent**: @ux-analyst
**Confidence**: 84%

## Overview

Validates that session state persists correctly across various scenarios.

## Input

### session_config (object)
Current session and storage configuration.

### test_scenarios (array)
List of scenarios to test (refresh, navigation, etc.).

## Output

### persistence_report (object)
Detailed report on what persists and what doesn't.

### recommendations (array)
Recommendations for improving persistence.

## Origin

Confidence: 84%
