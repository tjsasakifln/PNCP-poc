# STORY-1.1: pg_cron Monitoring + Sentry Alerts (TD-DB-040)

**Priority:** P0 (precede crons; sem monitoring, falha silenciosa)
**Effort:** S (4-8h)
**Squad:** @data-engineer (executor) + @dev (quality gate)
**Status:** Ready
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 0 — P0 Critical (Semana 1)

---

## Story

**As a** SRE/admin do SmartLic,
**I want** alertas Sentry quando qualquer pg_cron job falhar ou for skipped,
**so that** débitos críticos como purge_old_bids não falhem silenciosamente causando storage exceeded ou retention compliance breach.

---

## Contexto

A Phase 5 do brownfield-discovery (TD-DB-040) identificou que o SmartLic hoje tem `audit_events` cron schedulado (`0 4 1 * *`) mas **nenhum monitoramento se o job roda ou falha**. Esta story é **pré-requisito** para STORY-1.2/1.3/1.4 (schedule de novos cron jobs) — sem monitoring, agendar mais crons agrava o risco.

`cron.job_run_details` armazena histórico mas ninguém olha. Precisamos:
1. Função/view que exporta status de últimos runs
2. Endpoint backend `/admin/cron-status` (admin-only)
3. Cron job próprio que escreve métrica Prometheus + dispara Sentry alert se >24h sem run successful

---

## Acceptance Criteria

### AC1: View `cron_job_health` exposta via RPC

- [ ] Migration cria view `public.cron_job_health` agregando `cron.job` + `cron.job_run_details` (last 7 days)
- [ ] Colunas: `jobname`, `last_run_at`, `last_status` (succeeded/failed), `runs_24h`, `failures_24h`, `latency_avg_ms`
- [ ] RPC `get_cron_health()` SECURITY DEFINER granted to `service_role` (admin-only via backend)

### AC2: Endpoint backend `/admin/cron-status`

- [ ] Novo route handler `GET /admin/cron-status` em `backend/routes/admin_*.py`
- [ ] Requer `is_admin=true` ou `is_master=true` (via `authorization.py`)
- [ ] Retorna JSON com array de health rows; status code 200 sempre que query funciona

### AC3: Sentry alert on stale/failed jobs

- [ ] Monitor cron job (Python ARQ scheduled, hourly) chama `get_cron_health()`
- [ ] Para cada job, se `last_run_at < now() - interval '25 hours'` ou `last_status='failed'` → `sentry_sdk.capture_message(level="error")` com tags `cron_job={jobname}`
- [ ] Dedup: não spamar — usar fingerprint `[cron_job, jobname]` no Sentry

### AC4: Documentação

- [ ] CLAUDE.md atualizado com seção "pg_cron Monitoring"
- [ ] Quando usar e como interpretar `/admin/cron-status`
- [ ] Como adicionar novo cron job + auto-monitoring

### AC5: Testes

- [ ] Unit test backend: mock supabase client, verifica formato JSON resposta
- [ ] Integration test: smoke test em ambiente de staging confirma view existe e RPC retorna dados

---

## Tasks / Subtasks

- [ ] Task 1: Criar migration `cron_job_health_view.sql` (AC1)
  - [ ] Definir view com JOINs `cron.job` + `cron.job_run_details`
  - [ ] Criar RPC `get_cron_health()` SECURITY DEFINER
  - [ ] Grant ao `service_role`
- [ ] Task 2: Implementar endpoint backend (AC2)
  - [ ] Novo módulo `backend/routes/admin_cron.py` ou estender `admin_*.py`
  - [ ] Decorator `@require_admin`
  - [ ] Chama RPC + retorna JSON
- [ ] Task 3: Implementar monitor cron job (AC3)
  - [ ] Adicionar handler em `backend/cron_jobs.py`
  - [ ] Schedule hourly via ARQ WorkerSettings
  - [ ] Logic: query health, detectar stale/failed, capture_message
- [ ] Task 4: Documentação (AC4)
- [ ] Task 5: Testes (AC5)

---

## Dev Notes

### Relevant Source Files

- `supabase/migrations/` — adicionar novo arquivo `2026XXXXXXXXXX_cron_job_health.sql`
- `backend/routes/` — adicionar admin_cron.py ou estender existente
- `backend/cron_jobs.py` — adicionar `monitor_cron_jobs()` handler
- `backend/job_queue.py` — registrar novo cron schedule

### Key References

- pg_cron docs: `cron.job` table tem `jobid, schedule, command, jobname`; `cron.job_run_details` tem `runid, jobid, status, return_message, start_time, end_time`
- Sentry SDK: `sentry_sdk.capture_message(message, level="error")` + `set_tag("cron_job", jobname)`
- Auth pattern: ver `backend/authorization.py` `require_admin` dependency

### Constraints

- pg_cron schema é restrito; use `SECURITY DEFINER` para function que lê
- `cron.job_run_details` cresce sem limite — view deve filtrar last 7 days

---

## Testing

- **Unit**: pytest em `backend/tests/test_admin_cron.py` — mock supabase, verifica response shape
- **Integration**: `backend/tests/integration/test_cron_health.py` — testa contra Supabase real (CI-only)
- **Smoke**: após deploy, `curl /admin/cron-status` com token admin

---

## Definition of Done

- [ ] Migration aplicada em prod via CRIT-050 flow
- [ ] Endpoint funciona com role admin
- [ ] Cron monitor running e enviando heartbeat
- [ ] Sentry alert testado (forçar failed job em staging)
- [ ] Documentação atualizada
- [ ] PR aprovado por @qa

---

## Risks

- **R1**: pg_cron extension não habilitada em alguma env — mitigation: check em pre-conditions
- **R2**: Sentry rate limit se muitos jobs failing — mitigation: dedup via fingerprint

---

## Change Log

| Date       | Version | Description                                  | Author |
|------------|---------|----------------------------------------------|--------|
| 2026-04-14 | 1.0     | Initial draft from EPIC-TD-2026Q2 Phase 10  | @sm    |
| 2026-04-14 | 1.1     | GO (8/10) — Draft → Ready. Obs: adicionar IN/OUT antes de InProgress | @po    |
