# Story MSP-001-07: BNC (Bolsa Nacional de Compras) Client Implementation

**Story ID:** MSP-001-07
**GitHub Issue:** #162 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to implement a client for BNC (Bolsa Nacional de Compras),
**So that** users can search for electronic bidding opportunities from BNC.

---

## Objective

Create a new procurement client that:

1. Extends the `BaseClient` abstraction
2. Connects to BNC API/endpoints
3. Transforms BNC data to unified schema
4. Handles BNC-specific error scenarios
5. Respects BNC rate limits

---

## Background

**BNC - Bolsa Nacional de Compras:** https://bnc.org.br/

- Electronic bidding platform since 2016
- Covers 23 Brazilian states
- 1,500+ government departments
- 25,000+ active suppliers
- 100% cloud-hosted platform
- Legal framework: Law 10520/02, Decree 10024/19, Law 14133/21
- Public search: https://bnccompras.com/process/processsearchpublic

**API Status:** TBD (requires research)

---

## Acceptance Criteria

### AC1: Client Implementation
- [ ] `BNCClient` class extends `BaseClient`
- [ ] Connects to BNC API/search endpoint
- [ ] Implements `fetch_page()` method
- [ ] Implements `fetch_all()` generator method
- [ ] Handles pagination properly

### AC2: Data Transformation
- [ ] `BNCTransformer` implements `BaseTransformer`
- [ ] All BNC fields mapped to unified schema
- [ ] Modality codes normalized
- [ ] Status codes normalized
- [ ] Source URL preserved

### AC3: Error Handling
- [ ] BNC-specific exceptions defined
- [ ] Authentication errors handled (if applicable)
- [ ] Rate limit handling
- [ ] Network timeout handling

### AC4: Configuration
- [ ] `BNC_CONFIG` defined in sources.py
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
- [ ] Analyze BNC public search endpoint
- [ ] Document request/response format
- [ ] Identify authentication requirements
- [ ] Note rate limits and pagination

### Task 2: Client Implementation (4 SP)
- [ ] Create `backend/clients/bnc_client.py`
- [ ] Implement `BNCClient` class
- [ ] Implement `fetch_page()` method
- [ ] Implement `fetch_all()` generator
- [ ] Add BNC-specific configuration

### Task 3: Transformer Implementation (2 SP)
- [ ] Add BNC schema to `source_schemas.py`
- [ ] Implement `BNCTransformer` class
- [ ] Map all fields to unified schema
- [ ] Add field validation

### Task 4: Testing (1 SP)
- [ ] Create `backend/tests/test_bnc_client.py`
- [ ] Add mock responses for all scenarios
- [ ] Test error handling paths
- [ ] Test transformer

---

## Implementation Notes

### Known Endpoints

```
Main website: https://bnc.org.br/
Public search: https://bnccompras.com/process/processsearchpublic?param1=1
Editais page: https://bnc.org.br/editais/
```

### Expected Client Structure

```python
# backend/clients/bnc_client.py

from .base_client import BaseClient, SourceConfig
from schemas.transformers import BNCTransformer

class BNCClient(BaseClient):
    """Client for BNC (Bolsa Nacional de Compras) electronic bidding platform."""

    DEFAULT_CONFIG = SourceConfig(
        name="bnc",
        base_url="https://bnccompras.com",  # Confirm in analysis
        timeout=30.0,
        max_retries=3,
        base_delay=1.0,
        requests_per_second=5.0,
    )

    def __init__(self, config: SourceConfig | None = None):
        super().__init__(config or self.DEFAULT_CONFIG)
        self.transformer = BNCTransformer()

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        pagina: int = 1,
        **kwargs
    ) -> dict:
        """Fetch a single page of BNC procurement data."""
        # Implementation based on API analysis
        params = {
            "dataInicio": data_inicial,
            "dataFim": data_final,
            "pagina": pagina,
        }
        if uf:
            params["estado"] = uf

        return self._execute_with_retry(
            self._fetch_impl,
            params
        )

    def _fetch_impl(self, params: dict) -> dict:
        """Internal fetch implementation."""
        # Actual API call (to be refined after analysis)
        response = self.session.get(
            f"{self.config.base_url}/process/processsearchpublic",
            params=params,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        return response.json()

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        **kwargs
    ):
        """Fetch all BNC procurement records with pagination."""
        if ufs:
            for uf in ufs:
                yield from self._fetch_for_uf(data_inicial, data_final, uf)
        else:
            yield from self._fetch_for_uf(data_inicial, data_final, None)

    def _fetch_for_uf(self, data_inicial, data_final, uf):
        pagina = 1
        seen_ids = set()

        while True:
            response = self.fetch_page(data_inicial, data_final, uf, pagina)
            data = response.get("data", [])

            if not data:
                break

            for item in data:
                item_id = item.get("id", "")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    yield self.transformer.transform(item)

            # Check for more pages
            if not response.get("temProximaPagina", False):
                break

            pagina += 1
```

