# Lead Prospecting Workflow - *acha-leads v2

## 🎯 Mission

Identificar **>=10 leads com alta probabilidade de compra nos proximos 30-90 dias**, usando sinais comportamentais extraidos do PNCP e fontes complementares para detectar empresas em momento de decisao de investimento.

**Foco:** Intenção de compra (buy intent), não dependência.

## 🏗️ Architecture Overview

```
*acha-leads (User invokes)
    ↓
    ├── mode: --lean | --scale (default: lean)
    ↓
[1] Query PNCP API (participations + wins, 6-12 month window)
    ├── Month-over-month comparison
    ├── Participation count + win count + avg value
    ├── Growth detection (>=20% MoM)
    └── High-participation-low-conversion detection
    ↓
[2] Extract company profiles (CNPJ, volume, win rate, categories)
    ↓
[3] Calculate Buy Intent Score (6-factor model, 0-10)
    ↓
[4] Filter leads (score >= 7.0)
    ↓
    ┌─────────────────────┬──────────────────────────┐
    │     LEAN MODE        │       SCALE MODE          │
    │  (no LLM, fast)     │  (full enrichment + LLM)  │
    ├─────────────────────┼──────────────────────────┤
    │ [5L] Basic contact   │ [5S] Deep contact search   │
    │      search (web)    │      + LinkedIn signals     │
    │                      │ [6S] Buy signal detection   │
    │                      │      (hiring, expansion,    │
    │                      │       CNAE changes)         │
    │ [6L] Score + rank    │ [7S] LLM message generation │
    │ [7L] Output CSV      │ [8S] Output Markdown + CRM  │
    └─────────────────────┴──────────────────────────┘
```

## 📊 Buy Intent Scoring Model

### 6-Factor Weighted Score

| Factor | Weight | Signal | Scoring (0-10) |
|--------|--------|--------|-----------------|
| **Intensidade Operacional** | 25% | # participacoes ultimos 6-12 meses | >=20 = 10, 15-19 = 8, 10-14 = 6, 5-9 = 4, <5 = 2 |
| **Crescimento Recente** | 20% | Aumento volume contratos ou valor total (MoM) | >=40% = 10, 30-39% = 8, 20-29% = 6, 10-19% = 3, <10% = 0 |
| **Complexidade de Portfolio** | 15% | Atua em multiplos orgaos/segmentos | >=5 orgaos + >=3 segmentos = 10, >=3 + >=2 = 7, >=2 + >=1 = 4, else = 1 |
| **Sinal de Gargalo** | 20% | Alto volume com baixa taxa de vitoria | >=15 participacoes + <20% win rate = 10, >=10 + <30% = 7, else = 2 |
| **Dependencia Publica** | 10% | % receita estimada via contratos publicos | >=70% = 10, 50-69% = 7, 30-49% = 4, <30% = 1 |
| **Qualidade de Contato** | 10% | Email direto + telefone valido | Email + telefone = 10, email direto = 7, email generico = 4, nenhum = 0 |

### Score Interpretation

| Score Range | Classification | Action |
|-------------|---------------|--------|
| **8.5 - 10.0** | Hot Lead | Contato prioritario em 48h |
| **7.0 - 8.4** | Warm Lead | Contato na proxima semana |
| **5.0 - 6.9** | Nurture | Adicionar a lista de acompanhamento |
| **< 5.0** | Discard | Nao qualificado |

**Minimum Score:** 7.0/10 para inclusao no output.

### Score Calculation

