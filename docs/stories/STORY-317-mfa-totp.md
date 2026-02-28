# STORY-317: MFA (TOTP)

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 3 (Post-launch)
**Priority:** MEDIUM
**Story Points:** 8 SP
**Estimate:** 4-5 dias
**Owner:** @dev + @architect

---

## Problem

Contas de usuarios (especialmente admin e master) nao possuem segundo fator de autenticacao. Em caso de comprometimento de senha, atacante tem acesso total. Para compliance e seguranca enterprise, MFA/TOTP e requisito. Supabase suporta MFA nativamente mas nao esta habilitado.

## Solution

Habilitar MFA TOTP no Supabase Auth e criar UI de setup/verificacao no frontend. Forcar MFA para roles admin/master. Oferecer como opcional para usuarios regulares. Incluir recovery codes para caso de perda do dispositivo.

---

## Acceptance Criteria

### Backend — Supabase MFA Config

- [ ] **AC1:** Habilitar MFA no Supabase Dashboard:
  - Auth → MFA → Enable TOTP
  - Max enrolled factors: 1 (TOTP apenas, nao SMS)
- [ ] **AC2:** Atualizar `auth.py` → `require_auth()` para verificar `aal` (Authenticator Assurance Level):
  - `aal1`: password only (default)
  - `aal2`: password + TOTP verified
  - Para roles admin/master: rejeitar `aal1` com erro "MFA obrigatorio"
- [ ] **AC3:** Criar middleware `require_mfa` para endpoints sensiveis:
  - Admin endpoints (`/admin/*`)
  - Billing endpoints (`/checkout`, `/billing-portal`)
  - Account changes (`/change-password`)
- [ ] **AC4:** Endpoint `GET /v1/mfa/status` que retorna:
  ```json
  {
    "mfa_enabled": true,
    "factors": [{ "id": "...", "type": "totp", "friendly_name": "...", "verified": true }],
    "aal_level": "aal2",
    "mfa_required": true  // true for admin/master roles
  }
  ```

### Backend — Recovery Codes

- [ ] **AC5:** Gerar 10 recovery codes de uso unico no momento do MFA enrollment
- [ ] **AC6:** Armazenar recovery codes hashed (bcrypt) em `mfa_recovery_codes` table:
  - `user_id`, `code_hash`, `used_at` (null = nao usado), `created_at`
- [ ] **AC7:** Endpoint `POST /v1/mfa/verify-recovery` para autenticar com recovery code:
  - Verifica hash, marca como usado, eleva para aal2
  - Maximo 3 tentativas erradas por hora (brute force protection)
- [ ] **AC8:** Endpoint `POST /v1/mfa/regenerate-recovery` para gerar novos codes (requer aal2)

### Frontend — Setup MFA

- [ ] **AC9:** Pagina `/conta/seguranca` com secao MFA:
  - Se MFA nao ativo: botao "Ativar autenticacao em dois fatores"
  - Se MFA ativo: badge verde "MFA Ativo", botao "Desativar" (requer verificacao)
- [ ] **AC10:** Fluxo de setup:
  - Step 1: Gerar QR code TOTP (Supabase `mfa.enroll()`)
  - Step 2: Mostrar QR code + chave manual (para apps que nao leem QR)
  - Step 3: Verificar codigo de 6 digitos (Supabase `mfa.challengeAndVerify()`)
  - Step 4: Mostrar 10 recovery codes com aviso "Salve em local seguro"
  - Step 5: Confirmar: "Salvei meus codigos de recuperacao"
- [ ] **AC11:** QR code deve incluir issuer "SmartLic" e label com email do usuario
- [ ] **AC12:** Suporte a apps: Google Authenticator, Authy, 1Password, Microsoft Authenticator

### Frontend — Login com MFA

- [ ] **AC13:** Apos login com email/senha, se MFA ativo → tela de verificacao TOTP:
  - Input de 6 digitos com auto-focus
  - Auto-submit quando 6 digitos digitados
  - Link "Usar codigo de recuperacao" → input alternativo
  - Botao "Verificar"
- [ ] **AC14:** Se verificacao falhar: mostrar erro com tentativas restantes
- [ ] **AC15:** Redirect para destino original apos verificacao bem-sucedida

### Frontend — Admin/Master Enforcement

- [ ] **AC16:** Se role e admin/master e MFA nao ativo:
  - Banner persistente vermelho: "MFA obrigatorio para sua conta. Configure agora."
  - Redirecionar para `/conta/seguranca` apos login
  - Bloquear acesso a `/admin/*` ate MFA configurado
- [ ] **AC17:** Banner nao-dismissavel ate MFA configurado

### Frontend — Desativar MFA

- [ ] **AC18:** Fluxo de desativacao (requer aal2):
  - Confirmar com codigo TOTP atual
  - Confirmacao: "Tem certeza? Sua conta ficara menos segura"
  - Desativar via Supabase `mfa.unenroll()`
- [ ] **AC19:** Nao permitir desativacao para admin/master (MFA obrigatorio)

### Testes

- [ ] **AC20:** Backend: testes para require_mfa middleware, recovery codes (hash, verify, exhaust), aal checking
- [ ] **AC21:** Frontend: testes para setup flow (QR, verify, recovery codes), login TOTP screen, enforcement banner
- [ ] **AC22:** Teste de brute force protection (3 tentativas/hora)
- [ ] **AC23:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Supabase Auth | Supabase Cloud | MFA suportado, nao habilitado |
| Auth middleware | `backend/auth.py` → require_auth() | Existe, precisa aal check |
| Login page | `frontend/app/login/page.tsx` | Existe, precisa step TOTP |
| Account page | `frontend/app/conta/page.tsx` | Existe, precisa secao MFA |
| Password reset | `frontend/app/recuperar-senha/` | Existe |
| Supabase SSR client | `@supabase/ssr` | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/routes/mfa.py`
- `backend/tests/test_mfa.py`
- `frontend/app/conta/seguranca/page.tsx`
- `frontend/components/auth/MfaSetupWizard.tsx`
- `frontend/components/auth/TotpVerificationScreen.tsx`
- `frontend/components/auth/MfaEnforcementBanner.tsx`
- `frontend/__tests__/auth/mfa-flow.test.tsx`
- `supabase/migrations/XXXXXXXX_add_mfa_recovery_codes.sql`

**Modificados:**
- `backend/auth.py` (aal check)
- `backend/main.py` (include mfa router)
- `frontend/app/login/page.tsx` (TOTP step)
- `frontend/app/conta/page.tsx` (link to /seguranca)

## Dependencias

- Supabase MFA habilitado no dashboard
- Nenhuma dependencia de outras stories

## Riscos

- Supabase MFA TOTP e nativo — evitar reimplementar crypto (usar SDK)
- Recovery codes sao criticos: se usuario perde phone + codes, precisa de reset manual admin
- Rate limiting de TOTP verify: Supabase ja implementa, verificar se suficiente
- QR code generation: usar biblioteca `qrcode.react` ou Supabase SDK built-in
- Admin lockout: se admin ativa MFA e perde acesso → recovery via Supabase Dashboard (manual)

## Notas de Seguranca

- Recovery codes: 10 alphanumericos de 8 chars, crypto.getRandomValues()
- Hash: bcrypt com salt (nao plain text no DB)
- TOTP window: ±1 step (30s tolerance padrao)
- Nao implementar SMS MFA (custo, seguranca inferior a TOTP)
