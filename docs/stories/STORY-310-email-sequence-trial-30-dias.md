# STORY-310: Email Sequence Trial — 30 Dias

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 1 (Pre-GTM)
**Priority:** BLOCKER
**Story Points:** 8 SP
**Estimate:** 5-7 dias
**Owner:** @dev + @data-engineer

---

## Problem

O trial de 30 dias nao possui sequencia de emails automatizada para engajar usuarios e converter em pagantes. Templates ja existem (`trial.py`) mas nao ha cron job disparando os envios. Usuarios entram no trial, podem nunca mais voltar, e expiram sem nenhum contato. Conversao trial→paid e metrica critica pre-launch.

## Solution

Implementar sequencia completa de 8 emails ao longo dos 30 dias de trial, utilizando os templates existentes + novos, disparados por cron job ARQ. Tracking de opens/clicks para otimizacao.

---

## Acceptance Criteria

### Backend — Sequencia de Emails

- [ ] **AC1:** Criar `backend/services/trial_email_sequence.py` com logica de disparo baseada em `created_at` do perfil:
  - Dia 0: Email de boas-vindas + primeiros passos (novo template)
  - Dia 3: Email midpoint com stats de uso (template existente: `render_trial_midpoint_email`)
  - Dia 7: Email de engajamento "Voce ja descobriu X oportunidades" (novo)
  - Dia 14: Email educacional "3 dicas para maximizar o SmartLic" (novo)
  - Dia 21: Email de urgencia leve "Faltam 9 dias" (novo)
  - Dia 25: Email expiring com stats (template existente: `render_trial_expiring_email`)
  - Dia 29: Email last day (template existente: `render_trial_last_day_email`)
  - Dia 32: Email expired reengagement (template existente: `render_trial_expired_email`)
- [ ] **AC2:** Cada email deve incluir:
  - Nome do usuario
  - Stats de uso (buscas realizadas, oportunidades encontradas, valor total analizado)
  - CTA principal contextual (varia por email)
  - Link de unsubscribe (RFC 8058 one-click)
- [ ] **AC3:** Respeitar `TRIAL_EMAILS_ENABLED` flag em `config.py` (ja existe)
- [ ] **AC4:** Nao enviar email se usuario ja converteu para plano pago
- [ ] **AC5:** Nao enviar email se usuario fez unsubscribe de marketing

### Backend — Templates Novos

- [ ] **AC6:** Criar 4 novos templates em `backend/templates/emails/trial.py`:
  - `render_trial_welcome_email()` — Boas-vindas, 3 passos iniciais, CTA "Fazer primeira busca"
  - `render_trial_engagement_email()` — Stats de uso, destaques, CTA "Explorar mais"
  - `render_trial_tips_email()` — 3 dicas praticas, CTA "Aplicar dicas"
  - `render_trial_urgency_email()` — Countdown, stats, CTA "Assinar agora"
- [ ] **AC7:** Reutilizar `_stats_block()` helper existente em `trial.py:23-71` para blocos de estatisticas
- [ ] **AC8:** Reutilizar `base.py` wrapper HTML para layout consistente

### Backend — Cron Job / ARQ Worker

- [ ] **AC9:** Criar ARQ task `process_trial_emails` em `cron_jobs.py`:
  - Executar diariamente as 08:00 BRT (11:00 UTC, alinhado com `ALERTS_HOUR_UTC`)
  - Query: usuarios com `plan_type = 'free_trial'` e `created_at` matching cada milestone
  - Batch processing com rate limit (max 50 emails/execucao)
- [ ] **AC10:** Criar tabela `trial_email_log` para tracking:
  - `user_id`, `email_number` (1-8), `sent_at`, `opened_at`, `clicked_at`
  - Constraint UNIQUE(user_id, email_number) — previne duplicatas
- [ ] **AC11:** Integrar com Resend webhook para tracking de opens/clicks (se Resend suportar)

### Backend — Stats Query

- [ ] **AC12:** Criar funcao `get_trial_user_stats(user_id)` que retorna:
  - `searches_executed` (count from search_sessions)
  - `opportunities_found` (sum from search results)
  - `total_value_analyzed` (sum valor_estimado)
  - `pipeline_items` (count from pipeline)
  - `days_remaining` (30 - days_since_created)

### Frontend — Email Preview (Admin)

- [ ] **AC13:** Adicionar pagina admin `/admin/emails` para preview de todos os templates
- [ ] **AC14:** Botao "Enviar teste" para cada template (envia para admin logado)

### Testes

- [ ] **AC15:** Testes para cada email da sequencia (8 emails x cenarios)
- [ ] **AC16:** Testes para cron job (scheduling, dedup, rate limit, skip converted)
- [ ] **AC17:** Testes para stats query
- [ ] **AC18:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Trial email templates (4/8) | `backend/templates/emails/trial.py:1-258` | Existe parcial |
| Stats block helper | `backend/templates/emails/trial.py:23-71` | Existe |
| Base HTML wrapper | `backend/templates/emails/base.py` | Existe |
| Email service (Resend) | `backend/email_service.py` | Existe |
| Feature flag | `config.py` → `TRIAL_EMAILS_ENABLED` | Existe |
| ARQ queue | `backend/job_queue.py` | Existe |
| Cron framework | `backend/cron_jobs.py` | Existe |
| Trial status endpoint | `backend/routes/user.py` → GET /trial-status | Existe |
| Trial value analytics | `backend/routes/analytics.py` → GET /trial-value | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/services/trial_email_sequence.py`
- `backend/tests/test_trial_email_sequence.py`
- `supabase/migrations/XXXXXXXX_add_trial_email_log.sql`
- `frontend/app/admin/emails/page.tsx`

**Modificados:**
- `backend/templates/emails/trial.py` (4 novos templates)
- `backend/cron_jobs.py` (novo task)

## Dependencias

- Email service funcional (Resend configurado)
- STORY-308 (dashboard) para metricas de conversao

## Riscos

- Rate limiting Resend: verificar limites do plano atual
- Spam filters: emails transacionais devem passar SPF/DKIM (ja configurado para smartlic.tech)
- Horario de envio: 08:00 BRT e otimo para Brasil, mas considerar timezone do usuario no futuro
