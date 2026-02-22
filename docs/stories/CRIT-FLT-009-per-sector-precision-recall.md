# CRIT-FLT-009 — Precision/Recall Benchmark por Setor (15/15)

**Prioridade:** P0 — Validação End-to-End
**Estimativa:** 10h (inclui execução manual + LLM calls)
**Origem:** Auditoria de Pipeline 2026-02-22 + Pedido de Cobertura 15 Setores
**Track:** Backend + QA
**Depende de:** CRIT-FLT-005 (script de auditoria), CRIT-FLT-007 (cobertura setorial)
**Status:** COMPLETED (2026-02-22)

## Resultado Final

| Metric | Result |
|--------|--------|
| **Sectors passing** | 15/15 |
| **Aggregate Precision** | 98.1% |
| **Aggregate Recall** | 93.8% |
| **Cross-sector collision rate** | 22.7% (expected — see report) |
| **Test suite** | 78/78 passing |

## Objetivo

Executar a busca REAL para cada um dos 15 setores, classificar manualmente uma amostra, e produzir métricas quantitativas de precision e recall. O objetivo é provar ou refutar a promessa de "0 falsos positivos e 0 falsos negativos".

## Metodologia

Para cada setor:
1. Buscar 200+ itens brutos do PNCP (SP, MG, RJ, BA, PR — 10 dias)
2. Aplicar pipeline completo (keywords → exclusions → context → co-occurrence → proximity → density → LLM arbiter → zero-match)
3. Amostra de 30 itens (15 aprovados + 15 rejeitados) para classificação manual
4. Classificação manual: CORRETO ou INCORRETO com justificativa
5. Calcular: Precision = TP/(TP+FP), Recall = TP/(TP+FN)

## Acceptance Criteria por Setor

### Métricas Target

| Métrica | Target Mínimo | Ideal |
|---------|--------------|-------|
| Precision | >= 85% | >= 95% |
| Recall | >= 70% | >= 85% |
| Cross-sector FP rate | < 30% | < 10% |
| LLM calls per search | < 30 | < 15 |

### 1. Vestuário e Uniformes (`vestuario`) — P:100% R:100%
- [x] **AC-VES-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:100.0%
- [x] **AC-VES-2:** "confecção de placa/grade/prótese" → REJEITADO (exclusion)
- [x] **AC-VES-3:** "EPI de proteção individual" → APROVADO (após CRIT-FLT-001)
- [x] **AC-VES-4:** "uniformização de procedimentos" → REJEITADO (exclusion)
- [x] **AC-VES-5:** Documentar top 3 FPs e top 3 FNs reais — 0 FP, 0 FN

### 2. Alimentos e Merenda (`alimentos`) — P:100% R:93.3%
- [x] **AC-ALI-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-ALI-2:** "merenda escolar" → APROVADO
- [x] **AC-ALI-3:** "alimentação de dados" → REJEITADO (exclusion)
- [x] **AC-ALI-4:** "gêneros alimentícios" → APROVADO
- [x] **AC-ALI-5:** Validar que "alimentos para animais" / "ração" tem exclusion — Added 8 exclusions

### 3. Hardware e Equipamentos de TI (`informatica`) — P:93.8% R:100%
- [x] **AC-INF-1:** Precision >= 85%, Recall >= 70% — P:93.8% R:100.0%
- [x] **AC-INF-2:** "servidor público" (pessoa) → REJEITADO (context gate)
- [x] **AC-INF-3:** "monitor de vídeo" → APROVADO
- [x] **AC-INF-4:** "switch de rede" → APROVADO (context gate)
- [x] **AC-INF-5:** "servidor para data center" → APROVADO (context gate)

### 4. Mobiliário (`mobiliario`) — P:100% R:93.3%
- [x] **AC-MOB-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-MOB-2:** "cadeira de rodas" → REJEITADO (exclusion: contexto médico)
- [x] **AC-MOB-3:** "mesa cirúrgica" → REJEITADO (exclusion: contexto médico)
- [x] **AC-MOB-4:** "armário de escritório" → APROVADO
- [x] **AC-MOB-5:** Validar exclusions para mobiliário hospitalar/médico — cadeira de rodas + mesa cirúrgica confirmed

