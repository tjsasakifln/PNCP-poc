# Story MSP-001-01: API Research & Discovery

**Story ID:** MSP-001-01
**GitHub Issue:** #156 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @analyst
**Created:** February 3, 2026

---

## Story

**As a** product team member,
**I want** comprehensive documentation of all 4 new procurement source APIs,
**So that** we can make informed architectural and implementation decisions.

---

## Objective

Research and document the API capabilities, authentication requirements, rate limits, data structures, and terms of service for:

1. BLL Compras
2. Portal de Compras Publicas
3. BNC (Bolsa Nacional de Compras)
4. Licitar Digital

---

## Acceptance Criteria

### AC1: BLL Compras Research
- [ ] API endpoint documentation (or confirmation none exists)
- [ ] Authentication method identified
- [ ] Rate limits documented
- [ ] Sample response structure captured
- [ ] Terms of service reviewed for API usage rights
- [ ] Alternative access methods identified (scraping, RSS, etc.)

### AC2: Portal de Compras Publicas Research
- [ ] Full API documentation reviewed (apipcp.portaldecompraspublicas.com.br)
- [ ] Available endpoints cataloged
- [ ] Authentication requirements documented
- [ ] Rate limits documented
- [ ] Sample responses captured for each relevant endpoint
- [ ] Data fields mapped to our requirements

### AC3: BNC Research
- [ ] API endpoint documentation (or confirmation none exists)
- [ ] Public search endpoint analyzed (bnccompras.com)
- [ ] Authentication method identified
- [ ] Rate limits documented
- [ ] Sample response structure captured
- [ ] Alternative access methods identified

### AC4: Licitar Digital Research
- [ ] RESTful API documentation obtained
- [ ] Registration requirements for automated access clarified
- [ ] Authentication method identified
- [ ] Rate limits documented
- [ ] Sample responses captured
- [ ] Terms of service for automated access reviewed

### AC5: Comparison Matrix
- [ ] Create comparison table: API vs Scraping feasibility
- [ ] Document data field availability per source
- [ ] Identify common fields across all sources
- [ ] Flag source-specific unique fields
- [ ] Rate reliability/stability assessment per source

### AC6: Deliverable
- [ ] Research report created at `docs/research/multi-source-api-research.md`
- [ ] Sample API responses saved to `docs/research/samples/`
- [ ] Risks and blockers documented
- [ ] Recommendations for implementation approach

---

## Research Tasks

### Task 1: BLL Compras Investigation (2 SP)
- [ ] Visit https://bll.org.br/ and explore documentation
- [ ] Contact BLL support if no public API docs
- [ ] Analyze https://bllcompras.com/process/processsearchpublic
- [ ] Test public search endpoint
- [ ] Document findings

### Task 2: Portal Compras Publicas Investigation (2 SP)
- [ ] Review https://apipcp.portaldecompraspublicas.com.br/
- [ ] Test API endpoints with sample requests
- [ ] Document all available endpoints
- [ ] Capture authentication flow
- [ ] Note any restrictions

### Task 3: BNC Investigation (2 SP)
- [ ] Visit https://bnc.org.br/ developer resources
- [ ] Analyze https://bnccompras.com/process/processsearchpublic
- [ ] Contact BNC if no public API docs
- [ ] Test public endpoints
- [ ] Document findings

### Task 4: Licitar Digital Investigation (1.5 SP)
- [ ] Review https://licitar.digital/ API documentation
- [ ] Understand automated system registration
- [ ] Test available endpoints
- [ ] Document API capabilities

### Task 5: Deliverable Compilation (0.5 SP)
- [ ] Compile all findings into research report
- [ ] Create comparison matrix
- [ ] Document recommendations
- [ ] Present to team

---

## Definition of Done

- [ ] All 4 sources researched
- [ ] Research report created and reviewed
- [ ] Sample responses documented
- [ ] Risks communicated to team
- [ ] Blocking issues escalated (if any)
- [ ] Architecture team briefed on findings

---

## Story Points: 8 SP

**Complexity:** Medium-High (external dependencies, uncertain API availability)
**Uncertainty:** High (API documentation may not exist)

---

## Dependencies

- None (this is the first story in the epic)

---

## Blocks

- MSP-001-02 (Unified Schema Design)
- MSP-001-03 (Architecture Design)

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No public API available | High | High | Document scraping alternatives |
| API requires paid access | Medium | Medium | Budget approval process |
| ToS prohibits automated access | Low | Critical | Legal review, alternative sources |
| Rate limits too restrictive | Medium | Medium | Document for architecture design |

---

## Technical Notes

### Known API Endpoints to Investigate

```
# Portal de Compras Publicas (confirmed)
https://apipcp.portaldecompraspublicas.com.br/

# BLL Public Search (to analyze)
https://bllcompras.com/process/processsearchpublic

# BNC Public Search (to analyze)
https://bnccompras.com/process/processsearchpublic

# Licitar Digital (confirmed RESTful API)
https://licitar.digital/ (check developer docs)
```

### Research Output Template

For each source, document:
1. **Base URL:** API base endpoint
2. **Authentication:** None / API Key / OAuth / Other
3. **Endpoints:** List of relevant endpoints
4. **Rate Limits:** Requests/second, daily limits
5. **Data Format:** JSON / XML / Other
6. **Key Fields:** Available data fields
7. **Pagination:** How results are paginated
8. **Legal:** ToS restrictions on automated access

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Existing PNCP Client: `backend/pncp_client.py`

---

**Story Status:** READY FOR SPRINT PLANNING
**Estimated Duration:** 3-4 days
**Priority:** P1 - Critical Path
