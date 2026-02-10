---
task: Implement ComprasGov Adapter Modalidade Support
responsavel: "@backend-engineer"
responsavel_type: agent
atomic_layer: task
elicit: false
priority: P0
phase: 3
parallel_execution: true
Entrada: |
  - Updated ModalidadeContratacao enum from Phase 2
  - ComprasGov API modalidade field mapping
  - Current compras_gov_client.py normalize() method
  - Modalidade name normalization requirements
Saida: |
  - Updated normalize() method with all 8 modalities
  - Modalidade name normalization logic
  - Unit tests for each modality
  - Integration tests with real API
Checklist:
  - "[ ] Read current ComprasGovAdapter.normalize() method"
  - "[ ] Identify modalidade field in API response"
  - "[ ] Create modalidade name mapping for variations"
  - "[ ] Update normalize() to handle all 8 modalities"
  - "[ ] Add normalization for name variations"
  - "[ ] Write unit tests for each modality"
  - "[ ] Test with real ComprasGov API data"
  - "[ ] Verify no regressions in existing functionality"
---

# Implement ComprasGov Adapter - Lei 14.133 Modalities

## Objective

Update the ComprasGov source adapter to correctly normalize all 8 Lei 14.133/2021 modalities from the API response format to the unified schema format.

## Background

**ComprasGov API:**
- Base URL: https://compras.dados.gov.br
- Endpoint: /licitacoes/v1/licitacoes.json
- Open data API (no auth required)
- Returns modalidade in various field names and formats

**Current State:**
- Adapter exists in `backend/clients/compras_gov_client.py`
- `normalize()` method extracts modalidade from raw record
- May not handle all Lei 14.133 modalities correctly

**Target State:**
- All 8 official modalities correctly mapped
- Name variations handled (accents, casing, abbreviations)
- Deprecated modalities flagged if present
- Consistent normalization to standard names

## Implementation Steps

### 1. Analyze Current Implementation

```bash
# Read the current adapter
Read backend/clients/compras_gov_client.py

# Focus on normalize() method around line 325-450
# Look for modalidade extraction logic
```

### 2. Create Modalidade Mapping Dictionary

Add to `ComprasGovAdapter` class:

