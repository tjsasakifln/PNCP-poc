# STORY-184: Architecture Design Document

**Phase:** 2 (Design)
**Agents:** @architect + @data-engineer
**Date:** 2026-02-10
**Status:** ✅ Complete

---

## 🏗️ System Architecture

### High-Level Data Flow

```
*acha-leads CLI
    ↓
lead_prospecting.py (orchestrator)
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 1: Query PNCP (homologated contracts)         │
│ - pncp_homologados_client.py                       │
│ - Date range filter (last N months)                │
│ - Pagination handler (500/page)                    │
│ - Returns: List[ContractData]                      │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Extract unique CNPJs                        │
│ - Group by CNPJ                                     │
│ - Aggregate contract values per company             │
│ - Returns: Dict[CNPJ, List[ContractData]]          │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: DEDUPLICATION (AC10)                        │
│ - lead_deduplicator.py                              │
│ - Load cnpj-history.json                            │
│ - Filter out already-discovered CNPJs               │
│ - Returns: List[CNPJ] (new only)                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: Enrich with Receita Federal                 │
│ - receita_federal_client.py                         │
│ - Query 3 req/min (rate limited)                    │
│ - Cache results (company data static)               │
│ - Returns: Dict[CNPJ, CompanyData]                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 5: Calculate Dependency Score                  │
│ - lead_scorer.py                                    │
│ - Formula: (contract_total / annual_revenue) * 100 │
│ - Filter: score >= 70%                              │
│ - Returns: List[CompanyProfile]                     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 6: Web Search (contact data)                   │
│ - contact_searcher.py                               │
│ - Google Custom Search OR web scraping              │
│ - Extract: email, phone, WhatsApp                   │
│ - Returns: Dict[CNPJ, ContactData]                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 7: Gather Strategic Intelligence               │
│ - contact_searcher.py                               │
│ - Web search: recent news, press releases           │
│ - Returns: Dict[CNPJ, str] (intelligence summary)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 8: Generate Personalized Messages              │
│ - message_generator.py                              │
│ - OpenAI GPT-4.1-nano                               │
│ - Context: company data + recent wins + sector      │
│ - Returns: Dict[CNPJ, str] (personalized message)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 9: Qualification Scoring                       │
│ - lead_scorer.py                                    │
│ - Multi-factor: dependency + activity + sector +    │
│                 contact quality                     │
│ - Filter: score >= min_score (default 7.0)          │
│ - Returns: List[LeadProfile]                        │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 10: Update History (AC10)                      │
│ - lead_deduplicator.py                              │
│ - Add new leads to cnpj-history.json                │
│ - Update: first_discovered, last_seen, times_disc.  │
│ - Returns: int (total leads in history)             │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Step 11: Generate Markdown Report                   │
│ - report_generator.py                               │
│ - Template: docs/leads/leads-{date}.md              │
│ - Include: contact data, intelligence, message,     │
│            qualification breakdown                  │
│ - Returns: str (file path)                          │
└─────────────────────────────────────────────────────┘
    ↓
Output: docs/leads/leads-2026-02-10.md
```

---

## 📦 Module Structure

### Backend Modules (backend/)

```
backend/
├── pncp_homologados_client.py     # PNCP /contratos endpoint client
├── receita_federal_client.py      # Receita Federal API client
├── lead_scorer.py                  # Dependency + qualification scoring
├── contact_searcher.py             # Web search for contact data
├── message_generator.py            # OpenAI message generation
├── lead_deduplicator.py            # History management (AC10)
├── report_generator.py             # Markdown output generator
├── lead_prospecting.py             # Main orchestrator
└── schemas_lead_prospecting.py    # Pydantic schemas
```

---

## 📐 Data Models (Pydantic Schemas)

### Core Schemas

