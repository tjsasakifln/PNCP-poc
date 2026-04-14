# STORY-1.4: Schedule search_results_store cleanup cron (TD-DB-014)

**Priority:** P0 (storage growth — expired rows acumulam)
**Effort:** XS (0.5h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0
**Depends on:** STORY-1.1

---

## Story

**As a** plataforma SmartLic,
**I want** o cron diário deletando rows com `expires_at < now()` em `search_results_store`,
**so that** a tabela L3 fallback não cresça indefinidamente.

---

## Contexto

A Phase 2 (DB-AUDIT TD-DB-014) e Phase 5 confirmaram: `search_results_store.expires_at` define soft TTL (24h) MAS sem cron deleta rows expired. Tabela cresce linearmente com searches. Eventual problema de storage (mesmo padrão do TD-DB-013).

---

## Acceptance Criteria

### AC1: pg_cron schedule criado

- [ ] Migration adiciona:
  ```sql
  SELECT cron.schedule(
    'cleanup-search-store',
    '15 4 * * *',  -- Daily at 4:15 AM UTC (15min após search_cache cleanup)
    $$DELETE FROM public.search_results_store WHERE expires_at < now()$$
  );
  ```

### AC2: Aparece no monitoring (STORY-1.1)

### AC3: Smoke test

---

## Tasks / Subtasks

- [ ] Task 1: Criar migration `2026XXXXXXXXXX_schedule_search_store_cleanup.sql`
- [ ] Task 2: Aplicar via CRIT-050 flow
- [ ] Task 3: Smoke test
- [ ] Task 4: Atualizar SCHEMA.md mencionando cron

## Dev Notes

- Tabela `search_results_store`: SCHEMA.md item 18
- Coluna `expires_at` definida com default `now() + 24h`
- DELETE idempotent — safe to repeat

## Testing

- **Smoke**: `cron.job` confirma schedule
- **Validation**: row com `expires_at < now()` deletada após run

## Definition of Done

- [ ] Migration aplicada + cron monitorado + docs atualizados

## Risks

- **R1**: User pode acessar resultado expired entre delete e refresh — mitigation: app layer já lida com 404

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
