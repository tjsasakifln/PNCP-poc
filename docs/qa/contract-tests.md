# Contract Tests (STORY-3.4)

> Related: [EPIC-TD-2026Q2](../../docs/stories/2026-04/EPIC-TD-2026Q2/),
> [STORY-3.4](../../docs/stories/2026-04/EPIC-TD-2026Q2/STORY-3.4-contract-tests-pncp-stripe.md)

## Why contract tests

SmartLic depends on four external APIs:

| API | Priority | Breaking-change risk |
|-----|----------|---------------------|
| PNCP (`pncp.gov.br`) | Primary source | High — Feb 2026 silently dropped `tamanhoPagina` from 500 → 50 (TD-SYS-002) |
| PCP v2 (`portaldecompraspublicas.com.br`) | Secondary | Medium |
| ComprasGov v3 (`dadosabertos.compras.gov.br`) | Tertiary | Currently offline (2026-03), expected to return |
| Stripe (webhooks) | Billing | Low — Stripe pins `api_version`, but events can add fields |

Contract tests detect breaking changes in **response shape** (fields, types,
required-ness) before they hit production. Value regressions (e.g. bad
data) are still covered by the normal test suite and runtime monitoring.

## Architecture

```
backend/tests/contracts/
├── contract_validator.py         # validate_shape, extract_schema_from_samples, diff_shapes
├── conftest.py                   # pncp_schema, pcp_v2_schema, ... fixtures + load_snapshot
├── snapshots/
│   ├── pncp/            (10 JSON files — real response bodies)
│   ├── pcp_v2/          (3)
│   ├── compras_gov_v3/  (3)
│   └── stripe/          (4 webhook events)
├── schemas/                      # Source of truth — auto-generated from snapshots
│   ├── pncp_search_response.schema.json
│   ├── pcp_v2_search_response.schema.json
│   ├── compras_gov_v3_search_response.schema.json
│   └── stripe_webhook_event.schema.json
├── test_pncp_contract.py         # per-API test file
├── test_pcp_v2_contract.py
├── test_compras_gov_contract.py
├── test_stripe_webhook_contract.py
└── test_contract_validator.py    # unit tests for the helper itself
```

### Design choices

- **Permissive schemas.** `additionalProperties: true` — an API adding a
  new field is NOT a breaking change, so we don't fail on it. We only
  fail when required fields disappear or types change.
- **`required` = intersection.** A field is required only when present
  in every recorded sample. Optional / sometimes-null fields become
  union types (e.g. `["integer", "null"]`).
- **Default run is offline.** CI validates the committed snapshots
  against the committed schemas — no network, no flakiness.
- **Live checks are opt-in.** `RUN_LIVE_CONTRACT_TESTS=1` (or the
  `workflow_dispatch` form) hits the real APIs. Scheduled weekly.

## Running locally

```bash
cd backend

# Offline (default) — should be <2s, 41 tests
python -m pytest tests/contracts/ -m contract -v

# Live checks (opt-in — hits real APIs, may be flaky)
RUN_LIVE_CONTRACT_TESTS=1 python -m pytest tests/contracts/ -m external -v

# Both
RUN_LIVE_CONTRACT_TESTS=1 python -m pytest tests/contracts/ -v
```

## Adding a new contract test

### New snapshot for an existing API

1. Capture a real response body (from staging, a debug log, or an
   authenticated manual call). Strip any PII / secrets.
2. Save it to `backend/tests/contracts/snapshots/<api>/<case-name>.json`
   using the envelope:

   ```json
   {
     "_recorded_at": "YYYY-MM-DD",
     "_endpoint": "/v1/...",
     "_params": { "...": "..." },
     "response": { ... actual body ... }
   }
   ```

3. Re-generate the schema (see below) — OR just add it to the file list
   in `test_<api>_contract.py::SNAPSHOT_FILES` and confirm it still
   validates against the existing schema.
4. Run `pytest tests/contracts/test_<api>_contract.py -v`.

### New API entirely

1. Add a directory under `snapshots/` and record 3-10 samples.
2. Add a generator run to bootstrap the schema (see
   [Re-baselining](#re-baselining-when-an-api-legitimately-changes)).
3. Add a `<api>_schema` fixture to `conftest.py`.
4. Create `test_<api>_contract.py` following the shape of
   `test_pncp_contract.py`.
5. Update this document + the workflow if the new API should participate
   in the weekly run.

## Re-baselining (when an API legitimately changes)

If the API changed on purpose (new field, deprecated field, upgraded
`api_version`, etc.), the schema needs to be re-derived from updated
samples.

```bash
# 1. Record fresh samples under snapshots/<api>/
# 2. Re-generate the schema from those samples
cd backend
python - <<'PY'
import json, sys
sys.path.insert(0, ".")
from tests.contracts.contract_validator import (
    extract_schema_from_samples, write_schema, load_snapshot,
)

files = [
    # ... list all snapshot files for the API ...
    "pncp/pregao_eletronico_modalidade_6.json",
    # ...
]
samples = [load_snapshot(f)["response"] for f in files]
schema = extract_schema_from_samples(samples, title="PNCP Search Response")
path = write_schema("pncp_search_response.schema.json", schema)
print(f"Regenerated {path}")
PY

# 3. Review diff to confirm the changes match your expectation
git diff backend/tests/contracts/schemas/

# 4. Run the tests — they should all pass
python -m pytest tests/contracts/ -m contract -v
```

> **Policy:** any PR that modifies `schemas/*.schema.json` MUST have a
> reviewer sign-off. A schema change is a contract change — don't let it
> slip through on auto-merge.

## CI integration

- `.github/workflows/contract-tests.yml` runs:
  - **Weekly** (Mondays 04:00 UTC) — offline snapshot validation +
    optional live check if repo var `RUN_LIVE_CONTRACT_TESTS=true`.
  - **On demand** (`workflow_dispatch`) — accepts an input to also run
    live checks.
- On failure the workflow opens (or reuses) a GitHub issue labelled
  `contract-tests, bug, priority:high` with a pointer to the failed
  run. If `SENTRY_AUTH_TOKEN` is configured the workflow also files a
  Sentry user-feedback entry.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Offline tests fail locally | Schema out of sync with snapshots | Re-generate schema (above) or revert the snapshot change |
| Offline tests fail in CI but pass locally | Whitespace / line-ending diff in snapshot | Re-commit with LF endings (`dos2unix`) |
| Live test fails once | Transient network / rate limit | The test already retries 3x — just re-run |
| Live test fails repeatedly | API actually changed | Re-baseline + open a bug if the change is not benign |
| `MISSING_REQUIRED at root: field 'X'` | API stopped returning field X | Check the API changelog. If X is genuinely optional now, re-record samples that include the no-X case so the schema intersection marks it optional |
| `TYPE_MISMATCH at root.X: expected integer, got string` | API changed field type | Likely a breaking change — file an incident, don't just re-baseline |

## Related docs

- [AC from STORY-3.4](../../docs/stories/2026-04/EPIC-TD-2026Q2/STORY-3.4-contract-tests-pncp-stripe.md)
- [PNCP API constraints (CLAUDE.md)](../../CLAUDE.md#pncp-api-used-by-ingestion--legacy-fallback)
- [Stripe webhook handler](../../backend/webhooks/stripe.py)
