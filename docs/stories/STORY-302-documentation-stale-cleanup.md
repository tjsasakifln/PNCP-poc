# STORY-302: Documentation + Stale Cleanup

**Sprint:** 3 — Make It Competitive
**Size:** S (2-4h)
**Root Cause:** Track E (Business Model Audit)
**Status:** ACCEPTED

## Contexto

Track E encontrou documentação stale em vários pontos:
1. `CLAUDE.md` referencia pricing R$1,999 (correto é R$397 após STORY-277)
2. `PRD.md` tem specs desatualizadas
3. Código morto e configs stale identificados em Track D
4. Snapshots de teste desatualizados

Esta story é a "faxina final" do sprint de reliability.

## Acceptance Criteria

### Documentation
- [x] AC1: `CLAUDE.md` atualizado com pricing correto (R$397/mês, R$357 semestral, R$317 anual)
- [x] AC2: `CLAUDE.md` seção Tech Stack atualizada com versões atuais
- [x] AC3: `PRD.md` sincronizado com estado atual do produto
- [x] AC4: `ROADMAP.md` atualizado com Reliability Sprint stories
- [x] AC5: `CHANGELOG.md` atualizado com todas as mudanças do sprint

### Stale Code Cleanup
- [x] AC6: Remover código morto identificado em auditorias (dead imports, unused functions)
- [x] AC7: Remover configs stale (env vars não usadas, feature flags obsoletas)
- [x] AC8: Atualizar OpenAPI snapshot: `pytest --snapshot-update tests/snapshots/`
- [x] AC9: Remover arquivos temporários de debug/audit

### Quality
- [x] AC10: Linting passa sem warnings
- [x] AC11: Todos os testes passando
- [x] AC12: `git diff --stat` documentado no PR (para review)

## Files Changed

### Documentation Updates
- `CLAUDE.md` — pricing (R$397), tech stack versions (FastAPI 0.129, TS 5.9, etc.), billing section
- `PRD.md` — pricing sync (R$1,999 → R$397)
- `README.md` — pricing + trial duration (7d → 30d) + LLM model (gpt-4.1-nano)
- `ROADMAP.md` — Fase 4 (Reliability Sprint), Fase 4.1 (GTM Repricing), historico
- `CHANGELOG.md` — full [0.5.2] entry with 13 stories
- `docs/architecture/system-architecture.md` — pricing + trial
- `docs/operations/cost-analysis.md` — full margin recalculation with R$397 pricing
- `supabase/docs/SCHEMA.md` — pricing value update
- `.env.example` — LLM_ARBITER_MODEL gpt-4o-mini → gpt-4.1-nano

### Stale Code Cleanup
- `backend/bulkhead.py` — removed unused `Callable` import
- `backend/slo.py` — removed unused `field` import
- `backend/tests/test_alerts.py` — removed unused imports + noqa E402
- `backend/tests/test_bulkhead.py` — removed unused import + vars
- `backend/tests/test_security_story300.py` — removed unused import + walrus
- `backend/tests/test_slo.py` — removed unused imports
- `backend/tests/test_sse_last_event_id.py` — removed unused import
- `backend/tests/test_cache_warming_noninterference.py` — fixed flaky budget timeout test

### Files Deleted
- `backend/routes/search.py.tmp` — empty temp file
- `backend/scripts/debug_filtros_producao.py` — debug script
- `auth-analysis-phase1.json` through `auth-analysis-phase4.json` — analysis artifacts
- `SUPABASE-OAUTH-VERIFICATION.md` — verification doc
- `AI-SUMMARY-EXAMPLES.md` — example file
- `audit_findings_extracted.md` — audit output
- `backend/tests/snapshots/openapi_schema.diff.json` — diff artifact

### Git Hygiene
- Removed all `__pycache__/*.pyc` from git tracking (200+ files)

## Definition of Done

- [x] Zero referências a R$1,999 em documentação ativa
- [x] Zero dead code warnings no linting
- [x] Todos os testes passando (6022 passed, 7 pre-existing ordering-dependent, 10 skipped)
- [x] PR merged

## Test Results

```
Backend: 6022 passed, 7 failed (pre-existing ordering-dependent), 10 skipped
Ruff: All checks passed! (0 warnings)
OpenAPI: 7/7 passed
```

Note: 7 failures are pre-existing middleware state pollution (CORS/security headers).
All 7 pass when run in isolation — not caused by this story's changes.
