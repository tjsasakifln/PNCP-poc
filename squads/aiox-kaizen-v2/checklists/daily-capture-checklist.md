# Daily Capture Checklist

**Task:** capture-daily.md | **Executor:** memory-keeper | **Trigger:** Stop hook or *capture

## Pre-Capture Validation

- [ ] 1. Daily YAML template loaded (daily-digest-tmpl.yaml)
- [ ] 2. Git log available (`git log --since=today` succeeds)
- [ ] 3. `data/intelligence/daily/` directory exists + writable

## Capture Execution

- [ ] 4. Date field populated (YYYY-MM-DD format)
- [ ] 5. Session count accurate (>= 1)
- [ ] 6. Providers active list non-empty
- [ ] 7. Activity summary present (1-2 sentences)

## Learnings Quality

- [ ] 8. Learnings array has >= 1 entry (if learnings today)
- [ ] 9. Each learning is specific, not generic ("Fixed Windows hook issue" not "Did work")
- [ ] 10. Learnings are verified in context (traceable to code/decision)

## File Validation

- [ ] 11. Valid YAML syntax (`yaml_parse` succeeds)
- [ ] 12. File size <= 3KB (pass with warning if 3-5KB)

## Optional but Encouraged

- [ ] 13. Highlights array populated (unusual findings)
- [ ] 14. Decisions array populated (key choices made)
- [ ] 15. Stories touched listed (story IDs worked on)
- [ ] 16. Agents involved listed (which agents ran)

## Post-Capture Verification

- [ ] 17. File created at `data/intelligence/daily/YYYY-MM-DD.yaml`
- [ ] 18. File timestamp = today
- [ ] 19. Checklist passes: >= 11/12 mandatory items

---

**Result:** PASS | PASS WITH WARNINGS | FAIL

**Failure Recovery:**
- If FAIL: Re-run capture with all mandatory fields populated
- If WARN (size > 3KB): Trim learnings to essential only, retry
- If file missing: Check `data/intelligence/daily/` permissions
