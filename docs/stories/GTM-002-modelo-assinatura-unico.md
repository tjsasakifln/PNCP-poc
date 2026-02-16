# GTM-002: Modelo de Assinatura Único — R$ 1.999/mês

## Metadata
| Field | Value |
|-------|-------|
| **ID** | GTM-002 |
| **Priority** | P0 (GTM-blocker) |
| **Sprint** | Sprint 1 |
| **Estimate** | 16h |
| **Depends on** | TD-001 (Migration 027 — production verification) |
| **Blocks** | GTM-003, GTM-010 |
| **Absorbs** | TD-002 (Pricing Divergence), TD-018 (Plan Consolidation, parcial) |

## Filosofia

> **"Não existem 'planos de assinatura'. Existem 'níveis de compromisso em se destacar no mercado'."**

O modelo atual de 3 planos (Consultor Ágil R$297, Máquina R$597, Sala de Guerra R$1.497) gera comparação interna, dilui valor percebido e comunica "acesso" em vez de "resultado". Múltiplos níveis convidam o usuário a escolher o mais barato.

**Argumento central:** "Quem avalia constantemente oportunidades é quem vence mais licitações."

## Problema

### Estado Atual: 3 Planos com Features Diferenciadas

| Plano | Preço | Buscas/Mês | Excel | Pipeline | IA | Histórico |
|-------|-------|-----------|-------|----------|----|----|
| Consultor Ágil | R$ 297 | 30 | ❌ | ❌ | Básica (200 tokens) | 30 dias |
| Máquina | R$ 597 | 100 | ✅ | ❌ | Detalhada (2k tokens) | 180 dias |
| Sala de Guerra | R$ 1.497 | 500 | ✅ | ✅ | Prioritária (10k tokens) | 5 anos |

**Problemas identificados:**

1. **Comparação interna:** Usuário compara planos entre si, não SmartLic vs alternativa (busca manual)
2. **Anchor pricing errado:** R$ 297 ancora valor muito baixo
3. **Dilui valor:** IA "básica" vs "detalhada" vs "prioritária" confunde — o que é "IA básica"?
4. **Naming ruim:** "Máquina" e "Sala de Guerra" não comunicam valor de negócio
5. **Divergência backend/frontend:** TD-002 identificou 9.6x discrepância entre `/planos` page e billing backend
6. **Complexidade desnecessária:** 3 níveis de IA, 3 níveis de histórico, 3 níveis de quota — muito a gerenciar

## Solução: Plano Único com Billing Periods

### Nova Estrutura

| "Nível de Compromisso" | Preço | Desconto | Equivalência | Billing Period |
|------------------------|-------|----------|--------------|----------------|
| **Mensal** | R$ 1.999/mês | — | Avaliação constante | `monthly` |
| **Semestral** | R$ 1.799/mês | 10% (R$ 10.794/6 meses) | Consistência competitiva | `semiannual` |
| **Anual** | R$ 1.599/mês | 20% (R$ 19.188/ano) | Domínio do mercado | `annual` |

**Capabilities (únicas, não escalonadas):**
- **Buscas/Mês:** 1000 (suficiente para qualquer uso realista)
- **Excel:** ✅ Habilitado
- **Pipeline:** ✅ Habilitado
- **IA:** Completa (10.000 tokens — análise estratégica)
- **Histórico:** 5 anos
- **Priority:** Normal (não "low priority" vs "high priority")

**Mensagem:** "O SmartLic é um só. A única escolha é com que frequência você quer ser cobrado."

## Escopo — Backend

### Arquivos Modificados

| Arquivo | Mudança | Linhas Afetadas |
|---------|---------|----------------|
| **`backend/quota.py`** | Substituir 4 planos por 1 | L62-135 (PLAN_CAPABILITIES, PLAN_NAMES, PLAN_PRICES) |
| **`backend/quota.py`** | Novo plano `smartlic_pro` | L62-80 |
| **`backend/quota.py`** | Simplificar UPGRADE_SUGGESTIONS | L120-135 |
| **`backend/routes/billing.py`** | Aceitar `billing_period` param | Função `create_checkout_session` |
| **`backend/services/billing.py`** | Remover pro-rata customizado | Stripe já faz automaticamente |
| **`backend/routes/plans.py`** | Retornar plano único com 3 billing options | Endpoint `/plans` |
| **`backend/webhooks/stripe.py`** | Manter compatibilidade com planos legados | Handlers `checkout.session.completed`, `customer.subscription.updated` |

### Migration 028: Novo Plano no Supabase

