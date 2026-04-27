# MON-FN-004: Race Condition `/planos/obrigado` — Polling Client-Side

**Priority:** P0
**Effort:** M (2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 2 (06–12/mai)
**Sprint Window:** Sprint 2 (depende de MON-FN-003)
**Dependências bloqueadoras:** MON-FN-003 (invalidação atômica server-side antes de polling client-side)

---

## Contexto

`frontend/app/planos/obrigado/page.tsx` + `ObrigadoContent.tsx` é a tela pós-checkout Stripe success. Hoje a tela é renderizada imediatamente após Stripe Checkout success_url callback, **sem aguardar confirmação do webhook**. Resultado: usuário vê "Obrigado!" mas sua próxima request pode ainda hit `paywall_hit` porque `plan_type` ainda é `'free_trial'` no DB.

Sequência atual (race):
1. User completa Stripe Checkout → Stripe redireciona para `success_url=https://smartlic.tech/planos/obrigado?session_id=cs_xxx`
2. Webhook `checkout.session.completed` parte da Stripe ao mesmo tempo (paralelo)
3. `/planos/obrigado` renderiza imediatamente
4. User clica "Ir para painel" → request hit `/buscar` → backend ainda vê `plan_type='free_trial'` (webhook não terminou)
5. `quota/plan_auth.py:68` emite `paywall_hit` event → user vê erro "Trial expirado, faça upgrade" pós-pagamento

MON-FN-003 reduz a janela de stale cache de até 5min → <500ms via Pub/Sub. Mas mesmo 500ms é confusão UX. **Esta story adiciona polling client-side para confirmar `plan_type=paid` ANTES de liberar UI.**

**Por que P0:** UX falso positivo pós-pagamento é o pior momento de abandono — primeira impressão "pago e quebrado" gera ticket support + churn. Pre-revenue precisa cada conversão. Bloqueia MON-FN-008 (free tier) porque downsell paywall depende de status confiável.

**Paths críticos:**
- `frontend/app/planos/obrigado/page.tsx` (server component wrapper)
- `frontend/app/planos/obrigado/ObrigadoContent.tsx` (client component — tela atual)
- `frontend/app/api/me/route.ts` ou backend `GET /me` (endpoint polled)
- `backend/routes/user.py::get_me` (já retorna `plan_type` — verificar)

---

## Acceptance Criteria

### AC1: Hook `useCheckoutConfirmation` com polling

Given que user chegou em `/planos/obrigado?session_id=cs_xxx`,
When o componente montado,
Then dispara polling a cada 500ms para `GET /me` por até 30s OR até `plan_type !== 'free_trial'`.

- [ ] Novo `frontend/app/planos/obrigado/useCheckoutConfirmation.ts`:
```typescript
import { useState, useEffect, useRef } from "react";

type ConfirmationState = "polling" | "confirmed" | "timeout" | "error";

interface UseCheckoutConfirmationResult {
  state: ConfirmationState;
  planType: string | null;
  attemptCount: number;
  elapsedMs: number;
}

export function useCheckoutConfirmation(
  initialPlan: string,
  options: { intervalMs?: number; maxAttempts?: number } = {}
): UseCheckoutConfirmationResult {
  const intervalMs = options.intervalMs ?? 500;
  const maxAttempts = options.maxAttempts ?? 60; // 60 * 500ms = 30s
  const [state, setState] = useState<ConfirmationState>("polling");
  const [planType, setPlanType] = useState<string | null>(initialPlan);
  const [attemptCount, setAttemptCount] = useState(0);
  const startedAtRef = useRef(Date.now());

  useEffect(() => {
    if (initialPlan && initialPlan !== "free_trial") {
      setState("confirmed");
      return;
    }
    let attempts = 0;
    let cancelled = false;

    const tick = async () => {
      if (cancelled) return;
      attempts += 1;
      setAttemptCount(attempts);
      try {
        const res = await fetch("/api/me", { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setPlanType(data.plan_type);
        if (data.plan_type && data.plan_type !== "free_trial") {
          setState("confirmed");
          return;
        }
      } catch (err) {
        // Don't fail-fast; keep polling — webhook may still arrive
        console.warn("Polling /me failed:", err);
      }
      if (attempts >= maxAttempts) {
        setState("timeout");
        return;
      }
      setTimeout(tick, intervalMs);
    };

    tick();
    return () => {
      cancelled = true;
    };
  }, [initialPlan, intervalMs, maxAttempts]);

  return {
    state,
    planType,
    attemptCount,
    elapsedMs: Date.now() - startedAtRef.current,
  };
}
```
- [ ] Polling interval 500ms (configurável); max 60 attempts (30s total)
- [ ] Stop em sucesso (`plan_type !== 'free_trial'`) ou timeout
- [ ] AbortController para cancelar fetches em unmount
- [ ] Não retry-on-error infinito — registra em Sentry após 5 erros consecutivos

### AC2: UX states em `ObrigadoContent.tsx`

Given que polling estado pode ser polling|confirmed|timeout|error,
When cada estado,
Then UI mostra mensagem + visual apropriado.

- [ ] **State `polling` (0-30s):**
  - Spinner animado (Framer Motion)
  - Texto: "Confirmando seu pagamento..." (h1)
  - Subtexto: "Isso pode levar alguns segundos"
  - Botões "Ir para painel" desabilitados (graayed out) com tooltip "Aguardando confirmação"
  - Após 5s (10 attempts), mostrar "Quase lá... ⏳" para reduzir ansiedade
  - Mixpanel event `checkout_polling_started`
- [ ] **State `confirmed`:**
  - Animação success (checkmark verde, Framer Motion)
  - h1: "Pagamento confirmado!"
  - Subtexto: "Seu acesso foi liberado. Vamos começar?"
  - CTA primário "Ir para painel" → `/buscar` (navegação)
  - Mixpanel event `checkout_confirmed` com properties `{elapsed_ms, attempt_count, plan_type}`
- [ ] **State `timeout` (>30s sem confirmação):**
  - Ícone alert ⚠️ (não erro — é situação esperada raramente)
  - h1: "Pagamento em processamento"
  - Texto: "Estamos finalizando seu pagamento. Você receberá um email em até 5 minutos confirmando o acesso."
  - CTA secundário "Ver minha conta" → `/conta`
  - CTA "Falar com suporte" → mailto + Mixpanel event `checkout_timeout`
  - Não bloquear navegação; user pode prosseguir para painel mas pode ainda ver paywall (graceful)
- [ ] **State `error` (5+ erros consecutivos):**
  - Sentry capture com `session_id` (Stripe)
  - UI similar a timeout mas com texto "Estamos verificando seu pagamento..."

### AC3: Telemetria Mixpanel

Given que user completa fluxo,
When eventos disparam,
Then Mixpanel recebe granularidade por estágio (vai alimentar funnel MON-FN-006).

- [ ] Event `checkout_completed` (frontend) — disparado em mount com `{session_id, came_from: stripe_checkout}`
- [ ] Event `checkout_polling_started` — disparado em primeiro tick
- [ ] Event `checkout_confirmed` — disparado em state=confirmed; properties `{elapsed_ms, attempt_count, plan_type}`
- [ ] Event `checkout_timeout` — disparado em state=timeout; properties `{elapsed_ms: 30000, attempt_count: 60, last_known_plan_type}`
- [ ] Event `checkout_polling_error` — disparado a cada 5 erros consecutivos
- [ ] Properties incluem `stripe_session_id` mascarado (último 4 chars apenas: `cs_xxxx_LAST4`)

### AC4: Backend endpoint `/api/me` com cache-bypass header

Given que polling chama `/me` repetidamente,
When request,
Then backend retorna `plan_type` real-time (não cached) com header opt-out.

- [ ] Frontend envia `Cache-Control: no-store` header (já tem `cache: "no-store"` no fetch)
- [ ] Backend `GET /me` (`backend/routes/user.py::get_me`): após MON-FN-003, cache local `_plan_status_cache` é invalidado em <500ms via Pub/Sub. Polling lê DB direto se cache miss — OK.
- [ ] Verificar: rota `/me` não cacheia em CDN (header `Cache-Control: private, no-cache, no-store`)
- [ ] Rate limit: relaxado para `/me` quando user está autenticado e em fluxo de polling (heuristica: 60 req/min permitido se path == `/me` para autenticados)

### AC5: Server component wrapper

Given que `/planos/obrigado` é Next.js 16 App Router,
When user chega via redirect Stripe,
Then server component lê initial state (plan_type via SSR) e passa para client component.

- [ ] `frontend/app/planos/obrigado/page.tsx` (server component):
```typescript
import { redirect } from "next/navigation";
import { ObrigadoContent } from "./ObrigadoContent";

export const dynamic = "force-dynamic"; // sempre fresh
export const revalidate = 0;

export default async function ObrigadoPage({
  searchParams,
}: {
  searchParams: Promise<{ session_id?: string }>;
}) {
  const params = await searchParams;
  const sessionId = params.session_id;
  if (!sessionId) {
    redirect("/planos");
  }

  // SSR fetch initial /me — gives best-case immediate confirmed state
  const initialMe = await fetchInitialMe();

  return (
    <ObrigadoContent
      sessionId={sessionId}
      initialPlanType={initialMe?.plan_type ?? "free_trial"}
    />
  );
}
```
- [ ] Se SSR já retorna `plan_type=paid`, ObrigadoContent skip polling e vai direto para state=confirmed
- [ ] Polling só ativa se SSR retornou `'free_trial'` (graceful)
- [ ] Verificar `frontend/Dockerfile` ARG `BACKEND_URL` (memory `reference_frontend_dockerfile_backend_url_gap`) — se ausente, SSR fetch falha em build

### AC6: Edge cases

- [ ] Se `session_id` ausente/inválido na query → redirect `/planos`
- [ ] Se user não autenticado (sessão expirou durante checkout) → redirect `/login?return=/planos/obrigado?session_id=cs_xxx`
- [ ] Se webhook falhou (DLQ entry exhausted) → polling timeout 30s → mensagem "em processamento" + email automático após DLQ recovery
- [ ] Visibilidade: usar `document.visibilityState` para pausar polling em tab oculto (eficiência energia)
- [ ] Backoff em polling errors: 500ms → 1s → 2s → 5s (não martelar `/me` se backend devolver 5xx)

### AC7: Testes (unit + integration + E2E Playwright)

- [ ] Unit `frontend/__tests__/planos/obrigado/useCheckoutConfirmation.test.tsx`:
  - [ ] Polling resolve em `confirmed` quando `/me` retorna `plan_type='paid'`
  - [ ] Polling timeout em 30s se `/me` continua retornando `'free_trial'`
  - [ ] Initial plan já é `'paid'` → state confirmed imediato (sem polling)
  - [ ] AbortController cancela em unmount
  - [ ] Backoff em errors consecutivos
  - [ ] visibilityState=hidden pausa polling
- [ ] Integration `frontend/__tests__/planos/obrigado/ObrigadoContent.integration.tsx`:
  - [ ] Render em state polling → spinner visível, botões disabled
  - [ ] Render em state confirmed → checkmark + CTA habilitado
  - [ ] Render em state timeout → mensagem "em processamento"
  - [ ] MSW mock de `/me` simula transição free_trial → paid
- [ ] E2E Playwright `frontend/e2e-tests/checkout-obrigado-polling.spec.ts`:
  - [ ] Mock Stripe checkout success → land em `/planos/obrigado?session_id=cs_test_xxx`
  - [ ] Mock backend `/me` returna `'free_trial'` 3x, depois `'paid'` → assert UI transita para confirmed
  - [ ] Mock backend `/me` retorna sempre `'free_trial'` → assert UI mostra timeout após 30s
  - [ ] Verify Mixpanel events disparados (`checkout_confirmed`, `checkout_timeout`)
- [ ] Cobertura ≥85% em `useCheckoutConfirmation` + `ObrigadoContent`

---

## Scope

**IN:**
- Hook `useCheckoutConfirmation` com polling 500ms / max 30s
- 4 UI states: polling, confirmed, timeout, error
- Telemetria Mixpanel para cada estado
- SSR initial state via `/me` no server component
- Edge cases (visibilidade, backoff, session_id missing)
- E2E Playwright

**OUT:**
- Refactor backend `/me` endpoint (apenas relaxar rate limit)
- Server-Sent Events (over-engineering para 30s window; polling suficiente)
- Webhooks frontend-side (não há tal mecanismo)
- Mudanças em Stripe Checkout config (success_url já correto)
- Internationalização — pt-BR único
- Animação Lottie complexa (Framer Motion sufficient)

---

## Definition of Done

- [ ] Hook `useCheckoutConfirmation` implementado com tests
- [ ] 4 UI states implementados em `ObrigadoContent.tsx` com Framer Motion
- [ ] Mixpanel events `checkout_completed`, `checkout_polling_started`, `checkout_confirmed`, `checkout_timeout`, `checkout_polling_error` disparam
- [ ] E2E Playwright validando happy + timeout paths
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] Visual review @ux-design-expert (UI states aprovados)
- [ ] Smoke test em staging: Stripe Checkout test mode → assert polling resolve em <2s (após MON-FN-003 ativo)
- [ ] Rate limit relaxado para `/me` validado (60 req/min em fluxo polling)
- [ ] Rollback runbook documentado

