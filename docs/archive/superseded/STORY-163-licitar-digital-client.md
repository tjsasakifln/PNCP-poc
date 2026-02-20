# Story MSP-001-08: Licitar Digital Client Implementation

**Story ID:** MSP-001-08
**GitHub Issue:** #163 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to implement a client for Licitar Digital,
**So that** users can search for multi-agency procurement opportunities from this platform.

---

## Objective

Create a new procurement client that:

1. Extends the `BaseClient` abstraction
2. Connects to Licitar Digital RESTful APIs
3. Transforms Licitar data to unified schema
4. Handles Licitar-specific error scenarios
5. Respects Licitar rate limits

---

## Background

**Licitar Digital:** https://licitar.digital/

- Most innovative public procurement platform in Brazil
- Completely free for public entities
- Multiple modalities: Pregao, Dispensa, Credenciamento, Leilao, Concorrencia
- RESTful API integration confirmed
- Supports automated system registration (webservices, APIs, robots)
- Integrated price database

**API Status:** CONFIRMED - RESTful APIs available

---

## Acceptance Criteria

### AC1: Client Implementation
- [ ] `LicitarClient` class extends `BaseClient`
- [ ] Connects to Licitar Digital REST API
- [ ] Implements `fetch_page()` method
- [ ] Implements `fetch_all()` generator method
- [ ] Handles pagination properly
- [ ] Registers as automated system if required

### AC2: Data Transformation
- [ ] `LicitarTransformer` implements `BaseTransformer`
- [ ] All Licitar fields mapped to unified schema
- [ ] Modality codes normalized (7 modalities)
- [ ] Status codes normalized
- [ ] Source URL preserved

### AC3: Error Handling
- [ ] Licitar-specific exceptions defined
- [ ] Authentication errors handled
- [ ] Rate limit handling
- [ ] Network timeout handling

### AC4: Configuration
- [ ] `LICITAR_CONFIG` defined in sources.py
- [ ] API credentials support (if required)
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
- [ ] Registration process documented

---

## Technical Tasks

### Task 1: API Documentation Review (1 SP)
- [ ] Review Licitar Digital API documentation
- [ ] Understand registration for automated access
- [ ] Document all available endpoints
- [ ] Note rate limits and pagination

### Task 2: Client Implementation (4 SP)
- [ ] Create `backend/clients/licitar_client.py`
- [ ] Implement `LicitarClient` class
- [ ] Implement authentication/registration
- [ ] Implement `fetch_page()` method
- [ ] Implement `fetch_all()` generator

### Task 3: Transformer Implementation (2 SP)
- [ ] Add Licitar schema to `source_schemas.py`
- [ ] Implement `LicitarTransformer` class
- [ ] Map all 7 modalities
- [ ] Add field validation

### Task 4: Testing (1 SP)
- [ ] Create `backend/tests/test_licitar_client.py`
- [ ] Add mock responses
- [ ] Test all modality transformations
- [ ] Test error handling paths

---

## Implementation Notes

### Known API Information

```
Main website: https://licitar.digital/
API: RESTful APIs available
Registration: Required for automated access
Docs: Available at licitardigital.com.br
```

### Supported Modalities

1. **Pregao** - Electronic bidding
2. **Dispensa** - Bidding exemption
3. **Credenciamento** - Accreditation
4. **Leilao** - Auction
5. **Concorrencia** - Competitive bidding
6. **Inexigibilidade** - Non-requirement
7. **Pre-qualificacao** - Pre-qualification

### Expected Client Structure

