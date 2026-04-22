# MON-REP-04: Relatório Preço de Referência por Categoria (R$ 97–297)

**Priority:** P1
**Effort:** L (4-5 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1 (depende MON-SCH-02)

---

## Contexto

Personas-alvo: **fiscais de contrato, orçamentistas, pregoeiros** que precisam justificar preço estimado em contratação pública. Hoje usam "Painel de Preços" do governo (UX horrível) + planilhas manuais. Relatório SmartLic entrega distribuição estatística automática em PDF profissional.

Pergunta-mãe: *"Quanto o governo pagou por [CATMAT/CATSER X] em [UF Y] nos últimos [N meses]?"*

**3 tiers:**
- **Basic R$ 97:** distribuição nacional para 1 CATMAT/CATSER, 12 meses
- **Standard R$ 197:** distribuição por UF + 24 meses + outliers
- **Premium R$ 297:** 3 CATMAT/CATSER em um único relatório + análise comparativa

---

## Acceptance Criteria

### AC1: Gerador PDF

- [ ] `backend/reports/price_reference_report.py` implementa `PriceReferenceReportGenerator`:
  - Input: `{catmats: [str], uf: str|'all', periodo_meses: 12|24|36, tier: ...}`
  - Usa RPC `benchmark_by_catmat` (MON-SCH-02) como fonte principal
  - Seções: Capa → Sumário executivo (LLM) → Distribuição estatística (P10/P25/P50/P75/P90, média, mediana, desvio) → Histograma de preços → Tabela outliers (top/bottom 10%)
  - Standard (+): Mapa de calor por UF
  - Premium (+): Análise comparativa multi-CATMAT

### AC2: Landing + seletor de categoria

- [ ] `frontend/app/relatorios/preco-referencia/page.tsx`:
  - Seletor autocompletar de CATMAT/CATSER (query `catmat_catser_catalog`)
  - Seletor UF (27 + "Nacional")
  - Seletor período (12/24/36 meses)
  - Preview gratuito: "123 contratos encontrados, mediana R$ 4.500" (visible sem compra)
  - 3 cards de tier
  - SEO: `/relatorios/preco-referencia` (sem parâmetros na URL), compra persiste parâmetros em `product_params`

### AC3: Prompt LLM para sumário

- [ ] `backend/llm/prompts/price_reference_summary.py`:
  - Input: estatísticas + top outliers
  - Output: resumo executivo (narrativo) + "contexto comparativo" (ex: "preços em SP são 15% acima da mediana nacional")
  - Ground-truth correction garante que não invente percentis

### AC4: Validação de escopo estatístico mínimo

- [ ] Se RPC retorna < 20 contratos para a combinação (catmat+uf+periodo):
  - Basic/Standard: sugere expandir período ou remover filtro UF; bloqueia checkout com mensagem
  - Premium: permite prosseguir mas com disclaimer "dados limitados"
- [ ] Nunca gera relatório com < 5 contratos (validar antes do job iniciar)

### AC5: Testes

- [ ] Unit: `backend/tests/reports/test_price_reference_report.py`
  - Gera PDF Basic válido com dados mockados
  - Rejeita combinação com < 20 contratos (Basic)
  - Premium com 3 CATMATs diferentes
- [ ] Integration: E2E flow completo
- [ ] Snapshot test: PDF Basic tem páginas/seções esperadas

---

## Scope

**IN:**
- Gerador PDF + prompt LLM
- Landing + seletor
- Validação de escopo estatístico
- Testes

**OUT:**
- Sub-categorização (ex: CATMAT pai + filhos) — v2
- Export Excel/CSV — v2
- Alerta quando preço-alvo está dentro de faixa — vira add-on MON-SUB-*

---

## Dependências

- MON-REP-01 + MON-REP-02 (checkout + delivery)
- **MON-SCH-02 (CATMAT/CATSER)** — bloqueador absoluto
- RPC `benchmark_by_catmat` operacional

---

## Riscos

- **CATMAT coverage < 80%:** produto mostra "dados parciais" no rodapé se coverage <90% para aquela categoria
- **Outliers extremos distorcendo stats:** aplicar IQR filter opcional (flag) para tier Premium

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/reports/price_reference_report.py` (novo)
- `backend/llm/prompts/price_reference_summary.py` (novo)
- `frontend/app/relatorios/preco-referencia/page.tsx` (novo)
- `frontend/app/components/CatmatAutocomplete.tsx` (novo)
- `backend/tests/reports/test_price_reference_report.py` (novo)
- `frontend/e2e-tests/buy-price-reference.spec.ts` (novo)

---

## Definition of Done

- [ ] 3 test purchases (1 por tier)
- [ ] PDFs validados: estatísticas batem com queries diretas ao datalake
- [ ] Landing Lighthouse >= 85
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — produto para fiscais/pregoeiros; requer MON-SCH-02 CATMAT |
