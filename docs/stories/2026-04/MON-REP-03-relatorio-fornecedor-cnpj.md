# MON-REP-03: Relatório Fornecedor por CNPJ (R$ 47–197)

**Priority:** P1
**Effort:** L (4-5 dias)
**Squad:** @dev + @ux-design-expert + @qa
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

Primeiro produto monetizável da Camada 2. **Maior volume esperado** — qualquer pessoa pesquisando um CNPJ é lead potencial (advogado, banco, M&A, construtora verificando concorrente).

**3 tiers de preço:**
- **Basic R$ 47:** histórico resumido, top 5 órgãos, valor total por ano
- **Standard R$ 97:** + comparativo vs mediana setor/UF, distribuição modalidade, gráfico evolução
- **Premium R$ 197:** + sinais de risco (score, índice de aditivos*), histórico completo até 5 anos, apêndice com top 20 contratos

*Se MON-SCH-01 ainda não completado na data de lançamento, tier Premium lança sem "índice de aditivos" (documentar em landing).

---

## Acceptance Criteria

### AC1: Gerador PDF do relatório

- [ ] `backend/reports/supplier_report.py` implementa `SupplierReportGenerator`:
  - Input: `purchase.product_params = {cnpj: str, tier: 'basic'|'standard'|'premium', periodo_anos: int}`
  - Output: PDF em bytes
  - Seções Basic: Capa → Sumário executivo LLM → Top órgãos (tabela) → Valor por ano (gráfico) → Rodapé legal
  - Seções Standard (+): Distribuição modalidade (pizza) → Comparativo vs mediana (bar chart) → Timeline de contratos
  - Seções Premium (+): Sinais de risco (score, % contratos aditados, concentração top 3 órgãos) → Apêndice top 20 contratos (tabela detalhada)

### AC2: Prompt LLM customizado

- [ ] `backend/llm/prompts/supplier_summary.py` com prompt estruturado:
  - Input: dados agregados do CNPJ (top órgãos, valores, tendências)
  - Output: `SupplierSummarySchema` (Pydantic) com `resumo_executivo`, `destaques[]`, `sinais_atencao[]`
- [ ] Ground-truth correction: valida que `resumo_executivo` não inventa dados ausentes (ex: não diz "90% em SP" se no dataset é 60%)
- [ ] Fallback determinístico se LLM falhar (template estático com placeholders)

### AC3: Landing + preview + checkout

- [ ] `frontend/app/relatorios/fornecedor/[cnpj]/page.tsx`:
  - SSR: buscar dados básicos do CNPJ (via `empresa_publica.py`)
  - Header: "Relatório Fornecedor — {nome}"
  - **Preview gratuito** (3 bullets gerados por LLM: "Empresa X atende principalmente Y", "Top órgão: Z", "Valor total R$ W")
  - 3 cards de tier (Basic / Standard / Premium) com comparativo de features
  - Botão "Comprar por R$ X" chama `POST /v1/purchases/checkout` com `{product_type: 'report_supplier', product_params: {cnpj, tier}}`
  - Redirect para Stripe Checkout (sucesso → `/conta/compras?purchase_id=X`)
  - SEO: title + description otimizados para busca CNPJ

### AC4: Página de conta "Meus Relatórios"

- [ ] `frontend/app/conta/compras/page.tsx` (nova ou estende `/conta/assinatura`):
  - Lista todos `purchases` do user
  - Cada linha: produto, data compra, status (pending/gerando/pronto/expirado), botão Download
  - Download chama `GET /v1/reports/{report_id}/download` e abre em nova aba
  - Exibe "Relatório expira em Xh" se `expires_at` próximo

### AC5: Testes

- [ ] Unit: `backend/tests/reports/test_supplier_report.py`
  - Gera PDF Basic válido (>0 bytes, páginas esperadas)
  - Gera PDF Premium com todas as seções
  - LLM falha → fallback determinístico funciona
  - CNPJ sem contratos → PDF com mensagem "Nenhum contrato encontrado" (não quebra)
- [ ] Integration: `backend/tests/integration/test_supplier_report_e2e.py`
  - purchase paid → job → PDF gerado → storage → email
- [ ] Frontend: `frontend/__tests__/relatorios-fornecedor.test.tsx`
  - Preview renderiza sem crash
  - Click em tier → chama checkout
- [ ] E2E Playwright: user compra Basic, recebe email mockado, download link funciona

### AC6: Observability

- [ ] Prometheus: `smartlic_supplier_reports_generated_total{tier}`, `smartlic_supplier_reports_revenue_cents_total{tier}`
- [ ] Sentry breadcrumbs em cada etapa da geração

---

## Scope

**IN:**
- Gerador PDF (reportlab — já em uso)
- Prompt LLM + ground-truth correction
- Landing SSR + checkout UI
- Página "Meus Relatórios"
- Testes unit + integration + E2E

**OUT:**
- Relatório customizado (user escolhe seções) — fora de v1
- Relatório em formato Word ou Excel — v1 só PDF
- Comparativo de 2 CNPJs — fora de v1

---

## Dependências

- MON-REP-01 (checkout + purchases)
- MON-REP-02 (generator dispatch + delivery)
- Dados de `pncp_supplier_contracts` (já existem)
- BrasilAPI ou `empresa_publica.py` para razão social/endereço (já em uso)

---

## Riscos

- **LLM hallucination em sinais de risco Premium:** ground-truth correction obrigatória; testes cobrem casos edge
- **CNPJ com milhares de contratos (empresas grandes) geram PDF pesado:** limite `MAX_CONTRACTS_IN_DETAIL=500` no Premium; incluir tabela paginada ou apêndice "top 500 por valor"
- **CNPJ sem contratos:** PDF com mensagem explicativa; considerar oferecer refund se coverage=0

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/reports/supplier_report.py` (novo)
- `backend/reports/_base.py` (novo — abstract ReportGenerator)
- `backend/reports/_registry.py` (estender)
- `backend/llm/prompts/supplier_summary.py` (novo)
- `backend/schemas/supplier_summary.py` (novo — Pydantic schema)
- `frontend/app/relatorios/fornecedor/[cnpj]/page.tsx` (novo)
- `frontend/app/conta/compras/page.tsx` (novo ou estende)
- `backend/tests/reports/test_supplier_report.py` (novo)
- `frontend/__tests__/relatorios-fornecedor.test.tsx` (novo)
- `frontend/e2e-tests/buy-supplier-report.spec.ts` (novo)

---

## Definition of Done

- [ ] 3 test purchases end-to-end (1 por tier) bem-sucedidas em staging
- [ ] PDFs validados por review humano: nenhum dado inventado, layout legível, branding consistente
- [ ] Prometheus métricas visíveis
- [ ] Testes backend + frontend + E2E passando
- [ ] Landing page SSR com Lighthouse >= 85

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — primeiro produto monetizável da Camada 2, maior volume esperado |
