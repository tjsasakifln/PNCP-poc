# STORY-BTS-010b — PNCP, Security & Infra Misc (13 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1 — Security critical path + PNCP ingestion (data source core)
**Effort:** M (3-5h)
**Agents:** @dev + @qa + @architect (se security tests revelarem prod vuln)
**Status:** Ready

---

## Escopo

**IN:**
- Fix de suítes de PNCP date format/422 handling/client params
- Security critical + JWT PNCP compliance + RLS retention + backend stability
- JSONB storage governance + sector coverage audit + blog stats + ingestion loader

**OUT:**
- Billing/partners/feature flags (movidos para BTS-010a)
- PNCP canary test (coberto por STORY-4.5 existente)
- Refactor em `backend/clients/pncp/*` além de strict test scope

---

## Contexto

Split da STORY-BTS-010 original (Opção A @po review) — agrupa **13 testes** em domínio coerente: **PNCP ingestion + security/compliance + infra misc**. Complementa BTS-010a (billing/flags).

⚠️ **Security priority:** `test_debt101_security_critical` é P0 se revelar regressão real — escalar para @architect imediatamente.

---

## Valor

- **PNCP data integrity** — date formats + 422 retry + modalidade params são pré-requisito do pipeline `/buscar`
- **Security compliance** — JWT PNCP auth + RLS retention são guard-rails de data exposure
- **Backend stability foundation** — debt008/009 cobrem invariantes que se quebrarem afetam operação

---

## Riscos

- **`test_debt101_security_critical`** pode revelar CVE-like vulnerability. Mitigação: se fail tem natureza de exploit real (não mock drift), abrir issue P0 + Sentry alert.
- **PNCP API change** — se 4 tests de date formats falharem por mudança real da API (não drift), pode afetar ingestion em produção. Mitigação: cruzar com STORY-4.5 PNCP canary status antes de mergear.

---

## Arquivos (tests — 13 testes exatos)

**PNCP (6 testes em 3 arquivos):**
- `backend/tests/test_pncp_date_formats.py` (4 failures)
- `backend/tests/test_pncp_422_dates.py` (1 failure)
- `backend/tests/test_pncp_client_requires_modalidade.py` (1 failure)

**Security & Compliance (4 testes em 4 arquivos):**
- `backend/tests/test_debt101_security_critical.py` (1 failure)
- `backend/tests/test_debt102_jwt_pncp_compliance.py` (1 failure)
- `backend/tests/test_debt009_database_rls_retention.py` (1 failure)
- `backend/tests/test_debt008_backend_stability.py` (1 failure)

**Infra Misc (3 testes em 3 arquivos):**
- `backend/tests/test_sector_coverage_audit.py` (1 failure)
- `backend/tests/test_jsonb_storage_governance.py` (1 failure)
- `backend/tests/test_blog_stats.py` (2 failures — conta como 1 arquivo, 2 tests)
- `backend/tests/test_ingestion_loader.py` (1 failure)

**Total: 13 failures em 10 arquivos.**

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_pncp_date_formats.py backend/tests/test_pncp_422_dates.py backend/tests/test_pncp_client_requires_modalidade.py backend/tests/test_debt101_security_critical.py backend/tests/test_debt102_jwt_pncp_compliance.py backend/tests/test_debt009_database_rls_retention.py backend/tests/test_debt008_backend_stability.py backend/tests/test_sector_coverage_audit.py backend/tests/test_jsonb_storage_governance.py backend/tests/test_blog_stats.py backend/tests/test_ingestion_loader.py -v --timeout=30` retorna exit code 0 (13/13 PASS).
- [ ] AC2: `backend-tests.yml` run mostra 10 arquivos com **0 failed**. Link no Change Log.
- [ ] AC3: RCA por sub-grupo (PNCP API drift vs assertion drift, security: mock vs prod vuln, RLS: migration missing vs policy drift).
- [ ] AC4: Cobertura backend não caiu (threshold 70%). Se `test_debt101_security_critical` revelar prod vuln, AC4 secundário: vulnerability fixed com regression test.
- [ ] AC5 (NEGATIVO): zero quarantine novas.

---

## Investigation Checklist

- [ ] Para `test_pncp_*`: cruzar com `backend/jobs/cron/pncp_canary.py` status via `smartlic_pncp_max_page_size_changed_total` metric — se canary triggered, PNCP API mudou e teste está correto em falhar
- [ ] Para `test_debt101_security_critical`: **PAUSAR e escalar @architect** se fail é exploit-shaped (path traversal, SQL injection, auth bypass). Não mergear com vuln aberta.
- [ ] Para `test_debt009_database_rls_retention`: validar que migrations RLS estão aplicadas em `supabase/migrations/`
- [ ] Para `test_blog_stats`: verificar se refactor de `routes/blog.py` alterou shape de resposta

---

## Dependências

- **Bloqueado por:** BTS-001 (quota), BTS-003 (DB schema)
- **Bloqueia:** nenhum
- **Cross-ref:** STORY-4.5 (PNCP canary) — consultar antes de tocar PNCP tests

---

## Change Log

- **2026-04-19** — @sm (River): Story criada do split BTS-010 (Opção A do @po review). Status Ready. Security critical flagged.
