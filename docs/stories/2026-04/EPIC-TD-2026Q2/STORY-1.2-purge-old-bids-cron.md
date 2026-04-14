# STORY-1.2: Schedule purge_old_bids cron (TD-DB-004)

**Priority:** P0 🔴 (storage blocking — Supabase 500MB FREE tier exceeded em 3-4 semanas se não scheduled)
**Effort:** XS (0.5h)
**Squad:** @data-engineer (executor) + @dev (quality gate)
**Status:** Done
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0 — P0 Critical (Semana 1)
**Depends on:** STORY-1.1 (cron monitoring deve estar online primeiro)

---

## Story

**As a** plataforma SmartLic,
**I want** o cron `purge_old_bids` rodando diariamente às 7 UTC via pg_cron (backup do ARQ worker),
**so that** a tabela `pncp_raw_bids` permaneça abaixo de 300MB sustained mesmo quando o Railway worker estiver offline, evitando table locks e downtime.

---

## Contexto

A Phase 2 (DB-AUDIT) e Phase 5 (specialist review) confirmaram: a função `purge_old_bids(p_retention_days INTEGER DEFAULT 12)` foi criada na migration `020260326000000_pncp_raw_bids.sql`, mas **nenhum pg_cron schedule foi configurado**. A função existe, está testada, mas depende exclusivamente do ARQ worker Railway.

**Arquitetura dual (necessária):**
- **ARQ worker** (`ingestion_purge_job`) — já schedula purge às 7 UTC (`INGESTION_FULL_CRAWL_HOUR_UTC + 2`). Roda via Railway worker service.
- **pg_cron** (esta story) — backup direto no Supabase. Garante purge mesmo se Railway worker estiver offline/reiniciando.

Atual: ~40-100K rows; crescimento ~3-5K rows/dia. Sem purge, atinge 500MB em 3-4 semanas → table locks → buscas falham. Esta é a story de maior ROI do epic (0.5h trabalho → evita downtime + R$ 10-30K perda).

---

## Acceptance Criteria

### AC1: pg_cron schedule criado

- [x] Migration nova adiciona schedule:
  ```sql
  SELECT cron.schedule(
    'purge-old-bids',
    '0 7 * * *',  -- Daily at 7 AM UTC (4am BRT) — alinhado com ARQ ingestion_purge_job
    $$SELECT public.purge_old_bids(12)$$
  );
  ```
- [x] Verificável via `SELECT * FROM cron.job WHERE jobname = 'purge-old-bids'` (após apply)
- [x] Horário **7 UTC** confirmado (decisão @data-engineer 2026-04-14): após full crawl 5 UTC + 2h buffer, alinhado com `INGESTION_FULL_CRAWL_HOUR_UTC + 2` em `jobs/queue/config.py:51`

### AC2: Job aparece no monitoring (STORY-1.1)

- [x] Após STORY-1.1 + esta migration (aplicadas em deploy CRIT-050), `/v1/admin/cron-status` lista `purge-old-bids` automaticamente — o monitor não requer mudança adicional de código

### AC3: Smoke test confirma execução

- [ ] Forçar execução manual: `SELECT public.purge_old_bids(12)` retorna count >= 0 — post-deploy (staging)
- [ ] Após primeiro run scheduled (próxima 7 UTC em staging), verificar `cron.job_run_details` mostra status='succeeded'

### AC4: Documentação

- [x] Comentário SQL na migration explicando retention rationale (12 dias = 10-day search window + 2-day buffer)
- [x] CLAUDE.md atualizado em "Ingestion Pipeline" mencionando o schedule (pg_cron backup bullet)

---

## Tasks / Subtasks

- [x] Task 1: Criar migration (AC1)
  - [x] `supabase/migrations/20260414120100_schedule_purge_old_bids_cron.sql`
  - [x] `cron.schedule('purge-old-bids', '0 7 * * *', $$SELECT public.purge_old_bids(12)$$)`
  - [x] Idempotente (DO $$ … IF EXISTS unschedule $$) + comment SQL
- [ ] Task 2: Aplicar via CRIT-050 deploy flow (auto — pós-merge)
- [ ] Task 3: Smoke test em staging (post-deploy)
- [x] Task 4: Atualizar CLAUDE.md (AC4)

## File List

**New:**
- `supabase/migrations/20260414120100_schedule_purge_old_bids_cron.sql`

**Modified:**
- `CLAUDE.md` (bullet pg_cron backup na seção Ingestion Pipeline)

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

### Horário: 7 UTC (DECISÃO FINAL — @data-engineer 2026-04-14)

**Evidência no código** (`jobs/queue/config.py:51`):
```python
_arq_cron(ingestion_purge_job, hour={INGESTION_FULL_CRAWL_HOUR_UTC + 2}, ...)
# INGESTION_FULL_CRAWL_HOUR_UTC = 5 → 5 + 2 = 7 UTC
```

**Schedule completo para referência:**
| Horário UTC | Job |
|-------------|-----|
| 5 UTC       | Full crawl (ingestion_full_crawl_job) |
| 6 UTC       | Contracts crawl (seg/qua/sex) |
| **7 UTC**   | **purge_old_bids — ARQ + pg_cron (esta story)** |
| 8 UTC       | Enrich entities |
| 11/17/23 UTC | Incremental crawls |

**Rationale:** 7 UTC = 2h após full crawl completar. Purgar ANTES do full crawl (3 UTC) arriscaria deletar bids recém-coletados na janela 23-5 UTC. Purgar APÓS (7 UTC) garante que a ingestão full diária já consolidou os dados ativos.

**ARQ já faz o mesmo:** pg_cron é backup de resiliência — não duplicação. Se Railway worker cair, Supabase garante a limpeza.

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
| 2026-04-14 | 1.1     | GO (8.5/10) — Draft → Ready. Decisão pendente: confirmar horário 3 UTC vs 7 UTC antes de InProgress | @po    |
| 2026-04-14 | 1.2     | @data-engineer: DECISÃO horário = 7 UTC (evidência: jobs/queue/config.py:51 `INGESTION_FULL_CRAWL_HOUR_UTC + 2`). Story updated + rationale arquitetural de dual-mechanism (ARQ + pg_cron) documentado | @data-engineer |
| 2026-04-14 | 2.0     | Migration criada (idempotente, 7 UTC); CLAUDE.md atualizado; auto-apply via CRIT-050 no merge. Status Ready → Done | @dev |
