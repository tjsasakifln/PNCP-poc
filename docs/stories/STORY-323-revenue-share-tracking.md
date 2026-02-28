# STORY-323: Revenue Share Tracking — UTM + Cupom por Consultoria

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 2 (Short-Term Revenue)
**Priority:** P1 — HIGH
**Story Points:** 8 SP
**Estimate:** 4-6 dias
**Owner:** @dev + @data-engineer
**Origem:** TurboCash Playbook — Acao 4 (Revenue Share com 3 Consultorias)

---

## Problem

O TurboCash propoe revenue share de 25% com consultorias parceiras. Para funcionar, precisamos rastrear qual consultoria indicou cada cliente (via UTM + cupom), calcular o revenue share automaticamente, e dar visibilidade as consultorias sobre suas indicacoes. STORY-289 cobre referral entre usuarios individuais (+7 dias), mas nao cobre revenue share B2B com consultorias.

## Solution

Sistema de partner tracking com:
- Link de indicacao por consultoria (`/signup?partner=triunfo-legis`)
- Cupom exclusivo por consultoria (ex: `TRIUNFO25`)
- Dashboard parceiro mostrando indicacoes e revenue share
- Calculo automatico de 25% da mensalidade por cliente indicado
- Relatorio mensal para o founder pagar os parceiros

**Evidencia:** Revenue share vs flat fee partners: +32% performance (PartnerStack)

---

## Acceptance Criteria

### Backend — Modelo de Dados

- [ ] **AC1:** Migration para tabela `partners`:
  ```sql
  CREATE TABLE partners (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,  -- ex: "triunfo-legis"
    contact_email TEXT NOT NULL,
    contact_name TEXT,
    stripe_coupon_id TEXT,      -- cupom Stripe vinculado
    revenue_share_pct NUMERIC(5,2) DEFAULT 25.00,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending')),
    created_at TIMESTAMPTZ DEFAULT now()
  );
  ```
- [ ] **AC2:** Migration para tabela `partner_referrals`:
  ```sql
  CREATE TABLE partner_referrals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    partner_id UUID REFERENCES partners(id),
    referred_user_id UUID REFERENCES auth.users(id),
    signup_at TIMESTAMPTZ DEFAULT now(),
    converted_at TIMESTAMPTZ,          -- quando assinou plano pago
    churned_at TIMESTAMPTZ,            -- quando cancelou
    monthly_revenue NUMERIC(10,2),     -- valor da mensalidade
    revenue_share_amount NUMERIC(10,2) -- 25% do monthly_revenue
  );
  ```
- [ ] **AC3:** RLS: parceiro so ve seus proprios referrals; admin ve todos

### Backend — Signup com Partner Tracking

- [ ] **AC4:** Endpoint de signup captura `partner` query param:
  - `/signup?partner=triunfo-legis` → salva `partner_id` no perfil do usuario
  - Persiste em `profiles.referred_by_partner_id`
- [ ] **AC5:** Se cupom aplicado no checkout corresponde a um parceiro → vincular automaticamente
- [ ] **AC6:** Webhook `checkout.session.completed` → cria registro em `partner_referrals` com `converted_at`
- [ ] **AC7:** Webhook `customer.subscription.deleted` → atualiza `churned_at`

### Backend — Calculo de Revenue Share

- [ ] **AC8:** Funcao `calculate_partner_revenue(partner_id, month)`:
  - Soma `monthly_revenue` de todos os referrals ativos no mes
  - Aplica `revenue_share_pct` (default 25%)
  - Retorna: total revenue, share amount, count de clientes ativos
- [ ] **AC9:** Cron job mensal (dia 1, 09:00 BRT): gera relatorio de revenue share para todos os parceiros

### Backend — API Endpoints

- [ ] **AC10:** `GET /v1/admin/partners` — listar parceiros (admin only)
- [ ] **AC11:** `POST /v1/admin/partners` — criar parceiro (admin only)
- [ ] **AC12:** `GET /v1/admin/partners/{id}/referrals` — referrals do parceiro (admin only)
- [ ] **AC13:** `GET /v1/admin/partners/{id}/revenue` — revenue share do parceiro (admin only)
- [ ] **AC14:** `GET /v1/partner/dashboard` — dashboard para o parceiro logado (self-service futuro)

### Backend — Stripe Coupons

- [ ] **AC15:** Script para criar cupons Stripe por parceiro:
  - Cupom: `{PARTNER_SLUG}_25` (ex: `TRIUNFO_25`)
  - Tipo: porcentagem, 25% off, duracao: forever (enquanto parceria ativa)
  - Vinculado ao `partners.stripe_coupon_id`

### Frontend — Partner Landing

- [ ] **AC16:** Pagina `/signup` detecta `?partner=slug` e:
  - Exibe badge "Indicado por {partner.name}"
  - Salva `partner` em cookie/localStorage para persistir ate checkout
  - Aplica cupom automaticamente no checkout
- [ ] **AC17:** Pagina `/planos` detecta partner cookie e mostra preco com desconto

### Frontend — Admin Dashboard

- [ ] **AC18:** Pagina admin `/admin/partners`:
  - Lista de parceiros (nome, email, referrals ativos, revenue share mensal)
  - Detalhe por parceiro: lista de clientes indicados, status, valor
  - Relatorio mensal exportavel (CSV)

### Testes

- [ ] **AC19:** Testes: signup com partner param → vincula parceiro
- [ ] **AC20:** Testes: checkout com cupom → cria partner_referral
- [ ] **AC21:** Testes: calculo de revenue share (mensal)
- [ ] **AC22:** Testes: churn atualiza referral
- [ ] **AC23:** Zero regressions

---

## Files Esperados (Output)

**Novos:**
- `supabase/migrations/XXXXXXXX_create_partners.sql`
- `backend/routes/partners.py`
- `backend/services/partner_service.py`
- `backend/tests/test_partners.py`
- `frontend/app/admin/partners/page.tsx`
- `frontend/__tests__/admin/partners.test.tsx`
- `scripts/create_partner_coupons.py`

**Modificados:**
- `backend/routes/billing.py` (aplicar cupom de parceiro)
- `backend/webhooks/stripe.py` (vincular partner_referral)
- `backend/cron_jobs.py` (relatorio mensal)
- `frontend/app/signup/page.tsx` (partner badge)
- `frontend/app/planos/page.tsx` (preco com desconto)

## Dependencias

- Stripe coupons criados (AC15)
- 3 consultorias Tier 1 identificadas no TurboCash (Triunfo Legis, Concreta, Brasil Licitar)

## Riscos

- Parceiros aceitam acesso gratis mas nao indicam → monitorar conversion rate por parceiro
- Revenue share de 25% pode reduzir margem se LTV for baixo → monitorar LTV de indicados
- Self-service dashboard para parceiros (AC14) pode ser fase 2
