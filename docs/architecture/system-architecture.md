# BidIQ Uniformes - System Architecture Documentation

**Project:** BidIQ Uniformes - POC v0.2
**Date:** January 2026
**Version:** 1.0
**Status:** BROWNFIELD DISCOVERY - PHASE 1
**Documented by:** @architect

---

## Executive Summary

BidIQ Uniformes is a **specialized procurement discovery system** for Brazil's public procurement market (PNCP - Portal Nacional de Contratações Públicas). It automates the identification of uniform/apparel procurement contracts matching specific business criteria, with intelligent filtering, Excel report generation, and AI-powered executive summaries.

**Core Value Proposition:**
- Automate manual PNCP searches for procurement opportunities
- Filter by state, value range, and keyword matching
- Generate downloadable Excel reports with rich formatting
- Provide AI-powered executive summaries (GPT-4.1-nano)
- Support multiple simultaneous searches

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER (Browser)                             │
│              Next.js 14+ SPA at localhost:3000                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP/REST
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│         FRONTEND LAYER (Next.js App Router)                     │
│                                                                  │
│  Components:                                                     │
│  - UF Multi-Select (27 states)                                  │
│  - Date Range Picker (default: last 7 days)                    │
│  - Results Display with GPT Summary Cards                       │
│  - Excel Download Manager                                       │
│  - Loading/Error States                                         │
│                                                                  │
│  State: React Hooks (useState)                                  │
│  Styling: Tailwind CSS 3.4+                                    │
│  Type Safety: TypeScript 5.3+                                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ REST/POST to /api/buscar
                      │ GET /api/download?id=...
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│        BACKEND LAYER (FastAPI 0.110+ Python 3.11+)             │
│                                                                  │
│  Endpoints:                                                      │
│  - POST /api/buscar → Search & filter & summarize               │
│  - GET /api/download → Serve generated Excel                    │
│                                                                  │
│  Architecture Layers:                                            │
│  1. HTTP Client (resilient with retry logic)                   │
│  2. Filtering Engine (sequential fail-fast)                    │
│  3. LLM Integration (GPT-4.1-nano summaries)                   │
│  4. Excel Generator (openpyxl with styling)                    │
│  5. Pydantic Schemas (type validation)                         │
│                                                                  │
│  State: In-memory download cache (10min TTL)                   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS to PNCP API
                      │ HTTPS to OpenAI API
                      ↓
┌────────────────────────────────────────────────────────────────┐
│              EXTERNAL APIs (Third-Party)                       │
│                                                                 │
│  1. PNCP API (pncp.gov.br)                                    │
│     - Unstable, requires robust retry logic                   │
│     - Rate limiting: 429 responses                            │
│     - Max 500 items/page pagination                           │
│     - Response: JSON with bid details                         │
│                                                                 │
│  2. OpenAI API (api.openai.com)                               │
│     - Model: gpt-4.1-nano                                     │
│     - Structured output: Pydantic ResumoLicitacoes            │
│     - Max 500 tokens, temp=0.3                                │
│     - Fallback: Return results without LLM                    │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture (`frontend/app/`)

```
app/
├── page.tsx                    # Main SPA (UF selector, date picker, results)
├── layout.tsx                  # Root layout (global styles, providers)
├── api/
│   ├── buscar/route.ts         # POST /api/buscar (proxy to backend)
│   └── download/route.ts       # GET /api/download (serve Excel)
└── [components/]               # (To be created per atomic design)
```

**State Management:**
- `useState` hooks for UF selections, date range, results
- In-memory download cache with 10-minute TTL
- Future: Consider Redis for distributed caching

**Key Features:**
- Multi-select UF buttons (27 Brazilian states)
- Date range picker (defaults to last 7 days)
- Loading skeleton during search
- Error boundaries with user-friendly messages
- Direct Excel download from cache
- Display of GPT-generated summaries

**Type Safety:**
- TypeScript strict mode enabled
- Interfaces for API responses
- No `any` types

### 2.2 Backend Architecture (`backend/`)

**Core Modules:**

#### 1. **pncp_client.py** - Resilient HTTP Client

