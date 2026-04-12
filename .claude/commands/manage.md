# /manage — CEO Advisory Board

**Squad:** `squad-ceo-advisory-board`
**Workflow:** `ceo-advisory-deliberation.yaml`
**Mode:** Advisory (read-only, never modifies code)

## Activation

```
/manage <sua pergunta ou solicitacao estrategica>
```

## What This Does

Convoca o Conselho de 53 CEOs organizados em 8 clusters de perspectiva estratégica, com foco em **monetização acelerada, ganho de escala e posicionamento de outlier absoluto** — sempre considerando a realidade de um founder solo que construiu a plataforma integralmente via AI Pair Programming, com 7 anos de experiência como servidor público estadual em Santa Catarina.

O conselho entende que benchmarks são ponto de partida, não destino. O objetivo é criar novos benchmarks.

### 8 Clusters de CEOs (53 ao total)

1. **Bootstrap & Profitability-First** (7) — DHH/37signals, Pieter Levels/Nomad List, Sahil Lavingia/Gumroad, Nathan Barry/ConvertKit, Jason Fried/Basecamp, Rob Walling/TinySeed, Rand Fishkin/SparkToro
2. **GovTech & Regulated Markets** (7) — Alex Karp/Palantir, Rodrigo Borges/Jusbrasil, Aneesh Chopra/ex-US CTO, Ilan Paretsky/Govini, Bernardo Carneiro/Neoway, Todd Park/ex-US Federal CTO, Diego Gualda
3. **Category Creator & Positioning** (7) — April Dunford/Obviously Awesome, Aaron Levie/Box, Tien Tzuo/Zuora, Geoffrey Moore/Crossing the Chasm, Scott Brinker/MarTech, Richard Socher/You.com, Dave Gray/XPLANE
4. **Product-Led Growth & Self-Serve** (7) — Tobi Lutke/Shopify (early), Wes Bush/ProductLed, Elena Verna/ex-Miro, Leah Tharin, Todd Olson/Pendo, Blake Bartlett/OpenView, Kieran Flanagan/ex-HubSpot
5. **LATAM & Brazil Outlier** (7) — David Vélez/Nubank, Sergio Furio/Creditas, Guilherme Benchimol/XP Investimentos, Cristina Junqueira/Nubank, Florian Hagenbuch/Loft, Eduardo Marques/Sólides, Pierre Schurmann/Bossa Invest
6. **Capital Efficiency & Lean Scale** (7) — Ben Chestnut/Mailchimp, Paul Jarvis/Company of One, Wade Foster/Zapier, Tyler Tringas/Earnest Capital, Hiten Shah/FYI, Patrick McKenzie/patio11, Jason Cohen/WP Engine founder
7. **B2B Sales-Led & Pipeline Scale** (7) — Jason Lemkin/SaaStr, Aaron Ross/Predictable Revenue, Mark Roberge/ex-HubSpot CRO, Steli Efti/Close CRM, Jacco van der Kooij/Winning by Design, Bob Tinker/MobileIron, Kyle Parrish
8. **Contrarian & Outlier Bets** (7) — Peter Thiel/Palantir (Zero to One), Reed Hastings/Netflix, Sam Altman/OpenAI, John Collison/Stripe, Marc Andreessen/a16z, Ben Horowitz/wartime CEO, Balaji Srinivasan

**Zero bias:** Nenhuma estratégia é favorecida a priori. Todas competem igualmente na deliberação.

## Deliberation Protocol

```
Phase 1: Evidence Gathering — OBRIGATORIO, sempre paralelo:
         ├─ Explore agent: produto (pricing, planos, features, trial flow, setores, pipeline,
         │                 analytics, onboarding, billing — o que está funcionando agora)
         └─ general-purpose agent: web search para dados reais —
              - movimentos de concorrentes B2G (Licitanet, BLL, Neoway, ComprasNet, startups PNCP)
              - tendencias GovTech 2026 globais + Brasil (Lei 14.133, PNCP v2, novas leis)
              - benchmarks SaaS B2G: CAC, LTV, churn, trial-to-paid conversion rates
              - exemplos de AI-first startups com obsolescencia acelerada (risco real)
              - cases de solo founders que escalonaram em mercados regulados
              - valuations recentes de GovTech LATAM

Phase 2: Strategic Positions (8 visoes divergentes de CEO — baseadas em dados reais)
Phase 3: CEO Confrontation (4 pares desafiam uns aos outros com evidencias)
Phase 4: Synthesis & Iteration (resolve objecoes, max 3 rodadas)
Phase 5: Unanimous Consensus (8/8 obrigatorio)
```

