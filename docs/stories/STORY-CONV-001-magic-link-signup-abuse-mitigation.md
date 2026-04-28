# STORY-CONV-001: Magic-link signup (substitui email-confirm gate) + abuse mitigation

## Status

Approved

## Story

**As a** novo usuário pousando em `/signup` com intenção genuína de testar SmartLic,
**I want** acesso ao produto em <30s sem esperar 5-10min por email Resend nem ser bloqueado por bots farmando trial,
**so that** eu experimente o valor imediatamente e converta em primeira sessão (vs abandonar enquanto checo email).

## Acceptance Criteria

1. Signup form retorna sucesso e abre sessão autenticada em <30s wall-clock (sem email-confirmation gate).
2. Solução escolhida (TBD via ADR @architect) pode ser: (a) magic-link instantâneo via Supabase OTP com sessão criada imediatamente após validação token; OU (b) auto-confirm + magic-link enviado em paralelo para verificação posterior. Decisão documentada.
3. Anti-abuse stack: Cloudflare Turnstile widget no signup form; rate-limit Redis bucket por IP (default 5 trials/IP/24h), por email domain (10 trials/domain/24h), por dispositivo fingerprint (3 trials/device/24h).
4. Load test sintético: 100 requests do mesmo IP em 60s → 95+ rejeitados com HTTP 429 e mensagem clara.
5. Mixpanel `signup_start` e `signup_completed` rastreáveis via paridade `distinct_id` (depende STORY-GROW-001).
6. LGPD: opt-in transactional documentado em `/termos`; checkbox no signup form (não pre-checked) para "concordo receber emails do SmartLic"; mecanismo de opt-out funcional.
7. Backend `auth_signup.py` não bloqueia com `email_confirm=False` — fluxo decide entre auto-confirm + magic-link follow-up vs OTP-first.
8. Pós-signup, user é redirecionado direto a `/onboarding` (ou skip-to-search se STORY-CONV-003 já live).
9. Métrica de bot detection: `bot_signup_blocked_total` Prometheus counter exposto.

## Tasks / Subtasks

- [ ] Task 1 — ADR de approach (AC: 2)
  - [ ] @architect escreve `docs/adr/NNN-magic-link-vs-auto-confirm.md`
  - [ ] Considera: Supabase OTP API limits, fricção UX, abuse vector LLM cost
- [ ] Task 2 — Backend auth flow (AC: 1, 7)
  - [ ] Modificar `backend/routes/auth_signup.py:147` conforme ADR
  - [ ] Sessão Supabase criada antes do redirect (sem aguardar Resend delivery)
- [ ] Task 3 — Anti-abuse: Turnstile (AC: 3, 4)
  - [ ] @devops obtém site-key + secret-key Cloudflare Turnstile
  - [ ] Frontend integra `<Turnstile />` widget; backend valida token
- [ ] Task 4 — Anti-abuse: rate-limit (AC: 3, 4, 9)
  - [ ] @data-engineer + @dev: Redis token bucket por (IP, email_domain, device_fingerprint)
  - [ ] Headers `Retry-After` corretos
  - [ ] Counter `bot_signup_blocked_total` (labels: reason=ip|domain|device)
- [ ] Task 5 — LGPD compliance (AC: 6)
  - [ ] @analyst review de `/termos` para opt-in transactional
  - [ ] Checkbox no form (não pre-checked)
  - [ ] Endpoint de opt-out funcional
- [ ] Task 6 — Load test (AC: 4)
  - [ ] Locust scenario: 100 req mesmo IP em 60s
  - [ ] Validar 95+ rejected
- [ ] Task 7 — E2E + tracking validation (AC: 5, 8)
  - [ ] Mixpanel funnel signup_start → signup_completed → onboarding_step_1
  - [ ] Playwright happy path

## Dev Notes

**Plano:** Wave 3, story 7 (CRITICAL conversion — biggest single blocker, ~40% drop atual).

**Audit evidence:**
- `backend/routes/auth_signup.py:147` faz `email_confirm=False` — força confirmação Resend (5-10min delay) antes de qualquer ação.
- Memória `reference_admin_bypass_paywall.md` lembra que admin users bypassam paywall — não confundir com bypass de email confirm.

**Advisor warning sobre auto-confirm direto:**
- Trial gratuito sem cartão + auto-confirm sem mitigation = bots farmando ~$0.20-0.50/trial em LLM
- Solução: magic-link instant (zero-friction) + Turnstile + rate-limit
- @analyst LGPD review obrigatório (memória menciona como gate)

**Files mapeados:**
- `backend/routes/auth_signup.py:147` (edit)
- `frontend/app/signup/page.tsx` (Turnstile widget)
- `backend/quota.py` ou novo `backend/anti_abuse.py` (rate-limit logic)
- `frontend/app/termos/page.tsx` (opt-in copy revisada)
- `docs/adr/NNN-magic-link-vs-auto-confirm.md` (criar)

**Memória lookup adicional:** memória `feedback_load_test_404_investigation.md` avisa contra premissa "pre-existing" — verificar antes do load test que rota não está degradada por outro motivo.

### Testing

- Unit: rate-limit logic (jest)
- Integration: Turnstile token validation (mock Cloudflare API)
- Load: Locust scenario (memória `feedback_locust_catch_response.md` — sempre `response.success()/failure()` explícito)
- E2E: Playwright signup happy path + bot path

## Dependencies

- **Bloqueado por:** nenhum (mas STORY-GROW-001 ajuda AC 5 mensurável)
- **Bloqueia:** STORY-CONV-002 (landing copy fica honesta — "sem cartão, instant access")
- **Risco:** alto blast radius (auth flow); requer feature flag para rollback rápido

## Owners

- Primary: @architect (ADR), @dev (implementação), @qa
- Anti-abuse: @data-engineer (Redis schema)
- Compliance: @analyst (LGPD)
- Infra: @devops (Turnstile keys, feature flag)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — abuse vector flagged by advisor | @sm (River) |
