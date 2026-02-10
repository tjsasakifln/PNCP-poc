# Lead Prospecting Workflow - *acha-leads

## 🎯 Mission

Identificar cirurgicamente empresas cuja sobrevivência depende de licitações públicas, fornecendo dados de contato e estratégia de conversão personalizada.

## 🏗️ Architecture Overview

```
*acha-leads (User invokes)
    ↓
[1] Query PNCP API (homologated contracts, recent)
    ↓
[2] Extract winning companies
    ↓
[3] Cross-reference with Receita Federal API
    ↓
[4] Calculate dependency score (% revenue from public contracts)
    ↓
[5] Filter high-dependency companies (score ≥ 70%)
    ↓
[6] Web search for contact data + strategic intelligence
    ↓
[7] Generate personalized outreach message
    ↓
[8] Output structured lead document
```

## 📊 Data Sources

### Primary APIs

| API | Purpose | Endpoint | Auth |
|-----|---------|----------|------|
| **PNCP** | Homologated contracts | `/api/consulta/v1/contratacoes/homologadas` | None |
| **Receita Federal** | Company registration data | `/cnpj/{cnpj}` | None (public) |
| **Google Custom Search** | Contact data, strategic intelligence | Custom Search API | API Key |

### Data Points to Extract

**From PNCP:**
- Winning company CNPJ
- Contract value
- Contract date (homologation)
- Procurement object
- Sector/category

**From Receita Federal:**
- Company legal name
- Registration date
- Primary activity (CNAE)
- Size (micro, small, medium, large)

**From Web Search:**
- Email (preferably contato@, vendas@)
- Phone number
- WhatsApp (preferably business)
- Recent news/press releases
- Website URL

## 🧮 Lead Qualification Algorithm

### Dependency Score Calculation

```python
def calculate_dependency_score(cnpj: str, time_window_months: int = 12) -> float:
    """
    Calculate how dependent a company is on public procurement.

    Score = (total_public_contracts_value / estimated_annual_revenue) * 100

    High dependency: ≥ 70% (prime targets)
    Medium dependency: 40-69% (secondary targets)
    Low dependency: < 40% (discard)
    """
    # Implementation details in phase 3
    pass
```

### Qualification Criteria

| Criteria | Weight | Scoring |
|----------|--------|---------|
| **Dependency Score** | 40% | ≥70% = 10, 60-69% = 7, 50-59% = 4, <50% = 0 |
| **Recent Activity** | 20% | Win in last 30d = 10, 90d = 7, 180d = 4, >180d = 0 |
| **Sector Match** | 20% | Exact match = 10, related = 6, unrelated = 2 |
| **Contact Data Quality** | 20% | Email+Phone+WhatsApp = 10, Email+Phone = 7, Email only = 4 |

**Minimum Score:** 7/10 to be included in output

## 📝 Output Format

### Lead Profile Template

```markdown
## Lead #{N} - {Company Name}

### Contact Data
- **Email:** {email}
- **Phone:** {phone}
- **WhatsApp:** {whatsapp} ✅ (if available)
- **Website:** {url}

### Company Intelligence
- **CNPJ:** {cnpj}
- **Sector:** {sector}
- **Size:** {micro/small/medium/large}
- **Founded:** {year}

### Procurement Profile
- **Dependency Score:** {score}% 🎯
- **Recent Wins:** {count} contracts in last 12 months
- **Total Contract Value:** R$ {value}
- **Primary Sectors:** {sector1, sector2, sector3}
- **Last Win:** {date} - {contract_object}

### Strategic Intelligence
{paragraph with actionable insights from web search:
- Recent news
- Market positioning
- Pain points identified
- Competitive landscape
}

### Personalized Outreach Message

---
**Subject:** Oportunidades de Licitação em {Sector} - SmartLic

Olá, {Contact Name or Company Name},

{Personalized opening based on recent win or sector activity}

Notamos que sua empresa teve sucesso recente em licitações de {sector},
como {specific contract reference}.

Estou entrando em contato porque temos {X} novas oportunidades abertas
em {sector} que se alinham perfeitamente com o histórico de atuação da
{Company Name}.

Preparei uma planilha com estas oportunidades (anexo), incluindo:
- {X} licitações abertas em {states}
- Valores entre R$ {min} e R$ {max}
- Prazos de até {days} dias

O SmartLic é um sistema que automatiza a busca de oportunidades de
licitação em todo o Brasil, filtrando por setor, região e valor.
Empresas como a sua economizam {X} horas por semana na prospecção manual.

Gostaria de agendar 15 minutos para apresentar outras {Y} oportunidades
que identificamos para vocês?

Atenciosamente,
{Your Name}
SmartLic
{Your Contact}
---

### Qualification Score
**Overall:** {score}/10
- Dependency: {score}/10
- Activity: {score}/10
- Sector Match: {score}/10
- Contact Quality: {score}/10

---
```

## 🛠️ Implementation Phases

### Phase 1: Discovery (@analyst + @data-engineer)
**Duration:** 1 session

**Deliverables:**
1. Complete API inventory with endpoints, rate limits, authentication
2. Qualification criteria finalized
3. Lead scoring algorithm documented
4. Sample data collection from PNCP/Receita Federal

**Acceptance Criteria:**
- [ ] PNCP API tested and documented (homologated contracts endpoint)
- [ ] Receita Federal API tested and documented
- [ ] Web search strategy defined (which sources, which keywords)
- [ ] Sample dataset: 5 real companies analyzed manually