```python
class PNCPClient:
    # Exponential backoff retry: base 2s, max 60s, 5 retries max
    # Rate limiting: 10 req/s (100ms minimum between requests)
    # Circuit breaker pattern for API failures
    # Handles 429 rate limits with Retry-After header
    # Automatic pagination with fetch_all() generator

    async def fetch_all(
        self,
        ufs: list[str],
        data_inicio: str,     # YYYY-MM-DD
        data_fim: str         # YYYY-MM-DD
    ) -> AsyncGenerator[dict]:
        """Yields all matching bids across all pages"""
```

**Resilience Strategy:**
- Retry on: 429 (rate limit), 5xx server errors
- Not retried: 4xx client errors (e.g., invalid params)
- Backoff formula: `min(base * 2^attempt, max) + jitter`
- Timeout: 30 seconds per request

#### 2. **filter.py** - Keyword-Based Filtering Engine

```python
KEYWORDS_UNIFORMES = {
    'uniforme', 'jaleco', 'fardamento', 'calça', 'camiseta',
    'boné', 'meia', 'sapato', 'luva', 'proteção', ...
}  # ~50 terms total

KEYWORDS_EXCLUSAO = {
    'militar', 'polícia', 'segurança', ...  # False positive prevention
}

class FilterEngine:
    # Fail-fast sequential filters (optimization)
    # 1. UF check (fastest)
    # 2. Value range (R$ 50k - R$ 5M)
    # 3. Keyword matching (most expensive)
    # 4. Status/date validation

    def apply_filters(licitacao: dict) -> tuple[bool, str | None]:
        """Returns (approved: bool, rejection_reason: str | None)"""
```

**Filtering Logic:**
- Unicode normalization for consistent matching
- Word boundary regex for precision (not partial matches)
- All filters must pass (AND logic)
- Value thresholds: R$ 50k minimum, R$ 5M maximum

#### 3. **excel.py** - Excel Report Generator

```python
class ExcelGenerator:
    # openpyxl with styled formatting
    # Green header (#2E7D32) with bold, white text
    # Auto-width columns based on content
    # Frozen header row (first row stays visible)
    # Currency formatting for value columns
    # Hyperlinks to PNCP URLs
    # Metadata sheet with generation stats

    def create_report(
        bids: list[dict],
        metadata: dict
    ) -> bytes:
        """Returns Excel file as bytes"""
```

**Report Structure:**
```
Columns:
- Código (codigoCompra)
- Objeto (objetoCompra - shortened to 200 chars)
- Órgão (nomeOrgao)
- UF (uf)
- Município (municipio)
- Valor (valorTotalEstimado) - currency format
- Modalidade (modalidadeCompra)
- Datas (dataAberturaProposta - dataFechamentoProposta)
- Status (statusCompra)
- Link (hyperlink to PNCP)

Metadata Sheet:
- Data de geração
- Total de registros
- Filtros aplicados
- Tempo de processamento
```

#### 4. **llm.py** - GPT-4.1-nano Integration

```python
class LLMSummarizer:
    # Structured output via Pydantic (ResumoLicitacoes schema)
    # Input limited to 50 bids to avoid token overflow
    # Max 500 tokens output, temperature=0.3 (deterministic)
    # Fallback: Return results without LLM if API fails
    # Timeout: 30 seconds

    async def summarize(
        bids: list[dict]  # Max 50
    ) -> ResumoLicitacoes | None:
        """Returns structured summary or None on error"""

class ResumoLicitacoes(BaseModel):
    resumo_executivo: str
    total_oportunidades: int
    valor_total: float
    destaques: list[str]
    recomendacoes: list[str]
```

**LLM Strategy:**
- Summarization prompt: Focus on key opportunities
- Deduplication of similar contracts
- Risk/opportunity flagging
- Language: Portuguese
- Output: Structured Pydantic model (not raw text)

#### 5. **schemas.py** - Pydantic Models

```python
class BuscaRequest(BaseModel):
    ufs: list[str]              # 1-27 states
    data_inicio: str            # YYYY-MM-DD pattern
    data_fim: str               # YYYY-MM-DD pattern
    valor_minimo: float = 50_000.0
    valor_maximo: float = 5_000_000.0

class BuscaResponse(BaseModel):
    id: str                     # Unique search ID
    total: int
    resultados: list[Licitacao]
    resumo: ResumoLicitacoes | None
    gerado_em: datetime

class Licitacao(BaseModel):
    codigo: str
    objeto: str
    orgao: str
    uf: str
    municipio: str
    valor: float
    status: str
    link: str
```

