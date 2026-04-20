# Extraction Criteria — Pattern Validation

**Governing:** `tasks/mine-patterns.md`
**Enforced by:** memory-keeper agent
**Applied when:** Extracting learnings from daily YAMLs into patterns.yaml

## 5-Point Validation

**ALL 5 criteria must be met for a learning to become a pattern.**

### 1. VERIFIED ✓

**Definition:** Pattern observed independently 2+ times OR documented in trusted sources.

**Check:**
- How many times has this learning appeared in recent dailies?
- Is it mentioned in code comments, git commits, or documentation?
- Is it confirmed by multiple team members or agents?

**Pass Conditions:**
- `verification_count >= 2` (observed 2+ times independently), OR
- Learning documented in `docs/patterns/`, `docs/architecture/`, or code comments, OR
- Mentioned in git commit message (searchable: `git log --grep`)

**Fail Conditions:**
- Only 1 sighting in available dailies
- Not documented anywhere in codebase
- Speculation ("I think...", "Maybe...", "Seems like...")

**Example:**
- ✓ PASS: "Windows hook issue — encountered twice (daily 2026-03-10, daily 2026-03-11)"
- ✗ FAIL: "Might be a Windows issue, not sure"

---

### 2. NON-OBVIOUS ✓

**Definition:** Pattern not already documented in existing patterns.yaml OR contradicts prior belief (new insight).

**Check:**
- Grep patterns.yaml: `grep "pattern name"` → does it exist?
- Is this learning repeating what we already know?
- Or is it a new insight that changes our understanding?

**Pass Conditions:**
- Pattern does NOT appear in patterns.yaml (new), OR
- Pattern contradicts existing belief (worth reinforcing over old assumption)

**Fail Conditions:**
- Pattern already in patterns.yaml (use reinforcement instead of extraction), OR
- Pattern is obvious/common knowledge (not worth capturing)

**Example:**
- ✓ PASS: New insight "Use timer.unref() not process.exit() on Windows" (not in patterns yet)
- ✗ FAIL: "Claude Code is an AI coding assistant" (obvious, already documented)

---

### 3. REUSABLE ✓

**Definition:** Applicable to >1 scenario in the project. Not a one-off edge case.

**Check:**
- Can this pattern help with other tasks, squads, or scenarios?
- Is it a general principle or a specific incident?
- Would I want to apply this again in the future?

**Pass Conditions:**
- Applicable to 2+ different tasks/squads/agents, OR
- General principle (applies broadly), OR
- Recurring scenario (happened before, will happen again)

**Fail Conditions:**
- One-time edge case (never again)
- Specific to single task/squad (not reusable)
- Too narrow in scope

**Example:**
- ✓ PASS: "Windows hooks need async/fail-silent design" (applies to all Windows hooks)
- ✗ FAIL: "On Tuesday, we had a weird UUID collision" (one-time edge case)

---

### 4. ACTIONABLE ✓

**Definition:** Includes trigger condition AND action (if X, then Y). Not just observation.

**Check:**
- Can I extract a "when to apply" trigger from this?
- Does the pattern have a clear action/recommendation?
- Would someone reading this know WHAT TO DO?

**Pass Conditions:**
- Pattern has `suggested_trigger` (when X applies, do Y), AND
- Pattern includes explicit action (fix, avoid, adopt, etc.)

**Fail Conditions:**
- Pure observation without guidance ("We noticed this...")
- No clear action ("This is interesting...")
- Ambiguous trigger ("Sometimes...")

**Example:**
- ✓ PASS: Trigger: "When implementing hooks on Windows" → Action: "Use timer.unref() + let Node exit naturally"
- ✗ FAIL: "Windows behaves differently from macOS" (observation, no action)

---

### 5. EMPIRICAL ✓

**Definition:** Based on direct observation OR documented evidence, not speculation.

**Check:**
- Can I trace this learning to a specific git commit, code change, or task?
- Is it based on what actually happened?
- Or is it guesswork/assumption?

