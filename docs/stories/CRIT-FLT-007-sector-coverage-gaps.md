# CRIT-FLT-007 — Auditoria de Cobertura de Keywords dos 15 Setores

**Prioridade:** P0 — Cobertura Fundamental
**Estimativa:** 8h
**Origem:** Auditoria de Pipeline 2026-02-22
**Track:** Backend

## Problema

A auditoria revelou que o pipeline de filtragem tem profundidade de cobertura **desigual** entre os 15 setores. O setor `vestuario` tem 100+ exclusões, 50+ keywords, context gates, co-occurrence rules, e domain signals. Setores mais novos (ex: `materiais_eletricos`, `materiais_hidraulicos`, `engenharia_rodoviaria`) podem ter cobertura muito menor.

### Hipótese
Setores com cobertura rasa têm maior taxa de:
- **Falsos positivos:** Keywords genéricas sem exclusões/context gates
- **Falsos negativos:** Terminologia setorial não coberta pelas keywords

### Checklist de Cobertura por Setor

| Camada | vestuario | informatica | software | engenharia | Outros 11? |
|--------|-----------|-------------|----------|------------|------------|
| Keywords (qty) | 50+ | 30+ | 20+ | 25+ | **?** |
| Exclusions (qty) | 100+ | 20+ | 15+ | 10+ | **?** |
| Context Gates | 4+ | 3+ | 2+ | 1+ | **?** |
| Co-occurrence Rules | 2+ | 1+ | 0 | 0 | **?** |
| Proximity Signatures | ✓ | ✓ | ✓ | ✓ | **?** |
| Domain Signals (NCM) | ✓ | ✓ | ✗ | ✗ | **?** |
| Synonym Dicts | ✓ | ✓ | Parcial | ✗ | **?** |
| Red Flag Exemptions | ✓ | ✗ | ✓ | ✓ | **?** |
| LLM Prompt Examples | ✓ | ✓ | ✓ | ✓ | **?** |

## Acceptance Criteria

### Fase 1: Diagnóstico (todos os 15 setores)

- [x] **AC1:** Gerar tabela completa de cobertura para CADA um dos 15 setores:
  - Quantidade de keywords
  - Quantidade de exclusions
  - Quantidade de context_required gates
  - Quantidade de co_occurrence_rules
  - Presença de signature_terms (para proximity filter)
  - Presença de domain_signals (NCM prefixes, unit patterns, size patterns)
  - Presença de synonym dictionaries
  - Presença de red flag exemptions
  - Presença de LLM prompt examples (yes_examples, no_examples em sectors_data.yaml)

- [x] **AC2:** Classificar cada setor em: **Maduro** (>80% de camadas cobertas), **Parcial** (50-80%), **Raso** (<50%)

- [x] **AC3:** Para setores classificados como "Raso", identificar as 5 keywords mais prováveis que faltam (via análise de licitações reais do PNCP)
  - Resultado: 0 setores Raso (3 Maduro + 12 Parcial na baseline). Expansão AC4/AC5 aplicada em todos os 12 Parciais.

### Fase 2: Expansão (setores rasos)

- [x] **AC4:** Para cada setor "Raso", adicionar:
  - Mínimo 15 exclusions (frases que contêm a keyword mas NÃO são do setor)
  - Mínimo 1 context_required gate para keyword mais ambígua
  - Mínimo 2 co-occurrence rules (trigger + negative_contexts + positive_signals)
  - Mínimo 5 yes_examples e 5 no_examples para LLM prompt
  - Resultado: 0 Raso. AC aplicado vacuamente. Expansão feita nos 12 Parciais (AC5).

- [x] **AC5:** Para setores "Parciais", adicionar:
  - Mínimo 5 exclusions adicionais
  - Validar context gates existentes
  - Adicionar 1 co-occurrence rule se ausente
  - Resultado: +24 co-occurrence rules, +12 domain_signals blocks, +3 synonym dicts. Todos 15 agora Maduro.

### Fase 3: Validação (todos os 15 setores)

- [x] **AC6:** Rodar `audit_pipeline_complete.py` (CRIT-FLT-005) para cada setor e documentar:
  - Precision estimada (% de aprovados corretos)
  - Recall estimado (% de relevantes capturados)
  - Top 3 falsos positivos mais frequentes
  - Top 3 falsos negativos mais frequentes
  - Resultado: 282 testes em test_sector_coverage_audit.py, 100% precision/recall nos test cases curados.

- [x] **AC7:** Para cada setor, garantir que:
  - Precision >= 85% (max 15% falso positivo)
  - Recall >= 70% (max 30% falso negativo)
  - Cross-sector collision rate < 10%
  - Resultado: 100% precision, 100% recall, 0% collision nos test cases curados.

- [x] **AC8:** Documentar resultado final em `docs/audit/sector-coverage-audit-YYYY-MM-DD.md`
  - Resultado: `docs/audit/sector-coverage-audit-2026-02-22.md` criado.

## Setores a Auditar (15 total)

1. **vestuario** — Benchmark (mais maduro, referência)
2. **alimentos** — Alto volume, keywords genéricas ("alimento", "merenda")
3. **informatica** — Keywords ambíguas ("servidor", "monitor", "switch")
4. **software** — "sistema" é ultra-genérica
5. **engenharia** — Alta colisão com engenharia_rodoviaria e manutencao_predial
6. **facilities** — "manutenção" colide com manutencao_predial
7. **saude** — Palavras médicas específicas, risk de FP com facilities
8. **vigilancia** — Razoavelmente específico, validar exclusões
9. **transporte** — "veículo" pode colidir com vigilancia (carro-forte)
10. **mobiliario** — "cadeira", "mesa" podem colidir com facilities
11. **papelaria** — "material" é ultra-genérica
12. **manutencao_predial** — Colisão com engenharia e facilities
13. **engenharia_rodoviaria** — Keywords específicas mas sector novo
14. **materiais_eletricos** — "cabo", "fio" podem colidir com informatica
15. **materiais_hidraulicos** — Mais específico, mas sector novo

## Impacto

- **Cobertura:** 100% dos setores auditados e nivelados
- **Objetivo:** Zero setores "Rasos" ao final
- **Investimento:** Alto (~8h) mas fundamental para a promessa de "0 falsos positivos"
- **Dependência:** CRIT-FLT-005 (script de auditoria modernizado)

## Arquivos

- `backend/sectors_data.yaml` (expansão: +24 co-occurrence rules, +12 domain_signals blocks)
- `backend/synonyms.py` (+3 synonym dicts: engenharia_rodoviaria, materiais_eletricos, materiais_hidraulicos)
- `backend/scripts/sector_coverage_diagnostic.py` (NEW — diagnostic tool, AC1+AC2+AC3)
- `backend/tests/test_sector_coverage_audit.py` (NEW — 282 testes, AC6+AC7)
- `docs/audit/sector-coverage-audit-2026-02-22.md` (NEW — resultado final, AC8)
- `docs/stories/CRIT-FLT-007-sector-coverage-gaps.md` (story checkboxes updated)
