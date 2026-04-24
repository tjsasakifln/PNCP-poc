# EPIC-GROWTH-VIRAL-2026-Q3: On-Page CAC-Zero Viral Growth

**Priority:** P0 — crescimento exponencial sem dependência de paid ads
**Status:** Draft
**Owner:** @pm (Morgan) + @dev + @ux-design-expert + @devops
**Sprint:** Q3 2026 (Sprint 1-4 — ~2 meses)
**Meta:** K-factor B2B ≥0.20, 30% novos signups via viral loops, -40% CAC blended em 6 meses.

---

## Contexto Estratégico

SmartLic v0.5 em produção tem 80-90% de cobertura nos pilares on-page fundamentais (landing, signup, onboarding, trial mechanics, SEO programático com 10k+ URLs, analytics Mixpanel/Clarity, paywall, email sequences). Epics em execução: `EPIC-CONVERSION-2026-04`, `EPIC-SEO-ORGANIC-2026-04`, `EPIC-MON-SCHEMA/REPORTS/SEO/API/AI-2026-04`, `BACKLOG-MKT-BLOG-GROWTH`.

**Gap real:** Layer "viral loop engineered" inexistente. Backend de referral + share já existe (`/v1/referral/*`, `/v1/share`, página `/analise/[hash]`), mas UI de sharing, replay público, embed widgets, waitlist scarcity, habit loops, collaboration seats e gamification não estão implementados nem planejados.

**Insights dos cases analisados (web research 2026-04-24):**

| Case | Mecânica | Resultado |
|------|----------|-----------|
| **Manus** | Waitlist scarcity + replay público shareable + invite codes | 500k waitlist orgânico, invite codes vendidos secundário, Discord 138k/dias |
| **Lovable** | "Edit with Lovable" watermark em toda página pública + gallery gamificada com upvotes | Hundreds of apps shared/week, viral gallery drove signups (pivotou April/2026 após incidente segurança) |
| **ChatGPT** | Screenshot virality + share conversation link | 100M MAU em 2 meses, zero ad spend |
| **Loom/Calendly/Figma** | "Todo output é anúncio" (Loom) + collaboration-driven recipient sees value (Figma/Calendly) | K-factor B2B ≥0.20 sustentado |
| **Referral B2B** (Dropbox/Calendly) | Dual-sided rewards + tiered | 15-25% volume novos clientes, 40-60% CAC menor |

**Decisão learning April/2026:** Lovable incidente exposição pública → pseudonimização default + opt-in explícito para dados sensíveis é **mandatório** em B2G (CNPJ + estratégia competitiva + LGPD).

---

## Objetivos Mensuráveis

| KPI | Baseline (2026-04) | Meta 90d | Meta 180d |
|-----|-------------------|----------|-----------|
| K-factor (signups via share / active users) | ~0 | 0.10 | ≥0.20 |
| Novos signups via viral loops | 0% | 15% | 30% |
| Signups via team invite | 0% | 5% | ≥15% |
| Trial → Paid conversion rate | ~3% | 5% | ≥8% |
| DAU/MAU ratio | ? | 22% | ≥30% |
| Blended CAC (efetivo) | baseline | -20% | -40% |
| Early-access waitlist signups/mês | 0 | 200 | 500+ |
| Orgânico signups via lead magnet | 0 | 80 | 200+/mês |

---

## Stories do Epic

### Wave 0 — Infra Experimental (BLOCKER)

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-001](GV-001-ab-testing-framework.md) | P0 | M (8 SP) | @dev + @devops | Draft | A/B testing framework + funnel auto-tracking |