### Phase 2: Design (@architect + @data-engineer)
**Duration:** 1 session

**Deliverables:**
1. Workflow architecture diagram
2. Data model (schemas for Lead, Company, Contract)
3. Integration patterns (retry logic, rate limiting, error handling)
4. Output document structure

**Acceptance Criteria:**
- [ ] Architecture diagram approved
- [ ] Pydantic schemas defined
- [ ] Resilience patterns documented
- [ ] Output format template created

### Phase 3: Implementation (@dev)
**Duration:** 2-3 sessions

**Deliverables:**
1. `backend/lead_prospecting.py` - Core workflow logic
2. `backend/pncp_homologados_client.py` - PNCP homologated contracts client
3. `backend/receita_federal_client.py` - Receita Federal API client
4. `backend/lead_scorer.py` - Lead qualification algorithm
5. `backend/message_generator.py` - Personalized message generator
6. `.aios-core/development/tasks/acha-leads.md` - Task definition

**Acceptance Criteria:**
- [ ] `*acha-leads` invocable from AIOS
- [ ] Successfully queries PNCP for homologated contracts (last 12 months)
- [ ] Cross-references CNPJs with Receita Federal
- [ ] Calculates dependency scores
- [ ] Filters leads by qualification score (≥ 7/10)
- [ ] Performs web search for contact data
- [ ] Generates personalized messages
- [ ] Outputs ≥10 qualified leads in markdown format
- [ ] Handles API failures gracefully (retry + fallback)
- [ ] Respects rate limits (no 429 errors)

### Phase 4: Validation (@qa)
**Duration:** 1 session

**Deliverables:**
1. Test suite for lead prospecting workflow
2. Quality report (accuracy of contact data, relevance of intelligence)
3. Edge case validation (no recent contracts, incomplete data, API failures)

**Acceptance Criteria:**
- [ ] 100% of outputted leads have valid email format
- [ ] ≥80% of leads have phone numbers
- [ ] ≥50% of leads have WhatsApp
- [ ] Dependency scores mathematically correct
- [ ] Personalized messages contextually relevant (manual review)
- [ ] Workflow completes in <5 minutes for 12-month window
- [ ] No crashes on API failures (graceful degradation)

## 🚀 Success Criteria

### Quantitative
- [x] Outputs ≥10 qualified leads per invocation
- [x] Lead qualification score ≥ 7/10 average
- [x] 100% of leads have email + phone
- [x] ≥50% of leads have WhatsApp
- [x] Workflow execution time <5 minutes

### Qualitative
- [x] Strategic intelligence is actionable (not generic)
- [x] Personalized messages feel genuinely tailored (not template spam)
- [x] Leads align with SmartLic's 12 sectors
- [x] Contact data is up-to-date and verified (no dead emails/phones)

## 📦 Output Artifact

**File:** `docs/leads/leads-{YYYY-MM-DD}.md`

**Structure:**
```markdown
# Lead Prospecting Report - {Date}

**Generated by:** *acha-leads workflow
**Time Window:** Last 12 months
**Sectors:** {sectors queried}
**Total Candidates:** {N}
**Qualified Leads:** {N}

---

{Lead Profile #1}
{Lead Profile #2}
...
{Lead Profile #10+}

---

## Execution Summary
- API Calls: PNCP {N}, Receita Federal {N}, Web Search {N}
- Errors: {N} (see logs)
- Average Qualification Score: {score}/10
- Recommendation: Prioritize Leads #{x}, #{y}, #{z} (highest dependency scores)
```

## 🔧 Technical Considerations

### Rate Limiting
- PNCP: Unknown (test empirically, start with 10 req/s)
- Receita Federal: Unknown (test empirically, start with 5 req/s)
- Google Custom Search: 100 queries/day (free tier)

### Resilience
- Exponential backoff for retries (same as existing pncp_client.py)
- Fallback to partial data if web search fails
- Cache Receita Federal data (static company info)

### Privacy & Ethics
- Only use publicly available data
- No scraping of personal emails (only business emails: contato@, vendas@)
- Respect robots.txt and rate limits
- LGPD compliance: no personal data storage beyond workflow execution

## 🧪 Testing Strategy

### Unit Tests
- PNCP client for homologated contracts
- Receita Federal client
- Lead scoring algorithm
- Message personalization logic

### Integration Tests
- End-to-end workflow execution
- API failure scenarios
- Rate limiting compliance

### Manual Validation
- Review 10 sample leads for quality
- Verify contact data accuracy (spot check)
- Assess personalized message relevance

## 📚 Related Documentation

- **PNCP API Docs:** https://pncp.gov.br/api/
- **Receita Federal API:** https://www.receitafederal.gov.br/
- **Google Custom Search API:** https://developers.google.com/custom-search
- **Existing PNCP Client:** `backend/pncp_client.py`
- **Sector Configuration:** `backend/sectors.py`

## 🎯 Next Steps

1. **Squad Activation:** Activate Lead Prospecting Task Force
2. **Phase 1 Kickoff:** @analyst + @data-engineer begin discovery
3. **API Testing:** Test PNCP homologated endpoint + Receita Federal API
4. **Sample Analysis:** Manually analyze 5 real companies to validate approach
5. **Architecture Design:** @architect creates workflow architecture

---

**Squad:** Lead Prospecting Task Force (`.aios-core/development/agent-teams/squad-lead-prospecting.yaml`)
**Lead Agent:** @analyst
**Estimated Timeline:** 4-5 sessions (discovery → design → implementation → validation)
