# STORY-301: Email Alert System

**Sprint:** 3 — Make It Competitive
**Size:** XL (16-24h)
**Root Cause:** Track A (Market Intelligence) / Track E (Business Model)
**Depends on:** STORY-292, STORY-295
**Industry Standard:** Table Stakes — todos os concorrentes (Licitanet, LicitaJá, Portal de Compras) oferecem alertas por email
**Status:** accepted

## Contexto

Alertas por email é feature table-stakes no mercado de licitações. Sem ela, o usuário precisa entrar na plataforma ativamente para descobrir oportunidades. Todos os concorrentes oferecem isso. É o feature gap mais crítico identificado no Track A (Market Intelligence).

## Acceptance Criteria

### Backend
- [x] AC1: `POST /v1/alerts` — criar alerta com filtros (setor, UFs, valor_min, valor_max, keywords)
- [x] AC2: `GET /v1/alerts` — listar alertas do usuário
- [x] AC3: `PATCH /v1/alerts/{id}` — editar alerta (ativar/desativar, mudar filtros)
- [x] AC4: `DELETE /v1/alerts/{id}` — remover alerta
- [x] AC5: Cron job diário (8h BRT): executa busca para cada alerta ativo
- [x] AC6: Dedup: não envia oportunidade já enviada antes (tracking table `alert_sent_items`)
- [x] AC7: Email via Resend com template HTML responsivo
- [x] AC8: Rate limit: máximo 1 email/dia por alerta (digest format)
- [x] AC9: Unsubscribe link em cada email (one-click, RFC 8058)

### Frontend
- [x] AC10: Página `/alertas` — CRUD de alertas
- [x] AC11: "Criar alerta a partir desta busca" — botão na página de resultados
- [x] AC12: Preview do alerta antes de salvar
- [x] AC13: Histórico de alertas enviados
- [x] AC14: Toggle on/off para cada alerta

### Email Template
- [x] AC15: Subject: "SmartLic — {N} novas oportunidades em {setor}"
- [x] AC16: Body: tabela com top 10 oportunidades (objeto, UF, valor, modalidade, link PNCP)
- [x] AC17: CTA: "Ver todas as {total} oportunidades no SmartLic"
- [x] AC18: Footer: link unsubscribe + preferências

### Database
- [x] AC19: Tabela `alerts` (id, user_id, name, filters JSONB, active, created_at, updated_at)
- [x] AC20: Tabela `alert_sent_items` (alert_id, item_id, sent_at) — dedup tracking
- [x] AC21: RLS: usuário só vê seus próprios alertas

### Quality
- [x] AC22: Teste: cron executa busca e envia email com resultados
- [x] AC23: Teste: dedup funciona (mesma oportunidade não enviada 2x)
- [x] AC24: Teste: unsubscribe link desativa alerta
- [x] AC25: Testes existentes passando

## Technical Notes

O cron job reutiliza a search_results_cache (resultados já existentes no cache L2), evitando chamadas adicionais às APIs governamentais. O resultado é filtrado pelo alerta e formatado como email digest.

```python
# Cron job flow (alert_service.py)
for alert in active_alerts:
    if not check_rate_limit(alert.id):  # 20h window
        continue
    results = execute_alert_search(alert.filters)  # queries search_results_cache
    new_items = dedup_results(results, get_sent_item_ids(alert.id))
    if new_items:
        email = render_alert_digest_email(alert, new_items)
        await send_email(alert.user_email, subject, email)
        finalize_alert_send(alert.id, [item.id for item in new_items])
```

## Files Changed

### New Files
- `supabase/migrations/20260227100000_create_alerts.sql` — tables + RLS + indexes
- `backend/routes/alerts.py` — CRUD + unsubscribe + history endpoints
- `backend/services/alert_service.py` — cron job logic (search, dedup, rate limit)
- `backend/templates/emails/alert_digest.py` — email template rendering
- `backend/tests/test_alerts.py` — 74 backend tests
- `frontend/app/alertas/page.tsx` — alerts management page (CRUD, preview, toggle)
- `frontend/app/api/alerts/route.ts` — GET/POST API proxy
- `frontend/app/api/alerts/[id]/route.ts` — PATCH/DELETE API proxy
- `frontend/__tests__/alertas-page.test.tsx` — 20 frontend tests
- `frontend/__tests__/api-alerts-route.test.ts` — 6 API route tests

### Modified Files
- `backend/main.py` — register alerts_router
- `backend/config.py` — ALERTS_ENABLED, ALERTS_HOUR_UTC, ALERTS_MAX_PER_EMAIL flags
- `backend/job_queue.py` — email_alerts_job cron + WorkerSettings registration
- `frontend/components/Sidebar.tsx` — added Alertas nav item
- `frontend/components/BottomNav.tsx` — added Alertas nav item + fixed aria-label encoding
- `frontend/app/buscar/components/SearchResults.tsx` — "Criar alerta a partir desta busca" link
- `backend/tests/snapshots/openapi_schema.json` — regenerated with alert endpoints

## Definition of Done

- [x] Alerta criado → email recebido no dia seguinte com oportunidades novas
- [x] Unsubscribe funciona em 1 click
- [x] Zero duplicatas em emails
- [x] Todos os testes passando
- [x] PR merged
