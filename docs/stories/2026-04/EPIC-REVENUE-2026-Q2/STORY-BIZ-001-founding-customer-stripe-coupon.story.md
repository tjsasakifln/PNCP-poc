# STORY-BIZ-001: Founding Customer — Stripe Coupon + Landing /founding

**Priority:** P0 — Dispositivo de fechamento low-risk, alto ROI
**Effort:** XS (4 horas)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Wave Receita D+1 a D+7

---

## Contexto

Primeiros 10 clientes sempre têm ciclo de venda mais longo:

- Sem case study social proof
- Sem reviews em G2/Capterra
- Produto ainda em v0.5 (v1.0 prometida)
- Risk-aversion natural de early-adopter B2G (ticket médio R$ 4.764/ano)

Descontar **30% por 12 meses em troca de commitment anual** remove ~R$ 1.430 do atrito de fechamento **sem** deprecar preço de catálogo. Comunicação: "founding partner" — narrativa defensiva quando clientes posteriores questionarem.

Cupom Stripe gerenciado via Dashboard (fora do código) + landing dedicada `/founding` + handler backend que injeta cupom no Checkout Session.

**Impacto esperado:** Reduz objeção de preço para founders B2G wave 1 (outreach de STORY-B2G-001). Estimado: +10pp na trial-to-paid dessa cohort específica.

---

## Acceptance Criteria

### AC1: Cupom Stripe configurado via Dashboard
- [ ] Coupon ID: `FOUNDING30`
- [ ] Desconto: 30% off
- [ ] Duração: 12 meses (depois volta ao preço cheio)
- [ ] Aplicável a: plano SmartLic Pro (todos períodos: mensal, semestral, anual)
- [ ] Limite: 10 usos totais
- [ ] Expira em: 2026-07-18 (D+90 do plano)
- [ ] Restrito a: new customers only (`restrictions.first_time_transaction=true`)

### AC2: Landing page /founding
- [ ] Route: `frontend/app/founding/page.tsx`
- [ ] SEO: `title="SmartLic Founding Partners — Os primeiros 10 clientes moldam o produto"`, `description` otimizada, `noindex` opcional (decidir no DoD)
- [ ] Copy estrutura:
  1. Headline emocional: "Os primeiros 10 clientes do SmartLic moldam o produto. Você pode ser um deles."
  2. 3 parágrafos explicando o deal: 30% off por 12 meses, compromisso anual, voz direta no roadmap
  3. Social proof: "Produto v0.5, 14 dias grátis, infra production-ready (Railway, Supabase, SOC-2 ready)"
  4. CTA principal: formulário qualificatório → Stripe Checkout
  5. FAQ com 5 objeções comuns (preço após 12 meses, cancelamento, suporte, roadmap, escala)
- [ ] Layout responsivo, performance >90 Lighthouse

### AC3: Formulário qualificatório pré-checkout
- [ ] `frontend/app/founding/components/FoundingForm.tsx`
- [ ] Campos: email corporativo, nome completo, CNPJ (validado via Pydantic backend), razão social (auto-complete via BrasilAPI se CNPJ válido), "Por que o SmartLic é relevante para você?" (textarea 140 chars min)
- [ ] Submit chama `POST /v1/founding/checkout` com payload completo
- [ ] Resposta: `{ checkout_url }` — redireciona para Stripe Checkout com cupom aplicado

### AC4: Backend handler /v1/founding/checkout
- [ ] `backend/routes/billing.py` (ou novo `backend/routes/founding.py`) adiciona `@router.post("/founding/checkout")`
- [ ] Validações:
  - Rate limit 3 submissions/IP/hora (Redis)
  - Email não pode existir em `profiles` (evita double-enrollment)
  - CNPJ formato válido + consultável em BrasilAPI (cache 24h)
  - Textarea não vazia, ≥140 chars, ≤1000 chars
- [ ] Criação:
  - Stripe Customer (`email`, `name`, `metadata.cnpj`, `metadata.source='founding'`)
  - Stripe Checkout Session com `discounts=[{coupon: 'FOUNDING30'}]`, `mode='subscription'`, line item plan Pro anual, `success_url=/founding/obrigado`, `cancel_url=/founding`
- [ ] Logging: cada submission em `founding_leads` table (supabase migration) — usado para follow-up manual se checkout abandonado
- [ ] Retorna `{ checkout_url: session.url }`

### AC5: Database: founding_leads table
- [ ] Migration `supabase/migrations/20260420000002_create_founding_leads.sql`:
  ```sql
  CREATE TABLE founding_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    nome TEXT NOT NULL,
    cnpj TEXT NOT NULL,
    razao_social TEXT,
    motivo TEXT NOT NULL,
    checkout_session_id TEXT,
    checkout_status TEXT DEFAULT 'pending', -- pending, completed, abandoned
    stripe_customer_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
  );
  CREATE INDEX idx_founding_leads_email ON founding_leads(email);
  CREATE INDEX idx_founding_leads_status ON founding_leads(checkout_status);
  ```
- [ ] RLS: admins only (apenas admins podem SELECT/UPDATE)
- [ ] Paired `.down.sql`

