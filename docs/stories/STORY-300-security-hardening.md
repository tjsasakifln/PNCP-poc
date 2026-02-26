# STORY-300: Security Hardening

**Sprint:** 2 — Make It Observable
**Size:** M (4-8h)
**Root Cause:** Track F (Security & Compliance Audit)
**Industry Standard:** [OWASP Top 10 (2021)](https://owasp.org/Top10/), [LGPD — Lei 13.709/2018](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)

## Contexto

Track F da auditoria GTM encontrou 3 issues MEDIUM:
1. **Missing CSP headers** — sem Content-Security-Policy, vulnerável a XSS injection
2. **Error information leak** — Excel export endpoint vaza stack traces no response body
3. **LGPD legal basis missing** — página de privacidade não especifica base legal para tratamento

Nenhum é BLOCKER para go-live, mas são requisitos para qualquer cliente enterprise ou processo de compliance.

## Acceptance Criteria

### Content Security Policy
- [ ] AC1: CSP header configurado no Next.js `middleware.ts`:
  ```
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://js.stripe.com https://cdn.sentry.io;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://*.supabase.co https://api.stripe.com https://*.sentry.io wss://*.supabase.co;
  frame-src https://js.stripe.com;
  ```
- [ ] AC2: CSP report-only mode first (`Content-Security-Policy-Report-Only`), depois enforce
- [ ] AC3: `X-Content-Type-Options: nosniff` header
- [ ] AC4: `X-Frame-Options: DENY` header

### Error Sanitization
- [ ] AC5: Backend: NUNCA retorna stack traces em responses (production mode)
- [ ] AC6: Excel export errors retornam mensagem genérica + correlation_id
- [ ] AC7: Sentry captura o erro completo (stack trace + context)
- [ ] AC8: Log sanitization: `log_sanitizer.py` cobre novos endpoints

### LGPD Compliance
- [ ] AC9: Página `/privacidade` atualizada com:
  - Base legal para cada tipo de tratamento (Art. 7° LGPD)
  - Dados coletados explicitamente listados
  - Período de retenção para cada categoria
  - Direitos do titular (Art. 18° LGPD)
  - Contato do encarregado (DPO)
- [ ] AC10: Cookie consent banner (se não existir)
- [ ] AC11: Endpoint `DELETE /me` para exclusão de dados (Art. 18° V LGPD)

### Quality
- [ ] AC12: Security headers verificados com `securityheaders.com`
- [ ] AC13: Zero erros no CSP report
- [ ] AC14: Testes existentes passando

## Files to Change

- `frontend/middleware.ts` — CSP + security headers
- `backend/main.py` — error handler sanitization
- `backend/excel.py` — sanitize error responses
- `backend/log_sanitizer.py` — extend coverage
- `frontend/app/privacidade/page.tsx` — LGPD content update
- `backend/routes/user.py` — DELETE /me endpoint

## Definition of Done

- [ ] Security headers: A+ no securityheaders.com
- [ ] Zero stack traces em production responses
- [ ] LGPD compliance documentada
- [ ] Todos os testes passando
- [ ] PR merged
