# EPIC-REVENUE-2026-Q2 — Primeiro Pagante em 45 dias, R$3k MRR em 90 dias

**Priority:** P0 — Receita direta, maior EV do plano 90d
**Status:** Ready
**Owner:** @sm (criação) + @po (validação) + @dev (execução) + @devops (push)
**Horizonte:** D+1 a D+90 (2026-04-19 → 2026-07-18)
**Created by:** @sm (River) em 2026-04-19

---

## Contexto

Auditoria de codebase em 2026-04-19 confirmou que:

- **EPIC-CONVERSION-2026-04 está 100% Done** (10 stories: 440–449) — UX de conversão visual e email nurturing implementados
- **EPIC-CI-GREEN Frontend está 95% Done** (19/20)
- **Incident hotfixes (412–429)** estão 17/18 em InReview aguardando merge
- **SEO defensivo (430/436/439) Done**, ofensivo (431/432/433) InProgress

Mas MRR continua R$ 0. Logo, o gargalo **nunca foi** UX de conversão — é:

1. Poucos leads qualificados entram no funil (aquisição outbound ausente)
2. Trials não têm skin-in-the-game (cartão não é coletado na entrada)
3. Não existe mecanismo de fechamento para os primeiros clientes (founding)
4. Plano Consultoria R$997 não é upsell visível para CNAEs de consultoria

Este epic ataca os 4 pontos diretamente + prevê instrumentos de validação condicionais caso TIER 1 não converta em 45 dias.

## Thesis

> **"Estabilização + UX já estão feitas. Falta trazer leads qualificados, capturar commitment via cartão, e ter mecânicas de fechamento. Essas 4 peças + 3 instrumentos de validação são suficientes para primeiro pagante em 4-6 semanas e R$3k MRR em 90 dias."**

## Stories deste Epic

**Sprint 1 — Wave receita (D+1 a D+17):**

- `STORY-CONV-003` — Cartão obrigatório no trial via Stripe (P0, M)
- `STORY-B2G-001` — Outreach via DataLake aos primeiros 15 (P0, ongoing)
- `STORY-BIZ-001` — Founding customer Stripe coupon + landing (P0, XS)
- `STORY-BIZ-002` — Upsell plano Consultoria para CNAEs 70.2/74.9/82.9 (P1, S)

**Sprint 2 — Validação condicional (disparar pós gate D+30 ou D+45):**

- `STORY-OPS-001` — Trial cohort interviews 5× (P1, S)
- `STORY-GROWTH-001` — Paid acquisition smoke test Google Ads (P1, S)
- `STORY-BIZ-003` — Pricing A/B test R$297/R$397/R$497 (P2, S)

## KPIs do Epic

- North Star: MRR R$ 0 → R$ 397 (D+45) → R$ 3.000 (D+90)
- Input: 15 contatos outbound/semana × 6 semanas = 90 contatos
- Input: ≥40% dos novos signups capturados com cartão (D+45)
- Input: ≥1 pagante fechado até D+45
- Guard-rail: CI verde por 10 runs consecutivos até D+60

## Gate Reviews

- **D+30 (2026-05-19):** TIER 1 stories em InReview ou Done; 5+ runs CI verdes; 8+ trials ativos
- **D+45 (2026-06-03):** Primeiro pagante fechado; MRR ≥ R$ 397
- **D+60 (2026-06-18):** 3+ pagantes; CI 10 runs verdes mantido
- **D+90 (2026-07-18):** MRR ≥ R$ 3.000; 6+ pagantes; runway > 6 meses

Kill criteria documentados em `docs/strategy/kill-criteria.md` (criado como parte de TIER 0 do plano).

## Dependências

- EPIC-CONVERSION-2026-04 Done (instrumentação Mixpanel já existe)
- EPIC-CI-GREEN-MAIN-2026Q2 com CI estável (não bloqueante, mas reduz risco de deploy)
- Stripe live mode config + webhooks funcionais (pré-existente)
- DataLake com ≥50k licitações + 2M contratos (commit 184109f0 confirmou primary query path)

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-19 | @sm (River) | Epic criado com base em auditoria de codebase + plano Board v1.0 (2026-04-19). Todas 7 stories criadas Ready. |
