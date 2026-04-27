# MON-FN-014: Onboarding Tracking Server-Side (Deprecate localStorage)

**Priority:** P1
**Effort:** S (1 dia)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 3 (13–19/mai)
**Sprint Window:** Sprint 3 (depende de MON-FN-006)
**Dependências bloqueadoras:** MON-FN-006 (`first_search` server-side event + `profiles.first_search_at` column)

---

## Contexto

Hoje onboarding completion é tracked **apenas client-side** via `localStorage.smartlic_onboarding_completed` flag em `frontend/components/GuidedTour.tsx` (Shepherd.js). Problemas:
- localStorage é per-device — user em mobile + desktop tem flags diferentes (mostra onboarding 2x)
- Limpa cache → flag perdida → re-mostra onboarding (confusão)
- Modo incógnito → flag never persists → re-show every session
- Backend não sabe se user completou onboarding → impossível segmentar funnel "onboarded but not converted"
- Source de verdade fragmentada: localStorage no cliente, Mixpanel pelo lado, DB ausente

MON-FN-006 já adicionou `profiles.first_search_at` + emit server-side `first_search` event. Esta story aproveita: **server-side `first_search_at` é a source of truth real para onboarding completion**. localStorage flag mantida 30d para compatibility, depois removida.

**Por que P1:** elimina friction UX (user vê onboarding 2x em diferentes devices) + permite segmentação backend "completou onboarding sim/não". S effort, alta alavancagem.

**Paths críticos:**
- `frontend/components/GuidedTour.tsx` (Shepherd.js)
- `frontend/app/buscar/page.tsx` (consumer do flag)
- `backend/routes/user.py::get_me` (retornar `first_search_at`)
- `frontend/app/api/me/route.ts` (proxy)

---

## Acceptance Criteria

### AC1: Backend `/me` retorna `first_search_at` + `onboarded`

Given que server-side é source of truth,
When frontend pede `/me`,
Then response inclui `first_search_at` (datetime) + `onboarded` (bool).

- [ ] Em `backend/routes/user.py::get_me`:
```python
@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    sb = get_supabase()
    profile = sb.table("profiles").select("*").eq("id", user["id"]).single().execute()
    if not profile.data:
        raise HTTPException(404, "Profile not found")

    p = profile.data
    return {
        "id": p["id"],
        "email": p["email"],
        "name": p.get("name"),
        "plan_type": p["plan_type"],
        "trial_expires_at": p.get("trial_expires_at"),
        "first_search_at": p.get("first_search_at"),
        "onboarded": p.get("first_search_at") is not None,  # MON-FN-014
        # ... existing fields ...
    }
```
- [ ] Update Pydantic response schema `MeResponse` com novos fields
- [ ] Regenerate `frontend/app/api-types.generated.ts` via `npm run generate:api-types` (CLAUDE.md convention)

### AC2: Frontend lê `onboarded` do `/me` em vez de localStorage

Given user loga,
When frontend valida onboarding state,
Then `/me.onboarded` é primary source; localStorage é fallback durante migration.

- [ ] Em `frontend/components/GuidedTour.tsx`:
```typescript
import { useEffect, useState } from "react";

export function GuidedTour() {
  const [shouldShow, setShouldShow] = useState(false);

  useEffect(() => {
    async function checkOnboarding() {
      try {
        const res = await fetch("/api/me", { cache: "no-store" });
        if (!res.ok) {
          // Fallback to localStorage during migration window (30d)
          const localFlag = localStorage.getItem("smartlic_onboarding_completed");
          setShouldShow(!localFlag);
          return;
        }
        const data = await res.json();
        // Server is source of truth
        setShouldShow(!data.onboarded);
      } catch (e) {
        // Network error — fallback
        const localFlag = localStorage.getItem("smartlic_onboarding_completed");
        setShouldShow(!localFlag);
      }
    }
    checkOnboarding();
  }, []);

  // ... existing Shepherd.js init ...
}
```
- [ ] Mantém `localStorage.smartlic_onboarding_completed` writes pelos próximos 30 dias (compat para users que ainda não disparam first_search server-side por algum motivo)
- [ ] Após 30 dias (sprint futura), remove localStorage logic completamente
- [ ] Edge case: user com first_search_at SET mas localStorage cleared → server-side wins (não re-show onboarding) ✓
- [ ] Edge case: user sem first_search_at + localStorage SET → mostra onboarding (server says not onboarded) → ⚠️ check com @ux-design-expert se quer respeitar localStorage como "user already saw it"

### AC3: Mixpanel `onboarding_completed` event consistente

Given que server-side first_search já emite event,
When user faz first_search,
Then frontend NÃO emite `onboarding_completed` duplicado.

