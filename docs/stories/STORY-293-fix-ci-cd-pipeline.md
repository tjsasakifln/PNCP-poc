# STORY-293: Fix CI/CD Pipeline

**Sprint:** 0 — Make It Work
**Size:** S (2-4h)
**Root Cause:** Track D findings
**Industry Standard:** CI/CD green = deploy gate

## Contexto

Track D (Infrastructure Audit) encontrou 3 problemas que mantêm CI/CD vermelho:
1. Deploy workflow: Railway CLI `-y` flag não suportada em `variables set`
2. Backend lint: unused import em `test_story280_boleto_pix.py`
3. E2E: standalone build faltando `server.js`

## Acceptance Criteria

- [x] AC1: `.github/workflows/deploy.yml` line ~120 — remover `-y` de `railway variables set`
- [x] AC2: `backend/tests/test_story280_boleto_pix.py` line 19 — remover `from fastapi import HTTPException`
- [x] AC3: Regenerar OpenAPI snapshot: `pytest --snapshot-update tests/snapshots/`
- [x] AC4: E2E workflow: investigar e corrigir missing `server.js` em standalone build
- [x] AC5: Fix event loop RuntimeError em `test_watchdog_uses_new_timeout` e `test_paid_plan_can_post_buscar`
- [ ] AC6: Todos os 4 workflows GitHub Actions passando em verde

## Definition of Done

- [ ] `gh run list --limit 5` mostra todos os workflows passing
- [ ] PR merged

## Implementation Notes

### AC1: Deploy workflow `-y` flag
Removed `-y` from `railway variables set` command (line 120). Kept `-y` on `railway redeploy` (lines 128, 190) where it IS supported.

### AC2: Unused import
Removed `from fastapi import HTTPException` — confirmed unused across all 768 lines of `test_story280_boleto_pix.py`.

### AC3: OpenAPI snapshot
Deleted old snapshot and diff, regenerated via `pytest tests/test_openapi_schema.py`. All 7 schema tests pass.

### AC4: Standalone build `server.js`
**Root cause:** Next.js 16 defaults to Turbopack for `next build`, but Turbopack has known issues with `output: 'standalone'` ([vercel/next.js#77721](https://github.com/vercel/next.js/discussions/77721)). Combined with `@sentry/nextjs` webpack plugins, the build fails silently.
**Fix:** Added `--webpack` flag to `next build` in `package.json` build script to explicitly use webpack, ensuring standalone output generates `server.js`.

### AC5: Event loop RuntimeError
- `test_watchdog_uses_new_timeout`: Already replaced by STORY-292 async search pattern (`TestT8AsyncSearchExecution` in `test_search_async.py`). No fix needed.
- `test_paid_plan_can_post_buscar`: Converted from sync test using `asyncio.get_event_loop().run_until_complete()` to proper async test with `@pytest.mark.asyncio` + `await`.

## File List

| File | Change |
|------|--------|
| `.github/workflows/deploy.yml` | Removed `-y` from `railway variables set` |
| `backend/tests/test_story280_boleto_pix.py` | Removed unused `HTTPException` import |
| `backend/tests/snapshots/openapi_schema.json` | Regenerated snapshot |
| `backend/tests/test_trial_block.py` | Fixed async test pattern |
| `frontend/package.json` | Added `--webpack` to `next build` |
