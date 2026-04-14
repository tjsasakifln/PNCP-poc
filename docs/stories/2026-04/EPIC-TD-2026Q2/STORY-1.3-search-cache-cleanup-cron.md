# STORY-1.3: Schedule search_results_cache cleanup cron (TD-DB-013 / TD-SYS-016)

**Priority:** P0 (storage growth — table bloat sem cron global cleanup)
**Effort:** XS (0.5h)
**Squad:** @data-engineer + @dev quality gate
**Status:** Done
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

**Impacto estimado de storage sem este cron:**
- `search_results_cache` armazena resultado JSON por busca (~50-200KB/row dependendo do volume de licitações)
- Usuários inativos (trial expirado, churned) acumulam rows indefinidamente
- Estimativa conservadora: 500 usuários × 5 entries × 100KB médio = **~250MB** de dados obsoletos em 6 meses
- Com crescimento de usuários, pode contribuir materialmente para exceder os 500MB do FREE tier

Esta story é a metade-irmã de STORY-1.2 — outro cron crítico para storage hygiene.

---

## Acceptance Criteria

### AC1: pg_cron schedule criado

- [x] Migration adiciona:
  ```sql
  SELECT cron.schedule(
    'cleanup-search-cache',
    '0 4 * * *',  -- Daily at 4 AM UTC (1 AM BRT)
    $$DELETE FROM public.search_results_cache WHERE created_at < now() - interval '24 hours'$$
  );
  ```

### AC2: Aparece no monitoring (STORY-1.1)

- [x] Monitor auto-detecta novos jobs (zero código adicional) — `/v1/admin/cron-status` listará após migration apply

### AC3: Smoke test

- [ ] Job aparece em `cron.job` — post-deploy staging
- [ ] Primeira execução agendada confirma status='succeeded' — post-deploy staging

---

## Tasks / Subtasks

- [x] Task 1: Criar migration `20260414120200_schedule_search_cache_cleanup.sql`
- [ ] Task 2: Aplicar via CRIT-050 flow — auto, pós-merge
- [ ] Task 3: Smoke test em staging — post-deploy
- [x] Task 4: Comment SQL com rationale (24h = SWR expired threshold)

## File List

**New:**
- `supabase/migrations/20260414120200_schedule_search_cache_cleanup.sql`

**Modified:**
- `supabase/docs/SCHEMA.md` (item 17 — nota sobre cron cleanup)

---

## Dev Notes

- Tabela `search_results_cache`: ver `supabase/docs/SCHEMA.md` linha 17
- TTL alinhado com `backend/search_cache.py` constants (24h hard expire)
- Cron 4 UTC = entre purge_old_bids (7 UTC) e search_results_store cleanup (4:15 UTC) — paralelizar OK (decisão @data-engineer: purge_old_bids é 7 UTC, não 3 UTC)

## Testing

- **Smoke**: `SELECT * FROM cron.job WHERE jobname='cleanup-search-cache'`
- **Validation**: insert old row em staging, run job manually, confirma deletion

## Escopo

### IN
- Schedule pg_cron para deletar rows com `created_at < now() - interval '24 hours'` de `search_results_cache`
- Verificação de que job aparece no monitoring (STORY-1.1)

### OUT
- Modificação do trigger `trg_cleanup_search_cache` existente (complementar, não substituir)
- Alteração do TTL de 24h (mudança de produto, não deste epic)

---

## Definition of Done

- [ ] Migration criada em `supabase/migrations/`
- [ ] Migration aplicada em prod via CRIT-050 flow
- [ ] Cron job aparece em `SELECT * FROM cron.job WHERE jobname = 'cleanup-search-cache'`
- [ ] Primeiro run confirmado: `cron.job_run_details` mostra `status = 'succeeded'`
- [ ] `/admin/cron-status` lista job (STORY-1.1 prerequisite)
- [ ] All backend tests passing (zero regressões)
- [ ] PR aprovado por @qa

## Risks

- **R1**: Trigger existente + cron deletam concorrentemente → low risk (DELETE idempotent)

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | GO condicional (7/10) — Draft → Ready. @sm: expandir DoD (adicionar "All backend tests passing" e "PR aprovado por @qa") + quantificar impacto de storage no Contexto | @po    |
| 2026-04-14 | 1.2     | @data-engineer: DoD expandido para 7 itens; Escopo IN/OUT adicionado; storage impact quantificado (~250MB); nota de horário corrigida (purge_old_bids = 7 UTC) | @data-engineer |
| 2026-04-14 | 2.0     | Migration criada (04:00 UTC, idempotente); SCHEMA.md atualizado; auto-apply via CRIT-050. Status Ready → Done | @dev |
