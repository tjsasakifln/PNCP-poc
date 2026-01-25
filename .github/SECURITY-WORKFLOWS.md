# Security Workflows Documentation

## Overview

This repository uses three security workflows configured in `.github/workflows/codeql.yml`:

1. **CodeQL Security Scan** - Static analysis for Python and JavaScript/TypeScript
2. **Secret Scanning** - TruffleHog OSS for detecting leaked credentials
3. **Dependency Review** - Checks for vulnerable dependencies in PRs

## Workflow Triggers

### CodeQL Security Scan
- **Pull Requests:** Runs on all PRs targeting `main` or `master`
- **Push Events:** Runs on all pushes to `main` or `master`
- **Scheduled:** Every Monday at 00:00 UTC (weekly full scan)
- **Manual:** Can be triggered via workflow_dispatch

### Secret Scanning (TruffleHog)
- **Pull Requests:** Scans diff between PR head and base branch
- **Push Events:** **SKIPPED on main branch** (see "Known Limitations" below)
- **Scheduled:** Every Monday at 00:00 UTC (full repository scan)
- **Manual:** Can be triggered via workflow_dispatch

### Dependency Review
- **Pull Requests Only:** Analyzes dependency changes in PRs
- **Configuration:** Fails on `high` severity, denies `GPL-3.0` and `AGPL-3.0` licenses

## Known Limitations

### TruffleHog BASE==HEAD Issue

**Problem:** TruffleHog GitHub Action fails when `BASE` and `HEAD` resolve to the same commit, which happens on push events to `main` because:
```yaml
base: ${{ github.event.repository.default_branch }} # Resolves to "main"
head: HEAD                                           # Also points to main HEAD
```

**Solution:** Skip secret scanning on `push` events to `main` branch:
```yaml
if: github.event_name != 'push' || github.ref != 'refs/heads/main'
```

**Coverage Strategy:**
1. **PRs:** TruffleHog scans all pull request diffs before merge
2. **Scheduled Scans:** Weekly full repository scan on Mondays
3. **Manual Triggers:** Workflow can be run manually anytime

**Rationale:** This approach ensures comprehensive coverage while avoiding the BASE==HEAD error:
- All code changes are scanned in PRs before reaching main
- Weekly scans catch any edge cases or manual commits
- No security gaps despite skipping push events

## Security Best Practices

### For Developers
1. **Never commit secrets** - Use environment variables or secret management
2. **Run pre-commit hooks** - Consider local TruffleHog scans
3. **Review security alerts** - Check GitHub Security tab regularly
4. **Keep dependencies updated** - Address Dependabot alerts promptly

### For Reviewers
1. **Check security workflow results** - All checks must pass before merge
2. **Review TruffleHog findings** - Even `--only-verified` can have false positives
3. **Validate dependency changes** - Ensure no high-severity vulnerabilities
4. **CodeQL alerts** - Review and triage any new findings

## Troubleshooting

### TruffleHog False Positives
If TruffleHog flags non-secret content:
1. Add to `.truffleignore` file (if using config)
2. Or use `extra_args: --exclude-paths=path/to/exclude`

### CodeQL Autobuild Failures
For Python/JavaScript build issues:
1. Check language file detection logic (lines 32-43)
2. Verify dependencies are installable
3. Review autobuild logs for specific errors

### Dependency Review Blocking Legitimate Packages
If a safe dependency is flagged:
1. Review the specific vulnerability or license issue
2. Update `deny-licenses` list if appropriate
3. Add exceptions via `allow-licenses` if needed

## References

- [CodeQL Documentation](https://codeql.github.com/docs/)
- [TruffleHog GitHub Action](https://github.com/trufflesecurity/trufflehog#octocat-trufflehog-github-action)
- [Dependency Review Action](https://github.com/actions/dependency-review-action)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)

---

**Last Updated:** 2026-01-25
**Issue:** #40 - fix(ci): CodeQL Security Scan / Secret Scanning falhando na main
