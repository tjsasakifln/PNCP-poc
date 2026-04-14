# STORY-4.1: LLM Async + Batch API Integration (TD-SYS-014)

**Priority:** P1 (latência 30s+ em alta concorrência)
**Effort:** M (16-24h)
**Squad:** @dev + @architect + @qa
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3
**Depends on:** STORY-3.1 (search.py decompose)

---

## Story

**As a** SmartLic,
**I want** chamadas LLM via async client + Batch API quando aplicável,
**so that** latência média de search caia 50%+ em alta concorrência.

---

## Acceptance Criteria

### AC1: Async OpenAI client

- [ ] `backend/llm.py` migra para `AsyncOpenAI` client
- [ ] `ThreadPoolExecutor(max_workers=10)` removido — async concurrency via `asyncio.gather`
- [ ] Pool size configurable via `LLM_MAX_CONCURRENT` env (default 50)

### AC2: Batch API para classificação

- [ ] `backend/llm_arbiter.py` usa OpenAI Batch API quando >20 items para classificar
- [ ] Async polling de batch status (cron ARQ)
- [ ] Cost reduction 50% confirmed via cost tracking (STORY-2.11)

### AC3: Telemetria

- [ ] Métricas Prometheus: `llm_call_duration_seconds`, `llm_batch_jobs_active`, `llm_concurrent_calls`
- [ ] Grafana dashboard atualizado

### AC4: Latency improvement

- [ ] Baseline (STORY-3.3) vs novo: p95 latency reduce >40% para `/buscar`

---

## Tasks / Subtasks

- [ ] Task 1: Migrar `llm.py` para AsyncOpenAI
- [ ] Task 2: Refactor llm_arbiter para async/await pattern
- [ ] Task 3: Batch API integration (separated cron job processador)
- [ ] Task 4: Métricas + dashboard
- [ ] Task 5: Load test compare baseline vs new
- [ ] Task 6: Atualizar tests

## Dev Notes

- AsyncOpenAI: https://github.com/openai/openai-python (async client docs)
- Batch API: https://platform.openai.com/docs/guides/batch
- Pattern: gather + semaphore para rate limit
- Costs cap (STORY-2.11) precisa adaptar para batch

## Testing

- pytest async tests
- Load test compare (STORY-3.3 baseline)
- Smoke prod canary

## Definition of Done

- [ ] Async migration + batch API + metrics + load test improvement confirmed

## Risks

- **R1**: Batch API latency >5min em low volume — mitigation: only batch quando >20 items
- **R2**: Race conditions em async refactor — mitigation: pytest-asyncio extensive coverage

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