**Web search é mandatório em toda invocação** — o conselho não delibera com dados obsoletos. Evidências de mercado reais informam cada posição de cada cluster.

## Confrontation Pairs

- **Bootstrap vs Sales-Led** — crescimento organico/sustentavel vs pipeline agressivo sem equipe
- **GovTech/Regulado vs Product-Led Growth** — procurement complexo vs auto-servico simples
- **Category Creator vs LATAM Outlier** — posicionamento conceitual vs execucao com restricoes locais
- **Capital Efficiency vs Contrarian/Outlier** — minimo viavel vs apostas assimetricas de ruptura

## Execution

Quando o usuário invoca `/manage`, executar este protocolo:

1. **Parse the question** from args
2. **Launch parallel evidence agents:**
   - `Explore` agent: Analisa SmartLic em profundidade — pricing atual, planos ativos, trial flow, setores configurados, features de IA, pipeline kanban, analytics disponíveis, código de billing, quota system, onboarding flow
   - `general-purpose` agent: Web search para inteligência de mercado real — concorrentes B2G ativos, movimentos regulatórios (PNCP, Lei 14.133/2021, Compras.gov), benchmarks SaaS B2G LATAM 2026, cases de solo founders em mercados regulados, risco de commoditização por IA em GovTech
3. **Launch deliberation agent** (Opus deep-executor) com todas as evidências:
   - Simula as 8 perspectivas de CEO, cada uma fundamentada em dados reais coletados
   - Cada cluster propõe estratégia com: visão, alavanca principal, timeline, risco-chave, dependência de time/capital
   - Roda confrontação CEO nos 4 pares — cada par DEVE desafiar o outro com evidências reais
   - Sintetiza até consenso unânime
   - DEVE incluir Vetor de Obsolescência (risco de commoditizacao por IA)
   - DEVE incluir Escala com AI (como IA substitui equipe em cada função)
   - DEVE incluir Outlier Move (a aposta nao-obvia)
   - DEVE incluir Sprint 90 Dias do CEO
   - Output: APENAS o consenso final + todos os outputs obrigatorios
4. **Present consensus** no formato padrão abaixo

## Output Format

