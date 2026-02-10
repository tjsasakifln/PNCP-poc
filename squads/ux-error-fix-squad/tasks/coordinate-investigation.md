---
task: "Coordinate Investigation"
responsavel: "@lead-investigator"
responsavel_type: agent
atomic_layer: task
Entrada: |
  - bug_description: Description of the bug reported
  - logs: Array of relevant log entries
  - user_scenario: User scenario and reproduction steps
Saida: |
  - investigation_plan: Structured investigation plan
  - priorities: Prioritized list of investigation areas
  - assignments: Task assignments to specialist agents
Checklist:
  - "[ ] Review bug description and user reports"
  - "[ ] Analyze available logs and error messages"
  - "[ ] Identify affected components and systems"
  - "[ ] Create investigation plan with phases"
  - "[ ] Assign tasks to specialist agents"
  - "[ ] Define success criteria and milestones"
  - "[ ] Establish communication channels"
  - "[ ] Set timeline and deadlines"
---

# *coordinate-investigation

**Task**: Coordinate Investigation
**Agent**: @lead-investigator
**Confidence**: 90%

## Overview

Creates a comprehensive investigation plan based on bug reports, logs, and user scenarios. This task coordinates the entire bug investigation effort by analyzing the problem, identifying investigation areas, and delegating tasks to specialist agents.

## Purpose

When a complex bug affects multiple systems (frontend, backend, database), systematic coordination is essential. This task ensures:
- All aspects of the bug are investigated
- Specialists work on appropriate areas
- Investigation is efficient and thorough
- Findings are tracked and consolidated

## Usage

```
@lead-investigator
*coordinate-investigation
```

## Input Parameters

### bug_description (object)
Description of the bug being investigated.

**Structure**:
```json
{
  "title": "Free user search results not persisted",
  "severity": "CRITICAL",
  "impact": "Users lose search results after navigation",
  "affected_users": "All free tier users",
  "first_reported": "2026-02-10",
  "reproduction_rate": "100%"
}
```

### logs (array)
Relevant log entries from different systems.

**Structure**:
```json
[
  {
    "timestamp": "2026-02-10T14:30:00Z",
    "level": "ERROR",
    "source": "backend",
    "message": "Transaction not committed",
    "user_id": "c56e47f1-***"
  },
  {
    "timestamp": "2026-02-10T14:30:05Z",
    "level": "WARNING",
    "source": "frontend",
    "message": "localStorage write failed",
    "context": {"key": "searchState"}
  }
]
```

### user_scenario (object)
Detailed user scenario and reproduction steps.

**Structure**:
```json
{
  "user_type": "free_user",
  "scenario": "Search and navigate",
  "steps": [
    "Login with free account",
    "Navigate to /buscar",
    "Enter search query",
    "View results (10 items)",
    "Click on menu",
    "Return to /buscar",
    "Results are empty"
  ],
  "expected": "Results should persist",
  "actual": "Results lost, history empty"
}
```

## Output

### investigation_plan (object)
Structured investigation plan with phases and tasks.

**Structure**:
```json
{
  "phases": [
    {
      "name": "Initial Assessment",
      "duration": "2 hours",
      "objectives": [
        "Reproduce the bug reliably",
        "Identify affected components",
        "Gather all relevant logs"
      ]
    },
    {
      "name": "Root Cause Analysis",
      "duration": "4 hours",
      "objectives": [
        "Trace state persistence flow",
        "Analyze database transactions",
        "Debug API failures"
      ]
    },
    {
      "name": "Solution Design",
      "duration": "2 hours",
      "objectives": [
        "Consolidate findings",
        "Identify root causes",
        "Design fixes"
      ]
    }
  ],
  "parallel_investigations": true,
  "communication_frequency": "Every 2 hours"
}
```

### priorities (array)
Prioritized investigation areas.

**Structure**:
```json
[
  {
    "area": "Balance consumption without completion",
    "priority": "P0",
    "rationale": "Financial impact on users",
    "assigned_to": "backend-debugger"
  },
  {
    "area": "Search history not saved",
    "priority": "P0",
    "rationale": "Core functionality broken",
    "assigned_to": "backend-debugger"
  },
  {
    "area": "State lost on navigation",
    "priority": "P1",
    "rationale": "UX issue, workaround exists",
    "assigned_to": "ux-analyst"
  }
]
```

### assignments (object)
Task assignments to specialist agents.

