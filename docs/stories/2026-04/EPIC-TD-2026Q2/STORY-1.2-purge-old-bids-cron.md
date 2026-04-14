# STORY-1.2: Schedule purge_old_bids cron (TD-DB-004)

**Priority:** P0 🔴 (storage blocking — Supabase 500MB FREE tier exceeded em 3-4 semanas se não scheduled)
**Effort:** XS (0.5h)
**Squad:** @data-engineer (executor) + @dev (quality gate)
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0 — P0 Critical (Semana 1)
**Depends on:** STORY-1.1 (cron monitoring deve estar online primeiro)

---

## Story

**As a** plataforma SmartLic,
**I want** o cron `purge_old_bids` rodando diariamente às 3 UTC,
**so that** a tabela `pncp_raw_bids` permaneça abaixo de 300MB sustained, evitando exceeding o limite Supabase FREE tier (500MB) que causa table locks e downtime.

---

## Contexto

A Phase 2 (DB-AUDIT) e Phase 5 (specialist review) confirmaram: a função `purge_old_bids(p_retention_days INTEGER DEFAULT 12)` foi criada na migration `020260326000000_pncp_raw_bids.sql`, mas **nenhum cron schedule foi configurado**. A função existe, está testada, mas nunca roda automaticamente em produção.

Atual: ~40-100K rows; crescimento ~3-5K rows/dia. Sem purge, atinge 500MB em 3-4 semanas → table locks → buscas falham. Esta é a story de maior ROI do epic (0.5h trabalho → evita downtime + R$ 10-30K perda).

---

## Acceptance Criteria

### AC1: pg_cron schedule criado

- [ ] Migration nova adiciona schedule:
  ```sql
  SELECT cron.schedule(
    'purge-old-bids',
    '0 3 * * *',  -- Daily at 3 AM UTC (00:00 BRT)
    $$SELECT public.purge_old_bids(12)$$
  );
  ```
- [ ] Verificável via `SELECT * FROM cron.job WHERE jobname = 'purge-old-bids'`

### AC2: Job aparece no monitoring (STORY-1.1)

- [ ] Após STORY-1.1 + esta migration, `/admin/cron-status` lista `purge-old-bids` com status

### AC3: Smoke test confirma execução

- [ ] Forçar execução manual: `SELECT public.purge_old_bids(12)` retorna count >= 0
- [ ] Após primeiro run scheduled (esperar 24h em staging ou disparar via `cron.schedule_in_database` test), verificar `cron.job_run_details` mostra status='succeeded'

### AC4: Documentação

- [ ] Comentário SQL na migration explicando retention rationale (12 dias = 10-day search window + 2-day buffer)
- [ ] CLAUDE.md atualizado em "Ingestion Pipeline" mencionando o schedule

---

## Tasks / Subtasks

- [ ] Task 1: Criar migration (AC1)
  - [ ] `supabase/migrations/2026XXXXXXXXXX_schedule_purge_old_bids_cron.sql`
  - [ ] Adicionar `cron.schedule` call
  - [ ] Adicionar comment SQL com rationale
- [ ] Task 2: Aplicar via CRIT-050 deploy flow (AC1)
  - [ ] PR triggera `migration-gate.yml` warning
  - [ ] Push merge triggera auto-apply via `deploy.yml`
- [ ] Task 3: Smoke test (AC3)
  - [ ] Verificar `cron.job` em produção
  - [ ] Aguardar primeiro run (próxima 3 UTC) e validar `cron.job_run_details`
- [ ] Task 4: Atualizar CLAUDE.md (AC4)

---

## Dev Notes

### Relevant Source Files

- `supabase/migrations/020260326000000_pncp_raw_bids.sql` — define função `purge_old_bids()`
- `backend/ingestion/config.py` — define retention_days (12)
- `CLAUDE.md` seção "Ingestion Pipeline (Layer 1)" — atualizar

### Function Signature (already exists)

```sql
CREATE OR REPLACE FUNCTION public.purge_old_bids(p_retention_days INTEGER DEFAULT 12)
RETURNS INTEGER AS $$ ... $$;
```

### Why 3 UTC?

- 00:00 BRT (medianoche local) — minimal user impact
- After full daily ingestion (5 UTC = 2 AM BRT)... wait, esse cron roda ANTES do ingestion. Verificar se ordem é OK ou ajustar para após.
- Recomendação: 7 UTC (4 AM BRT, depois do incremental 23 UTC e antes do full 5 UTC do dia seguinte). MAS workflow define 7 UTC como "purge daily" — confirmar.

### Constraints

- pg_cron extension deve estar habilitada (verificar em pre-condition)
- `purge_old_bids` é DELETE — não rodar em hora de pico

---

## Testing

- **Smoke**: query `cron.job` confirma schedule criado
- **Integration (staging)**: forçar run com `SELECT cron.schedule_in_database(...)` ou aguardar 24h
- **Monitoring**: confirmar Sentry NÃO dispara alert nos próximos 7 dias (validates STORY-1.1 monitoring funciona)

---

## Definition of Done

- [ ] Migration aplicada em prod
- [ ] Cron job aparece em `cron.job`
- [ ] Primeiro run successful confirmado
- [ ] STORY-1.1 monitoring exibe job
- [ ] CLAUDE.md atualizado
- [ ] PR aprovado

---

## Risks

- **R1**: Cron rodando antes do ingestion poderia deletar bids recém-coletados → mitigation: agendar APÓS incremental crawl (7 UTC)
- **R2**: pg_cron job conflict com manual purges → mitigation: documentar que automação ON

---

## Change Log

| Date       | Version | Description                                 | Author |
|------------|---------|---------------------------------------------|--------|
| 2026-04-14 | 1.0     | Initial draft from EPIC-TD-2026Q2 Phase 10 | @sm    |
