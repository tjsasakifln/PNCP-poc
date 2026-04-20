# Reflection Quality Checklist

**Task:** reflect.md | **Executor:** memory-keeper | **Trigger:** Overnight schedule or manual

## Pre-Reflection Validation

- [ ] 1. >= 1 daily file found in `data/intelligence/daily/`
- [ ] 2. patterns.yaml exists and is valid YAML
- [ ] 3. Extraction criteria loaded (rules/extraction-criteria.md)
- [ ] 4. Forgetting curve formula available (rules/forgetting-curve.md)

## Pattern Mining

- [ ] 5. >= 1 learning candidate identified (if any learnings in dailies)
- [ ] 6. Each candidate validated against 5 extraction criteria
- [ ] 7. Rejected candidates logged with reason
- [ ] 8. Duplicate patterns identified and marked for reinforcement

## Decay Recalculation

- [ ] 9. All existing patterns have decay_score recalculated
- [ ] 10. Decay formula applied: e^(-rate × days_since_observed)
- [ ] 11. Decay scores in valid range: 0.0 <= score <= 1.0
- [ ] 12. Patterns with decay < 0.1 flagged for archive

## Reflection Output

- [ ] 13. Reflection markdown generated with all sections
- [ ] 14. New patterns listed with decay_score (+ verification_count if available)
- [ ] 15. Reinforced patterns listed
- [ ] 16. Archive candidates listed
- [ ] 17. Reflection file saved to `data/intelligence/reflections/`

## Data Integrity

- [ ] 18. patterns.yaml updated (new patterns merged)
- [ ] 19. Metadata updated: total_patterns, last_updated, etc.
- [ ] 20. Backup created before modifications (patterns.yaml.bak)
- [ ] 21. File format remains valid YAML

---

**Result:** PASS | PASS WITH WARNINGS | FAIL

**Failure Recovery:**
- If pattern validation fails: Check extraction criteria — may be too strict
- If decay calc error: Inspect rule logic, use fallback formula
- If reflection gen fails: Create minimal reflection (timestamp + summary)
- If patterns.yaml corruption: Restore from backup, re-run reflect