```python
# Modalidade name normalization mapping
MODALIDADE_MAPPING = {
    # Exact Lei 14.133 names (preferred output)
    "Pregao Eletronico": "Pregao Eletronico",
    "Pregao Presencial": "Pregao Presencial",
    "Concorrencia": "Concorrencia",
    "Concurso": "Concurso",
    "Leilao": "Leilao",
    "Dispensa de Licitacao": "Dispensa de Licitacao",
    "Inexigibilidade": "Inexigibilidade",
    "Dialogo Competitivo": "Dialogo Competitivo",

    # Common variations (input normalization)
    "PREGAO ELETRONICO": "Pregao Eletronico",
    "PREGÃO ELETRÔNICO": "Pregao Eletronico",
    "Pregão Eletrônico": "Pregao Eletronico",
    "pregão eletrônico": "Pregao Eletronico",
    "Pregão - Eletrônico": "Pregao Eletronico",
    "PE": "Pregao Eletronico",

    "PREGAO PRESENCIAL": "Pregao Presencial",
    "PREGÃO PRESENCIAL": "Pregao Presencial",
    "Pregão Presencial": "Pregao Presencial",
    "pregão presencial": "Pregao Presencial",
    "Pregão - Presencial": "Pregao Presencial",
    "PP": "Pregao Presencial",

    "CONCORRENCIA": "Concorrencia",
    "CONCORRÊNCIA": "Concorrencia",
    "Concorrência": "Concorrencia",
    "concorrência": "Concorrencia",

    "CONCURSO": "Concurso",
    "concurso": "Concurso",

    "LEILAO": "Leilao",
    "LEILÃO": "Leilao",
    "Leilão": "Leilao",
    "leilão": "Leilao",

    "DISPENSA DE LICITACAO": "Dispensa de Licitacao",
    "DISPENSA DE LICITAÇÃO": "Dispensa de Licitacao",
    "Dispensa de Licitação": "Dispensa de Licitacao",
    "dispensa de licitação": "Dispensa de Licitacao",
    "Dispensa": "Dispensa de Licitacao",
    "DISPENSA": "Dispensa de Licitacao",

    "INEXIGIBILIDADE": "Inexigibilidade",
    "Inexigibilidade": "Inexigibilidade",
    "inexigibilidade": "Inexigibilidade",
    "Inexigível": "Inexigibilidade",
    "INEXIGIVEL": "Inexigibilidade",

    "DIALOGO COMPETITIVO": "Dialogo Competitivo",
    "DIÁLOGO COMPETITIVO": "Dialogo Competitivo",
    "Diálogo Competitivo": "Dialogo Competitivo",
    "diálogo competitivo": "Dialogo Competitivo",

    # Deprecated (Lei 8.666/93) - flag for logging
    "Tomada de Precos": "DEPRECATED_TOMADA_PRECOS",
    "TOMADA DE PREÇOS": "DEPRECATED_TOMADA_PRECOS",
    "Tomada de Preços": "DEPRECATED_TOMADA_PRECOS",
    "TP": "DEPRECATED_TOMADA_PRECOS",

    "Convite": "DEPRECATED_CONVITE",
    "CONVITE": "DEPRECATED_CONVITE",
    "convite": "DEPRECATED_CONVITE",
}

def _normalize_modalidade_name(self, raw_name: str) -> str:
    """
    Normalize modalidade name to Lei 14.133 standard.

    Args:
        raw_name: Raw modalidade name from API

    Returns:
        Normalized modalidade name or empty string
    """
    if not raw_name:
        return ""

    # Try direct mapping first
    normalized = self.MODALIDADE_MAPPING.get(raw_name)
    if normalized:
        if normalized.startswith("DEPRECATED_"):
            logger.warning(
                f"[COMPRAS_GOV] Deprecated modalidade found: {raw_name}. "
                "This modality was revoked by Lei 14.133/2021."
            )
            # Return normalized name without DEPRECATED_ prefix for legacy data
            return normalized.replace("DEPRECATED_", "").replace("_", " ").title()
        return normalized

    # Try case-insensitive match
    raw_upper = raw_name.upper()
    for key, value in self.MODALIDADE_MAPPING.items():
        if key.upper() == raw_upper:
            return value

    # Unknown modalidade - log warning
    logger.warning(
        f"[COMPRAS_GOV] Unknown modalidade name: {raw_name}. "
        "Please add to MODALIDADE_MAPPING if valid."
    )
    return raw_name  # Return as-is for debugging
```

### 3. Update normalize() Method

**File:** `backend/clients/compras_gov_client.py`

Locate the modalidade extraction (around line 419-426):

```python
# Extract modalidade
modalidade_raw = (
    raw_record.get("modalidade_licitacao")
    or raw_record.get("modalidade")
    or raw_record.get("tipo")
    or ""
)

# Normalize modalidade name
modalidade = self._normalize_modalidade_name(modalidade_raw)
```

### 4. Add Unit Tests

**File:** `backend/tests/test_compras_gov_client.py`

