# STORY-171: Annual Subscription Toggle with Premium Benefits

**Epic:** Monetization & Subscription
**Priority:** High
**Points:** 13 SP (Updated after Architect + PO Review)
**Status:** 🔍 Ready for Implementation
**Created:** 2026-02-07
**Updated:** 2026-02-07 (Post-Review)
**Owner:** @pm (Morgan)
**Reviewed By:** @architect (Aria), @po (Sarah)

---

## 📚 Review Documents

- **Architect Review:** `docs/stories/STORY-171-architect-review.md` (✅ Approved with 5 critical changes)
- **PO Review:** `docs/stories/STORY-171-po-review.md` (✅ Approved with 7 adjustments)

---

## User Story

**Como** administrador de empresa,
**Quero** poder escolher entre plano mensal ou anual na tela de assinatura,
**Para que** eu possa obter descontos significativos e benefícios exclusivos ao comprometer-me anualmente.

---

## Contexto

Atualmente o sistema oferece apenas planos mensais. Para aumentar receita recorrente (ARR), melhorar cash flow e reduzir churn, precisamos:

1. **Toggle UI** para alternar entre visualização mensal/anual
2. **Benefícios exclusivos** para assinantes anuais (early access, busca proativa, análise IA)
3. **Precificação competitiva** (anual = 9.6x mensal, economizando 20% = ~2.4 meses grátis)
4. **Feature flags robustos** com cache Redis para performance
5. **Rollout seguro** com A/B testing e phased launch

### Benefícios Plano Anual (Todos os Planos)

| Benefício | Descrição | Disponibilidade |
|-----------|-----------|-----------------|
| ✨ **Early Access** | Recebe novas features 2-4 semanas antes | ✅ Imediato |
| 🎯 **Busca Proativa** | Sistema busca automaticamente oportunidades do setor | 🚀 Março 2026 (STORY-172) |
| 💰 **Desconto 20%** | Paga 9.6 meses em vez de 12 (economiza R$ 713 - R$ 3,594 dependendo do plano) | ✅ Imediato |

### Benefícios Exclusivos "Sala de Guerra" (Apenas Plano Top)

| Benefício | Descrição | Disponibilidade |
|-----------|-----------|-----------------|
| 🤖 **Análise IA de Editais** | GPT-4 analisa editais e gera relatórios executivos | 🚀 Abril 2026 (STORY-173) |
| 📊 **Dashboard Executivo** | Gráficos de tendências, heatmaps, análise de concorrência | 🔮 Backlog (STORY-174) |
| 🔔 **Alertas Multi-Canal** | WhatsApp, Telegram, Email (não só in-app) | 🔮 Backlog (STORY-175) |

### Pricing (Atualizado - PO Approval)

| Plano | Mensal | Anual (20% off) | Economia Anual |
|-------|--------|-----------------|----------------|
| **Consultor Ágil** | R$ 297 | R$ 2,851 (R$ 237/mês) | R$ 713 |
| **Máquina** | R$ 597 | R$ 5,731 (R$ 478/mês) | R$ 1,433 |
| **Sala de Guerra** | R$ 1,497 | R$ 14,362 (R$ 1,197/mês) | R$ 3,594 |

**Fórmula:** `Anual = Mensal × 12 × 0.80` (ou `Mensal × 9.6`)

---

## Acceptance Criteria

### AC1: Toggle UI - Seleção Mensal/Anual
- [ ] Componente `PlanToggle` criado em `components/subscriptions/PlanToggle.tsx`
- [ ] Estados: "Mensal" (default) e "Anual"
- [ ] Visual claro com indicador de economia: "💰 Economize 20% pagando anual"
- [ ] Animação suave ao alternar (transition CSS 300ms)
- [ ] Acessível via teclado (Space/Enter para toggle)
- [ ] ARIA labels: `aria-label="Alternar entre plano mensal e anual"`
- [ ] Responsive (mobile + desktop)

**Design Reference:** Seguir pattern de toggle do Stripe Pricing (toggle horizontal com slider)

---

### AC2: Cálculo de Preços Dinâmico (UPDATED - 20% Discount)
- [ ] Quando toggle = "Anual", preços exibidos = `preço_mensal × 9.6`
- [ ] Badge "💰 Economize 20%" visível apenas em modo Anual
- [ ] Preços formatados em BRL: `R$ 2.851,00` (separador de milhar)
- [ ] Tooltip explicando economia:
  ```
  Plano Anual: R$ 2.851/ano (R$ 237/mês)
  Plano Mensal: R$ 297/mês × 12 = R$ 3.564/ano
  Você economiza: R$ 713 por ano!
  ```
- [ ] Cálculo em tempo real (sem lag perceptível)

---

### AC3: Exibição de Benefícios por Plano
- [ ] Seção "Benefícios Anuais" aparece apenas quando toggle = "Anual"
- [ ] Lista de benefícios com badges de status:
  - ✅ **Ativo** (early access, desconto)
  - 🚀 **Em breve** (busca proativa, análise IA) + tooltip com data prevista
  - 🔮 **Futuro** (dashboard, alertas multi-canal)
- [ ] Ícones consistentes com design system
- [ ] Texto claro e conciso (max 1 linha por benefício)
- [ ] Benefícios de Sala de Guerra destacados visualmente

---

### AC4: Backend - Schema de Planos (CRITICAL - Architect Change #1)

**⚠️ CORRECTED FROM ORIGINAL:** Use `user_subscriptions`, NOT `subscriptions`

- [ ] Migration `006_add_billing_period.sql` criada:
  ```sql
  -- Add billing_period column (NOT NULL)
  ALTER TABLE public.user_subscriptions
    ADD COLUMN billing_period VARCHAR(10) NOT NULL DEFAULT 'monthly'
      CHECK (billing_period IN ('monthly', 'annual'));

  -- Add annual_benefits column
  ALTER TABLE public.user_subscriptions
    ADD COLUMN annual_benefits JSONB NOT NULL DEFAULT '{}'::jsonb;

  -- CRITICAL: Backfill existing annual plans
  UPDATE public.user_subscriptions
  SET billing_period = 'annual'
  WHERE plan_id = 'annual' AND is_active = true;

  -- Performance index
  CREATE INDEX idx_user_subscriptions_billing
    ON public.user_subscriptions(user_id, billing_period, is_active)
    WHERE is_active = true;
  ```

- [ ] Rollback script `006_rollback.sql`:
  ```sql
  DROP INDEX IF EXISTS idx_user_subscriptions_billing;
  ALTER TABLE public.user_subscriptions DROP COLUMN annual_benefits;
  ALTER TABLE public.user_subscriptions DROP COLUMN billing_period;
  ```

- [ ] Validation query after migration:
  ```sql
  -- Should return 0
  SELECT COUNT(*) FROM user_subscriptions WHERE billing_period IS NULL;

  -- Should show backfilled annual plans
  SELECT user_id, plan_id, billing_period
  FROM user_subscriptions
  WHERE plan_id = 'annual';
  ```

- [ ] Test on staging FIRST with real data clone
- [ ] Verify migration executes in < 5 seconds (even with 100k+ rows)

---

### AC5: Backend - Endpoint de Upgrade/Downgrade (EXPANDED - Architect Change #4)

**Endpoint:** `POST /api/subscriptions/update-billing-period`

**Request:**
```typescript
{
  billing_period: 'monthly' | 'annual',
  timezone?: string  // Optional, defaults to 'America/Sao_Paulo'
}
```

