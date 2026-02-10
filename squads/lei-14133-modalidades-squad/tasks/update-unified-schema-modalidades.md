---
task: Update Unified Schema with All Lei 14.133 Modalities
responsavel: "@backend-engineer"
responsavel_type: agent
atomic_layer: task
elicit: false
priority: P0
phase: 2
Entrada: |
  - Lei 14.133/2021 official modalities list (from legal research)
  - Current unified.py schema
  - Current schemas.py with ModalidadeContratacao enum
  - Validation requirements
Saida: |
  - Updated UnifiedProcurement with modalidade field
  - Complete ModalidadeContratacao enum (codes 1-3, 6-7, 9-11)
  - Removed deprecated codes (4, 5)
  - Updated validation logic
  - Updated docstrings with Lei article references
Checklist:
  - "[ ] Read current unified.py schema"
  - "[ ] Read current schemas.py with enums"
  - "[ ] Update ModalidadeContratacao enum with codes 1,2,3,6,7,9,10,11"
  - "[ ] Remove or deprecate codes 4, 5"
  - "[ ] Add Lei article references in docstrings"
  - "[ ] Update field validation"
  - "[ ] Run schema validation tests"
  - "[ ] Verify backward compatibility strategy"
---

# Update Unified Schema - Lei 14.133 Modalities

## Objective

Update the unified procurement schema to support all 8 official modalities from Lei 14.133/2021 and remove deprecated modalities from Lei 8.666/93.

## Background

**Current State:**
- `UnifiedProcurement` has a `modalidade: str` field
- `ModalidadeContratacao` enum exists in schemas.py with codes 1-10
- Includes deprecated codes 4 (Tomada de Preços) and 5 (Convite)
- Missing code 11 (Concurso)

**Target State:**
- Complete enum with codes: 1, 2, 3, 6, 7, 9, 10, 11
- Deprecated codes removed: 4, 5
- Code 8 (Credenciamento) status determined
- All modalities have Lei article references

## Implementation Steps

### 1. Read Current Schema

```bash
# Read the current unified schema
Read backend/unified_schemas/unified.py

# Read the current modalidade enum
Read backend/schemas.py
```

### 2. Update ModalidadeContratacao Enum

**File:** `backend/schemas.py`

```python
from enum import IntEnum

class ModalidadeContratacao(IntEnum):
    """
    Modalidades de contratação definidas na Lei 14.133/2021.

    References:
    - Lei 14.133/2021: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm
    - Revogou Lei 8.666/93 e Lei 10.520/02
    """

    # Pregão (Art. 6º, XLIII)
    PREGAO_ELETRONICO = 1
    """Pregão Eletrônico - Modalidade obrigatória para bens/serviços comuns."""

    PREGAO_PRESENCIAL = 2
    """Pregão Presencial - Forma presencial do pregão (quando motivado)."""

    # Concorrência (Art. 6º, XLII)
    CONCORRENCIA = 3
    """Concorrência - Para bens/serviços especiais e obras de engenharia."""

    # Dispensa e Inexigibilidade (Art. 74 e 75)
    DISPENSA = 6
    """Dispensa de Licitação - Contratação direta (Art. 75)."""

    INEXIGIBILIDADE = 7
    """Inexigibilidade - Inviabilidade de competição (Art. 74)."""

    # Outras Modalidades
    LEILAO = 9
    """Leilão - Alienação de bens (Art. 6º, XLV)."""

    DIALOGO_COMPETITIVO = 10
    """Diálogo Competitivo - Soluções inovadoras (Art. 6º, XLVI)."""

    CONCURSO = 11
    """Concurso - Trabalho técnico, científico ou artístico (Art. 6º, XLIV)."""

    # DEPRECATED - Lei 8.666/93 (revogada)
    # TOMADA_PRECOS = 4  # REMOVED - Use CONCORRENCIA or PREGAO
    # CONVITE = 5         # REMOVED - Use PREGAO or DISPENSA

    @classmethod
    def is_valid(cls, code: int) -> bool:
        """Validate if code is an official Lei 14.133 modality."""
        return code in {1, 2, 3, 6, 7, 9, 10, 11}

    @classmethod
    def get_deprecated_message(cls, code: int) -> str:
        """Get deprecation message for legacy codes."""
        messages = {
            4: "Tomada de Preços foi revogada pela Lei 14.133/2021. Use Concorrência (3) ou Pregão (1/2).",
            5: "Convite foi revogado pela Lei 14.133/2021. Use Pregão (1/2) ou Dispensa (6).",
        }
        return messages.get(code, f"Código {code} não é uma modalidade válida da Lei 14.133/2021.")
```

### 3. Update UnifiedProcurement Docstrings

**File:** `backend/unified_schemas/unified.py`

Update the `modalidade` field docstring:

