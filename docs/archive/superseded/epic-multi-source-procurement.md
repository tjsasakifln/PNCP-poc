# EPIC: Multi-Source Procurement Consolidation

**Epic ID:** MSP-001
**Title:** Multi-Source Procurement Consolidation - Unified Data Aggregation
**Version:** 1.0
**Status:** PLANNING
**Created:** February 3, 2026
**Author:** @pm (Morgan)

---

## 1. Executive Summary

Transform BidIQ from a **single-source PNCP system** into a **multi-source procurement aggregator** that consolidates opportunities from 5 major Brazilian procurement platforms into a unified, searchable interface.

**Business Value:** Increase procurement opportunity coverage by an estimated 300-400%, capturing municipal, state, and federal contracts that currently fall outside PNCP's scope.

---

## 2. Objective

Implement a unified procurement data aggregation layer that:

1. **Integrates 4 new procurement sources** alongside existing PNCP
2. **Normalizes heterogeneous data** into a common schema
3. **Deduplicates cross-platform listings** (same bid on multiple portals)
4. **Maintains source-specific resilience** (one source down doesn't affect others)
5. **Provides transparent source attribution** in results and reports

---

## 3. New Procurement Sources

### 3.1 BLL Compras (Priority: HIGH)

**Platform:** https://bll.org.br/
**Type:** Municipal Procurement Platform
**Coverage:** 3,000+ public agencies, 60,000+ suppliers
**Modalities:** Pregao Eletronico, Compra Direta, RDC
**Integration:** PNCP-integrated, +Brasil Platform
**API Status:** TBD (requires research)

**Key Characteristics:**
- Largest private procurement portal in Brazil
- Strong municipal focus
- 1.5% commission model for winning bids
- Free for public entities
- Lightweight technology (works on 3G)

### 3.2 Portal de Compras Publicas (Priority: HIGH)

**Platform:** https://www.portaldecompraspublicas.com.br/
**Type:** National Marketplace
**Coverage:** Multi-state, cross-sector
**API:** https://apipcp.portaldecompraspublicas.com.br/
**Documentation:** Available at API endpoint
**API Status:** CONFIRMED - REST API available

**Key Characteristics:**
- Dedicated API exists (apipcp.portaldecompraspublicas.com.br)
- Buyer-focused API documentation
- Integration with government data
- Swagger/OpenAPI documentation available

### 3.3 BNC - Bolsa Nacional de Compras (Priority: MEDIUM)

**Platform:** https://bnc.org.br/
**Type:** Electronic Bidding System
**Coverage:** 23 states, 1,500+ departments, 25,000+ suppliers
**Legal Framework:** Law 10520/02, Decree 10024/19, Law 14133/21
**API Status:** TBD (requires research)

**Key Characteristics:**
- 100% cloud-hosted
- Strong presence since 2016
- PNCP-integrated
- Free registration for suppliers
- Public process search available at bnccompras.com

### 3.4 Licitar Digital (Priority: MEDIUM)

**Platform:** https://licitar.digital/
**Type:** Multi-Agency Procurement Platform
**Coverage:** Public entities of all sizes
**Modalities:** Pregao, Dispensa, Credenciamento, Leilao, Concorrencia
**API Status:** CONFIRMED - RESTful APIs available

**Key Characteristics:**
- Completely free platform
- RESTful API integration available
- Automated system registration (webservices, APIs, robots)
- Pre-formatted document templates
- Integrated price database
- Electronic signatures

---

## 4. Current State vs Target State

| Aspect | Current (v0.3) | Target (v1.0) |
|--------|----------------|---------------|
| **Sources** | 1 (PNCP only) | 5 (PNCP + 4 new) |
| **Coverage** | Federal + some state | Federal + State + Municipal |
| **Opportunities/day** | ~500-2,000 | ~2,000-8,000 (estimated) |
| **Data Schema** | PNCP-specific | Unified multi-source |
| **Deduplication** | None | Cross-platform matching |
| **Source Attribution** | N/A | Full traceability |
| **Resilience** | Single point of failure | Graceful degradation |

---

## 5. Technical Architecture

### 5.1 High-Level Design

```
                    +------------------+
                    |   User Request   |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Consolidation    |
                    | Service          |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |         |         |         |         |
    +----v----+ +--v---+ +---v--+ +----v---+ +---v----+
    |  PNCP   | | BLL  | | PCP  | |  BNC   | | Licitar|
    | Client  | |Client| |Client| | Client | | Client |
    +----+----+ +--+---+ +---+--+ +----+---+ +---+----+
         |         |         |         |         |
    +----v----+ +--v---+ +---v--+ +----v---+ +---v----+
    | pncp.   | | bll. | | pcp. | | bnc.   | |licitar.|
    | gov.br  | |org.br| |com.br| | org.br | |digital |
    +---------+ +------+ +------+ +--------+ +--------+
```

### 5.2 Component Design

```
backend/
├── clients/
│   ├── base_client.py       # Abstract base with retry logic
│   ├── pncp_client.py       # Existing (refactored)
│   ├── bll_client.py        # NEW
│   ├── pcp_client.py        # NEW (Portal Compras Publicas)
│   ├── bnc_client.py        # NEW
│   └── licitar_client.py    # NEW
├── schemas/
│   ├── unified_schema.py    # Common data model
│   ├── source_schemas.py    # Source-specific models
│   └── transformers.py      # Schema transformation
├── services/
│   ├── consolidation.py     # Multi-source aggregation
│   ├── deduplication.py     # Cross-platform matching
│   └── source_manager.py    # Health checks, circuit breaker
└── config/
    └── sources.py           # Source configuration
```

### 5.3 Unified Schema (Draft)

```python
class UnifiedProcurement(BaseModel):
    # Identity
    id: str                      # Internal UUID
    source: SourceType           # PNCP, BLL, PCP, BNC, LICITAR
    source_id: str               # Original ID from source
    source_url: HttpUrl          # Direct link to source

    # Core Data
    objeto: str                  # Procurement object/description
    valor_estimado: float | None # Estimated value
    modalidade: str              # Normalized modality
    status: ProcurementStatus    # Open, Closed, Suspended, etc.

    # Location
    uf: str                      # State code
    municipio: str | None        # Municipality

    # Organization
    orgao_nome: str              # Agency name
    orgao_cnpj: str | None       # Agency CNPJ

    # Dates
    data_publicacao: date        # Publication date
    data_abertura: datetime | None  # Opening date
    data_encerramento: datetime | None  # Closing date

    # Metadata
    fetched_at: datetime         # When we retrieved it
    raw_data: dict               # Original source data
```

---

## 6. Story Breakdown

### Phase 1: Research & Discovery (Week 1)

| Story ID | Title | Owner | Points | Dependencies |
|----------|-------|-------|--------|--------------|
| MSP-001-01 | API Research & Discovery | @analyst | 8 | None |

### Phase 2: Design (Week 1-2)

| Story ID | Title | Owner | Points | Dependencies |
|----------|-------|-------|--------|--------------|
| MSP-001-02 | Unified Schema Design | @data-engineer | 8 | MSP-001-01 |
| MSP-001-03 | Architecture Design | @architect | 5 | MSP-001-01 |

### Phase 3: Implementation (Weeks 2-4)

| Story ID | Title | Owner | Points | Dependencies |
|----------|-------|-------|--------|--------------|
| MSP-001-04 | Base Client Refactoring | @dev | 5 | MSP-001-03 |
| MSP-001-05 | BLL Compras Client | @dev | 8 | MSP-001-04 |
| MSP-001-06 | Portal Compras Publicas Client | @dev | 8 | MSP-001-04 |
| MSP-001-07 | BNC Client | @dev | 8 | MSP-001-04 |
| MSP-001-08 | Licitar Digital Client | @dev | 8 | MSP-001-04 |
| MSP-001-09 | Consolidation Service | @dev | 13 | MSP-001-05 to 08 |

### Phase 4: Quality & Deployment (Week 5)

| Story ID | Title | Owner | Points | Dependencies |
|----------|-------|-------|--------|--------------|
| MSP-001-10 | Multi-Source Test Suite | @qa | 13 | MSP-001-09 |
| MSP-001-11 | Deployment & Monitoring | @devops | 8 | MSP-001-10 |

**Total Story Points:** 92 SP
**Estimated Duration:** 5-6 weeks

---

## 7. Dependency Graph

```
MSP-001-01 (Research)
    |
    +---> MSP-001-02 (Schema Design)
    |         |
    |         +---> MSP-001-04 (Base Client)
    |                    |
    +---> MSP-001-03 (Architecture)
              |
              +---> MSP-001-04 (Base Client)
                         |
         +---------------+---------------+---------------+
         |               |               |               |
    MSP-001-05      MSP-001-06      MSP-001-07      MSP-001-08
    (BLL Client)   (PCP Client)   (BNC Client)   (Licitar Client)
         |               |               |               |
         +---------------+---------------+---------------+
                         |
                    MSP-001-09 (Consolidation Service)
                         |
                    MSP-001-10 (Test Suite)
                         |
                    MSP-001-11 (Deployment)
```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API unavailable/undocumented | High | Critical | Research phase validates API access; fallback to web scraping if needed |
| Rate limiting on new sources | High | Medium | Implement adaptive rate limiting per source |
| Schema incompatibility | Medium | High | Unified schema with source-specific transformers |
| Authentication requirements | Medium | Medium | Research phase identifies auth needs; budget for API keys |
| Data quality variations | Medium | Medium | Validation layer per source; data quality metrics |
| Legal/ToS restrictions | Low | High | Legal review of each platform's terms of service |
| Performance degradation | Medium | Medium | Parallel fetching, caching, circuit breakers |

---

## 9. Success Metrics

### Functional Metrics

- [ ] All 5 sources return valid procurement data
- [ ] Cross-platform deduplication accuracy > 95%
- [ ] Source attribution 100% accurate
- [ ] Filter functionality works across all sources

### Performance Metrics

- [ ] Multi-source search < 30s (all sources)
- [ ] Single source failure doesn't block others
- [ ] 99% availability when 3+ sources available

### Quality Metrics

- [ ] 80%+ test coverage on new clients
- [ ] 0 P0/P1 bugs in production
- [ ] API documentation complete

---

## 10. Out of Scope

The following are explicitly **NOT** in scope for this epic:

- Real-time bidding participation
- Automatic bid submission
- Source-specific advanced filters (use unified only)
- Historical data migration
- User accounts per source
- Payment/commission integration
- Mobile app changes (web only)

---

## 11. Resources Required

### Team Allocation

| Role | FTE | Duration | Responsibility |
|------|-----|----------|----------------|
| Business Analyst | 0.5 | 1 week | API research, ToS review |
| Data Engineer | 0.5 | 1 week | Schema design |
| Architect | 0.25 | 1 week | Architecture review |
| Backend Developer | 1.0 | 4 weeks | Client implementation |
| QA Engineer | 0.5 | 2 weeks | Test suite |
| DevOps | 0.25 | 1 week | Deployment, monitoring |

### Infrastructure

- API credentials/keys (if required by sources)
- Additional server capacity for parallel fetching
- Monitoring dashboards per source

---

## 12. Timeline

```
Week 1: Research & Design
├── Day 1-3: API Research (@analyst)
├── Day 3-5: Schema Design (@data-engineer)
└── Day 4-5: Architecture Design (@architect)

Week 2: Foundation
├── Day 1-2: Base Client Refactoring (@dev)
├── Day 3-5: BLL Client (@dev)
└── Day 3-5: Start PCP Client (@dev)

Week 3: Client Implementation
├── Day 1-2: Complete PCP Client (@dev)
├── Day 2-4: BNC Client (@dev)
└── Day 4-5: Licitar Client (@dev)

Week 4: Integration
├── Day 1-3: Consolidation Service (@dev)
├── Day 3-5: Integration testing (@qa)
└── Day 4-5: Bug fixes (@dev)

Week 5: Quality & Deployment
├── Day 1-3: Complete Test Suite (@qa)
├── Day 3-4: Deployment prep (@devops)
└── Day 4-5: Monitoring setup (@devops)

Week 6: Buffer
└── Reserved for issues, additional testing, documentation
```

---

## 13. Definition of Done (Epic Level)

- [ ] All 11 stories completed and merged
- [ ] All 5 sources fetching live data
- [ ] Consolidation service aggregating results
- [ ] Deduplication working cross-platform
- [ ] 80%+ test coverage on new code
- [ ] Performance benchmarks met
- [ ] Monitoring dashboards active
- [ ] Documentation complete
- [ ] Stakeholder sign-off obtained

---

## 14. Communication Plan

| Frequency | Audience | Format |
|-----------|----------|--------|
| Daily | Dev Team | Standup (15min) |
| Weekly | Stakeholders | Progress report |
| Bi-weekly | Product | Demo + metrics |
| End of epic | All | Final presentation |

---

## 15. References

### Source Platforms

- **PNCP:** https://pncp.gov.br/
- **BLL Compras:** https://bll.org.br/
- **Portal de Compras Publicas:** https://www.portaldecompraspublicas.com.br/
- **BNC:** https://bnc.org.br/
- **Licitar Digital:** https://licitar.digital/

### API Documentation

- **Portal de Compras Publicas API:** https://apipcp.portaldecompraspublicas.com.br/
- **Compras.gov.br Open Data:** https://compras.dados.gov.br/docs/home.html
- **Comprasnet Contratos API:** https://contratos.comprasnet.gov.br/api/docs

### Related Documents

- `docs/stories/epic-technical-debt.md` - Technical debt resolution
- `backend/pncp_client.py` - Existing PNCP implementation
- `PRD.md` - Product requirements

---

## 16. Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Product Owner | TBD | | Pending |
| Architect | @architect | | Pending |
| Engineering Manager | @pm | 2026-02-03 | Approved |
| Tech Lead | TBD | | Pending |

---

**Epic Created:** February 3, 2026
**Version:** 1.0
**Status:** PLANNING - Ready for story creation
**Estimated Duration:** 5-6 weeks
**Total Story Points:** 92 SP

---

*This epic consolidates 4 new procurement sources with the existing PNCP integration, positioning BidIQ as a comprehensive multi-source procurement aggregator for the Brazilian market.*
