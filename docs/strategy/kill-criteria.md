# Kill-Criteria — SmartLic (Plano Board v2.0)

**Data:** 2026-04-20 | **Horizonte:** D+1 a D+90 (→ 2026-07-18) | **North Star:** MRR R$ 0 → R$ 3.000+

---

## Propósito

Documento de triggers **executáveis** para os gates de decisão D+30 / D+45 / D+60 / D+90 definidos no plano board v2.0 (`/home/tjsasakifln/.claude/plans/considere-em-conjunto-o-silly-peacock.md`). Cada gate tem condição medível, comando SQL/API para medir, e ação específica a tomar.

**Regra de ouro:** falhar um gate NÃO é defeito do plano — é sinal para **pivotar, desescalar ou dobrar apostas** conforme as regras abaixo. Gate cego é mau management.

**Contexto financeiro:** custo operacional ~R$ 500/mês (Railway + Supabase + Stripe + OpenAI). Runway alvo >6 meses em D+90. Alerta se runway < 10 semanas.

---

## Gate D+30 (2026-05-19) — Pulso de tração inicial

**Pergunta:** O TIER 1 receita (CONV-003, B2G-001) está destravando trials e conversa?

### Medição

```bash
# 1. Stories TIER 1 shippadas
gh pr list --state merged --search "CONV-003 OR B2G-001" --search 'created:>2026-04-19' --limit 10

# 2. CI verde consecutivos
gh run list --workflow "Backend Tests (PR Gate)" --branch main --limit 10 --json conclusion \
  --jq '[.[] | .conclusion] | map(select(. == "success")) | length'

# 3. Trials ativos (Supabase)
# SELECT COUNT(*) FROM profiles WHERE subscription_status='trialing' AND trial_started_at > NOW() - interval '30 days';

# 4. Hotfixes incident merged
gh pr list --state merged --search "STORY-41 OR STORY-42" --limit 30 --json number,title
```

### Verdict matrix

| Resultado | Ação |
|-----------|------|
| **PASS** (stories TIER 1 em InReview+; CI 5+ verdes; 8+ trials ativos; 17 hotfixes merged) | Seguir plano — nada muda |
| **WARN** (1 das TIER 1 em InProgress; CI 2-4 verdes; 3-7 trials; ≥10 hotfixes merged) | Reallocar +10% para stabilização, reduzir 5% de SEO ofensivo |
| **FAIL** (0 TIER 1 started; CI 0 verdes; ≤2 trials; <5 hotfixes) | **Disparar STORY-OPS-001 imediatamente** (entrevistas cohort); halt feature work novo |

### Ações automáticas em FAIL

- Disparar `STORY-OPS-001` (trial cohort interviews — 5 × 30min) → síntese em 48h → top-3 insights viram stories semana seguinte
- Pausar outreach B2G novo (manter só follow-ups) → bandwidth founder para entrevistas
- Escrever hipóteses de pivot em `docs/strategy/pivot-hypotheses.md` (kill reborn)

---

## Gate D+45 (2026-06-03) — Primeiro pagante esperado

**Pergunta:** O funnel está convertendo? Existe receita documentada?

### Medição

```sql
-- Primeiro pagante Stripe
SELECT id, email, plan_type, subscription_status, trial_started_at,
       subscription_started_at, price_monthly_brl
FROM profiles
WHERE subscription_status = 'active'
  AND plan_type IN ('pro', 'consultoria')
  AND subscription_started_at IS NOT NULL
ORDER BY subscription_started_at ASC
LIMIT 5;

-- MRR atual
SELECT SUM(price_monthly_brl) AS mrr_brl,
       COUNT(*) AS paying_customers
FROM profiles
WHERE subscription_status = 'active'
  AND plan_type IN ('pro', 'consultoria');
```

```bash
# Mixpanel funnel signup → paid (validar numerador + denominador visíveis)
# Conversion rate = (paying / trials_started_30d) * 100
```

### Verdict matrix

| Resultado | Ação |
|-----------|------|
| **PASS** (1+ pagante; MRR ≥ R$ 397; CI 8+ verdes; 15+ trials) | **Celebrar + swap:** 80% stabilização, 20% crescimento; disparar `STORY-BIZ-003` (pricing A/B) se 20+ trials de baseline |
| **WARN** (zero pagante mas 3+ em checkout progression — `checkout_started` Mixpanel) | Hotfix no funnel específico (qual step perde?). Outreach continua no mesmo ritmo. |
| **FAIL** (zero pagante, zero checkout progression) | **Decisão de pivot documentada** em `docs/strategy/pivot-hypotheses.md`. Hipóteses a testar: (a) preço muito alto, (b) nicho errado (ampliar B2G além de consultorias), (c) produto não entrega o Jobs-To-Be-Done declarado |

### Ações automáticas em FAIL