```python
def calculate_buy_intent_score(company: CompanyProfile) -> float:
    """
    Calculate buy intent score based on 6 behavioral factors.

    Returns:
        float: Score 0.0-10.0, weighted average of all factors.
    """
    factors = {
        "intensidade_operacional": {
            "weight": 0.25,
            "value": score_operational_intensity(company.participations_6m),
        },
        "crescimento_recente": {
            "weight": 0.20,
            "value": score_recent_growth(company.mom_growth_pct),
        },
        "complexidade_portfolio": {
            "weight": 0.15,
            "value": score_portfolio_complexity(
                company.distinct_organs, company.distinct_segments
            ),
        },
        "sinal_gargalo": {
            "weight": 0.20,
            "value": score_bottleneck_signal(
                company.participations_6m, company.win_rate
            ),
        },
        "dependencia_publica": {
            "weight": 0.10,
            "value": score_public_dependency(company.estimated_public_revenue_pct),
        },
        "qualidade_contato": {
            "weight": 0.10,
            "value": score_contact_quality(company.email, company.phone),
        },
    }

    return sum(f["weight"] * f["value"] for f in factors.values())
```

## 📡 Data Sources

### Primary: PNCP API

| Query | Purpose | Endpoint |
|-------|---------|----------|
| Participacoes por CNPJ (6-12 meses) | Intensidade operacional | `/api/consulta/v1/contratacoes/publicacao` |
| Contratos homologados por CNPJ | Win count + valor | `/api/consulta/v1/contratacoes/homologadas` |
| Comparativo mes-a-mes | Detecao de crescimento | Derived (2 queries, months M-1 vs M-3) |

### PNCP Query Strategy

```python
def query_pncp_company_profile(cnpj: str, months: int = 6) -> CompanyPNCPProfile:
    """
    Build behavioral profile from PNCP data.

    Extracts:
    - total_participations: int        # Total bids submitted
    - total_wins: int                  # Contracts won
    - win_rate: float                  # wins / participations
    - avg_contract_value: float        # Mean value of won contracts
    - distinct_organs: int             # Unique contracting agencies
    - distinct_segments: int           # Unique procurement categories
    - mom_growth_pct: float            # Month-over-month growth (%)
    - categories: list[str]            # Active procurement categories

    Growth detection:
    - Compare last 3 months vs previous 3 months
    - Flag if participation count OR total value increased >= 20%

    Bottleneck detection:
    - Flag if participations >= 15 AND win_rate < 20%
    - These companies are ACTIVELY TRYING but FAILING = prime targets
    """
    pass
```

### Month-over-Month Comparison

```
Period A: months[-6:-3]  (older quarter)
Period B: months[-3:0]   (recent quarter)

growth_pct = ((period_b_count - period_a_count) / max(period_a_count, 1)) * 100

Flags:
  - GROWING:    growth_pct >= 20%
  - STABLE:     -10% < growth_pct < 20%
  - DECLINING:  growth_pct <= -10%
```

### Secondary Sources (Scale Mode Only)

| Source | Purpose | Signal |
|--------|---------|--------|
| **LinkedIn** (via web search) | Hiring signals, expansion posts | Contratando, expandindo, novo escritorio |
| **Receita Federal** | CNAE changes, company size | Alteracao cadastral recente |
| **Google Search** | News, press releases | Noticias sobre expansao, contratos |
| **Portal da Transparencia** | Cross-reference contract execution | Contratos em execucao |

### Data Points Extracted

**From PNCP (both modes):**
- CNPJ + Razao Social
- Participation count (last 6 months)
- Win count + win rate
- Average contract value
- Distinct organs + segments
- Month-over-month growth %
- Active categories
- Last participation date

**From Web Search (both modes):**
- Email (contato@, comercial@, vendas@, or personal)
- Phone (fixo or celular)
- Website URL

**From Enrichment (Scale mode only):**
- LinkedIn hiring posts
- Expansion signals (new offices, new regions)
- CNAE changes (new activity codes = new market entry)
- New category participation (categories not seen >6 months ago)
- News/press releases

## 🔀 Operating Modes

### Lean Mode (Default)

**Use when:** Quick prospecting, initial lead list, limited time.

| Aspect | Detail |
|--------|--------|
| **Data sources** | PNCP only + basic web search for contact |
| **LLM usage** | None |
| **Enrichment** | Contact info only (email, phone, website) |
| **Output** | CSV file |
| **Execution time** | < 3 minutes |
| **Cost** | Zero (no API calls beyond PNCP) |

