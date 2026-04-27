# MON-FN-008: Free Tier (5 buscas/mês) Como Downsell Paywall

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 4-5 (20/mai–02/jun)
**Sprint Window:** Sprint 4-5 (depende de MON-FN-006)
**Dependências bloqueadoras:** MON-FN-006 (eventos `paywall_hit` + audit funcional para medir downsell uptake)

---

## Contexto

Hoje quando trial expira (`trial_expires_at < now()` AND `plan_type='free_trial'`), `quota/plan_auth.py:135-152` lança HTTP 403 com `error_type='trial_expired'` — paywall imediato sem alternativa. UX-wise: usuário sai 100% (zero retention). Sem free tier, perdemos visibilidade de "engagement de longa cauda" que pode converter via SEO/produto improvements futuros.

Benchmark Fortune-500: free tier permite **continuar product engagement** com quotas reduzidas. Padrão "downsell" = quando paywall hits, oferecer free tier ANTES de exit. Empresas como Notion, Figma, Vercel usam exatamente esse pattern.

**Importante (do plano + memory `feedback_n2_below_noise_eng_theater`):** decisão de quotas exatas (5 buscas/mês? 3? 10?) **não é decisão desta story** — n=2 baseline impede A/B; precificação fica bloqueada até n≥30. Esta story **instrumenta a infraestrutura** com defaults razoáveis (5/mês) que podem ser ajustados em config sem mudança de código.

`backend/services/billing.py` mantém sync `profiles.plan_type`. Tabela `plan_billing_periods` é source of truth (memory `pricing-b2g`). Adicionar plan `smartlic_free` é mudança de DATA (insert row), não de schema.

**Por que P1:** retention zero post-trial é leak crítico. Após ramp-up SEO (EPIC B), traffic vem mas todo o user que não converte trial em 14 dias evapora. Free tier preserva pipeline para conversão futura.

**Paths críticos:**
- `backend/services/billing.py` (sync logic; adicionar handling para `smartlic_free`)
- `backend/quota/quota_core.py` (PlanCapabilities para free tier)
- `backend/quota/plan_auth.py` (substituir HTTP 403 por downgrade-or-block decision)
- `backend/cron/trial_lifecycle.py` (de MON-FN-006: trial_expired transitiona para `smartlic_free` em vez de paywall imediato)
- `frontend/components/Paywall*` (downsell UI)

---

## Acceptance Criteria

### AC1: Adicionar plan `smartlic_free` em `plan_billing_periods`

Given que tabela `plan_billing_periods` é source of truth de planos,
When migration roda,
Then linha `smartlic_free` é inserida com quotas reduzidas.

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_add_smartlic_free_plan.sql`:
```sql
INSERT INTO public.plan_billing_periods (
  plan_id,
  billing_period,
  display_name,
  monthly_price_cents,
  stripe_price_id,
  searches_per_month,
  alerts_enabled,
  exports_enabled,
  pipeline_enabled,
  is_active
) VALUES (
  'smartlic_free',
  'mensal',
  'SmartLic Free',
  0,
  NULL,                           -- no Stripe product (free)
  5,                              -- 5 searches/month default (configurable)
  false,                          -- no alerts
  false,                          -- no Excel/Sheets export
  false,                          -- no pipeline kanban
  true
)
ON CONFLICT (plan_id, billing_period) DO NOTHING;
```
- [ ] Migration paired down `.down.sql` (DELETE WHERE plan_id='smartlic_free')
- [ ] Verificar que não quebra `pricing-b2g` skill ou frontend `/planos` page (free tier exibido como "downgrade option" não como produto principal)

### AC2: PlanCapabilities entry para `smartlic_free`

Given quota system carrega `PlanCapabilities` de DB ou hard-coded,
When user é `smartlic_free`,
Then capabilities reduzidas aplicam.

- [ ] Em `backend/quota/quota_core.py` adicionar capabilities (verificar local exato — pode ser DB-driven ou hard-coded fallback):
```python
# In PlanCapabilities source (DB-driven preferred, hard-coded fallback)
SMARTLIC_FREE_CAPABILITIES = PlanCapabilities(
    plan_id="smartlic_free",
    searches_per_month=5,
    alerts_enabled=False,
    exports_enabled=False,
    pipeline_enabled=False,
    priority=PlanPriority.LOW,
    daily_search_limit=2,  # additional daily cap to prevent burst
)
```
- [ ] Capabilities cache (linha 19-22 quota_core.py) inclui novo plan
- [ ] `clear_plan_capabilities_cache` invalida quando admin muda quota

### AC3: Trial expira → transition para `smartlic_free` (não bloqueio)

Given trial expirado (cron `trial_lifecycle_job` de MON-FN-006),
When `dunning_phase` healthy AND `plan_type='free_trial'` AND `trial_expires_at < now()`,
Then transition para `plan_type='smartlic_free'` (não para `expired`).

- [ ] Em `backend/cron/trial_lifecycle.py` (criado em MON-FN-006), adicionar transição em vez de apenas evento:
```python
# Trial expired transition logic
expired_users = sb.table("profiles").select("id, trial_expires_at, plan_type, dunning_phase") \
    .eq("plan_type", "free_trial") \
    .lt("trial_expires_at", now.isoformat()) \
    .execute()

