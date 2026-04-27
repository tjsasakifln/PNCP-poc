# MON-FN-015: Email Confirmation Soft-Bypass (Browse + 1ª Busca Pré-Verify)

**Priority:** P1
**Effort:** M (3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 5 (27/mai–02/jun)
**Sprint Window:** Sprint 5 (paralelo, sem bloqueio direto)
**Dependências bloqueadoras:** Nenhuma

---

## Contexto

Hoje Supabase Auth está configurado com **email confirmation enforced** (default Supabase behavior). User signup → recebe magic link → MUST click antes de qualquer ação. Friction:
- Drop-off pós-signup pré-confirmação é **desconhecido** mas plausivelmente alto
- Email pode ir para spam (despite Resend domain verified — memory `reference_resend_personal_tone_send`)
- User está já hot durante signup; perder 5 minutos para navegar email mata momentum
- Correção de email digitado errado (ex: `gmial.com`) trava signup

Pattern Fortune-500 / B2C SaaS modern (Notion, Linear, Vercel): **soft-bypass** — permite browse + 1ª ação não-crítica antes de email confirm; bloqueia apenas billing/trial start. Resultado típico: signup completion +20-40%.

**Importante:** continua exigindo confirmação para:
- `trial_started` (subscription Stripe — fraud prevention)
- `checkout_started` (financial action)
- LGPD export/delete (compliance)

Permite (sem confirmação):
- Browse landing/dashboard
- 1ª busca (limited result)
- Pipeline view (read-only)

**Por que P1:** com tráfego SEO inbound (post-EPIC B), drop-off pós-signup é leak crítico. Pre-revenue pode pagar muito por reduce friction. M effort, isolated.

**Paths críticos:**
- `backend/routes/auth_signup.py` (signup flow)
- `backend/auth.py::require_auth` (verifica email_confirmed_at)
- Supabase Auth config (`Settings > Auth > Email Auth > "Confirm email"`)
- `frontend/app/login/`, `frontend/app/signup/` (UX)
- Magic link rate limit (Redis token bucket)

---

## Acceptance Criteria

### AC1: Supabase Auth config — soft-bypass

Given que Supabase força email confirm by default,
When config alterada,
Then signup completa sem confirm; flag `email_confirmed_at IS NULL` para tracking.

- [ ] Supabase Dashboard `Project Settings > Authentication > Email Auth`:
  - Manter "Enable email signup" = ON
  - **Mudar "Confirm email" = OFF** (permite signup sem confirmação)
- [ ] Documentação dessa mudança em `docs/operations/supabase-auth-config.md`
- [ ] Magic link continua sendo enviado (templates) mas não bloqueia primeiro login
- [ ] User é criado em `auth.users` com `email_confirmed_at = NULL`

### AC2: Backend dependency `require_email_verified` (granular)

Given que algumas rotas exigem confirmação,
When auth dep,
Then `require_email_verified` bloqueia se `email_confirmed_at IS NULL`.

- [ ] Em `backend/auth.py`:
```python
async def require_email_verified(user: User = Depends(require_auth)) -> User:
    """Stricter dependency: requires email_confirmed_at IS NOT NULL.

    Use for billing/trial actions; for browse/search use require_auth.
    """
    if not user.get("email_confirmed_at"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "email_not_verified",
                "message": "Confirme seu email para continuar.",
                "resend_url": "/api/auth/resend-confirmation",
            },
        )
    return user
```
- [ ] Aplicar `require_email_verified` em:
  - `routes/billing.py::create_checkout_session` (checkout)
  - `webhooks/handlers/subscription.py::handle_subscription_created` (trial start gate — N/A, isto é webhook; gate vai no checkout)
  - `routes/conta.py::request_data_export` (LGPD)
  - `routes/conta.py::request_account_deletion` (LGPD)
- [ ] Resto das rotas usa `require_auth` normal (browse, search, pipeline view)
- [ ] Frontend recebe 403 estruturado e mostra modal "Confirme seu email"

### AC3: First search permitido sem email_verified

Given user não confirmou email,
When tenta primeira busca,
Then permite (`require_auth` apenas, não `require_email_verified`).

- [ ] `routes/search/__init__.py` POST handler usa `require_auth` apenas (não strict)
- [ ] Quota: free trial sem email confirmed pode usar 1 busca (configurable via env `UNVERIFIED_USER_FREE_SEARCHES=1`)
- [ ] Após 1 busca, próximas exigem email confirmation:
  - 2ª busca → mostra modal "Confirme seu email para continuar buscando"
  - Frontend re-tenta após confirm
- [ ] Quota local separada por user (Redis ou DB):
```python
async def _check_unverified_search_quota(user_id: str, email_confirmed_at: Optional[str]) -> bool:
    """Returns True if unverified user can search; False if quota exceeded."""
    if email_confirmed_at:
        return True  # verified — normal quota applies
    redis = await get_redis_client()
    key = f"unverified_search_count:{user_id}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 30 * 24 * 60 * 60)  # 30d TTL
    return count <= int(os.getenv("UNVERIFIED_USER_FREE_SEARCHES", "1"))
```

### AC4: Magic link reenvio com rate limit

Given user pede resend de magic link,
When endpoint chamado,
Then rate limit Redis token bucket aplica (3 reenvios/hora).

- [ ] Endpoint `POST /api/auth/resend-confirmation`:
```python
@router.post("/auth/resend-confirmation")
async def resend_confirmation_email(user: User = Depends(require_auth)):
    """Resend Supabase confirmation magic link with rate limit."""
    if user.get("email_confirmed_at"):
        return {"status": "already_confirmed"}

    # Rate limit: 3 per hour per user
    redis = await get_redis_client()
    key = f"magic_link_resend:{user['id']}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60 * 60)
    if count > 3:
        ttl = await redis.ttl(key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "retry_after_seconds": ttl,
            },
        )

    # Trigger Supabase resend
    admin = get_supabase_admin()
    admin.auth.admin.invite_user_by_email(user["email"], {
        "redirect_to": f"{FRONTEND_URL}/auth/confirm",
    })
    # Or alternative: use admin.auth.resend method if available

    track_funnel_event("magic_link_resent", user["id"])
    return {"status": "sent"}
```
- [ ] Counter `smartlic_magic_link_resend_total{result}` (sent | rate_limited | already_confirmed)

### AC5: Frontend UX — banner + modal

Given user logado mas não confirmado,
When navega,
Then banner sticky topbar + modais em ações gated.

- [ ] Componente `<EmailVerificationBanner />` (sticky topbar):
  - Texto: "Confirme seu email para iniciar trial e fazer upgrade"
  - CTA primário "Reenviar email" → POST resend endpoint
  - CTA secundário "Já confirmei" → re-fetch /me (caso flag dessincronizada)
  - Dismissible mas reaparece a cada session
  - Cor: amarelo (warning não red)
- [ ] Modal `<EmailVerificationGate />` em ações bloqueadas:
  - Disparado quando backend retorna `403 email_not_verified`
  - h1: "Confirme seu email para continuar"
  - Texto explicativo: "Esta ação requer email verificado..."
  - CTA: "Reenviar email" + "Já confirmei"
  - Não-dismissible quando gate hit (must confirm)
- [ ] Mixpanel events:
  - `email_verification_banner_shown`
  - `email_verification_resend_clicked`
  - `email_verification_modal_shown` (com `gated_action`)
  - `email_verification_completed` (after webhook signup_completed event)

### AC6: Webhook ou polling para detect verification

Given user clica magic link em tab separado,
When email_confirmed_at set,
Then frontend detecta + UI updates.

- [ ] Polling em background (low frequency, 30s intervals) quando user logged in + unverified:
```typescript
useEffect(() => {
  if (user.email_confirmed_at) return;
  const interval = setInterval(async () => {
    const res = await fetch("/api/me", { cache: "no-store" });
    const data = await res.json();
    if (data.email_confirmed_at) {
      setUser(data);
      track("email_verification_completed");
      // Refresh page or banner state
    }
  }, 30000);
  return () => clearInterval(interval);
}, [user.email_confirmed_at]);
```
- [ ] Alternative: Supabase Auth state listener (`onAuthStateChange`) — pode capturar `USER_UPDATED` event

### AC7: Confirmation success page

Given user clica magic link,
When lands em `/auth/confirm`,
Then página confirma + redirect to `/buscar` (ou returnTo).

- [ ] `frontend/app/auth/confirm/page.tsx`:
  - Validate token via Supabase
  - Sucess: Mixpanel event `email_verified` + redirect `/buscar?welcome=verified`
  - Fail: mostrar erro + retry button
- [ ] `/buscar?welcome=verified` mostra toast "Email confirmado!" (UX delight)

### AC8: Métricas

- [ ] Counter `smartlic_signup_email_unverified_total` (signups completed sem confirm — esperado)
- [ ] Counter `smartlic_email_verification_completed_total` (confirmations)
- [ ] Funnel: `signup_completed → first_search (unverified ok) → email_verified → trial_started`
- [ ] Métrica nova: `signup_to_verification_rate` (verified / signups)

### AC9: Testes

- [ ] Unit `backend/tests/auth/test_require_email_verified.py`:
  - [ ] `require_email_verified` com email_confirmed_at NULL → 403
  - [ ] `require_email_verified` com email_confirmed_at SET → user retornado
  - [ ] `require_auth` (não strict) com NULL → user retornado normalmente
- [ ] Integration `backend/tests/routes/test_unverified_search_quota.py`:
  - [ ] Unverified user 1ª busca → permitido
  - [ ] Unverified user 2ª busca → 403 com `unverified_quota_exceeded`
  - [ ] Verified user → normal quota
- [ ] Integration `backend/tests/auth/test_magic_link_resend.py`:
  - [ ] First resend → 200
  - [ ] 4th resend in 1h → 429
  - [ ] Already confirmed → 200 with already_confirmed
- [ ] Frontend `frontend/__tests__/EmailVerificationBanner.test.tsx`:
  - [ ] Banner renderiza quando email_confirmed_at NULL
  - [ ] Banner hidden quando confirmed
  - [ ] Resend click → fetch endpoint
- [ ] E2E Playwright:
  - [ ] Signup → land em /buscar (no email confirm step)
  - [ ] Banner visível
  - [ ] First search permitido
  - [ ] Click "Pagar plano" → modal email gate
  - [ ] Mock magic link click → banner desaparece
- [ ] Cobertura ≥85%

---

## Scope

**IN:**
- Supabase Auth config: confirm email = OFF
- Backend `require_email_verified` strict dep
- Granular gates em billing/trial/LGPD
- Quota 1 busca pré-confirmação
- Magic link resend com rate limit
- Frontend banner + modal
- Polling detect verification
- Confirmation success page
- Mixpanel events

**OUT:**
- Phone number verification alternativa
- OAuth Google one-click signup (já existe via STORY-OAUTH)
- Captcha em signup (over-engineering pre-revenue)
- Email change flow pós-signup (separate feature)
- Múltiplos métodos de auth (apenas email magic link + OAuth Google)
- Suspension/ban automático após N unverified days

---

## Definition of Done

- [ ] Supabase Auth confirm email = OFF (verificar via dashboard)
- [ ] `require_email_verified` aplicado em billing/LGPD endpoints
- [ ] Frontend banner + modal funcionais
- [ ] Quota 1 busca pré-verify enforced
- [ ] Resend rate limit testado (4ª tentativa retorna 429)
- [ ] Polling auto-detect verification
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] CodeRabbit clean
- [ ] @ux-design-expert review do banner + modal
- [ ] E2E completo: signup → search → gate → resend → confirm → trial start
- [ ] Mixpanel funnel atualizado com novos events
- [ ] Operational runbook em `docs/operations/auth-runbook.md`
- [ ] Métrica baseline capturada: signup → verification rate em primeiras 2 semanas pós-deploy