**Output columns (CSV):**
```
cnpj, razao_social, score, classification, participations_6m, wins_6m,
win_rate, avg_value, growth_pct, bottleneck_flag, organs_count,
segments_count, email, phone, website, last_activity
```

### Scale Mode

**Use when:** High-value outreach campaign, CRM integration, personalized messaging.

| Aspect | Detail |
|--------|--------|
| **Data sources** | PNCP + LinkedIn + Receita Federal + Google + Transparencia |
| **LLM usage** | GPT-4.1-nano for message generation |
| **Enrichment** | Full (buy signals, hiring, CNAE changes, news) |
| **Output** | Markdown report + CRM-ready JSON |
| **Execution time** | < 8 minutes |
| **Cost** | ~$0.02-0.05 per lead (LLM calls) |

**Output:** Markdown lead profiles + JSON for CRM import.

**Invocation:**
```bash
# Lean mode (default)
*acha-leads --sector vestuario --ufs SP,RJ,MG

# Scale mode (full enrichment)
*acha-leads --sector vestuario --ufs SP,RJ,MG --mode scale

# Scale mode targeting specific CNPJs
*acha-leads --cnpjs 12345678000190,98765432000111 --mode scale
```

## 🔎 Buy Signal Detection (Scale Mode)

### Signal Categories

| Signal | Source | Weight Multiplier | Detection Method |
|--------|--------|-------------------|------------------|
| **Hiring in procurement** | LinkedIn | 1.15x | "analista de licitacao", "pregao", "compras publicas" in job posts |
| **Regional expansion** | LinkedIn + Google | 1.10x | "nova filial", "expansao", "novo escritorio" mentions |
| **CNAE change** | Receita Federal | 1.20x | New primary/secondary CNAE in last 6 months |
| **New category entry** | PNCP | 1.15x | Bidding in categories not seen >6 months ago |
| **Contract execution spike** | Transparencia | 1.10x | >3 contracts in simultaneous execution |
| **Press release** | Google | 1.05x | Recent news about growth, investment, awards |

### Signal Application

```python
def apply_buy_signals(base_score: float, signals: list[BuySignal]) -> float:
    """
    Apply buy signal multipliers to base score.
    Capped at 10.0.

    Example:
      base_score = 7.5
      signals = [hiring_procurement(1.15), cnae_change(1.20)]
      adjusted = min(7.5 * 1.15 * 1.20, 10.0) = min(10.35, 10.0) = 10.0
    """
    adjusted = base_score
    for signal in signals:
        adjusted *= signal.multiplier
    return min(adjusted, 10.0)
```

## 📝 Message Generation

### Behavioral Pattern Focus

Messages are generated based on the company's **observed behavioral patterns** in PNCP data, not generic templates. The core principle: reference specific, verifiable numbers that demonstrate you have done your homework.

### Message Strategy by Lead Type

| Lead Type | Behavioral Pattern | Message Angle |
|-----------|-------------------|---------------|
| **High-volume low-win** | Many participations, few wins | "Efficiency gain" - help them win more |
| **Growing fast** | Rapid MoM increase | "Scale support" - help them manage growth |
| **Multi-organ** | Active across many agencies | "Consolidation" - unified view of opportunities |
| **Category expander** | Entering new segments | "New market" - intelligence for unfamiliar territory |
| **High dependency** | >70% public revenue | "Risk mitigation" - never miss an opportunity |

### Message Template (Scale Mode - LLM Generated)

```
Ola {nome_contato ou razao_social},

{behavioral_observation}

{value_proposition}

{specific_data_point}

{call_to_action}

Atenciosamente,
{remetente}
SmartLic | smartlic.tech
```

### Behavioral Observation Examples

**High-volume low-win (Bottleneck):**
> "Notei que voces participaram de 18 pregoes no ultimo trimestre e venceram 3. Com uma taxa de 16%, existe uma oportunidade clara de melhorar a selecao de editais para focar nos que tem maior probabilidade de vitoria."