**Implementation Requirements:**
- [ ] Validação: apenas assinantes ativos podem alterar
- [ ] **Pro-Rata Calculation** com edge cases:
  - [ ] Se upgrade E `days_until_renewal < 7` → Defer para próximo ciclo
  - [ ] Timezone-aware calculation (user's TZ, not server UTC)
  - [ ] Arredondamento: sempre para baixo (favorece usuário)
  - [ ] Daily rate calculation:
    ```python
    if current_billing == 'monthly':
        daily_rate = price_brl / 30
    else:  # annual
        daily_rate = (price_brl * 9.6) / 365
    ```
- [ ] Atualiza Stripe subscription (`stripe.Subscription.modify()`)
- [ ] Atualiza DB local (`billing_period`, `updated_at`)
- [ ] **Cache invalidation:** `redis.delete(f"features:{user_id}")`
- [ ] Retorna confirmação com próximo `billing_date`

**Response (Success):**
```typescript
{
  success: true,
  subscription: {
    id: "sub_123",
    billing_period: "annual",
    next_billing_date: "2027-02-07T00:00:00Z",
    amount: 2851.00,
    prorated_credit: 50.00,  // Credit applied from unused monthly time
    deferred: false  // true if upgrade deferred to next cycle
  },
  enabled_features: ["early_access", "proactive_search"],
  message: "Plano atualizado para Anual! Novos benefícios ativados."
}
```

**Response (Deferred):**
```typescript
{
  success: true,
  subscription: { ... },
  deferred: true,
  message: "Upgrade será aplicado em 07/02/2027 (próximo ciclo de cobrança)"
}
```

**Response (Error):**
```typescript
{
  success: false,
  error: "No active subscription found",
  code: "NO_ACTIVE_SUBSCRIPTION"
}
```

---

### AC6: Feature Flags por Tipo de Plano (CRITICAL - Architect Changes #2 + #3)

#### Part A: Database Schema (Architect Change #2)

**⚠️ CORRECTED:** Use `plan_id` (FK to plans.id), NOT free-text `plan_name`

- [ ] Migration `007_create_plan_features.sql`:
  ```sql
  CREATE TABLE public.plan_features (
    id SERIAL PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES public.plans(id) ON DELETE CASCADE,
    billing_period VARCHAR(10) NOT NULL CHECK (billing_period IN ('monthly', 'annual')),
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb,  -- For future config (e.g., AI model version)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(plan_id, billing_period, feature_key)
  );

  -- Performance index for lookups
  CREATE INDEX idx_plan_features_lookup
    ON public.plan_features(plan_id, billing_period, enabled)
    WHERE enabled = true;

  -- Auto-update timestamp trigger
  CREATE TRIGGER plan_features_updated_at
    BEFORE UPDATE ON public.plan_features
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

  -- RLS Policy (public catalog)
  ALTER TABLE public.plan_features ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "plan_features_select_all" ON public.plan_features
    FOR SELECT USING (true);
  ```

- [ ] Seed data (use actual plan IDs from `plans` table):
  ```sql
  INSERT INTO public.plan_features (plan_id, billing_period, feature_key, enabled) VALUES
    -- Consultor Ágil (annual only)
    ('consultor_agil', 'annual', 'early_access', true),
    ('consultor_agil', 'annual', 'proactive_search', true),

    -- Máquina (annual only)
    ('maquina', 'annual', 'early_access', true),
    ('maquina', 'annual', 'proactive_search', true),

    -- Sala de Guerra (annual only)
    ('sala_guerra', 'annual', 'early_access', true),
    ('sala_guerra', 'annual', 'proactive_search', true),
    ('sala_guerra', 'annual', 'ai_edital_analysis', true);
  ```

#### Part B: Redis Cache Implementation (Architect Change #3)

**Backend:** `GET /api/features/:userId` (or `/api/features/me`)

- [ ] **Redis caching** with 5-minute TTL:
  ```python
  import redis
  import json

  redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
  CACHE_TTL = 300  # 5 minutes

  @router.get("/api/features/me")
  async def get_user_features(current_user = Depends(get_current_user)):
      user_id = str(current_user.id)

      # Try cache first
      cache_key = f"features:{user_id}"
      cached = redis_client.get(cache_key)
      if cached:
          return json.loads(cached)

      # Cache miss - query DB
      subscription = db.query(UserSubscription).filter(
          UserSubscription.user_id == user_id,
          UserSubscription.is_active == True
      ).first()

      if not subscription:
          return {"features": [], "plan_id": None, "billing_period": None}

      # JOIN with plan_features
      features = db.query(PlanFeature).filter(
          PlanFeature.plan_id == subscription.plan_id,
          PlanFeature.billing_period == subscription.billing_period,
          PlanFeature.enabled == True
      ).all()

      result = {
          "features": [f.feature_key for f in features],
          "plan_id": subscription.plan_id,
          "billing_period": subscription.billing_period,
          "cached_at": datetime.utcnow().isoformat()
      }

      # Cache for 5 minutes
      redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))

      return result
  ```

- [ ] **Cache invalidation** on billing_period update:
  ```python
  # In POST /api/subscriptions/update-billing-period
  redis_client.delete(f"features:{user_id}")
  ```

- [ ] **Cache invalidation** on Stripe webhook:
  ```python
  # In webhook handler after updating DB
  redis_client.delete(f"features:{user_sub.user_id}")
  ```

**Frontend:** React Hook with SWR

- [ ] Create `hooks/useFeatureFlags.ts`:
  ```typescript
  import useSWR from 'swr';

  const fetcher = (url: string) => fetch(url).then(r => r.json());

  export function useFeatureFlags() {
    const { data, error, mutate } = useSWR(
      '/api/features/me',
      fetcher,
      {
        revalidateOnFocus: false,
        revalidateOnReconnect: false,
        dedupingInterval: 300000,  // 5 minutes (matches backend TTL)
      }
    );

    const hasFeature = (key: string) => {
      return data?.features?.includes(key) || false;
    };

    return {
      features: data?.features || [],
      planId: data?.plan_id,
      billingPeriod: data?.billing_period,
      isLoading: !data && !error,
      isError: error,
      hasFeature,
      refresh: mutate,  // Call after billing update for optimistic UI
    };
  }
  ```

- [ ] **Optimistic UI** on upgrade:
  ```typescript
  const { features, refresh } = useFeatureFlags();

  const handleUpgrade = async () => {
    // Optimistically show new features
    mutate({ features: ['early_access', 'proactive_search'] }, false);

    const result = await fetch('/api/subscriptions/update-billing-period', {
      method: 'POST',
      body: JSON.stringify({ billing_period: 'annual' }),
    });

    // Revalidate to get server truth
    refresh();
  };
  ```

---

### AC7: Testes Unitários - Frontend
- [ ] `PlanToggle.test.tsx`: Toggle alterna estados corretamente
- [ ] `PlanCard.test.tsx`: Preços calculados corretamente (mensal vs anual, 20% discount)
- [ ] `AnnualBenefits.test.tsx`: Benefícios anuais aparecem apenas quando toggle = "Anual"
- [ ] `TrustSignals.test.tsx`: Social proof, guarantees, urgency badges render
- [ ] `useFeatureFlags.test.ts`: Hook retorna features corretas, cache funciona
- [ ] Snapshot tests para cada estado (mensal, anual, loading)

---

### AC8: Testes Unitários - Backend
- [ ] `test_billing_period_update.py`: Atualização bem-sucedida
- [ ] `test_prorata_calculation.py`: Cálculo proporcional correto (edge cases: last day, timezone)
- [ ] `test_prorata_defer_logic.py`: Upgrade adiado se < 7 dias para renewal
- [ ] `test_feature_flags.py`: Features habilitadas/desabilitadas corretamente
- [ ] `test_feature_cache.py`: Redis cache hit/miss, invalidation
- [ ] `test_stripe_webhook.py`: Webhook atualiza billing_period, idempotency funciona
- [ ] `test_webhook_signature.py`: Rejeita webhooks sem assinatura válida

---

### AC9: Testes E2E
- [ ] Usuário alterna toggle → Preços atualizam (9.6x mensal)
- [ ] Usuário seleciona plano anual → Checkout com valor correto
- [ ] Assinante mensal faz upgrade para anual → Pro-rata aplicado
- [ ] Assinante mensal faz upgrade 5 dias antes de renewal → Upgrade adiado (defer logic)
- [ ] Assinante anual faz downgrade para mensal → Mantém benefícios até fim do ciclo
- [ ] Feature "Análise IA" aparece apenas para "Sala de Guerra" anual
- [ ] Cache invalidation: Upgrade → Features atualizadas imediatamente

---

### AC10: Documentação
- [ ] `docs/features/annual-subscription.md` criado com:
  - Arquitetura da feature (diagrama de fluxo)
  - Fluxo de upgrade/downgrade (sequence diagram)
  - Cálculo de pro-rata com exemplos
  - Mapeamento de feature flags (tabela completa)
  - Redis cache strategy
  - Troubleshooting guide
- [ ] Exemplos de API requests/responses (Postman collection)
- [ ] Downgrade policy (Terms of Service update)

---

### AC11: Stripe Integration (CRITICAL - Architect Change #5)

#### Part A: Preços Anuais no Stripe
- [ ] Criar 3 preços anuais no Stripe Dashboard:
  - Consultor Ágil: R$ 2.851,00/ano (R$ 285.100 centavos)
  - Máquina: R$ 5.731,00/ano (R$ 573.100 centavos)
  - Sala de Guerra: R$ 14.362,00/ano (R$ 1.436.200 centavos)
- [ ] Copiar Price IDs para `.env`:
  ```
  STRIPE_PRICE_CONSULTOR_AGIL_MENSAL=price_xxx
  STRIPE_PRICE_CONSULTOR_AGIL_ANUAL=price_yyy
  STRIPE_PRICE_MAQUINA_MENSAL=price_xxx
  STRIPE_PRICE_MAQUINA_ANUAL=price_yyy
  STRIPE_PRICE_SALA_GUERRA_MENSAL=price_xxx
  STRIPE_PRICE_SALA_GUERRA_ANUAL=price_yyy
  ```

#### Part B: Webhook Handler (IDEMPOTENT - Architect Change #5)

**⚠️ CRITICAL:** Implement idempotency to prevent duplicate processing

- [ ] Create `stripe_webhook_events` table:
  ```sql
  CREATE TABLE public.stripe_webhook_events (
    id VARCHAR(255) PRIMARY KEY,  -- Stripe event ID (evt_xxx)
    type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB,
    INDEX idx_webhook_events_type (type, processed_at)
  );
  ```

- [ ] Webhook handler `backend/webhooks/stripe.py`:
  ```python
  import stripe
  from fastapi import APIRouter, Request, HTTPException
  from sqlalchemy.dialects.postgresql import insert

  @router.post("/webhooks/stripe")
  async def stripe_webhook(request: Request):
      payload = await request.body()
      sig_header = request.headers.get('stripe-signature')

      # CRITICAL: Verify signature (prevents fake webhooks)
      try:
          event = stripe.Webhook.construct_event(
              payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
          )
      except ValueError:
          raise HTTPException(400, "Invalid payload")
      except stripe.error.SignatureVerificationError:
          raise HTTPException(400, "Invalid signature")

      # Idempotency check
      existing = db.query(StripeWebhookEvent).filter(
          StripeWebhookEvent.id == event.id
      ).first()

      if existing:
          return {"status": "already_processed"}

      # Process event
      if event.type == 'customer.subscription.updated':
          subscription_data = event.data.object

          # Determine billing_period from Stripe interval
          billing_period = 'annual' if subscription_data.plan.interval == 'year' else 'monthly'

          # Atomic upsert (prevents race conditions)
          stmt = insert(UserSubscription).values(
              stripe_subscription_id=subscription_data.id,
              billing_period=billing_period,
              updated_at=datetime.utcnow()
          ).on_conflict_do_update(
              index_elements=['stripe_subscription_id'],
              set_={'billing_period': billing_period, 'updated_at': datetime.utcnow()}
          )

          db.execute(stmt)

          # Invalidate cache
          user_sub = db.query(UserSubscription).filter(
              UserSubscription.stripe_subscription_id == subscription_data.id
          ).first()
          redis_client.delete(f"features:{user_sub.user_id}")

      # Mark as processed (prevents duplicate processing)
      db.add(StripeWebhookEvent(
          id=event.id,
          type=event.type,
          payload=event.data.object
      ))
      db.commit()

      return {"status": "success"}
  ```

- [ ] Test with Stripe CLI:
  ```bash
  stripe listen --forward-to localhost:8000/webhooks/stripe
  stripe trigger customer.subscription.updated
  ```

- [ ] Verify:
  - [ ] Signature validation rejects unsigned requests
  - [ ] Duplicate webhooks return "already_processed"
  - [ ] billing_period updated in DB
  - [ ] Cache invalidated (Redis key deleted)

---

### AC12: UX/UI Polish
- [ ] Loading state durante atualização de plano (skeleton + spinner)
- [ ] Toast de confirmação: "✅ Plano atualizado para Anual! Novos benefícios ativados."
- [ ] Toast de erro: "❌ Não foi possível atualizar. Tente novamente ou contate o suporte."
- [ ] Modal de confirmação antes de downgrade:
  ```
  ⚠️ Tem certeza que deseja fazer downgrade?

  Você perderá acesso aos seguintes benefícios:
  • Early access a novas features
  • Busca proativa de oportunidades
  • Análise IA de editais (Sala de Guerra)

  Seus benefícios anuais serão mantidos até 07/02/2027.

  [Cancelar]  [Confirmar Downgrade]
  ```
- [ ] Design consistente com Figma/design system (colors, spacing, typography)

---

### AC13: Tracking & Analytics
- [ ] Evento `toggle_billing_period` (Google Analytics/Mixpanel):
  ```javascript
  trackEvent('toggle_billing_period', {
    from: 'monthly',
    to: 'annual',
    plan_name: 'Consultor Ágil',
    user_id: 'user_123'
  });
  ```
- [ ] Evento `subscription_upgraded` quando mensal → anual
- [ ] Evento `subscription_downgraded` quando anual → mensal
- [ ] Dashboard `/admin/annual-metrics` mostra:
  - % de assinantes anuais vs mensais (por plano)
  - ARR growth (última semana, mês, trimestre)
  - Cash flow collected (upfront payments)
  - Churn rate (annual vs monthly)
  - Conversion rate (new signups choosing annual)

---

### AC14: Rollout Seguro (A/B Test)
- [ ] Feature flag `ENABLE_ANNUAL_PLANS` (default: false)
- [ ] Habilitar primeiro em staging (internal testing)
- [ ] **A/B test (Week 2-3):**
  - Segment A (Control): 45% → See monthly only
  - Segment B (Test): 45% → See monthly + annual toggle
  - Segment C (Holdout): 10% → No changes (statistical significance)
- [ ] Rollback plan documentado:
  ```bash
  # Emergency rollback
  ENABLE_ANNUAL_PLANS=false  # .env variable
  # OR
  redis-cli SET feature_flag:annual_plans "false"
  ```
- [ ] Monitoring:
  - Error rate on `/api/subscriptions/update-billing-period`
  - Stripe failed charges (alert if > 10 in 1 hour)
  - User complaints (social media sentiment)

---

### AC15: Trust Signals & Urgency (NEW - PO Change #3)

**Component:** `components/subscriptions/TrustSignals.tsx`

- [ ] **Social Proof Badge:**
  ```tsx
  <Badge variant="success">
    ⭐ Escolha de {annualConversionRate}% dos nossos clientes
  </Badge>
  ```
  - Dynamic `annualConversionRate` from DB: `(annual_signups / total_signups) × 100`

- [ ] **Launch Offer (Limited Time):**
  ```tsx
  {launchOfferActive && (
    <Alert variant="info">
      🎁 Primeiros 100 assinantes ganham +1 mês grátis!
      <br />
      Restam {100 - currentAnnualSignups} vagas
    </Alert>
  )}
  ```
  - Track `currentAnnualSignups` in real-time (Redis counter)
  - Expire after 100 conversions OR 30 days (whichever first)

- [ ] **Guarantees Section:**
  ```tsx
  <div className="guarantees">
    <p>💳 Garantia de 30 dias — cancele e receba reembolso integral</p>
    <p>🔒 Seus dados protegidos com criptografia de nível bancário</p>
    <p>📞 Suporte prioritário 24/7 para assinantes anuais</p>
  </div>
  ```

- [ ] **Early Adopter Discount Code:**
  - Code: `EARLYBIRD`
  - Discount: Additional 10% off (on top of 20% annual discount)
  - Total discount: 28% off (R$ 2,851 → R$ 2,053 for Consultor Ágil)
  - Valid: First 50 uses OR until STORY-172 ships
  - Stripe Coupon ID: `EARLYBIRD_2026`

- [ ] Analytics tracking:
  - Track clicks on "Garantia de 30 dias" → Measure trust concern
  - Track `EARLYBIRD` coupon usage → Conversion attribution

---

### AC16: Coming Soon Badges (NEW - PO Change #4)

**Purpose:** Set expectations for features not yet implemented (Busca Proativa, Análise IA)

**Component:** `components/subscriptions/FeatureBadge.tsx`

- [ ] Badge types:
  ```typescript
  type FeatureStatus = 'active' | 'coming_soon' | 'future';

  interface FeatureBadgeProps {
    status: FeatureStatus;
    launchDate?: string;  // "Março 2026"
  }
  ```

- [ ] Badge UI:
  ```tsx
  {status === 'active' && <Badge variant="success">✅ Ativo</Badge>}
  {status === 'coming_soon' && (
    <Badge variant="warning">
      🚀 Em breve
      {launchDate && (
        <Tooltip>
          Previsão: {launchDate}
        </Tooltip>
      )}
    </Badge>
  )}
  {status === 'future' && <Badge variant="secondary">🔮 Futuro</Badge>}
  ```

- [ ] Feature mapping:
  ```typescript
  const featureStatuses = {
    early_access: { status: 'active' },
    proactive_search: { status: 'coming_soon', launchDate: 'Março 2026' },
    ai_edital_analysis: { status: 'coming_soon', launchDate: 'Abril 2026' },
    dashboard_executivo: { status: 'future' },
    alertas_multi_canal: { status: 'future' },
  };
  ```

- [ ] **Launch Notification System:**
  - When feature goes live (e.g., STORY-172 deployed):
    1. Update `featureStatuses.proactive_search.status = 'active'`
    2. Send in-app notification: "🎉 Busca Proativa está ativa!"
    3. Send email to all annual subscribers
    4. Track event: `feature_launched`

- [ ] Early adopter messaging:
  ```tsx
  <p>
    Como early adopter, você será notificado por email assim que
    essas features forem lançadas. Obrigado por acreditar em nós! 🚀
  </p>
  ```

---

### AC17: Cancelamento e Downgrade Flow (UPDATED - CDC Compliant)

**Policy:** 7-day refund window + no-refund downgrade

**Overview:**
- **0-7 dias:** Full refund (100%) - CDC right of withdrawal
- **8+ dias:** No refund, keep benefits until end of period

---

#### Tier 1: Cancelamento Total (0-7 dias) - Full Refund

- [ ] **Eligibility Check:**
  ```python
  def is_within_withdrawal_period(subscription):
      """Check if subscription is within 7-day CDC withdrawal period"""
      subscription_age = (datetime.utcnow() - subscription.created_at).days
      return subscription_age <= 7
  ```

- [ ] **Cancelamento Modal (0-7 days):**
  ```tsx
  <Modal title="Cancelamento com Reembolso Integral" variant="info">
    <Alert variant="success">
      ✅ Você está dentro do período de garantia (7 dias)
    </Alert>

    <p>Ao confirmar o cancelamento:</p>
    <ul>
      <li>💰 Você receberá reembolso integral de R$ {subscription.amount_paid}</li>
      <li>⏱️ Processamento em 5-10 dias úteis</li>
      <li>🚫 Seus benefícios anuais serão desativados imediatamente</li>
    </ul>

    <Checkbox required>
      Entendo que esta ação é irreversível e perderei acesso imediato
      aos benefícios anuais.
    </Checkbox>

    <ButtonGroup>
      <Button variant="secondary" onClick={onCancel}>Voltar</Button>
      <Button variant="danger" onClick={onConfirmCancellation}>
        Confirmar Cancelamento
      </Button>
    </ButtonGroup>
  </Modal>
  ```

- [ ] **Backend Logic (Full Refund):**
  ```python
  @router.post("/api/subscriptions/cancel")
  async def cancel_subscription(current_user = Depends(get_current_user)):
      subscription = get_active_subscription(current_user.id)

      # Check if within 7-day window
      subscription_age = (datetime.utcnow() - subscription.created_at).days

      if subscription_age <= 7:
          # TIER 1: Full refund
          refund = stripe.Refund.create(
              charge=subscription.stripe_charge_id,
              amount=subscription.amount_paid,  # 100% refund in cents
              reason='requested_by_customer',
              metadata={'tier': '1_full_refund', 'days_elapsed': subscription_age}
          )

          # Immediate cancellation
          subscription.is_active = False
          subscription.cancelled_at = datetime.utcnow()
          subscription.cancellation_reason = 'withdrawal_period'
          subscription.refund_amount = subscription.amount_paid / 100  # Store in BRL

          # Invalidate features cache
          redis_client.delete(f"features:{current_user.id}")

          # Cancel Stripe subscription
          stripe.Subscription.delete(subscription.stripe_subscription_id)

          db.commit()

          return {
              "success": True,
              "refund_amount": subscription.amount_paid / 100,
              "refund_id": refund.id,
              "processing_days": "5-10",
              "message": "Cancelamento confirmado. Reembolso em processamento."
          }
      else:
          # Redirect to Tier 2 (downgrade with pro-rata)
          return {
              "success": False,
              "error": "withdrawal_period_expired",
              "message": "Período de 7 dias expirado. Use a opção de downgrade.",
              "alternative": "downgrade_with_prorata"
          }
  ```

- [ ] **Confirmation Email (Tier 1):**
  ```
  Subject: Cancelamento confirmado — Reembolso integral em processamento

  Olá {user.name},

  Confirmamos o cancelamento da sua assinatura anual.

  💰 Reembolso: R$ {refund_amount} (100% do valor pago)
  ⏱️ Processamento: 5-10 dias úteis
  🚫 Benefícios desativados: Imediatamente

  O reembolso será creditado no mesmo método de pagamento usado na compra.

  Sentiremos sua falta! Se mudar de ideia, você pode reativar a qualquer momento.

  Atenciosamente,
  Equipe SmartLic
  ```

---

#### Tier 2: Downgrade sem Reembolso (8+ dias)

**Policy:** No refund, user keeps benefits until end of annual period, then converts to monthly

- [ ] **Downgrade Modal (8+ days):**
  ```tsx
  <Modal title="Downgrade para Plano Mensal" variant="warning">
    <Alert variant="warning">
      ⚠️ Você está fora do período de garantia (7 dias)
    </Alert>

    <p><strong>Política de downgrade após 7 dias:</strong></p>
    <ul>
      <li>❌ Sem reembolso do valor pago</li>
      <li>✅ Você mantém todos os benefícios anuais até {subscription.expires_at}</li>
      <li>📅 Após {subscription.expires_at}, sua assinatura será convertida para mensal</li>
      <li>💰 Próxima cobrança: R$ 297 (mensal) em {subscription.expires_at}</li>
    </ul>

    <div className="benefits-retained">
      <h4>Benefícios que você manterá até {subscription.expires_at}:</h4>
      <ul>
        <li>✨ Early access a novas features</li>
        <li>🎯 Busca proativa de oportunidades</li>
        <li>🤖 Análise IA de editais (Sala de Guerra)</li>
      </ul>
    </div>

    <Alert variant="info">
      💡 Dica: Aproveite seus benefícios anuais até o fim do período!
      Você já pagou por eles.
    </Alert>

    <Checkbox required>
      Entendo que não haverá reembolso e meus benefícios anuais
      serão mantidos até {subscription.expires_at}.
    </Checkbox>

    <ButtonGroup>
      <Button variant="secondary" onClick={onCancel}>Cancelar</Button>
      <Button variant="warning" onClick={onConfirmDowngrade}>
        Confirmar Downgrade
      </Button>
    </ButtonGroup>
  </Modal>
  ```

- [ ] **Backend Logic (No Refund Downgrade):**
  ```python
  @router.post("/api/subscriptions/downgrade")
  async def downgrade_subscription(current_user = Depends(get_current_user)):
      subscription = get_active_subscription(current_user.id)

      # Check NOT within 7-day window (must use cancellation for refund)
      subscription_age = (datetime.utcnow() - subscription.created_at).days

      if subscription_age <= 7:
          return {
              "success": False,
              "error": "use_cancellation_instead",
              "message": "Use cancelamento (reembolso integral) dentro de 7 dias."
          }

      # NO REFUND: Mark for non-renewal at period end
      subscription.will_not_renew = True
      subscription.downgrade_to = 'monthly'
      subscription.downgrade_effective_date = subscription.expires_at

      # Update Stripe: cancel at period end (no refund)
      stripe.Subscription.modify(
          subscription.stripe_subscription_id,
          cancel_at_period_end=True,
          metadata={'downgrade_requested_at': datetime.utcnow().isoformat()}
      )

      db.commit()

      return {
          "success": True,
          "refund_amount": 0,  # No refund
          "benefits_until": subscription.expires_at.isoformat(),
          "next_billing_date": subscription.expires_at.isoformat(),
          "next_billing_amount": 297.00,  # Monthly rate
          "message": "Downgrade agendado. Benefícios anuais mantidos até o fim do período."
      }
  ```

- [ ] **Confirmation Email (No Refund):**
  ```
  Subject: Downgrade agendado — Benefícios mantidos até {expires_at}

  Olá {user.name},

  Confirmamos o agendamento do downgrade do seu plano de Anual para Mensal.

  ℹ️ O que acontece agora:
  • Seus benefícios anuais continuam ativos até: {expires_at}
  • Sem reembolso (você já pagou pelo período completo)
  • Após {expires_at}, sua assinatura será convertida para mensal
  • Próxima cobrança: R$ 297 (mensal) em {expires_at}

  💡 Aproveite ao máximo seus benefícios anuais até o fim do período!

  Se mudar de ideia, você pode cancelar o downgrade a qualquer momento
  antes de {expires_at}.

  Atenciosamente,
  Equipe SmartLic
  ```

---

#### Testing Requirements

- [ ] **Test Tier 1 (0-7 days - Full Refund):**
  - [ ] Cancelamento no dia 1 → 100% refund, immediate cancellation
  - [ ] Cancelamento no dia 7 → 100% refund, immediate cancellation
  - [ ] Cancelamento no dia 8 → Rejeita, sugere downgrade (no refund)

- [ ] **Test Tier 2 (8+ days - No Refund Downgrade):**
  - [ ] Downgrade no dia 8 → No refund, benefits until expires_at
  - [ ] Downgrade após 6 meses → No refund, benefits for 6 more months
  - [ ] Downgrade no último mês → No refund, converts to monthly next billing
  - [ ] Verify will_not_renew flag set correctly
  - [ ] Verify Stripe cancel_at_period_end = true

- [ ] **Test Edge Cases:**
  - [ ] Exatamente 7 dias (168 horas) → Tier 1 (favor user)
  - [ ] Timezone differences (Brazil UTC-3) → Use user timezone
  - [ ] Stripe refund failures (Tier 1) → Rollback DB changes
  - [ ] User tries to upgrade after scheduling downgrade → Allow, cancel downgrade

- [ ] **Test Stripe Integration:**
  - [ ] Refund webhook (Tier 1) → Update local DB
  - [ ] Failed refund (Tier 1) → Retry logic
  - [ ] cancel_at_period_end webhook → Confirm downgrade scheduled

---

#### Terms of Service Update

- [ ] **Refund Policy Documentation:**
  ```markdown
  ## Política de Cancelamento e Reembolso - Planos Anuais

  ### Período de Garantia (0-7 dias) - Reembolso Integral
  Conforme o Código de Defesa do Consumidor (CDC - Lei 8.078/1990, Art. 49),
  você tem direito a cancelar sua assinatura anual dentro de 7 dias corridos
  da data de compra e receber reembolso integral (100%) do valor pago.

  O cancelamento com reembolso é imediato e seus benefícios anuais serão
  desativados na mesma hora.

  ### Downgrade Após 7 Dias - Sem Reembolso
  Após o período de garantia de 7 dias, não oferecemos reembolso para
  downgrade de plano anual para mensal.

  Caso solicite downgrade após 7 dias:
  - Você NÃO receberá reembolso do valor pago
  - Seus benefícios anuais serão mantidos até o fim do período pago
  - Ao término do período anual, sua assinatura será convertida
    automaticamente para plano mensal
  - A primeira cobrança mensal ocorrerá na data de vencimento do plano anual

  ### Exceções - Reembolso Integral a Qualquer Momento
  Reembolso integral será concedido independente do período se ocorrer:
  - Downtime do serviço superior a 72 horas contínuas (responsabilidade nossa)
  - Feature prometida não entregue com atraso superior a 6 meses do prazo
  - Cobrança não autorizada, fraude ou erro de sistema

  Para solicitar reembolso por exceção, entre em contato com nosso suporte
  em suporte@smartlic.tech com comprovação da situação.

  ### Processamento de Reembolsos
  Todos os reembolsos aprovados são processados em até 5-10 dias úteis
  e creditados no mesmo método de pagamento usado na compra original.
  ```

- [ ] **Legal review required:** CDC compliance verification before production deployment

---

## Tasks (UPDATED - 13 SP Total)

### 🎨 Frontend (4 SP)
- [ ] **Task 1.1**: Criar componente `PlanToggle` (0.5 SP)
  - File: `components/subscriptions/PlanToggle.tsx`
  - Props: `value: 'monthly' | 'annual'`, `onChange: (value) => void`
  - Acessível (ARIA labels, keyboard nav)

- [ ] **Task 1.2**: Atualizar `PlanCard` com cálculo dinâmico (1 SP)
  - File: `components/subscriptions/PlanCard.tsx`
  - Calcula `displayPrice = billingPeriod === 'annual' ? monthlyPrice * 9.6 : monthlyPrice`
  - Badge "Economize 20%" se anual

- [ ] **Task 1.3**: Criar componente `AnnualBenefits` com badges (1 SP)
  - File: `components/subscriptions/AnnualBenefits.tsx`
  - Integrate `FeatureBadge` (active, coming_soon, future)

- [ ] **Task 1.4**: Criar `TrustSignals` component (0.5 SP)
  - File: `components/subscriptions/TrustSignals.tsx`
  - Social proof, guarantees, launch offer

- [ ] **Task 1.5**: Integrar toggle + trust signals em `/planos` (0.5 SP)
  - File: `app/planos/page.tsx`
  - useState para controlar toggle
  - Load `annualConversionRate` from API

- [ ] **Task 1.6**: Downgrade modal (0.5 SP)
  - File: `components/subscriptions/DowngradeModal.tsx`

### 🔧 Backend (5 SP)
- [ ] **Task 2.1**: Migration `006_add_billing_period.sql` (0.5 SP)
  - Correct table name: `user_subscriptions`
  - NOT NULL constraint
  - Backfill script

- [ ] **Task 2.2**: Migration `007_create_plan_features.sql` (0.5 SP)
  - Robust schema (PK, FK, audit columns)
  - Seed data

- [ ] **Task 2.3**: Migration `008_stripe_webhook_events.sql` (0.5 SP)
  - Idempotency table

- [ ] **Task 2.4**: Endpoint `POST /api/subscriptions/update-billing-period` (2 SP)
  - File: `backend/routes/subscriptions.py`
  - Pro-rata calculation with edge cases
  - Timezone handling
  - Defer logic (< 7 days)
  - Cache invalidation

- [ ] **Task 2.5**: Endpoint `GET /api/features/me` with Redis (1 SP)
  - File: `backend/routes/features.py`
  - Redis cache (5min TTL)
  - Cache invalidation hooks

- [ ] **Task 2.6**: Webhook handler (idempotent) (0.5 SP)
  - File: `backend/webhooks/stripe.py`
  - Signature validation
  - Idempotency check
  - Atomic upsert

### 💳 Stripe Integration (1 SP)
- [ ] **Task 3.1**: Criar preços anuais no Stripe (0.5 SP)
  - 3 preços (Consultor Ágil, Máquina, Sala de Guerra)
  - Copy Price IDs to `.env`

- [ ] **Task 3.2**: Testes com Stripe CLI (0.5 SP)
  - Test webhooks
  - Test signature validation
  - Test idempotency

### 🧪 Testing (2 SP)
- [ ] **Task 4.1**: Testes unitários frontend (1 SP)
  - `PlanToggle.test.tsx`
  - `PlanCard.test.tsx` (20% discount calculation)
  - `TrustSignals.test.tsx`
  - `useFeatureFlags.test.ts`

- [ ] **Task 4.2**: Testes unitários backend (0.5 SP)
  - `test_prorata_edge_cases.py`
  - `test_feature_cache.py`
  - `test_webhook_idempotency.py`

- [ ] **Task 4.3**: Testes E2E (0.5 SP)
  - File: `e2e-tests/annual-subscription.spec.ts`
  - Full flow: toggle → upgrade → downgrade

### 📝 Documentação (1 SP)
- [ ] **Task 5.1**: `docs/features/annual-subscription.md` (0.5 SP)
  - Architecture, flows, troubleshooting

- [ ] **Task 5.2**: Update `.env.example` (0.25 SP)
  - Stripe Price IDs
  - Redis config
  - Feature flag

- [ ] **Task 5.3**: Terms of Service update (downgrade policy) (0.25 SP)
  - Legal review required

---

## Technical Design (UPDATED)

### Architecture Diagram

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ 1. Toggle Monthly/Annual
       ▼
┌─────────────────────────────────────┐
│  Frontend (Next.js)                 │
│  - PlanToggle component             │
│  - PlanCard (9.6x calculation)      │
│  - useFeatureFlags hook (SWR)      │
└──────┬──────────────────────────────┘
       │ 2. POST /api/subscriptions/update-billing-period
       ▼
┌─────────────────────────────────────┐
│  Backend API (FastAPI)              │
│  - Validate user                    │
│  - Calculate pro-rata               │
│  - Update Stripe subscription       │
│  - Update DB (billing_period)       │
│  - Invalidate Redis cache           │
└──────┬──────────────┬───────────────┘
       │              │
       │              ▼
       │         ┌──────────┐
       │         │  Redis   │
       │         │  (Cache) │
       │         └──────────┘
       │              ▲
       │              │ 3. GET /api/features/me
       │              │    (5min TTL)
       ▼              │
┌──────────────┐      │
│  Supabase    │◄─────┘
│  (Postgres)  │
│              │
│  - user_subscriptions (billing_period)
│  - plan_features (feature flags)
│  - stripe_webhook_events (idempotency)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Stripe     │
│  - Subscriptions
│  - Webhooks (customer.subscription.updated)
└──────────────┘
```

### Database Schema (FINAL)

```sql
-- 1. user_subscriptions (MODIFIED)
ALTER TABLE public.user_subscriptions
  ADD COLUMN billing_period VARCHAR(10) NOT NULL DEFAULT 'monthly'
    CHECK (billing_period IN ('monthly', 'annual')),
  ADD COLUMN annual_benefits JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN will_not_renew BOOLEAN DEFAULT false,
  ADD COLUMN downgrade_to VARCHAR(10),
  ADD COLUMN downgrade_effective_date TIMESTAMPTZ;

-- Index for performance
CREATE INDEX idx_user_subscriptions_billing
  ON public.user_subscriptions(user_id, billing_period, is_active)
  WHERE is_active = true;

-- 2. plan_features (NEW)
CREATE TABLE public.plan_features (
  id SERIAL PRIMARY KEY,
  plan_id TEXT NOT NULL REFERENCES public.plans(id) ON DELETE CASCADE,
  billing_period VARCHAR(10) NOT NULL CHECK (billing_period IN ('monthly', 'annual')),
  feature_key VARCHAR(100) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT true,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(plan_id, billing_period, feature_key)
);

CREATE INDEX idx_plan_features_lookup
  ON public.plan_features(plan_id, billing_period, enabled)
  WHERE enabled = true;

-- 3. stripe_webhook_events (NEW - Idempotency)
CREATE TABLE public.stripe_webhook_events (
  id VARCHAR(255) PRIMARY KEY,
  type VARCHAR(100) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  payload JSONB
);

CREATE INDEX idx_webhook_events_type
  ON public.stripe_webhook_events(type, processed_at);
```

---

## Architecture Decision Records

### ADR-001: Use Redis for Feature Flag Caching
**Status:** Approved by @architect

**Decision:** Implement Redis cache with 5-minute TTL for `GET /api/features/me`

**Rationale:**
- Reduces DB load from O(n_components) to O(1) per page load
- Sub-millisecond reads vs 50-200ms DB query
- SWR on frontend prevents multiple requests from same page

**Consequences:**
- Adds Redis dependency (already used for sessions)
- Requires cache invalidation logic on billing update

---

### ADR-002: 20% Annual Discount (vs original 16.67%)
**Status:** Approved by @po + Finance

**Decision:** Annual price = Monthly × 9.6 (20% discount)

**Rationale:**
- Competitive with market (BLL 25%, Portal 15%, Licitanet 20%)
- Psychological impact: "Economize R$ 713" > "Economize R$ 594"
- 2x expected conversion (10% → 20%) offsets -2.3% revenue

**Consequences:**
- Lower margin per annual subscriber
- Higher cash flow upfront (better for runway)

---

### ADR-003: 7-Day Refund + No-Refund Downgrade Policy
**Status:** Approved by Business Owner
**Date:** 2026-02-07
**Replaces:** Previous "No Refund at All" policy (rejected for CDC non-compliance)

**Decision:** Implement hybrid refund policy for annual subscriptions:
1. **0-7 days:** Full refund (100%) with immediate cancellation - CDC compliance
2. **8+ days:** No refund, keep benefits until end of annual period, then convert to monthly

**Context:**
Original proposal was "no refund at all" which violates Brazilian CDC (Código de Defesa do Consumidor).
Minimum compliance requires 7-day right of withdrawal. After 7 days, we protect cash flow by not offering refunds.

**Rationale:**

**Legal Compliance:**
- ✅ Brazilian CDC (Lei 8.078/1990, Art. 49) **REQUIRES** 7-day withdrawal for remote sales
- ✅ Non-compliance penalties: Fines up to R$ 10M + class action lawsuits
- ✅ After 7 days: No legal requirement for refund (we choose not to offer it)

**Business Benefits:**
- ✅ **CDC compliant:** Avoids legal risk and fines
- ✅ **Cash flow protection:** No refunds after 7 days (users paid for full year, get full year)
- ✅ **Fair to users:** They keep access to what they paid for (no "loss")
- ✅ **Lower complexity:** No pro-rata calculations needed

**Financial Impact:**
- ⚠️ **Refund rate (0-7 days):** Estimated 5-8% (CDC window)
- ✅ **Refund rate (8+ days):** 0% (no refunds offered)
- ✅ **Total refund rate:** 5-8% (vs 8-13% if we offered pro-rata)
- ✅ **Cash flow:** Protects 92-95% of annual revenue

**Comparison with Industry:**

| Company | 0-7 Days | 8+ Days | Brazilian? | CDC Compliant? |
|---------|----------|---------|------------|----------------|
| **SmartLic** | 100% refund | No refund, keep benefits | ✅ Yes | ✅ Yes |
| RD Station | 7 days refund | No refund | ✅ Yes | ✅ Yes |
| Conta Azul | 7 days refund | No refund | ✅ Yes | ✅ Yes |
| Stripe | No refund | No refund | ❌ No | N/A |
| Netflix | No refund | Cancel anytime (no refund) | ❌ No | N/A |

**Why No Refund After 7 Days?**
- ✅ Legally compliant (CDC only requires 7 days)
- ✅ Protects cash flow (critical for early-stage startup)
- ✅ Users still get value (keep benefits until end)
- ✅ Simpler than pro-rata (less support complexity)
- ✅ Industry standard for Brazilian B2B SaaS

**Implementation:**
- Tier 1 (0-7 days): `stripe.Refund.create(amount=full_amount)` + immediate cancellation
- Tier 2 (8+ days): `stripe.Subscription.modify(cancel_at_period_end=True)` + no refund

**Alternatives Considered:**

**Alternative A:** No refund at all, including 0-7 days (rejected)
- ❌ Violates Brazilian CDC
- ❌ Legal risk: Fines + lawsuits
- ❌ User perception: "illegal"

**Alternative B:** 7 days + pro-rata refund after (rejected)
- ✅ CDC compliant
- ✅ More "generous"
- ❌ Higher refund rate (8-13% vs 5-8%)
- ❌ Complex pro-rata calculations
- ❌ Worse cash flow
- **Rejected by Business Owner:** Too expensive for early-stage

**Alternative C:** 30-day money-back guarantee (rejected)
- ✅ Great for marketing
- ❌ Way too expensive (15-20% refund rate)
- ❌ Users "trial" annual, then refund

**Consequences:**

**Positive:**
- ✅ Legal compliance (avoid CDC violations)
- ✅ Cash flow protected (only lose 5-8% to CDC refunds)
- ✅ Fair to users (they keep what they paid for)
- ✅ Simple implementation (no complex calculations)

**Negative:**
- ⚠️ Possible chargebacks after 7 days (estimated 2-3%)
- ⚠️ User perception: "Not as generous as pro-rata"
- ⚠️ Support tickets: "Why no refund after 7 days?"

**Risks & Mitigations:**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Users abuse 7-day window | Medium | Track refund rate per user; flag if > 2/year |
| Chargebacks after 7 days | Low | Clear messaging in modal + Terms of Service |
| CDC audit finds non-compliance | Very Low | 7-day refund is compliant; legal review confirms |
| Bad reviews ("no refund") | Medium | Communicate: "You keep access to what you paid for" |

**Monitoring Metrics:**
- Refund rate (0-7 days): Target < 8%
- Chargeback rate (8+ days): Target < 3%
- Total refund+chargeback: Target < 11%
- NPS for downgraded users: Target > 40 (vs < 20 for immediate cancellation)

**Decision Maker:** Business Owner (via PM)
**Next Review:** Q2 2026 (after 3 months of data)

**Exception Policy:**
Full refund offered at any time if:
1. Service downtime > 72 hours continuous (our fault)
2. Promised feature not delivered 6+ months late
3. Unauthorized charge / fraud

---

## Dependencies

### Blocked By:
- [ ] **Finance approval** for 20% discount (30min meeting)
- [ ] **Legal review** of downgrade policy (1 day)
- [ ] **Redis provisioning** on Railway (DevOps - 1 hour)
- [ ] **Stripe annual prices** created (30 min)

### Blocks:
- **STORY-172** (Proactive Search Implementation) — Annual subscribers get this first
- **STORY-173** (AI Edital Analysis for Sala de Guerra) — Exclusive to annual
- **STORY-174** (Dashboard Executivo) — Backlog, enhances Sala de Guerra
- **STORY-175** (Alertas Multi-Canal) — Backlog, enhances Sala de Guerra

---

## Risks & Mitigations (UPDATED)

| Risk | Severity | Impact | Mitigation |
|------|----------|--------|------------|
| **Stripe API failures during upgrade** | 🔴 High | Users charged but billing_period not updated | Retry logic (3x) + error notifications + manual reconciliation script |
| **Pro-rata calculation errors** | 🟡 Medium | Over/under charging | Extensive unit tests + manual validation with sample data + rounding always favors user |
| **Timezone bugs (Brazil UTC-3)** | 🟡 Medium | Wrong billing date calculation | Store `billing_timezone` in user_subscriptions, always calculate in user's TZ |
| **Users downgrade immediately after upgrade** | 🟢 Low | Lost revenue | Modal confirmation + "cooling-off" messaging + downgrade-effective-date (keeps benefits until end) |
| **Feature flags not syncing** | 🔴 High | Users pay for annual but don't get features | Redis cache with aggressive invalidation + monitoring alerts if cache miss rate > 10% |
| **Webhook idempotency failure** | 🔴 High | Duplicate processing → double billing | `stripe_webhook_events` table + signature validation + atomic upsert |
| **UX confusa (toggle não claro)** | 🟡 Medium | Low conversion | User testing pre-launch + tooltips + trust signals |
| **Selling features not yet built** | 🟡 Medium | Negative reviews | "Coming Soon" badges + EARLYBIRD discount code + launch notifications |

---

## Success Metrics (UPDATED - PO Approval)

| Metric | Target | Measurement | How to Track |
|--------|--------|-------------|--------------|
| **Annual Conversion Rate** | 18-22% | Ongoing | `(annual signups / total signups) × 100` |
| **ARR Growth** | +30% in Q1 2026 | 3 months | `(new ARR - baseline ARR) / baseline ARR` |
| **Cash Collected** | R$ 200K in Q1 | 3 months | Sum of annual subscriptions paid upfront |
| **Annual Churn** | < 15% at renewal | 12 months | `(cancelled annual / total annual) × 100` |
| **Monthly Churn** | ~40% over 12 mo | 12 months | `1 - (0.92)^12` (baseline for comparison) |
| **Feature Adoption (Busca Proativa)** | >70% of annual users | 1 month after STORY-172 launch | Track usage via analytics |
| **NPS for Annual Users** | >50 | Quarterly survey | Survey annual subscribers only |
| **Error Rate (Billing Update)** | <1% | Ongoing | `(failed updates / total updates) × 100` |

**Dashboard:** Create `/admin/annual-metrics` with real-time tracking

---

## Rollout Plan (UPDATED - 4 Phases)

### Phase 1: Internal Alpha (Week 1)
**Goal:** Catch bugs before users see them

**Tasks:**
- [ ] Deploy to staging
- [ ] Internal team test (10 people)
- [ ] QA checklist (all 17 ACs validated)
- [ ] Test Stripe integration (test mode)
- [ ] **Support team training** (1-hour session):
  - FAQ doc: "How annual plans work"
  - Demo: Toggle UI walkthrough
  - Escalation path: Billing issues → DevOps

**Success Criteria:**
- ✅ Zero critical bugs
- ✅ Support can answer top 10 FAQs
- ✅ Stripe test transactions 100% success rate

**Duration:** 5 business days

---

### Phase 2: Controlled Beta (Week 2-3)
**Goal:** Validate conversion rate with A/B test

**Cohort Selection:**
```javascript
const getCohort = (userId) => {
  const hash = hashCode(userId);
  if (hash % 100 < 45) return 'A';  // Control (monthly only)
  if (hash % 100 < 90) return 'B';  // Test (annual toggle)
  return 'C';  // Holdout
};
```

**Cohorts:**
- **Segment A (Control):** 45% → See OLD pricing (monthly only)
- **Segment B (Test):** 45% → See NEW pricing (annual toggle)
- **Segment C (Holdout):** 10% → No changes (statistical significance)

**Metrics to Watch:**
- Conversion rate: Segment B annual signups
- Revenue per user: Segment B vs A
- Support tickets: Annual plan questions
- Bug reports: Payment failures, UI glitches

**Decision Point (End of Week 3):**
- If Segment B conversion ≥ 15% → Proceed to Phase 3 ✅
- If Segment B conversion < 10% → Revise messaging, extend beta ⚠️
- If critical bugs > 5 → Pause, fix, restart beta ❌

**Duration:** 10 business days

---

### Phase 3: Full Rollout (Week 4)
**Goal:** 100% of users see annual toggle

**Launch Day:**
- [ ] Feature flag: `ENABLE_ANNUAL_PLANS = true` (100% traffic)
- [ ] **Email campaign:** "🎉 Novo: Planos Anuais com 20% de desconto"
  - Segment: All active monthly subscribers (5,000+ users)
  - CTA: "Upgrade para anual e economize até R$ 3,594/ano"
  - Include `EARLYBIRD` code for first 50
- [ ] **Blog post:** "Por que escolher um plano anual?"
  - SEO keywords: "planos anuais licitações", "desconto SmartLic"
- [ ] **In-app announcement:** Banner on `/buscar`
  - "💡 Economize 20% com plano anual! Ver planos →"
- [ ] **Social media:** LinkedIn, Twitter posts

**Customer Support:**
- [ ] Extended hours (9am-9pm) for launch week
- [ ] Live chat enabled on `/planos` page
- [ ] SLA: Annual billing issues resolved in < 4 hours

**Monitoring:**
- [ ] Datadog alert: Error rate > 5% on billing endpoint
- [ ] Stripe dashboard: Failed charges alert
- [ ] Hotjar recordings: Watch user interactions with toggle

**Rollback Plan:**
- If error rate > 5% → `ENABLE_ANNUAL_PLANS = false` (instant)
- If Stripe failures > 10/hour → Pause new signups, investigate
- If negative sentiment → PR response in < 2 hours

**Duration:** 5 business days (launch + monitoring)

---

### Phase 4: Post-Launch Optimization (Week 5-8)
**Goal:** Iterate based on data

**Weekly Activities:**
- [ ] **Monday:** Review conversion, ARR, bugs
- [ ] **Wednesday:** A/B test messaging variants
  - Test 1: "Economize 20%" vs "Pague 9.6 meses"
  - Test 2: Badge placement (top vs bottom of card)
- [ ] **Friday:** Customer interviews
  - 5 users who chose annual (why?)
  - 5 users who chose monthly (why not annual?)

**Optimization Triggers:**
- If conversion < 18%: Increase discount to 25%
- If Sala de Guerra annual < 10%: Add more exclusive features (STORY-174, 175)
- If support tickets high: Improve onboarding/FAQ

**Duration:** 20 business days

---

### Communication Timeline

| Day | Channel | Message | Audience |
|-----|---------|---------|----------|
| **D-7** | Email (Teaser) | "Novidade chegando em 7 dias... 🤫" | All users |
| **D-3** | Blog | "Por que planos anuais valem a pena" (SEO) | Public |
| **D-1** | Email | "Amanhã: Planos anuais com desconto exclusivo" | All users |
| **D-0** | Email + In-app | "🎉 Planos anuais disponíveis agora! Código EARLYBIRD" | All users |
| **D+1** | Social Media | "Economize 20% com nossos planos anuais" | Public |
| **D+7** | Email (Retarget) | "Ainda não aproveitou o desconto anual?" | Viewed /planos, didn't convert |
| **D+14** | Case Study | "Como [Cliente X] economizou R$ 3,500" | All users |
| **D+30** | Feature Launch | "🎉 Busca Proativa ativa para assinantes anuais!" | Annual subscribers |

---

## File List (UPDATED)

### Created (Backend):
- `supabase/migrations/006_add_billing_period.sql`
- `supabase/migrations/006_rollback.sql`
- `supabase/migrations/007_create_plan_features.sql`
- `supabase/migrations/008_stripe_webhook_events.sql`
- `backend/routes/subscriptions.py` (update-billing-period endpoint)
- `backend/routes/features.py` (GET /api/features/me with Redis)
- `backend/services/billing.py` (pro-rata calculation logic)
- `backend/webhooks/stripe.py` (idempotent webhook handler)
- `backend/models/stripe_webhook_event.py`
- `backend/tests/test_billing_period.py`
- `backend/tests/test_prorata_edge_cases.py`
- `backend/tests/test_feature_cache.py`
- `backend/tests/test_webhook_idempotency.py`

### Created (Frontend):
- `components/subscriptions/PlanToggle.tsx`
- `components/subscriptions/AnnualBenefits.tsx`
- `components/subscriptions/TrustSignals.tsx`
- `components/subscriptions/FeatureBadge.tsx`
- `components/subscriptions/DowngradeModal.tsx`
- `hooks/useFeatureFlags.ts`
- `components/subscriptions/__tests__/PlanToggle.test.tsx`
- `components/subscriptions/__tests__/TrustSignals.test.tsx`
- `hooks/__tests__/useFeatureFlags.test.ts`
- `e2e-tests/annual-subscription.spec.ts`

### Created (Documentation):
- `docs/features/annual-subscription.md` (architecture, flows, troubleshooting)
- `docs/architecture/decisions/ADR-001-redis-cache.md`
- `docs/architecture/decisions/ADR-002-20-percent-discount.md`
- `docs/architecture/decisions/ADR-003-no-refund-downgrade.md`
- `docs/legal/downgrade-policy.md` (for Terms of Service)
- `docs/support/faq-annual-plans.md` (customer support)

### Modified:
- `app/planos/page.tsx` (toggle, trust signals integration)
- `components/subscriptions/PlanCard.tsx` (9.6x calculation, 20% discount badge)
- `.env.example` (Stripe Price IDs, Redis config, ENABLE_ANNUAL_PLANS flag)
- `backend/config.py` (feature flag, Redis connection)
- `package.json` (add `swr` dependency)
- `requirements.txt` (add `redis` dependency)

---

## Dev Notes

**2026-02-07 - Story Created by @pm (Morgan):**
- Requisito alinhado com estratégia de retenção e LTV
- Benefícios anuais focam em automação e early access (diferenciais competitivos)
- Feature "Análise IA" exclusiva para Sala de Guerra justifica premium pricing

**2026-02-07 - Reviewed by @architect (Aria):**
- ✅ Approved with 5 critical changes:
  1. Correct table name (user_subscriptions)
  2. Robust plan_features schema (PK, FK, audit)
  3. Redis cache implementation
  4. Pro-rata edge cases (timezone, defer logic)
  5. Webhook idempotency (signature validation, dedup table)
- **Story Points:** 8 SP → 13 SP (due to additional complexity)
- **ADRs created:** ADR-001 (Redis), ADR-002 (20% discount), ADR-003 (no refund)

**2026-02-07 - Reviewed by @po (Sarah):**
- ✅ Approved with 7 adjustments:
  1. Strengthen Sala de Guerra (add STORY-174, 175 to backlog)
  2. Increase discount 16.67% → 20%
  3. Add trust signals (social proof, guarantees, urgency)
  4. Launch with "Coming Soon" badges + EARLYBIRD code
  5. Revise metrics (ARR, cash flow, conversion 18-22%)
  6. 4-phase rollout (alpha, beta A/B test, full, optimization)
  7. No refund downgrade policy
- **Pricing approved:** Anual = Mensal × 9.6
- **Rollout approved:** 4 weeks (vs original 2 weeks)

**2026-02-07 - Updated Post-Review:**
- All critical changes incorporated
- New ACs added: AC15 (trust signals), AC16 (coming soon), AC17 (downgrade)
- Tasks reorganized: 13 SP total
- Success metrics updated
- Rollout plan expanded

**2026-02-07 - Refund Policy Corrected:**
- ✅ AC17 updated: 7-day full refund (CDC) + no-refund downgrade after
- ✅ ADR-003 revised: Removed pro-rata refund (rejected by Business Owner)
- **Final Policy:** 0-7 days = 100% refund | 8+ days = No refund, keep benefits until end
- **Rationale:** Protects cash flow while remaining CDC compliant
- **Impact:** Lower refund rate (5-8% vs 8-13%), simpler implementation

---

## Next Steps

1. **Finance Approval** (30 min) — Approve 20% discount impact
2. **Legal Review** (1 day) — Approve downgrade policy for Terms of Service
3. **Redis Provisioning** (1 hour) — DevOps setup on Railway
4. **Stripe Setup** (30 min) — Create 3 annual prices, copy IDs
5. **Sprint Planning** (1 hour) — Allocate to full-stack squad
6. **Kickoff** — Activate `/bidiq feature` squad for implementation

**Recommended Squad:** `team-bidiq-feature` (pm, architect, dev, qa, devops)
**Timeline:** 4 weeks (1 week implementation, 3 weeks rollout)
**Budget:** 13 SP (~2 weeks dev time)

---

**Status:** 🚀 **READY FOR IMPLEMENTATION**
