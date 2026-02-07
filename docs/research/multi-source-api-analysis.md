# Multi-Source Procurement API Analysis

**Research Date:** 2026-02-03
**Analyst:** @analyst (Business Analyst Agent)
**Purpose:** Evaluate 4 new procurement data sources for potential integration with SmartLic

---

## Executive Summary

| Platform | API Available | Feasibility | Recommended Approach |
|----------|--------------|-------------|---------------------|
| Portal de Compras Publicas | Yes (documented) | 4/5 | API Integration (Partnership) |
| Licitar Digital | Yes (private) | 3/5 | Partnership/ERP Integration |
| BLL Compras | Yes (private) | 2/5 | Partnership or Web Scraping |
| BNC | No | 2/5 | Web Scraping |

**Best Candidate:** Portal de Compras Publicas - has publicly documented API with JSON responses.

---

## 1. BLL Compras (bllcompras.com)

### Overview
- **Full Name:** Bolsa de Licitacoes e Leiloes do Brasil
- **CNPJ:** 10.508.843/0002-38
- **Founded:** 2008
- **Coverage:** 3,000+ public agencies, 60,000+ registered suppliers
- **Focus:** Municipal procurement, electronic auctions (pregao eletronico)

### API Availability

| Aspect | Details |
|--------|---------|
| **Public API** | No - not publicly documented |
| **Private API** | Yes - REST/SOAP for ERP integration (150+ systems) |
| **Documentation** | Not publicly available |
| **Authentication** | Unknown - requires partnership |

**Key Finding:** BLL Compras mentions "integracao automatica (via TXT, SOAP e REST), com mais de 150 sistemas de gestao" indicating they have APIs but only for registered ERP partners.

### Data Access Method

**Primary:** Web scraping required for public access
**Alternative:** Partnership agreement for API access

**Public Search Page:** `https://bllcompras.com/process/processsearchpublic?param1=1`

### Data Fields Available

| Field | Available | Notes |
|-------|-----------|-------|
| Process ID (Edital) | Yes | Unique identifier |
| Object Description | Yes | Via details page |
| Estimated Value | Yes | Via details page |
| Publication Date | Yes | Displayed in listings |
| Dispute Date | Yes | Displayed in listings |
| Status | Yes | GRAVADO, PUBLICADO, RECEPCAO DE PROPOSTAS, etc. |
| Agency/Promotor | Yes | Organization name |
| City | Yes | Municipal level |
| State (UF) | Yes | Filter available |
| Modality | Yes | PREGAO ELETRONICO, COMPRA DIRETA, etc. |

### Search/Filter Capabilities

| Filter | Available | Type |
|--------|-----------|------|
| State (UF) | Yes | Dropdown (all 27 states) |
| Date Range (Publication) | Yes | Date picker |
| Date Range (Dispute) | Yes | Date picker |
| Keywords | Yes | Text input |
| Value Range | No | Not directly available |
| Status | Yes | Dropdown |
| Modality | Yes | Dropdown |
| City | Yes | Text input |

### Rate Limits & Restrictions

- **robots.txt:** 404 (not found) - no explicit restrictions
- **reCAPTCHA:** v2 implemented (site key: `6LdpKvsmAAAAAA4rzH5iQNswgItyulQ1J2HQ1FkK`)
- **Pagination:** 100 items per load, infinite scroll via AJAX
- **Session:** Cookie-based session management required

### Technical Implementation

```
Technology Stack:
- ASP.NET backend
- jQuery frontend
- AJAX data loading via /Process/GetProcessByParams
- reCAPTCHA v2 protection
- Session-based authentication
```

### Data Format

- **Web:** HTML tables rendered via AJAX
- **API (private):** TXT, SOAP, REST (JSON likely)

### Integration Complexity

| Challenge | Severity |
|-----------|----------|
| reCAPTCHA bypass | High |
| AJAX pagination | Medium |
| Session management | Medium |
| No public API | High |

### Business Model

- **Public Agencies:** Free
- **Suppliers:** 1.5% commission on wins (up to R$40k), R$600 flat fee above

### Feasibility Score: 2/5

**Rationale:** Private APIs exist but require partnership. Web scraping is possible but complicated by reCAPTCHA. Best approach would be formal partnership agreement.

### Contact Information

- **Website:** https://bll.org.br
- **System:** https://bllcompras.com
- **LinkedIn:** https://br.linkedin.com/company/bll---bolsa-de-licita-es-e-leil-es

