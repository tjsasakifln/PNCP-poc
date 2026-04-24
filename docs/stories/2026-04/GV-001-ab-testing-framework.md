# GV-001: A/B Testing Framework + Funnel Auto-Tracking

**Priority:** P0 (bloqueia medição de todas stories do epic)
**Effort:** M (8 SP, 3-4 dias)
**Squad:** @dev + @devops + @data-engineer
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 1

---

## Contexto

SmartLic já tem Mixpanel (`frontend/hooks/useAnalytics.ts`), Clarity, GA4 e UTM capture (STORY-219). Falta:

1. **A/B testing framework** — hoje toda story lança sem variant routing; não consegue medir impacto isolado
2. **Funnel auto-tracking** — eventos espalhados manualmente; não há emissão automática em pontos chave

Sem GV-001, as 20 stories do epic não terão medição confiável. É blocker crítico de Sprint 1.

---

## Acceptance Criteria

### AC1: Feature flag + variant router client-side

- [ ] `frontend/lib/experiments.ts` exporta:
  - `getVariant(experimentKey: string, userId?: string): string | null`
  - Assignment determinístico via hash `sha256(userId + experimentKey) % 100` mapeando para variants configuradas
  - Fallback para anonymous users usando localStorage-persisted UUID
- [ ] `frontend/hooks/useExperiment.ts`:
  - `useExperiment(key: string)` → retorna `{ variant, isLoading, exposed }`
  - Emite `$experiment_exposure` Mixpanel event automaticamente no primeiro render (SDK convention)
- [ ] Configuração de experiments em `frontend/config/experiments.ts` (TypeScript const):
  ```ts
  export const EXPERIMENTS = {
    gv_002_watermark_copy: { variants: ['control', 'urgency', 'social'], split: [34, 33, 33], enabled: true },
    // ...
  } as const
  ```

### AC2: Persistência de assignment cross-session

- [ ] Backend endpoint `POST /v1/experiments/assign` persiste assignment por `(user_id, experiment_key)` na tabela `user_experiments`
- [ ] Client-side cacheia assignment no localStorage (key: `smartlic_exp_{experiment_key}`)
- [ ] Assignment uma vez atribuído NUNCA muda (determinístico)
- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_user_experiments.sql`:
  ```sql
  CREATE TABLE user_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    anon_id TEXT,
    experiment_key TEXT NOT NULL,
    variant TEXT NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, experiment_key),
    UNIQUE(anon_id, experiment_key)
  );
  ALTER TABLE user_experiments ENABLE ROW LEVEL SECURITY;
  ```
  Down migration obrigatório.

### AC3: Funnel auto-emission em eventos chave

- [ ] Estender `frontend/lib/mixpanel.ts` com `trackFunnelStep(stepName, properties?)` que:
  - Adiciona `funnel_step` e `funnel_timestamp` super properties
  - Emite com session_id e user_id canonical
- [ ] Auto-emitir nos pontos:
  - `funnel.signup_started` (signup page mount)
  - `funnel.signup_completed` (após success)
  - `funnel.onboarding_step_N` (N=1,2,3)
  - `funnel.onboarding_completed`
  - `funnel.first_search_started` / `funnel.first_search_completed`
  - `funnel.first_relevant_result` (resultados ≥ 3 relevantes)
  - `funnel.checkout_started` / `funnel.checkout_completed`
  - `funnel.share_initiated` / `funnel.share_completed`
  - `funnel.invite_sent` / `funnel.invite_accepted`

### AC4: Admin dashboard para experiments

- [ ] `frontend/app/admin/experiments/page.tsx` (requires `is_admin`):
  - Lista experiments ativos com split %, # de exposições, conversão por variant
  - Export CSV dos dados raw
  - Kill switch toggle (desabilita experiment — força todos para control)
- [ ] Backend `GET /v1/admin/experiments/stats?key=<experiment_key>` retorna agregados
- [ ] Quality gate: não mostrar vencedor até N mínimo de exposições (configurable, default 1000)

### AC5: Testes

- [ ] Unit `frontend/__tests__/lib/experiments.test.ts`:
  - Assignment determinístico (mesmo input = mesmo output)
  - Split respeita percentual configurado (±1% sobre 100k iterações)
  - Fallback para anon user funciona
- [ ] Integration `backend/tests/test_experiments_api.py`:
  - POST /assign retorna 200 + variant
  - GET /stats retorna agregados corretos
  - RLS impede user ver assignments de outros
- [ ] E2E Playwright: user entra, recebe variant, fecha browser, reabre, mesma variant

---

## Scope

**IN:**
- Framework TS client-side + hook React
- Endpoint backend + tabela RLS
- 3 experiments de exemplo cadastrados (usados em GV-002, GV-015, GV-018)
- Admin dashboard básico
- Funnel auto-tracking helpers

**OUT:**
- Multivariate testing (MVT) — v2
- Feature flag UI para criar experiments em runtime — v2
- Bayesian stats / sequential testing — v2 (usar simple z-test inicialmente)
- Server-side rendering variant (SSR) — v2

---

## Dependências

- **Nenhuma** externa. Bloqueia GV-002 até GV-021 (medição).

---

## Riscos

- **Assignment leak via timing:** experiment_key não deve expor intenção (usar slugs opacos ex `exp_a4f2`). Mitigação: não codar na frontend tags semânticas.
- **Cache localStorage desatualizado:** se experiment config mudar, variant cached pode ficar stale. Mitigação: `experiments.ts` export tem `configVersion` — bumpar invalida cache.
- **RLS wrong on user_experiments:** user poderia ver assignments de outros. Mitigação: teste RLS explícito.

---

## Arquivos Impactados

### Novos
- `frontend/lib/experiments.ts`
- `frontend/hooks/useExperiment.ts`
- `frontend/config/experiments.ts`
- `frontend/app/admin/experiments/page.tsx`
- `backend/routes/experiments.py`
- `supabase/migrations/YYYYMMDDHHMMSS_user_experiments.sql` (+ `.down.sql`)
- `frontend/__tests__/lib/experiments.test.ts`
- `backend/tests/test_experiments_api.py`

### Modificados
- `frontend/lib/mixpanel.ts` (+ `trackFunnelStep`)
- `frontend/hooks/useAnalytics.ts` (integra com experiments)
- `frontend/app/signup/page.tsx`, `onboarding/page.tsx`, `buscar/page.tsx` (emitir funnel events)

---

## Testing Strategy

1. **Unit tests** AC5 unit section
2. **Load test** `/v1/experiments/assign` — p95 <50ms sob 500 req/s (será chamado em todo page mount)
3. **Correctness:** simular 10k assignments, verificar distribuição ~33/33/33 para 3-way split
4. **E2E Playwright:** full funnel (signup → onboarding → busca → share) com assignment persistente

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada como infra bloqueadora do EPIC-GROWTH-VIRAL-2026-Q3 |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
