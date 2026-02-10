# Lei 14.133/2021 Compliance Checklist

**Squad:** lei-14133-modalidades-squad
**Legal Standard:** Lei 14.133/2021
**Decree Reference:** Decreto 12.807/2025
**Validation Date:** _____________
**Auditor:** @legal-compliance-auditor

---

## Section 1: Official Modalities Implementation

### 1.1 Pregão Eletrônico (Art. 6º, XLIII)
- [ ] Code 1 implemented in backend schema
- [ ] Code 1 present in frontend filter
- [ ] ComprasGov adapter supports Pregão Eletrônico
- [ ] Portal Compras adapter supports Pregão Eletrônico
- [ ] Licitar adapter supports Pregão Eletrônico
- [ ] Tests cover Pregão Eletrônico filtering
- [ ] Description references Art. 6º, XLIII
- [ ] Marked as "popular" in UI

**Article Reference:** Lei 14.133/2021, Art. 6º, XLIII
**Description:** "Modalidade de licitação obrigatória para aquisição de bens e serviços comuns"
**Criterion:** Menor preço ou maior desconto

---

### 1.2 Pregão Presencial (Art. 6º, XLIII)
- [ ] Code 2 implemented in backend schema
- [ ] Code 2 present in frontend filter
- [ ] ComprasGov adapter supports Pregão Presencial
- [ ] Portal Compras adapter supports Pregão Presencial
- [ ] Licitar adapter supports Pregão Presencial
- [ ] Tests cover Pregão Presencial filtering
- [ ] Description references Art. 6º, XLIII
- [ ] Marked as "popular" in UI

**Article Reference:** Lei 14.133/2021, Art. 6º, XLIII
**Description:** "Forma presencial do pregão, apenas quando motivado"
**Criterion:** Menor preço ou maior desconto

---

### 1.3 Concorrência (Art. 6º, XLII)
- [ ] Code 3 implemented in backend schema
- [ ] Code 3 present in frontend filter
- [ ] ComprasGov adapter supports Concorrência
- [ ] Portal Compras adapter supports Concorrência
- [ ] Licitar adapter supports Concorrência
- [ ] Tests cover Concorrência filtering
- [ ] Description references Art. 6º, XLII
- [ ] Categorization (popular/other) appropriate

**Article Reference:** Lei 14.133/2021, Art. 6º, XLII
**Description:** "Modalidade para contratação de bens e serviços especiais e obras/serviços de engenharia"
**Criterion:** Variados (menor preço, melhor técnica, técnica e preço)

---

### 1.4 Concurso (Art. 6º, XLIV)
- [ ] Code 11 implemented in backend schema
- [ ] Code 11 present in frontend filter
- [ ] ComprasGov adapter supports Concurso
- [ ] Portal Compras adapter supports Concurso
- [ ] Licitar adapter supports Concurso
- [ ] Tests cover Concurso filtering
- [ ] Description references Art. 6º, XLIV
- [ ] Categorization (popular/other) appropriate

**Article Reference:** Lei 14.133/2021, Art. 6º, XLIV
**Description:** "Escolha de trabalho técnico, científico ou artístico"
**Criterion:** Melhor técnica ou conteúdo artístico

---

### 1.5 Leilão (Art. 6º, XLV)
- [ ] Code 9 implemented in backend schema
- [ ] Code 9 present in frontend filter
- [ ] ComprasGov adapter supports Leilão
- [ ] Portal Compras adapter supports Leilão
- [ ] Licitar adapter supports Leilão
- [ ] Tests cover Leilão filtering
- [ ] Description references Art. 6º, XLV
- [ ] Categorization (popular/other) appropriate

**Article Reference:** Lei 14.133/2021, Art. 6º, XLV
**Description:** "Alienação de bens imóveis ou móveis inservíveis/apreendidos"
**Criterion:** Maior lance

---

### 1.6 Dispensa de Licitação (Art. 75)
- [ ] Code 6 implemented in backend schema
- [ ] Code 6 present in frontend filter
- [ ] ComprasGov adapter supports Dispensa
- [ ] Portal Compras adapter supports Dispensa
- [ ] Licitar adapter supports Dispensa
- [ ] Tests cover Dispensa filtering
- [ ] Description references Art. 75
- [ ] Marked as "popular" in UI
- [ ] Values from Decreto 12.807/2025 documented

**Article Reference:** Lei 14.133/2021, Art. 75
**Description:** "Contratação direta quando competição é dispensável"
**Decree Values (2026):**
- Obras/Serviços de Engenharia: < R$ 125.451,15
- Outros Serviços/Compras: < R$ 62.725,59
- Consórcios/Agências: 2x os valores acima

---

