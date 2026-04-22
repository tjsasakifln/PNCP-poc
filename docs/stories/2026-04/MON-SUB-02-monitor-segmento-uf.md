# MON-SUB-02: Monitor de Segmento por UF (R$ 197–497/mês)

**Priority:** P1
**Effort:** L (4-5 dias)
**Squad:** @dev + @qa
**Status:** Draft
**Epic:** [EPIC-MON-SUBS-2026-04](EPIC-MON-SUBS-2026-04.md)
**Sprint:** Wave 2 (depende MON-SUB-01)

---

## Contexto

Primeiro produto da Camada 3. Relatório automático semanal ou mensal sobre o mercado de um setor+UF específico — entregue por email + dashboard web interativo.

**Conteúdo do relatório:**
- Novos entrantes (fornecedores que ganharam primeiro contrato no período)
- Players que saíram (último contrato há > 6 meses)
- Variação de preços (CATMAT/CATSER mais comuns do setor, delta vs período anterior)
- Órgãos mais ativos no setor+UF (top 5 por valor contratado)
- Alertas de aditivos significativos

**2 tiers:**
- **R$ 197/mês** (weekly): relatório semanal segunda 06:00 BRT
- **R$ 497/mês** (weekly + alertas real-time): + alertas por email quando novo edital >R$ 500k no setor+UF

---

## Acceptance Criteria

### AC1: Gerador de relatório

- [ ] `backend/monitors/segment_uf_monitor.py`:
  - Input: `subscription_id, watchlist_items (setor, uf)`
  - Usa dados de `pncp_supplier_contracts` + `pncp_raw_bids`
  - Gera PDF (via pipeline MON-REP-02) + dashboard HTML (iframe embedável)

### AC2: ARQ crons

- [ ] `weekly_segment_monitor_job` — segunda 06:00 BRT:
  - Enfileira todos `monitored_subscriptions` com `addon_type='monitor_segmento_uf'` e `cadence='weekly'`
  - Por cada: gera relatório + envia email + armazena em `generated_reports`
- [ ] `monthly_segment_monitor_job` — dia 1 do mês 07:00 BRT (tier anual)
- [ ] Idempotência: não reenviar se `generated_reports` já tem entry para (subscription_id, period)

### AC3: Dashboard interativo `/monitores/{id}`

- [ ] `frontend/app/monitores/[id]/page.tsx` (protegido por ownership check):
  - Sidebar: histórico de relatórios do monitor (últimas 12 edições)
  - Main: visualização do relatório atual (embedable charts Recharts)
  - Seções: novos entrantes (tabela), saídas (tabela), variação de preços (gráfico), top órgãos (bar chart), alertas
  - Botão "Baixar PDF" (usa link assinado MON-REP-02)
  - Botão "Configurar alertas real-time" (tier Premium)

### AC4: Alertas real-time (tier Premium)

- [ ] Integra com pipeline de `new_bids_notifier` (STORY-315) extendido:
  - Ao detectar novo edital no `pncp_raw_bids` com setor+uf match + valor_estimado > threshold → email push em 15 min
- [ ] Unsubscribe link por alerta

### AC5: Email template

- [ ] `backend/templates/emails/segment_monitor.py`:
  - Assunto: `"📊 Monitor {setor} × {uf} — edição semanal"`
  - Body: resumo executivo (LLM) + 3 highlights + link para dashboard + link PDF
  - Versão text/plain

### AC6: Testes

- [ ] Unit: gerador com dados mockados
- [ ] Integration: cron dispara → relatório gerado → email enviado
- [ ] E2E: user assina → 7 dias depois (mock time) recebe primeiro relatório

---

## Scope

**IN:**
- Gerador PDF + dashboard HTML
- 2 crons (weekly + monthly)
- Alertas real-time (tier Premium)
- Email template
- Testes

**OUT:**
- Customização de seções (user escolhe o que aparece) — v2
- Notificações WhatsApp/Slack — v2 (considerar add-on separado)
- Multi-setor em um monitor — requer tier Enterprise v2

---

## Dependências

- MON-SUB-01 (bloqueador absoluto)
- MON-REP-02 (pipeline de geração + entrega)
- Classificação setorial IA existente
- `pncp_raw_bids` + `pncp_supplier_contracts`

---

## Riscos

- **Relatório vazio em setor pouco ativo + UF pequena:** aplicar "expand" (alargar UF para região) se amostra < 10 contratos no período; mensagem "dados limitados, considerar monitor regional"
- **Flood de alertas em setor quente:** rate limit 5 alertas/dia por monitor; consolidar em digest diário se > 5

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `backend/monitors/segment_uf_monitor.py` (novo)
- `backend/jobs/cron/monitors.py` (novo)
- `backend/templates/emails/segment_monitor.py` (novo)
- `frontend/app/monitores/[id]/page.tsx` (novo)
- `frontend/app/components/monitor/**` (componentes de dashboard)
- `backend/tests/monitors/test_segment_uf_monitor.py` (novo)

---

## Definition of Done

- [ ] Cron weekly rodando há 2 semanas sem Sentry errors
- [ ] 3 test subscribers recebendo relatórios corretos
- [ ] Dashboard funcional + PDF download funciona
- [ ] Tier Premium alertas real-time disparam em < 15 min
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — primeiro monitor da Camada 3 |