for u in expired_users.data or []:
    if (u.get("dunning_phase") or "healthy") != "healthy":
        continue  # dunning takes precedence

    # Transition to free tier
    sb.table("profiles").update({
        "plan_type": "smartlic_free",
    }).eq("id", u["id"]).execute()

    # Atomic cache invalidation (MON-FN-003)
    await publish_plan_invalidation(u["id"], "smartlic_free")

    track_funnel_event("trial_expired", u["id"], properties={
        "trial_expires_at": u["trial_expires_at"],
        "transitioned_to": "smartlic_free",
    })
    track_funnel_event("trial_downgraded_to_free", u["id"], properties={
        "from_plan": "free_trial",
        "to_plan": "smartlic_free",
    })
    smartlic_trial_downgraded_to_free_total.inc()
```
- [ ] Feature flag `FREE_TIER_DOWNSELL_ENABLED=true` (default); `false` mantém comportamento anterior (block direto)

### AC4: Quota enforcement para `smartlic_free`

Given user free tier excede 5 buscas no mês,
When tenta /buscar,
Then 402 Payment Required com paywall normal (CTA upgrade ou aguardar mês).

- [ ] `backend/quota/quota_atomic.py::check_and_increment_quota_atomic` já decisor por capabilities — verificar que `smartlic_free` flow corretamente
- [ ] Mensagem específica para free tier exceeded:
```python
if quota_exceeded and plan_id == "smartlic_free":
    raise HTTPException(
        status_code=402,
        detail={
            "error": "free_quota_exceeded",
            "message": "Você usou suas 5 buscas grátis deste mês. Faça upgrade para SmartLic Pro ou aguarde a renovação no dia X.",
            "upgrade_url": "/planos",
            "renews_at": _next_quota_reset_date(user_id).isoformat(),
        },
    )
```
- [ ] Mensal reset: monthly basis from `quota_reset_at` (existing column ou criar) — não ano-prorata

### AC5: Plan_auth — downsell paywall (não block direto)

Given user free tier hit feature gated (e.g. tenta export),
When acessa endpoint protegido,
Then mostra mensagem com 2 opções: upgrade OU continuar free.

- [ ] Em `backend/quota/plan_auth.py`:
```python
if plan_id == "smartlic_free" and feature_required and not capabilities.has(feature_required):
    track_funnel_event("paywall_hit", user_id, properties={
        "reason": "free_tier_feature_gated",
        "feature": feature_required,
        "plan_id": "smartlic_free",
    })
    raise HTTPException(
        status_code=402,
        detail={
            "error": "free_tier_feature_gated",
            "feature": feature_required,
            "message": f"O recurso '{feature_required}' não está disponível no plano gratuito.",
            "upgrade_url": "/planos",
            "downsell_offered": True,  # signals frontend to show "stay free" option
        },
    )
