# STORY-TRIAL-001: Audit operacional de `trial_email_sequence`

## Status

Approved

> Escopo restrito a ações on-system (queries DB internas, cron health, HMAC handler local, Sentry, Prometheus). Conteúdo de copy de emails outbound fica fora do escopo desta story sob diretriz "on-page exclusive" 2026-04-26.

## Story

**As a** time de growth/lifecycle confiando em STORY-321 (6 emails em 14 dias) para nutrir trials,
**I want** validação operacional de que a sequência está enviando, registrando, deduplicando e respeitando opt-out em prod,
**so that** quando atingirmos 30+ trials/mês (gate dos backlogs paywall/pricing), o lifecycle email não seja descoberto como gargalo silencioso.

> **Importante:** esta story **NÃO implementa** o sequencer — `backend/services/trial_email_sequence.py:50` JÁ existe (Wave 0 confirmou). Esta é uma auditoria operacional + correção de gaps observabilidade.

## Acceptance Criteria

1. Confirmar live: ARQ cron `_trial_sequence_loop` (`backend/jobs/cron/notifications.py:110-141`) rodando a cada 2h em prod (verificar via `cron_job_health` view + `get_cron_health()` RPC + `/v1/admin/cron-status` endpoint).
2. Query Supabase: `trial_email_log` populado para trials criados últimos 14d. Para cada trial completo (created_at > 16d atrás):
   - **AC esperado:** ≥4 dos 6 emails core (day 0, 3, 7, 13) registrados (day 10 e 16 podem variar)
   - Documentar % de cobertura real em `docs/qa/trial-email-coverage.md`
3. Resend webhook delivery tracking: HMAC verification implementado (memória 2026-04-24 deixou gap — `RESEND_WEBHOOK_SECRET` ATIVO Wave 0); `trial_email_log.delivery_status` populado (sent/delivered/bounced/complained) por webhook handler.
4. Bounce/complaint rate <2% (industry baseline B2B); se acima, investigar causa raiz (lista contaminada, copy spam-like, domain reputation).
5. Opt-out funcional: link unsubscribe nos emails leva a endpoint `/v1/email/unsubscribe?token=HMAC` que valida token, marca preferência, retorna confirmação clara. Smoke test manual (gerar token, hit endpoint, verificar `email_preferences` atualizada).
6. Sentry alertas: falhas no envio (Resend 5xx, OpenAI quota, etc.) emitem `capture_message(level="error")` com fingerprint `["trial_email", template_type]`. Verificar últimos 14d de Sentry para incidentes não tratados (memória `reference_sentry_credentials.md` — org=confenge, proj=smartlic-backend).
7. Métricas Prometheus: `smartlic_trial_email_sent_total{template,status}` exposto e populado (criar se ausente).
8. Runbook em `docs/runbooks/trial-email-sequence.md`: como verificar saúde, como reenviar manualmente, como investigar bounce, como atualizar copy.

## Tasks / Subtasks

- [ ] Task 1 — Verificar cron health (AC: 1)
  - [ ] @devops/@qa: hit `/v1/admin/cron-status` em prod
  - [ ] Confirmar `_trial_sequence_loop` last_run_at recente
- [ ] Task 2 — Audit cobertura `trial_email_log` (AC: 2)
  - [ ] @data-engineer: query Supabase com profiles trial recentes
  - [ ] Calcular % por dia (0/3/7/10/13/16)
  - [ ] Investigar gaps (timezone window? dedup falso positivo?)
- [ ] Task 3 — HMAC webhook verification (AC: 3)
  - [ ] @dev: validar handler Resend webhook em `backend/webhooks/resend.py` (TBD path) verifica HMAC com `RESEND_WEBHOOK_SECRET`
  - [ ] Atualizar `trial_email_log.delivery_status` com payload Resend
- [ ] Task 4 — Bounce/complaint análise (AC: 4)
  - [ ] Query Resend dashboard ou tabela local
  - [ ] Se >2%, ticket detalhado para investigação
- [ ] Task 5 — Opt-out smoke (AC: 5)
  - [ ] Manual: gerar token unsubscribe via `_UNSUBSCRIBE_SECRET` (linha 25 do service)
  - [ ] Hit endpoint, verificar DB
- [ ] Task 6 — Sentry review + alerts (AC: 6)
  - [ ] @qa: search Sentry últimos 14d "trial_email"
  - [ ] Triage incidentes não resolvidos
  - [ ] Adicionar fingerprint+capture se ausente
- [ ] Task 7 — Métricas Prometheus (AC: 7)
  - [ ] @dev: counter exposto se ausente
- [ ] Task 8 — Runbook (AC: 8)
  - [ ] @qa + @dev: documentar operacional

## Dev Notes

**Plano:** Wave 4, story 14 — **única story de trial pre-PMF** (advisor: outras 5 trial→paid stories diferidas para backlog até 30 trials/mês).

**Wave 0 evidence:**
- `ls backend/services/trial_email_sequence.py` confirmou existe
- Read primeiras 80 linhas: TRIAL_EMAIL_SEQUENCE com 6 emails (day 0/3/7/10/13/16) + opt-in extensions
- HMAC unsubscribe secret derivado de WEBHOOK_SECRET (linha 25)
- Timezone scheduling configurável via `TIMEZONE_SCHEDULING_ENABLED`
- Cron loop em `backend/jobs/cron/notifications.py:110-141`
- `RESEND_WEBHOOK_SECRET=whsec_5e...` ATIVO em backend Railway

**Memória relevante:**
- `reference_trial_email_log_delivery_status_null.md` (2026-04-24): migration `20260424180000` aplicada + webhook `758ea803` criado — gap aberto: HMAC verify ainda não implementado
- `project_cache_warming_deprecation.md`: padrão "audit operacional" funciona quando código existe mas observabilidade falta

**Files mapeados:**
- `backend/services/trial_email_sequence.py` (read-only audit)
- `backend/jobs/cron/notifications.py` (validar cron)
- `backend/webhooks/resend.py` ou similar (verify HMAC implementation)
- Supabase tables: `trial_email_log`, `email_preferences`
- `docs/qa/trial-email-coverage.md` (criar)
- `docs/runbooks/trial-email-sequence.md` (criar)

### Testing

- Manual SQL queries em prod (read-only)
- Smoke unsubscribe flow
- Sentry search via API

## Dependencies

- **Bloqueado por:** nenhum (audit puro)
- **Habilita:** confiança para re-prioritizar BACKLOG-1..5 quando volume signup ≥30/mês

## Owners

- Primary: @qa (audit), @dev (correções pontuais HMAC), @devops (Resend webhook health)
- Data: @data-engineer (queries de cobertura)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — audit puro, sem implementação (sequencer já vivo) | @sm (River) |
