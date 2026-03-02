# Roadmap Integrity Audit — Universal Synchronization Protocol

You are conducting a comprehensive audit to synchronize the project's strategic documentation (e.g., `ROADMAP.md`) with the actual state of the Issue Tracker / Version Control System.

# CONTEXT

High-velocity projects accumulate discrepancies between "Plan" and "Reality" due to:
- Tasks split into sub-tasks (Atomicity).
- Emergency hotfixes added mid-sprint.
- Discovered "Orphan" modules (code without a task).
- Documentation lag.

Your job is to detect ALL discrepancies (Drift) and provide actionable reconciliation steps to restore the Roadmap as the "Source of Truth".

# AUDIT SCOPE

## 1. ISSUE COUNT RECONCILIATION

**Compare:**
1.  Total issues listed in `[ROADMAP_FILE]`.
2.  Actual total issues in the Issue Tracker (e.g., GitHub/Jira/GitLab).

**Detect:**
* **Phantom References:** Issues mentioned in documentation that do not exist in the tracker.
* **Orphan Issues:** Issues existing in the tracker but missing from the documentation.
* **Status Mismatch:** Closed issues not marked as completed.

**Output Format:**

ISSUE COUNT AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documented: [DOC_COUNT] issues
Actual (Tracker): [ACTUAL_COUNT] issues
Drift: [DIFFERENCE] issues ([PERCENTAGE]%)
Status: [WARNING/OK] (Threshold: <5%)

BREAKDOWN:
✅ Documented & Exist: [COUNT]
❌ Phantom (Doc only): [LIST_IDS]
⚠️ Orphan (Tracker only): [LIST_IDS]

---

## 2. MILESTONE PROGRESS VALIDATION

**For each Milestone (M1–Mn):**

**Compare:**

* Stated progress in documentation (e.g., "M2: 10/10 (100%)").
* Actual milestone state in the Tracker API/Dashboard.

**Detect:**

* Open issues marked as closed in docs.
* Closed issues marked as open in docs.
* Issues assigned to the wrong milestone.

**Output Format:**

MILESTONE PROGRESS AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Milestone | Doc Progress | Real Progress | Sync | Discrepancies |
|-----------|--------------|---------------|------|---------------|
| M1        | 100%         | 100%          | ✅   | None          |
| M2        | 100%         | 90%           | ❌   | #112 is Open  |
| M3        | 60%          | 70%           | ⚠️   | #85 is Closed |

---

## 3. ISSUE STATE SYNCHRONIZATION

**For EVERY issue referenced in the Roadmap:**

**Check:**

1. Does the issue ID exist?
2. Is the state correct? (Open/Closed match).
3. Is the milestone assignment consistent?

**Detect:**

* `[ ]` (Unchecked) in docs but `Closed` in Tracker → **Understated Progress**.
* `[x]` (Checked) in docs but `Open` in Tracker → **Premature Closure**.

---

## 4. PHANTOM REFERENCE DETECTION

**Scan `[ROADMAP_FILE]` for:**

* Issue IDs that return "404 Not Found".
* Invalid ranges (e.g., `#50-#60` where #55 implies a deleted issue).
* Broken cross-references.

**Output Format:**

PHANTOM REFERENCES AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: [COUNT] phantom issues detected!

Line [X]: "Issues #49-#76"
├─ Reality: Range includes non-existent IDs.
└─ Action: Correct range to match actual created issues.

---

## 5. ORPHAN ISSUE DETECTION

**Find issues in Tracker NOT documented in Roadmap:**

**Query:** Get all issues from Tracker.
**Cross-reference:** Check against all IDs present in `[ROADMAP_FILE]`.

**Output Format:**

ORPHAN ISSUES AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOUND: [COUNT] orphan issues.

#[ID] - [TITLE]
├─ State: [STATE]
├─ Milestone: [MILESTONE]
└─ Action: Add to [SECTION] in Roadmap.

---

## 6. VELOCITY & ETA VALIDATION

**Calculate:**

* Issues closed in the last 7 days (Rolling Velocity).
* Average Velocity (Issues/Day).
* Projected completion dates vs. Documented Deadlines.

**Output Format:**

VELOCITY & ETA AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACTUAL VELOCITY (Last 7 days):
├─ Closed: [COUNT] issues
├─ Average: [X.X] issues/day
└─ Trend: [Accelerating/Decelerating]

ETA VALIDATION:
M3 (Current):
├─ Doc Deadline: [DATE]
├─ Projected: [DATE] (based on current velocity)
└─ Status: [AHEAD/BEHIND] by [DAYS]

---

## 7. DOCUMENTATION CONSISTENCY CHECK

**Verify:**

* Progress bars match calculated percentages.
* Summary text ("X issues closed") matches actual count.
* "Last Updated" timestamp is current.

---

## 8. FINAL RECONCILIATION REPORT

**Summarize findings:**

1. **Executive Summary:** Drift %, Velocity Health.
2. **Critical Actions (P0):** Fix Phantoms, Sync States.
3. **High Priority (P1):** Add Orphans, Update Progress Bars.
4. **Updated Metrics:** Snapshot of the correct state.

**Output Format:**

═══════════════════════════════════════════════════
ROADMAP AUDIT - EXECUTIVE SUMMARY
═══════════════════════════════════════════════════
Audit Date: [YYYY-MM-DD]
Sync Status: [DRIFT_LEVEL] ([X]% deviation)

REQUIRED ACTIONS:
[ ] 1. Remove Phantom IDs (Lines X, Y, Z).
[ ] 2. Sync 8 State Mismatches.
[ ] 3. Import 5 Orphan Issues to Roadmap.
[ ] 4. Update Header Metrics (Total: X -> Y).

UPDATED METRICS SNAPSHOT:
Total Issues: [NEW_TOTAL]
Overall Progress: [X]/[Y] ([Z]%)
Estimated Completion: [DATE]
═══════════════════════════════════════════════════

---

# EXECUTION INSTRUCTIONS

## Step 1: Data Collection

Fetch data from your source of truth.

# Example (Generic CLI concept):
# 1. Get all issues as JSON
[CLI_COMMAND] issue list --state all --json > issues.json

# 2. Get milestone data
[CLI_COMMAND] milestone list --json > milestones.json

# 3. Snapshot current docs
cat [ROADMAP_FILE] > roadmap_snapshot.md

## Step 2: Cross-Reference Analysis

1. **Map:** Create a map of `{ID: State}` from the Tracker data.
2. **Scan:** Regex scan the `[ROADMAP_FILE]` for `#(\d+)`.
3. **Compare:** Iterate and flag discrepancies.

## Step 3: Generate Diff

Produce specific line-by-line changes for the documentation.


Line 12:
- Total: 98 issues
+ Total: 103 issues

Line 85:
- [ ] #85 - Security Audit
+ [x] #85 - Security Audit (Merged)

## Success Criteria

* ✅ < 5% Drift between Docs and Tracker.
* ✅ Zero Phantom references.
* ✅ All Orphan issues documented.
* ✅ Progress bars mathematically accurate.

---

# IMPORTANT NOTES

* Documentation lag is normal in high-velocity teams; this audit resets the baseline.
* **Goal:** Synchronization, not blame.
* **Frequency:** Recommend running this protocol Weekly or per Sprint Review.
