# STORY-184: Lead Prospecting Workflow (*acha-leads)

**Status:** 📋 Planning
**Priority:** P1 (High - Revenue Generation)
**Squad:** Lead Prospecting Task Force
**Lead Agent:** @analyst
**Estimated Effort:** 4-5 sessions

## 🎯 Business Objective

Criar um workflow cirúrgico de prospecção que identifica empresas altamente dependentes de licitações públicas e gera dados de contato + mensagens personalizadas para conversão em assinantes do SmartLic.

### Success Metrics
- ≥10 leads qualificados por execução
- Taxa de conversão ≥15% (leads → assinantes)
- Tempo de execução <5 minutos
- 100% dos leads com email + telefone

## 📝 User Story

**Como** comercial do SmartLic
**Quero** executar `*acha-leads` e receber uma lista de empresas que dependem de licitações
**Para que** eu possa fazer contato imediato com mensagem personalizada + planilha de oportunidades

## 🔍 Context

O SmartLic busca licitações **abertas** (recebendo propostas), mas existem empresas que já vencem licitações regularmente e ainda não conhecem o sistema. Essas empresas são **leads perfeitos** porque:

1. **Provam demanda** - Já participam e vencem licitações
2. **Pain point claro** - Precisam encontrar oportunidades continuamente
3. **Orçamento disponível** - Já têm fluxo de receita de contratos públicos
4. **Ciclo de vendas curto** - Entendem o valor imediatamente

**Diferencial:** Não vamos buscar leads aleatórios, mas empresas onde licitações públicas são **fonte primária de receita** (≥70% do faturamento).

## 🏗️ Technical Architecture

### Data Flow

```
User: *acha-leads --sectors uniformes --months 12
    ↓
[1] PNCP API: Query homologated contracts (last 12 months)
    ↓
[2] Extract: Winning companies (CNPJs)
    ↓
[3] Receita Federal API: Enrich company data
    ↓
[4] Calculate: Dependency score (% revenue from public contracts)
    ↓
[5] Filter: Keep only high-dependency companies (≥70%)
    ↓
[6] Web Search: Extract contact data (email, phone, WhatsApp)
    ↓
[7] Web Search: Gather strategic intelligence (news, market positioning)
    ↓
[8] OpenAI: Generate personalized outreach message
    ↓
[9] Score: Multi-factor qualification (0-10)
    ↓
[10] Filter: Keep only score ≥7/10
    ↓
[11] Output: Markdown document with ≥10 qualified leads
```

### APIs Required

| API | Purpose | Rate Limit | Auth |
|-----|---------|------------|------|
| **PNCP** | Homologated contracts | ~10 req/s (TBD) | None |
| **Receita Federal** | Company data (CNPJ) | ~5 req/s (TBD) | None |
| **Google Custom Search** | Contact data + intelligence | 100/day (free) | API Key |
| **OpenAI** | Personalized messages | 10,000 TPM | API Key |

## 📋 Acceptance Criteria

### Functional Requirements

#### AC1: PNCP Integration (Homologated Contracts)
- [ ] Create `backend/pncp_homologados_client.py`
- [ ] Query `/api/consulta/v1/contratacoes/homologadas` endpoint
- [ ] Filter by date range (last N months, default 12)
- [ ] Filter by sector keywords (if --sectors provided)
- [ ] Extract: CNPJ, company name, contract value, date, object
- [ ] Handle pagination (500 items/page)
- [ ] Retry logic (exponential backoff, max 5 retries)
- [ ] Rate limiting compliance (10 req/s)
- [ ] Timeout: 30s per request

**Test Case:**
```python
client = PNCPHomologadosClient()
contracts = client.buscar_homologadas(
    meses=12,
    setores=["uniformes"]
)
assert len(contracts) > 0
assert all(c["cnpj_vencedor"] for c in contracts)
```

#### AC2: Receita Federal Integration
- [ ] Create `backend/receita_federal_client.py`
- [ ] Query CNPJ data: legal name, CNAE, size, founding date
- [ ] Cache results (company data is static)
- [ ] Retry logic (exponential backoff, max 3 retries)
- [ ] Rate limiting (5 req/s)
- [ ] Timeout: 20s per request
- [ ] Graceful handling of invalid CNPJs