```

### AC6: Frontend paywall component — downsell UI

Given paywall hit,
When user vê modal,
Then opções "Upgrade pra Pro" + "Continuar grátis" são apresentadas.

- [ ] Atualizar `frontend/app/components/Paywall*.tsx` (ou criar novo):
  - Header: "Você atingiu o limite do plano gratuito"
  - Card 1: "Continue grátis" — lista limitações (5 buscas/mês, sem alertas, sem export)
  - Card 2: "SmartLic Pro" — preço + features highlighted
  - CTA primário: "Upgrade para Pro" (Stripe Checkout)
  - CTA secundário: "Continuar grátis" (fecha modal — user mantém access free)
- [ ] Mixpanel events:
  - `paywall_displayed` (com `plan_id, reason`)
  - `paywall_upgrade_clicked` (CTA primário)
  - `paywall_stay_free_clicked` (CTA secundário) — sinal de retention preservada
  - `paywall_dismissed` (close button) — sinal de friction
- [ ] A11y: trap focus, ESC fecha, role="dialog"

### AC7: Re-upgrade path: free tier → trial → paid

Given user `smartlic_free` decide pagar,
When inicia checkout,
Then sistema **não inicia novo trial** (trial é one-time per user); vai direto para paid.

- [ ] Verificar `backend/services/billing.py` — quando `plan_type='smartlic_free'` e checkout success: skip trial_period_days, ir direto para subscription cobrança
- [ ] Stripe Customer side: `trial_period_days=None` quando user já teve trial anterior (check `profiles.trial_started_at IS NOT NULL`)
- [ ] Test: user A (already had trial) → free tier → checkout → no trial, charged immediately

### AC8: Quota refresh mensal

Given que free tier tem 5 buscas/mês,
When mês muda,
Then quota reseta para 5.

- [ ] Cron mensal (1º dia 02 UTC) — pode usar existing `quota_reset_job` se houver, ou novo
- [ ] Reset query:
```sql
UPDATE profiles
SET searches_used_this_month = 0,
    quota_reset_at = now()
