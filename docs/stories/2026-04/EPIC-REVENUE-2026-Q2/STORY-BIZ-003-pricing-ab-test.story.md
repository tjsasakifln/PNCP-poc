# STORY-BIZ-003: Pricing A/B Test — R$ 297 / R$ 397 / R$ 497

**Priority:** P2 — Otimização, não desbloqueador — só após 20 trials de baseline
**Effort:** S (1 dia setup + 14 dias run + 1 dia análise)
**Squad:** @dev + @data-engineer
**Status:** Ready (condicional: ativar APÓS primeiro pagante fechar + 20 trials de baseline)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Disparar W7-W8 ou depois

---

## Contexto

Preço atual SmartLic Pro: R$ 397/mês (mensal), R$ 357 (semestral), R$ 297 (anual). Definido em STORY-277 (2026-02) via benchmark de mercado, mas sem validação empírica de elasticidade em clientes reais.

Antes de testar pricing, precisamos de:
1. Baseline estatístico (≥20 trials completos com dados de conversão) — **pré-requisito**
2. Primeiro pagante fechado (valida que o produto vende em algum preço) — **pré-requisito**

Sem essas duas condições, testar pricing é ruído sobre ruído — resultado não é acionável.

Quando condições atendidas, este teste responde:

- Elasticidade: conversion rate cai muito a R$ 497? Sobe pouco a R$ 297?
- Sweet spot: qual preço maximiza **MRR** (não conversion isolada)?
- Segmentação: consultorias vs empresas B2G respondem diferente?

**Impacto esperado:** Se otimização de preço lift MRR em +15%, em D+90 significa R$ 450 adicional mensal. Com 90 dias de rodagem = R$ 1.350. ROI alto para 2 dias de esforço.

---

## Acceptance Criteria

### AC1: Pré-requisitos validados
- [ ] ≥1 pagante fechado (verificado em `profiles.plan_type='pro' AND subscription_status='active'`)
- [ ] ≥20 trials concluídos (14 dias rodados) com dados completos em Mixpanel
- [ ] Se pré-requisitos não atendidos, **abortar e aguardar** — não rodar o teste prematuramente

### AC2: Stripe setup com 3 prices
- [ ] Criar 2 novos Stripe Prices para o mesmo Product "SmartLic Pro":
  - `price_pro_297` — R$ 297/mês
  - `price_pro_497` — R$ 497/mês
- [ ] Manter `price_pro_397` existente
- [ ] Todos recurring mensal, BRL
- [ ] Documentar mapping em `docs/runbooks/pricing-ab-test.md`

### AC3: Distribuição A/B/C no backend
- [ ] `backend/services/pricing_experiment.py` novo módulo:
  - Função `get_experiment_variant(user_id: UUID) -> Literal["A", "B", "C"]`
  - Distribuição determinística por hash do `user_id` (consistência entre sessões)
  - 33/33/34 split: A=R$297, B=R$397 (control), C=R$497
- [ ] Variant é decidido no signup e persistido em `profiles.pricing_variant` (migration)

### AC4: Frontend /planos mostra preço baseado em variant
- [ ] `frontend/app/planos/page.tsx` busca variant via `/v1/user/pricing-variant`
- [ ] Renderiza preço mensal conforme variant (297/397/497)
- [ ] Anual mantém desconto % (×9 = 2.673 / 3.573 / 4.473) — não testar anual isoladamente (confounding)
- [ ] Checkout Stripe usa o Price correto conforme variant

### AC5: Feature flag master kill-switch
- [ ] Env var `PRICING_EXPERIMENT_ENABLED=true|false`
- [ ] Se `false`, todos os users veem R$ 397 (revert safe)
- [ ] Documentado em runbook

### AC6: Dashboard de acompanhamento
- [ ] `docs/growth/reports/pricing-ab-daily.md` atualizado diariamente (14 dias)
- [ ] Métricas por variant:
  - Trials iniciados
  - Signups com cartão capturado (se CONV-003 live)
  - Conversion rate trial→paid
  - MRR atribuído
  - Expected MRR = conversion_rate × preço × trials