```python
# schemas_lead_prospecting.py

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class ContractData(BaseModel):
    """Single contract from PNCP API."""
    cnpj: str = Field(..., description="CNPJ of winning company (14 digits)")
    company_name: str = Field(..., description="Razão social")
    contract_value: Decimal = Field(..., description="Contract value (R$)")
    contract_date: date = Field(..., description="Signature date")
    contract_object: str = Field(..., description="Contract description")
    uf: str = Field(..., description="State (UF)")
    municipality: str = Field(..., description="Municipality")
    contract_id: str = Field(..., description="Unique PNCP contract ID")


class CompanyData(BaseModel):
    """Company data from Receita Federal API."""
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    situacao: str = Field(..., description="ATIVA, BAIXADA, etc.")
    porte: str = Field(..., description="MEI, ME, EPP, GRANDE")
    capital_social: Decimal
    cnae_principal: str = Field(..., description="Primary CNAE description")
    cnae_codigo: str = Field(..., description="CNAE code")
    data_abertura: date
    municipio: str
    uf: str
    email: Optional[str] = None
    telefone: Optional[str] = None


class ContactData(BaseModel):
    """Contact information from web search."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, description="Format: +55 XX XXXXX-XXXX")
    whatsapp: Optional[str] = Field(None, description="Format: +55 XX XXXXX-XXXX")
    website: Optional[str] = None
    source: str = Field(..., description="Where data was found (e.g., 'company website', 'Google Maps')")


class StrategicIntelligence(BaseModel):
    """Strategic intelligence from web search."""
    summary: str = Field(..., description="1-2 paragraph summary")
    recent_news: List[str] = Field(default_factory=list, description="Recent news headlines")
    market_positioning: Optional[str] = None
    pain_points: Optional[str] = None


class DependencyScore(BaseModel):
    """Dependency score calculation."""
    total_contract_value: Decimal = Field(..., description="Sum of all contracts (R$)")
    estimated_annual_revenue: Decimal = Field(..., description="Estimated annual revenue (R$)")
    dependency_percentage: float = Field(..., description="(contracts / revenue) * 100")
    dependency_level: str = Field(..., description="HIGH (>=70%), MEDIUM (40-69%), LOW (<40%)")
    contract_count: int = Field(..., description="Number of contracts in period")


class QualificationScore(BaseModel):
    """Multi-factor qualification score."""
    dependency_score: float = Field(..., ge=0, le=10, description="Weighted 40%")
    activity_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    sector_match_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    contact_quality_score: float = Field(..., ge=0, le=10, description="Weighted 20%")
    overall_score: float = Field(..., ge=0, le=10, description="Weighted average")


class LeadProfile(BaseModel):
    """Complete lead profile for output."""
    # Identification
    cnpj: str
    company_name: str
    nome_fantasia: Optional[str] = None

    # Company data
    company_data: CompanyData

    # Procurement profile
    contracts: List[ContractData]
    dependency_score: DependencyScore

    # Contact information
    contact_data: ContactData

    # Strategic intelligence
    intelligence: StrategicIntelligence

    # Personalized message
    personalized_message: str

    # Qualification
    qualification: QualificationScore

    # Metadata
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    sectors: List[str] = Field(default_factory=list, description="Matched sectors")


class LeadHistory(BaseModel):
    """Lead history entry (AC10)."""
    cnpj: str
    company_name: str
    first_discovered: datetime
    last_seen: datetime
    times_discovered: int = 1
    qualification_score: float
    contact_made: bool = False
    converted: bool = False
    notes: str = ""


class LeadHistoryFile(BaseModel):
    """Lead history file structure (cnpj-history.json)."""
    version: str = "1.0"
    last_updated: datetime
    total_leads: int
    leads: List[LeadHistory]
```

---

## 🔌 Integration Patterns

### 1. Retry Strategy (All API Clients)

**Pattern:** Exponential backoff with jitter (reuse from `pncp_client.py`)

```python
from config import RetryConfig

retry_config = RetryConfig(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0,
    exponential_base=2,
    jitter=True,
    retryable_status_codes=[429, 500, 502, 503, 504]
)
```

### 2. Rate Limiting (Receita Federal Client)

**Challenge:** 3 requests/minute strict limit

**Solution:** Token bucket algorithm

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int = 3, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def wait_if_needed(self):
        """Block until a request slot is available."""
        now = time.time()

        # Remove requests outside time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # If at limit, wait for oldest request to age out
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            if sleep_time > 0:
                time.sleep(sleep_time)

        # Record this request
        self.requests.append(time.time())
```

### 3. Caching (Receita Federal Client)

**Strategy:** File-based cache (company data is static)

```python
import json
from pathlib import Path
from typing import Optional

class CompanyDataCache:
    def __init__(self, cache_dir: str = ".cache/receita_federal"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, cnpj: str) -> Optional[CompanyData]:
        """Get cached company data."""
        cache_file = self.cache_dir / f"{cnpj}.json"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return CompanyData(**data)
        return None

    def set(self, cnpj: str, company_data: CompanyData):
        """Cache company data."""
        cache_file = self.cache_dir / f"{cnpj}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(company_data.model_dump(), f, indent=2, ensure_ascii=False, default=str)
```

### 4. Error Handling

**Pattern:** Graceful degradation

```python
def enrich_with_receita_federal(cnpjs: List[str]) -> Dict[str, Optional[CompanyData]]:
    """Enrich CNPJs with Receita Federal data (with graceful degradation)."""
    results = {}

    for cnpj in cnpjs:
        try:
            # Try cache first
            company_data = cache.get(cnpj)
            if company_data:
                results[cnpj] = company_data
                continue

            # Query API with rate limiting
            rate_limiter.wait_if_needed()
            company_data = receita_federal_client.query(cnpj)

            # Cache result
            cache.set(cnpj, company_data)
            results[cnpj] = company_data

        except ReceitaFederalAPIError as e:
            logger.warning(f"Receita Federal API error for CNPJ {cnpj}: {e}")
            results[cnpj] = None  # Continue with partial data

        except Exception as e:
            logger.error(f"Unexpected error enriching CNPJ {cnpj}: {e}")
            results[cnpj] = None

    return results