**Arquivo:** `backend/supabase/migrations/028_single_plan_model.sql`

**Operações:**

1. Inserir novo plano `smartlic_pro`:
   ```sql
   INSERT INTO plans (id, name, price_monthly, description, active, display_order)
   VALUES (
     'smartlic_pro',
     'SmartLic Pro',
     199900, -- R$ 1.999,00 em centavos
     'Produto completo com inteligência de decisão em licitações',
     true,
     1
   );
   ```

2. Criar billing periods na tabela `plan_billing_periods` (nova tabela):
   ```sql
   CREATE TABLE plan_billing_periods (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     plan_id TEXT REFERENCES plans(id) ON DELETE CASCADE,
     billing_period TEXT NOT NULL CHECK (billing_period IN ('monthly', 'semiannual', 'annual')),
     price_cents INTEGER NOT NULL,
     discount_percent INTEGER DEFAULT 0,
     stripe_price_id TEXT UNIQUE,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );

   INSERT INTO plan_billing_periods (plan_id, billing_period, price_cents, discount_percent, stripe_price_id)
   VALUES
     ('smartlic_pro', 'monthly', 199900, 0, 'price_XXX'), -- A configurar no Stripe
     ('smartlic_pro', 'semiannual', 179900, 10, 'price_YYY'),
     ('smartlic_pro', 'annual', 159900, 20, 'price_ZZZ');
   ```

3. Manter planos legados como `active = false` para subscribers existentes:
   ```sql
   UPDATE plans
   SET active = false
   WHERE id IN ('consultor_agil', 'maquina', 'sala_guerra');
   ```

4. Adicionar feature flags unificadas:
   ```sql
   INSERT INTO plan_features (plan_id, feature_key, feature_value)
   VALUES
     ('smartlic_pro', 'max_requests_per_month', '1000'),
     ('smartlic_pro', 'allow_excel', 'true'),
     ('smartlic_pro', 'allow_pipeline', 'true'),
     ('smartlic_pro', 'max_summary_tokens', '10000'),
     ('smartlic_pro', 'max_history_days', '1825'), -- 5 anos
     ('smartlic_pro', 'priority', 'normal');
   ```

### `quota.py` — Novo Plan Capabilities

```python
PLAN_CAPABILITIES = {
    "free_trial": {
        "max_requests_per_month": 3,
        "allow_excel": True,  # GTM-003: trial tem produto completo
        "allow_pipeline": True,
        "max_summary_tokens": 10000,
        "max_history_days": 365,
        "priority": "normal",
    },
    "smartlic_pro": {
        "max_requests_per_month": 1000,
        "allow_excel": True,
        "allow_pipeline": True,
        "max_summary_tokens": 10000,
        "max_history_days": 1825,  # 5 anos
        "priority": "normal",
    },
    # Planos legados para compatibilidade
    "consultor_agil": {
        "max_requests_per_month": 30,
        "allow_excel": False,
        "allow_pipeline": False,
        "max_summary_tokens": 200,
        "max_history_days": 30,
        "priority": "low",
    },
    # ... maquina, sala_guerra mantidos para subscribers existentes
}

PLAN_NAMES = {
    "free_trial": "Trial (7 dias)",
    "smartlic_pro": "SmartLic Pro",
    # Legados
    "consultor_agil": "Consultor Ágil (legacy)",
    "maquina": "Máquina (legacy)",
    "sala_guerra": "Sala de Guerra (legacy)",
}

PLAN_PRICES = {
    "smartlic_pro": "R$ 1.999/mês",  # Mensal base
    # Billing period variants handled by Stripe Price IDs
}

UPGRADE_SUGGESTIONS = {
    "free_trial": "smartlic_pro",
    # Legados também sugerem upgrade para pro
    "consultor_agil": "smartlic_pro",
    "maquina": "smartlic_pro",
    "sala_guerra": "smartlic_pro",
}
```

### `billing.py` — Billing Period Support

**Função:** `create_checkout_session(user_id, plan_id, billing_period)`

```python
async def create_checkout_session(
    user_id: str,
    plan_id: str = "smartlic_pro",
    billing_period: str = "monthly"  # Novo param
):
    """
    Cria Stripe Checkout Session para plano único com billing period escolhido.

    billing_period: "monthly" | "semiannual" | "annual"
    """
    # Buscar Price ID correto baseado em billing_period
    price_id = await get_stripe_price_id(plan_id, billing_period)

    # Criar checkout session normalmente
    session = stripe.checkout.Session.create(
        customer_email=user_email,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/planos",
        metadata={"user_id": user_id, "plan_id": plan_id, "billing_period": billing_period}
    )

    return session
```