### 1.7 Inexigibilidade (Art. 74)
- [ ] Code 7 implemented in backend schema
- [ ] Code 7 present in frontend filter
- [ ] ComprasGov adapter supports Inexigibilidade
- [ ] Portal Compras adapter supports Inexigibilidade
- [ ] Licitar adapter supports Inexigibilidade
- [ ] Tests cover Inexigibilidade filtering
- [ ] Description references Art. 74
- [ ] Categorization (popular/other) appropriate

**Article Reference:** Lei 14.133/2021, Art. 74
**Description:** "Contratação direta quando há inviabilidade de competição"

---

### 1.8 Diálogo Competitivo (Art. 6º, XLVI)
- [ ] Code 10 implemented in backend schema
- [ ] Code 10 present in frontend filter
- [ ] ComprasGov adapter supports Diálogo Competitivo
- [ ] Portal Compras adapter supports Diálogo Competitivo
- [ ] Licitar adapter supports Diálogo Competitivo
- [ ] Tests cover Diálogo Competitivo filtering
- [ ] Description references Art. 6º, XLVI
- [ ] Categorization (popular/other) appropriate

**Article Reference:** Lei 14.133/2021, Art. 6º, XLVI
**Description:** "Para soluções inovadoras mediante diálogos com licitantes"

---

## Section 2: Deprecated Modalities Removal

### 2.1 Tomada de Preços (Lei 8.666/93 - DEPRECATED)
- [ ] Code 4 removed from backend schema
- [ ] Code 4 removed from frontend filter
- [ ] Validation rejects code 4 with clear error message
- [ ] Tests verify code 4 rejection
- [ ] Existing data with code 4 migrated to code 3 (Concorrência)
- [ ] Migration script tested and executed
- [ ] User documentation explains deprecation

**Deprecated By:** Lei 14.133/2021 (revoked Lei 8.666/93)
**Migration Target:** Concorrência (Code 3) or Pregão (Code 1/2)

---

### 2.2 Convite (Lei 8.666/93 - DEPRECATED)
- [ ] Code 5 removed from backend schema
- [ ] Code 5 removed from frontend filter
- [ ] Validation rejects code 5 with clear error message
- [ ] Tests verify code 5 rejection
- [ ] Existing data with code 5 migrated to code 6 (Dispensa) or code 1/2 (Pregão)
- [ ] Migration script tested and executed
- [ ] User documentation explains deprecation

**Deprecated By:** Lei 14.133/2021 (revoked Lei 8.666/93)
**Migration Target:** Dispensa (Code 6) or Pregão (Code 1/2)

---

### 2.3 Credenciamento (Code 8 - REVIEW NEEDED)
- [ ] Status of code 8 determined (not a modality per Lei 14.133)
- [ ] Decision made: remove, deprecate, or keep as auxiliary procedure
- [ ] Action taken based on decision
- [ ] Documentation updated

**Note:** Credenciamento is not listed as an official modality in Lei 14.133/2021. It may be an auxiliary procedure rather than a modality.

---

## Section 3: Backend Implementation

### 3.1 Schema Compliance
- [ ] `UnifiedProcurement.modalidade` field exists
- [ ] `ModalidadeContratacao` enum defined
- [ ] Enum contains codes: 1, 2, 3, 6, 7, 9, 10, 11
- [ ] Enum DOES NOT contain codes: 4, 5
- [ ] `BuscaRequest.modalidades` field validates codes
- [ ] Validation accepts: 1-3, 6-7, 9-11
- [ ] Validation rejects: 0, 4, 5, 12+
- [ ] Error messages are clear and reference Lei 14.133

**Files to Check:**
- `backend/unified_schemas/unified.py`
- `backend/schemas.py`

---

### 3.2 Source Adapter Compliance
- [ ] All adapters inherit from `SourceAdapter`
- [ ] All adapters implement `normalize()` method
- [ ] All adapters map source-specific modalidade to Lei 14.133 standard names
- [ ] Adapters handle name variations (accents, casing, etc.)
- [ ] Adapters log normalization warnings for unknown modalities
- [ ] No hardcoded dependencies on deprecated codes

**Files to Check:**
- `backend/clients/compras_gov_client.py`
- `backend/clients/portal_compras_client.py`
- `backend/clients/licitar_client.py`

---

### 3.3 Filtering Compliance
- [ ] `filtrar_por_modalidade()` function accepts list of codes
- [ ] Function filters by modalidadeId, codigoModalidadeContratacao, or modalidade_id
- [ ] Empty list returns all records
- [ ] None returns all records
- [ ] Function handles string/int conversions
- [ ] Function handles None values in records

**Files to Check:**
- `backend/filter.py`

---

## Section 4: Frontend Implementation