**Growing fast:**
> "Voces dobraram o volume de participacoes nos ultimos 3 meses (de 7 para 15), o que sugere um momento forte de expansao. Identificamos 12 novas oportunidades alinhadas aos segmentos em que voces ja atuam."

**Category expander:**
> "Percebi que voces comecaram a participar de editais de {nova_categoria} recentemente, alem do historico em {categoria_principal}. Temos inteligencia especifica nesses novos segmentos que pode acelerar essa diversificacao."

**Multi-organ:**
> "Com participacoes em {N} orgaos diferentes nos ultimos 6 meses, o volume de acompanhamento deve ser consideravel. O SmartLic consolida todas as fontes e alerta automaticamente sobre novas oportunidades relevantes."

### LLM Prompt (Scale Mode)

```python
LEAD_MESSAGE_PROMPT = """
Voce e um especialista em vendas B2G (business-to-government).
Gere uma mensagem de prospecao baseada nos dados comportamentais abaixo.

REGRAS:
- Cite numeros especificos do historico da empresa (participacoes, vitorias, taxa)
- Nunca use linguagem generica tipo "percebemos que sua empresa e lider"
- Maximo 120 palavras
- Tom profissional e direto, sem exageros
- Foque no problema observado e como o SmartLic resolve
- Termine com CTA especifico (reuniao de 15 min)

DADOS DA EMPRESA:
- Razao Social: {razao_social}
- Participacoes (6m): {participations}
- Vitorias (6m): {wins}
- Taxa de vitoria: {win_rate}%
- Crescimento MoM: {growth_pct}%
- Orgaos ativos: {organs}
- Segmentos: {segments}
- Valor medio: R$ {avg_value}
- Sinal principal: {primary_signal}

Gere APENAS a mensagem, sem explicacoes.
"""
```

## 📋 Contact Requirements

### Relaxed Contact Model

Contact data is **desirable but not blocking**. A lead with strong buy-intent signals but incomplete contact can still be included.

| Contact Level | Definition | Score Impact |
|---------------|-----------|--------------|
| **Full** | Email direto + telefone valido | 10/10 (Qualidade de Contato) |
| **Good** | Email direto (sem telefone) | 7/10 |
| **Basic** | Email generico (contato@, info@) | 4/10 |
| **Minimal** | Apenas website / sem contato | 0/10 |

**Key differences from v1:**
- Email OR phone is sufficient (not both mandatory)
- No WhatsApp requirement
- Contact quality affects score but does not disqualify
- A lead with score 9.0 and no email still appears (flagged for manual enrichment)

### Contact Search Strategy

```
Priority 1: Company website → "contato", "fale conosco", "comercial"
Priority 2: Google "{razao_social} email telefone"
Priority 3: LinkedIn company page → general info
Priority 4: Receita Federal → registered phone (often outdated)
```

## 📦 Output Formats

### Lean Mode: CSV

**File:** `docs/leads/leads-lean-{YYYY-MM-DD}.csv`

```csv
cnpj,razao_social,score,classification,participations_6m,wins_6m,win_rate,avg_value,growth_pct,bottleneck,organs,segments,email,phone,website,last_activity
12345678000190,EMPRESA ALPHA LTDA,8.7,hot,22,4,18.2,150000,35.0,true,6,3,contato@alpha.com.br,1133334444,alpha.com.br,2026-02-15
98765432000111,BETA SERVICOS SA,7.3,warm,12,5,41.7,80000,22.0,false,4,2,vendas@beta.com.br,,beta.com.br,2026-02-20
```

### Scale Mode: Markdown Report

**File:** `docs/leads/leads-scale-{YYYY-MM-DD}.md`

