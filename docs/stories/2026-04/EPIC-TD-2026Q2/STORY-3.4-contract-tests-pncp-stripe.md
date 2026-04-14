# STORY-3.4: Contract Tests PNCP/Stripe (TD-QA-062)

**Priority:** P1 (regression prevention — TD-SYS-002 PNCP page-size breaking poderia ter sido detectado)
**Effort:** S (8-12h)
**Squad:** @qa + @dev
**Status:** Draft
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

- [ ] Gravar 10 responses sample de cada API em `tests/snapshots/`
- [ ] PNCP: search responses por modalidade
- [ ] PCP v2: search responses
- [ ] ComprasGov v3: search responses
- [ ] Stripe webhook: invoice.paid, customer.subscription.deleted, etc.

### AC2: Contract validation

- [ ] Test compara live API response shape vs snapshot
- [ ] Diff alerta em CI se shape muda (não values)
- [ ] Tools: Pact, JSON Schema validation, ou simple jsonschema

### AC3: Weekly CI run

- [ ] `.github/workflows/contract-tests.yml` weekly schedule
- [ ] Sentry alert se contract fails
- [ ] Manual trigger para re-baseline

### AC4: Documentation

- [ ] Como adicionar novo contract test
- [ ] Como re-baseline quando API legitimately muda

---

## Tasks / Subtasks

- [ ] Task 1: Tool selection (Pact vs JSON Schema)
- [ ] Task 2: Record snapshots
- [ ] Task 3: Validation tests
- [ ] Task 4: CI workflow
- [ ] Task 5: Documentation

## Dev Notes

- PNCP TD-SYS-002 (page size 50) seria detectado por shape comparison
- Stripe webhooks já tem signature verification mas shape pode mudar

## Testing

- Tests rodam em CI weekly
- Manual trigger funciona

## Definition of Done

- [ ] Snapshots + validation + weekly CI + docs

## Risks

- **R1**: External APIs flaky → false positives — mitigation: retry 3x antes de fail
- **R2**: Contract baselining quando API muda legitimately — mitigation: re-record workflow + PR review

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
