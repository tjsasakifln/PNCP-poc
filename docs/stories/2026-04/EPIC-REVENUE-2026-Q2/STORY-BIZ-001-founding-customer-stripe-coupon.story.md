# STORY-BIZ-001: Founding Customer — Stripe Coupon + Landing /founding

**Priority:** P0 — Dispositivo de fechamento low-risk, alto ROI
**Effort:** XS (4 horas)
**Squad:** @dev
**Status:** Done
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
- [ ] **(post-merge)** Coupon ID `FOUNDING30` criado via Stripe Dashboard — instruções completas em `docs/runbooks/stripe-coupons.md`
- [ ] **(post-merge)** Desconto 30% off, duração 12 meses, limite 10 usos, expira 2026-07-18
- [ ] **(post-merge)** Promotion Code `FOUNDING30` com `restrictions.first_time_transaction=true`

### AC2: Landing page /founding
- [x] Route: `frontend/app/founding/page.tsx`
- [x] SEO: title, description otimizados + `noindex` ativado (landing não-pública)
- [x] Copy estrutura:
  1. Headline emocional: "Os primeiros 10 clientes do SmartLic moldam o produto. Você pode ser um deles."
  2. 3 parágrafos explicando o deal: 30% off por 12 meses, compromisso anual, voz direta no roadmap
  3. Social proof: "Produto v0.5, 14 dias grátis, infra production-ready (Railway, Supabase, SOC-2 ready)"
  4. CTA principal: formulário qualificatório → Stripe Checkout
  5. FAQ com 5 objeções comuns (preço após 12 meses, cancelamento, suporte, roadmap, escala)
- [x] Layout responsivo (Tailwind + prose), mobile-first
- [ ] **(post-merge)** Lighthouse > 90 (validar em produção após deploy)

### AC3: Formulário qualificatório pré-checkout
- [x] `frontend/app/founding/components/FoundingForm.tsx` implementado
- [x] Campos: email, nome, CNPJ (auto-máscara XX.XXX.XXX/XXXX-XX + validado no backend com dígitos verificadores), razão social opcional, motivo (textarea 140-1000 chars)
- Nota: auto-complete via BrasilAPI adiado para story futura (reduz escopo de 1 chamada externa no hot-path)
- [x] Submit chama `POST /api/founding/checkout` (proxy Next → `/v1/founding/checkout`)
- [x] Sucesso: `{ checkout_url, lead_id }` com redirect via `window.location.href`
- [x] Erro 4xx: exibe `detail` do backend; erro de rede: mensagem genérica

### AC4: Backend handler /v1/founding/checkout
- [x] `backend/routes/founding.py` novo, registrado em `backend/startup/routes.py::_v1_routers`
- [x] Validações:
  - [x] Rate limit 3 submissions/IP/hora via `FlexibleRateLimiter` (já existente, Redis + fallback in-memory)
  - [x] Email já existente em `profiles` → HTTP 409 (evita double-enrollment)
  - [x] CNPJ formato + dígitos verificadores (função pura `_is_valid_cnpj_check_digits`)
  - Nota: validação BrasilAPI externa não feita no hot-path (ruim para latência + rate-limit externo); CNPJ check digits é suficiente para front-gate.
  - [x] Motivo 140-1000 chars via Pydantic field validator
- [x] Criação Stripe Checkout Session com `discounts=[{promotion_code}]` (fallback para coupon id direto), `mode='subscription'`, plano Pro anual (`plan_billing_periods`), metadata `{source: 'founding', founding_lead_id, cnpj}`
- [x] Lead row persistido em `founding_leads` ANTES do Stripe call (para capturar abandonos); session_id atualizado pós-Stripe
- [x] Retorna `{ checkout_url, lead_id }`

