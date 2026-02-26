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

- [ ] AC1: `.github/workflows/deploy.yml` line ~120 — remover `-y` de `railway variables set`
- [ ] AC2: `backend/tests/test_story280_boleto_pix.py` line 19 — remover `from fastapi import HTTPException`
- [ ] AC3: Regenerar OpenAPI snapshot: `pytest --snapshot-update tests/snapshots/`
- [ ] AC4: E2E workflow: investigar e corrigir missing `server.js` em standalone build
- [ ] AC5: Fix event loop RuntimeError em `test_watchdog_uses_new_timeout` e `test_paid_plan_can_post_buscar`
- [ ] AC6: Todos os 4 workflows GitHub Actions passando em verde

## Definition of Done

- [ ] `gh run list --limit 5` mostra todos os workflows passing
- [ ] PR merged