### Sources

- [BLL Compras Official](https://bll.org.br/)
- [BLL Compras Guide](https://conlicitacao.com.br/bll-compras-guia-para-licitantes/)
- [BLL Compras B2BStack](https://www.b2bstack.com.br/product/bll-compras)
- [eLicitacao BLL Guide](https://elicitacao.com.br/2025/12/03/bll-compras/)

---

## 2. Portal de Compras Publicas (portaldecompraspublicas.com.br)

### Overview
- **Type:** National marketplace for public procurement
- **Integration:** 100% integrated with PNCP and +Brasil
- **Coverage:** Municipal, state, and federal levels

### API Availability

| Aspect | Details |
|--------|---------|
| **Public API** | Yes - documented |
| **API URL** | https://apipcp.portaldecompraspublicas.com.br/ |
| **Documentation** | https://apipcp.portaldecompraspublicas.com.br/comprador/apidoc/ |
| **Type** | REST API |
| **Format** | JSON |

### Authentication

| Requirement | Details |
|-------------|---------|
| **Method** | API Key (PublicKey) |
| **Request Process** | Fill form on Zendesk library |
| **Delivery Time** | Up to 7 business days |
| **Access Level** | Public information from finalized processes |

**Request URL:** https://bibliotecapcp.zendesk.com/hc/pt-br/articles/4593549708570-Parceiros-Consulta-publica-de-processos-via-API

### Data Access Method

**Primary:** REST API with API key authentication
**Scope:** Finalized/completed procurement processes only

### Data Fields Available

Based on documentation references and PNCP integration:

| Field | Available | Notes |
|-------|-----------|-------|
| Process ID | Yes | Unique identifier |
| Object Description | Yes | Full procurement object |
| Estimated Value | Yes | With up to 4 decimal precision |
| Opening Date | Yes | Proposal opening |
| Publication Date | Yes | Notice publication |
| Status | Yes | Process status |
| Agency/Organ | Yes | Contracting entity |
| Municipality | Yes | Location |
| State (UF) | Yes | Federation unit |
| Modality | Yes | Procurement type |
| PNCP Link | Yes | Integration data |

### Search/Filter Capabilities

| Filter | Available | Notes |
|--------|-----------|-------|
| State (UF) | Yes | Via API parameters |
| Date Range | Yes | Start/end dates |
| Keywords | Yes | Object search |
| Value Range | Unknown | Check documentation |
| Status | Partial | Finalized processes only |

### Rate Limits

- **robots.txt:**
  - Allows: `/`
  - Disallows: Query parameters (ttCD_CHAVE, v, rdCampoPesquisado, Busca, Objeto, Orgao, Abertura, Publicacao, OrderBy)
  - Sitemap: https://www.portaldecompraspublicas.com.br/sitemap.xml
- **API Rate Limits:** Not publicly documented (contact support)

### Technical Implementation

```
Technology Stack:
- REST API architecture
- JSON data format
- API key authentication
- PNCP integration
```

### Data Format

- **Response:** JSON
- **Encoding:** UTF-8 (standard for PNCP compliance)

### Integration Complexity

| Challenge | Severity |
|-----------|----------|
| API key request process | Low |
| Wait time (7 days) | Low |
| Only finalized processes | Medium |
| Documentation accessibility | Low |

### Feasibility Score: 4/5

**Rationale:** Best documented option with official API. Requires API key but process is straightforward. Limitation: only finalized processes available.

### Contact Information

- **Email:** gestor@portaldecompraspublicas.com.br
- **Phone:** (61) 3120-3737
- **Support:** 3003-5455
- **Website:** https://www.portaldecompraspublicas.com.br

### Sources

- [API Portal CP](https://apipcp.portaldecompraspublicas.com.br/)
- [API Documentation](https://apipcp.portaldecompraspublicas.com.br/comprador/apidoc/)
- [Zendesk Library - API Access](https://bibliotecapcp.zendesk.com/hc/pt-br/articles/4593549708570-Parceiros-Consulta-publica-de-processos-via-API)
- [Portal Official](https://www.portaldecompraspublicas.com.br)

---

## 3. BNC - Bolsa Nacional de Compras (bnc.org.br)

### Overview
- **CNPJ:** 25.099.967/0001-01
- **Founded:** April 2016
- **Location:** Ponta Grossa, PR
- **Coverage:** 23 Brazilian states, 1,500+ public agencies
- **Focus:** Electronic auctions, municipal procurement

### API Availability

| Aspect | Details |
|--------|---------|
| **Public API** | No |
| **Private API** | Unknown - no documentation found |
| **ERP Integration** | Available (Megasoft, others) |
| **PNCP Integration** | Yes - data synced to PNCP |

**Key Finding:** No public API documentation. Third-party integrations exist (e.g., Megasoft MegaAdmWeb) suggesting private APIs may be available through partnership.

### Data Access Method

**Primary:** Web scraping
**Alternative:** Partnership for ERP integration (contact required)

**Public Search Page:** `https://bnccompras.com/Process/ProcessSearchPublic?param1=0`

### Data Fields Available

| Field | Available | Notes |
|-------|-----------|-------|
| Process ID (Edital) | Yes | Tender number |
| Object Description | Yes | Via details page |
| Estimated Value | Yes | Via details page |
| Publication Date | Yes | Date and time |
| Dispute Date | Yes | Start and end times |
| Status | Yes | Multiple statuses available |
| Agency/Promotor | Yes | Organizing entity |
| City | Yes | Municipal level |
| State (UF) | Yes | Filter dropdown |
| Modality | Yes | Pregao, dispensa, etc. |

### Search/Filter Capabilities

| Filter | Available | Type |
|--------|-----------|------|
| State (UF) | Yes | Dropdown (AC to TO) |
| Date Range (Publication) | Yes | Date picker |
| Date Range (Dispute) | Yes | Date picker |
| Keywords | Yes | Text search (promoter, number, city) |
| Value Range | No | Not available |
| Status | Yes | Dropdown (multiple options) |
| Modality | Yes | Dropdown |
| Advanced Search | Yes | Toggle for expanded filters |

**Status Options:** GRAVADO, PUBLICADO, RECEPCAO DE PROPOSTAS, DESERTO, ANALISE, ADJUDICADO, HOMOLOGADO, REVOGADO, ANULADO, FRACASSADO

### Rate Limits & Restrictions

- **robots.txt:**
  - `User-agent: *`
  - `Disallow:` (empty - all access allowed)
  - `Sitemap: http://bnc.org.br/sitemap_index.xml`
- **reCAPTCHA:** v2 implemented
- **Pagination:** 100 items per load, scroll-based loading

### Technical Implementation

```
Technology Stack:
- Similar to BLL Compras (possibly same vendor)
- ASP.NET backend
- jQuery frontend
- AJAX data loading via /Process/GetProcessByParams
- reCAPTCHA v2 protection
```

### Data Format

- **Web:** HTML tables via AJAX
- **Export:** Not available publicly

### Integration Complexity

| Challenge | Severity |
|-----------|----------|
| No public API | High |
| reCAPTCHA bypass | High |
| AJAX pagination | Medium |
| Session management | Medium |

### Business Model

- **Supplier Registration:** Free
- **Participation Fee:** R$98.10 per auction
- **Long-term Plans:** Available via email request

### Feasibility Score: 2/5

**Rationale:** No public API. Similar technical challenges to BLL Compras. robots.txt allows access but reCAPTCHA complicates automated extraction. Since data syncs to PNCP, consider using PNCP API instead for BNC-originated data.

### Contact Information

- **Address:** Av. Monteiro Lobato, 106 - Jardim Carvalho I, CEP 84015-480, Ponta Grossa - PR
- **Phone (Suppliers):** (42) 3026-4555
- **WhatsApp:** (42) 3026-4550
- **Email:** contato@bnc.org.br
- **Website:** https://bnc.org.br
- **System:** https://bnccompras.com

### Sources

- [BNC Official](https://bnc.org.br/)
- [BNC Privacy Policy](https://bnc.org.br/politica-de-privacidade/)
- [BNC FAQ](https://bnc.org.br/faq/)
- [Megasoft BNC Integration](https://www.megasoft.com.br/megasoft-aprimora-ferramenta-para-integrar-ao-bnc-bolsa-nacional-de-compras/)
- [Lance Facil BNC Guide](https://blog.lancefacil.com/bnc-ou-bolsa-nacional-de-compras-conheca-essa-plataforma-de-pregao-eletronico/)

---

## 4. Licitar Digital (licitardigital.com.br)

### Overview
- **Type:** Multi-agency procurement platform
- **Target:** Municipalities, Public Consortiums, Chambers, Autarchies, State-owned companies
- **Positioning:** "Most innovative public procurement platform in Brazil"
- **Integration:** PNCP, +Brasil, multiple ERP systems

### API Availability

| Aspect | Details |
|--------|---------|
| **Public API** | No - not publicly documented |
| **Private API** | Yes - RESTful APIs for ERP integration |
| **ERP Integrations** | E&L, Memory, CMM, HLH, Sonner, ADPM, and others |
| **Custom Integration** | Available upon request |

**Key Finding:** Platform explicitly mentions "APIs RESTful" for ERP integration, indicating robust API infrastructure exists but is not publicly accessible.

### Data Access Method

**Primary:** Partnership/ERP integration
**Alternative:** Web scraping (limited - 403 errors observed)

**Public Search Pages:**
- `https://app.licitardigital.com.br/pesquisa/`
- `https://app2.licitardigital.com.br/pesquisa`

### Data Fields Available

| Field | Available | Notes |
|-------|-----------|-------|
| Process ID | Yes | Unique system identifier |
| Object Description | Yes | Procurement object |
| Estimated Value | Yes | Via details |
| Publication Date | Yes | Displayed |
| Dispute Date | Yes | Filterable |
| Status/Stage | Yes | Multiple stages |
| Agency | Yes | Public entity |
| Municipality | Yes | City level |
| State (UF) | Yes | Filterable |
| Type/Modality | Yes | Pregao, leilao, concorrencia, dispensa, credenciamento |

### Search/Filter Capabilities

| Filter | Available | Type |
|--------|-----------|------|
| State (UF) | Yes | Dropdown with city/micro/mesoregion |
| Date Range (Dispute) | Yes | Date picker |
| Keywords | Yes | Process number, municipality, object |
| Value Range | No | Not documented |
| Type/Modality | Yes | Pregao, leilao, concorrencia, dispensa, credenciamento |
| Stage | Yes | Recebendo proposta, disputa, decisao, contrato |
| Favorites/Suggestions | Yes | User preferences |

### Rate Limits & Restrictions

- **robots.txt:**
  - `User-agent: *`
  - `Disallow:` (empty - all access allowed)
  - `Sitemap: https://licitar.digital/sitemap_index.xml`
- **Access Control:** 403 errors observed on some endpoints
- **Authentication:** Required for full access

### Technical Implementation

```
Technology Stack:
- RESTful API backend
- Modern web frontend
- PNCP integration
- ERP connectors
- Digital signature support (free)
```

### Data Format

- **API:** JSON (inferred from RESTful architecture)
- **Web:** HTML/JavaScript SPA

### Integration Complexity

| Challenge | Severity |
|-----------|----------|
| No public API docs | High |
| 403 access restrictions | Medium |
| Partnership required | Medium |
| Multiple app domains | Low |

### Business Model

- **Public Entities:** Free (including state-owned companies)
- **Suppliers:**
  - Free: Search, notifications
  - Paid: 1.3% of awarded value (max R$500 per process)
  - Post-paid model

### Feasibility Score: 3/5

**Rationale:** Has RESTful APIs but requires partnership. Better documented ERP integration path than BLL/BNC. Platform is open to new integrations per their website.

### Contact Information

- **Website:** https://licitar.digital
- **App:** https://app.licitardigital.com.br
- **Help Center:** https://licitardigital.tawk.help
- **LinkedIn:** https://br.linkedin.com/company/licitardigital

### Sources

- [Licitar Digital Official](https://licitar.digital/)
- [Licitar Digital Services](https://licitar.digital/servicos/)
- [Help Center - Search](https://licitardigital.tawk.help/article/como-pesquisar-editais-de-processos-eletr%C3%B4nicos)
- [ConLicitacao Guide](https://conlicitacao.com.br/licitar-digital-plataforma-de-licitacoes-online-como-participar/)
- [eLicitaRadar Integration](https://elicitacao.com.br/2024/12/10/elicitaradar-e-licitar-digital/)

---

## Comparative Analysis

### API Access Summary

| Platform | Public API | Auth Method | Format | Docs Available |
|----------|------------|-------------|--------|----------------|
| Portal de Compras Publicas | Yes | API Key | JSON | Yes |
| Licitar Digital | Private | Partnership | JSON | No |
| BLL Compras | Private | Partnership | TXT/SOAP/REST | No |
| BNC | No | N/A | N/A | No |

### Data Coverage

| Platform | Coverage | Primary Users |
|----------|----------|---------------|
| Portal de Compras Publicas | National | All levels |
| Licitar Digital | Growing | Municipalities, consortiums |
| BLL Compras | National | Municipalities (60k+ suppliers) |
| BNC | 23 states | Municipalities, chambers |

### Technical Comparison

| Platform | Tech Stack | Scraping Difficulty | PNCP Sync |
|----------|------------|---------------------|-----------|
| Portal de Compras Publicas | REST API | N/A (has API) | Yes |
| Licitar Digital | RESTful | Medium-High | Yes |
| BLL Compras | ASP.NET/jQuery | High (reCAPTCHA) | Yes |
| BNC | ASP.NET/jQuery | High (reCAPTCHA) | Yes |

### Integration Effort Estimate

| Platform | Effort | Timeline | Resources Needed |
|----------|--------|----------|------------------|
| Portal de Compras Publicas | Low | 2-3 weeks | API key request, client implementation |
| Licitar Digital | Medium | 4-6 weeks | Partnership negotiation, API access |
| BLL Compras | High | 6-8 weeks | Partnership or scraping infrastructure |
| BNC | High | 6-8 weeks | Scraping infrastructure + reCAPTCHA handling |

---

## Recommendations

### Priority 1: Portal de Compras Publicas

**Action:** Request API key immediately
- Best documented option
- Official support available
- 7-day turnaround for access
- JSON format aligns with current architecture

**Limitation:** Only finalized processes (consider for historical data and completed procurement analysis)

### Priority 2: Licitar Digital

**Action:** Initiate partnership discussion
- Has RESTful APIs ready
- Open to new integrations
- Growing platform with good coverage
- Modern architecture

**Approach:** Contact through official channels, emphasize mutual benefit

### Priority 3: Consider PNCP as Aggregator

Since BLL Compras and BNC both sync to PNCP, and SmartLic already integrates with PNCP:
- **BLL/BNC data is already accessible via PNCP API**
- Direct integration may not add significant value
- Focus on PNCP for comprehensive national coverage

### Priority 4: Evaluate Scraping Only If Needed

For real-time data from BLL/BNC not yet in PNCP:
- Requires significant infrastructure investment
- reCAPTCHA solving services needed
- Legal review recommended
- Consider third-party aggregators (eLicitacao, Lance Facil, Alerta Licitacao)

---

## Legal Considerations

### General Notes

1. **LGPD Compliance:** Web scraping of public data is generally permitted under Brazilian law, but must respect:
   - Data minimization principles
   - Purpose limitation
   - No collection of personal data beyond necessity

2. **Terms of Service:**
   - BLL Compras: No explicit prohibition found
   - BNC: No explicit prohibition found
   - Both have privacy policies focused on personal data, not bot access

3. **robots.txt Compliance:**
   - BNC: All access allowed
   - Licitar Digital: All access allowed
   - Portal de Compras Publicas: Specific query parameters disallowed

4. **Recommendation:** For production integration, seek formal partnership agreements to ensure:
   - Legal clarity
   - Reliable access
   - Support availability
   - Data quality guarantees

---

## Next Steps

1. **Immediate:**
   - [ ] Request Portal de Compras Publicas API key
   - [ ] Document exact data fields needed for integration

2. **Short-term (2-4 weeks):**
   - [ ] Receive and test Portal de Compras Publicas API
   - [ ] Contact Licitar Digital about partnership

3. **Medium-term (1-2 months):**
   - [ ] Evaluate if additional sources beyond PNCP needed
   - [ ] Design multi-source integration architecture

4. **Long-term:**
   - [ ] Consider third-party aggregator partnerships
   - [ ] Monitor new platforms entering market

---

## Appendix: Contact Quick Reference

| Platform | Email | Phone |
|----------|-------|-------|
| Portal de Compras Publicas | gestor@portaldecompraspublicas.com.br | (61) 3120-3737 |
| BNC | contato@bnc.org.br | (42) 3026-4555 |
| BLL Compras | (via website) | (via website) |
| Licitar Digital | (via website/help center) | (via website) |

---

*Document generated by @analyst agent as part of SmartLic multi-source integration research.*
