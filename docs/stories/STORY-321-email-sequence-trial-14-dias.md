# STORY-321: Adaptar Email Sequence para Trial de 14 Dias

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 1 (Quick Wins)
**Priority:** P0 — HIGH
**Story Points:** 8 SP
**Estimate:** 5-7 dias
**Owner:** @dev + @data-engineer
**Origem:** TurboCash Playbook — Acao 5 (Otimizar Trial Funnel)
**Supersede:** STORY-310 (email sequence 30 dias — substituida por esta)

---

## Problem

STORY-310 desenhava uma sequencia de 8 emails ao longo de 30 dias. Com a reducao do trial para 14 dias (STORY-319), a cadencia precisa ser comprimida para criar urgencia adequada no novo timeline. Emails nos dias 14, 21, 25, 29, 32 nao fazem mais sentido.

## Solution

Redesenhar a sequencia de emails para 6 touchpoints em 14 dias, com cadencia mais intensa na segunda metade (quando paywall suave esta ativo — STORY-320). Inclui implementacao completa (STORY-310 nao foi implementada).

**Evidencia:** Follow-up boost: +49% reply rate (Backlinko)

---

## Acceptance Criteria

### Backend — Nova Sequencia de Emails (6 emails)

- [ ] **AC1:** Criar `backend/services/trial_email_sequence.py` com logica de disparo:

  | Email | Dia | Objetivo | CTA |
  |-------|-----|----------|-----|
  | 1. Boas-vindas | 0 | Ativar — primeiros passos | "Fazer primeira busca" |
  | 2. Engajamento | 3 | Valor — stats de uso | "Explorar mais setores" |
  | 3. Paywall alert | 7 | Urgencia — paywall ativa amanha | "Assine antes do limite" |
  | 4. Valor acumulado | 10 | Social proof — "Voce ja analisou R$X" | "Nao perca esse progresso" |
  | 5. Ultimo dia | 13 | Escassez — "Amanha seu acesso expira" | "Assinar agora" |
  | 6. Expirado | 16 | Reengajamento — "Sentimos sua falta" | "Voltar com 20% off" |

- [ ] **AC2:** Cada email inclui:
  - Nome do usuario (personalizacao)
  - Stats de uso reais (buscas, oportunidades, valor analisado)
  - CTA principal contextual
  - Link de unsubscribe (RFC 8058 one-click)
  - Preheader text otimizado
- [ ] **AC3:** Respeitar `TRIAL_EMAILS_ENABLED` flag (config.py)
- [ ] **AC4:** Skip se usuario converteu para plano pago
- [ ] **AC5:** Skip se usuario fez unsubscribe de marketing
- [ ] **AC6:** Dedup: tabela `trial_email_log` previne envio duplicado

### Backend — Templates

- [ ] **AC7:** Criar/atualizar templates em `backend/templates/emails/trial.py`:
  - `render_trial_welcome_email()` — 3 passos, screenshot do SmartLic
  - `render_trial_engagement_email()` — stats reais, destaques de uso
  - `render_trial_paywall_alert_email()` — "A partir de amanha, preview limitado"
  - `render_trial_value_email()` — valor acumulado em destaque (R$ grande)
  - `render_trial_last_day_email()` — countdown visual, urgencia
  - `render_trial_expired_email()` — reengajamento com cupom 20% off
- [ ] **AC8:** Reutilizar `_stats_block()` helper existente
- [ ] **AC9:** Reutilizar `base.py` wrapper HTML

### Backend — Cron Job

- [ ] **AC10:** ARQ task `process_trial_emails` em `cron_jobs.py`:
  - Executar diariamente as 08:00 BRT (11:00 UTC)
  - Query: usuarios trial com `created_at` matching cada milestone
  - Batch: max 50 emails/execucao
  - Rate limit: 1 email/usuario/dia (nao empilhar)
- [ ] **AC11:** Criar migration para tabela `trial_email_log`:
  ```sql
  CREATE TABLE trial_email_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email_number INT NOT NULL CHECK (email_number BETWEEN 1 AND 6),
    sent_at TIMESTAMPTZ DEFAULT now(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    UNIQUE(user_id, email_number)
  );
  ALTER TABLE trial_email_log ENABLE ROW LEVEL SECURITY;
  ```

### Backend — Stats Query

- [ ] **AC12:** Funcao `get_trial_user_stats(user_id)` retorna:
  - `searches_executed` (count from search_sessions)
  - `opportunities_found` (sum from search results)
  - `total_value_analyzed` (sum valor_estimado)
  - `pipeline_items` (count from pipeline)
  - `days_remaining` (14 - days_since_created)

### Backend — Cupom Reengajamento

- [ ] **AC13:** Criar Stripe coupon `TRIAL_COMEBACK_20` (20% off primeiro mes)
- [ ] **AC14:** Email 6 (expirado) inclui link de checkout com cupom aplicado automaticamente

### Frontend — Admin Preview

- [ ] **AC15:** Pagina admin `/admin/emails` para preview de todos os 6 templates
- [ ] **AC16:** Botao "Enviar teste" para cada template

### Testes

- [ ] **AC17:** Testes para cada email (6 emails x cenarios)
- [ ] **AC18:** Testes para cron job (scheduling, dedup, rate limit, skip converted)
- [ ] **AC19:** Testes para stats query
- [ ] **AC20:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Trial email templates (4/6) | `backend/templates/emails/trial.py` | Existe parcial |
| Stats block helper | `backend/templates/emails/trial.py:23-71` | Existe |
| Base HTML wrapper | `backend/templates/emails/base.py` | Existe |
| Email service (Resend) | `backend/email_service.py` | Existe |
| Feature flag | `config.py` → `TRIAL_EMAILS_ENABLED` | Existe |
| ARQ queue | `backend/job_queue.py` | Existe |
| Cron framework | `backend/cron_jobs.py` | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/services/trial_email_sequence.py`
- `backend/tests/test_trial_email_sequence.py`
- `supabase/migrations/XXXXXXXX_add_trial_email_log.sql`
- `frontend/app/admin/emails/page.tsx`

**Modificados:**
- `backend/templates/emails/trial.py` (6 templates)
- `backend/cron_jobs.py` (novo task)
- `backend/config.py` (se necessario)

## Dependencias

- STORY-319 (trial 14 dias) — BLOQUEADORA (sequencia depende do novo duration)
- STORY-320 (paywall dia 7) — Email 3 referencia o paywall
- Email service funcional (Resend configurado)

## Riscos

- Rate limiting Resend: verificar limites do plano
- Cadencia comprimida pode parecer spam → monitorar unsubscribe rate
- Cupom 20% off no email 6 pode canibalizar receita → monitorar LTV dos convertidos via cupom
