# MON-SUB-03: Monitor de Órgão Contratante (R$ 147–397/mês)

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-MON-SUBS-2026-04](EPIC-MON-SUBS-2026-04.md)
**Sprint:** Wave 2 (depende MON-SUB-01 + MON-SCH-01)

---

## Contexto

Monitor focado em **1 órgão específico** (CNPJ de órgão público). Personas: fornecedores que vendem recorrente para 1 órgão e querem entender padrão de compras + sinais de renovação.

**Conteúdo:**
- O que o órgão comprou no período (por CATMAT/CATSER)
- De quem comprou (top fornecedores)
- Variação de preços pagos
- **Alertas de aditivos** (órgão aditou contrato >20% valor ou >6 meses) — inédito no mercado
- Próximas renovações esperadas (contratos com data_fim dentro de 90 dias)

**2 tiers:**
- **R$ 147/mês**: monthly report
- **R$ 397/mês**: monthly report + alertas real-time de novos editais publicados pelo órgão

---

## Acceptance Criteria

### AC1: Gerador de relatório

- [ ] `backend/monitors/orgao_monitor.py`:
  - Input: `subscription_id, watchlist_items (orgao_cnpj)`
  - Seções: perfil de compras (último mês), top fornecedores, variação preço vs mediana nacional, **seção alertas aditivos** (usa MON-SCH-01), próximas renovações (usa MON-SCH-03)

### AC2: ARQ cron

- [ ] `monthly_orgao_monitor_job` — dia 5 de cada mês 08:00 BRT
- [ ] Tier Premium: cron adicional `daily_orgao_edital_alerts` checa novos editais

### AC3: Dashboard interativo

- [ ] `/monitores/{id}` mesma infra de MON-SUB-02 — adaptar seções para visualização de órgão

### AC4: Email template

- [ ] `backend/templates/emails/orgao_monitor.py`
- [ ] Assunto: `"📋 {orgao_nome} — relatório mensal de compras"`

### AC5: Testes

- [ ] Unit: gerador com órgão simulado
- [ ] Integration: cron mensal → email
- [ ] Snapshot: seção de alertas de aditivos mostra corretamente

---

## Scope

**IN:**
- Gerador + cron
- Alertas aditivos (usa supplier_risk_summary_mv de MON-SCH-01)
- Próximas renovações (usa data_fim de MON-SCH-03)
- Email template
- Testes

**OUT:**
- Monitor de múltiplos órgãos em 1 assinatura — vira tier Enterprise v2
- Comparativo entre órgãos similares — v2

---

## Dependências

- MON-SUB-01 (bloqueador)
- **MON-SCH-01 (aditivos)** — obrigatório para alertas
- MON-SCH-03 (data_fim) — obrigatório para "próximas renovações"

---

## Riscos

- **Órgão com baixo volume:** amostra < 5 compras no mês → digest degradado com aviso
- **Falsos positivos em "renovação esperada":** apenas contratos com data_fim definida no schema; fallback para silêncio se dado ausente

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/monitors/orgao_monitor.py` (novo)
- `backend/templates/emails/orgao_monitor.py` (novo)
- `backend/jobs/cron/monitors.py` (estender — já criado em MON-SUB-02)
- `backend/tests/monitors/test_orgao_monitor.py` (novo)

---

## Definition of Done

- [ ] Cron monthly rodando
- [ ] 3 test subscribers recebendo relatório com dados corretos
- [ ] Alertas de aditivos validados: se órgão teve aditivo >20% no mês, aparece
- [ ] Próximas renovações mostram contratos com data_fim nos próximos 90d
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — monitor de órgão público; aditivos como diferencial |