**Test Case:**
```python
client = ReceitaFederalClient()
data = client.consultar_cnpj("00000000000191")  # Banco do Brasil
assert data["razao_social"] == "BANCO DO BRASIL SA"
assert data["cnae_principal"]
```

#### AC3: Dependency Score Calculation
- [ ] Create `backend/lead_scorer.py`
- [ ] Function: `calculate_dependency_score(cnpj, time_window_months)`
- [ ] Formula: (total_public_contracts_value / estimated_annual_revenue) * 100
- [ ] Revenue estimation (from Receita Federal or CNAE average)
- [ ] Return score 0-100%
- [ ] Flag high-dependency (≥70%), medium (40-69%), low (<40%)

**Test Case:**
```python
scorer = LeadScorer()
score = scorer.calculate_dependency_score(
    cnpj="12345678000190",
    time_window_months=12
)
assert 0 <= score <= 100
```

#### AC4: Web Search for Contact Data
- [ ] Implement web search using Google Custom Search API
- [ ] Extract email (prioritize: contato@, vendas@, comercial@)
- [ ] Extract phone number (format: +55 XX XXXXX-XXXX)
- [ ] Extract WhatsApp (if available)
- [ ] Extract website URL
- [ ] Validate email format (regex)
- [ ] Validate phone format (regex)
- [ ] Timeout: 10s per company
- [ ] Fallback: Mark as "incomplete contact data" if no email found

**Test Case:**
```python
searcher = ContactSearcher()
contact = searcher.find_contact_data("EMPRESA EXEMPLO LTDA", "12345678000190")
assert contact["email"]  # Required
assert "@" in contact["email"]
```

#### AC5: Strategic Intelligence Gathering
- [ ] Web search for company news (last 12 months)
- [ ] Extract press releases, awards, recent wins
- [ ] Identify pain points or market challenges
- [ ] Summarize in 1-2 paragraphs (actionable intelligence)
- [ ] Timeout: 10s per company
- [ ] Fallback: Generic intelligence if no specific data found

**Test Case:**
```python
intel = searcher.gather_intelligence("EMPRESA EXEMPLO LTDA")
assert len(intel) > 50  # At least 50 characters
assert "licitação" in intel.lower() or "contrato" in intel.lower()
```

#### AC6: Lead Qualification Scoring
- [ ] Multi-factor scoring algorithm in `backend/lead_scorer.py`
- [ ] Factor 1: Dependency Score (40% weight)
  - ≥70% = 10/10, 60-69% = 7/10, 50-59% = 4/10, <50% = 0/10
- [ ] Factor 2: Recent Activity (20% weight)
  - Win in last 30d = 10/10, 90d = 7/10, 180d = 4/10, >180d = 0/10
- [ ] Factor 3: Sector Match (20% weight)
  - Exact match = 10/10, related = 6/10, unrelated = 2/10
- [ ] Factor 4: Contact Data Quality (20% weight)
  - Email+Phone+WhatsApp = 10/10, Email+Phone = 7/10, Email only = 4/10
- [ ] Return overall score 0-10 (weighted average)
- [ ] Filter: Keep only score ≥ min_score (default 7.0)

**Test Case:**
```python
scorer = LeadScorer()
score = scorer.calculate_qualification_score(
    dependency_score=85,
    last_win_days_ago=15,
    sector_match="exact",
    has_email=True,
    has_phone=True,
    has_whatsapp=True
)
assert score >= 7.0
```

#### AC7: Personalized Message Generation
- [ ] Create `backend/message_generator.py`
- [ ] Use OpenAI GPT-4.1-nano for message generation
- [ ] Input: company data, recent wins, sector, strategic intelligence
- [ ] Output: Personalized email body (150 words max)
- [ ] Requirements:
  - Professional but warm tone
  - Reference specific recent win
  - Mention SmartLic value proposition
  - Offer immediate value (attached opportunities)
  - Call to action (15-minute intro call)
- [ ] Structured output via Pydantic
- [ ] Fallback: Template-based message if OpenAI fails