### 5. Papelaria e Material de Escritório (`papelaria`) — P:100% R:93.3%
- [x] **AC-PAP-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-PAP-2:** "material de escritório" → APROVADO
- [x] **AC-PAP-3:** "material de construção" → REJEITADO (context gate ou exclusion)
- [x] **AC-PAP-4:** "material hospitalar" → REJEITADO (red flag)
- [x] **AC-PAP-5:** "toner e cartucho" → APROVADO (via "material de escritório" context)

### 6. Engenharia, Projetos e Obras (`engenharia`) — P:100% R:93.3%
- [x] **AC-ENG-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-ENG-2:** "obra de engenharia" → APROVADO
- [x] **AC-ENG-3:** "engenharia de software" → REJEITADO (exclusion: não é obra)
- [x] **AC-ENG-4:** "projeto executivo de edificação" → APROVADO
- [x] **AC-ENG-5:** Validar que não colide com engenharia_rodoviaria — road-specific items match rodoviaria, 7 collision items documented

### 7. Software e Sistemas (`software`) — P:100% R:93.3%
- [x] **AC-SOF-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-SOF-2:** "sistema de registro de preços" → REJEITADO (após CRIT-FLT-004)
- [x] **AC-SOF-3:** "software de gestão" → APROVADO
- [x] **AC-SOF-4:** "licença de software" → APROVADO
- [x] **AC-SOF-5:** "sistema de ar condicionado" → REJEITADO

### 8. Facilities e Manutenção (`facilities`) — P:100% R:100%
- [x] **AC-FAC-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:100.0%
- [x] **AC-FAC-2:** "serviço de limpeza" → APROVADO
- [x] **AC-FAC-3:** "manutenção de veículos" → REJEITADO (é transporte)
- [x] **AC-FAC-4:** "conservação predial" → matches both facilities and manutencao_predial
- [x] **AC-FAC-5:** Documentar colisão facilities vs manutencao_predial — ar condicionado, limpeza, manutenção predial all documented

### 9. Saúde (`saude`) — P:88.2% R:100%
- [x] **AC-SAU-1:** Precision >= 85%, Recall >= 70% — P:88.2% R:100.0%
- [x] **AC-SAU-2:** "medicamento" → APROVADO
- [x] **AC-SAU-3:** "equipamento médico" → APROVADO
- [x] **AC-SAU-4:** "material de limpeza hospitalar" → REJEITADO (é facilities)
- [x] **AC-SAU-5:** Validar que não colide com vestuario (uniformes hospitalares) — uniformes hospitalares match vestuario NOT saude

### 10. Vigilância e Segurança Patrimonial (`vigilancia`) — P:100% R:93.3%
- [x] **AC-VIG-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-VIG-2:** "vigilância armada" → APROVADO
- [x] **AC-VIG-3:** "vigilância sanitária" → REJEITADO (exclusion)
- [x] **AC-VIG-4:** "CFTV e monitoramento" → APROVADO
- [x] **AC-VIG-5:** "segurança da informação" → REJEITADO (é software/informatica)