```python
# backend/clients/licitar_client.py

from .base_client import BaseClient, SourceConfig
from schemas.transformers import LicitarTransformer
import os

class LicitarClient(BaseClient):
    """Client for Licitar Digital multi-agency procurement platform."""

    DEFAULT_CONFIG = SourceConfig(
        name="licitar",
        base_url="https://api.licitar.digital",  # To be confirmed
        timeout=30.0,
        max_retries=3,
        base_delay=1.0,
        requests_per_second=5.0,
    )

    def __init__(self, config: SourceConfig | None = None, api_key: str | None = None):
        super().__init__(config or self.DEFAULT_CONFIG)
        self.api_key = api_key or os.getenv("LICITAR_API_KEY")
        self.transformer = LicitarTransformer()

    def _create_session(self):
        session = super()._create_session()
        if self.api_key:
            session.headers["X-API-Key"] = self.api_key  # Or appropriate auth header
        session.headers["Accept"] = "application/json"
        session.headers["User-Agent"] = "BidIQ/1.0 (automated-procurement-search)"
        return session

    def fetch_page(
        self,
        data_inicial: str,
        data_final: str,
        uf: str | None = None,
        modalidade: str | None = None,
        pagina: int = 1,
        **kwargs
    ) -> dict:
        """Fetch a single page of Licitar Digital procurement data."""
        params = {
            "dataInicio": data_inicial,
            "dataFim": data_final,
            "pagina": pagina,
            "tamanhoPagina": 50,  # Adjust based on API limits
        }
        if uf:
            params["uf"] = uf
        if modalidade:
            params["modalidade"] = modalidade

        return self._execute_with_retry(
            self._fetch_impl,
            "/api/licitacoes",  # Endpoint to be confirmed
            params
        )

    def _fetch_impl(self, endpoint: str, params: dict) -> dict:
        """Internal fetch implementation."""
        response = self.session.get(
            f"{self.config.base_url}{endpoint}",
            params=params,
            timeout=self.config.timeout
        )

        if response.status_code == 401:
            raise LicitarAuthError("Authentication failed - check API key")
        if response.status_code == 429:
            raise LicitarRateLimitError("Rate limit exceeded")

        response.raise_for_status()
        return response.json()

    def fetch_all(
        self,
        data_inicial: str,
        data_final: str,
        ufs: list[str] | None = None,
        modalidades: list[str] | None = None,
        **kwargs
    ):
        """Fetch all Licitar Digital procurement records."""
        # Fetch all modalities if not specified
        modalidades_to_fetch = modalidades or [
            "PREGAO", "DISPENSA", "CONCORRENCIA",
            "CREDENCIAMENTO", "LEILAO", "INEXIGIBILIDADE"
        ]

        seen_ids = set()

        for modalidade in modalidades_to_fetch:
            if ufs:
                for uf in ufs:
                    yield from self._fetch_paginated(
                        data_inicial, data_final, uf, modalidade, seen_ids
                    )
            else:
                yield from self._fetch_paginated(
                    data_inicial, data_final, None, modalidade, seen_ids
                )

    def _fetch_paginated(self, data_inicial, data_final, uf, modalidade, seen_ids):
        """Paginate through results for a specific filter combination."""
        pagina = 1

        while True:
            response = self.fetch_page(
                data_inicial, data_final, uf, modalidade, pagina
            )
            data = response.get("licitacoes", [])

            if not data:
                break

            for item in data:
                item_id = item.get("codigo", "")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    yield self.transformer.transform(item)

            # Check pagination
            total_pages = response.get("totalPaginas", 1)
            if pagina >= total_pages:
                break

            pagina += 1

class LicitarAuthError(Exception):
    """Raised when Licitar Digital authentication fails."""
    pass

class LicitarRateLimitError(Exception):
    """Raised when Licitar Digital rate limit is exceeded."""
    pass
```

### Transformer Structure

