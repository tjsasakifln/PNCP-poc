# *outreach — Cold Outreach Advisory Board

**Squad:** `squad-cold-outreach-board`
**Workflow:** `outreach-advisory-deliberation.yaml`
**Mode:** Advisory (read-only, never sends emails or modifies code)

## Activation

```
/outreach <sua pergunta ou solicitação>
```

## What This Does

Convoca o Conselho Consultivo de 52 Especialistas em Cold Outreach das principais referências mundiais em vendas B2B/B2G, organizados em 8 clusters de perspectiva:

1. **Cold Email & Deliverability** (7) — Alex Berman, Jack Reamer, Will Allred, Sujan Patel, Jesse Ouellette, Robert Indries, Lee Munroe
2. **Copywriting & Sales Messaging** (7) — Joanna Wiebe, Becc Holland, Justin Michael, Laura Belgray, Dave Gerhardt, Dan Kennedy, Chris Voss
3. **LinkedIn & Social Selling** (6) — Morgan J Ingram, Josh Braun, Daniel Disney, Tim Hughes, Jed Mahrle, Jill Konrath
4. **SDR Operations & Cadences** (7) — Trish Bertuzzi, Kyle Coleman, Sam Nelson, KD Dorsey, Lars Nilsson, Tito Bohrt, Jeremey Donovan
5. **Account-Based Marketing** (6) — Sangram Vajre, Jon Miller, Latané Conant, Chris Walker, Brandon Redlinger, Hillary Carpio
6. **B2B SaaS Sales** (7) — Aaron Ross, Mark Roberge, Jason Lemkin, Steli Efti, Kyle Parrish, Elena Verna, Tomasz Tunguz
7. **GovTech & B2G Sales** (6) — Mark Amtower, Bob Lohfeld, Judy Bradt, Steve Charles, Larry Allen, Gustavo Mendes
8. **Data-Driven Prospecting** (6) — Henry Schuck, Max Altschuler, Nicolas Waern, Leela Srinivasan, Tyler Lessard, Tim Zheng

## Deliberation Protocol

```
Phase 1: Evidence Gathering (product context + web search for outreach benchmarks, parallel)
Phase 2: Initial Positions (8 divergent outreach strategies)
Phase 3: Adversarial Confrontation (4 pairs challenge each other)
Phase 4: Synthesis & Iteration (resolve objections, max 3 rounds)
Phase 5: Unanimous Consensus (8/8 required)
```

**Confrontation Pairs:**
- Cold Email vs LinkedIn (channel strategy tension)
- Copywriting vs Data-Driven (art vs science of messaging)
- SDR Ops vs ABM (volume vs precision)
- B2B SaaS vs GovTech (speed vs compliance)

**Output:** Only the final unanimous consensus. Internal deliberation is hidden.

## Execution

When the user invokes `/outreach`, execute this protocol:

1. **Parse the question** from args
2. **Launch parallel evidence agents:**
   - `Explore` agent: Analyze product context, ICP docs, existing outreach materials in the codebase
   - `general-purpose` agent: Web search for 2026 cold outreach best practices, deliverability rules, B2G outreach benchmarks
3. **Launch deliberation agent** (Opus deep-executor) with all evidence:
   - Simulates 8 cluster perspectives
   - Runs adversarial confrontation across 4 pairs
   - Synthesizes until zero objections
   - Outputs ONLY the final consensus
4. **Present consensus** to user in the standard format

## Output Format

```markdown
## Consenso do Conselho de Cold Outreach

**Veredicto:** [Clear outreach recommendation]

**Estrategia:**
- [Channel, messaging, cadence, timing agreed by all]

**Fundamentos:**
- [Evidence-backed reasons with benchmarks]

**Template/Exemplo:**
- [Suggested copy or message structure, if applicable]

**Metricas-Alvo:**
- [Expected KPIs — open rate, reply rate, meeting rate]

**Riscos Reconhecidos:**
- [Accepted trade-offs, LGPD considerations]

**Proximos Passos:**
1. [Priority actions]

---
_Consenso unanime: 8/8 clusters (52 especialistas em cold outreach)_
```

## Examples

```
/outreach Qual a melhor cadencia para prospectar empresas de engenharia que participam de licitacoes?
/outreach Como abordar assessorias de licitacao por cold email?
/outreach Nosso ICP e empresa B2G 50-200 funcionarios — qual canal priorizar?
/outreach Como personalizar outreach usando dados do PNCP/ComprasGov?
/outreach Qual subject line converte melhor para decisores de orgaos publicos?
/outreach Devemos usar cold email ou LinkedIn para atingir consultorias de licitacao?
/outreach Como estruturar uma cadencia de 14 dias para trial conversion?
```