### 4.1 Component Compliance
- [ ] `ModalidadeFilter` component exists
- [ ] `MODALIDADES` constant contains all 8 official modalities
- [ ] Each modalidade has: codigo, nome, descricao, popular (optional)
- [ ] Codes match backend: 1, 2, 3, 6, 7, 9, 10, 11
- [ ] No deprecated codes present (4, 5)
- [ ] Descriptions reference Lei 14.133 articles
- [ ] Popular flags set appropriately (Pregões e Dispensa)

**Files to Check:**
- `frontend/components/ModalidadeFilter.tsx`

---

### 4.2 UI/UX Compliance
- [ ] Multi-select with checkboxes
- [ ] Popular modalities always visible
- [ ] Collapsible section for other modalities
- [ ] "Todas" button selects all
- [ ] "Limpar" button deselects all
- [ ] Counter shows selected count
- [ ] Fully keyboard accessible
- [ ] ARIA attributes correct
- [ ] Screen reader friendly

---

## Section 5: Testing Compliance

### 5.1 Backend Testing
- [ ] Unit tests for each modalidade code (1-3, 6-7, 9-11)
- [ ] Tests verify deprecated codes are rejected (4, 5)
- [ ] Tests cover edge cases (empty, None, invalid)
- [ ] Tests cover alternative field names
- [ ] Integration tests with real API data
- [ ] All tests passing
- [ ] Code coverage > 90%

**Files to Check:**
- `backend/tests/test_modalidade_filter.py`
- `backend/tests/test_compras_gov_client.py`
- `backend/tests/test_portal_compras_client.py`
- `backend/tests/test_licitar_client.py`

---

### 5.2 Frontend Testing
- [ ] Component tests for ModalidadeFilter
- [ ] Tests for user interactions (select, clear, all)
- [ ] Tests for popular/other sections
- [ ] Accessibility tests (keyboard, screen reader)
- [ ] Visual regression tests
- [ ] All tests passing

**Files to Check:**
- `frontend/components/ModalidadeFilter.test.tsx`

---

### 5.3 Cross-Source Testing
- [ ] Tests verify consistency across all sources
- [ ] Tests verify modalidade normalization
- [ ] Tests verify deduplication
- [ ] Tests with real data from all sources

---

## Section 6: Documentation Compliance

### 6.1 Code Documentation
- [ ] Docstrings reference Lei 14.133 articles
- [ ] Comments explain modalidade mappings
- [ ] Schema documentation updated
- [ ] API documentation updated

---

### 6.2 User Documentation
- [ ] Help documentation updated with new modalidades
- [ ] Each modalidade has user-friendly description
- [ ] Lei 14.133 article references provided
- [ ] FAQ about changes created
- [ ] Migration guide for existing users

---

### 6.3 Developer Documentation
- [ ] README updated
- [ ] Tech stack documentation updated
- [ ] Architecture documentation updated
- [ ] Migration guide for developers

---

## Section 7: Data Migration Compliance

### 7.1 Legacy Data Analysis
- [ ] All records with code 4 identified
- [ ] All records with code 5 identified
- [ ] Usage statistics collected
- [ ] Migration impact assessed
- [ ] Migration strategy approved

---

### 7.2 Migration Execution
- [ ] Backup created before migration
- [ ] Migration script tested on staging
- [ ] Migration executed on production
- [ ] Migrated data validated
- [ ] Rollback plan ready
- [ ] No data loss

---

## Section 8: Performance & Quality

### 8.1 Performance
- [ ] API response time < 5s
- [ ] No performance regressions
- [ ] Pagination works correctly
- [ ] Rate limiting respected

---

### 8.2 Code Quality
- [ ] Linting passes (pylint, eslint)
- [ ] Type checking passes (mypy, TypeScript)
- [ ] No security vulnerabilities
- [ ] Code review completed

---

## Section 9: Deployment & Monitoring

### 9.1 Deployment
- [ ] Changes merged to main branch
- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] No deployment errors

---

### 9.2 Monitoring
- [ ] Error monitoring active
- [ ] Usage metrics tracked
- [ ] Performance metrics tracked
- [ ] Alerts configured

---

## Final Certification

### Compliance Summary

**Total Checks:** 150+
**Passed:** _____
**Failed:** _____
**Warnings:** _____

### Legal Compliance Statement

I certify that the implementation:
- ✅ Includes all 8 official modalities from Lei 14.133/2021
- ✅ Removes deprecated modalities from Lei 8.666/93
- ✅ References correct Lei articles
- ✅ Uses updated Decreto 12.807/2025 values
- ✅ Meets all legal requirements for government procurement systems

**Auditor Signature:** _________________________
**Date:** _____________
**Legal Standard:** Lei 14.133/2021
**Compliance Level:** ☐ Full  ☐ Partial  ☐ Non-Compliant

---

**Created:** 2026-02-10
**Squad:** lei-14133-modalidades-squad
**Agent:** @legal-compliance-auditor