```python
import pytest
from backend.clients.compras_gov_client import ComprasGovAdapter

class TestComprasGovModalidadeNormalization:
    """Test modalidade normalization for ComprasGov adapter."""

    @pytest.fixture
    def adapter(self):
        return ComprasGovAdapter()

    def test_pregao_eletronico_variations(self, adapter):
        """Test various forms of Pregão Eletrônico."""
        variations = [
            "Pregao Eletronico",
            "PREGÃO ELETRÔNICO",
            "Pregão Eletrônico",
            "pregão eletrônico",
            "Pregão - Eletrônico",
            "PE",
        ]
        for var in variations:
            assert adapter._normalize_modalidade_name(var) == "Pregao Eletronico"

    def test_all_lei_14133_modalities(self, adapter):
        """Test all 8 official Lei 14.133 modalities."""
        modalities = {
            "Pregao Eletronico": "Pregao Eletronico",
            "Pregao Presencial": "Pregao Presencial",
            "Concorrencia": "Concorrencia",
            "Concurso": "Concurso",
            "Leilao": "Leilao",
            "Dispensa de Licitacao": "Dispensa de Licitacao",
            "Inexigibilidade": "Inexigibilidade",
            "Dialogo Competitivo": "Dialogo Competitivo",
        }
        for input_name, expected in modalities.items():
            assert adapter._normalize_modalidade_name(input_name) == expected

    def test_deprecated_modalities_logged(self, adapter, caplog):
        """Deprecated modalities should trigger warning logs."""
        adapter._normalize_modalidade_name("Tomada de Preços")
        assert "deprecated" in caplog.text.lower()
        assert "8.666" in caplog.text or "revoked" in caplog.text.lower()

    def test_unknown_modalidade_logged(self, adapter, caplog):
        """Unknown modalities should trigger warning logs."""
        result = adapter._normalize_modalidade_name("Unknown Modality")
        assert "unknown modalidade" in caplog.text.lower()
        assert result == "Unknown Modality"  # Returned as-is for debugging

@pytest.mark.asyncio
async def test_normalize_with_real_structure():
    """Test normalize() with realistic ComprasGov data structure."""
    adapter = ComprasGovAdapter()

    raw_record = {
        "identificador": "12345",
        "objeto": "Aquisição de uniformes",
        "valor_licitacao": 150000.0,
        "orgao_nome": "Prefeitura Municipal",
        "orgao_cnpj": "12.345.678/0001-90",
        "uf": "SP",
        "municipio": "São Paulo",
        "data_publicacao": "2026-02-10T10:00:00Z",
        "modalidade_licitacao": "Pregão Eletrônico",  # <-- This field
        "situacao": "Publicada",
    }

    result = adapter.normalize(raw_record)

    assert result.modalidade == "Pregao Eletronico"
    assert result.source_name == "COMPRAS_GOV"
```

### 5. Integration Test with Real API

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_compras_gov_real_api_modalidades():
    """Test with real ComprasGov API to verify modalidade extraction."""
    from datetime import date, timedelta

    adapter = ComprasGovAdapter()

    # Fetch recent data
    data_final = date.today().isoformat()
    data_inicial = (date.today() - timedelta(days=7)).isoformat()

    modalidades_found = set()
    count = 0

    async for record in adapter.fetch(data_inicial, data_final):
        if record.modalidade:
            modalidades_found.add(record.modalidade)
        count += 1
        if count >= 100:  # Sample first 100 records
            break

    # Verify we're getting Lei 14.133 modalities
    valid_modalities = {
        "Pregao Eletronico",
        "Pregao Presencial",
        "Concorrencia",
        "Concurso",
        "Leilao",
        "Dispensa de Licitacao",
        "Inexigibilidade",
        "Dialogo Competitivo",
    }

    # At least some modalities should be in the valid set
    assert modalidades_found & valid_modalities, \
        f"No valid Lei 14.133 modalities found. Got: {modalidades_found}"

    # Log all found modalities for analysis
    print(f"Modalidades found in ComprasGov API: {modalidades_found}")
```

### 6. Run Tests

```bash
# Unit tests
pytest backend/tests/test_compras_gov_client.py::TestComprasGovModalidadeNormalization -v

# Integration test (requires API access)
pytest backend/tests/test_compras_gov_client.py::test_compras_gov_real_api_modalidades -v -m integration
```

## Validation Checklist

- [ ] All 8 Lei 14.133 modalities handled
- [ ] Name variations normalized correctly
- [ ] Deprecated modalities logged with warnings
- [ ] Unknown modalities logged for investigation
- [ ] Unit tests pass for all modalities
- [ ] Integration tests pass with real API
- [ ] No regressions in existing normalize() logic
- [ ] Performance not degraded

## Files Modified

- `backend/clients/compras_gov_client.py`
- `backend/tests/test_compras_gov_client.py`

## Success Criteria

✅ All 8 modalities correctly extracted and normalized
✅ Name variations handled (accents, casing, etc.)
✅ Deprecated modalities flagged in logs
✅ Unit tests pass (100% coverage for modalidade logic)
✅ Integration tests pass with real API
✅ No performance degradation

## Expected API Field Names

ComprasGov may use these field names for modalidade:
- `modalidade_licitacao` (most common)
- `modalidade`
- `tipo`
- `tipo_modalidade`

The normalize() method should check all variations.

---

**Priority:** P0 (Critical - ComprasGov is a major data source)
**Phase:** 3 (Source Adapters)
**Agent:** @backend-engineer
**Parallel Execution:** Can run in parallel with Portal Compras and Licitar adapters
**Estimated Duration:** 3-4 hours
