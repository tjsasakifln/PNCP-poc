# STORY-309: Dunning — Recuperacao de Pagamentos

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 1 (Pre-GTM)
**Priority:** BLOCKER
**Story Points:** 8 SP
**Estimate:** 3-5 dias
**Owner:** @dev + @devops

---

## Problem

Quando o pagamento de um assinante falha (cartao expirado, saldo insuficiente, etc.), o sistema atual envia apenas 1 email generico e marca o status como `past_due`. Nao existe sequencia de recuperacao, escalada de urgencia, nem CTA in-app alem do banner basico. Resultado: perda de receita por churn involuntario sem tentativa real de recuperacao.

Estudos indicam que 20-40% do churn em SaaS e involuntario (falha de pagamento, nao insatisfacao). Com dunning adequado, 50-70% desses pagamentos sao recuperaveis.

## Solution

Implementar fluxo completo de dunning com:
1. Sequencia de 4 emails com urgencia escalada (dia 0, 3, 7, 14)
2. Banner in-app persistente e contextual durante `past_due`
3. Modal bloqueante no grace period pos-retry
4. Degradacao gradual de acesso (full → read-only → bloqueio)
5. Metricas Prometheus para tracking de recuperacao
6. Configuracao via Stripe Smart Retries (8 tentativas / 14 dias)

---

## Acceptance Criteria

### Backend — Sequencia de Emails Dunning

- [x] **AC1:** Criar `backend/services/dunning.py` com logica de sequencia de emails baseada em `attempt_count` do Stripe:
  - Tentativa 1 (dia 0): Email amigavel "Isso acontece — vamos resolver rapidinho"
  - Tentativa 2 (dia 3): Lembrete gentil "Acao necessaria: atualize seu pagamento"
  - Tentativa 3 (dia 7): Urgencia "Sua assinatura esta em risco — X dias restantes"
  - Tentativa 4 (dia 14): Aviso final "Aviso final: sua conta sera suspensa amanha"
- [x] **AC2:** Criar templates em `backend/templates/emails/dunning.py` com:
  - Nome do usuario, plano, valor, motivo da falha
  - Dias restantes ate cancelamento (countdown)
  - CTA unico: "Atualizar Forma de Pagamento" → Stripe Billing Portal
  - Tom: empatico, sem culpa ("voce deve"), direto ("pagamento falhou")
  - Remetente: "Tiago from SmartLic" (nao noreply@)
- [x] **AC3:** Atualizar `_handle_invoice_payment_failed()` em `webhooks/stripe.py:675` para:
  - Chamar `dunning.send_dunning_email(user_id, attempt_count, invoice_data)`
  - Extrair `decline_type` (soft vs hard) do charge details
  - Registrar `decline_code` no log estruturado
- [x] **AC4:** Criar cron job em `cron_jobs.py` para email pre-dunning:
  - 7 dias antes de vencimento do cartao: "Seu cartao termina em MM/AA — atualize"
  - Usar webhook `invoice.upcoming` como trigger alternativo

### Backend — Degradacao Gradual de Acesso

- [x] **AC5:** Atualizar `quota.py` para implementar acesso gradual durante `past_due`:
  - Dias 0-14 (Smart Retries ativas): Acesso completo, banner de aviso
  - Dias 14-21 (grace period estendido): Read-only (pipeline, historico), novas buscas bloqueadas
  - Dia 21+: Acesso totalmente bloqueado, redirecionar para /planos
- [x] **AC6:** Estender `SUBSCRIPTION_GRACE_DAYS` de 3 para 7 dias (pos-retry) em `quota.py:573`
- [x] **AC7:** Adicionar campo `first_failed_at` em `user_subscriptions` para calcular dias desde primeira falha (migration necessaria)

### Backend — Metricas e Observabilidade

- [x] **AC8:** Adicionar metricas Prometheus em `metrics.py`:
  - `smartlic_dunning_emails_sent_total` (labels: email_number, plan_type)
  - `smartlic_dunning_recovery_total` (labels: recovered_via: email|in_app|self_service)
  - `smartlic_dunning_churned_total` (labels: decline_type: soft|hard)
  - `smartlic_subscription_past_due_gauge` (current count)
  - `smartlic_payment_failure_total` (labels: decline_type, decline_code)
- [x] **AC9:** Logging estruturado em cada etapa do dunning para analytics:
  - `dunning_email_sent`, `dunning_recovered`, `dunning_churned`
  - Incluir: user_id (sanitized), plan_type, attempt_count, decline_type, days_since_failure

### Backend — Webhook Enhancements

- [x] **AC10:** Adicionar handler para `invoice.payment_action_required` (3D Secure / SCA):
  - Enviar email com link para completar autenticacao
