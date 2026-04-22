# MON-REP-06: Due Diligence Express Lite (R$ 297–697, SEM CEIS/CNEP na v1)

**Priority:** P1
**Effort:** L (5 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1 (depende MON-SCH-01 + MON-SCH-02)

---

## Contexto

Personas: **bancos, fintechs de crédito PME, seguradoras** com exposição a fornecedores B2G. Produto mais alto ticket da Camada 2.

**v1 é "lite" — documentado explicitamente:**
- Inclui: score de adimplência via aditivos, concentração de receita (top 3 órgãos %), padrão de superfaturamento (desvio vs mediana por categoria)
- **NÃO inclui:** consultas CEIS/CNEP (bases de sanções da CGU), histórico judicial, CND, scraping Receita. Esses ficam para `MON-REP-06b` em Q3.

Disclaimer obrigatório no PDF + landing.

**3 tiers:**
- **Basic R$ 297:** score geral, top concentrações
- **Standard R$ 497:** + histórico de aditivos por contrato + análise de superfaturamento
- **Premium R$ 697:** + comparativo vs peers setor/UF + recomendações de mitigação

---

## Acceptance Criteria

### AC1: Score de risco derivado

- [ ] `backend/services/supplier_risk_score.py` calcula score 0-100 combinando:
  - **Índice de aditivos (30%):** `aditivos_pct_valor` médio ponderado (quanto maior, pior score)
  - **Concentração de receita (25%):** % top 3 órgãos no total (concentração > 80% = alto risco)
  - **Padrão de preço (25%):** desvio médio vs mediana por categoria (contratos muito acima = sinal alerta)
  - **Volatilidade (20%):** desvio padrão do valor anual (alta volatilidade = instabilidade)
- [ ] Normalização percentil: score do fornecedor X comparado à distribuição de peers (setor + UF)
- [ ] Retorna `{score_geral, breakdown, percentil_setor, flags[], explicacao}`
- [ ] Cacheado em `supplier_risk_summary_mv` (view materializada de MON-SCH-01)

### AC2: Gerador PDF

- [ ] `backend/reports/due_diligence_report.py`:
  - Input: `{cnpj: str, tier: ...}`
  - Header com disclaimer "v1 não inclui CEIS/CNEP — consulta complementar recomendada"
  - Basic: resumo LLM → score 0-100 + bar chart → top 3 órgãos concentração → flags
  - Standard (+): timeline de aditivos por contrato → análise de superfaturamento com outliers → seção "sinais de atenção"
  - Premium (+): comparativo percentil vs peers → tabela de recomendações (estruturada em 5-7 items por LLM com RAG sobre casos similares)

### AC3: Landing com disclaimer explícito

- [ ] `frontend/app/relatorios/due-diligence/page.tsx`:
  - Seletor CNPJ (input ou autocompletar)
  - **Box destacado:** "v1 não substitui consulta CEIS/CNEP — disponível em Q3"
  - Preview: score dummy + 2 flags (para dar gostinho)
  - 3 cards tier
  - Seção FAQ com "O que está incluído" / "O que NÃO está incluído"

### AC4: Prompt LLM para recomendações (Premium)

- [ ] `backend/llm/prompts/due_diligence_recommendations.py`:
  - Input: flags detectadas + stats do fornecedor
  - Output: 5-7 recomendações estruturadas (ex: "Solicitar comprovação de capacidade técnica antes de contratar"; "Avaliar garantia reforçada por concentração de receita >80%")
  - Ground-truth correction evita recomendações genéricas que não se aplicam

### AC5: Testes

- [ ] Unit: `test_supplier_risk_score.py` — score determinístico para dados conhecidos
- [ ] Unit: geração PDF por tier
- [ ] Integration: E2E com CNPJ real
- [ ] Snapshot: disclaimer aparece no PDF e landing

---

## Scope

**IN:**
- Risk score calculado (5 dimensões, normalização percentil)
- Gerador PDF 3 tiers
- Landing + disclaimer
- Prompt LLM para recomendações Premium
- Testes

**OUT:**
- **CEIS/CNEP integration (fica para MON-REP-06b Q3)**
- Consulta CNPJ na Receita Federal — fora de escopo
- Score com ML — futuro (MON-API-06)
- Monitoramento contínuo — fica para Radar de Risco (MON-SUB-04)

---

## Dependências

- MON-REP-01 + MON-REP-02
- **MON-SCH-01 (aditivos)** — bloqueador absoluto (score precisa de aditivos)
- **MON-SCH-02 (CATMAT)** — necessário para desvio de preço por categoria
- View `supplier_risk_summary_mv` populada

---

## Riscos

- **Expectativa frustrada com "sem CEIS":** disclaimer obrigatório em landing + PDF; email de confirmação de compra reforça
- **Score inadequado sem aditivos completos:** se `aditivos_last_checked_at IS NULL` para >50% dos contratos, rebaixar confiança do score com flag visual
- **Falsos positivos em "superfaturamento":** diferença >50% vs mediana pode ser explicada (especificação técnica diferente); disclaimer "sinal para investigação, não conclusão"

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/services/supplier_risk_score.py` (novo)
- `backend/reports/due_diligence_report.py` (novo)
- `backend/llm/prompts/due_diligence_recommendations.py` (novo)
- `frontend/app/relatorios/due-diligence/page.tsx` (novo)
- `backend/tests/services/test_supplier_risk_score.py` (novo)
- `backend/tests/reports/test_due_diligence_report.py` (novo)

---

## Definition of Done

- [ ] 3 test purchases por tier
- [ ] Score validado: fornecedor com muitos aditivos score baixo; fornecedor limpo score alto
- [ ] PDFs + landing com disclaimer visível e claro
- [ ] Testes passando
- [ ] Future story `MON-REP-06b` (integração CEIS/CNEP) documentada em backlog Q3

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — v1 lite sem CEIS/CNEP; persona bancos/fintechs de crédito PME |