**Validation:**
- UF list validation (must be valid Brazilian states)
- Date pattern matching (YYYY-MM-DD)
- Value range validation
- All fields required except `resumo` (can be None if LLM fails)

---

## 3. Data Flow Diagrams

### 3.1 Search Flow (Happy Path)

```
USER CLICK "BUSCAR"
        ↓
FRONTEND: POST /api/buscar
  {ufs: ['SP', 'MG'], data_inicio: '2026-01-15', ...}
        ↓
BACKEND: BuscaRequest validation
  ✓ UFs valid? ✓ Dates valid? ✓ Values valid?
        ↓
PNCP CLIENT: fetch_all()
  ├─ Loop through UFs
  ├─ Paginate through results (max 500/page)
  └─ Yield each bid with retry logic
        ↓
FILTER ENGINE: apply_filters()
  1. UF ✓
  2. Value ✓
  3. Keywords ✓
  4. Status ✓
        ↓
LLM SUMMARIZER: summarize(bids[:50])
  → GPT-4.1-nano → ResumoLicitacoes (structured)
  (or None if fails)
        ↓
EXCEL GENERATOR: create_report()
  → Styled Excel file (bytes)
  → Stored in cache with 10min TTL
        ↓
BACKEND: Return BuscaResponse
  {id: "ABC123", total: 42, resultados: [...], resumo: {...}}
        ↓
FRONTEND: Display results
  ├─ Show summary card (from resumo)
  ├─ Show results table
  └─ Show "Download Excel" button
        ↓
USER CLICK "Download"
        ↓
FRONTEND: GET /api/download?id=ABC123
        ↓
BACKEND: Retrieve from cache, serve file
        ↓
USER: Excel downloaded
```

### 3.2 Error Handling

```
PNCP API Returns 429 (Rate Limited)
        ↓
PNCP CLIENT: Check Retry-After header
        ↓
Exponential backoff + jitter
        ↓
Retry (max 5 times)
        ↓
If still failing: Return cached results or error
        ↓
FRONTEND: Show user-friendly error
```

---

## 4. PNCP API Integration Details

### 4.1 API Characteristics

- **Base URL:** `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao`
- **Instability:** Requires robust retry logic
- **Rate Limiting:** 429 responses with Retry-After header
- **Pagination:** Max 500 items/page, uses `temProximaPagina` flag
- **Response Format:** JSON with nested objects

### 4.2 Request Schema

```
Query Parameters:
- uf: string (e.g., "SP", "RJ")
- dataInício: string (YYYY-MM-DD)
- dataFim: string (YYYY-MM-DD)
- pagina: integer (1-indexed)
```

### 4.3 Response Schema

```json
{
  "data": [
    {
      "codigoCompra": "2026000001",
      "objetoCompra": "Fornecimento de uniformes escolares...",
      "valorTotalEstimado": 75000.00,
      "dataAberturaProposta": "2026-01-20",
      "dataFechamentoProposta": "2026-02-20",
      "uf": "SP",
      "municipio": "São Paulo",
      "nomeOrgao": "Secretaria de Educação",
      "modalidadeCompra": "Pregão Eletrônico",
      "statusCompra": "Aberta"
    }
  ],
  "totalRegistros": 1523,
  "totalPaginas": 4,
  "paginaAtual": 1,
  "temProximaPagina": true
}
```

### 4.4 Field Mapping

| PNCP Field | Internal Field | Usage |
|------------|----------------|-------|
| `codigoCompra` | `codigo` | Unique ID, PDF link construction |
| `objetoCompra` | `objeto` | Keyword matching, summary |
| `valorTotalEstimado` | `valor` | Value range filtering |
| `dataAberturaProposta` | Date range | Filter by timeline |
| `uf` | State | UF filtering |
| `municipio` | Municipality | Display, grouping |
| `nomeOrgao` | Agency name | Display, analysis |
| `statusCompra` | Status | Filter by open/closed |

---

## 5. Technical Debt & Architectural Issues

### 5.1 Current Issues (POC v0.2)