**Test Case:**
```python
generator = MessageGenerator()
message = generator.generate_message(
    company_name="EMPRESA EXEMPLO LTDA",
    sector="uniformes",
    recent_win="Fornecimento de uniformes para Prefeitura de SP",
    intelligence="Empresa atua há 15 anos no setor público"
)
assert len(message) > 0
assert "EMPRESA EXEMPLO" in message
assert "uniformes" in message.lower()
```

#### AC8: Output Document Generation
- [ ] Generate markdown file: `docs/leads/leads-{YYYY-MM-DD}.md`
- [ ] Structure: Header → Lead Profiles → Execution Summary
- [ ] Lead Profile includes:
  - Contact data (email, phone, WhatsApp, website)
  - Company intelligence (CNPJ, sector, size, founded)
  - Procurement profile (dependency score, recent wins, contract values)
  - Strategic intelligence (actionable insights)
  - Personalized message (ready to copy/paste)
  - Qualification score breakdown
- [ ] Execution Summary includes:
  - Parameters used (sectors, months, min_score)
  - API call statistics
  - Performance metrics
  - Recommendations (prioritized leads)

**Test Case:**
```python
# Execute workflow
output_path = execute_acha_leads(sectors=["uniformes"], months=12, min_score=7.0)

# Verify output
assert os.path.exists(output_path)
with open(output_path) as f:
    content = f.read()
assert "# Lead Prospecting Report" in content
assert "## Lead #1" in content
```

#### AC9: Workflow Execution (*acha-leads)
- [ ] Create task definition: `.aios-core/development/tasks/acha-leads.md`
- [ ] Invocable via: `*acha-leads [--sectors X,Y] [--months N] [--min-score S]`
- [ ] Execute all steps sequentially (see architecture diagram)
- [ ] Handle errors gracefully (retry, fallback, logging)
- [ ] Respect rate limits (PNCP, Receita Federal, Google)
- [ ] Complete in <5 minutes
- [ ] Output ≥10 qualified leads (if available)
- [ ] If <10 leads, lower min_score by 1.0 and retry once

**Test Case:**
```bash
*acha-leads --sectors uniformes --months 6 --min-score 7.0

# Expected output:
# ✅ PNCP: 234 contratos homologados encontrados
# ✅ Receita Federal: 187 CNPJs enriquecidos
# ✅ Dependency Score: 45 empresas com score ≥70%
# ✅ Contact Data: 32 empresas com dados completos
# ✅ Qualification: 12 leads com score ≥7.0
# 📄 Relatório gerado: docs/leads/leads-2026-02-10.md
```

n#### AC10: Lead Deduplication
- [ ] Create `docs/leads/history/` directory structure
- [ ] Implement `cnpj-history.json` storage format (see STORY-184-lead-deduplication-spec.md)
- [ ] Implement `filter_new_leads()` function
- [ ] Implement `update_history()` function
- [ ] Integrate deduplication into main workflow
- [ ] Test: Second execution should NOT return same leads as first
- [ ] History metadata: track first_discovered, last_seen, times_discovered
- [ ] Future enhancement: CRM commands (*acha-leads-history, *acha-leads-update)

**Test Case:**
```python
# First execution
leads_1 = execute_acha_leads(sectors=["uniformes"], months=12, min_score=7.0)
assert len(leads_1) >= 10

# Second execution (immediately after)
leads_2 = execute_acha_leads(sectors=["uniformes"], months=12, min_score=7.0)
assert len(leads_2) == 0  # No new leads

# Verify history
assert os.path.exists("docs/leads/history/cnpj-history.json")
```

**Business Value:**
- Guarantees 100% fresh leads every execution
- Prevents duplicate outreach (better prospect experience)
- Saves ~50 minutes per execution (no wasted research)
- Foundation for future CRM integration
### Non-Functional Requirements

#### NFR1: Performance
- [ ] Workflow execution time <5 minutes for 12-month window
- [ ] PNCP pagination efficient (handle 10,000+ contracts)
- [ ] Receita Federal caching reduces redundant API calls
- [ ] Parallel web searches where possible

#### NFR2: Resilience
- [ ] Exponential backoff on API failures (same as pncp_client.py)
- [ ] Circuit breaker pattern for unstable APIs
- [ ] Graceful degradation (proceed with partial data)
- [ ] No crashes on API timeouts or rate limits

