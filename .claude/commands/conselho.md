# *conselho — CTO Advisory Board

**Squad:** `squad-cto-advisory-board`
**Workflow:** `cto-advisory-deliberation.yaml`
**Mode:** Advisory (read-only, never modifies code)

## Activation

```
/conselho <sua pergunta ou solicitação>
```

## What This Does

Convoca o Conselho Consultivo de 53 CTOs das maiores empresas de tecnologia do mundo, organizados em 8 clusters de perspectiva:

1. **Scale & Infra** (7) — AWS, Google, Azure, Cloudflare, Fastly, Confluent, Oxide
2. **DevEx & Platform** (7) — Stripe, Vercel, GitHub, GitLab, Twilio, Akita, Vanta
3. **Data & AI/ML** (7) — OpenAI, Databricks, Snowflake, Hugging Face, AWS AI, Stability, Anthropic
4. **Security & SRE** (7) — CrowdStrike, Datadog, PagerDuty, Snyk, Elastic, Honeycomb, Verica
5. **Product Engineering** (7) — Spotify, Airbnb, Uber, Netflix, Slack, Instagram, Webflow
6. **Enterprise SaaS** (6) — Salesforce, SAP, ServiceNow, Atlassian, Workday, DevRev
7. **Fintech & GovTech** (6) — Nubank, Stripe, Square, Brex, VTEX
8. **Startup Velocity** (6) — YC, Kelsey Hightower, HashiCorp, DHH, Pieter Levels

## Deliberation Protocol

```
Phase 1: Evidence Gathering (code + web search, parallel)
Phase 2: Initial Positions (8 divergent positions)
Phase 3: Adversarial Confrontation (4 pairs challenge each other)
Phase 4: Synthesis & Iteration (resolve objections, max 3 rounds)
Phase 5: Unanimous Consensus (8/8 required)
```

**Output:** Only the final unanimous consensus. Internal deliberation is hidden.

## Execution

When the user invokes `/conselho`, execute this protocol:

1. **Parse the question** from args
2. **Launch parallel evidence agents:**
   - `Explore` agent: Deep codebase analysis relevant to the question
   - `general-purpose` agent: Web search for 2026 best practices
3. **Launch deliberation agent** (Opus deep-executor) with all evidence:
   - Simulates 8 cluster perspectives
   - Runs adversarial confrontation across 4 pairs
   - Synthesizes until zero objections
   - Outputs ONLY the final consensus
4. **Present consensus** to user in the standard format

## Output Format

```markdown
## Consenso do Conselho de CTOs

**Veredicto:** [Clear recommendation]

**Fundamentos:**
- [Evidence-backed reasons]

**Evidências no Código:**
- `file:line` — [finding]

**Referências Externas:**
- [Source + URL]

**Riscos Reconhecidos:**
- [Accepted trade-offs]

**Próximos Passos:**
1. [Priority actions]

---
_Consenso unânime: 8/8 clusters (53 CTOs)_
```

## Examples

```
/conselho Devo migrar de REST para GraphQL?
/conselho Nossa arquitetura de cache está adequada para 1000 usuários?
/conselho Qual a melhor estratégia para reduzir o tempo de busca de 30s para 5s?
/conselho O pipeline de busca multi-fonte é resiliente o suficiente para produção?
/conselho Devemos adotar microserviços ou manter o monolito?
```
