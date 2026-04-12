# STORY-445: Notificação In-App de Novas Oportunidades

**Priority:** P1 — Cria hábito de retorno diário
**Effort:** M (4 dias)
**Squad:** @dev + @qa
**Status:** Ready
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
- [ ] Badge no header/navbar mostrando "X novos" quando há editais novos relevantes para o perfil do usuário
- [ ] Badge só aparece se count > 0
- [ ] Badge some após usuário fazer uma busca (limpa o estado)
- [ ] Badge aparece para trial E pagantes

### AC2: Backend — cron job de detecção diária
- [ ] Novo arquivo `backend/jobs/cron/new_bids_notifier.py` (ou job em `notifications.py`)
- [ ] Executa 1x/dia após a ingestão matinal (sugestão: 9h BRT = 12h UTC)
- [ ] Para cada usuário com `profile_context` configurado (setor + UFs):
  - Query: `SELECT COUNT(*) FROM pncp_raw_bids WHERE created_at > NOW() - INTERVAL '24 hours' AND [filtros do perfil]`
  - Se count > 0: salvar em Redis `new_bids_count:{user_id}` = count (TTL: 26h)
- [ ] Não processar usuários com trial expirado ou sem setor configurado

### AC3: Backend — endpoint de contagem
- [ ] Novo endpoint `GET /v1/notifications/new-bids-count`
- [ ] Retorna: `{ "count": N }` (lê de Redis)
- [ ] Autenticado (Bearer token)
- [ ] Se Redis key não existe: retorna `{ "count": 0 }`

### AC4: Frontend — proxy e fetch
- [ ] Novo proxy `frontend/app/api/new-bids-count/route.ts` → backend `/v1/notifications/new-bids-count`
- [ ] Fetch feito no header/navbar com polling a cada 30 minutos (não em tempo real)
- [ ] Cache via SWR com `revalidateOnFocus: true`

### AC5: Limpar badge após busca
- [ ] Quando usuário executa uma busca (`POST /buscar`): backend deleta Redis key `new_bids_count:{user_id}`
- [ ] Frontend: invalidar cache do SWR do badge após busca bem-sucedida

### AC6: Condicional por perfil
- [ ] Se usuário não tem setor configurado em `profile_context`: badge NÃO é exibido (sem perfil = sem relevância)
- [ ] Se Redis key não existe (usuário novo ou já viu): badge não aparece

### AC7: Funcional para trial e pagantes
- [ ] Badge funciona independente de `plan_type`
- [ ] Apenas trial expirado e não autenticado ficam fora

### AC8: Testes
- [ ] Teste backend: query retorna 5 editais novos → Redis salvo com `new_bids_count:{id}` = 5
- [ ] Teste backend: GET /new-bids-count → `{ count: 5 }`
- [ ] Teste backend: após POST /buscar → Redis key deletada
- [ ] Teste frontend: badge visível com count > 0
- [ ] Teste frontend: badge não visível com count = 0
- [ ] Teste frontend: badge não visível sem perfil configurado

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

- [ ] `backend/jobs/cron/new_bids_notifier.py` — AC2: novo cron job
- [ ] `backend/routes/notifications.py` — AC3: novo endpoint (ou estender existente)
- [ ] `frontend/components/NewBidsNotificationBadge.tsx` — AC1: badge no header
- [ ] `frontend/app/api/new-bids-count/route.ts` — AC4: proxy
- [ ] `frontend/components/Navbar.tsx` (ou Header.tsx) — AC1: integrar badge
- [ ] `backend/tests/test_new_bids_notifier.py` — AC8: testes de backend
- [ ] `frontend/__tests__/NewBidsNotificationBadge.test.tsx` — AC8: testes frontend

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