```markdown
## Consenso do Conselho de CEOs — SmartLic

**Veredicto Estratégico:**
> [1 frase que define o que o founder deve fazer agora — clara, sem ambiguidade]

---

### Outlier Move
[A aposta assimétrica não-óbvia que a maioria dos players ignoraria. Por que funciona aqui
com este founder, neste mercado, neste momento?]

---

### Sprint 90 Dias do CEO

| Semana | Foco | Ação Principal | Resultado Esperado |
|--------|------|---------------|-------------------|
| 1-2 | [foco] | [acao] | [resultado] |
| 3-4 | [foco] | [acao] | [resultado] |
| 5-8 | [foco] | [acao] | [resultado] |
| 9-12 | [foco] | [acao] | [resultado] |

---

### Escala com AI (founder solo como time completo)

| Função | Como IA substitui a equipe | Ferramenta/Abordagem | Alavanca |
|--------|--------------------------|----------------------|---------|
| Vendas | [como] | [ferramenta] | [resultado] |
| Marketing | [como] | [ferramenta] | [resultado] |
| Suporte | [como] | [ferramenta] | [resultado] |
| Produto | [como] | [ferramenta] | [resultado] |
| Operações | [como] | [ferramenta] | [resultado] |

---

### Análise de Moat

Os 3 fatores de barreira real de entrada (considerando que IA nivela o campo técnico):

1. **[Moat 1]** — [descrição + por que é defensável mesmo com AI democratizando código]
2. **[Moat 2]** — [descrição]
3. **[Moat 3]** — [descrição]

*O insider knowledge de 7 anos como servidor público estadual em SC é ativo — como monetizar?*

---

### ⚠ Vetor de Obsolescência

**O que torna o SmartLic irrelevante em 12-24 meses?**

| Ameaça | Probabilidade | Janela de Tempo | Como Imunizar |
|--------|:---:|:---:|--------------|
| [ameaca 1 — ex: PNCP lanca ferramenta nativa] | Alta/Media/Baixa | X meses | [acao] |
| [ameaca 2 — ex: player grande replica com IA] | Alta/Media/Baixa | X meses | [acao] |
| [ameaca 3 — ex: commodity LLM faz busca gratis] | Alta/Media/Baixa | X meses | [acao] |

**Imunização prioritária:** [A acao mais importante para se tornar insubstituivel]

---

### Kill This Company

Os 3 riscos existenciais (além de obsolescência) e como eliminar cada um:

1. **[Risco 1]** → Eliminação: [acao]
2. **[Risco 2]** → Eliminação: [acao]
3. **[Risco 3]** → Eliminação: [acao]

---

### Analogia Outlier

Empresas que fizeram algo parecido com recursos parecidos:

1. **[Empresa]** — [contexto similar] → [o que o SmartLic pode aprender/replicar]
2. **[Empresa]** — [contexto similar] → [aprendizado]
3. **[Empresa]** — [contexto similar] → [aprendizado]

---

### Fundamentos da Deliberação
- [Por que o veredicto estratégico venceu — evidence-backed, com dados de mercado reais]

### Evidências de Mercado (fontes reais pesquisadas)
- [Dado/benchmark/case + URL ou fonte]

### Calendário do CEO esta semana

| Atividade | % do tempo | Horas/semana |
|-----------|:---:|:---:|
| [Atividade 1] | X% | X h |
| [Atividade 2] | X% | X h |
| [Atividade 3] | X% | X h |
| [Atividade 4] | X% | X h |

**Próxima Ação Imediata (hoje):**
> [A ÚNICA coisa mais importante para fazer hoje — específica, mensurável]

---
_Consenso unânime: 8/8 clusters (53 CEOs) | Evidências: produto + mercado real_
```

## Examples

```
/manage Como ser um outlier absoluto no mercado B2G brasileiro?
/manage Qual a estratégia para escalar sem contratar equipe?
/manage Como monetizar meu conhecimento de 7 anos como servidor público em SC?
/manage O que me torna irrelevante em 24 meses e como me imunizo?
/manage Devo buscar VC ou continuar bootstrap?
/manage Como usar AI Pair Programming não só para código mas para crescer a empresa?
/manage Qual é o posicionamento que cria categoria nova no mercado de licitações?
/manage Como fechar os primeiros 10 clientes pagantes sendo founder solo?
/manage Playbook completo de escala 2026 para SmartLic
/manage Quando e como fazer a primeira contratação?
/manage Qual parceria estratégica pode nos fazer crescer 10x?
/manage O PNCP pode nos matar — como construir moat real?
```

## Constraints

- **Founder solo** — nenhum time, nenhum recurso externo; tudo que requer equipe é irrelevante
- **7 anos como servidor público estadual em SC** — insider knowledge único do mercado B2G; tratar como ativo estratégico, não apenas contexto
- **100% AI Pair Programming** — plataforma desenvolvida com IA como equipe e continuará assim; IA não é diferencial técnico, é infraestrutura — o diferencial tem de estar em outro lugar
- **Trials reais acontecendo** — pré-revenue mas tração genuína; usuários reais usando em produção
- **Bootstrap** — sem capital externo; toda estratégia deve ser cash-flow compatible
- **Mercado B2G brasileiro** — licitações públicas reguladas pela Lei 14.133/2021, ciclo de decisão longo, resistência institucional à mudança
- **Ambição de outlier absoluto** — não seguir benchmarks; criar novos benchmarks
- **Risco de obsolescência por IA é real** — a mesma IA que viabilizou a plataforma reduz a barreira para concorrentes; commodity risk cresce a cada mês
- **Web search obrigatório** — nenhuma deliberação sem dados de mercado reais e atuais
- **Metas em BRL** — realidade econômica brasileira
- **Zero viés** — nenhuma estratégia é favorecida a priori; a deliberação decide baseada em evidências
