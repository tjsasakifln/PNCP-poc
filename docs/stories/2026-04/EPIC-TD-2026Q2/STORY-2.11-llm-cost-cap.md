# STORY-2.11: LLM Monthly Cost Cap + Alerts (TD-SYS-018)

**Priority:** P1 (financial protection — runaway spending risk)
**Effort:** S (4-8h)
**Squad:** @dev + @architect quality gate
**Status:** Draft
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

- [ ] Counter Prometheus `llm_tokens_used_total{model, request_type}` + `llm_cost_usd_total`
- [ ] Wrapper em `backend/llm.py` instrumenta `client.chat.completions.create()`

### AC2: Budget config

- [ ] Env var `LLM_MONTHLY_BUDGET_USD` (default 100)
- [ ] Counter mensal em Redis `llm_cost_month_2026_04` (TTL 32 dias)

### AC3: Thresholds + alerts

- [ ] 50% budget → Sentry warning
- [ ] 80% budget → Sentry error + email admin
- [ ] 100% budget → reject novas LLM calls (return PENDING_REVIEW), Sentry critical

### AC4: Admin dashboard

- [ ] `/admin/llm-cost` endpoint retorna mês atual + projeção fim de mês

---

## Tasks / Subtasks

- [ ] Task 1: Wrapper instrumentation (AC1)
- [ ] Task 2: Redis counter + budget config (AC2)
- [ ] Task 3: Threshold logic em llm_arbiter (AC3)
- [ ] Task 4: Admin endpoint (AC4)

## Dev Notes

- GPT-4.1-nano pricing ~$0.0001/1K input + $0.0004/1K output (verify)
- Counter pattern: similar a `quota.py`

## Testing

- pytest mock OpenAI + budget exceeded
- Manual em staging com low budget threshold

## Definition of Done

- [ ] Tracking + alerts + reject behavior + admin endpoint

## Risks

- **R1**: False reject em traffic legítimo — mitigation: alert agressivo antes do hard reject

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