**Pass Conditions:**
- Directly observed (captured in daily YAML), OR
- Traceable to git log (commit message, code change), OR
- Documented in meeting notes, tickets, or design docs

**Fail Conditions:**
- Speculation ("I think X might be true")
- Assumption without evidence ("X is probably the cause")
- Hearsay ("Someone told me...")
- Untested hypothesis

**Example:**
- ✓ PASS: "Hook output not reaching Claude Code on Windows" (observed in 2 sessions, git log confirms hook timeout)
- ✗ FAIL: "Windows hooks might be broken, not sure" (speculation)

---

## Extraction Process

```
For each learning in daily YAML:
  1. Check criteria 1-5 (all must PASS)
  2. If any fails → REJECT (log reason, keep in daily)
  3. If all pass → EXTRACT (add to patterns.yaml)
  4. Mark verification_count = N (how many sightings)
  5. Assign decay_score = 1.0 (fresh)
```

## Rejection Logging

When a learning fails criteria, log rejection:
```yaml
rejected_learning: "Windows hook process.exit() issue"
reason: "verification_count = 1 (not verified yet, need 2+ sightings)"
first_sighting: "2026-03-11"
status: "Candidate (observe 1 more time to extract)"
suggestion: "If pattern observed again, extract on next reflection"
```

## Special Cases

### Patterns Already in patterns.yaml
If a learning matches an existing pattern:
```
Instead of extracting:
1. Find matching pattern in patterns.yaml
2. Update last_reinforced = today
3. Increment verification_count
4. Reset days_since_observed = 0
5. If verification_count >= 2: Set verified = true
```

### Contradictions
If a learning contradicts an existing pattern:
```
1. Mark old pattern with flag: "contradicted_by: new_learning"
2. Extract new learning as separate pattern (if meets criteria)
3. Note both patterns with explanation
4. Allow human to choose which is "correct"
```

### Ambiguous Learnings
If criteria pass but trigger is unclear:
```
ACCEPT but WARN:
- Add pattern with note: "trigger condition needs clarification"
- User can refine suggested_trigger later
- Don't delete; let human decide
```

---

## Quality Assurance

Checklist for `reflection-quality-checklist.md`:
- [ ] All extracted patterns have verification_count >= 1
- [ ] All rejected learnings logged with reason
- [ ] No duplicate patterns in patterns.yaml
- [ ] All patterns have actionable `suggested_trigger`
- [ ] All patterns have empirical basis (traceable)

---

## Examples

### Learning 1: PASS All 5 Criteria

```yaml
daily_learning: "Windows process.exit() cuts hook stdout prematurely"

Criterion 1 — VERIFIED:
  ✓ Observed 2 times (daily 2026-03-10, daily 2026-03-11)

Criterion 2 — NON-OBVIOUS:
  ✓ New insight (not in existing patterns)

Criterion 3 — REUSABLE:
  ✓ Applies to all Windows hooks (Stop, SessionStart, custom)

Criterion 4 — ACTIONABLE:
  ✓ Trigger: "When implementing hooks on Windows"
  ✓ Action: "Use timer.unref() instead of process.exit()"

Criterion 5 — EMPIRICAL:
  ✓ Traced to git commit: "fix(hooks): resolve Windows stdout issue"

Result: EXTRACT as pattern
```

### Learning 2: FAILS Criterion 1 (Not Verified)

```yaml
daily_learning: "Redis might be faster than in-memory cache"

Criterion 1 — VERIFIED:
  ✗ Only hypothesized, not tested

Result: REJECT (log as "Candidate — observe in practice, then extract")
```

### Learning 3: FAILS Criterion 4 (Not Actionable)

```yaml
daily_learning: "Team velocity was high this week"

Criterion 4 — ACTIONABLE:
  ✗ Observation without action (no suggested_trigger)

Result: REJECT (suggestion: "Provide trigger + action, e.g., 'If velocity drops 20%, investigate resource constraints'")
```

---

**Last Updated:** 2026-03-11 | **Applied by:** memory-keeper | **Enforced in:** tasks/mine-patterns.md
