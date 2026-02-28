# STORY-315: Search Alerts com Notificacao

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 3 (Post-launch)
**Priority:** HIGH
**Story Points:** 8 SP
**Estimate:** 5-7 dias
**Owner:** @dev + @data-engineer

---

## Problem

Usuarios precisam verificar manualmente o SmartLic todos os dias para descobrir novas oportunidades. Nao ha mecanismo de alerta que notifique quando editais relevantes sao publicados. Isso reduz engajamento e time-to-opportunity. Rotas CRUD ja existem (`routes/alerts.py`) mas falta o motor de matching e o envio de notificacoes.

## Solution

Implementar motor de matching de alertas que roda como cron job diario, compara novos editais contra filtros salvos de cada alerta, e envia digest email com oportunidades encontradas.

---

## Acceptance Criteria

### Backend — Motor de Matching

- [ ] **AC1:** Criar `backend/services/alert_matcher.py` com funcao `match_alerts()`:
  - Query: alertas ativos de usuarios com plano ativo
  - Para cada alerta: executar busca com filtros do alerta (setor, UFs, valor, keywords)
  - Comparar resultados contra `alert_sent_items` para encontrar NOVOS (nao enviados antes)
  - Return: `{ alert_id, user_id, new_items: LicitacaoItem[] }`
- [ ] **AC2:** Filtros de matching devem usar mesma logica de `filter.py`:
  - Keyword density scoring
  - UF filtering
  - Value range filtering
  - Status filtering (apenas abertas)
- [ ] **AC3:** Dedup: nao enviar mesma licitacao em alertas diferentes do mesmo usuario
- [ ] **AC4:** Periodo de busca: ultimas 24h (desde ultimo run)

### Backend — Digest Email

- [ ] **AC5:** Criar template `backend/templates/emails/alert_digest.py` (complementar ao existente):
  - Assunto: "SmartLic: {N} novas oportunidades para {alert_name}"
  - Corpo: lista de licitacoes com orgao, UF, valor, data, link
  - Max 20 itens por email (paginar se necessario)
  - CTA: "Ver todas no SmartLic" → /buscar com filtros pre-aplicados
  - Footer: "Gerenciar alertas" → /conta#alertas + one-click unsubscribe
- [ ] **AC6:** Suporte para digest consolidado (1 email com todos os alertas do usuario)
  vs email individual por alerta — configuravel pelo usuario
- [ ] **AC7:** Incluir `List-Unsubscribe` header (RFC 8058) reutilizando pattern existente de `alerts.py`

### Backend — Cron Job

- [ ] **AC8:** Criar ARQ task `process_search_alerts` em `cron_jobs.py`:
  - Executar diariamente as 08:00 BRT (`ALERTS_HOUR_UTC = 11` ja existe em config)
  - Rate limit: max 100 alertas/execucao, batch de 10 concurrent
  - Respeitar `ALERTS_ENABLED` flag (ja existe em config)
- [ ] **AC9:** Criar tabela `alert_sent_items`:
  - `alert_id`, `licitacao_id` (or `pncp_id`), `sent_at`, `digest_id`
  - Index em (alert_id, licitacao_id) para dedup rapido
- [ ] **AC10:** Criar tabela `alert_runs`:
  - `id`, `alert_id`, `run_at`, `items_found`, `items_sent`, `status`
  - Para historico e debugging

### Backend — CRUD Existente (Validar/Estender)

- [ ] **AC11:** Validar que rotas CRUD existentes em `routes/alerts.py` funcionam end-to-end:
  - POST /alerts — criar alerta com filtros
  - GET /alerts — listar alertas do usuario com sent_count
  - PATCH /alerts/{id} — editar filtros
  - DELETE /alerts/{id} — deletar alerta
- [ ] **AC12:** Adicionar `GET /alerts/{id}/preview`:
  - Executa matching sem enviar email
  - Retorna oportunidades que seriam enviadas (dry-run)
  - Util para usuario validar filtros antes de ativar alerta
