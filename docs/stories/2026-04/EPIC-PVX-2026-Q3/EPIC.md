# EPIC-PVX-2026-Q3 — Product-Value Extraction (Blue Ocean Moats)

**Priority:** P0 — Maior EV pós primeira receita; habilita upsell Pro Plus / Enterprise
**Status:** Ready
**Owner:** @sm (criação) + @po (validação) + @dev (execução) + @devops (push)
**Horizonte:** D+30 a D+120 (2026-05-22 → 2026-08-20)
**Created by:** @sm (River) em 2026-04-22
**Source:** `docs/research/2026-04-22-blue-ocean-product-value-extraction.md` (PR #476)
**ICP:** Vendor-first (B2G empresas que vendem para governo) — decisão user 2026-04-22

---

## Contexto

Blue Ocean research (PR #476) executado pelo squad `/aiox-deep-research` em 2026-04-22. Filtro binário moat-vs-commodity sobre 15 candidatas, validação empírica vs 6 concorrentes (Licitanet, ConectaBR, LicitaGov, ConLicitação, Banco de Preços, Effecti) + 7 fontes setoriais 2026.

Resultado: **3 features moat** identificadas, 2 das quais **virgin blue ocean** (zero concorrentes entregam).

Decisão tomada pelo user 2026-04-22 (sign-off via plan generic-sparrow):
- **Decisão A** = Novos moats primeiro (Contract Expiration Radar + Organ Health Dashboard) — PVX-001 e PVX-002 abrem imediatamente
- **Decisão B** = Vendor-first (não G-Buyer paralelo)
- **CATMAT Price Intelligence Pro** (PVX-004) deferido para fase 2 / track paralelo
- **Competitive Radar CNPJ** (PVX-003) entra como #3 mas com positioning "superior existing feature" (LicitaGov replica parcialmente)

## Thesis

> **"SmartLic tem o único dataset B2G correlacionado do Brasil — 2M+ contratos históricos × 50K editais abertos × classificação setorial LLM × série temporal multi-ano. Isso vira moat de retenção brutal e upsell Enterprise via 3 features que NENHUM concorrente entrega: alerta preditivo de sucessão de contratos (60-120d antes), dashboard de saúde operacional do órgão comprador, e matriz competitiva head-to-head."**

## Stories deste Epic

**Sprint 1 — Virgin Moats Foundation (D+30 a D+60):**

- `STORY-PVX-001` — Contract Expiration Radar v1 (backend MVP, 5 SP)
- `STORY-PVX-002` — Organ Health Dashboard v1 (5 SP — refactor V1 conforme calibração ground truth)

**Sprint 2 — Frontend extension + Competitive (D+60 a D+90):**

- `STORY-PVX-001-v2` — Contract Expiration Radar Frontend (badge + página + UI, 8 SP)
- `STORY-PVX-002-v2` — Organ Health Dashboard Frontend (UI, 8 SP)
- `STORY-PVX-003` — Competitive Radar CNPJ V1 proxy (8 SP, pricing review por @pm separado)

**Sprint 3 — Pricing + Validation (D+90 a D+120):**

- `STORY-PVX-PRICING-001` — Tier Pro Plus / Enterprise definition + Stripe SKU
- `STORY-PVX-CALIBRATION-001` — Ground truth survey + accuracy benchmark V1

## KPIs do Epic

- North Star: **+R$5K MRR incremental** via tier Pro Plus (D+90), **+R$15K MRR** (D+120)
- Adoption: PVX-001 v1 ativo em ≥5 contas internas/beta (D+45)
- Accuracy V1 (PVX-001): ≥50% alertas dentro da janela prevista (±15 dias) — measured 90d post-launch
- NPS PVX-002 score composto: ≥40 entre users com ≥10 órgãos no pipeline
- Guard-rail: zero regressão em features existentes (busca, pipeline, classificação)

## Gate Reviews

- **D+45 (2026-06-06):** PVX-001 v1 ativo em conta interna (`tiago.sasaki@gmail.com`); cron diário emite alertas; email Resend funcional
- **D+60 (2026-06-21):** PVX-002 v1 backend ativo; reliability_score_v1 calculado para top-100 órgãos por volume
- **D+90 (2026-07-21):** Frontend v2 de ambos shippado; pricing tier Pro Plus Stripe SKU criado; ≥3 trial-to-paid conversions atribuídas a moat features (Mixpanel funnel)

## Dependências

- Dataset `supplier_contracts` (~2M rows) + `pncp_raw_bids` (~50K) — **disponível** (DataLake STORY-1.1+)
- ARQ cron infra — **disponível**
- Resend email + template engine — **disponível**
- Mixpanel funnel events (`signup_completed`, `trial_started`, `paywall_hit`, `checkout_completed`) — **disponível** (Wave B trial_started, PR #480 em curso)

## Out-of-scope deste Epic

- G-Buyer persona (decisão B 2026-04-22 = vendor-first definitivo; G-Buyer mínimo em fase 3 condicional ao MRR)
- ML model avançado (V1 é regressão linear + heurística sobre dataset existente)
- Crawl de atas de pregão (V2 do PVX-003)
- Pipeline de extração item-level (PVX-005 spike separado)
- Payment delay metric V2 (depende de crawl ComprasGov v3)

## Stakeholders

- **User/Founder:** Tiago Sasaki (decisão final pricing, validação positioning)
- **Tech:** @architect (data architecture review), @data-engineer (materialized views + cron), @dev (backend + frontend), @qa (test gate), @devops (push + Railway)
- **Product:** @pm (pricing + sequenciamento com EPIC-REVENUE), @po (story validation 10-point), @sm (story creation)

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Accuracy V1 abaixo de 50% (PVX-001) | Médio — feature credibility damage | Disclaimer explícito "preview/beta"; melhoria via ground truth survey D+90 |
| Calibração Organ Health pesos errados (40/30/30) | Médio — false positives/negatives | A/B com pesos 50/25/25 e 30/40/30 em cohort separado D+60 |
| Capacidade @dev conflito com EPIC-REVENUE-2026-Q2 | Alto — atrasa primeiro pagante | Sequenciamento: PVX inicia APÓS gate D+45 EPIC-REVENUE OR @pm dedica 1 @dev exclusivo |
| Concorrente copia em <12 meses | Baixo — moat defensível ≥18m | Speed = primary moat; D+90 ship completo = window de 6m de exclusividade |

---

**Status do Epic:** Ready (post user sign-off 2026-04-22).
**Próximo passo:** @po validate PVX-001 + PVX-002 drafts → @dev abre execução de PVX-001 v1.
