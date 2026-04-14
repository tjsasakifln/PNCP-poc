# STORY-1.1: pg_cron Monitoring + Sentry Alerts (TD-DB-040)

**Priority:** P0 (precede crons; sem monitoring, falha silenciosa)
**Effort:** S (4-8h)
**Squad:** @data-engineer (executor) + @dev (quality gate)
**Status:** Done
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

- [x] Migration cria view `public.cron_job_health` agregando `cron.job` + `cron.job_run_details` (last 7 days)
- [x] Colunas: `jobname`, `last_run_at`, `last_status` (succeeded/failed), `runs_24h`, `failures_24h`, `latency_avg_ms`
- [x] RPC `get_cron_health()` SECURITY DEFINER granted to `service_role` (admin-only via backend)

### AC2: Endpoint backend `/admin/cron-status`

- [x] Novo route handler `GET /v1/admin/cron-status` em `backend/routes/admin_cron.py`
- [x] Requer `is_admin=true` ou `is_master=true` (via `admin.require_admin`)
- [x] Retorna JSON com array de health rows; status code 200 sempre que query funciona (graceful degrade para `status=error` quando RPC falha)

### AC3: Sentry alert on stale/failed jobs

- [x] Monitor cron job (ARQ, hourly minute=0) chama `get_cron_health()`
- [x] Para cada job, se `last_run_at < now() - interval '25 hours'` ou `last_status='failed'` → `sentry_sdk.capture_message(level="error")` com tags `cron_job={jobname}` + `cron_job.reason`
- [x] Dedup: fingerprint `["cron_job", jobname, reason]` no Sentry

### AC4: Documentação

- [x] CLAUDE.md atualizado com seção "pg_cron Monitoring (STORY-1.1 EPIC-TD-2026Q2)"
- [x] Quando usar e como interpretar `/v1/admin/cron-status`
- [x] Como adicionar novo cron job + auto-monitoring (1 step: criar migration)

### AC5: Testes

- [x] Unit tests backend: `test_admin_cron.py` (4 tests) + `test_cron_monitoring.py` (12 tests) = 16 passing, 0 regressões
- [ ] Integration test em staging — aplicável após merge + migration apply via CRIT-050 deploy flow

---

## Tasks / Subtasks

- [x] Task 1: Criar migration `20260414120000_cron_job_health.sql` (AC1)
  - [x] View com JOINs `cron.job` + `cron.job_run_details` (7-day window)
  - [x] RPC `get_cron_health()` SECURITY DEFINER
  - [x] Grant `service_role` + revoke anon/authenticated
- [x] Task 2: Implementar endpoint backend (AC2)
  - [x] Novo módulo `backend/routes/admin_cron.py`
  - [x] `Depends(require_admin)`
  - [x] Chama RPC via `sb_execute_direct` + serializa datetime/numeric
- [x] Task 3: Implementar monitor cron job (AC3)
  - [x] Handler `cron_monitoring_job` em `backend/jobs/cron/cron_monitor.py`
  - [x] Schedule hourly (`minute={0}`) em `backend/jobs/queue/config.py`
  - [x] Logic: `evaluate_jobs()` detecta stale (>25h) / failed + fingerprint dedup
- [x] Task 4: Documentação (AC4)
- [x] Task 5: Testes (AC5) — 16 tests pass

## File List

**New:**
- `supabase/migrations/20260414120000_cron_job_health.sql`
- `backend/routes/admin_cron.py`
- `backend/jobs/cron/cron_monitor.py`
- `backend/tests/test_admin_cron.py`
- `backend/tests/test_cron_monitoring.py`

**Modified:**
- `backend/startup/routes.py` (+2 lines — include_router admin_cron)
- `backend/jobs/queue/config.py` (+14 lines — register cron_monitoring_job)
- `CLAUDE.md` (+section "pg_cron Monitoring")

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
| 2026-04-14 | 2.0     | Implementation complete — view + RPC + /v1/admin/cron-status + ARQ hourly monitor + Sentry alerts + 16 unit tests passing; Status Ready → Done | @dev |
