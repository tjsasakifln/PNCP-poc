# Lei 14.133 Modalidades Squad

**Version:** 1.0.0
**Status:** Active
**Compliance:** Lei 14.133/2021 + Decreto 12.807/2025

## Overview

This squad implements full support for all procurement modalities defined in **Lei 14.133/2021** (Brazilian Public Procurement Law) across all data sources in the SmartLic system.

### Legal Context

- **Lei 14.133/2021**: Enacted April 1, 2021, fully enforced January 1, 2024
- **Revokes**: Lei 8.666/93, Lei 10.520/02
- **Latest Updates**: Decreto 12.807/2025 (updated monetary values)

## Official Modalities (Lei 14.133/2021)

| Code | Modalidade | Article | Status | Description |
|------|------------|---------|--------|-------------|
| 1 | Pregão Eletrônico | Art. 6º, XLIII | ✅ Implemented | Mandatory for common goods/services |
| 2 | Pregão Presencial | Art. 6º, XLIII | ✅ Implemented | In-person bidding (when justified) |
| 3 | Concorrência | Art. 6º, XLII | ⚠️ Partial | For special goods/services and engineering works |
| 11 | Concurso | Art. 6º, XLIV | ❌ Not Implemented | Selection of technical/artistic work |
| 9 | Leilão | Art. 6º, XLV | ⚠️ Partial | Auction for asset disposal |
| 6 | Dispensa de Licitação | Art. 75 | ✅ Implemented | Direct contracting (competition waived) |
| 7 | Inexigibilidade | Art. 74 | ⚠️ Partial | Direct contracting (competition impossible) |
| 10 | Diálogo Competitivo | Art. 6º, XLVI | ⚠️ Partial | For innovative solutions |

## Deprecated Modalities (Lei 8.666/93)

| Code | Modalidade | Replacement | Action |
|------|------------|-------------|--------|
| 4 | Tomada de Preços | Concorrência/Pregão | ❌ Remove |
| 5 | Convite | Pregão/Dispensa | ❌ Remove |
| 8 | Credenciamento | (Not a modality) | ⚠️ Review |

## Objectives

1. **Backend Implementation**
   - ✅ Add all official modalities to UnifiedProcurement schema
   - ✅ Implement modalidade support in all source adapters (ComprasGov, Portal Compras, Licitar)
   - ✅ Add validation for new modalidade codes (1-3, 6-7, 9-11)
   - ✅ Remove/deprecate old modalities (4, 5)

2. **Frontend Implementation**
   - ✅ Update ModalidadeFilter component with all official modalities
   - ✅ Remove deprecated modalities from UI
   - ✅ Update descriptions per Lei 14.133 articles
   - ✅ Maintain popular/unpopular categorization

3. **Testing & Validation**
   - ✅ Comprehensive testing across all modalities
   - ✅ Legal compliance validation
   - ✅ Cross-source consistency checks
   - ✅ Edge case and error scenario testing

4. **Data Migration**
   - ✅ Analyze existing data with legacy codes
   - ✅ Create migration strategy for deprecated modalities
   - ✅ Validate migrated data

5. **Documentation**
   - ✅ Update user-facing documentation
   - ✅ Add Lei 14.133 article references
   - ✅ Create FAQ for changes
   - ✅ Provide migration guide

## Squad Members (Agents)

### 🔧 Backend Engineer
**Role:** Implements backend changes for modalidade support across all source adapters
**Commands:** `*update-compras-gov-adapter`, `*update-portal-compras-adapter`, `*update-licitar-adapter`, `*update-unified-schemas`, `*add-modalidade-validation`

### 🎨 Frontend Engineer
**Role:** Updates frontend ModalidadeFilter component and related UI
**Commands:** `*update-modalidade-filter-component`, `*update-modalidade-constants`, `*update-frontend-types`, `*remove-legacy-modalidades`

### ✅ QA Engineer
**Role:** Tests modalidade filtering across all sources and validates compliance
**Commands:** `*test-backend-filters`, `*test-frontend-filters`, `*test-source-adapters`, `*validate-lei-compliance`, `*test-edge-cases`

### ⚖️ Legal Compliance Auditor
**Role:** Validates implementation against Lei 14.133/2021 requirements
**Commands:** `*audit-modalidades`, `*verify-artigo-references`, `*check-deprecated-removal`, `*validate-user-documentation`

### 📊 Data Migration Specialist
**Role:** Handles migration of existing data with old modalidade codes
**Commands:** `*analyze-existing-data`, `*create-migration-script`, `*map-legacy-to-new`, `*validate-migration`

## Implementation Phases

### Phase 1: Research & Planning (1 day)
- ✅ Research Lei 14.133/2021 official modalities
- ✅ Audit current implementation
- ✅ Gap analysis

### Phase 2: Backend Core Updates (2 days)
- Update unified schema with new modalities
- Add validation for new codes
- Remove deprecated enum values