#### CRITICAL
1. **Frontend Not Initialized**
   - `package.json` configured but Next.js app structure missing
   - Issue #21: Set up Next.js 14+ App Router
   - Impact: Cannot test UI or integration
   - Effort: 4-6 hours
   - Blocker: Can't complete end-to-end testing

2. **Backend Structure Incomplete**
   - `main.py` is placeholder only
   - Issue #17: Implement FastAPI endpoints
   - Missing: All core modules (pncp_client, filter, excel, llm)
   - Impact: API non-functional
   - Effort: 8-12 hours
   - Blocker: Can't run actual searches

#### HIGH
3. **Test Infrastructure Missing**
   - Issue #27: Configure test frameworks
   - Backend: pytest configured but tests incomplete
   - Frontend: Jest/Vitest configured but no tests written
   - Current coverage: 96.69% for existing tests, but many areas untested
   - Impact: Risk of regressions
   - Effort: 6-8 hours (per backend/frontend)
   - Risk: No automated quality gates

4. **Excel Export Incomplete**
   - Excel generation module exists but not integrated
   - Issue #13: Add comprehensive Excel tests
   - Missing: Test coverage for all styling/formatting
   - Impact: Generated files may have formatting issues
   - Effort: 3-4 hours

5. **LLM Integration Incomplete**
   - GPT-4.1-nano integration designed but not tested
   - Issue #14: Add LLM summarization tests
   - Missing: Edge cases (0 bids, 100+ bids, API failures)
   - Impact: Fallback behavior untested
   - Effort: 2-3 hours

#### MEDIUM
6. **Rate Limiting Not Validated**
   - Retry logic implemented but not tested against real PNCP API
   - Need: Live integration test or mock with realistic delays
   - Impact: May fail under actual rate limiting
   - Effort: 3-4 hours

7. **Download Cache Strategy**
   - In-memory cache works for POC but not scalable
   - Issue #18: Implement Redis caching for production
   - Impact: Multi-instance deployment impossible
   - Effort: 4-6 hours
   - Timeline: Post-MVP

8. **Environment Configuration**
   - `.env.example` has placeholders
   - Missing: Environment variable validation at startup
   - Impact: Cryptic errors if vars missing
   - Effort: 1-2 hours

9. **CORS Configuration**
   - FastAPI CORS not configured for production
   - Current: Allow all origins (security risk)
   - Missing: Environment-based origin whitelist
   - Impact: Not production-safe
   - Effort: 1 hour

### 5.2 Future Enhancements (Post-MVP)

10. **Database Integration (Supabase)**
    - Currently: No persistent storage
    - Future: Store searches, favorites, saved reports
    - Impact: Enable user profiles, history, sharing
    - Effort: 8-12 hours

11. **Real-time Notifications**
    - Currently: No notifications
    - Future: WebSocket-based price/status alerts
    - Impact: Enable subscription-based monitoring
    - Effort: 6-8 hours

12. **Advanced Filtering**
    - Currently: Keyword + value + UF only
    - Future: Regex patterns, semantic search, fuzzy matching
    - Impact: More precise results
    - Effort: 4-6 hours

13. **User Authentication**
    - Currently: None
    - Future: OAuth/JWT-based user accounts
    - Impact: Enable per-user settings, history
    - Effort: 6-8 hours

14. **Deployment Automation**
    - Currently: Manual
    - Future: GitHub Actions CI/CD
    - Impact: Automated testing, deployment
    - Effort: 4-5 hours

---

## 6. Deployment Architecture

### 6.1 Development Environment

```
Developer Machine
├── Frontend: http://localhost:3000 (Next.js dev server)
├── Backend: http://localhost:8000 (FastAPI dev server)
└── Browser: Dev tools + network inspection
```

### 6.2 Current Architecture (POC)

```
┌──────────────────────────────────────────────────────┐
│          Browser (User)                              │
└──────────────┬───────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
   Next.js 14+    FastAPI
   (Port 3000)    (Port 8000)
        │             │
        └──────┬──────┘
               ↓
        PNCP API (external)
               │
        OpenAI API (external)
```

### 6.3 Production Architecture (Future)