#### NFR3: Data Quality
- [ ] 100% of leads have valid email format
- [ ] ≥80% of leads have phone numbers
- [ ] ≥50% of leads have WhatsApp
- [ ] Dependency scores mathematically correct (unit tested)
- [ ] Personalized messages contextually relevant (manual review)

#### NFR4: Privacy & Ethics
- [ ] Only use publicly available data
- [ ] No scraping of personal emails (only business: contato@, vendas@, etc.)
- [ ] Respect robots.txt and rate limits
- [ ] LGPD compliance (no personal data storage beyond execution)
- [ ] Clear disclosure in outreach messages (no spam)

#### NFR5: Maintainability
- [ ] Modular design (separate clients, scorers, generators)
- [ ] Type hints on all functions (Python 3.11+)
- [ ] Docstrings (Google style)
- [ ] Unit tests for each module (≥70% coverage)
- [ ] Integration test for end-to-end workflow

## 📁 File List

### New Files (To Be Created)

**Backend Modules:**
- [ ] `backend/pncp_homologados_client.py` - PNCP client for homologated contracts
- [ ] `backend/receita_federal_client.py` - Receita Federal API client
- [ ] `backend/lead_scorer.py` - Lead qualification algorithm
- [ ] `backend/message_generator.py` - Personalized message generation
- [ ] `backend/contact_searcher.py` - Web search for contact data

**Tests:**
- [ ] `backend/tests/test_pncp_homologados_client.py`
- [ ] `backend/tests/test_receita_federal_client.py`
- [ ] `backend/tests/test_lead_scorer.py`
- [ ] `backend/tests/test_message_generator.py`
- [ ] `backend/tests/test_contact_searcher.py`
- [ ] `backend/tests/test_acha_leads_workflow.py` (integration)

**Documentation:**
- [ ] `docs/workflows/lead-prospecting-workflow.md` ✅ (Created)
- [ ] `.aios-core/development/tasks/acha-leads.md` ✅ (Created)
- [ ] `.aios-core/development/agent-teams/squad-lead-prospecting.yaml` ✅ (Created)

**Output (Generated by Workflow):**
- `docs/leads/leads-{YYYY-MM-DD}.md` (auto-generated)

### Modified Files (If Any)

- [ ] `backend/requirements.txt` - Add new dependencies (if needed)
- [ ] `.env.example` - Document GOOGLE_CUSTOM_SEARCH_API_KEY (optional)

## 🧪 Testing Strategy

### Unit Tests (70% Coverage)
- PNCP Homologados Client (pagination, filtering, error handling)
- Receita Federal Client (CNPJ lookup, caching, retries)
- Lead Scorer (dependency calculation, qualification scoring)
- Message Generator (prompt engineering, fallback)
- Contact Searcher (web search, data extraction, validation)

### Integration Tests
- End-to-end workflow execution with real APIs (staging)
- API failure scenarios (mock 500/429 responses)
- Rate limiting compliance (no 429 errors)
- Output document validation (structure, data integrity)

### Manual Validation
- Execute `*acha-leads --sectors uniformes --months 3`
- Review 10 sample leads for quality
- Verify contact data accuracy (spot check 5 emails/phones)
- Assess personalized message relevance (manual review)
- Confirm overall workflow experience (speed, output clarity)

## 🚀 Implementation Plan

### Phase 1: Discovery (1 session)
**Agents:** @analyst + @data-engineer

**Deliverables:**
- [ ] PNCP API tested (homologated contracts endpoint)
- [ ] Receita Federal API tested (CNPJ lookup endpoint)
- [ ] Google Custom Search API tested (contact data extraction)
- [ ] Sample dataset: 5 real companies analyzed manually
- [ ] Qualification criteria finalized
- [ ] Lead scoring algorithm documented

**Acceptance:**
- [ ] All APIs successfully queried with sample data
- [ ] Manual analysis confirms approach viability
- [ ] Scoring algorithm mathematically sound

### Phase 2: Design (1 session)
**Agents:** @architect + @data-engineer

**Deliverables:**
- [ ] Workflow architecture diagram
- [ ] Data models (Pydantic schemas for Lead, Company, Contract)
- [ ] Integration patterns (retry, rate limiting, caching)
- [ ] Output document template