### Phase 3: Source Adapter Implementation (3 days - parallel)
- ComprasGov adapter implementation
- Portal Compras adapter implementation
- Licitar adapter implementation

### Phase 4: Frontend Updates (1 day)
- Update ModalidadeFilter UI component
- Update TypeScript types
- Remove deprecated options

### Phase 5: Testing & Validation (2 days)
- Backend filter testing
- Frontend component testing
- Cross-source consistency testing
- Legal compliance validation

### Phase 6: Data Migration & Documentation (1 day)
- Analyze legacy data usage
- Create and execute migration scripts
- Update user documentation

**Total Estimated Duration:** 6 days
**Complexity:** High
**Risk Level:** Medium

## Key Files

### Backend
- `backend/unified_schemas/unified.py` - UnifiedProcurement schema
- `backend/clients/base.py` - SourceAdapter interface
- `backend/clients/compras_gov_client.py` - ComprasGov adapter
- `backend/clients/portal_compras_client.py` - Portal Compras adapter
- `backend/clients/licitar_client.py` - Licitar adapter
- `backend/filter.py` - Modalidade filtering logic
- `backend/schemas.py` - BuscaRequest schema with modalidade validation

### Frontend
- `frontend/components/ModalidadeFilter.tsx` - UI component
- `frontend/components/ModalidadeFilter.test.tsx` - Component tests

### Tests
- `backend/tests/test_modalidade_filter.py` - Backend filter tests
- `backend/tests/test_compras_gov_client.py` - ComprasGov adapter tests

## Breaking Changes

⚠️ **Warning:** This implementation includes breaking changes:

1. **Removed Modalities**
   - Code 4 (Tomada de Preços) - deprecated by Lei 14.133
   - Code 5 (Convite) - deprecated by Lei 14.133

2. **New Modalidade**
   - Code 11 (Concurso) - new modality from Lei 14.133

3. **API Changes**
   - `BuscaRequest.modalidades` now accepts: 1-3, 6-7, 9-11
   - Rejects codes 4, 5 with validation error
   - Frontend filter hides deprecated options

## Backward Compatibility Strategy

- **Deprecation Warnings:** Codes 4, 5 return warning messages
- **Auto-Mapping:** Legacy codes auto-map to equivalent new modalities
- **Sunset Period:** 6-month grace period for full migration
- **Database Scripts:** Migration scripts provided for existing data

## Legal References

### Lei 14.133/2021 Articles

- **Art. 6º, XLII** - Concorrência
- **Art. 6º, XLIII** - Pregão (Eletrônico e Presencial)
- **Art. 6º, XLIV** - Concurso
- **Art. 6º, XLV** - Leilão
- **Art. 6º, XLVI** - Diálogo Competitivo
- **Art. 74** - Inexigibilidade
- **Art. 75** - Dispensa de Licitação

### Decreto 12.807/2025 Values

- **Obras/Serviços de Engenharia:** < R$ 125.451,15
- **Outros Serviços/Compras:** < R$ 62.725,59
- **Consórcios/Agências Executivas:** 2x the above values

## Usage

### Activate Squad

```bash
# Activate squad-creator agent
@squad-creator

# Create squad from design blueprint
*create-squad lei-14133-modalidades-squad --from-design ./squads/.designs/lei-14133-modalidades-squad-design.yaml
```

### Run Workflow

```bash
# Run full implementation workflow
@aios-master
*execute-workflow lei-14133-modalidades-squad/full-implementation-workflow
```

### Individual Tasks

```bash
# Research phase
@legal-compliance-auditor
*research-lei-14133-modalidades

# Backend implementation
@backend-engineer
*update-unified-schema-modalidades
*implement-compras-gov-modalidades

# Frontend implementation
@frontend-engineer
*update-modalidade-filter-ui

# Testing
@qa-engineer
*test-modalidade-filtering-backend
*validate-lei-compliance

# Data migration
@data-migration-specialist
*analyze-legacy-data
*migrate-legacy-modalidades
```

## Success Criteria

✅ All 8 official modalities from Lei 14.133/2021 implemented
✅ Deprecated modalities (4, 5) removed or marked as legacy
✅ All source adapters support new modalities
✅ Frontend component updated and tested
✅ Legal compliance validated against Lei 14.133
✅ Existing data migrated successfully
✅ User documentation updated
✅ All tests passing (unit + integration)
✅ Performance benchmarks met
✅ Zero regressions in existing functionality

## Support & References

- **Lei 14.133/2021:** https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm
- **Decreto 12.807/2025:** https://www.in.gov.br/en/web/dou/-/decreto-n-12.807-de-29-de-dezembro-de-2025
- **TCU Guidelines:** https://licitacoesecontratos.tcu.gov.br/
- **PNCP Portal:** https://www.gov.br/pncp/

## License

MIT

---

**Created:** 2026-02-10
**Squad Creator:** Craft (squad-creator agent)
**Legal Standard:** Lei 14.133/2021
**Compliance Required:** Yes