- [ ] **AC13:** Validar unsubscribe endpoint `GET /alerts/{id}/unsubscribe` com token HMAC

### Frontend — UI de Alertas

- [ ] **AC14:** Pagina `/conta` — secao "Meus Alertas" com:
  - Lista de alertas ativos com filtros resumidos
  - Toggle on/off por alerta
  - Botao "Criar novo alerta"
  - Historico: ultimos envios com count de oportunidades
- [ ] **AC15:** Modal "Criar Alerta" com:
  - Selector de setor (ou termos livres)
  - Selector de UFs (reutilizar componente existente)
  - Range de valor (opcional)
  - Preview: "Baseado nesses filtros, encontrariamos ~{N} oportunidades nos ultimos 7 dias"
- [ ] **AC16:** Integracao com `/buscar`: botao "Criar alerta com esses filtros" nos resultados de busca
  - Pre-preenche modal com filtros atuais da busca
- [ ] **AC17:** Preferencia de digest: "Receber 1 email consolidado" vs "1 email por alerta"

### Frontend — Notificacao In-App (Opcional)

- [ ] **AC18:** Badge de notificacao no header quando ha novos alertas nao vistos
- [ ] **AC19:** Dropdown de notificacoes com ultimos alertas disparados

### Metricas

- [ ] **AC20:** Prometheus metrics:
  - `smartlic_alerts_processed_total`
  - `smartlic_alerts_items_matched_total`
  - `smartlic_alerts_emails_sent_total`
  - `smartlic_alerts_processing_duration_seconds`

### Testes

- [ ] **AC21:** Testes para matcher (match, no-match, dedup, periodo)
- [ ] **AC22:** Testes para cron job (scheduling, rate limit, ALERTS_ENABLED flag)
- [ ] **AC23:** Testes para digest email template
- [ ] **AC24:** Testes frontend (CRUD UI, criar alerta, preview)
- [ ] **AC25:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Alert CRUD routes | `backend/routes/alerts.py` | Existe |
| Alert models | `backend/routes/alerts.py:42-91` | Existe |
| Unsubscribe (HMAC) | `backend/routes/alerts.py:98` | Existe |
| MAX_ALERTS_PER_USER | `backend/routes/alerts.py:35` (20) | Existe |
| ALERTS_ENABLED flag | `backend/config.py` | Existe |
| ALERTS_HOUR_UTC | `backend/config.py` (11 = 08:00 BRT) | Existe |
| Alert digest template | `backend/templates/emails/alert_digest.py` | Existe (basico) |
| Email service | `backend/email_service.py` | Existe |
| Filter logic | `backend/filter.py` | Existe (reutilizar) |
| ARQ queue | `backend/job_queue.py` | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/services/alert_matcher.py`
- `backend/tests/test_alert_matcher.py`
- `frontend/app/conta/components/AlertsSection.tsx`
- `frontend/app/conta/components/CreateAlertModal.tsx`
- `frontend/__tests__/alerts/alerts-ui.test.tsx`
- `supabase/migrations/XXXXXXXX_add_alert_sent_items.sql`
- `supabase/migrations/XXXXXXXX_add_alert_runs.sql`

**Modificados:**
- `backend/cron_jobs.py`
- `backend/routes/alerts.py` (adicionar preview)
- `backend/metrics.py`
- `frontend/app/conta/page.tsx` (secao alertas)
- `frontend/app/buscar/components/SearchResults.tsx` (botao "criar alerta")

## Dependencias

- STORY-310 (trial emails) — compartilha infra de cron/ARQ
- Alert CRUD routes precisam estar testadas end-to-end

## Riscos

- Matching pode ser pesado (muitos alertas x muitos editais) — batch + timeout necessario
- Rate limit de fontes PNCP/PCP se matching fizer queries reais (considerar usar cache L2)
- Spam: limitar max 1 digest/dia por usuario