- [ ] Teste estatístico: significância com n=20+/variant (power calculation antes — pode precisar 30+)

### AC7: Relatório final + decisão
- [ ] Ao fim de 14 dias, `docs/growth/reports/pricing-ab-final.md`
- [ ] Decisão:
  - Se Variant A (R$ 297) tem **MRR projetado ≥ 20% acima** de B: adotar R$ 297 como default
  - Se Variant C (R$ 497) tem **MRR projetado ≥ 10% acima** de B: adotar R$ 497
  - Senão: manter R$ 397 (control vence)
- [ ] Se inconclusivo (p-value > 0.1): rodar +14 dias

### AC8: Rollback plan
- [ ] Se variant A ou C gera rate alto de churn pós-1º charge (>20%) vs control: rollback imediato
- [ ] Rollback steps documentados em runbook

---

## Arquivos

**Backend (novos + modificados):**
- `backend/services/pricing_experiment.py` (novo)
- `backend/routes/user.py` (modificar — endpoint `/user/pricing-variant`)
- `backend/config/features.py` (adicionar `PRICING_EXPERIMENT_ENABLED`)

**Frontend (modificar):**
- `frontend/app/planos/page.tsx` (respeitar variant)
- `frontend/app/planos/components/PlanCard.tsx` (receber preço via prop)

**Database:**
- `supabase/migrations/20260510000001_add_pricing_variant.sql` (nova coluna)
- `supabase/migrations/20260510000001_add_pricing_variant.down.sql`

**Documentação:**
- `docs/runbooks/pricing-ab-test.md`
- `docs/growth/reports/pricing-ab-daily.md` (gerados durante)
- `docs/growth/reports/pricing-ab-final.md` (gerado ao fim)

---

## Riscos e Mitigações

**Risco 1:** Baixa amostra gera falso positivo/negativo
- **Mitigação:** Power calculation antes (n ≥ 30/variant para detectar lift de 20% com p<0.05); se inconclusivo, rodar +14 dias

**Risco 2:** Diferença sazonal confunde (B2G tem ciclos de fim de mês)
- **Mitigação:** 14 dias cobrem ciclos típicos. Se coincidir com dezembro/janeiro, re-avaliar.

**Risco 3:** Usuários mudam de browser (logged-out) e veem preços diferentes — percepção de preço inconsistente
- **Mitigação:** Variant baseado em user_id autenticado, não em anon session. Logged-out sempre vê R$ 397.

**Risco 4:** Existing users veem preço mudado, confusão
- **Mitigação:** Variant só aplica a NEW signups pós-deploy. Existing mantém legacy pricing.

---

## Definition of Done

- [ ] AC1-AC8 todos marcados `[x]`
- [ ] Pré-requisitos (AC1) validados e documentados
- [ ] 14 dias de teste rodados com dados completos
- [ ] Relatório final commitado com decisão
- [ ] Se adotar novo preço: STORY de migration criada para ajustar preço default
- [ ] PR mergeado, CI verde

---

## Dev Notes

**Power calculation (n mínimo por variant):**
- Baseline conversion rate: 3% (atual SmartLic)
- Lift mínimo detectável: 20% (3% → 3.6%)
- Significância: p<0.05
- Power: 0.8
- Resultado: n ≈ 300 trials/variant — **isso é muito para nosso volume**
- **Alternativa pragmática:** rodar 30/variant e medir **MRR projetado** (mesmo com p-value alto, direção do efeito é informativa se lift >30%)

**Regra de ouro:** se só 20 trials/variant e diferença <50% entre variants, resultado é inconclusivo — adotar heurística "default vence" e revisitar em Q3.

---

## File List

_(populado pelo @dev durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Condicional: pré-requisitos em AC1. |
