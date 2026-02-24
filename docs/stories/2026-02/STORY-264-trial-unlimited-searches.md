# STORY-264 — Trial Sem Fricção: Acesso Completo por 7 Dias

**Status:** Done
**Sprint:** GTM-TRIAL
**Priority:** P0 — Conversão
**Estimate:** 3 SP
**Squad:** team-bidiq-backend + frontend

---

## Contexto

O trial atual de 7 dias limita o usuário a **3 buscas/mês** (`max_requests_per_month: 3` em `quota.py:67`). Essa fricção impede que o usuário explore o produto o suficiente para perceber valor e converter. Estratégia: dar acesso **completo e ilimitado** durante os 7 dias para maximizar engajamento e conversão.

## Objetivo

Remover o limite de buscas do trial, equiparando ao plano SmartLic Pro em todas as capabilities durante os 7 dias.

## Acceptance Criteria

### Backend (quota.py)

- [x] **AC1**: `PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"]` alterado de `3` para `1000` (mesmo do smartlic_pro)
- [x] **AC2**: `PLAN_CAPABILITIES["free_trial"]["max_requests_per_min"]` mantido em `2` (rate limit por minuto continua como proteção anti-abuso)
- [x] **AC3**: Todas as demais capabilities do free_trial permanecem iguais ao smartlic_pro (já estão: allow_excel, allow_pipeline, max_history_days, max_summary_tokens, priority)
- [x] **AC4**: Constante `TRIAL_DURATION_DAYS = 7` criada em config.py (centralizar o valor que hoje está implícito)

### Backend (trial-status endpoint)

- [x] **AC5**: `GET /v1/me/trial-status` → campo `searches_limit` reflete o novo limite (1000)
- [x] **AC6**: Endpoint retorna campo adicional `plan_features: list[str]` com as features disponíveis (ex: `["busca_ilimitada", "excel_export", "pipeline", "ia_resumo"]`) para o frontend poder comunicar

### Frontend

- [x] **AC7**: `TrialCountdown.tsx` — Texto atualizado de "X dia(s) restante(s) no trial" para "X dia(s) de acesso completo"
- [x] **AC8**: `TrialExpiringBanner.tsx` — Atualizar copy para enfatizar que o acesso completo vai acabar (não apenas "trial expira")
- [x] **AC9**: Remover qualquer indicador de "X/3 buscas" no frontend (TrialConversionScreen mostra `searches_used/3`)
- [x] **AC10**: Se existir barra de progresso de quota no trial, remover ou ocultar durante o período de trial ativo

### Testes

- [x] **AC11**: Testes em `test_quota.py` atualizados para refletir novo limite de 1000 buscas no trial
- [x] **AC12**: Teste que valida que trial com 50 buscas NÃO é bloqueado (regressão do limite antigo)
- [x] **AC13**: Teste que valida que trial expirado continua bloqueando (independente de quantas buscas restam)
- [x] **AC14**: Testes frontend atualizados (trial-components.test.tsx)

---

## Notas Técnicas

- **Não alterar** a lógica de expiração por tempo (7 dias) — isso é responsabilidade da STORY-265
- O limite de 1000/mês é efetivamente "ilimitado" para 7 dias (impossível fazer 1000 buscas em uma semana)
- Manter rate limit por minuto (2/min) como proteção anti-abuso
- `check_quota()` em quota.py:565-733 — a lógica de expiração por data (L664-677) permanece intacta

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/quota.py` | Alterar max_requests_per_month de 3→1000 |
| `backend/config.py` | Adicionar TRIAL_DURATION_DAYS = 7 |
| `backend/routes/user.py` | Adicionar plan_features ao trial-status |
| `backend/tests/test_quota.py` | Atualizar testes de limite + 2 novos (AC12, AC13) |
| `backend/tests/test_trial_endpoints.py` | Atualizar assertions (searches_limit=1000, plan_features) |
| `backend/tests/test_plan_capabilities.py` | Atualizar assertions (max_requests_per_month=1000) |
| `backend/tests/test_admin.py` | Atualizar credits_remaining assertions (3→1000) |
| `backend/tests/snapshots/openapi_schema.json` | Regenerado (plan_features adicionado) |
| `frontend/app/components/TrialCountdown.tsx` | "de acesso completo" em vez de "restante(s)" |
| `frontend/app/components/TrialExpiringBanner.tsx` | "acesso completo termina" em vez de "expira" |
| `frontend/app/components/TrialConversionScreen.tsx` | Removido "/3" do searches_executed |
| `frontend/app/components/QuotaCounter.tsx` | Novo bloco isActiveTrial: "Acesso completo" sem progress bar |
| `frontend/hooks/useQuota.ts` | FREE_SEARCHES_LIMIT: 3→1000 |
| `frontend/__tests__/trial-components.test.tsx` | Atualizar copy assertions |
| `frontend/__tests__/QuotaCounter.test.tsx` | Atualizar trial display test |
| `frontend/__tests__/free-user-balance-deduction.test.tsx` | Atualizar creditsRemaining assertions |