### Transformer Structure

```python
# In schemas/transformers.py

class BNCTransformer(BaseTransformer):
    """Transform BNC data to unified schema."""

    # Field mappings (to be completed after API analysis)
    FIELD_MAP = {
        # "bnc_field": "unified_field"
    }

    MODALITY_MAP = {
        "PREGAO_ELETRONICO": UnifiedModality.PREGAO_ELETRONICO,
        "DISPENSA": UnifiedModality.DISPENSA,
        "RDC": UnifiedModality.RDC,
        # Add more based on API analysis
    }

    STATUS_MAP = {
        "EM_ANDAMENTO": ProcurementStatus.OPEN,
        "ENCERRADO": ProcurementStatus.CLOSED,
        "SUSPENSO": ProcurementStatus.SUSPENDED,
        "ANULADO": ProcurementStatus.CANCELLED,
        "ADJUDICADO": ProcurementStatus.AWARDED,
    }

    def transform(self, raw: dict) -> UnifiedProcurement:
        return UnifiedProcurement(
            id=str(uuid.uuid4()),
            source=SourceType.BNC,
            source_id=str(raw.get("id", "")),
            source_url=self._build_url(raw),
            objeto=raw.get("objeto", ""),
            valor_estimado=self._parse_float(raw.get("valorEstimado")),
            modalidade=self._map_modality(raw.get("modalidade")),
            modalidade_original=raw.get("modalidade"),
            status=self._map_status(raw.get("situacao")),
            uf=raw.get("uf", ""),
            municipio=raw.get("municipio"),
            orgao_nome=raw.get("orgaoNome", ""),
            orgao_cnpj=self._normalize_cnpj(raw.get("orgaoCnpj")),
            data_publicacao=self._parse_date(raw.get("dataPublicacao")),
            data_abertura=self._parse_datetime(raw.get("dataAbertura")),
            raw_data=raw,
        )

    def _build_url(self, raw: dict) -> str | None:
        """Build BNC process URL."""
        process_id = raw.get("id")
        if process_id:
            return f"https://bnc.org.br/editais/{process_id}"
        return None
```

---

## Alternative Approaches

If BNC does not have a public API:

1. **Web Scraping:** Scrape the public search and editais pages
2. **RSS Feed:** Check if BNC offers RSS feeds for new bids
3. **Partner Integration:** Contact BNC for integration partnership
4. **PNCP Fallback:** BNC publishes to PNCP, could rely on that

---

## Definition of Done

- [ ] `BNCClient` implemented and working
- [ ] `BNCTransformer` mapping all fields
- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration test documented
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
| Cloudflare/bot protection | Medium | High | Use proper headers, consider proxy |
| Data format varies | Medium | Medium | Defensive parsing |
| PNCP overlap | Low | Low | Deduplication handles this |

---

## Test Data

Mock response for testing (to be updated after API analysis):

```json
{
  "data": [
    {
      "id": "BNC-2026-54321",
      "objeto": "Fornecimento de equipamentos de informatica",
      "valorEstimado": 320000.00,
      "modalidade": "PREGAO_ELETRONICO",
      "situacao": "EM_ANDAMENTO",
      "uf": "MG",
      "municipio": "Belo Horizonte",
      "orgaoNome": "Tribunal de Justica de MG",
      "orgaoCnpj": "21154554000179",
      "dataPublicacao": "2026-01-28",
      "dataAbertura": "2026-02-10T14:00:00"
    }
  ],
  "totalRegistros": 67,
  "pagina": 1,
  "totalPaginas": 4,
  "temProximaPagina": true
}
```

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research: `docs/stories/STORY-156-api-research-discovery.md`
- Base Client: `docs/stories/STORY-159-base-client-refactoring.md`
- BNC Website: https://bnc.org.br/
- BNC Search: https://bnccompras.com/process/processsearchpublic

---

**Story Status:** READY (pending dependencies)
**Estimated Duration:** 3-4 days
**Priority:** P2 - Important