**Remover:** Custom pro-rata logic — Stripe faz automaticamente ao trocar planos.

### `webhooks/stripe.py` — Backward Compatibility

**Handlers afetados:**
- `checkout.session.completed`: Deve sincronizar `profiles.plan_type` para planos legados E `smartlic_pro`
- `customer.subscription.updated`: Idem
- `customer.subscription.deleted`: Downgrades para `free_trial`

**Regra de compatibilidade:**
- Se subscriber tem `consultor_agil`, `maquina`, ou `sala_guerra`: continuar funcionando normalmente, sem forçar upgrade
- UI pode mostrar banner "Migre para SmartLic Pro" mas não bloquear funcionalidade

## Escopo — Frontend

### Arquivos Modificados

| Arquivo | Mudança | Estimativa |
|---------|---------|------------|
| **`frontend/app/planos/page.tsx`** | Reescrita completa (~700 linhas) | 4h |
| **`frontend/app/pricing/page.tsx`** | Atualizar estrutura | 1h |
| **`frontend/lib/copy/valueProps.ts`** | Recalcular ROI com novo preço | 1h |
| **`frontend/lib/copy/roi.ts`** | Atualizar DEFAULT_VALUES | 0.5h |
| **`frontend/components/subscriptions/PlanToggle.tsx`** | Adaptar para 3 billing periods | 1h |
| **`frontend/app/components/UpgradeModal.tsx`** | Simplificar (plano único) | 0.5h |
| **`frontend/app/components/PlanBadge.tsx`** | Simplificar | 0.5h |

### `/planos` Page — Nova Estrutura

**Layout:**
```
Hero Section
├─ Headline: "Escolha Seu Nível de Compromisso"
├─ Sub: "O SmartLic é um só. Você decide com que frequência quer ser cobrado."

Plan Card (único, centralizado)
├─ "SmartLic Pro"
├─ Billing Toggle: [Mensal] [Semestral] [Anual]
├─ Preço dinâmico: R$ 1.999/mês (ou 1.799 ou 1.599 conforme toggle)
├─ Discount badge: "Economize 10%" (semiannual) ou "Economize 20%" (anual)
├─ Feature List (SEM comparação):
│   ├─ ✅ 1000 análises/mês
│   ├─ ✅ Excel exportável
│   ├─ ✅ Pipeline de acompanhamento
│   ├─ ✅ Inteligência de decisão completa
│   ├─ ✅ 5 anos de histórico
│   ├─ ✅ Cobertura nacional
├─ CTA: "Começar Agora"

ROI Section (atualizado)
├─ "Uma única licitação ganha pode pagar um ano inteiro"
├─ Calculadora removida ou ultra-simplificada (não é sobre economizar, é sobre ganhar)

FAQ
├─ "Posso cancelar a qualquer momento?" → Sim
├─ "Existe contrato de fidelidade?" → Não (mesmo no anual)
├─ "O que acontece se eu cancelar?" → Acesso até fim do período pago
```

**Copy Rules:**
- NUNCA usar "plano", "tier", "pacote" → Usar "nível de compromisso"
- NUNCA usar "assinatura" → Usar "acesso mensal/semestral/anual"
- NUNCA comparar features (não há o que comparar)
- SEMPRE focar em resultado ("ganhar mais licitações") não em acesso

### ROI Calculator — Simplificação

**Atual:** Calculadora complexa com inputs de horas, salário, licitações, etc.

**Novo:** Mensagem âncora simples sem interatividade:
```
"Licitação média no seu setor: R$ 150.000
SmartLic Pro anual: R$ 19.188
ROI de uma única licitação ganha: 7.8x"
```

Se manter calculadora: remover foco em "tempo economizado", focar em "quantas licitações a mais você pode avaliar/ganhar".

## Acceptance Criteria

### Backend

- [x] **AC1: Backend aceita `plan_id=smartlic_pro` com `billing_period` em `monthly|semiannual|annual`**
  - Endpoint `/billing/create-checkout-session` aceita param `billing_period`
  - Retorna Stripe Checkout URL correto para o Price ID correspondente
  - **Critério de validação:** `POST /billing/create-checkout-session {"plan_id": "smartlic_pro", "billing_period": "annual"}` retorna session com price_id correto