```markdown
# Lead Prospecting Report - {Date}

**Generated by:** *acha-leads v2 (Scale Mode)
**Scoring Model:** Buy Intent 6-Factor
**Time Window:** Last 6 months
**Sectors:** {sectors queried}
**UFs:** {ufs queried}
**Total Candidates Analyzed:** {N}
**Qualified Leads (>= 7.0):** {N}
**Hot Leads (>= 8.5):** {N}

---

## Lead #1 - {Company Name} 🔥

### Buy Intent Score: {score}/10 — {HOT|WARM}

| Factor | Score | Detail |
|--------|-------|--------|
| Intensidade Operacional | {x}/10 | {N} participacoes em 6 meses |
| Crescimento Recente | {x}/10 | {N}% crescimento MoM |
| Complexidade Portfolio | {x}/10 | {N} orgaos, {N} segmentos |
| Sinal de Gargalo | {x}/10 | {N} participacoes, {N}% win rate |
| Dependencia Publica | {x}/10 | ~{N}% receita publica |
| Qualidade de Contato | {x}/10 | {email + phone | email only | ...} |

### Contact
- **Email:** {email}
- **Phone:** {phone}
- **Website:** {url}

### Behavioral Profile
- **Participacoes (6m):** {N}
- **Vitorias (6m):** {N}
- **Win Rate:** {N}%
- **Valor Medio:** R$ {value}
- **Crescimento MoM:** {N}%
- **Orgaos Ativos:** {list}
- **Segmentos:** {list}
- **Ultima Atividade:** {date}

### Buy Signals Detected
- {signal_1}: {detail}
- {signal_2}: {detail}

### Personalized Message

---
Ola {contact},

{LLM-generated behavioral message}

Atenciosamente,
{Remetente}
SmartLic | smartlic.tech
---

---

{Lead #2, #3, ... #10+}

---

## Execution Summary
- **Total PNCP Queries:** {N}
- **Companies Analyzed:** {N}
- **Qualified Leads:** {N} (score >= 7.0)
- **Hot Leads:** {N} (score >= 8.5)
- **Average Score:** {score}/10
- **Buy Signals Detected:** {N} across {N} companies
- **Execution Time:** {N}s
- **Errors:** {N} (see logs)
- **Recommendation:** Prioritize leads #{x}, #{y}, #{z} (highest buy intent)
```

### Scale Mode: CRM JSON

**File:** `docs/leads/leads-crm-{YYYY-MM-DD}.json`

```json
{
  "generated_at": "2026-02-24T14:30:00Z",
  "model_version": "buy-intent-v2",
  "leads": [
    {
      "cnpj": "12345678000190",
      "razao_social": "EMPRESA ALPHA LTDA",
      "score": 8.7,
      "classification": "hot",
      "factors": {
        "intensidade_operacional": 9,
        "crescimento_recente": 8,
        "complexidade_portfolio": 7,
        "sinal_gargalo": 10,
        "dependencia_publica": 7,
        "qualidade_contato": 10
      },
      "contact": {
        "email": "contato@alpha.com.br",
        "phone": "1133334444",
        "website": "alpha.com.br"
      },
      "behavioral_profile": {
        "participations_6m": 22,
        "wins_6m": 4,
        "win_rate": 18.2,
        "avg_contract_value": 150000,
        "mom_growth_pct": 35.0,
        "distinct_organs": 6,
        "distinct_segments": 3,
        "bottleneck_flag": true,
        "last_activity": "2026-02-15"
      },
      "buy_signals": [
        {"type": "hiring_procurement", "detail": "Vaga analista licitacao LinkedIn"},
        {"type": "cnae_change", "detail": "Novo CNAE secundario adicionado"}
      ],
      "message": "Notei que voces participaram de 22 pregoes..."
    }
  ]
}
```

## 🛠️ Implementation Phases

### Phase 1: PNCP Behavioral Queries (@data-engineer)
**Duration:** 1 session

**Deliverables:**
1. PNCP query functions for participation history by CNPJ
2. Month-over-month comparison logic
3. Bottleneck detection (high participation + low win rate)
4. Growth detection (>=20% MoM)
5. Sample dataset: 20 companies with behavioral profiles

