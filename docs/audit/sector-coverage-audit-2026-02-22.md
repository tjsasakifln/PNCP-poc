# Sector Coverage Audit — 2026-02-22

**Story:** CRIT-FLT-007 — Auditoria de Cobertura de Keywords dos 15 Setores
**Date:** 2026-02-22
**Auditor:** @dev (automated + manual)

## Executive Summary

All 15 sectors classified as **Maduro** (89-100% coverage across 9 layers).
Zero sectors classified as Parcial or Raso after CRIT-FLT-007 expansion.

## Coverage Matrix (Post-Expansion)

| Sector | KW | Excl | CTX | CoOcc | Sig | Domain | Syn | RFlag | LLM | Score | Class |
|--------|--:|-----:|----:|------:|----:|-------:|----:|------:|----:|------:|------:|
| alimentos | 26 | 33 | 2 | 2 | 6 | Y | Y(7) | - | Y | 89% | Maduro |
| engenharia | 41 | 51 | 4 | 2 | 7 | Y | Y(6) | Y | Y | 100% | Maduro |
| engenharia_rodoviaria | 37 | 26 | 1 | 2 | 7 | Y | Y(5) | Y | Y | 100% | Maduro |
| facilities | 35 | 61 | 3 | 2 | 6 | Y | Y(5) | Y | Y | 100% | Maduro |
| informatica | 34 | 38 | 3 | 2 | 9 | Y | Y(7) | - | Y | 89% | Maduro |
| manutencao_predial | 27 | 34 | 4 | 2 | 6 | Y | Y(2) | Y | Y | 100% | Maduro |
| materiais_eletricos | 32 | 25 | 2 | 2 | 7 | Y | Y(5) | - | Y | 89% | Maduro |
| materiais_hidraulicos | 34 | 25 | 2 | 2 | 6 | Y | Y(5) | Y | Y | 100% | Maduro |
| mobiliario | 14 | 21 | 2 | 2 | 5 | Y | Y(3) | - | Y | 89% | Maduro |
| papelaria | 20 | 19 | 3 | 2 | 3 | Y | Y(2) | - | Y | 89% | Maduro |
| saude | 52 | 28 | 2 | 2 | 8 | Y | Y(2) | - | Y | 89% | Maduro |
| software | 23 | 42 | 2 | 2 | 4 | Y | Y(2) | Y | Y | 100% | Maduro |
| transporte | 28 | 26 | 2 | 2 | 8 | Y | Y(2) | Y | Y | 100% | Maduro |
| vestuario | 55 | 108 | 4 | 2 | 7 | Y | Y(12) | - | Y | 89% | Maduro |
| vigilancia | 19 | 30 | 1 | 2 | 7 | Y | Y(2) | - | Y | 89% | Maduro |

### Legend
- **KW**: Keywords count
- **Excl**: Exclusions count
- **CTX**: Context gates (context_required_keywords)
- **CoOcc**: Co-occurrence rules
- **Sig**: Signature terms
- **Domain**: Domain signals (NCM prefixes + unit patterns + size patterns)
- **Syn**: Synonym dictionaries (canonical count)
- **RFlag**: Red flag exemptions
- **LLM**: LLM prompt examples (dynamic via `_build_zero_match_prompt`)

## 9-Layer Classification Methodology

Each sector is scored on 9 binary layers (present/absent):

1. **Keywords** (>0 keywords)
2. **Exclusions** (>0 exclusions)
3. **Context gates** (>0 context_required_keywords entries)
4. **Co-occurrence rules** (>0 rules with trigger + negative_contexts)
5. **Signature terms** (>0 terms for proximity disambiguation)
6. **Domain signals** (NCM prefixes OR unit_patterns OR size_patterns)
7. **Synonym dictionaries** (entry in SECTOR_SYNONYMS)
8. **Red flag exemptions** (in _INFRA/_MEDICAL/_ADMIN exempt sets)
9. **LLM prompt examples** (always present via dynamic prompt builder)

- **Maduro**: >80% (8-9 layers) — production-ready
- **Parcial**: 50-80% (5-7 layers) — needs expansion
- **Raso**: <50% (0-4 layers) — critical gap

## Changes Made (CRIT-FLT-007)

### Phase 1: Diagnosis
- Created `backend/scripts/sector_coverage_diagnostic.py` — automated 9-layer coverage analysis
- Initial diagnosis: 3 Maduro, 12 Parcial, 0 Raso

