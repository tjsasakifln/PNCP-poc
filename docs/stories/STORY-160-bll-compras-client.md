# Story MSP-001-05: BLL Compras Client Implementation

**Story ID:** MSP-001-05
**GitHub Issue:** #160 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to implement a client for the BLL Compras procurement platform,
**So that** users can search for municipal procurement opportunities from BLL.

---

## Objective

Create a new procurement client that:

1. Extends the `BaseClient` abstraction
2. Connects to BLL Compras API/endpoints
3. Transforms BLL data to unified schema
4. Handles BLL-specific error scenarios
5. Respects BLL rate limits

---

## Background

**BLL Compras:** https://bll.org.br/

- Largest private procurement portal in Brazil
- 3,000+ public agencies, 60,000+ suppliers
- Strong municipal focus
- Public search: https://bllcompras.com/process/processsearchpublic
- Integration with PNCP and +Brasil Platform

---

## Acceptance Criteria

### AC1: Client Implementation
- [ ] `BLLClient` class extends `BaseClient`
- [ ] Connects to BLL API/search endpoint
- [ ] Implements `fetch_page()` method
- [ ] Implements `fetch_all()` generator method
- [ ] Handles pagination properly

### AC2: Data Transformation
- [ ] `BLLTransformer` implements `BaseTransformer`
- [ ] All BLL fields mapped to unified schema
- [ ] Modality codes normalized
- [ ] Status codes normalized
- [ ] Source URL preserved

### AC3: Error Handling
- [ ] BLL-specific exceptions defined
- [ ] Authentication errors handled (if applicable)
- [ ] Rate limit handling (if applicable)
- [ ] Network timeout handling

### AC4: Configuration
- [ ] `BLL_CONFIG` defined in sources.py
- [ ] Environment variable overrides supported
- [ ] Timeout and retry settings configured

### AC5: Testing
- [ ] Unit tests with mocked responses
- [ ] Integration test (marked for manual run)
- [ ] Transformer tests
- [ ] 90%+ code coverage

### AC6: Documentation
- [ ] Docstrings for all public methods
- [ ] Field mapping documented
- [ ] Known limitations documented

---

## Technical Tasks

### Task 1: API Analysis (1 SP)
- [ ] Analyze BLL public search endpoint
- [ ] Document request/response format
- [ ] Identify authentication requirements
- [ ] Note rate limits and pagination

### Task 2: Client Implementation (4 SP)
- [ ] Create `backend/clients/bll_client.py`
- [ ] Implement `BLLClient` class
- [ ] Implement `fetch_page()` method
- [ ] Implement `fetch_all()` generator
- [ ] Add BLL-specific configuration

### Task 3: Transformer Implementation (2 SP)
- [ ] Add BLL schema to `source_schemas.py`
- [ ] Implement `BLLTransformer` class
- [ ] Map all fields to unified schema
- [ ] Add field validation

### Task 4: Testing (1 SP)
- [ ] Create `backend/tests/test_bll_client.py`
- [ ] Add mock responses for all scenarios
- [ ] Test error handling paths
- [ ] Test transformer

---

## Implementation Notes

### Public Search Endpoint

Based on research, BLL has a public process search at:
```
https://bllcompras.com/process/processsearchpublic?param1=1
```

This endpoint needs to be analyzed for:
- Request parameters (date range, UF, keywords)
- Response format (JSON expected)
- Pagination mechanism
- Rate limits

### Expected Client Structure

```python
# backend/clients/bll_client.py

from .base_client import BaseClient, SourceConfig
from schemas.transformers import BLLTransformer

class BLLClient(BaseClient):
    """Client for BLL Compras municipal procurement platform."""

    DEFAULT_CONFIG = SourceConfig(
        name="bll",
        base_url="https://bllcompras.com",  # Confirm in analysis
        timeout=30.0,
        max_retries=3,
        base_delay=1.0,
        requests_per_second=5.0,  # Conservative default
    )

    def __init__(self, config: SourceConfig | None = None):
        super().__init__(config or self.DEFAULT_CONFIG)
        self.transformer = BLLTransformer()

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        pagina: int = 1,
        **kwargs
    ) -> dict:
        """Fetch a single page of BLL procurement data."""
        # Implementation based on API analysis
        ...

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        **kwargs
    ):
        """Fetch all BLL procurement records with pagination."""
        # Generator implementation
        for page_data in self._paginate(...):
            for item in page_data:
                yield self.transformer.transform(item)
```