---

## Dev Notes

### Padrões existentes a reutilizar

- **`require_auth`:** existing `backend/auth.py`
- **Redis client:** `cache/redis.py::get_redis_client`
- **Supabase admin:** `supabase_client.get_supabase_admin`
- **Mixpanel events:** `analytics_events.track_funnel_event` (MON-FN-006)
- **Frontend types:** auto-regen `api-types.generated.ts`

### Funções afetadas

- `backend/auth.py` (NOVA dep `require_email_verified`)
- `backend/routes/billing.py` (aplica strict)
- `backend/routes/conta.py` (aplica strict em LGPD)
- `backend/routes/auth_signup.py` ou `routes/auth_email.py` (resend endpoint)
- `backend/routes/search/__init__.py` (unverified quota)
- `frontend/components/EmailVerificationBanner.tsx` (NOVO)
- `frontend/components/EmailVerificationModal.tsx` (NOVO)
- `frontend/app/auth/confirm/page.tsx` (NOVO ou estender)
- `backend/metrics.py` (counters)
- `backend/config.py` (`UNVERIFIED_USER_FREE_SEARCHES` env)

### Trade-off: Supabase config vs custom enforcement

Alternativa: keep Supabase enforce ON, override no backend. Trade-off:
- Supabase ON: signup retorna error sem confirm; impossível browse pré-verify
- Supabase OFF: signup completa, gates manuais no backend (escolhido)