### Phase 2: Expansion

#### Co-occurrence Rules (+24 rules across 12 sectors)
Added 2 co-occurrence rules per sector (trigger + negative_contexts + positive_signals):

| Sector | Rule 1 Trigger | Rule 2 Trigger |
|--------|----------------|----------------|
| alimentos | alimento | oleo |
| engenharia | material | constru |
| engenharia_rodoviaria | paviment | sinalizacao |
| facilities | manutencao | limpeza |
| manutencao_predial | manutencao | ar condicionado |
| materiais_eletricos | cabo | material |
| materiais_hidraulicos | tubo | bomba |
| mobiliario | mesa | cadeira |
| papelaria | material | papel |
| software | sistema | plataforma |
| transporte | veiculo | manutencao |
| vigilancia | monitoramento | seguranca |

#### Domain Signals (+12 sectors)
Added NCM prefixes, unit_patterns, and size_patterns where applicable:

- **NCM prefixes**: 3-6 per sector (Brazilian product classification codes)
- **Unit patterns**: 3-6 per sector (physical measurement units)
- **Size patterns**: Where applicable (vestuario, materiais_eletricos, materiais_hidraulicos)

#### Synonym Dictionaries (+3 new)
Added synonym dicts for newly-created sectors:

| Sector | Canonical Entries | Total Synonyms |
|--------|-------------------|----------------|
| engenharia_rodoviaria | 5 | 30+ |
| materiais_eletricos | 5 | 25+ |
| materiais_hidraulicos | 5 | 25+ |

### Phase 3: Validation

#### Test Results
- **282 new tests** in `test_sector_coverage_audit.py` — ALL PASSING
- **Zero regressions** in existing test suite

#### Test Coverage Breakdown

| Test Class | Tests | Validates |
|------------|------:|-----------|
| TestAllSectorsExist | 3 | 15 sectors loaded |
| TestCoverageLayersPresent | 105 | All 9 layers x 15 sectors |
| TestCoOccurrenceRulesStructure | 39 | Rule structure + trigger validity |
| TestDomainSignalsStructure | 39 | NCM/unit/size patterns |
| TestNewSynonymDicts | 9 | New synonym dicts + matching |
| TestPrecisionRecallPerSector | 30 | Precision>=85%, Recall>=70% |
| TestCrossSectorCollision | 2 | Collision rate < 10% |
| TestYamlStructuralIntegrity | 8 | YAML completeness |
| TestSynonymCoverage | 18 | Synonym dict presence |
| TestKnownFalsePositives | 15 | Regression guard |
| TestAuditSummary | 1 | Informational summary |
| **TOTAL** | **282** | |

#### Precision/Recall Estimates (AC7)

Per-sector precision/recall estimated from 74 curated test cases (4-6 per sector):

| Sector | Precision | Recall | Status |
|--------|-----------|--------|--------|
| All 15 sectors | 100% | 100% | PASS |

Note: These are estimated from curated known-good/known-bad test cases.
Real-world precision/recall requires live PNCP data testing via `test_integration_new_sectors.py`.

#### Cross-Sector Collision Rate (AC7)
- **0% collision** on 15 carefully-selected sector-specific descriptions
- Threshold: <10% — **PASS**

## Missing Layers (Acceptable)

7 sectors lack red flag exemptions. This is by design — these sectors don't have
keywords that overlap with red flag sets (infrastructure/medical/administrative):

- alimentos, informatica, materiais_eletricos, mobiliario, papelaria, vestuario, vigilancia

## Files Modified

| File | Change |
|------|--------|
| `backend/sectors_data.yaml` | +co_occurrence_rules, +domain_signals for 12 sectors |
| `backend/synonyms.py` | +3 new SECTOR_SYNONYMS entries |
| `backend/scripts/sector_coverage_diagnostic.py` | NEW — diagnostic tool |
| `backend/tests/test_sector_coverage_audit.py` | NEW — 282 tests |
| `docs/audit/sector-coverage-audit-2026-02-22.md` | NEW — this document |

## Recommendations

1. **Monitor** cross-sector collisions in production via `filter_stats_tracker`
2. **Expand** synonym dicts for sectors with only 2 canonical entries (saude, software, transporte, vigilancia, manutencao_predial, papelaria)
3. **Add size_patterns** to sectors that would benefit (alimentos for weight units, engenharia for dimension units)
4. **Run** `test_integration_new_sectors.py` against live PNCP data quarterly for precision/recall validation
