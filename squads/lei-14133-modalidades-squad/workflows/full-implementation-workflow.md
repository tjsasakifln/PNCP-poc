---
workflow: Full Lei 14.133 Modalidades Implementation
responsavel: "@aios-master"
atomic_layer: workflow
duration: "6 days"
complexity: high
---

# Full Implementation Workflow - Lei 14.133 Modalidades

**Objective:** Implement complete support for all procurement modalities defined in Lei 14.133/2021 across the entire SmartLic system.

**Duration:** 6 days
**Complexity:** High
**Risk:** Medium
**Legal Compliance:** Required

---

## Phase 1: Research & Planning (Day 1)

### 1.1 Legal Research
**Agent:** @legal-compliance-auditor
**Task:** `*research-lei-14133-modalidades`

**Steps:**
1. Review Lei 14.133/2021 full text
2. Identify all 8 official modalities with article references
3. Review Decreto 12.807/2025 for updated values
4. Document deprecated modalities from Lei 8.666/93
5. Create compliance requirements checklist

**Deliverables:**
- ✅ Complete list of official modalities
- ✅ Article references for each modality
- ✅ Deprecation list
- ✅ Legal validation criteria

**Checkpoints:**
- [ ] All 8 modalities identified
- [ ] Article references documented
- [ ] Decree values noted (R$ 125.451,15 and R$ 62.725,59)
- [ ] Deprecated modalities listed (Tomada de Preços, Convite)

---

### 1.2 Current Implementation Audit
**Agent:** @qa-engineer
**Task:** `*audit-current-implementation`

