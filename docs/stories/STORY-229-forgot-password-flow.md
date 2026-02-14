# STORY-229: Add "Forgot Password" Flow to Login Page

**Status:** Completed
**Priority:** P1 — GTM Blocker
**Sprint:** Sprint 3
**Estimated Effort:** S (2-3h)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (MAJ-3)
**Squad:** team-bidiq-frontend (dev, qa)

---

## Context

The login page (`/login`) has email/password fields and "Entrar com Google" button but **no "Esqueci minha senha" (Forgot Password) link**. The FAQ at `/ajuda` explicitly tells users:
> "Na tela de login, clique em 'Esqueci minha senha'"

But the link doesn't exist. Users who forget their password are completely locked out.

## Acceptance Criteria

### Login Page — Reset Link

- [x] AC1: "Esqueci minha senha" link is visible below the password field on `/login`
- [x] AC2: Clicking the link navigates to `/recuperar-senha` (or opens inline reset form)
- [x] AC3: Link is styled consistently with the login page design (not jarring or out of place)

### Password Reset Page

- [x] AC4: `/recuperar-senha` page has an email input field and "Enviar link de recuperação" button
- [x] AC5: Submitting a valid email calls Supabase `resetPasswordForEmail()` API
- [x] AC6: Success state shows: "Link de recuperação enviado para {email}. Verifique sua caixa de entrada."
- [x] AC7: Error state shows user-friendly message if email fails (e.g., rate limit, network error)
- [x] AC8: "Voltar ao login" link navigates back to `/login`
- [x] AC9: If user is already authenticated, redirect to `/buscar` (consistent with login page behavior)

### Password Update Callback

- [x] AC10: Supabase password reset email contains a link that redirects to the app
- [x] AC11: App handles the Supabase `RECOVERY` auth event and shows a "Nova senha" form
- [x] AC12: New password form validates: minimum 8 characters
- [x] AC13: On successful password update, user is logged in and redirected to `/buscar`
- [x] AC14: On failure, user sees error message with retry option

### Tests

- [x] AC15: Unit test for `/recuperar-senha` page rendering (5 tests)
- [x] AC16: Unit test for Supabase `resetPasswordForEmail` call (2 tests)
- [x] AC17: Unit test for success/error states (4 tests + 7 RedefinirSenha tests)

## Technical Notes

- Supabase SDK: `supabase.auth.resetPasswordForEmail(email, { redirectTo: '...' })`
- Recovery event: listen for `RECOVERY` event in `onAuthStateChange`
- Redirect URL must be in Supabase Auth allowed redirect URLs list
- Rate limiting on the frontend: button disabled for 60s after submission
- No backend API routes needed — all handled client-side via Supabase SDK
- Password confirmation field added for better UX (not in original ACs)

## Dependencies

- None (uses existing Supabase auth infrastructure)
- **NOTE:** Supabase redirect URL `https://smartlic.tech/redefinir-senha` must be added to Supabase Auth allowed redirect URLs

## File List

| File | Action | Description |
|------|--------|-------------|
| `frontend/app/login/page.tsx` | Modify | Add "Esqueci minha senha" link below password field |
| `frontend/app/recuperar-senha/page.tsx` | Create | Password reset request page (email form, success/error states) |
| `frontend/app/redefinir-senha/page.tsx` | Create | New password form (RECOVERY event handler, validation) |
| `frontend/__tests__/recuperar-senha.test.tsx` | Create | 19 tests covering all ACs |