Pattern Fortune-500 prefer Supabase OFF + backend granular control = mais flexibility.

### Testing Standards

- Mock Supabase admin via `@patch("supabase_client.get_supabase_admin")`
- Mock Redis via `fakeredis`
- Frontend tests com MSW
- E2E Playwright cobre full flow
- Anti-hang: pytest-timeout 30s

---

## Risk & Rollback

### Triggers de rollback
- Spam signups (bot automation aproveitando soft-bypass)
- Bounces increased (low-quality emails passing pré-confirm)
- Fraud: trials iniciados com emails fake bloqueados → loops
- Resend rate limit hit (Resend account)

### Ações de rollback
1. **Imediato:** Supabase Dashboard re-enable "Confirm email" = ON; rollback código backend
2. **Anti-spam:** habilitar Cloudflare Turnstile em /signup endpoint
3. **Email-only revert:** keep soft-bypass mas exigir confirm para 1ª busca (intermediate)
4. **Communication:** Sentry alert em spike de unverified signups

### Compliance
- LGPD: email é PII; user pode pedir deletion mesmo sem verify (MON-FN-011)
- Anti-fraud: gating em billing previne creditcard fraud com email fake

---

## Dependencies

### Entrada
- Supabase Auth project ativo
- Magic link templates configurados
- Redis disponível (rate limit)

