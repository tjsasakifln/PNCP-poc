# /marketing — CMO Advisory Board

**Squad:** `squad-cmo-advisory-board`
**Mode:** Advisory (read-only, never modifies code)
**Focus:** Crescimento orgânico e viral — zero ads

## Activation

```
/marketing <sua pergunta ou solicitação>
```

## What This Does

Convoca o Conselho Consultivo de 53 CMOs e líderes de growth das maiores empresas de tecnologia e SaaS do mundo, organizados em 8 clusters de perspectiva:

1. **SEO & Content Marketing** (7) — SparkToro, Backlinko, Orainti, Zyppy, Amsive, Siege Media, ex-Shopify
2. **Product-Led Growth** (7) — ex-Dropbox/Miro, ProductLed, OpenView, ex-HubSpot, Appcues, ex-GitLab
3. **Community & Ecosystem** (6) — Camunda, Orbit, CMX, Bevy, ex-Reddit, Boast.AI
4. **Viral & Referral Growth** (7) — a16z, GrowthHackers, Hooked, YC, ex-Shopify, ex-Grammarly
5. **B2B & GovTech GTM** (7) — Demandbase, GTM Partners, Refine Labs, Exit Five, Obviously Awesome, 6sense
6. **Brand & Thought Leadership** (6) — Seth Godin, MarketingProfs, ex-Atlassian, Red Antler, SparkToro
7. **Growth Engineering & Analytics** (7) — Reforge, ex-Airbnb, ex-Gojek, ex-Eventbrite, ex-TikTok
8. **Organic Distribution & Social** (6) — VaynerMedia, Justin Welsh, Foundation, ex-HubSpot, Creator Science

## Deliberation Protocol

```
Phase 1: Market & Product Evidence (product analysis + web search 2026)
Phase 2: Strategy Proposals (8 divergent growth strategies)
Phase 3: Strategic Confrontation (4 pairs challenge each other)
Phase 4: Synthesis & Prioritization (resolve objections, max 3 rounds)
Phase 5: Unanimous Consensus (8/8 required)
```

**Output:** Only the final unanimous growth playbook. Internal deliberation is hidden.

## Confrontation Pairs

- **SEO & Content** vs **Growth Engineering** — quality vs velocity
- **Product-Led Growth** vs **B2B & GovTech GTM** — self-serve vs enterprise
- **Community & Ecosystem** vs **Organic Distribution** — depth vs reach
- **Viral & Referral** vs **Brand & Thought Leadership** — mechanics vs narrative

## Execution

When the user invokes `/marketing`, execute this protocol:

1. **Parse the question** from args
2. **Launch parallel evidence agents:**
   - `Explore` agent: Analyze SmartLic product (features, UX, onboarding, pricing)
   - `general-purpose` agent: Web search for 2026 B2G/SaaS organic growth tactics, competitor analysis, market data
3. **Launch deliberation agent** (Opus deep-executor) with all evidence:
   - Simulates 8 cluster perspectives
   - Each cluster proposes organic growth strategy with: tactic, channel, timeline, KPI, effort
   - Runs strategic confrontation across 4 pairs
   - Synthesizes and prioritizes by impact × effort for SmartLic context
   - Outputs ONLY the final consensus playbook
4. **Present consensus** to user in the standard format

## Output Format

```markdown
## Consenso do Conselho de CMOs — Growth Orgânico SmartLic

**Estratégia Central:** [Big idea — recomendação unânime]

**Playbook Priorizado:**
[Estratégias em ordem de prioridade com timeline]

**Quick Wins (0-30 dias):**
- [Ações de impacto imediato com esforço mínimo]

**Fundamentos:**
- [Evidence-backed reasons]

**Evidências de Mercado:**
- [Benchmarks, cases, dados — com fontes/URLs]

**Métricas de Sucesso:**
- [KPIs mensuráveis por estratégia]

**Riscos Reconhecidos:**
- [Trade-offs aceitos conscientemente]

**O que NÃO fazer:**
- [Anti-patterns e armadilhas]

---
_Consenso unânime: 8/8 clusters (53 CMOs)_
```

## Examples

```
/marketing Como crescer a base de usuários de 0 a 1000 sem ads?
/marketing Qual a melhor estratégia de SEO para licitações públicas?
/marketing Como criar um loop viral no SmartLic?
/marketing Qual conteúdo produzir para atrair empresas B2G?
/marketing Como posicionar SmartLic como referência em inteligência de licitações?
/marketing Playbook completo de crescimento orgânico para 2026
/marketing Estratégia de LinkedIn para B2G SaaS no Brasil
/marketing Como transformar usuários trial em evangelistas?
```

## Constraints

- **Zero ads** — todas as estratégias devem ser 100% orgânicas
- **Contexto Brasil** — mercado B2G brasileiro, licitações públicas
- **Pré-revenue** — budget mínimo, priorizar esforço do founder
- **2026** — práticas atualizadas (AI Overviews, zero-click, etc.)
- **Métricas gratuitas** — GA4, Search Console, Mixpanel free tier
