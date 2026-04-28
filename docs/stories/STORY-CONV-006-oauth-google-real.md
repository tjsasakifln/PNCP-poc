# STORY-CONV-006: OAuth Google real para signup (CONDITIONAL)

## Status

Approved

> Conditional precondition: Wave 0 manual check (Supabase Dashboard → Auth → Providers → Google) deve ser resolvido como Task 0 antes de @dev pegar a story. Não é gate de aprovação — é gate de sprint pickup.

## Story

**As a** novo usuário com conta Google que quer experimentar SmartLic,
**I want** botão "Continuar com Google" funcional ponta-a-ponta no signup,
**so that** eu pule criação de senha + email confirmation e entre em sessão autenticada em 1 clique.

## Acceptance Criteria

1. **PRECONDITION (Wave 0 manual check):** confirmar via Supabase Dashboard → Auth → Providers se Google OAuth provider está ATIVO para o projeto. Se ATIVO → escopo desta story = fix de UX (cobrir apenas pontos 4-7); se INATIVO → escopo completo (cobrir 2-7).
2. Provider Google ativado em Supabase com Client ID + Secret apropriados (credenciais Google Cloud Console; redirect URIs incluem `https://fqqyovlzdzimiwfofdjk.supabase.co/auth/v1/callback` e localhost para dev).
3. `frontend/app/signup/page.tsx:397` `<SignupOAuth />` chama `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: window.location.origin + '/auth/callback' } })`.
4. `/auth/callback` exchange code por session, cria perfil em `profiles` table se não existir, dispara trial padrão, redireciona para `/onboarding` (ou `/buscar` se `onboarding_skipped`).
5. Botão "Continuar com Google" também presente em `/login` com mesma lógica.
6. Mixpanel events: `signup_oauth_started` + `signup_oauth_completed` com prop `provider: 'google'` (depende STORY-GROW-001).
7. E2E test (Playwright + mock OAuth): user via Google chega em `/onboarding` autenticado, com perfil + trial criados, em <5s.
8. Erro tratado: usuário cancela consent → mensagem clara "Cancelado, tente novamente ou use email/senha"; rate-limit do Google → exponential backoff.

## Tasks / Subtasks

- [ ] Task 0 — **Wave 0 verification (PRE-WORK)** (AC: 1)
  - [ ] @devops abre Supabase Dashboard → Auth → Providers → Google
  - [ ] Documenta status (ATIVO / INATIVO) em comentário desta story
  - [ ] Decisão: full-scope vs UX-only-scope
- [ ] Task 1 — Setup provider (se INATIVO) (AC: 2)
  - [ ] Google Cloud Console: criar OAuth 2.0 client + redirect URIs
  - [ ] Supabase: ativar provider, salvar Client ID/Secret
- [ ] Task 2 — Frontend integration (AC: 3, 5)
  - [ ] Validar `<SignupOAuth />` componente atual (Audit Agent 2 viu chamada — verificar se provider correto)
  - [ ] Replicar em `/login`
- [ ] Task 3 — Callback flow (AC: 4)
  - [ ] `/auth/callback/page.tsx` cria profile + trial
  - [ ] Redirect inteligente baseado em `onboarding_skipped`
- [ ] Task 4 — Tracking (AC: 6)
- [ ] Task 5 — E2E + error handling (AC: 7, 8)
  - [ ] Playwright com mock OAuth
  - [ ] User journey cancel + retry

## Dev Notes

**Plano:** Wave 3, story 12 — **CONDITIONAL** pending Wave 0.

**Audit evidence:**
- `frontend/app/signup/page.tsx:397` renderiza `<SignupOAuth />`
- Função `signInWithGoogle()` é referenciada via `useAuth()` hook → Supabase client
- Audit Agent 2 alertou: "Verificar — Supabase tem Google OAuth provider configurado? (não visto em .env)"
- Memória `reference_railway_url_already_set.md` confirma BACKEND_URL/SUPABASE setados; não cobre OAuth provider config

**Files mapeados:**
- `frontend/app/signup/page.tsx:397` (verify)
- `frontend/components/SignupOAuth.tsx` (verify nome)
- `frontend/app/auth/callback/page.tsx` (edit)
- `frontend/app/login/page.tsx` (replicar)
- Supabase Dashboard (manual)
- Google Cloud Console (manual)

### Testing

- Unit: callback handler com mock session
- Integration: Supabase auth signInWithOAuth com test provider
- E2E: Playwright OAuth flow com mock

## Dependencies

- **Bloqueado por:** Wave 0 manual check (sem qual story não pode ser refinada)
- **Sinérgico com:** STORY-CONV-001 (magic-link fica para usuário sem Google; OAuth para quem tem)

## Owners

- Primary: @devops (Supabase + Google config), @dev (integration), @qa
- Compliance: @analyst (LGPD opt-in via OAuth)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — CONDITIONAL pending Wave 0 Supabase Dashboard check | @sm (River) |