```

---

## 📝 Output Template

### Markdown Report Structure

```markdown
# Lead Prospecting Report - {date}

**Generated by:** *acha-leads workflow
**Parameters:** sectors={sectors}, months={months}, min_score={min_score}
**Execution Time:** {duration}

## Summary

**Deduplication:**
- Total Candidates: {total_candidates}
- Already in History: {in_history}
- **NEW Leads Processed:** {new_processed}
- **NEW Qualified Leads:** {new_qualified}

**History Status:**
- Total Leads in History: {total_in_history}
- Contacted: {contacted} ({contacted_pct}%)
- Converted: {converted} ({converted_pct}%)

---

## Lead #1 - [NEW] {company_name} ⭐ (Score: {score}/10)

### Contact Data
- **Email:** {email}
- **Phone:** {phone}
- **WhatsApp:** {whatsapp} ✅
- **Website:** {website}

### Company Intelligence
- **CNPJ:** {cnpj}
- **Nome Fantasia:** {nome_fantasia}
- **Sector:** {sector}
- **Size:** {porte}
- **Founded:** {data_abertura}
- **Primary Activity:** {cnae_principal}

### Procurement Profile
- **Dependency Score:** {dependency_pct}% 🎯 ({dependency_level})
- **Recent Wins:** {contract_count} contracts in last {months} months
- **Total Contract Value:** R$ {total_value:,.2f}
- **Primary Sectors:** {sectors_list}
- **Last Win:** {last_contract_date} - {last_contract_object} (R$ {last_contract_value:,.2f})

### Strategic Intelligence

{intelligence_summary}

**Recent Activity:**
- {news_1}
- {news_2}

### Personalized Outreach Message

```
Subject: Oportunidades de Licitação em {sector} - SmartLic

{personalized_message}
```

### Qualification Score Breakdown
- **Dependency:** {dep_score}/10 ({dependency_pct}% - Weight: 40%)
- **Recent Activity:** {activity_score}/10 (Last win {days_ago} days ago - Weight: 20%)
- **Sector Match:** {sector_score}/10 (Match: {match_type} - Weight: 20%)
- **Contact Quality:** {contact_score}/10 (Email+Phone+WhatsApp - Weight: 20%)
- **Overall:** {overall_score}/10 ⭐

---

{repeat for all leads}

---

## Execution Details

**API Calls:**
- PNCP: {pncp_calls} requests ({pncp_success} successful)
- Receita Federal: {rf_calls} requests ({rf_cached} cached, {rf_success} new)
- Web Search: {web_search_calls} queries

**Performance:**
- Execution Time: {execution_time}
- Candidates Analyzed: {total_candidates}
- Qualified Leads: {qualified_leads}
- Disqualified (low score): {disqualified}
- Incomplete Data: {incomplete}

**Recommendations:**
1. **High Priority:** Leads #{ids} (dependency score ≥ 85%)
2. **Immediate Action:** Leads with recent wins in last 30 days
3. **Follow-up Strategy:** Attach Excel with {n} current opportunities in {sectors}

---

**Generated:** {timestamp}
**Workflow Version:** 1.0.0
**Squad:** Lead Prospecting Task Force
```

---

## 🎯 Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| **Execution Time** | <5 minutes | Parallel PNCP queries, async processing |
| **PNCP Queries** | ~347 pages × 500 items | Pagination optimization |
| **Receita Federal Queries** | 3 req/min (180/hour) | Aggressive caching + rate limiter |
| **Web Search Queries** | 100/day (free tier) | Batch processing, prioritize high-value leads |
| **Memory Usage** | <500 MB | Stream processing, don't load all contracts at once |

---

## 🔒 Security & Privacy

### Data Handling

- **Personal Data:** ONLY CNPJ (public registry) - NO personal information stored
- **Contact Data:** Business emails/phones (publicly available) - NO personal contacts
- **LGPD Compliance:** CNPJ is public data, no consent required
- **History Storage:** Local file system (docs/leads/history/) - NOT in database
- **Access Control:** File permissions restrict access to history files

### API Keys

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
GOOGLE_CUSTOM_SEARCH_API_KEY=...
GOOGLE_CUSTOM_SEARCH_ENGINE_ID=...
```

---

## ✅ Design Approval Criteria

- [x] Architecture diagram complete
- [x] All Pydantic schemas defined
- [x] Integration patterns documented
- [x] Rate limiting strategy specified
- [x] Caching strategy specified
- [x] Error handling patterns defined
- [x] Output template created
- [x] Performance targets set
- [x] Security considerations documented

**Status:** ✅ DESIGN COMPLETE - Ready for Phase 3 (Implementation)

---

**Architect:** @architect
**Data Engineer:** @data-engineer
**Date:** 2026-02-10
**Next Phase:** Implementation (@dev)