### Saída
- Funnel Mixpanel mostra mais signups (success metric pré vs pós)
- Better baseline para A/B test pós n≥30 (signup conversion as input)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO (conditional)
**Score:** 7/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "Email Confirmation Soft-Bypass (Browse + 1ª Busca Pré-Verify)" |
| 2 | Complete description | Y | Pattern Notion/Linear/Vercel cited; benchmark +20-40% conversion |
| 3 | Testable acceptance criteria | Y | 9 ACs incluindo E2E full flow + rate limit 4ª resend = 429 |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT exclui phone verify/captcha/OAuth |
| 5 | Dependencies mapped | Y | Entrada Supabase Auth + Magic link templates + Redis |
| 6 | Complexity estimate | Y | M (3 dias) coerente — auth dep + UI banner + modal + polling |
| 7 | Business value | Y | "Drop-off pós-signup pré-confirmação leak crítico"; SEO ramp-up |
| 8 | Risks documented | Y | Spam signups + bounces + fraud + métrica `signup_to_verification_rate` |
| 9 | Criteria of Done | Y | Métrica baseline capturada em primeiras 2 semanas pós-deploy |
| 10 | Alignment with PRD/Epic | Y | EPIC P1 Sprint 5; mudança UX major reconhecida |

### Required Fixes (CONDITIONAL — para @dev resolver durante implementation)

- [ ] **Adicionar feature flag runtime `EMAIL_SOFT_BYPASS_ENABLED` (env var Railway):** Rollback atual é "Supabase Dashboard re-enable Confirm email = ON; rollback código backend" — exige PR revert + dashboard touch. Para mudança UX behavioral significativa, ops precisa env flag para revert sem deploy:
  ```python
  # backend/auth.py
  EMAIL_SOFT_BYPASS_ENABLED = os.getenv("EMAIL_SOFT_BYPASS_ENABLED", "true").lower() == "true"

  # require_email_verified bypass: when flag false, ALL routes use strict (back to old behavior)
  ```
- [ ] Documentar em `docs/operations/feature-flags.md`

### Observations
- Score 7 reflete: rollback mecanismo é config + code revert (não env-only); para mudança UX dessa magnitude (paywall pre vs post auth) Fortune-500 standard prefere env flag + immediate rollback
- Métrica `signup_to_verification_rate` baseline capturada em DoD (correto)
- Granular gates corretos: billing/LGPD usam `require_email_verified`, browse/search usam `require_auth`
- Quota 1 busca pre-verify configurável via `UNVERIFIED_USER_FREE_SEARCHES` env (boa prática)
- Magic link rate limit 3/hora via Redis token bucket
- Polling /me com 30s interval para detectar verification cross-tab (low frequency, OK)
- Anti-spam rollback: Cloudflare Turnstile mencionado em rollback ações (fallback)

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — soft-bypass email confirmation com gates seletivos | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO conditional (7/10). Required fix: env flag `EMAIL_SOFT_BYPASS_ENABLED` para rollback runtime sem deploy. Status Draft → Ready com fix obrigatório pre-merge. | @po (Pax) |