---

## Dev Notes

### Padrões existentes a reutilizar

- **Framer Motion:** já usado em landing page; padrões em `frontend/components/Animations/*`
- **Mixpanel client:** `frontend/lib/mixpanel.ts` (existente)
- **Fetch wrapper:** `frontend/lib/api.ts` (com auth header automático)
- **Sentry:** `frontend/lib/sentry.ts` (capture exception com tags)

### Funções afetadas

- `frontend/app/planos/obrigado/page.tsx` (server component wrapper)
- `frontend/app/planos/obrigado/ObrigadoContent.tsx` (client component — refactor para usar hook)
- `frontend/app/planos/obrigado/useCheckoutConfirmation.ts` (NOVO)
- `frontend/__tests__/planos/obrigado/*` (NOVO tests)
- `frontend/e2e-tests/checkout-obrigado-polling.spec.ts` (NOVO E2E)
- `backend/routes/user.py::get_me` (verificar que não cacheia; Cache-Control header)
- Backend rate limit config — relaxar para `/me` em paths-list

### Testing Standards

- Jest + Testing Library para unit/integration
- MSW (Mock Service Worker) para mock `/me` em integration tests
- Playwright para E2E (already in suite)
- Mock Mixpanel via `__mocks__/mixpanel.ts`
- Anti-hang: `jest.useFakeTimers()` em testes de polling para avançar 500ms ticks sem sleep real
- AbortController testing: assert fetch aborted em unmount via spy