- Halt STORY-GROWTH-001 Google Ads smoke test se ainda não disparou (CAC alvo ≤ R$ 500 inviável sem conversão base)
- Considerar pivot: B2C consultoria individual? B2B agregador de consultorias? Produto gratuito freemium?
- Timeline: decisão pivot máximo D+52 para preservar runway

---

## Gate D+60 (2026-06-18) — Escala da primeira cohort

**Pergunta:** Os primeiros pagantes ficaram? A máquina outreach+trial escala?

### Medição

```sql
-- Churn nos primeiros 30 dias
SELECT
  COUNT(*) FILTER (WHERE subscription_status = 'canceled') AS churned,
  COUNT(*) FILTER (WHERE subscription_status = 'active') AS retained,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE subscription_status = 'canceled')
    / NULLIF(COUNT(*) FILTER (WHERE subscription_started_at IS NOT NULL), 0),
    1
  ) AS churn_pct
FROM profiles
WHERE subscription_started_at BETWEEN NOW() - interval '60 days' AND NOW() - interval '30 days';

-- MRR total
SELECT SUM(price_monthly_brl) AS mrr_brl, COUNT(*) AS paying FROM profiles WHERE subscription_status='active';
```

### Verdict matrix

| Resultado | Ação |
|-----------|------|
| **PASS** (3+ pagantes; MRR R$ 1.200+; churn ≤ 15%; CI 10 runs verdes — **EPIC-CI-GREEN encerra**; branch protection re-enforce) | Escalar outreach wave 2 (60 contatos/mês vs 60 wave 1); publicar Observatório relatório mensal (STORY-431) |
| **WARN** (1-2 pagantes, MRR R$ 397-800; churn 15-30%) | Investigar churn drivers (entrevista sair — "churn interview") → ajustar produto |
| **FAIL** (0-1 pagante; churn >50%) | Produto ainda não tem PMF — voltar para entrevistas + iteração produto. Halt SEO ofensivo, halt outreach novo |

---

## Gate D+90 (2026-07-18) — Runway positivo?

**Pergunta:** R$ 3.000 MRR é destino ou apenas bridge?

### Medição

```sql
-- MRR final + ARR projetado
SELECT
  SUM(price_monthly_brl) AS mrr_brl,
  SUM(price_monthly_brl) * 12 AS arr_projected_brl,
  COUNT(*) AS paying_customers,
  AVG(price_monthly_brl) AS arpu_brl
FROM profiles
WHERE subscription_status = 'active';

-- Cohort retention (30d, 60d, 90d)
SELECT
  CASE
    WHEN subscription_started_at > NOW() - interval '30 days' THEN 'd30'
    WHEN subscription_started_at > NOW() - interval '60 days' THEN 'd60'
    WHEN subscription_started_at > NOW() - interval '90 days' THEN 'd90'
  END AS cohort,
  COUNT(*) FILTER (WHERE subscription_status = 'active') AS retained,
  COUNT(*) FILTER (WHERE subscription_status = 'canceled') AS churned
FROM profiles
WHERE subscription_started_at > NOW() - interval '90 days'
GROUP BY 1;
```

### Verdict matrix

| MRR | Runway | Ação |
|-----|--------|------|
| **MRR ≥ R$ 3.000** | >6 meses | **PASS:** seguir para D+180 target R$ 8k MRR (break-even pró-labore mínimo) |
| **MRR R$ 1.500-3.000** | 3-6 meses | **WARN:** suficiente para bridge 2026-Q3 — pedir review financeiro (founder pessoal); manter discipline TIER 1 |
| **MRR < R$ 1.500** | <3 meses | **FAIL:** pivot significativo ou busca de funding de terceiros. Plano bridge expira. Escrever documento "SmartLic year-2 options". |

---

## Swap rules automáticos (pré-gate)

Regras que disparam SEM esperar gate:

- **Runway cai < 10 semanas** → rebalancear allocation para 20% estabilização / 50% receita direta / 20% cartão-Stripe / 5% SEO / 5% ritual
- **1º pagante fecha antes de D+30** → pausar SEO ofensivo, dobrar B2G (15 → 25 contatos/semana)
- **CI vermelho > 5 runs pós-D+30** → halt stories novas, foco 100% BACKEND-SWEEP
- **3+ trials ativos mas zero conversão em 14 dias** → pausar TUDO, disparar STORY-OPS-001 (entrevistas)
- **Wave B2G response rate < 5% em 30 dias** → iterar template v2 (educacional em vez de vendedor); se ainda < 5% em 60 dias, kill B2G e escalar paid (GROWTH-001)

---

## Commitments desta doc

- Este doc é revisado no início de cada gate check
- Qualquer FAIL aciona docs adicional em `docs/strategy/` (ex: `pivot-hypotheses.md`, `kill-decisions-YYYY-MM.md`)
- Founder compromete: medir, não dar desculpa; seguir regras escritas; não inventar gates novos sob stress

---

## Verification history

| Data | Gate | Resultado | Ação tomada | Nota |
|------|------|-----------|-------------|------|
| — | — | — | — | Preencher à medida que gates disparam |
