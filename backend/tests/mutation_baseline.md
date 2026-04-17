# Mutation Testing Baseline Report (STORY-6.6)

## Environment Status

**Date:** 2026-04-16
**Tool:** mutmut >= 2.4.0
**Config:** `backend/setup.cfg` `[mutmut]` section
**Modules targeted:** `filter/`, `llm_arbiter/`, `consolidation/`, `quota/`

### Windows Limitation

mutmut does **not** support native Windows (tracked in
[mutmut issue #397](https://github.com/boxed/mutmut/issues/397)).
The development environment is Windows 11 Pro and WSL2 is not available
(virtualization not enabled on this machine).

As a result, the local baseline run could not be completed.
**The authoritative baseline will be produced by the weekly CI job**
(`.github/workflows/mutation-testing.yml`) on the first Sunday run after
this branch is merged.

## Configuration

```ini
[mutmut]
paths_to_mutate=filter/,llm_arbiter/,consolidation/,quota/
tests_dir=tests/
runner=python -m pytest -x -q --timeout=30 --ignore=tests/fuzz --ignore=tests/integration
```

## Expected Scope (line counts)

| Module | Files | ~Lines | Estimated mutants |
|--------|-------|--------|-------------------|
| `filter/` | 9 | ~2 900 | ~500-700 |
| `llm_arbiter/` | 6 | ~1 600 | ~250-350 |
| `consolidation/` | 5 | ~1 100 | ~150-250 |
| `quota/` | 6 | ~1 600 | ~250-350 |
| **Total** | **26** | **~7 200** | **~1 150-1 650** |

## Baseline Scores (CI — pending first run)

| Module | Total mutants | Killed | Survived | Timeout | Score |
|--------|---------------|--------|----------|---------|-------|
| `filter/` | TBD | TBD | TBD | TBD | TBD |
| `llm_arbiter/` | TBD | TBD | TBD | TBD | TBD |
| `consolidation/` | TBD | TBD | TBD | TBD | TBD |
| `quota/` | TBD | TBD | TBD | TBD | TBD |

_Table will be populated automatically by the weekly CI artifact after first run._

## AC3 Status

**AC3 baseline medido: NOT YET — blocked by Windows environment limitation.**

The >70% target remains in place. After the first CI run produces real scores,
update this table and mark AC3 `[x]` if all four modules reach ≥ 70%.
If any module is below 70%, create follow-up **STORY-6.6.1 (mutation tuning)**
with targeted test additions for surviving mutants.

See `.github/workflows/mutation-testing.yml` for the automated weekly schedule.

## Survivor Analysis (CI — pending)

Top surviving mutants will be listed here after first CI run using:

```bash
mutmut show <id>
```

for IDs from `mutmut results --suspicious` and `mutmut results --survived`.

## How to Run Locally (Linux / WSL)

```bash
cd backend
pip install -r requirements-dev.txt

# Single module (fastest first)
mutmut run --paths-to-mutate=consolidation/
mutmut run --paths-to-mutate=quota/
mutmut run --paths-to-mutate=llm_arbiter/
mutmut run --paths-to-mutate=filter/

# Results summary
mutmut results

# Inspect a surviving mutant
mutmut show <id>
```

Time-box: 20 minutes per module. Interrupt with Ctrl+C if limit exceeded.