```
┌─────────────────────────────────────────────────────┐
│            CDN (Cloudflare)                         │
│         (Static assets cache)                       │
└──────────────┬──────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ↓             ↓
   Next.js Frontend   FastAPI Backend
   (Vercel)          (Railway/Heroku)
        │                   │
        └────────┬──────────┘
                 ↓
            PostgreSQL
            (Supabase)
                 │
        ┌────────┴──────────┐
        ↓                   ↓
   PNCP API           OpenAI API
```

---

## 7. Technology Stack Rationale

### Backend: FastAPI
- **Why:** Type hints, automatic OpenAPI docs, excellent async support
- **Version:** 0.110+ required for latest features
- **Pydantic:** 2.6+ for strict validation
- **httpx:** Better than requests for async + resilience
- **openpyxl:** Industry standard for Excel generation

### Frontend: Next.js 14+
- **Why:** Full-stack TypeScript, App Router simplifies routing
- **React 18+:** Latest hooks, concurrent rendering
- **Tailwind CSS:** Utility-first, minimal bundle impact
- **TypeScript:** Strict mode for type safety

### External Services
- **PNCP API:** Only source of procurement data
- **OpenAI API:** GPT-4.1-nano for summaries (temperature=0.3 for consistency)

---

## 8. Code Patterns & Standards

### 8.1 Python (Backend)

```python
# Type hints required
def filter_licitacao(
    licitacao: dict,
    ufs_selecionadas: set[str]
) -> tuple[bool, str | None]:
    """Filter a single bid. Returns (approved, reason_if_rejected)"""
    ...

# Pydantic for validation
class BuscaRequest(BaseModel):
    ufs: list[str]
    data_inicio: str  # YYYY-MM-DD pattern

    @field_validator('ufs')
    def validate_ufs(cls, v):
        valid_ufs = {'SP', 'RJ', ...}
        if not all(uf in valid_ufs for uf in v):
            raise ValueError('Invalid UF')
        return v

# Docstrings for public functions
def fetch_all_bids(...) -> AsyncGenerator[dict]:
    """Fetch all bids across paginated results.

    Handles retry logic, rate limiting, pagination automatically.
    Yields individual bid dictionaries.
    """
    ...
```

### 8.2 TypeScript (Frontend)

```typescript
// Explicit return types
interface Licitacao {
  codigo: string;
  objeto: string;
  valor: number;
}

async function buscarLicitacoes(
  ufs: string[],
  dataInicial: string
): Promise<BuscaResponse> {
  // ...
}

// No any types
const [ufs, setUfs] = useState<Set<string>>(new Set());
```

---

## 9. Security Considerations

### 9.1 Input Validation
- ✓ UF whitelist validation (Pydantic)
- ✓ Date pattern matching (YYYY-MM-DD)
- ✓ Value range validation
- ⚠️ Missing: URL parameter sanitization (low risk - internal API)

### 9.2 API Security
- ✓ PNCP: Public API, no authentication required
- ⚠️ OpenAI: API key in environment variable (not committed)
- ⚠️ CORS: Currently allow all (fix before production)

### 9.3 Data Protection
- ✓ No user authentication yet (public data)
- ✓ PNCP data is public (no privacy concerns)
- ⚠️ Download cache in memory (no encryption needed for POC)

---

## 10. Performance Targets

### Backend
- **PNCP queries:** 30s timeout per request
- **Rate limiting:** 10 req/second (100ms minimum)
- **Filtering:** <1s for 1000 bids
- **Excel generation:** <2s for 500 rows
- **LLM summarization:** <5s for 50 bids

### Frontend
- **First Contentful Paint:** <1.5s
- **Time to Interactive:** <3s
- **Bundle size:** <200KB gzipped
- **Search to results:** <5s (including API call)

---

## 11. Monitoring & Observability (Future)

### Metrics to Track
- PNCP API success rate
- Rate limit 429 frequency
- LLM API latency
- Excel generation time
- User search frequency by UF/timerange

### Error Logging
- ✓ Structured logging (not print statements)
- ⚠️ Missing: Centralized log aggregation
- ⚠️ Missing: Error alerting (future)

---

## 12. Decision Log

### ADR-001: Use FastAPI for Backend
**Status:** ACCEPTED
**Rationale:** Type safety, async support, minimal boilerplate
**Alternative Considered:** Django REST Framework (too heavy for POC)
**Consequences:** Requires Python 3.11+, but enables fast iteration