- [x] **AC11:** Atualizar `_handle_invoice_payment_succeeded()` em `webhooks/stripe.py:612` para:
  - Limpar estado dunning (reset `first_failed_at`, subscription_status → "active")
  - Enviar email "Pagamento restaurado com sucesso!"
  - Incrementar `smartlic_dunning_recovery_total`

### Frontend — Banners e CTAs In-App

- [x] **AC12:** Evoluir `PaymentFailedBanner.tsx` com 3 niveis de urgencia visual:
  - `past_due` recente (0-7 dias): Banner amarelo, tom informativo
  - `past_due` critico (7-14 dias): Banner vermelho, countdown de dias
  - Grace period (14-21 dias): Banner vermelho escuro com "Acesso limitado — X dias restantes"
- [x] **AC13:** Criar modal bloqueante `PaymentRecoveryModal.tsx` para grace period:
  - Full-screen overlay (reutilizar pattern de TrialConversionScreen)
  - Mostrar valor ja analisado (reusar endpoint `/v1/analytics/trial-value`)
  - Countdown de dias restantes
  - CTA: "Atualizar Pagamento Agora" → Stripe Billing Portal
- [x] **AC14:** Mostrar badge vermelho no nav item "Conta" quando `past_due`
- [x] **AC15:** Apos recuperacao: banner verde "Pagamento restaurado" com fade-out 5s (reusar pattern CRIT-008 recovered)

### Frontend — Feature Degradation UI

- [x] **AC16:** Em `/buscar` durante grace period: mostrar banner "Novas buscas suspensas ate regularizacao. Historico e pipeline acessiveis."
- [x] **AC17:** Desabilitar botao "Buscar" durante grace period com tooltip explicativo
- [x] **AC18:** Pipeline e historico permanecem read-only acessiveis

### Testes

- [x] **AC19:** Backend: Testes para cada email da sequencia (4), degradacao gradual (3 fases), metricas, webhook enhancements — minimo 20 testes (35 tests in test_dunning.py)
- [x] **AC20:** Frontend: Testes para 3 niveis de banner, modal bloqueante, badge, recovery banner — minimo 12 testes (18 tests in dunning-flow.test.tsx)
- [x] **AC21:** Zero regressions no test suite existente (BE: 6092 pass, FE: 3641 pass)

### Configuracao Stripe (Dashboard)

- [x] **AC22:** Configurar Smart Retries: 8 tentativas over 2 semanas _(verificado via Playwright: ja configurado — 8 vezes / 2 semanas)_
- [x] **AC23:** Apos retries esgotadas: marcar como `unpaid` (nao cancelar — permite reativacao) _(verificado via Playwright: "deixar a assinatura vencida" por 60 dias)_

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Payment failed handler | `backend/webhooks/stripe.py:675-763` | Existe, precisa estender |
| Payment failed email | `backend/templates/emails/billing.py:177-253` | Existe (1 template), precisa 4 |
| PaymentFailedBanner | `frontend/components/billing/PaymentFailedBanner.tsx` | Existe, precisa evoluir |
| Grace period | `backend/quota.py:573` (3 dias) | Existe, precisa estender para 7 |
| Billing portal | `backend/routes/billing.py` POST /billing-portal | Existe |
| Email service | `backend/email_service.py` | Existe (Resend + async) |
| Stripe webhook idempotency | `backend/webhooks/stripe.py:55-149` | Existe |
| Prometheus metrics | `backend/metrics.py` | Existe, adicionar novas |

## Files Esperados (Output)

**Novos:**
- `backend/services/dunning.py`
- `backend/templates/emails/dunning.py`
- `frontend/components/billing/PaymentRecoveryModal.tsx`
- `backend/tests/test_dunning.py`
- `frontend/__tests__/billing/dunning-flow.test.tsx`
- `supabase/migrations/XXXXXXXX_add_dunning_fields.sql`

**Modificados:**
- `backend/webhooks/stripe.py`
- `backend/quota.py`
- `backend/cron_jobs.py`
- `backend/metrics.py`
- `frontend/components/billing/PaymentFailedBanner.tsx`
- `frontend/app/buscar/page.tsx`

## Dependencias

- STORY-308 (Founder Dashboard) — metricas de dunning alimentam dashboard
- Stripe Dashboard configurado com Smart Retries

## Riscos

- Stripe Smart Retries vs custom retry: **usar Smart Retries** (ML-optimized, respeita limites Visa/Mastercard)
- Card network limits: Visa 15 tentativas/30 dias, Mastercard 35/30 dias — Smart Retries respeita automaticamente
- Nao construir retry logic custom — investir esforco em emails + UX in-app
