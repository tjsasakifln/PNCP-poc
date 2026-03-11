# DEBT-130: E2E Python Version Fix
**Priority:** P2
**Effort:** 5min
**Owner:** @devops
**Sprint:** Week 1, Day 1

## Context

The E2E workflow (`.github/workflows/e2e.yml`) uses Python 3.11 while the backend runs Python 3.12 in production and all other CI workflows. This mismatch means E2E tests could pass on 3.11 but fail on 3.12 (or vice versa), undermining CI reliability. A one-line fix.

## Acceptance Criteria

- [ ] AC1: `.github/workflows/e2e.yml` uses `python-version: '3.12'` (not `'3.11'`)
- [ ] AC2: E2E workflow passes with Python 3.12
- [ ] AC3: All other workflows already use 3.12 (verify, do not change)

## Technical Notes

Single line change in `.github/workflows/e2e.yml` (approximately line 48):
```yaml
# Before
python-version: '3.11'

# After
python-version: '3.12'
```

Verify by searching all workflows:
```bash
grep -r "python-version" .github/workflows/
```

All should show `3.12`. Fix any other mismatches found.

## Test Requirements

- [ ] E2E workflow runs successfully with Python 3.12 (verify via CI run)

## Files to Modify

- `.github/workflows/e2e.yml` -- Change python-version from 3.11 to 3.12

## Definition of Done

- [ ] AC1 pass (version updated)
- [ ] CI run confirms no regressions
- [ ] Code reviewed