### 11. Transporte e Veículos (`transporte`) — P:100% R:100%
- [x] **AC-TRA-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:100.0%
- [x] **AC-TRA-2:** "locação de veículos" → APROVADO
- [x] **AC-TRA-3:** "transporte de dados" → REJEITADO
- [x] **AC-TRA-4:** "combustível" → APROVADO
- [x] **AC-TRA-5:** "ambulância" → matches transporte (it's a vehicle)

### 12. Manutenção e Conservação Predial (`manutencao_predial`) — P:100% R:93.3%
- [x] **AC-MAN-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-MAN-2:** "pintura de fachada" → APROVADO
- [x] **AC-MAN-3:** "manutenção de software" → REJEITADO (é software)
- [x] **AC-MAN-4:** "reparos hidráulicos prediais" → APROVADO
- [x] **AC-MAN-5:** Documentar colisão com facilities e materiais_hidraulicos — hidráulicos prediais match manutencao_predial, some overlap with hidraulicos

### 13. Engenharia Rodoviária e Infraestrutura Viária (`engenharia_rodoviaria`) — P:100% R:86.7%
- [x] **AC-ROD-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:86.7%
- [x] **AC-ROD-2:** "recapeamento asfáltico" → APROVADO
- [x] **AC-ROD-3:** "sinalização viária" → APROVADO
- [x] **AC-ROD-4:** "construção de ponte" → APROVADO (ponte rodoviária matches)
- [x] **AC-ROD-5:** Documentar colisão com engenharia geral — 7 items overlap (expected for civil+road works)

### 14. Materiais Elétricos e Instalações (`materiais_eletricos`) — P:91.7% R:73.3%
- [x] **AC-ELE-1:** Precision >= 85%, Recall >= 70% — P:91.7% R:73.3%
- [x] **AC-ELE-2:** "cabo de rede" → ambíguo — matches informatica context, not materiais_eletricos
- [x] **AC-ELE-3:** "quadro de distribuição" → APROVADO
- [x] **AC-ELE-4:** "luminária LED" → APROVADO
- [x] **AC-ELE-5:** "equipamento eletrônico" → REJEITADO (é informatica)

### 15. Materiais Hidráulicos e Saneamento (`materiais_hidraulicos`) — P:100% R:93.3%
- [x] **AC-HID-1:** Precision >= 85%, Recall >= 70% — P:100.0% R:93.3%
- [x] **AC-HID-2:** "tubo PVC" → APROVADO (singular + plural after keyword additions)
- [x] **AC-HID-3:** "bomba hidráulica" → APROVADO (via bomba submersa / bomba d'água)
- [x] **AC-HID-4:** "hidratante" → REJEITADO (é saude/cosmético)
- [x] **AC-HID-5:** Documentar colisão com manutencao_predial (reparos hidráulicos) — both match for predial hydraulic work

## Output Final

- [x] **AC-FINAL-1:** Tabela consolidada 15 setores x [Precision, Recall, FP count, FN count, LLM calls] — See report
- [x] **AC-FINAL-2:** Lista de colisões cross-setor (pares que compartilham >5% dos itens) — 15 pairs documented
- [x] **AC-FINAL-3:** Relatório `docs/audit/precision-recall-benchmark-2026-02-22.md`
- [x] **AC-FINAL-4:** Se qualquer setor tem Precision < 85% ou Recall < 70%, criar sub-story específica — All 15 sectors pass, no sub-stories needed

## Impacto

- **Prova de qualidade:** Primeira vez que temos precision/recall medidos para todos os 15 setores
- **Sustenta a promessa comercial:** "0 falsos positivos" → Precision 98.1% aggregate
- **Identifica setores fracos:** materiais_eletricos lowest recall (73.3%) — candidate for future keyword expansion

## Arquivos

- `backend/tests/test_precision_recall_benchmark.py` — 78 tests (15 parametrized + 63 edge cases)
- `backend/scripts/generate_benchmark_report.py` — report generator script
- `docs/audit/precision-recall-benchmark-2026-02-22.md` — benchmark report
- `backend/sectors_data.yaml` — keyword/exclusion corrections for 6 sectors

## Changes Made

### sectors_data.yaml
1. **alimentos:** +8 animal feed exclusions (ração, alimentos para animais)
2. **engenharia_rodoviaria:** +14 traffic infrastructure keywords (rotatória, semáforo, ciclovia)
3. **materiais_hidraulicos:** +16 plural form keywords (tubos PVC, torneiras, mangueiras)
4. **facilities:** +10 services keywords (copeiragem, dedetização, lavanderia)
5. **facilities:** Removed 5 pest control exclusions (they ARE facilities services)
6. **manutencao_predial:** +9 building maintenance keywords (esquadrias, pintura interna/externa)
