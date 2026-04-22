# MON-DIST-02: White-label para Consultorias (Stripe Connect + Branding Customizado)

**Priority:** P2
**Effort:** XL (8-10 dias)
**Squad:** @dev + @architect + @devops
**Status:** Draft
**Epic:** [EPIC-MON-DIST-2026-04](EPIC-MON-DIST-2026-04.md)
**Sprint:** Wave 3 (depende MON-REP-01 + MON-SUB-01)

---

## Contexto

~15% das empresas B2G usam **consultorias especializadas** em licitação — canal paralelo massivo. Modelo: consultoria A revende relatórios/monitores/Copilot com sua marca + Stripe Connect revshare.

**Benefícios:**
- Consultoria traz carteira existente de clientes (distribuição)
- SmartLic cobra revshare (20-50% flat sobre GMV)
- Consultoria oferece serviço "premium branded" sem precisar construir backend

**Mecânica Stripe Connect Express:** consultoria faz onboarding → SmartLic processa pagamento (customer do consultor) → Stripe transfere automaticamente % para conta conectada.

---

## Acceptance Criteria

### AC1: Schema partners

- [ ] Migração:
```sql
CREATE TABLE public.partner_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_name text NOT NULL,
  slug text UNIQUE NOT NULL,  -- usado em URL /parceiros/{slug}
  cnpj varchar(14) NOT NULL,
  contact_email text NOT NULL,
  logo_url text NULL,
  primary_color text NULL DEFAULT '#000000',
  revshare_pct numeric(4,2) NOT NULL CHECK (revshare_pct BETWEEN 10 AND 80),
  stripe_connect_account_id text UNIQUE NULL,
  stripe_connect_onboarded boolean NOT NULL DEFAULT false,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE public.partner_clients (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id uuid NOT NULL REFERENCES partner_accounts(id),
  end_user_id uuid NOT NULL REFERENCES auth.users(id),
  acquired_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(partner_id, end_user_id)
);

CREATE TABLE public.partner_revshare_events (
  id bigserial PRIMARY KEY,
  partner_id uuid NOT NULL REFERENCES partner_accounts(id),
  purchase_id uuid NULL REFERENCES purchases(id),
  subscription_id uuid NULL REFERENCES monitored_subscriptions(id),
  gmv_cents int NOT NULL,
  revshare_cents int NOT NULL,
  stripe_transfer_id text NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
```

### AC2: Stripe Connect Express onboarding

- [ ] Endpoint `POST /v1/partners/onboard` (admin-trigger ou partner-self-serve):
  - Cria Stripe Connect account `type=express`
  - Retorna `onboarding_url` (Stripe-hosted)
  - Webhook `account.updated` sincroniza `stripe_connect_onboarded=true` quando KYC completo

### AC3: Branding customizado em relatórios

- [ ] `backend/reports/_branding.py`:
  - Função `get_branding_for_purchase(purchase) -> Branding`
  - Se `partner_clients` tem end_user_id = purchase.user_id: usa branding do partner
  - Substitui header/footer do PDF com logo + cor do partner
  - Footer disclaimer: "Serviço oferecido por {partner_name} em parceria com SmartLic"

### AC4: Revshare automático em pagamentos

- [ ] Em MON-REP-01 webhook `checkout.session.completed`:
  - Se purchase vinculada a partner: calcular `revshare_cents = amount_cents × revshare_pct`
  - Criar `stripe.Transfer.create(amount, destination=stripe_connect_account_id, ...)`
  - Insert em `partner_revshare_events` com `stripe_transfer_id`
- [ ] Para subscriptions (MON-SUB-01): transferência recorrente configurada via Stripe Connect (`application_fee_percent` no subscription item)

### AC5: Dashboard do partner

- [ ] `frontend/app/parceiros/dashboard/page.tsx` (auth via partner portal, não end-user):
  - Métricas: GMV do mês, revshare acumulado, clientes ativos, taxa conversão
  - Gráfico evolução GMV 12 meses
  - Tabela últimas transações
  - Botão "Dashboard Stripe Connect" (link para Stripe Express)
  - Códigos de referral (partner slug) para tracking

### AC6: Landing do programa de parceiros

- [ ] `frontend/app/parceiros/page.tsx`:
  - Proposta de valor
  - Modelos (20% revshare / 50% / flat fee custom)
  - FAQ
  - Formulário "Torne-se parceiro" → lead

### AC7: Attribution de end users a partners

- [ ] Quando usuário chega via URL `?ref={partner_slug}` ou `/parceiros/{partner_slug}`:
  - Cookie `partner_attribution` (90 dias)
  - Quando fizer signup: insere em `partner_clients`
  - Todas purchases futuras desse user têm `partner_id` no metadata

### AC8: Testes

- [ ] Unit: `test_partner_revshare.py` — cálculo correto + criação de transfer
- [ ] Integration: purchase via partner → transfer efetivado no Stripe
- [ ] E2E: partner onboarding → envio de link ref → end user compra → revshare calculado

---

## Scope

**IN:**
- Schema partners (3 tabelas)
- Stripe Connect Express onboarding
- Branding custom em relatórios PDF
- Revshare automático (one-shot + recorrente)
- Dashboards partner + landing
- Attribution via ref
- Testes

**OUT:**
- Marketplace público de parceiros — v2
- Badges/selos customizáveis no dashboard do end user — v2
- Multi-tier branding (sub-parceiros) — fora de escopo

---

## Dependências

- MON-REP-01 + MON-SUB-01 (infra de checkout e subscription)
- Stripe Connect habilitado (requer KYC da SmartLic como plataforma)

---

## Riscos

- **Stripe Connect KYC para SmartLic:** processo de dias; iniciar cedo no sprint
- **Revshare 50% pode ser inviável com custo OpenAI alto (Copilot):** ajustar revshare por produto (AI Copilot talvez 30% vs relatórios 50%)
- **Fraude do partner:** rate limit em onboarding novos usuários via ref (max 50/mês até validar padrão)
- **End user confundido com branding:** disclaimer discreto + claridade nos ToS

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `supabase/migrations/.../create_partners_tables.sql` + `.down.sql`
- `backend/services/partner_revshare.py` (novo)
- `backend/services/partner_onboarding.py` (novo)
- `backend/reports/_branding.py` (novo + integrar em todos os geradores)
- `backend/webhooks/handlers/partner_account.py` (novo)
- `backend/routes/partners.py` (novo)
- `backend/middleware/partner_attribution.py` (novo — cookie)
- `frontend/app/parceiros/page.tsx` (novo)
- `frontend/app/parceiros/dashboard/page.tsx` (novo)
- `frontend/app/parceiros/[slug]/page.tsx` (novo — landing customizada por partner)
- `backend/tests/services/test_partner_revshare.py` (novo)

---

## Definition of Done

- [ ] 2 partners em onboarding + 1 completo (KYC done)
- [ ] Test purchase via ref URL → transfer real efetivado no Stripe test mode
- [ ] Partner dashboard mostra GMV + revshare em tempo real
- [ ] Branding custom funciona em PDF gerado
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — canal white-label de alto leverage; complexidade XL justifica a prioridade P2 |
