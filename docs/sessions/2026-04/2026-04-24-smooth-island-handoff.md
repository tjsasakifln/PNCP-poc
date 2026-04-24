# Session smooth-island — 2026-04-24

**Branch:** `feat/trial-conversion-smooth-island` (isolada de main)
**PR:** [#501](https://github.com/tjsasakifln/PNCP-poc/pull/501)
**Plan:** `~/.claude/plans/mission-empresa-morrendo-smooth-island.md`
**Mission:** empresa-morrendo (MRR única métrica)
**Classe:** REVENUE-DIRECT

## Objetivo

Ship 3 deltas no caminho trial-expiring → paid: coupon badge visual em `/planos` + 2 eventos Mixpanel no funil (`paywall_hit` backend + `plan_selected` frontend). 1 PR isolado.

## Entregue

| PR | Commit | Scope |
|----|--------|-------|
| **#501 OPEN** | `812fb39f` | `feat(backend): emit paywall_hit Mixpanel event em require_active_plan` — 3 choke points (dunning_blocked, dunning_grace_period, trial_expired) em `backend/quota/plan_auth.py` |
| **#501 OPEN** | `ee394342` | `feat(frontend): coupon badge + plan_selected Mixpanel em /planos` — `COUPON_DISCOUNTS` constant, banner emerald, preços riscados em `PlanProCard`+`PlanConsultoriaCard`, `window.mixpanel.track('plan_selected')` antes do POST checkout |

## Audit GATE (Step 1)

Query ad-hoc `backend/scripts/audit_trial_email_log_smooth_island.py` (NÃO commitado) confirmou scheduler funciona:

| User | Created | Trial exp | Emails log |
|------|---------|-----------|------------|
| dslicitacoesthe@gmail.com | 2026-04-08 | 2026-04-22 | 5 emails (engagement, paywall_alert, value, last_day, expired) |
| paulo.souza@adeque-t.com.br | 2026-04-10 | 2026-04-24 | 4 emails (engagement, paywall_alert, value, last_day) — Day 16 expired ainda não caiu |

Observação não-derivável: `delivery_status` coluna está NULL p/ todos os registros — verificar Resend dashboard delivery rate separadamente se métricas forem inconclusivas na próxima sessão.

Mental model corrigido durante sessão (advisor feedback): scheduler de email usa `created_at` + milestones fixos `[0, 3, 7, 10, 13, 16]` — independente do bug velvet-music em `trial_expires_at`. Scheduler estava sempre funcionando mesmo com bug anterior no paywall.

## Impacto em receita

| Mudança | Estado | Como medir (24h soak) |
|---------|--------|------------------------|
| Coupon badge 20% visível em `/planos?coupon=TRIAL_COMEBACK_20` | Aguarda merge PR #501 | Smoke manual: abrir URL em browser privado, banner emerald renderiza + preços riscados |
| `paywall_hit` event Mixpanel (backend) | Aguarda merge PR #501 | Mixpanel: count por `reason={trial_expired, plan_expired, dunning_blocked, dunning_grace_period}` |
| `plan_selected` event Mixpanel (frontend) | Aguarda merge PR #501 | Mixpanel: count por `plan_id` + `has_coupon`. Funnel rate vs `checkout_initiated` |

Hipótese conversion bump Day 16: hoje user chega em `/planos?coupon=TRIAL_COMEBACK_20`, vê preço cheio sem perceber desconto. Com banner + preço riscado, desconto torna-se acionável visualmente. Mensurável via `plan_selected` rate em cohort com `has_coupon=true`.

## Pendente (dono + prazo)

- [ ] **Merge PR #501** — @devops — aguardando CI (Backend Tests + Frontend Tests são os únicos required); auto-merge off, merge manual após checks green
- [ ] **Smoke prod pós-deploy** — @devops — site+api 200 por ≥30min, `/planos?coupon=TRIAL_COMEBACK_20` renderiza badge
- [ ] **24h soak Mixpanel verify** — próxima sessão (2026-04-25+) — queries prontas abaixo
- [ ] **Delete script ad-hoc** `backend/scripts/audit_trial_email_log_smooth_island.py` — próxima sessão (untracked, só existe local)

## 24h soak queries (para próxima sessão)

Mixpanel:
- `paywall_hit` count 24h, segmentado por `reason` — esperamos ver dunning minoritário vs trial_expired maioria
- `plan_selected` count 24h, segmentado por `has_coupon` — cohort com coupon deve ter taxa de conversão para `checkout_initiated` maior que sem coupon
- Funnel: `paywall_hit` → `plan_selected` → `checkout_initiated` → `payment_succeeded` — identificar onde vaza

Sentry:
- Sem spike de exceptions em `analytics_events` ou `plan_auth` pós-deploy

DB:
```sql
SELECT user_id, email_type, sent_at
FROM trial_email_log
WHERE user_id IN (
  '39b32b6f-15ec-4347-b282-ab7da6ea43af',  -- dsl
  '285edd6e-6353-424a-9030-b488c01bcf50'   -- pau
)
ORDER BY sent_at DESC;
```

## Riscos vivos

| Risco | Severidade | Prazo virar incidente |
|-------|-----------|------------------------|
| Mixpanel token não configurado em prod (eventos silenciam) | LOW | Nenhum — `track_funnel_event` silent-fail, não derruba request. Verify em soak query |
| `delivery_status` NULL em `trial_email_log` indica que emails talvez não cheguem (apenas logs de dispatch) | MED | Verificar Resend dashboard na próxima sessão — se delivery rate <90%, abrir story |
| Day 16 expired email não disparou para pau (trial expirou hoje, scheduler corre a cada 2h) | LOW | Cron próxima hora cobre; sem ação necessária |

## Memory updates

| File | Razão |
|------|-------|
| Nenhum nesta sessão | Todos findings são derivable do código (scheduler milestones, signature track_funnel_event, pattern window.mixpanel inline) |

Nada não-derivável descoberto — memory permanece inalterada.

## KPIs da sessão

| Métrica | Alvo | Realizado |
|---------|------|-----------|
| Shipped to prod | ≥1 mudança caminho de receita | PR #501 pronto (aguarda merge + deploy) |
| Incidentes novos | 0 | 0 |
| Tempo em docs | <15% | ~10% (este handoff) |
| Tempo em fix não-prod | <25% | 0% (tudo prod-targeted) |
| Instrumentação adicionada | ≥1 evento funil | 2 eventos (`paywall_hit` + `plan_selected`) |

## Próxima ação prioritária

**@devops aguarda CI green e mergeia #501. Depois smoke prod. Próxima sessão: verify 24h soak Mixpanel.**