- [ ] **AC2: Stripe tem Product "SmartLic Pro" com 3 Prices configurados** *(Stripe dashboard — manual config needed)*
  - Product ID: `prod_smartlic_pro`
  - Price IDs: `price_monthly_1999`, `price_semiannual_1799`, `price_annual_1599`
  - Cada Price tem `recurring.interval` correto (month, month*6, year)
  - **Critério de validação:** `stripe products list` e `stripe prices list` mostram 1 produto com 3 prices

- [x] **AC3: Migration 029 cria plano e billing periods no Supabase**
  - Tabela `plans` tem row `smartlic_pro`
  - Tabela `plan_billing_periods` tem 3 rows (monthly, semiannual, annual)
  - Tabela `plan_features` tem 6 features para `smartlic_pro`
  - **Critério de validação:** `SELECT * FROM plans WHERE id = 'smartlic_pro'` retorna dados corretos

- [x] **AC4: Planos legados marcados como inativos mas funcionais**
  - `UPDATE plans SET active = false WHERE id IN ('consultor_agil', 'maquina', 'sala_guerra')` executado
  - Subscribers existentes com planos legados continuam tendo acesso conforme capabilities
  - **Critério de validação:** Usuário com `plan_type='maquina'` consegue fazer buscas com quotas corretas

- [x] **AC5: `quota.py` tem capabilities corretas para `smartlic_pro`**
  - `PLAN_CAPABILITIES["smartlic_pro"]["max_requests_per_month"] == 1000`
  - `PLAN_CAPABILITIES["smartlic_pro"]["allow_excel"] == True`
  - `PLAN_CAPABILITIES["smartlic_pro"]["max_summary_tokens"] == 10000`
  - **Critério de validação:** `check_quota(user_id)` para user com smartlic_pro retorna capabilities corretas

- [x] **AC6: Webhooks sincronizam `profiles.plan_type` corretamente**
  - `checkout.session.completed`: Atualiza `plan_type` para `smartlic_pro`
  - `customer.subscription.updated`: Sincroniza mudanças de plano
  - `customer.subscription.deleted`: Downgrade para `free_trial`
  - **Critério de validação:** Completar checkout no Stripe → webhook atualiza `profiles.plan_type` em <5s

- [x] **AC7: Pro-rata removido (Stripe faz automaticamente)**
  - Remover custom pro-rata logic de `services/billing.py`
  - Stripe Price configurado com `proration_behavior: 'create_prorations'`
  - **Critério de validação:** Trocar de monthly para annual no meio do ciclo → Stripe aplica crédito automaticamente

### Frontend

- [x] **AC8: `/planos` exibe plano único com 3 "níveis de compromisso"**
  - Layout: 1 card centralizado (não 3 cards lado a lado)
  - Toggle: Mensal / Semestral / Anual (não planos diferentes)
  - **Critério de validação:** Page renderiza 1 card, toggle funciona, preço atualiza dinamicamente

- [x] **AC9: Copy nunca usa "plano", "assinatura" ou "tier"**
  - Grep de "plano", "assinatura", "tier", "pacote" em `planos/page.tsx` retorna zero (exceto comments técnicos)
  - Usar: "nível de compromisso", "acesso mensal/semestral/anual", "produto"
  - **Critério de validação:** Regex `/plano|assinatura|tier|pacote/gi` em copy visível retorna zero

- [x] **AC10: Preços corretos com discount badges**
  - Mensal: R$ 1.999/mês (sem badge)
  - Semestral: R$ 1.799/mês com badge "Economize 10%"
  - Anual: R$ 1.599/mês com badge "Economize 20%"
  - **Critério de validação:** Toggle para Anual → preço muda para R$ 1.599 e badge "Economize 20%" aparece

- [x] **AC11: ROI calculator atualizado com novo preço**
  - `lib/copy/roi.ts`: `DEFAULT_VALUES.plan_price = 1999` (mensal base)
  - Mensagem âncora: "Uma única licitação ganha pode pagar um ano inteiro"
  - Se calculadora interativa removida: substituir por mensagem estática com ROI example
  - **Critério de validação:** ROI section mostra R$ 1.999 (ou 19.188 anual) corretamente

- [x] **AC12: Subscribers existentes continuam funcionando (backward compatible)**
  - Usuários com `consultor_agil`, `maquina`, `sala_guerra` veem suas features funcionando
  - UI pode mostrar banner sugerindo upgrade para `smartlic_pro` (não obrigatório nesta story)
  - **Critério de validação:** Login com usuário `maquina` → acesso funciona, quotas aplicadas corretamente