### AC6: Webhook handler atualiza status
- [ ] `backend/webhooks/stripe.py` handler `checkout.session.completed`:
  - Atualiza `founding_leads.checkout_status='completed'`, `founding_leads.completed_at=NOW()`, `founding_leads.stripe_customer_id=session.customer`
- [ ] Handler `checkout.session.expired`:
  - Atualiza `founding_leads.checkout_status='abandoned'`
  - Dispara email follow-up D+1: "Vi que começou o checkout mas não finalizou — qual foi a dúvida?"

### AC7: Página /founding/obrigado
- [ ] Route: `frontend/app/founding/obrigado/page.tsx`
- [ ] Confirmação: "Bem-vindo ao SmartLic Founding Partners. Em breve receberá acesso ao dashboard + convite para um call de 30min comigo para entender seu caso."
- [ ] Auto-enviar email de boas-vindas via webhook (não usar Next.js — backend)
- [ ] Calendly/Cal.com link embebido para agendar call

### AC8: Observabilidade
- [ ] Evento Mixpanel `founding_page_viewed` ao carregar `/founding`
- [ ] Evento Mixpanel `founding_form_submitted` no submit
- [ ] Evento Mixpanel `founding_checkout_started` após redirect Stripe
- [ ] Evento Mixpanel `founding_checkout_completed` no webhook success
- [ ] Evento Mixpanel `founding_checkout_abandoned` no webhook expired

---

## Arquivos

**Frontend (novos):**
- `frontend/app/founding/page.tsx`
- `frontend/app/founding/components/FoundingForm.tsx`
- `frontend/app/founding/components/FoundingFAQ.tsx`
- `frontend/app/founding/obrigado/page.tsx`

**Backend (novos + modificados):**
- `backend/routes/founding.py` (novo)
- `backend/routes/__init__.py` (registrar novo router)
- `backend/webhooks/stripe.py` (modificar — handlers completed/expired)
- `backend/startup/routes.py` (registrar no `_v1_routers`)

**Database:**
- `supabase/migrations/20260420000002_create_founding_leads.sql`
- `supabase/migrations/20260420000002_create_founding_leads.down.sql`

**Stripe (config externa, não-código):**
- Coupon `FOUNDING30` criado via dashboard
- Documentado em `docs/runbooks/stripe-coupons.md`

**Tests:**
- `backend/tests/test_founding_checkout.py` (novo — ≥8 test cases)
- `frontend/__tests__/founding/FoundingForm.test.tsx` (novo)

---

## Riscos e Mitigações

**Risco 1:** Clientes futuros questionam por que não têm o desconto
- **Mitigação:** Narrativa "founding partner" defensiva: primeiros 10 ajudaram a moldar o produto, receberam desconto em troca. Comunicar em FAQ da landing regular `/pricing`.

**Risco 2:** Cupom é aplicado a signup não qualificado (fora do outreach B2G-001)
- **Mitigação:** Restrição `first_time_transaction=true` no Stripe + cupom público mas landing não indexada (noindex opcional), link compartilhado manualmente no outreach

**Risco 3:** 10 usos preenchidos rapidamente
- **Mitigação:** Sucesso é esse. Se D+30 já tem 10/10 usos, avaliar se vale a pena estender (nova story BIZ-XXX) ou aumentar pricing.

---

## Definition of Done

- [ ] AC1-AC8 todos marcados `[x]`
- [ ] Cupom `FOUNDING30` ativo no Stripe com 10 usos
- [ ] `/founding` live em produção
- [ ] Teste end-to-end: submeter form + completar checkout + webhook atualiza `founding_leads`
- [ ] `docs/runbooks/stripe-coupons.md` commitado
- [ ] PR mergeado, CI verde

---

## Dev Notes

**Sequência de implementação (4h estimadas):**

1. **H1:** Stripe Dashboard setup (cupom) + Supabase migration + backend route stub
2. **H2:** Frontend landing + form + integração ao endpoint
3. **H3:** Webhook handlers + events Mixpanel + página `/founding/obrigado`
4. **H4:** Tests + PR + deploy

**Copy-esboço da landing (validar com @sm antes):**

```
# Os primeiros 10 clientes do SmartLic moldam o produto.

Você pode ser um deles — com 30% de desconto por 12 meses.

O SmartLic está em beta produtivo (v0.5). Já analisamos 2 milhões de contratos públicos, 50 mil licitações abertas, 15 setores. Funciona — mas ainda é jovem.

Nos próximos 90 dias, os primeiros 10 clientes pagantes serão **founding partners**: pagam menos, têm linha direta comigo, têm voz no roadmap.

## O que você ganha

- **30% off por 12 meses** no plano SmartLic Pro (R$ 277,90 vs R$ 397 cheio)
- **Onboarding 1:1 comigo** (30 min via Zoom)
- **Prioridade em feature requests** — o roadmap é feito junto
- **Trial 14 dias grátis** antes da cobrança
- **Cancele a qualquer momento** sem multa

[CTA: Quero ser um founding partner]

## Por que só 10?

Não é gimmick de escassez. É disciplina: founding partners exigem atenção individual. Com mais de 10, não consigo entregar o 1:1. Os próximos clientes pagam preço regular (R$ 397/mês) — que continua competitivo vs concorrentes.

## FAQ
...
```

---

## File List

_(populado pelo @dev durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0. |