- [ ] Remover `mixpanel.track("onboarding_completed")` do `GuidedTour.tsx` (já era inconsistente entre devices)
- [ ] Backend emit `first_search` (MON-FN-006) é authoritative
- [ ] Mixpanel funnel definition: `signup_completed → first_search` (skip onboarding_completed que era client-side noise)
- [ ] Adicionar event `tour_finished` (frontend, optional) para tracking interação Shepherd specifically — separado de "onboarding completed" sense

### AC4: Migration handling — usuários existentes

Given que existem users hoje SEM `first_search_at` mas que JÁ fizeram busca antes da story,
When story deploy,
Then backfill `first_search_at` baseado em `search_sessions` history.

- [ ] Script SQL one-time `supabase/migrations/YYYYMMDDHHMMSS_backfill_first_search_at.sql`:
```sql
-- Backfill first_search_at from earliest search_sessions row per user
UPDATE public.profiles p
SET first_search_at = ss.first_search
FROM (
  SELECT user_id, MIN(created_at) AS first_search
  FROM public.search_sessions
  WHERE user_id IS NOT NULL
  GROUP BY user_id
) ss
WHERE p.id = ss.user_id
  AND p.first_search_at IS NULL;
```
- [ ] Migration paired down (`UPDATE ... SET first_search_at = NULL WHERE first_search_at IS NOT NULL` é destructive — preferir não-reversal e documentar)
- [ ] Validar: COUNT users com first_search_at NULL pós-backfill → only truly never-searched users
- [ ] Não emitir Mixpanel events em backfill (eventos retroativos confundem analytics)

### AC5: Endpoint admin para forçar reset onboarding (debug)

Given que support pode precisar resetar para test,
When `POST /v1/admin/users/{user_id}/reset-onboarding`,
Then `first_search_at = NULL` (próxima busca emite first_search again).

- [ ] Endpoint admin-only (existing `require_admin`):
```python
@router.post("/v1/admin/users/{user_id}/reset-onboarding")
async def reset_onboarding(
    user_id: str,
    user: User = Depends(require_admin),
):
    sb = get_supabase()
    sb.table("profiles").update({"first_search_at": None}).eq("id", user_id).execute()
    return {"status": "reset", "user_id": user_id}
```
- [ ] Audit log em `admin_actions` ou similar
- [ ] Mixpanel event `admin_action_reset_onboarding` (admin debug tracking)

### AC6: Métricas

- [ ] Counter `smartlic_onboarding_completion_rate_total{state}` (completed | not_completed) — atualizado em /me reads
- [ ] Funnel Mixpanel já cobre via `signup_completed → first_search`

### AC7: Testes

- [ ] Unit `backend/tests/routes/test_get_me_onboarded.py`:
  - [ ] User com first_search_at → onboarded=true
  - [ ] User sem first_search_at → onboarded=false
- [ ] Integration `backend/tests/migrations/test_backfill_first_search_at.py`:
  - [ ] Seed users + search_sessions → run migration → assert `first_search_at` populated correctly
  - [ ] User sem search_sessions → `first_search_at` permanece NULL
- [ ] Frontend `frontend/__tests__/GuidedTour.test.tsx`:
  - [ ] `/me.onboarded=true` → não show onboarding
  - [ ] `/me.onboarded=false` + localStorage SET → ainda show? (UX decision; default: respeitar server)
  - [ ] `/me` fetch fail → fallback to localStorage
  - [ ] No localStorage + no /me → show onboarding (default)
- [ ] E2E Playwright:
  - [ ] User signup → first /buscar → assert `first_search_at` set in DB
  - [ ] Re-load /buscar → onboarding NÃO aparece (server says onboarded)
  - [ ] Logout + login em outro device → onboarding NÃO aparece (server consistency)
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- `/me` retorna `first_search_at` + `onboarded`
- Frontend GuidedTour lê `/me.onboarded` primary
- Backfill migration para users existentes
- Endpoint admin reset
- localStorage fallback 30d (compat)
- Métricas

**OUT:**
- Refactor completo Shepherd.js init
- Multi-step onboarding tracking (current is binary: did/didn't first_search)
- Onboarding completion via outros eventos (e.g., adicionou setor, viu primeiro resultado) — futuro
- Cross-device sync de onboarding _progress_ (apenas estado final)
- Email re-engagement para users não-onboarded (futuro lifecycle)

---

## Definition of Done

- [ ] Backend `/me` retorna `onboarded` field
- [ ] Frontend types regenerados (`api-types.generated.ts`)
- [ ] GuidedTour usa `/me.onboarded` primary
- [ ] Backfill migration executada em prod (validar COUNT esperado)
- [ ] localStorage fallback documentado com TODO de remoção em 30d
- [ ] Endpoint admin reset funcional
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] E2E Playwright valida cross-device consistency (signup → 2 browsers)
- [ ] Mixpanel funnel atualizado (remove `onboarding_completed` se ainda em definição)
- [ ] Memory existente complementada: "MON-FN-014 deprecated localStorage onboarding flag"

