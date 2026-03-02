# /review-pr — Universal Automated Governance & Merge Protocol

## Purpose

To automatically select, analyze, correct, and merge pull requests with absolute rigor based on High-Performance Engineering standards. Only PRs that achieve a **perfect score (100%)** across all Governance Categories are merged automatically.

## Key Principles

1.  **Deterministic Selection**: Uses a scoring algorithm to select the highest-priority PR (removing human bias).
2.  **Incontestable Criteria**: Based on Industry Standards (OWASP, ISO, Conventional Commits).
3.  **Automated Fixes**: Applies only consensual fixes (formatting, import sorting) without blocking the flow.
4.  **Zero Tolerance**: 100% score required — any violation blocks the merge.
5.  **Safety Net**: Multi-layer post-merge validation with automatic rollback.
6.  **CI/CD Optimized**: Leverages caching and path filters for rapid validation.

## Selection Algorithm (Deterministic)

When invoked, the protocol automatically selects the most important PR using:

### Eligibility Filter

Only PRs meeting ALL criteria are considered:
* ✅ CI Status: ALL checks passing (100% Green).
* ✅ Not marked as Draft.
* ✅ No "wip" or "do-not-merge" labels.
* ✅ No merge conflicts.
* ✅ State: OPEN.

### Scoring Formula

Total Score = Priority_Weight + Age_Weight + Size_Weight + Label_Weight

Where:
 Priority_Weight = Commit type priority
 - hotfix: 10 points
 - feat: 8 points
 - fix: 6 points
 - refactor: 4 points
 - test: 7 points (High priority for Quality assurance)
 - docs: 2 points
 - chore: 1 point

 Age_Weight = Days since PR created
 - >72 hours: +4 points
 - >48 hours: +2 points
 - >24 hours: +1 point

 Size_Weight = Lines changed (Inversely proportional)
 - <100 lines: +3 points
 - <200 lines: +2 points
 - <400 lines: +1 point
 - >400 lines: -2 points (Discourage large PRs)

 Label_Weight = Special labels
 - security/deploy/performance: +5 points each
 - wip/blocked: -100 points (Effective blocker)


### Tiebreaker

If multiple PRs have the same score, select the **oldest PR** (First In, First Out).

## 8 Categories of Validation Criteria

### Category 1: Code Quality Gates (12.5%)

* ✅ **CI Pipeline**: 100% green.
* ✅ **Test Coverage**: ≥ [MIN_COVERAGE_BACKEND]% Backend, ≥ [MIN_COVERAGE_FRONTEND]% Frontend.
* ✅ **Linting Errors**: 0 (e.g., ESLint, Pylint, Sonar).
* ✅ **Type/Compile Errors**: 0 (e.g., TypeScript, Rust, Go).
* ✅ **Code Formatting**: 100% compliant with project standard (e.g., Prettier, Black, Gofmt).
* ✅ **Import Sorting**: Clean, no circular dependencies.

### Category 2: Testing Requirements (12.5%)

* ✅ **Unit Tests**: 100% passing.
* ✅ **Integration Tests**: 100% passing (if applicable).
* ✅ **E2E Tests**: 100% passing (if implemented).
* ✅ **Performance**: No regression > [MAX_REGRESSION]% (if applicable).
* ✅ **Smoke Tests**: Critical paths validated.

### Category 3: Security Standards (12.5%)

* ✅ **Vulnerability Scan**: 0 HIGH/CRITICAL issues (e.g., `npm audit`, `safety check`).
* ✅ **Dependency Audit**: 0 CVEs.
* ✅ **Hardcoded Secrets**: 0 secrets detected (e.g., Gitleaks).
* ✅ **Injection Protection**: No raw queries or unescaped inputs.
* ✅ **Input Sanitization**: Validation layer applied.

### Category 4: Documentation Standards (12.5%)

* ✅ **Function Docstrings**: 100% public functions.
* ✅ **Class/Module Docstrings**: 100% public classes.
* ✅ **CHANGELOG**: Updated if feature/fix PR.
* ✅ **API Docs**: Swagger/OpenAPI updated if API changed.
* ✅ **Type Hints**: Strong typing enforced (no `any` or equivalent).

### Category 5: Architecture & Design (12.5%)

* ✅ **Cyclomatic Complexity**: ≤ [MAX_COMPLEXITY] per function.
* ✅ **Code Duplication**: < [MAX_DUPLICATION]%.
* ✅ **Function Length**: ≤ [MAX_LINES] lines.
* ✅ **Maintainability Index**: Grade A/B.