### AC5: Database: founding_leads table
- [x] Migration `supabase/migrations/20260420000001_create_founding_leads.sql` (número ajustado vs story original: 20260420000001 é o primeiro livre; 20260420000002 fica para BIZ-002 se precisar)
- [x] Campos: id (uuid), email, nome, cnpj, razao_social, motivo, checkout_session_id, checkout_status (enum pending/completed/abandoned/failed), stripe_customer_id, ip_address, user_agent, created_at, completed_at
- [x] RLS: admins (`plan_type='master'`) leem; service_role escreve
- [x] 3 índices: email, status (partial where !=completed), session_id (partial where not null)
- [x] Paired `.down.sql` criado
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
- [x] `webhooks/handlers/founding.py` novo com `mark_founding_lead_completed` + `mark_founding_lead_abandoned`
- [x] `checkout.session.completed` hook em `handle_checkout_session_completed` — filtro `metadata.source=='founding'` garante que só founding leads são afetados
- [x] `checkout.session.expired` adicionado ao dispatcher em `webhooks/stripe.py` — chama `mark_founding_lead_abandoned` para founding sessions; no-op para sessões regulares
- [x] Idempotente + survive DB errors (non-fatal — nunca quebra flow principal de checkout)
- [ ] **(post-merge)** Email follow-up D+1 para abandonos — adiado para story futura (precisa queue ARQ + template)

### AC7: Página /founding/obrigado
- [x] Route: `frontend/app/founding/obrigado/page.tsx` + `FoundingObrigadoClient.tsx`
- [x] Confirmação estruturada com lista de próximos passos (credenciais, trial 14d, call)
- [x] Link Cal.com configurável via `NEXT_PUBLIC_FOUNDING_CALENDLY_URL` (default `https://cal.com/tiago-sasaki/founding-onboarding`)
- [ ] **(post-merge)** Email de boas-vindas via webhook Stripe — reutilizará fluxo existente de welcome email após primeira cobrança (já existe em `webhooks/handlers/checkout.py`)

### AC8: Observabilidade
- [x] `founding_page_viewed` disparado em `FoundingClient.tsx::useEffect` no mount
- [x] `founding_form_submitted` disparado em `FoundingForm.tsx::handleSubmit` pre-fetch
- [x] `founding_checkout_started` disparado após response.ok antes do redirect Stripe
- [x] `founding_checkout_completed` disparado em `/founding/obrigado` mount (melhor proxy que webhook para engagement front)
- Nota: `founding_checkout_abandoned` para Mixpanel exigiria server-sent event — substituído por log `WARN` + telemetry no backend (Sentry breadcrumb possível em story futura)

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

**Frontend (novos):**
- `frontend/app/founding/page.tsx` (server component + metadata)
- `frontend/app/founding/FoundingClient.tsx` (client entry com Mixpanel mount)
- `frontend/app/founding/components/FoundingForm.tsx` (form + validação + CNPJ mask)
- `frontend/app/founding/components/FoundingFAQ.tsx` (acordeão, 5 objeções)
- `frontend/app/founding/obrigado/page.tsx` + `FoundingObrigadoClient.tsx`
- `frontend/app/api/founding/checkout/route.ts` (Next proxy para backend)
- `frontend/__tests__/founding/FoundingForm.test.tsx` (7 casos, todos passando)

**Backend (novos):**
- `backend/routes/founding.py` (POST `/v1/founding/checkout` + CNPJ validator + Stripe Session create)
- `backend/webhooks/handlers/founding.py` (`mark_founding_lead_completed`, `mark_founding_lead_abandoned`)
- `backend/tests/test_founding_checkout.py` (21 casos, todos passando)

**Backend (modificados):**
- `backend/startup/routes.py` — registra `founding_router` em `_v1_routers`
- `backend/webhooks/stripe.py` — adiciona dispatcher branch `checkout.session.expired`
- `backend/webhooks/handlers/checkout.py` — hook `mark_founding_lead_completed` no topo do `handle_checkout_session_completed`

**Database:**
- `supabase/migrations/20260420000001_create_founding_leads.sql`
- `supabase/migrations/20260420000001_create_founding_leads.down.sql`

**Documentação:**
- `docs/runbooks/stripe-coupons.md` (instruções Dashboard + verificação + rollback)

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0. |
| 2026-04-19 | @dev | Implementação code-side completa. 21/21 testes backend + 7/7 testes frontend passando. 114/114 testes stripe webhook zero regressão. AC1 (coupon Dashboard) e emails de boas-vindas/abandono ficam post-merge (requerem setup externo ou story futura). Status → InReview. |
| 2026-04-19 | @devops (Gage) | Status InReview → Done. PR #388 merged to main. Código, testes e docs em produção. Status-sync post-merge. |
