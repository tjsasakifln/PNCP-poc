# MON-REP-05: Relatório Mapeamento de Concorrência (R$ 197–497)

**Priority:** P1
**Effort:** L (5 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-REPORTS-2026-04](EPIC-MON-REPORTS-2026-04.md)
**Sprint:** Wave 1

---

## Contexto

Personas: **construtoras, consultorias, M&A advisors** que precisam entender players dominantes em um segmento+UF. Pergunta-mãe: *"Quem são os maiores players em [setor] em [UF], quem cresceu, quem perdeu share?"*

Valor percebido alto (R$ 197–497) justifica análise longitudinal rica.

**3 tiers:**
- **Basic R$ 197:** top 20 players, market share atual, 12 meses
- **Standard R$ 347:** + growth/decline YTD, novos entrantes, churn, 24 meses
- **Premium R$ 497:** + análise multi-UF, tendência trimestral, heatmap de concentração

---

## Acceptance Criteria

### AC1: Gerador PDF

- [ ] `backend/reports/competition_mapping_report.py`:
  - Input: `{setor: str, uf: str, periodo_meses: int, tier: ...}`
  - Seções Basic: Capa → Resumo LLM → Top 20 players (tabela ordenada por valor) → Tree map market share → Distribuição modalidade
  - Standard (+): Timeline entrantes/saídas (gráfico lollipop) → Growth/decline YTD por player (bar chart ordenado) → "Concentração HHI" (Herfindahl-Hirschman Index)
  - Premium (+): Multi-UF comparativa → Tendência trimestral evolutiva → Heatmap player × órgão

### AC2: RPC agregador

- [ ] Migração cria função `competitors_in_segment(p_setor text, p_uf text, p_periodo_meses int)`:
  - Retorna lista ordenada de players com: `ni_fornecedor, nome, total_valor, contratos_count, market_share_pct, growth_yoy_pct, rank`
  - Performance p95 < 500ms (índices existentes bastam)
- [ ] RPC `new_entrants_churn(p_setor, p_uf, p_periodo)` retorna listas de entrantes e saídas (primeira/última aparição em N meses)

### AC3: Landing + seletor

- [ ] `frontend/app/relatorios/concorrencia/page.tsx`:
  - Seletor setor (do catálogo existente — 15 setores SmartLic)
  - Seletor UF
  - Seletor período
  - Preview: "47 players encontrados no setor X em UF Y. Top player detém 22% de share"
  - 3 cards de tier

### AC4: Prompt LLM

- [ ] `backend/llm/prompts/competition_analysis.py`:
  - Input: top 20 players + métricas
  - Output: análise narrativa de "dinâmica competitiva" (ex: "setor concentrado com HHI 2.800, liderança de X")
  - Ground-truth correction obrigatória

### AC5: Testes

- [ ] Unit: teste de geração para cada tier com dados sintéticos
- [ ] Integration: E2E completo
- [ ] Snapshot: Basic tem exatamente as seções esperadas

---

## Scope

**IN:**
- Gerador PDF
- 2 RPCs agregadores
- Landing + seletor
- Prompt LLM + ground truth
- Testes

**OUT:**
- Exportação Excel — v2
- Análise geográfica detalhada por município — v2
- Comparação entre 2+ setores — v2

---

## Dependências

- MON-REP-01 + MON-REP-02
- Dados de `pncp_supplier_contracts` + classificação setorial IA (existente)

---

## Riscos

- **Setor com <20 players:** bloqueia Basic; Standard permite com disclaimer
- **HHI calculation em dataset ruidoso:** aplicar dedupe por `ni_fornecedor` (mesmo CNPJ pode aparecer como variante)

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/reports/competition_mapping_report.py` (novo)
- `backend/llm/prompts/competition_analysis.py` (novo)
- `supabase/migrations/.../create_competitors_rpcs.sql` + `.down.sql`
- `frontend/app/relatorios/concorrencia/page.tsx` (novo)
- `backend/tests/reports/test_competition_mapping.py` (novo)

---

## Definition of Done

- [ ] 3 test purchases por tier
- [ ] PDFs validados contra query manual
- [ ] Testes passando
- [ ] Dogfood: equipe compra 1 relatório do próprio setor SmartLic ("SaaS B2G") e confirma dados

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — produto para construtoras/consultorias/M&A |
