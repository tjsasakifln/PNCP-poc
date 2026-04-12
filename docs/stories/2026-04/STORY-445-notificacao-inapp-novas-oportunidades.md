# STORY-445: Notificação In-App de Novas Oportunidades

**Priority:** P1 — Cria hábito de retorno diário
**Effort:** M (4 dias)
**Squad:** @dev + @qa
**Status:** Done
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 3 — Semanas 5-8

---

## Contexto

Não existe nenhum mecanismo de notificação in-app. O usuário só vê novas oportunidades se fizer uma busca manualmente. O datalake `pncp_raw_bids` é atualizado 3x/dia — é possível detectar novos editais relevantes para o perfil salvo do usuário e surfacear isso no header sem exigir nova busca.

O objetivo é criar uma razão diária para o usuário retornar ao produto — o hábito de retorno é o maior preditor de conversão em SaaS B2B.

**Impacto estimado:** +1pp em trial-to-paid conversion (via aumento de DAU e hábito de retorno).

---

## Acceptance Criteria

### AC1: Badge no header com contagem de novos editais
- [x] Badge no header/navbar mostrando "X novos" quando há editais novos relevantes para o perfil do usuário
- [x] Badge só aparece se count > 0
- [x] Badge some após usuário fazer uma busca (limpa o estado)
- [x] Badge aparece para trial E pagantes

### AC2: Backend — cron job de detecção diária
- [x] Novo arquivo `backend/jobs/cron/new_bids_notifier.py` (ou job em `notifications.py`)
- [x] Executa 1x/dia após a ingestão matinal (sugestão: 9h BRT = 12h UTC)
- [x] Para cada usuário com `profile_context` configurado (setor + UFs):
  - Query: `SELECT COUNT(*) FROM pncp_raw_bids WHERE created_at > NOW() - INTERVAL '24 hours' AND [filtros do perfil]`
  - Se count > 0: salvar em Redis `new_bids_count:{user_id}` = count (TTL: 26h)
- [x] Não processar usuários com trial expirado ou sem setor configurado

### AC3: Backend — endpoint de contagem
- [x] Novo endpoint `GET /v1/notifications/new-bids-count`
- [x] Retorna: `{ "count": N }` (lê de Redis)
- [x] Autenticado (Bearer token)
- [x] Se Redis key não existe: retorna `{ "count": 0 }`

### AC4: Frontend — proxy e fetch
- [x] Novo proxy `frontend/app/api/new-bids-count/route.ts` → backend `/v1/notifications/new-bids-count`
- [x] Fetch feito no header/navbar com polling a cada 30 minutos (não em tempo real)
- [x] Cache via SWR com `revalidateOnFocus: true`

### AC5: Limpar badge após busca
- [x] Quando usuário executa uma busca (`POST /buscar`): backend deleta Redis key `new_bids_count:{user_id}`
- [x] Frontend: invalidar cache do SWR do badge após busca bem-sucedida

### AC6: Condicional por perfil
- [x] Se usuário não tem setor configurado em `profile_context`: badge NÃO é exibido (sem perfil = sem relevância)
- [x] Se Redis key não existe (usuário novo ou já viu): badge não aparece

### AC7: Funcional para trial e pagantes
- [x] Badge funciona independente de `plan_type`
- [x] Apenas trial expirado e não autenticado ficam fora

### AC8: Testes
- [x] Teste backend: query retorna 5 editais novos → Redis salvo com `new_bids_count:{id}` = 5
- [x] Teste backend: GET /new-bids-count → `{ count: 5 }`
- [x] Teste backend: após POST /buscar → Redis key deletada
- [x] Teste frontend: badge visível com count > 0
- [x] Teste frontend: badge não visível com count = 0
- [x] Teste frontend: badge não visível sem perfil configurado

---

## Scope

**IN:**
- Cron job de detecção diária
- Redis para armazenar contagem por usuário
- Endpoint `/v1/notifications/new-bids-count`
- Badge no header
- Proxy no frontend
- Limpeza após busca

**OUT:**
- Push notifications (browser/mobile)
- Email de notificação (→ STORY-444 parcialmente cobre)
- Notificação por WhatsApp/Telegram
- Notificação em tempo real (SSE/WebSocket)
- Configuração de frequência pelo usuário

---

## Dependencies

- Redis disponível (Upstash/Railway — já configurado)
- `profile_context` salvo com setor e UFs (onboarding garante isso)
- Ingestão diária do PNCP (cron de 9h BRT) deve estar funcionando para dados serem frescos
- `pncp_raw_bids` com campo `created_at` e campos de setor/UF

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Filtro por setor em `pncp_raw_bids` é complexo (usa keywords, não campo direto) | Alta | Simplificar: usar campo `uf` + keywords básicas do setor (não classificação IA completa); count aproximado é suficiente para o badge |
| Redis TTL expirar antes do usuário logar | Baixa | TTL de 26h (cobre 1 dia completo + margem); cron reinicia a cada dia |
| Performance do cron job com muitos usuários | Média | Processar em batches (100 usuários/vez), adicionar rate limiting interno |

---

## File List

- [x] `backend/jobs/cron/new_bids_notifier.py` — AC2: novo cron job
- [x] `backend/routes/notifications.py` — AC3: novo endpoint (ou estender existente)
- [x] `frontend/components/NewBidsNotificationBadge.tsx` — AC1: badge no header
- [x] `frontend/app/api/new-bids-count/route.ts` — AC4: proxy
- [x] `frontend/components/Navbar.tsx` (ou Header.tsx) — AC1: integrar badge
- [x] `backend/tests/test_new_bids_notifier.py` — AC8: testes de backend
- [x] `frontend/__tests__/NewBidsNotificationBadge.test.tsx` — AC8: testes frontend

---

## Dev Notes

- Filtro simplificado para o cron (não usa classificação IA — apenas keywords básicas):
  ```sql
  SELECT COUNT(*) FROM pncp_raw_bids 
  WHERE created_at > NOW() - INTERVAL '24 hours'
  AND uf = ANY(:ufs)
  AND (titulo ILIKE ANY(ARRAY[:%keyword1%, :%keyword2%]))
  ```
- Keywords do setor: pegar as primeiras 5 de `sectors_data.yaml` para o setor do usuário
- Navbar atual: verificar se é `Navbar.tsx` ou `Header.tsx` e onde está o espaço para o badge
- SWR revalidação: `{ refreshInterval: 1800000 }` (30 minutos em ms)

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +1pp |
| 2026-04-12 | @dev | Implementação completa: cron new_bids_notifier, endpoint GET/DELETE /v1/notifications/new-bids-count, NewBidsNotificationBadge, proxy, integração PageHeader + buscar/page. 14 testes passando. |
