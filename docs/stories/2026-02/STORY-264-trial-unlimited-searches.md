# STORY-264 — Trial Sem Fricção: Acesso Completo por 7 Dias

**Status:** TODO
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

- [ ] **AC1**: `PLAN_CAPABILITIES["free_trial"]["max_requests_per_month"]` alterado de `3` para `1000` (mesmo do smartlic_pro)
- [ ] **AC2**: `PLAN_CAPABILITIES["free_trial"]["max_requests_per_min"]` mantido em `2` (rate limit por minuto continua como proteção anti-abuso)
- [ ] **AC3**: Todas as demais capabilities do free_trial permanecem iguais ao smartlic_pro (já estão: allow_excel, allow_pipeline, max_history_days, max_summary_tokens, priority)
- [ ] **AC4**: Constante `TRIAL_DURATION_DAYS = 7` criada em config.py (centralizar o valor que hoje está implícito)

### Backend (trial-status endpoint)

- [ ] **AC5**: `GET /v1/me/trial-status` → campo `searches_limit` reflete o novo limite (1000)
- [ ] **AC6**: Endpoint retorna campo adicional `plan_features: list[str]` com as features disponíveis (ex: `["busca_ilimitada", "excel_export", "pipeline", "ia_resumo"]`) para o frontend poder comunicar

### Frontend

- [ ] **AC7**: `TrialCountdown.tsx` — Texto atualizado de "X dia(s) restante(s) no trial" para "X dia(s) de acesso completo"
- [ ] **AC8**: `TrialExpiringBanner.tsx` — Atualizar copy para enfatizar que o acesso completo vai acabar (não apenas "trial expira")
- [ ] **AC9**: Remover qualquer indicador de "X/3 buscas" no frontend (TrialConversionScreen mostra `searches_used/3`)
- [ ] **AC10**: Se existir barra de progresso de quota no trial, remover ou ocultar durante o período de trial ativo

### Testes

- [ ] **AC11**: Testes em `test_quota.py` atualizados para refletir novo limite de 1000 buscas no trial
- [ ] **AC12**: Teste que valida que trial com 50 buscas NÃO é bloqueado (regressão do limite antigo)
- [ ] **AC13**: Teste que valida que trial expirado continua bloqueando (independente de quantas buscas restam)
- [ ] **AC14**: Testes frontend atualizados (trial-components.test.tsx)

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
| `backend/tests/test_quota.py` | Atualizar testes de limite |
| `backend/tests/test_trial_endpoints.py` | Atualizar assertions |
| `frontend/app/components/TrialCountdown.tsx` | Atualizar copy |
| `frontend/app/components/TrialExpiringBanner.tsx` | Atualizar copy |
| `frontend/app/components/TrialConversionScreen.tsx` | Remover "X/3 buscas" |
| `frontend/__tests__/trial-components.test.tsx` | Atualizar testes |