---

## Dev Notes

### Padrões existentes a reutilizar

- **`profiles.first_search_at`:** column já adicionada por MON-FN-006
- **Pydantic `MeResponse`:** existente em `backend/schemas/`
- **API types regen:** `npm --prefix frontend run generate:api-types` (CLAUDE.md)
- **Shepherd.js:** existing in GuidedTour.tsx
- **`require_admin`:** auth dep existente

### Funções afetadas

- `backend/routes/user.py::get_me` (adicionar campos)
- `backend/schemas/user.py` (response model)
- `frontend/components/GuidedTour.tsx` (refactor)
- `frontend/app/api-types.generated.ts` (regen)
- `backend/routes/admin.py` (endpoint reset)
- `supabase/migrations/YYYYMMDDHHMMSS_backfill_first_search_at.sql` (no down — preserve backfill)

### Testing Standards

- Backend tests usam `app.dependency_overrides[require_auth]` (CLAUDE.md)
- Frontend tests com MSW para mock /me
- Playwright E2E em CI (ja existente)
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Backfill migration timeout em prod (search_sessions table grande?)
- Frontend onboarding aparecendo erroneamente para users existentes (backfill incompleto)
- `/me` performance degrada (single field add — improvável)

### Ações de rollback
1. **Imediato:** revert PR; localStorage logic volta a ser primary
2. **Backfill rollback:** SQL `UPDATE profiles SET first_search_at = NULL WHERE ...` (mas perde data — preferir não-reversal)
3. **Frontend-only revert:** flip flag `USE_SERVER_ONBOARDING=false` (env var Next.js public) — fallback localStorage

### Compliance
- `first_search_at` é metadata (não PII direta) — incluir em LGPD export (MON-FN-010)
- ON DELETE CASCADE da `profiles` cuida automaticamente

---

## Dependencies

### Entrada
- **MON-FN-006** (eventos funil): `first_search` event + column populada
- Search session data (existente, populated por buscar handler)

### Saída
- Funnel Mixpanel mais limpo (remove client-side onboarding_completed noise)
- Lifecycle marketing (futuro): segment "onboarded but not converted" precisa server-side flag
- Frontend type safety melhor (apenas server source)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO (conditional)
**Score:** 7/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Onboarding Tracking Server-Side (Deprecate localStorage)" |
| 2 | Complete description | Y | Problemas localStorage enumerados (per-device, incógnito, cache) |
| 3 | Testable acceptance criteria | Y | 7 ACs incluindo cross-device consistency E2E + backfill validation |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui multi-step + lifecycle marketing |
| 5 | Dependencies mapped | Y | Entrada MON-FN-006 (`first_search_at` column) |
| 6 | Complexity estimate | Y | S (1 dia) coerente — campo + frontend swap + backfill |
| 7 | Business value | Y | "User vê onboarding 2x diferentes devices" — friction concrete |
| 8 | Risks documented | Y | Backfill timeout em prod + frontend incorretamente mostrando onboarding |
| 9 | Criteria of Done | Y | E2E cross-device validation + types regen + memory complementada |
| 10 | Alignment with PRD/Epic | Y | EPIC sprint 3; reaproveita MON-FN-006 column |

### Required Fixes (CONDITIONAL — para @dev resolver durante implementation)

- [ ] **Migration `.down.sql` pareado obrigatório (CLAUDE.md STORY-6.2 / migration-gate.yml CI):** AC4 declara explicitamente `(no down — preserve backfill)` mas `migration-gate.yml` BLOCK merge se ausente. Solução: criar `YYYYMMDDHHMMSS_backfill_first_search_at.down.sql` como **no-op** com comentário:
  ```sql
  -- No-op rollback: backfill é informacional/idempotente.
  -- Reverter setaria first_search_at=NULL perdendo dados; preferir deixar como está.
  -- This file exists to satisfy migration-gate.yml STORY-6.2 convention.
  SELECT 1;
  ```
- [ ] Validar migration-gate.yml passa antes de merge

### Observations
- Score 7 reflete o gap concreto na convenção `.down.sql` (CI blocker), não falta de conceitual quality
- AC4 reconhece migration "destructive" mas decide "preferir não-reversal" — correto, mas precisa shipping no-op file para CI gate
- Pattern allow-list extensível (server primary + localStorage 30d compat) é resilient
- Pydantic `MeResponse` regen via `npm run generate:api-types` (CLAUDE.md convention) em DoD
- Endpoint admin reset com Mixpanel event tracking
- Edge case AC2 levanta UX decision (server says not onboarded + localStorage SET) — requer @ux-design-expert review durante implementation; default "respeitar server" é razoável

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — server-side onboarding tracking | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO conditional (7/10). Required fix: `.down.sql` no-op pareado (migration-gate.yml CI gate). Status Draft → Ready com fix obrigatório pre-merge. | @po (Pax) |
