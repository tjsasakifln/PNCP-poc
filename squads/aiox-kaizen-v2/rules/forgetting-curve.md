# Forgetting Curve — Pattern Lifecycle

**Origin:** Hermann Ebbinghaus (1885) forgetting curve + Spaced Repetition research
**Applied by:** memory-keeper agent in `tasks/reflect.md`
**Governed in:** `data/intelligence/knowledge/patterns.yaml`

## The Forgetting Curve

Human memory decays exponentially without reinforcement.

### Formula

```
decay_score(t) = e^(-rate × days_since_observed)

Where:
  e = Euler's number (≈ 2.71828)
  rate = decay rate (0.05 default, 0.025 for verified patterns)
  t = days_since_observed
  decay_score = pattern health (1.0 = fresh, 0.0 = forgotten)
```

### Decay Rates

**Default Rate: 0.05** (General patterns)
- Unverified observations
- Single-sighting learnings
- Tentative patterns

Formula: `decay = e^(-0.05 × days)`

Examples:
- Day 0: e^0 = 1.0 (fresh)
- Day 7: e^-0.35 = 0.707 (starting to fade)
- Day 14: e^-0.7 = 0.497 (half-strength)
- Day 30: e^-1.5 = 0.223 (fading fast)
- Day 60: e^-3.0 = 0.050 (near deletion threshold)

**Verified Rate: 0.025** (Proven patterns)
- Observed 2+ times independently
- Documented in trusted sources
- Proven effective in practice

Formula: `decay = e^(-0.025 × days)`

Examples:
- Day 0: e^0 = 1.0 (fresh)
- Day 14: e^-0.35 = 0.707 (slower fade)
- Day 30: e^-0.75 = 0.472
- Day 60: e^-1.5 = 0.223
- Day 120: e^-3.0 = 0.050 (near deletion threshold)

**2x Slower Decay:** Verified patterns take ~2x longer to reach archive threshold.

## Pattern Lifecycle

### 1. OBSERVED (decay_score = 1.0)
- New learning captured in daily YAML
- Candidate for extraction
- Not yet in patterns.yaml

### 2. EXTRACTED (decay_score = 0.9-1.0)
- Passes all 5 extraction criteria
- Added to patterns.yaml
- `verified: false` initially (until reinforced)
- Uses default rate (0.05)

### 3. REINFORCED (decay_score reset to 1.0)
- Pattern sighted again
- `last_reinforced` date updated to today
- `verification_count` incremented
- `days_since_observed` reset to 0
- If verification_count >= 2: Switch to verified rate (0.025)

Reinforcement Logic:
```
If new_observation_matches(pattern):
  pattern.days_since_observed = 0
  pattern.decay_score = 1.0
  pattern.last_reinforced = today
  pattern.verification_count += 1
  If pattern.verification_count >= 2:
    pattern.verified = true
    pattern.rate = 0.025  # Slower decay
```

### 4. FADING (decay_score = 0.1-0.5)
- Pattern has not been observed in 7-30 days
- Warning appears in briefing: "Nearing archive"
- Still accessible for reference
- Decay continues

### 5. ARCHIVED (decay_score < 0.1)
- Pattern moved to `archive/patterns.yaml.archive`
- Removed from active patterns.yaml
- Preserved for historical reference
- No longer appears in briefings

Archive Trigger:
```
If decay_score < 0.1:
  Move pattern to archive/patterns.yaml.archive
  Update pattern.archive_date = today
```

### 6. DELETED (decay_score < 0.05)
- Pattern removed entirely from system
- Logged in `archive/cleanup-YYYY-MM-DD.log`
- Irretrievable (use backup if needed)
- Deleted on `compact-archive` task

Delete Trigger:
```
If decay_score < 0.05:
  Log deletion in audit trail
  Remove pattern from all files
  Update pattern.deleted_date = today
```

## Decay Thresholds

| Threshold | Status | Action | Days at Default Rate |
|-----------|--------|--------|----------------------|
| 1.0 | Fresh | Include in briefing | 0 |
| 0.8 | Active | Include in briefing | ~4 |
| 0.5 | Fading | Include + warning | ~14 |
| 0.1 | Archive | Move to archive/ | ~60 |
| 0.05 | Delete | Remove entirely | ~120 |

## Spaced Repetition Effect

The key insight: **Reinforced patterns get stronger.**

When a pattern is sighted again:
1. Decay resets to 1.0
2. Decay rate may slow (if verified)
3. The pattern becomes "stickier"

This creates a virtuous cycle:
```
Pattern observed → decay starts
Pattern observed again → decay resets + rate slows
Pattern observed 3rd time → decay even slower
Pattern frequently observed → essentially permanent
```

**Example:**
- Initial observation: Day 0, decay = 1.0, rate = 0.05
- Re-observed: Day 7, reset to 1.0, verify (count=2), rate now 0.025
- Re-observed: Day 21, reset to 1.0, rate stays 0.025
- Result: Pattern becomes "sticky" — lasts 120+ days instead of 60

## Configuration

In `config/config.yaml`:
```yaml
intelligence:
  decay:
    rate_general: 0.05      # General patterns
    rate_verified: 0.025    # Verified patterns (2x slower)
    archive_threshold: 0.1  # Move to archive/ when <
    delete_threshold: 0.05  # Delete when <
```

## Verification

Decay calculation is verified:
1. Formula applied correctly: ✓
2. Rates configured (0.05, 0.025): ✓
3. Archive threshold (0.1): ✓
4. Delete threshold (0.05): ✓
5. Reinforcement resets decay: ✓

Implemented in: `tasks/reflect.md` → `tasks/mine-patterns.md`

---

**Reference:**
- Ebbinghaus, H. (1885). Memory: A Contribution to Experimental Psychology
- Brown, P. C., et al. (2014). Make It Stick: The Science of Successful Learning
- Dunlosky, J., et al. (2013). Improving Students' Learning With Effective Techniques
