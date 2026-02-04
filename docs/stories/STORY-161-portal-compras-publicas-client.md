# Story MSP-001-06: Portal de Compras Publicas Client Implementation

**Story ID:** MSP-001-06
**GitHub Issue:** #161 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to implement a client for Portal de Compras Publicas,
**So that** users can search for procurement opportunities from this national marketplace.

---

## Objective

Create a new procurement client that:

1. Extends the `BaseClient` abstraction
2. Connects to Portal de Compras Publicas API
3. Transforms PCP data to unified schema
4. Handles PCP-specific error scenarios
5. Respects PCP rate limits

---

## Background

**Portal de Compras Publicas:** https://www.portaldecompraspublicas.com.br/

- National marketplace for public procurement
- Dedicated API: https://apipcp.portaldecompraspublicas.com.br/
- Documentation available at API endpoint
- Multi-state, cross-sector coverage

**API Status:** CONFIRMED - REST API available

---

## Acceptance Criteria

### AC1: Client Implementation
- [ ] `PCPClient` class extends `BaseClient`
- [ ] Connects to PCP API endpoints
- [ ] Implements `fetch_page()` method
- [ ] Implements `fetch_all()` generator method
- [ ] Handles pagination properly
- [ ] Implements authentication if required

### AC2: Data Transformation
- [ ] `PCPTransformer` implements `BaseTransformer`
- [ ] All PCP fields mapped to unified schema
- [ ] Modality codes normalized
- [ ] Status codes normalized
- [ ] Source URL preserved

### AC3: Error Handling
- [ ] PCP-specific exceptions defined
- [ ] Authentication errors handled
- [ ] Rate limit errors handled (429)
- [ ] Network timeout handling

### AC4: Configuration
- [ ] `PCP_CONFIG` defined in sources.py
- [ ] API key support (if required)
- [ ] Environment variable overrides
- [ ] Timeout and retry settings

### AC5: Testing
- [ ] Unit tests with mocked responses
- [ ] Integration test (marked for manual run)
- [ ] Transformer tests
- [ ] 90%+ code coverage

### AC6: Documentation
- [ ] Docstrings for all public methods
- [ ] API endpoint documentation
- [ ] Field mapping documented

---

## Technical Tasks

### Task 1: API Documentation Review (1 SP)
- [ ] Review https://apipcp.portaldecompraspublicas.com.br/
- [ ] Document all available endpoints
- [ ] Understand authentication mechanism
- [ ] Note rate limits and pagination

### Task 2: Client Implementation (4 SP)
- [ ] Create `backend/clients/pcp_client.py`
- [ ] Implement `PCPClient` class
- [ ] Implement authentication
- [ ] Implement `fetch_page()` method
- [ ] Implement `fetch_all()` generator

### Task 3: Transformer Implementation (2 SP)
- [ ] Add PCP schema to `source_schemas.py`
- [ ] Implement `PCPTransformer` class
- [ ] Map all fields to unified schema
- [ ] Add field validation

### Task 4: Testing (1 SP)
- [ ] Create `backend/tests/test_pcp_client.py`
- [ ] Add mock responses
- [ ] Test authentication flow
- [ ] Test error handling paths

---

## Implementation Notes

### Known API Information

```
Base URL: https://apipcp.portaldecompraspublicas.com.br/
Documentation: https://apipcp.portaldecompraspublicas.com.br/comprador/apidoc/
```

### Expected Client Structure

```python
# backend/clients/pcp_client.py

from .base_client import BaseClient, SourceConfig
from schemas.transformers import PCPTransformer
import os

class PCPClient(BaseClient):
    """Client for Portal de Compras Publicas marketplace."""

    DEFAULT_CONFIG = SourceConfig(
        name="pcp",
        base_url="https://apipcp.portaldecompraspublicas.com.br",
        timeout=30.0,
        max_retries=3,
        base_delay=1.0,
        requests_per_second=5.0,
    )

    def __init__(self, config: SourceConfig | None = None, api_key: str | None = None):
        super().__init__(config or self.DEFAULT_CONFIG)
        self.api_key = api_key or os.getenv("PCP_API_KEY")
        self.transformer = PCPTransformer()

    def _create_session(self):
        session = super()._create_session()
        if self.api_key:
            session.headers["Authorization"] = f"Bearer {self.api_key}"
        session.headers["Accept"] = "application/json"
        return session

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        pagina: int = 1,
        **kwargs
    ) -> dict:
        """Fetch a single page of PCP procurement data."""
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
        }
        if uf:
            params["uf"] = uf

        response = self._execute_with_retry(
            self._get,
            "/licitacoes",  # Endpoint to be confirmed
            params=params
        )
        return response.json()

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        **kwargs
    ):
        """Fetch all PCP procurement records with pagination."""
        if ufs:
            for uf in ufs:
                yield from self._fetch_for_uf(data_inicial, data_final, uf)
        else:
            yield from self._fetch_for_uf(data_inicial, data_final, None)

    def _fetch_for_uf(self, data_inicial, data_final, uf):
        pagina = 1
        while True:
            response = self.fetch_page(data_inicial, data_final, uf, pagina)
            data = response.get("data", [])

            for item in data:
                yield self.transformer.transform(item)

            if not response.get("temProximaPagina", False):
                break
            pagina += 1
```