**Steps:**
1. Analyze current backend code (clients/*.py, unified_schemas/)
2. Analyze current frontend code (ModalidadeFilter.tsx)
3. Review test files (test_modalidade_filter.py)
4. Identify gaps between current and required state
5. Assess implementation risks

**Deliverables:**
- ✅ Gap analysis report
- ✅ Implemented vs missing modalities list
- ✅ Risk assessment
- ✅ Implementation roadmap

**Checkpoints:**
- [ ] All source adapters analyzed
- [ ] Frontend component analyzed
- [ ] Gaps documented
- [ ] Risks identified and mitigated

---

## Phase 2: Backend Core Updates (Days 2-3)

### 2.1 Update Unified Schema
**Agent:** @backend-engineer
**Task:** `*update-unified-schema-modalidades`

**Steps:**
1. Update `UnifiedProcurement` schema in `unified.py`
2. Create/update `ModalidadeContratacao` enum with codes 1-3, 6-7, 9-11
3. Add validation for modalidade codes
4. Remove deprecated codes 4, 5
5. Update docstrings with Lei article references

**Files Modified:**
- `backend/unified_schemas/unified.py`
- `backend/schemas.py` (BuscaRequest)

**Deliverables:**
- ✅ Updated UnifiedProcurement schema
- ✅ Modalidade enum with all official values
- ✅ Validation rules
- ✅ Migration guide

**Checkpoints:**
- [ ] Enum includes codes: 1, 2, 3, 6, 7, 9, 10, 11
- [ ] Codes 4, 5 removed or deprecated
- [ ] Validation rejects invalid codes
- [ ] Schema validation tests pass

---

### 2.2 Add Backend Validation
**Agent:** @backend-engineer
**Task:** `*add-modalidade-backend-validation`

**Steps:**
1. Update `BuscaRequest` schema validation
2. Add custom validator for modalidade codes
3. Create clear error messages for deprecated codes
4. Add validation tests

**Files Modified:**
- `backend/schemas.py`
- `backend/tests/test_modalidade_filter.py`

**Deliverables:**
- ✅ Updated validation rules
- ✅ Error messages
- ✅ Validation tests

**Checkpoints:**
- [ ] Valid codes accepted: 1-3, 6-7, 9-11
- [ ] Invalid codes rejected: 4, 5, 0, 11+
- [ ] Clear error messages
- [ ] Tests cover all edge cases

---

## Phase 3: Source Adapter Implementation (Days 3-5 - Parallel)

### 3.1 ComprasGov Adapter
**Agent:** @backend-engineer
**Task:** `*implement-compras-gov-modalidades`

**Steps:**
1. Review ComprasGov API modalidade field mapping
2. Update `normalize()` method in `ComprasGovAdapter`
3. Add modalidade name normalization logic
4. Handle variations in API responses
5. Add unit tests
6. Add integration tests with real API

**Files Modified:**
- `backend/clients/compras_gov_client.py`
- `backend/tests/test_compras_gov_client.py`

**Deliverables:**
- ✅ Updated normalize() method
- ✅ Modalidade mapping logic
- ✅ Unit tests
- ✅ Integration tests

**Checkpoints:**
- [ ] All 8 modalities mapped correctly
- [ ] Name variations handled
- [ ] Tests pass with real API data
- [ ] No regressions in existing functionality

---

### 3.2 Portal Compras Adapter
**Agent:** @backend-engineer
**Task:** `*implement-portal-compras-modalidades`

**Steps:**
1. Review Portal Compras API modalidade field mapping
2. Update `normalize()` method in `PortalComprasAdapter`
3. Add modalidade name normalization logic
4. Handle API-specific variations
5. Add tests

**Files Modified:**
- `backend/clients/portal_compras_client.py`
- `backend/tests/test_portal_compras_client.py`

**Deliverables:**
- ✅ Updated normalize() method
- ✅ Modalidade mapping logic
- ✅ Tests

**Checkpoints:**
- [ ] All modalities mapped
- [ ] Tests pass
- [ ] No regressions

---

### 3.3 Licitar Adapter
**Agent:** @backend-engineer
**Task:** `*implement-licitar-modalidades`

**Steps:**
1. Review Licitar API modalidade field mapping
2. Update `normalize()` method in `LicitarAdapter`
3. Add modalidade name normalization logic
4. Handle API-specific variations
5. Add tests

**Files Modified:**
- `backend/clients/licitar_client.py`
- `backend/tests/test_licitar_client.py`

**Deliverables:**
- ✅ Updated normalize() method
- ✅ Modalidade mapping logic
- ✅ Tests

**Checkpoints:**
- [ ] All modalities mapped
- [ ] Tests pass
- [ ] No regressions

---

## Phase 4: Frontend Updates (Day 4)

### 4.1 Update ModalidadeFilter Component
**Agent:** @frontend-engineer
**Task:** `*update-modalidade-filter-ui`

**Steps:**
1. Update `MODALIDADES` constant with all official modalities
2. Remove deprecated modalities (codes 4, 5)
3. Add new modalidade (Concurso - code 11)
4. Update descriptions with Lei 14.133 article references
5. Maintain popular/unpopular categorization
6. Update component tests

**Files Modified:**
- `frontend/components/ModalidadeFilter.tsx`
- `frontend/components/ModalidadeFilter.test.tsx`

**Deliverables:**
- ✅ Updated MODALIDADES constant
- ✅ Removed deprecated modalities
- ✅ Added missing modalities
- ✅ Updated descriptions
- ✅ Component tests updated

**Checkpoints:**
- [ ] All 8 official modalities present
- [ ] Deprecated modalities removed
- [ ] Descriptions reference Lei articles
- [ ] Popular flags correctly set
- [ ] Component tests pass
- [ ] Accessibility maintained

---

### 4.2 Update Frontend Types
**Agent:** @frontend-engineer
**Task:** `*update-frontend-types`

**Steps:**
1. Update TypeScript interfaces for Modalidade
2. Ensure type safety for new codes
3. Remove deprecated type definitions
4. Update related components

**Files Modified:**
- `frontend/types/modalidade.ts` (if exists)
- `frontend/components/ModalidadeFilter.tsx`

**Deliverables:**
- ✅ Updated Modalidade interface
- ✅ Type safety for new codes
- ✅ Removed deprecated types

**Checkpoints:**
- [ ] TypeScript compilation succeeds
- [ ] No type errors
- [ ] IDE autocomplete works

---

## Phase 5: Testing & Validation (Days 5-6)

### 5.1 Backend Filter Testing
**Agent:** @qa-engineer
**Task:** `*test-modalidade-filtering-backend`

**Steps:**
1. Update `test_modalidade_filter.py` with all new codes
2. Add tests for each modalidade (1-3, 6-7, 9-11)
3. Test deprecated code rejection (4, 5)
4. Test edge cases (empty list, None, invalid codes)
5. Run full test suite

**Files Modified:**
- `backend/tests/test_modalidade_filter.py`

**Deliverables:**
- ✅ Comprehensive test suite
- ✅ Tests for codes 1-11
- ✅ Edge case tests
- ✅ Integration tests with real data

**Checkpoints:**
- [ ] All tests pass
- [ ] Code coverage > 90%
- [ ] Edge cases covered
- [ ] No flaky tests

---

### 5.2 Frontend Component Testing
**Agent:** @qa-engineer
**Task:** `*test-modalidade-filtering-frontend`

**Steps:**
1. Write component tests for ModalidadeFilter
2. Test user interactions (select, deselect, clear, all)
3. Test popular/other sections
4. Test accessibility (keyboard nav, screen readers)
5. Run visual regression tests

**Files Modified:**
- `frontend/components/ModalidadeFilter.test.tsx`

**Deliverables:**
- ✅ Component tests
- ✅ Integration tests
- ✅ Accessibility tests
- ✅ Visual regression tests

**Checkpoints:**
- [ ] All component tests pass
- [ ] Keyboard navigation works
- [ ] ARIA attributes correct
- [ ] Visual regression tests pass

---

### 5.3 Cross-Source Consistency Testing
**Agent:** @qa-engineer
**Task:** `*test-cross-source-consistency`

**Steps:**
1. Fetch sample data from all sources
2. Verify modalidade normalization consistency
3. Test cross-source deduplication
4. Validate modalidade filtering across sources

**Deliverables:**
- ✅ Consistency validation report
- ✅ Modalidade normalization verification
- ✅ Cross-source mapping validation

**Checkpoints:**
- [ ] All sources return normalized modalidade names
- [ ] Deduplication works correctly
- [ ] Filtering consistent across sources

---

### 5.4 Legal Compliance Validation
**Agent:** @legal-compliance-auditor
**Task:** `*validate-lei-compliance`

**Steps:**
1. Review implementation against Lei 14.133/2021
2. Verify all 8 official modalities present
3. Confirm deprecated modalities removed
4. Validate article references
5. Sign off on compliance

**Deliverables:**
- ✅ Compliance certification
- ✅ Article-by-article validation
- ✅ Non-compliance issues (if any)
- ✅ Remediation recommendations

**Checkpoints:**
- [ ] All 8 modalities implemented per Lei
- [ ] Deprecated modalities removed
- [ ] Article references accurate
- [ ] No legal compliance issues

---

## Phase 6: Data Migration & Documentation (Day 6)

### 6.1 Analyze Legacy Data
**Agent:** @data-migration-specialist
**Task:** `*analyze-legacy-data`

**Steps:**
1. Query database for records with codes 4, 5
2. Analyze usage statistics
3. Assess migration impact
4. Create migration strategy

**Deliverables:**
- ✅ Usage statistics per modalidade code
- ✅ Migration impact assessment
- ✅ Data quality report

**Checkpoints:**
- [ ] All legacy data identified
- [ ] Impact assessed
- [ ] Migration strategy approved

---

### 6.2 Migrate Legacy Modalidades
**Agent:** @data-migration-specialist
**Task:** `*migrate-legacy-modalidades`

**Steps:**
1. Create migration script for codes 4 → 3 (Tomada de Preços → Concorrência)
2. Create migration script for codes 5 → 6 (Convite → Dispensa)
3. Test migration on staging data
4. Execute migration on production
5. Validate migrated data

**Deliverables:**
- ✅ Migration script
- ✅ Backup strategy
- ✅ Rollback plan
- ✅ Migration validation

**Checkpoints:**
- [ ] Migration script tested
- [ ] Backup created
- [ ] Migration executed
- [ ] Data validated

---

### 6.3 Update User Documentation
**Agent:** @frontend-engineer
**Task:** `*update-user-documentation`

**Steps:**
1. Update help documentation with new modalidades
2. Add Lei 14.133 article references
3. Create FAQ about changes
4. Write migration guide for existing users

**Deliverables:**
- ✅ Updated help documentation
- ✅ Modalidade descriptions for users
- ✅ FAQ about changes
- ✅ Migration guide

**Checkpoints:**
- [ ] Documentation updated
- [ ] FAQ comprehensive
- [ ] Migration guide clear
- [ ] Legal references accurate

---

## Workflow Completion Criteria

### Must Have (P0)
- ✅ All 8 official modalities from Lei 14.133/2021 implemented
- ✅ Deprecated modalities (4, 5) removed
- ✅ All source adapters support new modalities
- ✅ Frontend component updated
- ✅ Legal compliance validated
- ✅ All tests passing

### Should Have (P1)
- ✅ Existing data migrated
- ✅ User documentation updated
- ✅ Performance benchmarks met
- ✅ Zero regressions

### Nice to Have (P2)
- ✅ Visual regression tests
- ✅ Load testing
- ✅ Monitoring dashboards

---

## Rollback Plan

If critical issues are discovered:

1. **Immediate Actions:**
   - Revert frontend changes (git revert)
   - Disable new modalidade codes in backend
   - Restore previous MODALIDADES constant

2. **Data Recovery:**
   - Restore database from backup
   - Re-run legacy modalidade codes

3. **Communication:**
   - Notify users of rollback
   - Document issues
   - Plan remediation

---

## Success Metrics

### Technical Metrics
- **Test Coverage:** > 90%
- **API Response Time:** < 5s
- **Zero Regressions:** All existing tests pass
- **Code Quality:** pylint score > 9.0

### Legal Metrics
- **Compliance:** 100% (all 8 modalities)
- **Article References:** 100% accurate
- **Deprecated Removal:** 100% (codes 4, 5)

### User Metrics
- **Filter Usage:** Track modalidade filter usage
- **Error Rate:** < 1% validation errors
- **User Satisfaction:** Collect feedback

---

## Next Steps After Completion

1. **Deploy to Production**
   - Merge to main branch
   - Deploy backend changes
   - Deploy frontend changes
   - Monitor for issues

2. **User Communication**
   - Announce new modalidades
   - Share migration guide
   - Provide support documentation

3. **Monitoring**
   - Set up alerts for modalidade-related errors
   - Track usage metrics
   - Monitor API performance

4. **Future Enhancements**
   - Add modalidade-specific help text
   - Implement advanced filtering
   - Add modalidade analytics

---

**Workflow Owner:** @aios-master
**Legal Compliance:** @legal-compliance-auditor
**Created:** 2026-02-10
**Squad:** lei-14133-modalidades-squad
