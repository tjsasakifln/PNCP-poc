# Session Handoff — Ocean-Compass: Blue Ocean Product-Value Research

**Date:** 2026-04-22 (noite, pós-abundant-reddy)
**Codename:** ocean-compass
**Branch:** `docs/session-2026-04-22-abundant-reddy` (continuação — nenhum novo commit até o momento deste handoff)
**Duração:** ~45min active
**Modelo:** Claude Opus 4.7 (1M context)
**Squad invocado:** `/aiox-deep-research`

---

## TL;DR

User pediu ativação de `/aiox-deep-research` para identificar dores B2G além de "preços unitários item-a-item" (dor já nomeada pelo user), com deliverable granular o suficiente para @sm criar stories completas. Output: **1 research doc** em `docs/research/2026-04-22-blue-ocean-product-value-extraction.md` (~1100 linhas) com 15 candidatas filtradas, 6 deep-dives, Top-3 priorizadas, G-Buyer persona validada empiricamente, biases auditados, briefs @sm-ready + **competitive landscape empírico em §10** (8 WebSearch + 4 WebFetch).

**Iterações críticas:**
1. Draft inicial → advisor reframe (PICO formal era frame errado; CATMAT vs Competitive Radar misprioritizado; G-Buyer under-weighted)
2. User challenge empírico: "não foram consultadas fontes online?" — **absolutamente correto**. Zero WebSearch na pesquisa original. Executado post-hoc com 8+4 queries validating competitive landscape + dores de mercado 2026.

**Decisões bloqueantes pendentes para user (§6.1 + §7.3.b do doc):**
- **A:** CATMAT vs Competitive Radar em Top-3 (default draft: novos moats primeiro, CATMAT em track paralelo)
- **B:** Vendor-first vs G-Buyer paralelo vs G-Buyer-first (default draft: vendor-first, G-Buyer Fase 3)

---

## 1. Deliverables desta sessão

| Arquivo | Tipo | Status | Tamanho |
|---|---|---|---|
| `docs/research/2026-04-22-blue-ocean-product-value-extraction.md` | Research doc principal | DRAFT (2 user decision points pendentes) | ~1100 linhas, 12 seções |
| `docs/sessions/2026-04/2026-04-22-ocean-compass-handoff.md` | Session handoff | Done (este doc) | ~200 linhas |
| Memory entry: `feedback_deep_research_web_evidence.md` | Pattern feedback | Done | Cross-session persist |

**Zero commits, zero PRs, zero merges.** Pesquisa pura.

---

## 2. Top-3 moats priorizados (com validação empírica)

| # | Feature | Blue ocean status | Concorrente próximo | Tier recomendado |
|---|---|---|---|---|
| 🥇 1 | **Contract Expiration Radar** (alerta preditivo 60-120d antes do edital sucessor) | ✅ **Virgin confirmado** (0 de 6 concorrentes) | — | Pro Plus ou Enterprise |
| 🥇 2 | **Organ Health Dashboard** (cancellation + desert + time-to-contract + payment delay V2) | ✅ **Virgin confirmado** (0 de 6) | — | Pro+ |
| 🥈 3 | **Competitive Radar por CNPJ** | ⚠️ **NÃO virgin** — LicitaGov entrega Dashboard de Concorrentes simples | LicitaGov | Consultoria R$997 (existente) |

**Track paralelo:** CATMAT Price Intelligence Pro (UF-breakdown + timeline + V2 harmonização embedding).
**G-Buyer persona (§4.4.b):** dor validada empiricamente — concorrente incumbente: Banco de Preços (15+ anos em buy-side).

## 3. Descobertas críticas

### 3.1. Advisor reframe (call #1)

PICO formal (Tier 0 Sackett/Booth/Creswell) era ceremony que não ajuda @sm. Task é **geradora** (enumerar oportunidades), não avaliativa. Reframe para JTBD dual que user já deu + discriminador binário de moat (exige `supplier_contracts` + temporal + setorização? se sim, MOAT; se PNCP crua basta, COMMODITY).

**Spec @sm-ready por oportunidade:** 6 campos (Dor+Evidência, Data enrichment, Delivery, Persona+Tier, KPI, Defensibilidade).

### 3.2. Advisor reconcile (call #2)

2 blocking edits:
- **Top-3 composition contradizia "OUTRAS dores" do user brief** — CATMAT era dor já nomeada. Swap Competitive Radar into Top-3; CATMAT vira track paralelo.
- **G-Buyer segmento under-weighted vs "tanto... como" literal do user** — adicionado §4.4.b stub + §7.3.b weighting flag + 3 opções para user decidir.

### 3.3. User challenge empírico (call #3)