- [x] **AC13: Zero menção a "busca" na page de planos**
  - Banned: "busca", "buscar", "pesquisa"
  - Preferred: "análise", "inteligência", "avaliação de oportunidades", "decisão"
  - **Critério de validação:** Grep de "busca", "buscar", "pesquisa" em `planos/page.tsx` retorna zero

- [x] **AC14: Feature list SEM comparação (não há tiers)**
  - Lista única de features (não "basic vs pro vs premium")
  - Todas com ✅ (não "✅ vs ❌")
  - **Critério de validação:** Página não contém tabela comparativa ou colunas de features

## Definition of Done

- [ ] Todos os 14 Acceptance Criteria passam (13/14 code-complete, AC2 = Stripe dashboard config)
- [x] Migration 029 criada (028 já existia)
- [ ] Stripe Product + 3 Prices criados e testados (sandbox primeiro, depois production)
- [x] Backend testado: criar checkout para cada billing period, webhook sync
- [x] Frontend testado: toggle funciona, checkout flow completo (sandbox Stripe)
- [x] Backward compatibility verificada: usuário com plano legado não quebra
- [ ] Documentação atualizada: `docs/billing/plans-model.md` (se existir)
- [ ] Merged to main, deployed to production
- [ ] Monitoring: verificar por 48h que novos signups usam `smartlic_pro` corretamente

## File List

### Backend Modified
- `backend/quota.py` — PLAN_CAPABILITIES, PLAN_NAMES, PLAN_PRICES, UPGRADE_SUGGESTIONS for smartlic_pro
- `backend/services/billing.py` — removed custom pro-rata, simplified billing period support
- `backend/routes/subscriptions.py` — simplified UpdateBillingPeriodResponse (no deferred/prorated_credit)
- `backend/webhooks/stripe.py` — semiannual detection (interval=month, interval_count=6)

### Backend New
- `backend/supabase/migrations/029_single_plan_model.sql`

### Backend Tests Modified
- `backend/tests/test_plan_capabilities.py` — smartlic_pro capabilities + legacy "(legacy)" suffix
- `backend/tests/test_routes_subscriptions.py` — rewritten for simplified API + semiannual
- `backend/tests/test_billing_period_update.py` — rewritten without pro-rata/deferred
- `backend/tests/test_quota.py` — updated plan name assertions

### Backend Tests Deleted
- `backend/tests/test_prorata_edge_cases.py` — pro-rata removed entirely

### Frontend Modified
- `frontend/app/planos/page.tsx` — rewritten: single card, PlanToggle, 3 billing periods
- `frontend/app/pricing/page.tsx` — rewritten: single SmartLic Pro at R$1,999
- `frontend/app/buscar/page.tsx` — removed preSelectedPlan state
- `frontend/app/buscar/components/SearchResults.tsx` — smartlic_pro upgrade reference
- `frontend/app/buscar/components/SearchForm.tsx` — smartlic_pro upgrade reference
- `frontend/app/planos/obrigado/page.tsx` — added smartlic_pro entry
- `frontend/lib/copy/valueProps.ts` — updated for single plan model
- `frontend/lib/copy/roi.ts` — updated DEFAULT_VALUES, getRecommendedPlanId
- `frontend/components/subscriptions/PlanToggle.tsx` — 3-option toggle (monthly/semiannual/annual)
- `frontend/app/components/UpgradeModal.tsx` — single plan with PlanToggle

### Frontend Tests Modified
- `frontend/__tests__/lib/roi.test.ts` — updated for smartlic_pro + R$1,999
- `frontend/__tests__/components/subscriptions/PlanToggle.test.tsx` — rewritten for 3-option toggle
- `frontend/__tests__/UpgradeModal.test.tsx` — rewritten for single plan
- `frontend/__tests__/pages/PlanosPage.test.tsx` — rewritten for single plan card

## Notes

- Esta story absorve TD-002 (Pricing Divergence) e parcial de TD-018 (Plan Consolidation)
- Depende de TD-001 completar primeiro (Migration 027 production verification) para garantir database estável
- Bloqueia GTM-003 (redesign trial) e GTM-010 (fluxo conversão) pois ambos dependem da estrutura de plano único
- **Estimativa de 16h:** 6h backend (migration + billing + webhooks) + 6h frontend (planos page rewrite) + 2h Stripe config + 2h testing
- **Stripe config manual:** Criar Product + Prices no dashboard Stripe (ou via CLI) — não automatizado em migration
- **Rollback plan:** Se migration falhar, planos legados continuam funcionando (migration é aditiva, não destrutiva)
