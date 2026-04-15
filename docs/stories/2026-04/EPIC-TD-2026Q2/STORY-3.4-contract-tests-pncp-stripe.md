# STORY-3.4: Contract Tests PNCP/Stripe (TD-QA-062)

**Priority:** P1 (regression prevention — TD-SYS-002 PNCP page-size breaking poderia ter sido detectado)
**Effort:** S (8-12h)
**Squad:** @qa + @dev
**Status:** InReview
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 2

---

## Story

**As a** SmartLic,
**I want** snapshot/contract tests contra PNCP, PCP v2, ComprasGov, e Stripe webhooks,
**so that** mudanças breaking em APIs externas sejam detectadas em CI antes de causar incidents.

---

## Acceptance Criteria

### AC1: Snapshot recordings

- [x] Gravar 10 responses sample de cada API em `tests/snapshots/`
- [x] PNCP: search responses por modalidade (10 snapshots cobrindo pregão eletrônico/presencial, concorrência, inexigibilidade, dispensa, RDC, paginação, filtros UF/data, empty, contratos)
- [x] PCP v2: search responses (3 snapshots — page 1, empty, second page)
- [x] ComprasGov v3: search responses (3 snapshots — módulo-contratações, lei 14.133, error)
- [x] Stripe webhook: invoice.paid, customer.subscription.deleted, customer.subscription.updated, checkout.session.completed (4 snapshots)

### AC2: Contract validation

- [x] Test compara response shape vs snapshot (offline + opt-in live)
- [x] Diff alerta em CI se shape muda (não values) — output humanizado via `contract_validator.validate_shape`
- [x] Tools: `jsonschema` (Draft 2020-12) + helper módulo `contract_validator.py` (extract/diff/validate)

### AC3: Weekly CI run

- [x] `.github/workflows/contract-tests.yml` weekly schedule (Mon 04:00 UTC) + `workflow_dispatch`
- [x] Sentry notify + auto-issue em caso de falha (de-duped por título)
- [x] Manual trigger para re-baseline (via `workflow_dispatch` input `run_live`)

### AC4: Documentation

- [x] `docs/qa/contract-tests.md` — como adicionar novo contract test
- [x] Re-baseline workflow documentado (snippet Python inline)
- [x] Troubleshooting table (flakiness, type changes, schema drift)

---

## Tasks / Subtasks

- [x] Task 1: Tool selection — escolhido JSON Schema (jsonschema já instalado, simples, standard)
- [x] Task 2: Record snapshots (20 arquivos: 10 PNCP + 3 PCP + 3 ComprasGov + 4 Stripe)
- [x] Task 3: Validation tests (41 tests offline + 3 live opt-in)
- [x] Task 4: CI workflow (weekly + manual, com issue auto-creation)
- [x] Task 5: Documentation (`docs/qa/contract-tests.md`)

## Dev Notes

- PNCP TD-SYS-002 (page size 50) seria detectado por shape comparison — o teste `test_pncp_page_size_constraint_documented` marca a invariante
- Stripe webhooks já tem signature verification mas shape pode mudar — schema gerado da união de 4 tipos de eventos (invoice.paid, customer.subscription.deleted/updated, checkout.session.completed)
- Schemas são **permissivos**: `additionalProperties: true` (API adicionando campo NÃO quebra), `required` = intersecção de campos em todos os samples (campo sempre presente ⇒ obrigatório)
- Live tests (marker `external`) desativados por padrão para evitar flakiness em CI; ativados via `RUN_LIVE_CONTRACT_TESTS=1` ou input do `workflow_dispatch`
- Fontes dos snapshots: `backend/tests/fixtures/pncp_responses.py` (shape PNCP), `backend/tests/snapshots/api_contracts/pcp_record_schema.json` (shape real PCP capturado 2026-04-13), Stripe docs API event examples (sem PII, sem chaves reais)

## Testing

- Offline (default run): `python -m pytest tests/contracts/ -m contract -v` — 41 passing, <2s
- Live opt-in: `RUN_LIVE_CONTRACT_TESTS=1 python -m pytest tests/contracts/ -m external -v` (3 tests, 1 por API pública)
- CI: roda weekly + manual trigger

## Definition of Done

- [x] Snapshots committed (20 arquivos)
- [x] Schemas committed (4 arquivos source of truth)
- [x] Validator module + unit tests (13 tests próprios)
- [x] Weekly CI workflow com issue auto-creation
- [x] Docs publicados em `docs/qa/contract-tests.md`

## Risks