**Acceptance Criteria:**
- [ ] Query PNCP participations by CNPJ (last 6 months)
- [ ] Query PNCP wins by CNPJ (last 6 months)
- [ ] Calculate MoM growth % correctly
- [ ] Detect bottleneck pattern (>=15 participations + <20% win rate)
- [ ] Detect growth pattern (>=20% MoM increase)
- [ ] Sample dataset validated with 20 real companies

### Phase 2: Scoring Engine (@dev + @architect)
**Duration:** 1 session

**Deliverables:**
1. `backend/lead_scorer.py` — 6-factor scoring model
2. `backend/schemas/lead.py` — Pydantic models (CompanyProfile, BuyIntentScore, LeadResult)
3. Unit tests for each scoring factor
4. Integration test with sample PNCP data

**Acceptance Criteria:**
- [ ] All 6 factors correctly weighted (25+20+15+20+10+10 = 100%)
- [ ] Score range 0.0-10.0 validated
- [ ] Bottleneck signal correctly identified and scored
- [ ] Growth signal correctly identified and scored
- [ ] Portfolio complexity accounts for distinct organs AND segments
- [ ] Contact quality handles email-only, phone-only, both, neither
- [ ] Unit tests: >=20 cases covering edge conditions
- [ ] Integration test with real PNCP data

### Phase 3: Contact Search + Lean Pipeline (@dev)
**Duration:** 1 session

**Deliverables:**
1. `backend/lead_contact_search.py` — Web search for email/phone
2. `backend/lead_prospecting.py` — Lean mode pipeline (end-to-end)
3. CSV output generation
4. CLI invocation via `*acha-leads`

**Acceptance Criteria:**
- [ ] Web search finds email for >=70% of companies
- [ ] Web search finds phone for >=50% of companies
- [ ] Lean pipeline executes end-to-end in <3 minutes
- [ ] CSV output contains all required columns
- [ ] `*acha-leads --sector X --ufs Y` works from CLI
- [ ] Handles PNCP API failures gracefully (retry + partial results)

### Phase 4: Scale Pipeline + Buy Signals (@dev + @analyst)
**Duration:** 1-2 sessions

**Deliverables:**
1. `backend/lead_buy_signals.py` — Buy signal detection
2. `backend/lead_message_generator.py` — LLM-powered message generation
3. Scale mode pipeline (Markdown + CRM JSON output)
4. LinkedIn signal detection via web search

**Acceptance Criteria:**
- [ ] Buy signal multipliers correctly applied (capped at 10.0)
- [ ] At least 3 signal types detectable (hiring, CNAE change, new category)
- [ ] LLM messages reference specific behavioral data (not generic)
- [ ] Markdown output follows template exactly
- [ ] CRM JSON output is valid and importable
- [ ] Scale pipeline executes in <8 minutes
- [ ] Graceful degradation: if LinkedIn/enrichment fails, still outputs leads

### Phase 5: Validation (@qa)
**Duration:** 1 session

**Deliverables:**
1. Test suite for scoring model (unit + integration)
2. Quality review of 10 generated leads
3. Message quality assessment (manual)
4. Edge case validation

**Acceptance Criteria:**
- [ ] >=5 leads with score >=8.5 in a typical run
- [ ] >=15% estimated response rate (based on message quality + contact quality)
- [ ] Scores mathematically correct across all 6 factors
- [ ] Messages contextually relevant (manual review of 10 samples)
- [ ] No crashes on API failures
- [ ] Lean mode produces valid CSV
- [ ] Scale mode produces valid Markdown + JSON

## 🚀 Success Criteria

### Quantitative

| Metric | Target | Measurement |
|--------|--------|-------------|
| Qualified leads per run | >=10 | Leads with score >= 7.0 |
| Hot leads per run | >=5 | Leads with score >= 8.5 |
| Estimated response rate | >=15% | Based on contact quality + message relevance |
| Lean mode execution | <3 min | End-to-end wall clock |
| Scale mode execution | <8 min | End-to-end wall clock |
| Email coverage | >=70% | Leads with valid email |
| Phone coverage | >=50% | Leads with valid phone |