```python
modalidade: str = Field(
    default="",
    description="Procurement modality per Lei 14.133/2021 (e.g., 'Pregao Eletronico', 'Concorrencia')"
)
```

### 4. Update BuscaRequest Validation

**File:** `backend/schemas.py`

```python
class BuscaRequest(BaseModel):
    """Request schema for procurement search."""

    modalidades: Optional[List[int]] = Field(
        default=None,
        description="Modalidade codes to filter (1,2,3,6,7,9,10,11)"
    )

    @field_validator("modalidades")
    @classmethod
    def validate_modalidades(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Validate modalidade codes against Lei 14.133/2021."""
        if v is None or len(v) == 0:
            return v

        invalid = [code for code in v if not ModalidadeContratacao.is_valid(code)]

        if invalid:
            deprecated = [c for c in invalid if c in {4, 5}]
            truly_invalid = [c for c in invalid if c not in {4, 5}]

            messages = []
            if deprecated:
                messages.append(
                    f"Códigos deprecated (Lei 8.666/93 revogada): {deprecated}. "
                    "Use modalidades da Lei 14.133/2021."
                )
            if truly_invalid:
                messages.append(
                    f"Códigos inválidos: {truly_invalid}. "
                    "Códigos válidos: 1,2,3,6,7,9,10,11."
                )

            raise ValueError(" ".join(messages))

        return v
```

### 5. Add Helper Constants

```python
# Valid Lei 14.133 modality codes
VALID_MODALIDADE_CODES = {1, 2, 3, 6, 7, 9, 10, 11}

# Deprecated Lei 8.666/93 codes
DEPRECATED_MODALIDADE_CODES = {4, 5}

# Modalidade name mapping (for normalization)
MODALIDADE_NAMES = {
    1: "Pregao Eletronico",
    2: "Pregao Presencial",
    3: "Concorrencia",
    6: "Dispensa de Licitacao",
    7: "Inexigibilidade",
    9: "Leilao",
    10: "Dialogo Competitivo",
    11: "Concurso",
}
```

### 6. Update Tests

**File:** `backend/tests/test_modalidade_filter.py`

```python
def test_valid_lei_14133_modalidades():
    """All valid Lei 14.133 codes should be accepted."""
    d_ini, d_fin = _recent_dates(7)
    request = BuscaRequest(
        ufs=["SP"],
        data_inicial=d_ini,
        data_final=d_fin,
        modalidades=[1, 2, 3, 6, 7, 9, 10, 11],
    )
    assert len(request.modalidades) == 8

def test_deprecated_modalidade_rejection():
    """Deprecated codes 4 and 5 should be rejected."""
    d_ini, d_fin = _recent_dates(7)

    # Code 4 (Tomada de Preços)
    with pytest.raises(ValidationError) as exc:
        BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[4],
        )
    assert "deprecated" in str(exc.value).lower()
    assert "8.666" in str(exc.value)

    # Code 5 (Convite)
    with pytest.raises(ValidationError) as exc:
        BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[5],
        )
    assert "deprecated" in str(exc.value).lower()

def test_concurso_new_modalidade():
    """Concurso (code 11) should be accepted."""
    d_ini, d_fin = _recent_dates(7)
    request = BuscaRequest(
        ufs=["SP"],
        data_inicial=d_ini,
        data_final=d_fin,
        modalidades=[11],
    )
    assert 11 in request.modalidades
```

## Validation Checklist

- [ ] Enum contains exactly 8 codes: 1, 2, 3, 6, 7, 9, 10, 11
- [ ] Codes 4 and 5 are NOT in enum
- [ ] Each modality has Lei article reference in docstring
- [ ] Validation rejects codes 4, 5 with clear error
- [ ] Validation rejects invalid codes (0, 12+)
- [ ] Tests pass for all 8 valid codes
- [ ] Tests verify deprecated code rejection
- [ ] Backward compatibility strategy documented

## Files Modified

- `backend/schemas.py` - ModalidadeContratacao enum, BuscaRequest validation
- `backend/unified_schemas/unified.py` - Docstring updates
- `backend/tests/test_modalidade_filter.py` - New tests for all codes

## Success Criteria

✅ All 8 Lei 14.133 modalities in enum
✅ Deprecated codes removed/rejected
✅ Clear error messages for invalid codes
✅ All tests passing
✅ Lei article references in docstrings
✅ Validation logic prevents deprecated usage

## References

- **Lei 14.133/2021:** https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm
- **Decreto 12.807/2025:** Valores atualizados para dispensa
- **TCU Guidelines:** https://licitacoesecontratos.tcu.gov.br/

---

**Priority:** P0 (Critical - Foundation for all other changes)
**Phase:** 2 (Backend Core)
**Agent:** @backend-engineer
**Estimated Duration:** 2-3 hours