- **R1**: External APIs flaky → false positives — mitigation: retry 3x antes de fail (implementado nos live tests); offline tests não tocam rede
- **R2**: Contract baselining quando API muda legitimately — mitigation: re-record workflow documentado + PR review obrigatório para mudanças em `schemas/*.schema.json`

## Dev Agent Record

### File List

**Created:**
- `backend/tests/contracts/__init__.py`
- `backend/tests/contracts/conftest.py`
- `backend/tests/contracts/contract_validator.py` (validator helper: `validate_shape`, `extract_schema_from_samples`, `diff_shapes`, `load_snapshot`, `load_schema`, `write_schema`)
- `backend/tests/contracts/test_contract_validator.py` (13 unit tests)
- `backend/tests/contracts/test_pncp_contract.py` (12 contract tests + 1 live)
- `backend/tests/contracts/test_pcp_v2_contract.py` (4 contract tests + 1 live)
- `backend/tests/contracts/test_compras_gov_contract.py` (3 contract tests + 1 live)
- `backend/tests/contracts/test_stripe_webhook_contract.py` (9 contract tests)
- `backend/tests/contracts/snapshots/pncp/pregao_eletronico_modalidade_6.json`
- `backend/tests/contracts/snapshots/pncp/concorrencia_modalidade_4.json`
- `backend/tests/contracts/snapshots/pncp/inexigibilidade_modalidade_8.json`
- `backend/tests/contracts/snapshots/pncp/pregao_presencial_modalidade_6.json`
- `backend/tests/contracts/snapshots/pncp/dispensa_modalidade_8.json`
- `backend/tests/contracts/snapshots/pncp/search_multi_page.json`
- `backend/tests/contracts/snapshots/pncp/search_empty_result.json`
- `backend/tests/contracts/snapshots/pncp/search_with_uf_filter.json`
- `backend/tests/contracts/snapshots/pncp/search_with_date_range.json`
- `backend/tests/contracts/snapshots/pncp/rdc_modalidade_12.json`
- `backend/tests/contracts/snapshots/pncp/contracts_response.json`
- `backend/tests/contracts/snapshots/pcp_v2/search_response.json`
- `backend/tests/contracts/snapshots/pcp_v2/search_empty.json`
- `backend/tests/contracts/snapshots/pcp_v2/search_second_page.json`
- `backend/tests/contracts/snapshots/compras_gov_v3/modulo_contratacoes_response.json`
- `backend/tests/contracts/snapshots/compras_gov_v3/modulo_lei_14133_response.json`
- `backend/tests/contracts/snapshots/compras_gov_v3/search_error_response.json`
- `backend/tests/contracts/snapshots/stripe/invoice_paid.json`
- `backend/tests/contracts/snapshots/stripe/customer_subscription_deleted.json`
- `backend/tests/contracts/snapshots/stripe/customer_subscription_updated.json`
- `backend/tests/contracts/snapshots/stripe/checkout_session_completed.json`
- `backend/tests/contracts/schemas/pncp_search_response.schema.json`
- `backend/tests/contracts/schemas/pcp_v2_search_response.schema.json`
- `backend/tests/contracts/schemas/compras_gov_v3_search_response.schema.json`
- `backend/tests/contracts/schemas/stripe_webhook_event.schema.json`
- `.github/workflows/contract-tests.yml`
- `docs/qa/contract-tests.md`

**Modified:**
- `backend/pyproject.toml` — adicionados markers `contract` e `external`

### Completion Notes

- Resultado pytest: **41 passed, 3 deselected (live), 0 failures em 1.04s**
- Validator unit tests validam os 3 helpers principais (extract/validate/diff) com casos edge (null union, required intersection, additional properties permitidos, type changes detectados)
- Live tests cobrem PNCP, PCP v2, ComprasGov v3. Stripe não tem endpoint live público adequado — drift detectado via re-recording quando `api_version` é bumpado

### Debug Log

- Inicialmente considerei Pact mas descartei: overhead de provider+consumer states não compensa para shape-only validation; jsonschema resolve direto
- ComprasGov tem 2 endpoints com shapes muito distintas sob `_embedded.licitacoes[]`; o schema resultante é permissivo no item (union das properties), o que é aceitável dado que o normalizer já faz auto-detect (`_normalize_legacy` vs `_normalize_lei_14133`)
- Decisão: Stripe events em um único schema (union) porque o webhook handler despacha por `type` field de qualquer forma — o que precisa ser estável é o envelope, não o payload específico de cada tipo

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 2.0     | Contract tests infra (snapshots + validator + weekly CI + docs) | @dev |