### Category 6: Git Standards (12.5%)

* ✅ **Commit Messages**: 100% semantic (Conventional Commits).
* ✅ **PR Description**: All required sections present (Context, Changes, Testing, Risks, Closes).
* ✅ **Linked Issue**: "Closes #xxx" present.
* ✅ **Merge Conflicts**: 0 conflicts.

### Category 7: Review Standards (12.5%)

* ✅ **PR Size**: ≤ [MAX_PR_LINES] lines (recommended).
* ✅ **Single Responsibility**: 1 primary purpose per PR.
* ✅ **Backwards Compatible**: No breaking changes (unless documented).
* ✅ **Test-to-Code Ratio**: ≥ [RATIO] (e.g., 0.5).

### Category 8: Operational Excellence (12.5%)

* ✅ **Health Checks**: Implemented for new services/endpoints.
* ✅ **Monitoring**: Logs added for critical paths.
* ✅ **Error Handling**: Proper try-catch/result wrapping with logging.
* ✅ **Rollback Plan**: Documented in PR.
* ✅ **Resource Cleanup**: No memory leaks or unclosed connections.

## Automated Fixes (Consensual Standards Only)

If score = 100% but minor formatting issues exist, these are auto-fixed:

1. **Code Formatting** (`[FORMAT_COMMAND]`)
* Deterministic, zero semantic changes.


2. **Import Sorting**
* Removes ambiguity, improves readability.


3. **Auto-fixable Linting** (`[LINT_FIX_COMMAND]`)
* Unused imports, variables, style consistency.


4. **Basic Docstrings**
* Skeleton generation for undocumented functions (if supported).



**After auto-fixes**: Re-run tests and await 100% passing before proceeding.

## Post-Merge Safety Net (3 Layers)

After successful merge, execute 3-layer validation on the main branch:

### Layer 1: Health Checks (Immediate)

# Build & Test Core
[BUILD_COMMAND] && [UNIT_TEST_COMMAND]

* Build succeeds.
* Unit tests pass.
* No runtime startup errors.

**Failure Action**: Immediate rollback.

### Layer 2: Smoke Tests (Functional)

# Run critical path tests
[SMOKE_TEST_COMMAND] --grep "critical"



* Critical user journeys.
* Authentication flows.
* Core API endpoints.

**Failure Action**: Immediate rollback + reopen PR with `post-merge-failure` label.

### Layer 3: CI Pipeline (Deep Validation)


# Trigger full CI suite
[TRIGGER_CI_COMMAND]


* Full test suite on `master`/`main`.
* Integration tests.
* Artifact generation.

**Failure Action**: Incident report + Hotfix priority.

## Rollback Strategy

If any post-merge validation fails:

# 1. Capture merge commit
MERGE_SHA=$(git log -1 --format="%H")

# 2. Revert merge commit
git revert $MERGE_SHA --no-edit -m 1

# 3. Push revert
git push origin master

# 4. Reopen PR & Label
[REOPEN_PR_COMMAND] $PR_NUMBER
[ADD_LABEL_COMMAND] $PR_NUMBER "post-merge-failure"

# 5. Comment failure details
[COMMENT_PR_COMMAND] $PR_NUMBER "⚠ Post-Merge Validation FAILED - Rollback executed."

## Execution Workflow

### Step 1: Select PR (Deterministic Algorithm)

Fetches open PRs, applies scoring formula, and selects the winner.

### Step 2: Validate Criteria (100% Required)

Checks the 8 categories. If any category fails (< 100%), the PR is rejected with specific feedback.

### Step 3: Apply Auto-Fixes (If Needed)

Runs formatters and linters. Commits changes as `chore: apply automated fixes`. Re-runs tests.

### Step 4: Merge PR

Merges to `master`/`main` using Merge Commit strategy (to preserve history and simplify revert).

### Step 5: Post-Merge Validation

Runs Layers 1 (Health), 2 (Smoke), and 3 (CI). Executes Rollback if Layer 1 or 2 fails.

### Step 6: Finalize

Closes linked issues. Comments on the PR with a summary of the operation and the validation score.

### Step 7: Update Documentation

Updates the project `ROADMAP.md` or Changelog:

* Marks linked issue as "Completed".
* Updates progress bars/metrics.
* Adds entry to "Recent Updates".
