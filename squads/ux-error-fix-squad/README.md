# UX Error Fix Squad

**Domain**: Free User Search Persistence & Balance Consumption
**Version**: 1.0.0
**AIOS**: 2.1.0+
**Blueprint Confidence**: 87%

## Mission

Investigate and fix critical bugs affecting free users:
1. **Search Persistence**: Search results not being saved to history
2. **Balance Consumption**: Balance deducted but operations not completing
3. **Auth Inconsistency**: Token verification and session state issues
4. **Navigation State**: Search state lost during page navigation

## Squad Composition

### Agents (4)

| Agent | Role | Confidence | Commands |
|-------|------|------------|----------|
| **lead-investigator** | Coordinates investigation, prioritizes fixes, consolidates findings | 92% | coordinate-investigation, prioritize-fixes, consolidate-findings, create-fix-plan |
| **ux-analyst** | Analyzes user flow, identifies UX breakpoints and state persistence issues | 88% | analyze-user-flow, trace-navigation-state, identify-ux-breakpoints, validate-session-persistence |
| **backend-debugger** | Investigates API failures, auth inconsistencies, and database transactions | 90% | analyze-auth-logs, debug-api-failures, verify-balance-consumption, trace-database-writes |
| **qa-validator** | Tests fixes, validates edge cases, ensures regression prevention | 85% | test-free-user-flow, validate-balance-deduction, verify-history-save, test-navigation-persistence |

### Tasks (16)

#### Lead Investigator Tasks (4)
1. **coordinate-investigation** - Create investigation plan and assign priorities
2. **prioritize-fixes** - Prioritize findings by impact and timeline
3. **consolidate-findings** - Consolidate all findings into root cause report
4. **create-fix-plan** - Create implementation plan with steps

#### UX Analyst Tasks (4)
5. **analyze-user-flow** - Map user journey and identify breakpoints
6. **trace-navigation-state** - Trace state changes during navigation
7. **identify-ux-breakpoints** - Identify where UX breaks occur
8. **validate-session-persistence** - Validate session state persistence

#### Backend Debugger Tasks (4)
9. **analyze-auth-logs** - Analyze auth logs for token issues
10. **debug-api-failures** - Debug API failure root causes
11. **verify-balance-consumption** - Trace balance deduction flow
12. **trace-database-writes** - Trace database write operations

#### QA Validator Tasks (4)
13. **test-free-user-flow** - Test complete free user flow
14. **validate-balance-deduction** - Validate balance deduction logic
15. **verify-history-save** - Verify search history is saved
16. **test-navigation-persistence** - Test state persistence during navigation

## Problem Statement

### Issue #1: Search Results Not Persisted

**Severity**: CRITICAL (UX)
**Status**: Active

**Problem**:
- Free user performs search
- Results displayed successfully
- Navigation away loses search results
- Search history not saved in database

**Impact**:
- User frustration
- Wasted balance credits
- Poor free user experience

---

### Issue #2: Balance Consumed Without Completion

**Severity**: CRITICAL (Business)
**Status**: Active

**Problem**:
- Balance deducted from user account
- Search operation starts
- Operation fails or incomplete
- Balance not refunded

**Impact**:
- Financial loss for users
- Trust issues
- Support tickets

---

### Issue #3: Auth Token Inconsistency

**Severity**: HIGH (Security/UX)
**Status**: Active

**Problem**:
- Auth token validation intermittent
- /me API calls failing
- Session state inconsistent
- User logged out unexpectedly

**Impact**:
- Poor user experience
- Lost work
- Security concerns

## Entities & Workflows

### Entities
- SearchResult
- SearchHistory
- UserBalance
- AuthToken
- Session
- FreePlan

### Workflows
- save-search-history
- consume-balance
- persist-search-state
- verify-auth-token
- restore-search-results

### Integrations
- Auth API (/me)
- Plans API (/plans)
- Messages API (/api/messages/unread-count)
- Database (search_history, user_balance tables)

## Execution Flow

### Phase 1: Investigation (Lead Investigator + All Agents)

