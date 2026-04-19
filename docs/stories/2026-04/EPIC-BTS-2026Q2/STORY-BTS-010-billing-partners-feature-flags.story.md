# STORY-BTS-010 — Billing, Partners, Feature Flags + Misc (15+ testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1
**Effort:** S (2-3h)
**Agents:** @dev + @qa
**Status:** Ready

---

## Contexto

15+ testes cobrindo billing ops (partners, dunning, Stripe events purge), feature flags admin, digest jobs, e misc (PNCP date formats, client requires modalidade, ingestion loader, security critical, etc.). Heterogêneo — pode precisar dividir em sub-tasks durante implement.

---

## Arquivos (tests)

**Billing & Partners (8):**
- `backend/tests/test_partners.py` (5 failures)
- `backend/tests/test_dunning.py` (2 failures)
- `backend/tests/test_harden028_stripe_events_purge.py` (1 failure)

**Feature Flags (6):**
- `backend/tests/test_feature_flag_matrix.py` (4 failures)
- `backend/tests/test_feature_flags_admin.py` (2 failures)

**Misc (9+):**
- `backend/tests/test_digest_job.py` (1 failure)
- `backend/tests/test_pncp_date_formats.py` (4 failures)
- `backend/tests/test_pncp_422_dates.py` (1 failure)
- `backend/tests/test_pncp_client_requires_modalidade.py` (1 failure)
- `backend/tests/test_ingestion_loader.py` (1 failure)
- `backend/tests/test_sector_coverage_audit.py` (1 failure)
- `backend/tests/test_jsonb_storage_governance.py` (1 failure)
- `backend/tests/test_debt101_security_critical.py` (1 failure)
- `backend/tests/test_debt102_jwt_pncp_compliance.py` (1 failure)
- `backend/tests/test_debt009_database_rls_retention.py` (1 failure)
- `backend/tests/test_debt008_backend_stability.py` (1 failure)
- `backend/tests/test_blog_stats.py` (2 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest` em todos os arquivos acima retorna exit code 0 (~25 tests PASS).
- [ ] AC2: CI verde.
- [ ] AC3: RCA por sub-grupo (billing, feature flags, misc). Misc pode revelar prod bugs — escalar conforme necessário.
- [ ] AC4: Cobertura não caiu.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] `test_partners`: validar ENABLE_NEW_PRICING flag + rota paths
- [ ] `test_feature_flag_matrix`: se o matrix é data-driven, verificar se feature flags de prod mudaram
- [ ] `test_pncp_date_formats` (4): verificar se PNCP API mudou formato de data recentemente
- [ ] `test_debt101_security_critical`: fix prioritário — qualquer regressão aqui é P0

---

## Dependências

- **Bloqueado por:** BTS-001 (quota), BTS-003 (DB/plan reconciliation)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready. Story é larga e heterogênea — split em implement se RCA revelar >2 causas não triviais.
