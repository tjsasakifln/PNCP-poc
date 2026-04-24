# GV-021: Churn Win-Back Campaign (Cancelled Users)

**Priority:** P1
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @data-engineer
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Users que cancelaram subscription = não são trial-expired (coberto por STORY-369 Exit Survey), são **paid users que saíram**. Hoje SmartLic não tem pipeline automatizado de reativação para esse segmento.

Industry benchmark B2B: reativação bem-feita recupera 8-12% de LTV perdida. É P1 para revenue recovery + fecha gap identificado em advisor review.

---

## Acceptance Criteria

### AC1: Trigger via Stripe webhook

- [ ] `backend/webhooks/stripe.py` estende handler para `subscription.deleted`:
  - Registra event em tabela `churn_events`:
    ```sql
    CREATE TABLE churn_events (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID REFERENCES auth.users(id),
      stripe_subscription_id TEXT,
      plan_type TEXT,
      churned_at TIMESTAMPTZ NOT NULL,
      cancellation_reason TEXT,
      months_as_customer INTEGER,
      mrr_lost_brl NUMERIC,
      winback_emails_sent INTEGER DEFAULT 0,
      reactivated BOOLEAN DEFAULT FALSE,
      reactivated_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```

### AC2: Cron scheduler win-back

- [ ] `backend/jobs/cron/win_back_campaigns.py`:
  - Trigger diário 10h BRT
  - Identifica users churned em janelas: D+7, D+30, D+90
  - Envia email correspondente + incrementa counter
  - Respeita unsubscribe global

### AC3: Email templates + offers

- [ ] D+7 `backend/templates/emails/winback_d7.html`:
  - "O que faltou?"
  - Survey 3-pergunta (feedback valioso + sinal de intent)
  - Sem oferta ainda (relationship-first)
- [ ] D+30 `backend/templates/emails/winback_d30.html`:
  - "Novidades desde sua saída" (3 features recentes destacadas)
  - Cupom `WINBACK30` 30% off primeiro mês reativação (one-time)
  - CTA "Voltar para SmartLic"
- [ ] D+90 `backend/templates/emails/winback_d90.html`:
  - "Última chamada"
  - Cupom `WINBACK50_ANNUAL` 50% off primeiro ano
  - Forte urgência + CTA definitivo

### AC4: Stripe cupons

- [ ] Setup via API:
  - `WINBACK30` — 30% off, 1 month, one-time use per customer
  - `WINBACK50_ANNUAL` — 50% off, 1 year, one-time use per customer
- [ ] Backend valida aplicação apenas para user em `churn_events`

### AC5: A/B subject lines mandatório

- [ ] Experiments registrados em `frontend/config/experiments.ts`:
  - `gv_021_winback_d7`: "O que faltou?" vs "Feedback: como podemos melhorar?"
  - `gv_021_winback_d30`: "Novidades esperando por você" vs "3 features que você perdeu" vs "30% off para voltar"
- [ ] Subject variants via Resend tags; tracking Mixpanel

### AC6: Dashboard cohort analytics

- [ ] `frontend/app/admin/churn/page.tsx` (admin only):
  - Cohort chart: % reactivation por mês churn (D+90 window)
  - Conversion por winback tier
  - MRR recuperado total
- [ ] Target: D+90 reactivation rate ≥8%

### AC7: Opt-out global

- [ ] Unsubscribe 1-click em todos emails winback
- [ ] Opt-out respeitado para futuros churn events também

### AC8: Testes

- [ ] Unit trigger logic (Stripe webhook → event logged)
- [ ] Integration cron → email sent via Resend mock
- [ ] E2E: simulate Stripe cancel → D+7 email → user opens → click cupom link → reactivation

---

## Scope

**IN:**
- Stripe webhook trigger
- Tabela churn_events
- 3 emails winback D+7/30/90
- Cupons Stripe
- A/B subject lines
- Dashboard admin cohort
- Opt-out global

**OUT:**
- Reactivation via call center (ops separado)
- Win-back via SMS/WhatsApp (email-first)
- Personalized cupom dinâmico por valor LTV (v2 ML)

---

## Dependências

- **GV-001** (A/B framework) — subject lines
- Stripe webhook handler existente
- Resend email service

---

## Riscos

- **Email spam complaints (3 emails em 90d):** opt-out 1-click + throttle max 3 per user lifetime winback
- **Cupom abuse (criar conta nova para re-cupom):** enforcement via Stripe customer_id + email uniqueness + CNPJ
- **Win-back canibaliza revenue de users que voltariam organicamente:** métrica incrementality (A/B holdout 10%)
- **LGPD — reativação após opt-out:** respeitar consent status global

---

## Arquivos Impactados

### Novos
- `backend/jobs/cron/win_back_campaigns.py`
- `backend/templates/emails/winback_d7.html`
- `backend/templates/emails/winback_d30.html`
- `backend/templates/emails/winback_d90.html`
- `backend/services/churn_analytics.py`
- `frontend/app/admin/churn/page.tsx`
- `supabase/migrations/YYYYMMDDHHMMSS_churn_events.sql` (+ down)
- `backend/tests/test_winback.py`

### Modificados
- `backend/webhooks/stripe.py` (handler subscription.deleted estendido)
- `frontend/config/experiments.ts` (registra experiments subject)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — gap advisor apontou, revenue recovery pipeline automatizado |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. A/B subject lines mandatório. Métrica incrementality via holdout 10%. Status Draft → Ready. |