### UX/UI considerações (@ux-design-expert)

- Spinner deve ser perceptível mas não assustador — usar Framer Motion `motion.div` com `animate={{rotate: 360}}` 1.5s linear infinite
- Cores: state=polling neutro (gray-500), confirmed verde (smartlic brand), timeout amarelo (warning, não red)
- Acessibilidade: spinner com `role="status"` + `aria-live="polite"`; mudanças de state anunciadas
- Mobile-first: layouts vertical centered; safe area iOS bottom

---

## Risk & Rollback

### Triggers de rollback
- Polling causa `/me` overload (>10 RPS sustained do bucket de polling)
- Mixpanel funnel mostra MAIS abandono em `/planos/obrigado` pós-deploy (sinal pior)
- E2E tests flaky (polling timing race em CI)
- Sentry events `checkout_polling_error` rate >5/min

### Ações de rollback
1. **Imediato:** feature flag `CHECKOUT_POLLING_ENABLED=false` (env var Next.js public ou Vercel-style; render direto state=confirmed sem polling — comportamento atual)
2. **UX-only revert:** descomentar `state=confirmed` default; deixa MON-FN-003 cuidar do server-side
3. **Polling-rate degrade:** se `/me` overload, aumentar interval 500ms → 2s temporariamente
4. **Comunicação:** equipe support tem playbook "se user reporta paywall pós-pagamento, manualmente trigger plan refresh via admin endpoint"

