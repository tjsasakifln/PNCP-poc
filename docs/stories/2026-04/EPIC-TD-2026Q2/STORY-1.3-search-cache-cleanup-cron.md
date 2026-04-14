# STORY-1.3: Schedule search_results_cache cleanup cron (TD-DB-013 / TD-SYS-016)

**Priority:** P0 (storage growth — table bloat sem cron global cleanup)
**Effort:** XS (0.5h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0
**Depends on:** STORY-1.1

---

## Story

**As a** plataforma SmartLic,
**I want** o cron diário deletando rows expired (>24h) de `search_results_cache`,
**so that** a tabela não cresça unbounded acumulando entries de usuários inativos.

---

## Contexto

A Phase 2 (DB-AUDIT TD-DB-013) e Phase 5 (specialist review) identificaram: trigger `trg_cleanup_search_cache` mantém max 5 entries/user MAS só dispara em INSERT novo. Se user não retorna, entries antigas ficam para sempre. Sobrepõe-se com TD-SYS-016 (Phase 1 architect notes).

Esta story é a metade-irmã de STORY-1.2 — outro cron crítico para storage hygiene.

---

## Acceptance Criteria

### AC1: pg_cron schedule criado

- [ ] Migration adiciona:
  ```sql
  SELECT cron.schedule(
    'cleanup-search-cache',
    '0 4 * * *',  -- Daily at 4 AM UTC (1 AM BRT)
    $$DELETE FROM public.search_results_cache WHERE created_at < now() - interval '24 hours'$$
  );
  ```

### AC2: Aparece no monitoring (STORY-1.1)

- [ ] `/admin/cron-status` lista job

### AC3: Smoke test

- [ ] Job aparece em `cron.job`
- [ ] Primeira execução agendada confirma status='succeeded'

---

## Tasks / Subtasks

- [ ] Task 1: Criar migration `2026XXXXXXXXXX_schedule_search_cache_cleanup.sql`
- [ ] Task 2: Aplicar via CRIT-050 flow
- [ ] Task 3: Smoke test em staging
- [ ] Task 4: Comment SQL com rationale (24h = SWR expired threshold)

---

## Dev Notes

- Tabela `search_results_cache`: ver `supabase/docs/SCHEMA.md` linha 17
- TTL alinhado com `backend/search_cache.py` constants (24h hard expire)
- Cron 4 UTC = entre purge_old_bids (3 UTC) e search_results_store cleanup (4 UTC) — paralelizar OK

## Testing

- **Smoke**: `SELECT * FROM cron.job WHERE jobname='cleanup-search-cache'`
- **Validation**: insert old row em staging, run job manually, confirma deletion

## Definition of Done

- [ ] Migration aplicada
- [ ] Cron monitorado
- [ ] CLAUDE.md atualizado

## Risks

- **R1**: Trigger existente + cron deletam concorrentemente → low risk (DELETE idempotent)

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