WHERE plan_type = 'smartlic_free';
```
- [ ] Idempotência: cron só roda dia 1 do mês; se já reseted (`quota_reset_at >= start_of_month`), skip
- [ ] Counter `smartlic_free_quota_reset_total{users_count}`

### AC9: Métricas

- [ ] Counters:
  - `smartlic_trial_downgraded_to_free_total`
  - `smartlic_free_to_paid_conversion_total` (free → paid via checkout)
  - `smartlic_free_quota_exceeded_total{action}` (search|export|alert)
  - `smartlic_paywall_stay_free_clicked_total`
- [ ] Gauge `smartlic_free_tier_active_users`
- [ ] Funnel Mixpanel: `trial_expired → trial_downgraded_to_free → paywall_hit (free_tier) → upgrade_clicked → paid`

### AC10: Testes

- [ ] Unit `backend/tests/quota/test_smartlic_free_capabilities.py`:
  - [ ] Free tier capabilities load corretamente
  - [ ] Quota 5/month enforced
  - [ ] Daily cap 2/day extra protection
  - [ ] Feature gates (export, alerts, pipeline) bloqueam corretamente
- [ ] Integration `backend/tests/cron/test_trial_to_free_transition.py`:
  - [ ] Trial expirado + dunning_phase healthy → transition para smartlic_free
  - [ ] Trial expirado + dunning_phase blocked → skip (dunning precedence)
  - [ ] Idempotência: re-run cron no mesmo dia → no double transition
  - [ ] Cache invalidated atomically
  - [ ] Events emitidos: `trial_expired` + `trial_downgraded_to_free`
- [ ] Integration `backend/tests/quota/test_free_quota_enforcement.py`:
  - [ ] User free tier 6 buscas → 6ª retorna 402
  - [ ] Mensal reset → quota volta a 5
- [ ] Unit `frontend/__tests__/Paywall.test.tsx`:
  - [ ] Render downsell UI com 2 cards
  - [ ] Click "Stay free" emite event + fecha modal
  - [ ] Click "Upgrade" redireciona para Stripe
- [ ] E2E Playwright:
  - [ ] User free tier → 5 buscas → 6ª shows paywall com downsell → click stay free → modal closes → user permanece free
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Plan `smartlic_free` em DB + capabilities
- Transição trial→smartlic_free no cron
- Quota enforcement (5/mês default, configurable)
- Downsell paywall UI (frontend)
- Métricas + Mixpanel events
- Re-upgrade path sem novo trial
- Quota mensal reset

**OUT:**
- **Decisão de quotas exatas (5 vs 3 vs 10)** — defaults configuráveis, decisão futura n≥30
- A/B test de copywriting paywall (n=2 impede)
- Free tier "lifetime" promotional (e.g., "free for 6 months") — Stripe coupons cobrem
- Affiliate/referral free quota boost (STORY-364 separado)
- Custom features per free tier (e.g., setor único) — fora escopo
- Re-engagement emails para inactive free users (futuro)
- Self-serve plan changes além de upgrade (downgrade premium→free não permitido inicialmente)

---

## Definition of Done

- [ ] Migration aplicada em prod; `smartlic_free` linha em `plan_billing_periods`
- [ ] PlanCapabilities reconhece free tier
- [ ] Trial expira → transition para smartlic_free (validar com test user manual)
- [ ] Quota 5/mês enforced (validar via 6 buscas em test user)
- [ ] Frontend paywall mostra downsell UI com 2 CTAs
- [ ] Eventos `trial_downgraded_to_free`, `paywall_stay_free_clicked` visíveis em Mixpanel
- [ ] Counter `smartlic_trial_downgraded_to_free_total` exposto
- [ ] Re-upgrade test: free user paga → no double-trial
- [ ] Cron quota reset mensal validado
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] @ux-design-expert review do paywall UI
- [ ] Operational runbook em `docs/operations/free-tier-runbook.md`
- [ ] Rollback feature flag `FREE_TIER_DOWNSELL_ENABLED` testada

---

## Dev Notes

### Padrões existentes a reutilizar

- **PlanCapabilities:** `quota/quota_core.py::PlanCapabilities` BaseModel
- **Quota atomic:** `quota/quota_atomic.py::check_and_increment_quota_atomic`
- **`plan_billing_periods` table:** STORY-277/360 — single source of truth de planos
- **Stripe Customer Portal:** `services/billing.py::_stripe_customer_portal_url`
- **Cache invalidation:** `publish_plan_invalidation` (MON-FN-003)
- **Mixpanel funnel events:** `track_funnel_event` (MON-FN-006)

### Funções afetadas

- `backend/services/billing.py` (handle smartlic_free transitions)
- `backend/quota/quota_core.py` (capabilities)
- `backend/quota/plan_auth.py` (downsell decision)
- `backend/quota/quota_atomic.py` (quota enforcement consistent)
- `backend/cron/trial_lifecycle.py` (de MON-FN-006: transition logic)
- `backend/cron/billing.py` ou novo `cron/quota_reset.py` (mensal reset)
- `frontend/app/components/Paywall*.tsx` (downsell UI)
- `frontend/app/planos/page.tsx` (mostrar free tier opcionalmente)
- `backend/metrics.py` (counters)
- `supabase/migrations/YYYYMMDDHHMMSS_add_smartlic_free_plan.sql` + `.down.sql`

### Trade-off decision: 5 vs 3 vs 10 buscas

Plano (`out_of_scope.md`) explicita: defaults configuráveis em `plan_billing_periods` row; ajuste sem code change. Recomendação inicial: **5 buscas/mês + 2/dia daily cap**. Justificativa:
- 5/mês: suficiente para "kick the tires"; insuficiente para B2G real (alvo conversão)
- 2/dia daily cap: previne burst de webscraping (anti-abuse)
- Trade-off: muito generoso (>10) reduce upgrade pressure; muito tight (<3) fricção desnecessária

Decisão final fica em `plan_billing_periods` row e pode ser ajustada após n≥30 com signal.

### Testing Standards

- Unit em `backend/tests/quota/`
- Integration em `backend/tests/cron/`
- Frontend tests em `frontend/__tests__/`
- E2E em `frontend/e2e-tests/`
- Mock Stripe via fixture
- `freezegun` para month rollover tests
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Mass abuse: >1000 signups/dia em free tier (sinal de bot ou farming)
- Free tier conversion to paid <2% após 30d (sinal de quota muito generosa — não bug, mas decisão produto)
- Bug em transition: usuários trial → blocked em vez de smartlic_free
- Quota reset cron falha (free users perdem acesso start of month)

### Ações de rollback
1. **Imediato:** `FREE_TIER_DOWNSELL_ENABLED=false` — trial expira → block (estado anterior)
2. **Mass abuse:** tightening quota de 5→2 via `plan_billing_periods` UPDATE (sem deploy)
3. **Bug transition:** manual SQL fix `UPDATE profiles SET plan_type='smartlic_free' WHERE plan_type='expired' AND trial_started_at IS NOT NULL`
4. **Quota reset crash:** manual SQL para reset; investigate cron logs

### Compliance
- Free tier não exige cartão — não há novo PII coletado
- LGPD: free users incluídos em export/deletion exatamente como trial users (MON-FN-010, MON-FN-011)

---

## Dependencies

### Entrada
- **MON-FN-006** (eventos funil): paywall_hit + audit funcional
- **MON-FN-003** (cache invalidation): downgrade trial→free precisa invalidar atomicamente
- **MON-FN-007** (dunning): coexistência sem race (dunning precedence)
- `plan_billing_periods` table existente
- PlanCapabilities system existente

### Saída
- **MON-FN-013** (ARPU/MRR): free tier user count alimenta métrica "free→paid conversion rate"
- **MON-FN-012** (cohort retention): free tier dramatizes retention curve (pre vs post)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Free Tier (5 buscas/mês) Como Downsell Paywall" |
| 2 | Complete description | Y | Memory `feedback_n2_below_noise_eng_theater` referenciada explicitamente; benchmark Notion/Figma/Vercel |
| 3 | Testable acceptance criteria | Y | 10 ACs incluindo E2E 6 buscas → paywall + Stripe re-upgrade test |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT delimita decisão quotas exatas (5 vs 3 vs 10) — **task constraint respeitada** |
| 5 | Dependencies mapped | Y | Entrada MON-FN-006/003/007; Saída MON-FN-013/012 |
| 6 | Complexity estimate | Y | L (5-7 dias) coerente — capabilities + transition + UI + E2E |
| 7 | Business value | Y | "Retention zero post-trial é leak crítico" + preserva pipeline futuro |
| 8 | Risks documented | Y | Mass abuse + low conversion <2% + bug transition; flag rollback testado |
| 9 | Criteria of Done | Y | UX review + manual validate test user + CodeRabbit clean |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #8 (free tier) + Out-of-Scope decisões pricing respeitado |

### Observations
- **Delimitação correta confirmada:** AC1 instrumenta DB row mas defaults (5 buscas/mês + 2/dia daily cap) são CONFIGURÁVEIS via `plan_billing_periods` UPDATE sem code change. Decisão final fica em config row e ajustável após n≥30 com signal.
- Trade-off section em Dev Notes documenta justificativa numérica para 5/2/dia
- Re-upgrade path: previne double-trial (verifica `profiles.trial_started_at IS NOT NULL`)
- Coexistência com MON-FN-007 (dunning precedence) explicita
- Cache invalidation atomic via `publish_plan_invalidation` (MON-FN-003)
- Mass abuse rollback via `plan_billing_periods` quota tightening (sem deploy)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — free tier downsell + transition logic + downsell UI | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P1 infra free tier configurável; quotas finais ficam pós-n≥30 (delimitação respeitada); Status Draft → Ready. | @po (Pax) |