### Compliance
- Mixpanel events incluem `stripe_session_id` mascarado (LGPD-safe)
- LGPD export (MON-FN-010): events Mixpanel funnel são incluídos via `analytics_events` table

---

## Dependencies

### Entrada
- **MON-FN-003** (cache invalidation atômica): essencial; sem ele polling resolve em até 5min em vez de <2s
- **MON-FN-002** (DLQ): garante que mesmo webhook delay não perde o evento
- Endpoint `GET /me` retornando `plan_type` (existente)

### Saída
- **MON-FN-006** (eventos funil): consome `checkout_confirmed` e `checkout_timeout` para funnel completo
- **MON-FN-008** (free tier): UX de paywall depende de status confirmável

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Race Condition `/planos/obrigado` — Polling Client-Side" |
| 2 | Complete description | Y | Sequência exata da race documentada (5 steps) + referência MON-FN-003 |
| 3 | Testable acceptance criteria | Y | 7 ACs incluindo Playwright E2E com mock /me state transitions |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui SSE (over-engineering 30s window) |
| 5 | Dependencies mapped | Y | Entrada MON-FN-003 (essencial); Saída MON-FN-006/008 |
| 6 | Complexity estimate | Y | M (2-3 dias) coerente — hook + 4 UX states + E2E |
| 7 | Business value | Y | "Pior momento de churn" articulado com clareza |
| 8 | Risks documented | Y | Triggers + feature flag `CHECKOUT_POLLING_ENABLED` + UX-only revert |
| 9 | Criteria of Done | Y | Visual review @ux-design-expert + smoke test staging |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #4; explicita "polling é band-aid sem MON-FN-003" |

### Observations
- 4 UI states (polling/confirmed/timeout/error) cobrem todos os edge cases
- AbortController + visibilityState pause + backoff em errors = polling de qualidade
- Memory `reference_frontend_dockerfile_backend_url_gap` referenciada corretamente em AC5
- A11y considerada (role="status", aria-live="polite")
- Mixpanel events estruturados alimentam funnel MON-FN-006

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — fix race condition checkout/obrigado | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P0 UX-critical pós-payment; Status Draft → Ready. | @po (Pax) |