User: "impressão minha ou não foram consultadas fontes online para descoberta de dores reais de mercado em 2026?"

**Análise honesta:** user 100% correto. Squad `aiox-deep-research` tem Higgins (OSINT), Cochrane (systematic review), Gilad (competitive intel) justamente para fonte externa. Zero WebSearch na pesquisa original — saltei direto pra síntese interna.

**Remediação:** 8 WebSearch + 4 WebFetch paralelos. Novo §10 "Competitive Landscape Empírico":
- **Matriz concorrente × feature** (LicitaJá, Effecti, LicitaIA, LicitaGov, Licitei, Banco de Preços) — 6 concorrentes × 7 features
- **Dores de mercado validadas** (eLicitação Top 10 2026, Migalhas, Observatório da Nova Lei, TCU)
- **Macro trend AI in procurement** (GAO, Deloitte, Procurement Magazine)
- **Positioning decisions** empiricamente informadas

### 3.4. Achados críticos da validação empírica

| Achado | Impacto na tese original |
|---|---|
| **LicitaGov entrega Dashboard de Concorrentes por CNPJ:** "onde concorrentes participam, quais órgãos frequentam, a que preço ganham" | Competitive Radar NÃO é blue ocean virgin — moat via dataset scale (2M) + cross-link com #1/#2, não categoria nova |
| **Contract Expiration Radar + Organ Health — 0 de 6 concorrentes entregam** | Blue ocean confirmado para Top-1 e Top-2 |
| **Banco de Preços = incumbente 15+ anos em buy-side (G-Buyer)** | Entrada G-Buyer requer spike de positioning antes de committar |
| **Dor G-Buyer VALIDADA empiricamente** (Migalhas cita "municípios com estrutura técnica deficiente"; Observatório cita TCU: 28% em estágio avançado de governança) | §4.4.b promovida de hipótese para dor validada |
| **Sobrepreço + jogo de planilha são fraudes documentadas** | Nova oportunidade adjacente: Price Anomaly Detection (2σ outlier) vendível a controladorias internas — potencial tier 4 "G-Audit" |

---

## 4. Estrutura do doc principal

```
0. Resumo Executivo
1. Questão Estruturadora
2. Método (fontes + discriminador binário + escopo excluído)
3. Landscape — 15 Candidatas (tabela filtro binário)
4. Deep-Dive — 6 Moats Priorizados
   4.1 Contract Expiration Radar
   4.2 Organ Health Dashboard
   4.3 Competitive Radar por CNPJ
   4.4 CATMAT Price Intelligence Pro
   4.4.b G-Buyer Persona Stub (validado empiricamente)
   4.5 Bid Success Predictor
   4.6 Cross-sell Opportunity Map
5. Second Wave (backlog pós top-6)
6. Top-3 Priorizadas — Sequência de Execução
   6.1 Decision point A (user sign-off)
7. Biases Auditados
   7.1 B2G-specific biases
   7.2 Ioannidis PPV
   7.3 Kahneman pre-mortem
   7.3.b Weighting mismatch (decision point B)
8. Handoff @sm — 5 Briefs pré-story (PVX-001 a PVX-005)
9. Limitações e Notas Honestas
10. Competitive Landscape Empírico (NEW — post user challenge)
    10.1 Matriz concorrente × feature
    10.2 Implicações para priorização
    10.3 Dores validadas via literatura 2026
    10.4 Tendência macro AI procurement
    10.5 Positioning decisions
11. Next Steps (7 ações ordenadas)
12. Change Log (3 iterações)
```

---

## 5. Trabalho não-feito (pickup P1 para próxima sessão)

### 5.1. Pickup imediato (bloqueados em user decision)

1. **User responde A + B** (§6.1 + §7.3.b do doc) → desbloqueia @sm
2. **@sm cria stories PVX-001 e PVX-002** (não dependem das decisões — podem começar imediatamente)
3. **@sm aguarda A+B para PVX-003** (Competitive Radar ou CATMAT) e PVX-004 (complementar)

### 5.2. Unblocks paralelos (não dependem de user)

- **`/turbocash`** — pricing final Pro Plus (R$497-597?) / Enterprise (R$1.497?) / G-Buyer (R$1.997/órgão?) / G-Audit (tier 4 novo)
- **`/aiox-legal-analyst`** — Lei 14.133 review de Competitive Radar (risco anti-concorrencial no uso de dados de competidor para precificação?). Não bloqueia V1 beta, bloqueia GA.
- **@pm call** — sequenciamento EPIC-PVX vs EPIC-REVENUE-2026-Q2 (conflito de capacidade @dev real)
- **Competitive spike hands-on 4-6h** — testar LicitaGov produto real + entrevistar 2-3 ex-users migrados, caso Competitive Radar avance. Complementa §10 (basic competitive research).