### Transformer Structure

```python
# In schemas/transformers.py

class PCPTransformer(BaseTransformer):
    """Transform Portal de Compras Publicas data to unified schema."""

    # Field mappings (to be confirmed from API docs)
    FIELD_MAP = {
        "codigo": "source_id",
        "objeto": "objeto",
        "valorEstimado": "valor_estimado",
        "modalidade": "modalidade_original",
        "situacao": "status",
        "uf": "uf",
        "municipio": "municipio",
        "orgao": "orgao_nome",
        "cnpj": "orgao_cnpj",
        "dataPublicacao": "data_publicacao",
        "dataAbertura": "data_abertura",
        "link": "source_url",
    }

    MODALITY_MAP = {
        "PE": UnifiedModality.PREGAO_ELETRONICO,
        "PP": UnifiedModality.PREGAO_PRESENCIAL,
        "CO": UnifiedModality.CONCORRENCIA,
        "TP": UnifiedModality.TOMADA_PRECOS,
        "CV": UnifiedModality.CONVITE,
        "DL": UnifiedModality.DISPENSA,
        "IN": UnifiedModality.INEXIGIBILIDADE,
    }

    STATUS_MAP = {
        "ABERTO": ProcurementStatus.OPEN,
        "FECHADO": ProcurementStatus.CLOSED,
        "SUSPENSO": ProcurementStatus.SUSPENDED,
        "CANCELADO": ProcurementStatus.CANCELLED,
        "HOMOLOGADO": ProcurementStatus.AWARDED,
    }

    def transform(self, raw: dict) -> UnifiedProcurement:
        return UnifiedProcurement(
            id=str(uuid.uuid4()),
            source=SourceType.PCP,
            source_id=str(raw.get("codigo", "")),
            source_url=raw.get("link"),
            objeto=raw.get("objeto", ""),
            valor_estimado=self._parse_float(raw.get("valorEstimado")),
            modalidade=self._map_modality(raw.get("modalidade")),
            modalidade_original=raw.get("modalidade"),
            status=self._map_status(raw.get("situacao")),
            uf=raw.get("uf", ""),
            municipio=raw.get("municipio"),
            orgao_nome=raw.get("orgao", ""),
            orgao_cnpj=self._normalize_cnpj(raw.get("cnpj")),
            data_publicacao=self._parse_date(raw.get("dataPublicacao")),
            data_abertura=self._parse_datetime(raw.get("dataAbertura")),
            raw_data=raw,
        )
```

---

## Environment Variables

```bash
# .env
PCP_API_KEY=your-api-key-here  # If required
PCP_TIMEOUT=30
PCP_MAX_RETRIES=3
```

---

## Definition of Done

- [ ] `PCPClient` implemented and working
- [ ] Authentication configured (if required)
- [ ] `PCPTransformer` mapping all fields
- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration test documented
- [ ] Configuration documented
- [ ] Code reviewed by peer

---

## Story Points: 8 SP

**Complexity:** Medium (API documented)
**Uncertainty:** Medium (authentication details TBD)

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
| API requires approval | Medium | High | Apply for access early |
| API costs/quotas | Medium | Medium | Budget for API costs |
| Data format differs | Low | Medium | Flexible parsing |
| Rate limits strict | Medium | Medium | Adaptive rate limiting |

---

## Test Data

Mock response for testing:

```json
{
  "data": [
    {
      "codigo": "PCP-2026-12345",
      "objeto": "Contratacao de servicos de limpeza",
      "valorEstimado": 250000.00,
      "modalidade": "PE",
      "situacao": "ABERTO",
      "uf": "RJ",
      "municipio": "Rio de Janeiro",
      "orgao": "Secretaria de Administracao",
      "cnpj": "42498733000148",
      "dataPublicacao": "2026-02-01",
      "dataAbertura": "2026-02-20T10:00:00",
      "link": "https://www.portaldecompraspublicas.com.br/licitacao/12345"
    }
  ],
  "totalRegistros": 85,
  "pagina": 1,
  "totalPaginas": 5,
  "temProximaPagina": true
}
```

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research: `docs/stories/STORY-156-api-research-discovery.md`
- Base Client: `docs/stories/STORY-159-base-client-refactoring.md`
- PCP Website: https://www.portaldecompraspublicas.com.br/
- PCP API: https://apipcp.portaldecompraspublicas.com.br/

---

**Story Status:** READY (pending dependencies)
**Estimated Duration:** 3-4 days
**Priority:** P1 - Critical Path
