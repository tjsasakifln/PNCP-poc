---
task: "Prioritize Fixes"
responsavel: "@lead-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - findings_list: List of all findings from investigation
  - impact_assessment: Assessment of user and business impact
Saida: |
  - prioritized_fixes: Ordered list of fixes by priority
  - timeline: Implementation timeline for each fix
Checklist:
  - "[ ] Review all findings from specialist agents"
  - "[ ] Assess user impact for each issue"
  - "[ ] Assess business impact for each issue"
  - "[ ] Evaluate technical complexity"
  - "[ ] Assign priority levels (P0-P3)"
  - "[ ] Create implementation timeline"
  - "[ ] Identify dependencies between fixes"
  - "[ ] Document rationale for prioritization"
---

# *prioritize-fixes

**Task**: Prioritize Fixes
**Agent**: @lead-investigator
**Confidence**: 88%

## Overview

Prioritizes bug fixes based on findings, impact assessment, and technical complexity. Creates an ordered implementation plan with timeline.

## Input Parameters

### findings_list (array)
```json
[
  {
    "issue": "Transaction not committed",
    "source": "backend-debugger",
    "severity": "critical",
    "affected_feature": "search_history"
  },
  {
    "issue": "State cleared on navigation",
    "source": "ux-analyst",
    "severity": "high",
    "affected_feature": "search_results"
  }
]
```

### impact_assessment (object)
```json
{
  "user_impact": {
    "data_loss": "HIGH",
    "frustration_level": "HIGH",
    "affected_users": "100%"
  },
  "business_impact": {
    "revenue_loss": "MEDIUM",
    "support_tickets": "HIGH",
    "reputation_damage": "HIGH"
  }
}
```

## Output

### prioritized_fixes (array)
```json
[
  {
    "priority": "P0",
    "issue": "Transaction not committed",
    "fix": "Add explicit commit to search history save",
    "estimated_effort": "2 hours",
    "risk": "LOW"
  },
  {
    "priority": "P0",
    "issue": "Balance deducted without rollback",
    "fix": "Wrap balance deduction in transaction",
    "estimated_effort": "3 hours",
    "risk": "MEDIUM"
  }
]
```

### timeline (object)
```json
{
  "sprint_1": {
    "duration": "1 day",
    "fixes": ["P0-1", "P0-2"],
    "goal": "Fix critical data integrity issues"
  },
  "sprint_2": {
    "duration": "2 days",
    "fixes": ["P1-1", "P1-2"],
    "goal": "Fix UX and state persistence"
  }
}
```

## Origin

Confidence: 88%
