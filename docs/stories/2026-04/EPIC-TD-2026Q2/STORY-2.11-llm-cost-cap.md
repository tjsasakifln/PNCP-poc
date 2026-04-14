# STORY-2.11: LLM Monthly Cost Cap + Alerts (TD-SYS-018)

**Priority:** P1 (financial protection — runaway spending risk)
**Effort:** S (4-8h)
**Squad:** @dev + @architect quality gate
**Status:** Ready for Review
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** SmartLic,
**I want** cap mensal de custo LLM com alertas progressivos,
**so that** prompts inadvertidamente em loop ou abuso não cause bill surprise.

---

## Acceptance Criteria

### AC1: Token + cost tracking

- [x] Counter `LLM_COST_USD` + gauge `LLM_BUDGET_USD_MTD` + counter `LLM_BUDGET_REJECTIONS` em `metrics.py`
- [x] `track_llm_cost()` instrumenta `gerar_resumo` + `_log_token_usage` em llm_arbiter — fire-and-forget async

### AC2: Budget config

- [x] Env var `LLM_MONTHLY_BUDGET_USD` (default 100) em `llm_budget.py`
- [x] Counter mensal em Redis `llm_cost_month_{YYYY_MM}` (TTL 32 dias) via INCRBYFLOAT + EXPIRE

### AC3: Thresholds + alerts

- [x] 50% budget → Sentry warning (deduped 1h via SETNX)
- [x] 80% budget → Sentry error (deduped)
- [x] 100% budget → Sentry critical + flag `llm_budget_exceeded_{YYYY_MM}` + reject (PENDING_REVIEW) em arbiter
- [ ] Email admin no 80% — placeholder (não bloqueante, definido como follow-up no plano)

### AC4: Admin dashboard

- [x] `GET /v1/admin/llm-cost` endpoint protegido por `require_admin`, retorna `{month_to_date_usd, budget_usd, pct_used, projected_end_of_month_usd, month}`

---

## Tasks / Subtasks

- [x] Task 1: Wrapper instrumentation (AC1)
- [x] Task 2: Redis counter + budget config (AC2)
- [x] Task 3: Threshold logic em llm_arbiter (AC3)
- [x] Task 4: Admin endpoint (AC4)

## Dev Notes

- GPT-4.1-nano pricing ~$0.0001/1K input + $0.0004/1K output (verify)
- Counter pattern: similar a `quota.py`

## Testing

- pytest mock OpenAI + budget exceeded
- Manual em staging com low budget threshold

## File List

- **Created**:
  - `backend/llm_budget.py`
  - `backend/routes/admin_llm_cost.py`
  - `backend/tests/test_llm_budget.py` (15 tests)
  - `backend/tests/test_llm_budget_reject.py` (5 tests)
- **Modified**:
  - `backend/metrics.py` (gauge + rejection counter)
  - `backend/llm.py` (hook em `gerar_resumo`)
  - `backend/llm_arbiter/classification.py` (check `is_budget_exceeded` antes de chamar OpenAI)
  - `backend/startup/routes.py` (registra router admin_llm_cost)

## Definition of Done

- [x] Tracking + alerts + reject behavior + admin endpoint (20 tests passing)

## Risks

- **R1**: False reject em traffic legítimo — mitigation: alert agressivo antes do hard reject

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — 20 tests. AC3 email admin placeholder (follow-up). | @dev (EPIC-TD Sprint 1 batch) |