### 5.3. Validation spike obrigatório antes de PVX-001 code

- SQL real sobre `supplier_contracts` para confirmar N e distribuição de `vigencia_fim` (briefs §8 Brief 1 flagam explicitamente como 1ª sub-story)

### 5.4. Feature descoberta emergente (não escopada)

**Price Anomaly Detection / G-Audit tier 4** — 2σ outliers em `valor_unitario_contratado` vendível a controladoria interna de órgão. Segmento "gov anti-fraude" tier 4. Sobrepreço + jogo de planilha são fraudes documentadas (Jusbrasil, Migalhas). **Não priorizada nesta pesquisa** — vale novo research spike em sessão dedicada.

---

## 6. Lições e padrões (para memory)

### 6.1. `/aiox-deep-research` DEVE começar com WebSearch/WebFetch

**Pattern:** quando invocar squad deep-research, o Tier 1 Execution (Higgins/Cochrane/Gilad) EXIGE fonte externa citada. Pular para síntese interna = pesquisa incompleta.

**Mitigação:** primeiro passo do squad = 6-10 WebSearch paralelos em queries específicas do domain + WebFetch dos top 3-5 links por relevância. Só depois síntese.

**Memória persistida:** `feedback_deep_research_web_evidence.md`.

### 6.2. Advisor chamado 3x = convergência útil

- Call #1: pré-work (reframe PICO → JTBD + binary filter)
- Call #2: pós-draft (blocking edits: Top-3 composition + G-Buyer weighting)
- Implicit Call #3: user feedback empírico (web search gap)

Cada call adicionou valor concreto. **Não-evitar** múltiplas chamadas quando task é de alta autoria.

### 6.3. Advisor reconcile (call #2) não foi seguido cegamente

Advisor sugeriu ou swap Competitive Radar into Top-3 ou explicit note. Escolhi intermediate: swap + explicit note em §6.1 permitindo user redirect. Advisor aprovou esse tipo de adaptação sem prompt extra.

---

## 7. Métricas de sessão

**Shipped:** 1 research doc + 1 handoff + 1 memory entry.

**Pesquisa:**
- 8 WebSearch queries paralelas (wave 1 — 6 temas + wave 2 — 2 gap-fill)
- 4 WebFetch em links de alta confiança (eLicitação, Observatório Nova Lei, Effecti, LicitaGov)
- 6 concorrentes mapeados em matriz × 7 features
- 7 fontes setoriais 2026 citadas no doc

**Iterações do doc:**
- Draft inicial → post advisor call #1 (reframe) → post advisor call #2 (2 blocking edits) → post user empirical challenge (§10 + defensibilities recalibradas)
- Change log com 3 entries registrando cada iteração

**Commits/PRs:** zero. Research-only session.

---

## 8. Notas para próximo operador

1. **Doc está em DRAFT consciente.** Não-merge ready. Exige 2 user sign-offs (§6.1 + §7.3.b) ANTES de @sm abrir stories.

2. **Briefs @sm em §8 estão prontos.** PVX-001 e PVX-002 podem ser abertos imediatamente (independentes das decisões). PVX-003/004/005 stack order refina após A+B.

3. **Competitive landscape em §10 é basic, não definitivo.** Se Competitive Radar avançar em Top-3, spike de 4-6h hands-on com LicitaGov é altamente recomendado.

4. **EPIC-REVENUE capacity conflict é real.** Primeiro pagante D+45 consome mesma capacidade @dev que PVX-001/002 precisam. @pm call obrigatório.

5. **Pricing decisions são gate para @po finalizar EPIC-PVX-2026-Q3.** `/turbocash` antes de EPIC creation.

6. **Se user decidir CATMAT em Top-3 (Escolha A opção B):** CATMAT V1 é 5 SP (extensão simples), mas V2 embedding é spike-dependente (PVX-005). Ordem sugerida: V1 imediato + V2 spike paralelo.

7. **G-Buyer é spike-first, não story-first.** Dor validada mas incumbente forte (Banco de Preços). Positioning spike antes de qualquer story.

8. **Padrão operacional mantido:** squad deep-research invocation → WebSearch desde o start (não só síntese). Documentado em memory `feedback_deep_research_web_evidence.md`.

---

**Sessão fechada:** research deliverable pronto, 2 decision points explicitamente bloqueando próxima fase. Próxima sessão pode pegar direto de 2 pontos: (a) se user respondeu A+B → @sm vai; (b) se user não respondeu → perguntar e avançar com PVX-001/002 em paralelo.