### Wave 1 — Viral Loops B2G Adaptados

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-002](GV-002-watermark-pseudonimizacao-analise.md) | P0 | S (5 SP) | @dev + @ux | Draft | "Powered by SmartLic" watermark + pseudonimização em `/analise/[hash]` |
| [GV-003](GV-003-analysis-replay-timeline.md) | P0 | M (8 SP) | @dev | Draft | Analysis Replay UI (Manus-inspired) |
| [GV-004](GV-004-embed-widget-viabilidade.md) | P1 | L (13 SP) | @dev + @devops | Draft | Embed widget `<iframe>/<script>` para sites terceiros |
| [GV-005](GV-005-propose-to-colleague-share.md) | P0 | S (5 SP) | @dev | Draft | "Enviar ao colega" contextual share no resultado de busca |

### Wave 2 — Waitlist / Scarcity + FOMO

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-006](GV-006-early-access-waitlist.md) | P1 | M (8 SP) | @dev + @pm | Draft | Early Access waitlist com invite codes (API B2B, GPT-5, Radar ML) |
| [GV-007](GV-007-trending-analyses-gallery.md) | P1 | M (8 SP) | @dev + @data-engineer | Draft | Public `/trending/analises` gallery (top 20/semana) |
| [GV-008](GV-008-live-impact-ticker.md) | P2 | XS (3 SP) | @dev | Draft | Live impact ticker landing (agregado 24h) |

### Wave 3 — Habit Loops + Gamification

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-009](GV-009-licitacao-do-dia-daily-matching.md) | P1 | M (8 SP) | @dev + @data-engineer | Draft | "Licitação do Dia" daily personalized matching |
| [GV-010](GV-010-badges-certificate-shareable.md) | P2 | M (8 SP) | @dev + @ux | Draft | Badges + LinkedIn-shareable certificate |
| [GV-011](GV-011-weekly-wins-digest.md) | P2 | S (5 SP) | @dev | Draft | Weekly Wins digest público opt-in |
| [GV-012](GV-012-post-win-celebration.md) | P1 | S (5 SP) | @dev + @ux | Draft | Post-win celebration modal + shareable card |

### Wave 4 — Collaboration Seats

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-013](GV-013-team-invites-bonus-tiered.md) | P1 | M (8 SP) | @dev + @data-engineer | Draft | Team invites com bonus tiered (workspaces) |
| [GV-014](GV-014-consultoria-client-readonly.md) | P1 | L (13 SP) | @dev + @ux | Draft | Consultoria → Cliente read-only dashboard |
| [GV-015](GV-015-concorrente-ganhou-alert.md) | P2 | M (8 SP) | @dev + @data-engineer | Draft | "Concorrente ganhou" alert + compare CTA |

### Wave 5 — Monetização Boost

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-016](GV-016-usage-milestone-roi-variant.md) | P1 | XS (3 SP) | @dev | Draft | Usage milestone ROI variant (extends STORY-312) |
| [GV-017](GV-017-exit-intent-trial-offer.md) | P1 | XS (3 SP) | @dev | Draft | Exit-intent modal D14 com countdown |
| [GV-018](GV-018-referral-tiered-social-widget.md) | P0 | S (5 SP) | @dev | Draft | Referral tiered + social widget (extends STORY-289) |

### Wave 6 — Engagement Content

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| [GV-019](GV-019-sectorial-benchmarking-lead-magnet.md) | P2 | M (8 SP) | @dev + @data-engineer | Draft | Sectorial benchmarking público + PDF gated |
| [GV-020](GV-020-roi-calculator-embed.md) | P2 | S (5 SP) | @dev | Draft | ROI calculator embed (extends STORY-432) |
| [GV-021](GV-021-churn-winback-campaign.md) | P1 | S (5 SP) | @dev | Draft | Churn win-back campaign (D+7/30/90) |

**Total:** 21 stories, ~142 SP

---

## Ordem de Execução (4 Sprints)

| Sprint | Stories | Total SP | Foco |
|--------|---------|----------|------|
| **1** | GV-001, 002, 005, 018 | 26 | Infra + viral loops base + referral UI |
| **2** | GV-003, 006, 009, 012, 013, 017, 021 | 42 | Replay + waitlist + daily matching + winback |
| **3** | GV-004, 007, 010, 014, 016 | 45 | Embed + trending + badges + consultoria |
| **4** | GV-008, 011, 015, 019, 020 | 29 | Ticker + wins digest + concorrente + content |