```python
# In schemas/transformers.py

class LicitarTransformer(BaseTransformer):
    """Transform Licitar Digital data to unified schema."""

    MODALITY_MAP = {
        "PREGAO": UnifiedModality.PREGAO_ELETRONICO,
        "PREGAO_PRESENCIAL": UnifiedModality.PREGAO_PRESENCIAL,
        "DISPENSA": UnifiedModality.DISPENSA,
        "CONCORRENCIA": UnifiedModality.CONCORRENCIA,
        "CREDENCIAMENTO": UnifiedModality.CREDENCIAMENTO,
        "LEILAO": UnifiedModality.LEILAO,
        "INEXIGIBILIDADE": UnifiedModality.INEXIGIBILIDADE,
        "TOMADA_PRECOS": UnifiedModality.TOMADA_PRECOS,
    }

    STATUS_MAP = {
        "PUBLICADO": ProcurementStatus.OPEN,
        "EM_ANDAMENTO": ProcurementStatus.OPEN,
        "ENCERRADO": ProcurementStatus.CLOSED,
        "SUSPENSO": ProcurementStatus.SUSPENDED,
        "CANCELADO": ProcurementStatus.CANCELLED,
        "HOMOLOGADO": ProcurementStatus.AWARDED,
        "ADJUDICADO": ProcurementStatus.AWARDED,
    }

    def transform(self, raw: dict) -> UnifiedProcurement:
        return UnifiedProcurement(
            id=str(uuid.uuid4()),
            source=SourceType.LICITAR,
            source_id=str(raw.get("codigo", "")),
            source_url=self._build_url(raw),
            objeto=raw.get("objeto", ""),
            valor_estimado=self._parse_float(raw.get("valorEstimado")),
            modalidade=self._map_modality(raw.get("modalidade")),
            modalidade_original=raw.get("modalidade"),
            status=self._map_status(raw.get("situacao")),
            uf=raw.get("uf", ""),
            municipio=raw.get("municipio"),
            orgao_nome=raw.get("entidade", {}).get("nome", ""),
            orgao_cnpj=self._normalize_cnpj(raw.get("entidade", {}).get("cnpj")),
            data_publicacao=self._parse_date(raw.get("dataPublicacao")),
            data_abertura=self._parse_datetime(raw.get("dataAbertura")),
            data_encerramento=self._parse_datetime(raw.get("dataEncerramento")),
            raw_data=raw,
        )

    def _build_url(self, raw: dict) -> str | None:
        """Build Licitar Digital process URL."""
        codigo = raw.get("codigo")
        if codigo:
            return f"https://licitar.digital/processo/{codigo}"
        return None
```

---

## Environment Variables

```bash
# .env
LICITAR_API_KEY=your-api-key-here  # If required
LICITAR_BASE_URL=https://api.licitar.digital
LICITAR_TIMEOUT=30
LICITAR_MAX_RETRIES=3
```

---

## Registration Process

Licitar Digital supports registration of automated systems. Process:

1. Access registration section on licitar.digital
2. Register as legal entity (webservice/API/robot type)
3. Obtain API credentials
4. Review terms of use for automated access

Document the registration process in `docs/setup/licitar-registration.md`.

---

## Definition of Done

- [ ] `LicitarClient` implemented and working
- [ ] API registration completed (if required)
- [ ] `LicitarTransformer` mapping all 7 modalities
- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration test documented
- [ ] Configuration documented
- [ ] Registration process documented
- [ ] Code reviewed by peer

---

## Story Points: 8 SP

**Complexity:** Medium (API documented, RESTful)
**Uncertainty:** Medium (registration process TBD)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-01 | Data dependency | API research provides full details |
| MSP-001-02 | Data dependency | Unified schema for transformation |
| MSP-001-04 | Code dependency | Must extend BaseClient |

---

## Blocks

- MSP-001-09 (Consolidation Service)

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Registration delays | Medium | Medium | Start registration early |
| API costs | Low | Medium | Licitar is free, but verify |
| ToS restrictions | Low | High | Review terms before development |
| Multiple modality handling | Medium | Medium | Test each modality separately |

---

## Test Data

Mock response for testing:

```json
{
  "licitacoes": [
    {
      "codigo": "LD-2026-98765",
      "objeto": "Aquisicao de mobiliario escolar",
      "valorEstimado": 180000.00,
      "modalidade": "PREGAO",
      "situacao": "PUBLICADO",
      "uf": "PR",
      "municipio": "Curitiba",
      "entidade": {
        "nome": "Prefeitura Municipal de Curitiba",
        "cnpj": "76417005000186"
      },
      "dataPublicacao": "2026-02-02",
      "dataAbertura": "2026-02-18T09:00:00",
      "dataEncerramento": null
    }
  ],
  "totalRegistros": 42,
  "pagina": 1,
  "totalPaginas": 3,
  "tamanhoPagina": 50
}
```

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Research: `docs/stories/STORY-156-api-research-discovery.md`
- Base Client: `docs/stories/STORY-159-base-client-refactoring.md`
- Licitar Website: https://licitar.digital/
- Licitar Regulations: https://licitar.digital/regulamento-sistema-de-compras-digital-licitar-digital/

---

**Story Status:** READY (pending dependencies)
**Estimated Duration:** 3-4 days
**Priority:** P2 - Important