### Qualitative

| Criteria | Validation Method |
|----------|-------------------|
| Messages reference specific behavioral data | Manual review: no generic phrases |
| Bottleneck leads correctly identified | Cross-check PNCP participation vs win data |
| Growth leads correctly identified | Verify MoM calculation with raw data |
| Buy signals are actionable | Manual review: signals lead to specific angles |
| Score factors are discriminating | Distribution analysis: not all leads cluster at same score |

## 🔧 Technical Considerations

### Rate Limiting

| API | Limit | Strategy |
|-----|-------|----------|
| PNCP | ~10 req/s (empirical) | Exponential backoff, same as `pncp_client.py` |
| Google Custom Search | 100/day (free) | Batch queries, cache results |
| Receita Federal | ~5 req/s (empirical) | Cache responses (company data is static) |

### Resilience

- Reuse existing `pncp_client.py` retry + circuit breaker patterns
- Fallback to partial data if enrichment sources fail
- Cache PNCP behavioral data per CNPJ (1h TTL, same Redis infrastructure)
- Lean mode has zero external dependencies beyond PNCP + web search

### Privacy & Ethics

- Only publicly available data (PNCP, Receita Federal, public LinkedIn)
- Business emails only (contato@, comercial@, vendas@) — no personal emails
- Respect robots.txt and rate limits on all web searches
- LGPD compliance: no personal data storage beyond workflow execution
- Messages clearly identify sender and purpose (no deception)

## 🧪 Testing Strategy

### Unit Tests
- Each of the 6 scoring factors (edge cases: 0, boundary values, max)
- Buy signal multiplier application (cap at 10.0)
- MoM growth calculation (division by zero, negative growth)
- Bottleneck detection (exact thresholds)
- CSV output format validation
- JSON output schema validation

### Integration Tests
- End-to-end Lean pipeline with mocked PNCP data
- End-to-end Scale pipeline with mocked PNCP + enrichment data
- API failure scenarios (PNCP down, web search fails)
- Rate limiting compliance

### Manual Validation
- Review 10 sample leads for scoring accuracy
- Verify behavioral observations match PNCP data
- Assess message quality and specificity
- Spot-check contact data accuracy

## 📚 Related Documentation

- **PNCP API Docs:** https://pncp.gov.br/api/
- **Existing PNCP Client:** `backend/pncp_client.py` (reuse retry + CB patterns)
- **Sector Configuration:** `backend/sectors_data.yaml`
- **Receita Federal API:** https://www.receitafederal.gov.br/
- **Google Custom Search API:** https://developers.google.com/custom-search
- **LLM Integration:** `backend/llm.py` (GPT-4.1-nano, reuse for Scale mode messages)
- **Redis Cache:** `backend/redis_pool.py` (reuse for PNCP behavioral data cache)

## 🎯 Next Steps

1. **Phase 1 Kickoff:** @data-engineer builds PNCP behavioral query functions
2. **Sample Analysis:** Query 20 real companies, validate scoring model with real data
3. **Lean Pipeline First:** Ship Lean mode as MVP (zero LLM cost, fast iteration)
4. **Scale Mode Second:** Add enrichment + LLM messages after Lean is validated
5. **Feedback Loop:** Use Lean mode output to calibrate scoring thresholds before Scale

---

**Squad:** Lead Prospecting Task Force (`.aios-core/development/agent-teams/squad-lead-prospecting.yaml`)
**Lead Agent:** @data-engineer (Phase 1-2), @dev (Phase 3-4), @qa (Phase 5)
**Estimated Timeline:** 4-6 sessions (behavioral queries -> scoring -> lean pipeline -> scale pipeline -> validation)
**Model Version:** Buy Intent v2 (6-factor, Lean/Scale fork)