### ADR-002: In-Memory Cache for Downloads
**Status:** ACCEPTED (POC only)
**Rationale:** Simple, no external dependencies
**Alternative Considered:** Redis (overkill for POC)
**Consequences:** Not scalable beyond single instance

### ADR-003: GPT-4.1-nano for Summaries
**Status:** ACCEPTED
**Rationale:** Cost-effective, fast, structured output via Pydantic
**Alternative Considered:** GPT-3.5-turbo (cheaper but less capable)
**Consequences:** ~$0.001 per summary, ~500 tokens max

---

## 13. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| PNCP API instability | HIGH | HIGH | Robust retry logic, circuit breaker |
| Rate limiting | HIGH | MEDIUM | Exponential backoff, rate limiter |
| LLM API cost overrun | MEDIUM | LOW | Token limits, fallback without LLM |
| Frontend not ready | MEDIUM | HIGH | Issue #21 is priority |
| Test coverage gaps | HIGH | MEDIUM | Issue #27 test framework setup |
| Cache expiration issues | LOW | LOW | 10min TTL, session-based cleanup |

---

## 14. Next Steps (Roadmap)

### Phase 1: MVP Completion (1-2 weeks)
- [ ] Issue #17: Implement FastAPI endpoints
- [ ] Issue #21: Set up Next.js frontend
- [ ] Issue #27: Configure test frameworks
- [ ] Issue #13: Complete Excel testing
- [ ] Issue #14: Complete LLM testing
- **Result:** Fully functional POC

### Phase 2: Production Readiness (2-3 weeks)
- [ ] Add comprehensive test coverage (70%+ backend, 60%+ frontend)
- [ ] Setup CI/CD (GitHub Actions)
- [ ] Environment configuration validation
- [ ] CORS configuration for production
- [ ] Deployment to Railway/Vercel
- **Result:** Production-ready system

### Phase 3: Enhancement (Post-MVP)
- [ ] Redis caching for scalability
- [ ] Supabase integration for persistence
- [ ] User authentication
- [ ] Real-time notifications
- [ ] Advanced filtering (semantic search)
- **Result:** Enterprise-grade platform

---

## 15. Architecture Strengths

✅ **Resilient API Integration**
- Exponential backoff with jitter
- Circuit breaker pattern
- Rate limit respect (Retry-After)
- Timeout boundaries

✅ **Fail-Fast Filtering**
- Sequential filters minimize computation
- Fastest checks first (UF)
- Early exit on mismatch

✅ **Type Safety**
- Pydantic validation (backend)
- TypeScript strict (frontend)
- No `any` types

✅ **Clean Separation of Concerns**
- HTTP client (pncp_client.py)
- Filtering logic (filter.py)
- Report generation (excel.py)
- LLM integration (llm.py)
- API schemas (schemas.py)

---

## 16. Architecture Weaknesses

⚠️ **Missing Integration Points**
- Frontend not fully developed
- Backend endpoints incomplete
- No persistent storage (yet)
- No user management

⚠️ **Limited Scalability**
- In-memory cache (single instance only)
- No queue system for long-running tasks
- No load balancing considerations

⚠️ **Incomplete Error Handling**
- No centralized error tracking
- Missing HTTP error status code strategy
- Limited user-facing error messages

⚠️ **Test Coverage Gaps**
- Existing tests: 96.69% coverage (but small scope)
- Missing: E2E tests, integration tests
- Missing: Load testing

---

## 17. Architecture Review Checklist

- [x] Data flows documented
- [x] Component separation clear
- [x] External dependencies identified
- [x] Error handling strategy defined (partially)
- [x] Security considerations addressed
- [ ] Performance targets set (documented but not validated)
- [ ] Scalability concerns identified
- [ ] Test strategy defined (partially)
- [x] Deployment path documented
- [x] Tech stack rationale provided

---

## Document Information

**Created:** January 26, 2026
**Last Updated:** January 26, 2026
**Format:** Markdown (GitHub-flavored)
**Status:** APPROVED FOR TECHNICAL DEBT REVIEW
**Next Review:** After Issue #17 & #21 completion

---

**Questions or clarifications?** Reference section numbers in technical discussions.