---

## Dependências

### Externas (stories existentes que precisam estar Done)

- **STORY-289** (Referral Program & Lead Magnets, TODO) → **bloqueia GV-018**. Precisa avançar antes do Sprint 1.
- **STORY-312** (Trial Upsell CTAs, Done) → **pré-requisito de GV-016** (extensão).
- **STORY-432** (Calculadora embeddável, InProgress) → **pré-requisito de GV-020** (extensão).
- **STORY-449** (Referral toast pós-busca, Done) → GV-018 integra, não sobrescreve.

### Internas (DAG do epic)

```
GV-001 (infra)
  └─ BLOQUEIA medição de todas abaixo

GV-002 (watermark) ← blocker para GV-003, GV-004, GV-010, GV-011, GV-012, GV-014
GV-013 (workspaces) ← blocker para GV-014
GV-012 (post-win modal) ← blocker para GV-011
```

### Reconciliação com epics paralelos

- Não sobrepõe `EPIC-CONVERSION-2026-04`: complementa com novas variants.
- Complementa `EPIC-SEO-ORGANIC-2026-04`: GV-007/019/020 adicionam páginas públicas indexáveis.
- Não conflita com `EPIC-MON-*`: stories desse epic são camadas pagas separadas.

---

## Considerações B2G Específicas

1. **LGPD + sensibilidade competitiva:** toda story com dados de terceiros (CNPJ concorrente, share links) usa pseudonimização default + opt-in explícito. Revisão jurídica obrigatória pré-broadcast em GV-015.
2. **Setor conservador:** empresas B2G cautelosas com exposição. Public galleries (GV-007, GV-011) = opt-in forte + anonimização de empresa.
3. **Compliance contratual:** GV-014 (Consultoria→Cliente) exige RLS workspaces impedindo cliente ver dados de outros clientes.
4. **Concorrência assimétrica:** GV-015 subject line A/B mandatório — copy sensível.

---

## Métricas de Acompanhamento (Dashboard)

- **Grafana/Mixpanel `growth-epic-q3`:** K-factor rolling 7d, signups por source, DAU/MAU, trial conversion, revenue per signup, share events funnel
- **Sentry alert:** K-factor queda >20% WoW → pager
- **Prometheus counters:** `smartlic_referral_*`, `smartlic_share_*`, `smartlic_waitlist_*`, `smartlic_winback_*`

---

## Riscos

| Risco | Severidade | Mitigação |
|-------|:----------:|-----------|
| Pseudonimização insuficiente expõe CNPJ cliente | Alta | Revisão jurídica + pen test antes GV-002 deploy |
| Consultoria plan sem users pagantes | Média | GV-014 deprioritizado se <3 pagantes; pivotar para free users B2B |
| Subject line "concorrente ganhou" gera backlash | Alta | A/B mandatório; opt-out 1-click; feedback loop Sentry |
| Waitlist vazio (nenhum uso) | Média | Pre-validar demand via landing MVP antes de construir backend completo |
| Referral gaming (self-invite) | Média | Reward on_signup_activation (não on_invite) + CNPJ uniqueness check |

---

## Stories Explicitamente Rejeitadas

- **Public-by-default projects (Lovable pré-abril 2026):** incidente + setor B2G = risco inaceitável
- **Scraping redes sociais para lead gen:** fora escopo on-page + compliance
- **SMS/WhatsApp outbound proativo:** distraction — foco inbound
- **Webinars ao vivo:** ops não on-page
- **Open API livre sem cadastro:** abuso + anti-monetização (EPIC-MON-API já cobre)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm (River) | Epic criado — resposta a pedido de stories on-page CAC-zero; web research Manus/Lovable/ChatGPT; reconciliado com STORY-289/312/449/432 (advisor pass) |