### Transformer Structure

```python
# In schemas/transformers.py

class BLLTransformer(BaseTransformer):
    """Transform BLL data to unified schema."""

    # Field mappings (to be completed after API analysis)
    FIELD_MAP = {
        # "bll_field": "unified_field"
    }

    MODALITY_MAP = {
        # BLL modality codes -> UnifiedModality
    }

    STATUS_MAP = {
        # BLL status codes -> ProcurementStatus
    }

    def transform(self, raw: dict) -> UnifiedProcurement:
        return UnifiedProcurement(
            id=str(uuid.uuid4()),
            source=SourceType.BLL,
            source_id=raw.get("id", ""),  # Adjust field name
            source_url=self._build_url(raw),
            objeto=raw.get("descricao", ""),  # Adjust field name
            valor_estimado=self._parse_value(raw),
            modalidade=self._map_modality(raw),
            status=self._map_status(raw),
            uf=raw.get("uf", ""),  # Adjust field name
            municipio=raw.get("municipio"),
            orgao_nome=raw.get("orgao", ""),  # Adjust field name
            orgao_cnpj=raw.get("cnpj"),
            data_publicacao=self._parse_date(raw, "dataPublicacao"),
            data_abertura=self._parse_datetime(raw, "dataAbertura"),
            raw_data=raw,
        )
```

---

## Alternative Approaches

If BLL does not have a public API:

1. **Web Scraping:** Use requests + BeautifulSoup to scrape public search
2. **Selenium/Playwright:** For JavaScript-rendered content
3. **Partner API:** Contact BLL for partner/integration access
4. **Defer:** Mark as lower priority if integration cost too high

---

## Definition of Done

- [ ] `BLLClient` implemented and working
- [ ] `BLLTransformer` mapping all fields
- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration test documented (manual)
- [ ] Configuration documented
- [ ] Code reviewed by peer

---

## Story Points: 8 SP

**Complexity:** High (unknown API structure)
**Uncertainty:** High (depends on API availability)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-01 | Data dependency | API research provides endpoint details |
| MSP-001-02 | Data dependency | Unified schema for transformation |
| MSP-001-04 | Code dependency | Must extend BaseClient |

---

## Blocks

- MSP-001-09 (Consolidation Service)

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No public API | High | Critical | Implement scraping fallback |
| Rate limiting | Medium | Medium | Conservative defaults, adaptive limiting |
| Data format changes | Medium | Medium | Defensive parsing, logging |
| Authentication required | Medium | High | Contact BLL for access |

---

## Test Data

Mock response for testing (to be updated after API analysis):

```json
{
  "data": [
    {
      "id": "BLL-2026-00001",
      "descricao": "Aquisicao de uniformes escolares",
      "valorEstimado": 150000.00,
      "modalidade": "PE",
      "situacao": "ABERTO",
      "uf": "SP",
      "municipio": "Sao Paulo",
      "orgao": "Prefeitura Municipal de Sao Paulo",
      "cnpj": "46395000000139",
      "dataPublicacao": "2026-02-01",
      "dataAbertura": "2026-02-15T09:00:00"
    }
  ],
  "totalRegistros": 150,
  "pagina": 1,
  "totalPaginas": 8
}
```

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research: `docs/stories/STORY-156-api-research-discovery.md`
- Base Client: `docs/stories/STORY-159-base-client-refactoring.md`
- BLL Website: https://bll.org.br/

---

**Story Status:** READY (pending dependencies)
**Estimated Duration:** 3-4 days
**Priority:** P1 - Critical Path