**Acceptance:**
- [ ] Architecture diagram approved by @analyst
- [ ] Pydantic schemas defined and validated
- [ ] Resilience patterns documented

### Phase 3: Implementation (2-3 sessions)
**Agents:** @dev

**Deliverables:**
- [ ] `pncp_homologados_client.py` implemented
- [ ] `receita_federal_client.py` implemented
- [ ] `lead_scorer.py` implemented (dependency + qualification)
- [ ] `contact_searcher.py` implemented (web search)
- [ ] `message_generator.py` implemented (OpenAI integration)
- [ ] `*acha-leads` task integrated into AIOS
- [ ] Unit tests for all modules (≥70% coverage)

**Acceptance:**
- [ ] All modules pass unit tests
- [ ] `*acha-leads` invocable from AIOS CLI
- [ ] Test execution generates valid output document
- [ ] Linting passes (ruff, mypy)

### Phase 4: Validation (1 session)
**Agents:** @qa

**Deliverables:**
- [ ] Integration test suite
- [ ] Quality report (contact data accuracy, message relevance)
- [ ] Edge case validation (API failures, incomplete data)
- [ ] Performance benchmarking (execution time)

**Acceptance:**
- [ ] All tests pass (unit + integration)
- [ ] Quality report shows ≥80% contact data accuracy
- [ ] Execution time <5 minutes for 12-month window
- [ ] No crashes on API failures (graceful degradation)

## 🔗 Dependencies

### External APIs
- PNCP API (homologated contracts) - PUBLIC
- Receita Federal API (CNPJ lookup) - PUBLIC
- Google Custom Search API (contact data) - REQUIRES API KEY (optional)
- OpenAI API (message generation) - REQUIRES API KEY

### Environment Variables
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (for enhanced web search)
GOOGLE_CUSTOM_SEARCH_API_KEY=...
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=...
```

### Backend Dependencies (requirements.txt)
```
# Already in requirements.txt:
httpx>=0.26.0
pydantic>=2.6.0
openai>=1.10.0

# May need to add:
beautifulsoup4>=4.12.0  # For web scraping
google-api-python-client>=2.100.0  # For Google Custom Search
```

## 🎯 Success Criteria

### Quantitative
- [x] ≥10 qualified leads per execution
- [x] Average qualification score ≥7.0
- [x] 100% of leads have email + phone
- [x] ≥50% of leads have WhatsApp
- [x] Execution time <5 minutes
- [x] 70% test coverage (backend modules)

### Qualitative
- [x] Strategic intelligence is actionable (not generic)
- [x] Personalized messages feel genuinely tailored (not spam)
- [x] Leads align with SmartLic's 12 sectors
- [x] Contact data is up-to-date (no dead emails/phones)
- [x] Workflow experience is smooth (clear progress, helpful errors)

### Business Impact
- [x] Conversion rate ≥15% (leads → assinantes) - **TRACK OVER TIME**
- [x] Reduces manual prospecting time from 8h/week to <1h/week
- [x] Scalable to all 12 sectors (not just uniformes)

## 📚 Related Documentation

- **Workflow Architecture:** `docs/workflows/lead-prospecting-workflow.md`
- **Task Definition:** `.aios-core/development/tasks/acha-leads.md`
- **Squad Configuration:** `.aios-core/development/agent-teams/squad-lead-prospecting.yaml`
- **Existing PNCP Client:** `backend/pncp_client.py` (reference for resilience patterns)
- **Sector Definitions:** `backend/sectors.py`
- **PNCP API Docs:** https://pncp.gov.br/api/
- **Receita Federal API:** https://www.receitafederal.gov.br/

## 🏁 Next Steps

1. **Squad Activation:** Activate Lead Prospecting Task Force
2. **Phase 1 Kickoff:** @analyst + @data-engineer begin discovery
3. **API Testing:** Test PNCP homologated endpoint + Receita Federal API
4. **Sample Analysis:** Manually analyze 5 real companies to validate approach
5. **Architecture Design:** @architect creates workflow architecture

---

**Created:** 2026-02-10
**Last Updated:** 2026-02-10
**Estimated Delivery:** 4-5 sessions (TBD based on Phase 1 findings)
