# STORY-301: Email Alert System

**Sprint:** 3 — Make It Competitive
**Size:** XL (16-24h)
**Root Cause:** Track A (Market Intelligence) / Track E (Business Model)
**Depends on:** STORY-292, STORY-295
**Industry Standard:** Table Stakes — todos os concorrentes (Licitanet, LicitaJá, Portal de Compras) oferecem alertas por email

## Contexto

Alertas por email é feature table-stakes no mercado de licitações. Sem ela, o usuário precisa entrar na plataforma ativamente para descobrir oportunidades. Todos os concorrentes oferecem isso. É o feature gap mais crítico identificado no Track A (Market Intelligence).

## Acceptance Criteria

### Backend
- [ ] AC1: `POST /v1/alerts` — criar alerta com filtros (setor, UFs, valor_min, valor_max, keywords)
- [ ] AC2: `GET /v1/alerts` — listar alertas do usuário
- [ ] AC3: `PATCH /v1/alerts/{id}` — editar alerta (ativar/desativar, mudar filtros)
- [ ] AC4: `DELETE /v1/alerts/{id}` — remover alerta
- [ ] AC5: Cron job diário (8h BRT): executa busca para cada alerta ativo
- [ ] AC6: Dedup: não envia oportunidade já enviada antes (tracking table `alert_sent_items`)
- [ ] AC7: Email via Resend com template HTML responsivo
- [ ] AC8: Rate limit: máximo 1 email/dia por alerta (digest format)
- [ ] AC9: Unsubscribe link em cada email (one-click, RFC 8058)

### Frontend
- [ ] AC10: Página `/alertas` — CRUD de alertas
- [ ] AC11: "Criar alerta a partir desta busca" — botão na página de resultados
- [ ] AC12: Preview do alerta antes de salvar
- [ ] AC13: Histórico de alertas enviados
- [ ] AC14: Toggle on/off para cada alerta

### Email Template
- [ ] AC15: Subject: "SmartLic — {N} novas oportunidades em {setor}"
- [ ] AC16: Body: tabela com top 10 oportunidades (objeto, UF, valor, modalidade, link PNCP)
- [ ] AC17: CTA: "Ver todas as {total} oportunidades no SmartLic"
- [ ] AC18: Footer: link unsubscribe + preferências

### Database
- [ ] AC19: Tabela `alerts` (id, user_id, name, filters JSONB, active, created_at, updated_at)
- [ ] AC20: Tabela `alert_sent_items` (alert_id, item_id, sent_at) — dedup tracking
- [ ] AC21: RLS: usuário só vê seus próprios alertas

### Quality
- [ ] AC22: Teste: cron executa busca e envia email com resultados
- [ ] AC23: Teste: dedup funciona (mesma oportunidade não enviada 2x)
- [ ] AC24: Teste: unsubscribe link desativa alerta
- [ ] AC25: Testes existentes passando

## Technical Notes

O cron job reutiliza a mesma search pipeline, mas sem SSE (background). O resultado é filtrado pelo alerta e formatado como email digest.

```python
# Cron job flow
for alert in active_alerts:
    results = await search_pipeline.execute(alert.filters, background=True)
    new_items = dedup(results, alert.sent_items)
    if new_items:
        email = render_alert_email(alert, new_items)
        await resend.send(email)
        track_sent_items(alert.id, new_items)
```

## Files to Change

- `backend/routes/alerts.py` — NEW: CRUD endpoints
- `backend/models/alert.py` — NEW: Alert model
- `backend/cron_jobs.py` — daily alert execution
- `backend/email_service.py` — alert email template
- `backend/templates/emails/alert_digest.html` — NEW: email template
- `supabase/migrations/XXX_create_alerts.sql` — NEW: tables + RLS
- `frontend/app/alertas/page.tsx` — NEW: alerts management page
- `frontend/app/buscar/page.tsx` — "Criar alerta" button

## Definition of Done

- [ ] Alerta criado → email recebido no dia seguinte com oportunidades novas
- [ ] Unsubscribe funciona em 1 click
- [ ] Zero duplicatas em emails
- [ ] Todos os testes passando
- [ ] PR merged