**Structure**:
```json
{
  "ux-analyst": [
    {
      "task": "analyze-user-flow",
      "inputs": {"user_scenario": "...", "ui_logs": "..."},
      "deadline": "2026-02-10T16:00:00Z"
    },
    {
      "task": "trace-navigation-state",
      "inputs": {"navigation_path": "...", "state_snapshots": "..."},
      "deadline": "2026-02-10T17:00:00Z"
    }
  ],
  "backend-debugger": [
    {
      "task": "analyze-auth-logs",
      "inputs": {"auth_logs": "...", "timestamp_range": "..."},
      "deadline": "2026-02-10T16:00:00Z"
    },
    {
      "task": "trace-database-writes",
      "inputs": {"transaction_logs": "...", "table_names": ["search_history"]},
      "deadline": "2026-02-10T17:00:00Z"
    }
  ],
  "qa-validator": [
    {
      "task": "test-free-user-flow",
      "inputs": {"test_scenario": "...", "expected_behavior": "..."},
      "deadline": "2026-02-10T16:00:00Z"
    }
  ]
}
```

## Execution Steps

### 1. Analyze Bug Report
- Review bug description
- Assess severity and impact
- Identify affected systems
- Note reproduction steps

### 2. Review Available Evidence
- Analyze logs from all sources
- Check error messages
- Review user scenarios
- Identify patterns

### 3. Identify Investigation Areas
- Frontend state management
- Backend API transactions
- Database operations
- Auth and session management
- Network communication

### 4. Create Investigation Plan
- Define phases
- Set objectives for each phase
- Establish timelines
- Define success criteria

### 5. Prioritize Issues
- Assess user impact
- Consider business impact
- Evaluate technical complexity
- Assign priority levels (P0-P3)

### 6. Delegate Tasks
- Assign tasks to specialists
- Provide necessary context
- Set clear expectations
- Define deadlines

### 7. Establish Coordination
- Set up communication channels
- Define status update frequency
- Create tracking mechanism
- Plan consolidation meeting

## Decision Framework

### Priority Assignment

**P0 - Critical**
- Data loss or corruption
- Financial impact
- Security vulnerabilities
- Complete feature failure

**P1 - High**
- Significant UX degradation
- Partial feature failure
- Workarounds available

**P2 - Medium**
- Minor UX issues
- Edge cases
- Performance degradation

**P3 - Low**
- Cosmetic issues
- Nice-to-have improvements

### Agent Assignment

| Investigation Area | Assigned Agent |
|-------------------|----------------|
| User flow and UX | @ux-analyst |
| API and backend | @backend-debugger |
| Database and transactions | @backend-debugger |
| Auth and sessions | @backend-debugger |
| Testing and validation | @qa-validator |

## Example Usage

### Scenario: Free User Search Bug

**Input**:
```
Bug: Free users search results not persisted
Logs: [
  "Transaction not committed",
  "localStorage write failed",
  "401 Unauthorized on /me"
]
User Scenario: Search > Navigate > Return > Empty results
```

**Coordination**:
```
Investigation Plan:
Phase 1: Parallel investigation (2h)
  - UX: Analyze user flow
  - Backend: Check database commits
  - QA: Reproduce bug

Phase 2: Root cause analysis (3h)
  - UX: Trace state persistence
  - Backend: Debug transaction flow
  - Backend: Analyze auth failures

Phase 3: Consolidation (1h)
  - Lead: Consolidate findings
  - Lead: Identify root causes
  - Lead: Create fix plan
```

**Output**:
```
Priorities:
1. P0: Transaction not committed (backend)
2. P0: Balance deducted without completion (backend)
3. P1: State not persisted (frontend)
4. P1: Auth token issues (backend)

Assignments:
- @backend-debugger: trace-database-writes, verify-balance-consumption
- @ux-analyst: analyze-user-flow, trace-navigation-state
- @qa-validator: test-free-user-flow
```

## Success Criteria

- [ ] Complete investigation plan created
- [ ] All investigation areas identified
- [ ] Priorities assigned based on impact
- [ ] Tasks delegated to appropriate specialists
- [ ] Timelines and deadlines established
- [ ] Communication channels set up
- [ ] All agents have clear assignments
- [ ] Success criteria defined

## Related Tasks

- **Next Tasks**: After coordination, specialists execute their assigned tasks
- **consolidate-findings**: Consolidates results after specialist investigations
- **prioritize-fixes**: Prioritizes fixes based on investigation findings

## Origin

Generated from squad design blueprint for ux-error-fix-squad.
Confidence: 90%
