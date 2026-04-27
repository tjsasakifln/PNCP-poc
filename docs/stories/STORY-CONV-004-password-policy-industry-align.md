# STORY-CONV-004: Password policy alinhar com indústria (NIST 800-63B)

## Status

Approved

## Story

**As a** usuário tentando criar conta com senha que considero segura ("minha-senha-segura-123"),
**I want** que SmartLic aceite senhas de 8+ caracteres sem exigir UPPERCASE+digit obrigatórios,
**so that** eu não abandone o signup por frustração com policy excessiva (pattern atual rejeita ~15-25% das submissões).

## Acceptance Criteria

1. Frontend `frontend/app/signup/page.tsx:75-84` regex aceita: 8+ caracteres, qualquer composição.
2. Backend `backend/auth.py` validação alinhada: 8+ chars, sem requisito de UPPERCASE/digit/símbolo.
3. zxcvbn-style strength meter visível em tempo real (verde/amarelo/vermelho) — guidance, não bloqueio (NIST 800-63B §5.1.1.2).
4. Backend rejeita senhas em top-1000 mais comuns (HIBP-style ou local list); mensagem clara "Esta senha aparece em vazamentos conhecidos, escolha outra".
5. Senhas legítimas que falharam no policy antigo (ex: "minha-senha-segura-123", "passphrase com espacos") agora passam.
6. Mixpanel evento `signup_password_rejected` com prop `reason: weak|common|too_short` (depende STORY-GROW-001) — para medir se nova policy reduz rejections.
7. @analyst review de compliance: LGPD + ISO 27001 OK; documentar em `docs/adr/NNN-password-policy.md`.
8. Migração: usuários existentes com senhas pre-policy não são forçados a trocar (não invalidar sessões).

## Tasks / Subtasks

- [ ] Task 1 — Frontend regex (AC: 1)
  - [ ] Trocar regex em `signup/page.tsx:75-84` para `/^.{8,}$/` (com sanitização)
  - [ ] Mensagem de erro ajustada
- [ ] Task 2 — Backend validation (AC: 2, 4)
  - [ ] Atualizar `backend/auth.py` policy
  - [ ] Lista top-1000 common passwords (HIBP top, ou pip lib `password-strength`)
- [ ] Task 3 — Strength meter (AC: 3)
  - [ ] Integrar `zxcvbn-ts` (ou similar) no signup form
  - [ ] Visual feedback verde/amarelo/vermelho
- [ ] Task 4 — Tracking (AC: 6)
  - [ ] Event `signup_password_rejected`
- [ ] Task 5 — Compliance review (AC: 7)
  - [ ] @analyst escreve ADR
- [ ] Task 6 — Backward compat (AC: 8)
  - [ ] Confirmar que mudança não invalida hashes existentes (Supabase Auth gerencia, low risk)

## Dev Notes

**Plano:** Wave 3, story 10.

**Audit evidence:**
- `frontend/app/signup/page.tsx:75-84` regex força UPPERCASE + digit (Audit Agent 2 confirmou)
- Padrão indústria (Google, Stripe, Notion): 8+ chars qualquer composição

**Files mapeados:**
- `frontend/app/signup/page.tsx:75-84` (edit)
- `backend/auth.py` (policy validation)
- `docs/adr/NNN-password-policy.md` (criar)

### Testing

- Unit: regex matrix em `frontend/__tests__/signup/password-policy.test.ts`
- Integration: backend rejection com common password
- E2E: Playwright signup com senhas variadas

## Dependencies

- **Bloqueado por:** STORY-GROW-001 (AC 6 mensurável)
- **Não bloqueia:** outras Wave 3

## Owners

- Primary: @dev (frontend+backend)
- Compliance: @analyst (ADR)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm | @sm (River) |