```
@lead-investigator
*coordinate-investigation
  Input: bug_description, logs, user_scenario
  Output: investigation_plan, priorities, assignments
  ↓
  Assigns tasks to specialists
  ↓

@ux-analyst *analyze-user-flow (parallel)
@backend-debugger *analyze-auth-logs (parallel)
@qa-validator *test-free-user-flow (parallel)
  ↓
  All findings collected
  ↓

@lead-investigator
*consolidate-findings
  Input: ux_findings, backend_findings, qa_findings
  Output: consolidated_report, root_causes
```

### Phase 2: Root Cause Analysis

```
@ux-analyst
*trace-navigation-state
  Input: navigation_path, state_snapshots
  Output: state_trace, missing_persistence
  ↓
*identify-ux-breakpoints
  Input: user_journey, session_data
  Output: breakpoint_list, ux_issues

@backend-debugger
*debug-api-failures
  Input: api_logs, failed_requests
  Output: failure_root_causes, fix_suggestions
  ↓
*verify-balance-consumption
  Input: user_id, search_event
  Output: balance_trace, consumption_status
  ↓
*trace-database-writes
  Input: transaction_logs, table_names
  Output: write_trace, missing_writes
```

### Phase 3: Fix Planning

```
@lead-investigator
*prioritize-fixes
  Input: findings_list, impact_assessment
  Output: prioritized_fixes, timeline
  ↓
*create-fix-plan
  Input: root_causes, priorities
  Output: fix_plan, implementation_steps
```

### Phase 4: Validation

```
@qa-validator
*validate-balance-deduction
  Input: user_id, initial_balance
  Output: deduction_verified, final_balance
  ↓
*verify-history-save
  Input: search_params, user_id
  Output: history_saved, saved_record
  ↓
*test-navigation-persistence
  Input: navigation_flow, state_keys
  Output: persistence_verified, lost_data
```

## Success Criteria

### Search Persistence
- Search results saved to database after every successful search
- Search history accessible after navigation
- No lost search results

### Balance Consumption
- Balance only deducted after successful operation
- Failed operations refund balance
- Transaction atomicity guaranteed

### Auth Consistency
- Auth token validation reliable
- Session state persists across navigation
- No unexpected logouts

### QA Validation
- All test scenarios pass
- Edge cases handled
- No regressions introduced

## Usage

### Activate Squad
```bash
# Start investigation
@lead-investigator
*coordinate-investigation

# Run specific analysis
@ux-analyst
*analyze-user-flow

@backend-debugger
*debug-api-failures

# Validate fixes
@qa-validator
*test-free-user-flow
```

### Full Investigation Workflow
```bash
# Phase 1: Coordinate
@lead-investigator
*coordinate-investigation

# Phase 2: Parallel Investigation
@ux-analyst *analyze-user-flow
@backend-debugger *analyze-auth-logs
@qa-validator *test-free-user-flow

# Phase 3: Consolidate
@lead-investigator
*consolidate-findings
*prioritize-fixes
*create-fix-plan

# Phase 4: Validate
@qa-validator
*validate-balance-deduction
*verify-history-save
*test-navigation-persistence
```

## Configuration

This squad uses local config files:
- **Coding Standards**: `config/coding-standards.md`
- **Tech Stack**: `config/tech-stack.md`
- **Source Tree**: `config/source-tree.md`

## Related Documentation

- [Supabase Auth Best Practices](https://supabase.com/docs/guides/auth)
- [FastAPI Database Transactions](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [Next.js State Management](https://nextjs.org/docs/basic-features/data-fetching)

## Blueprint Source

Generated from:
- Free user search bug with auth inconsistency (verbal description)
- Created: 2026-02-10T21:52:00.000Z
- Overall confidence: 87%

## Generated by

Squad Creator Agent (@craft)
- Task-first architecture (AIOS 2.1)
- 4 agents, 16 tasks, 0 workflows
- Domain: free-user-search-persistence-bug

---

**Author**: Tiago Sasaki
**License**: MIT
**Created**: 2026-02-10
