# STORY-311: Security Headers + Hardening

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 1 (Pre-GTM)
**Priority:** HIGH
**Story Points:** 3 SP
**Estimate:** 1-2 dias
**Owner:** @dev + @devops

---

## Problem

Headers de seguranca existem em modo Report-Only (CSP) e alguns sao redundantes entre `next.config.js` e `middleware.ts`. Para producao pre-launch, precisamos:
1. Promover CSP de Report-Only para Enforce
2. Auditar e unificar headers
3. Adicionar protecoes ausentes no backend
4. Rate limiting adequado para APIs publicas

## Solution

Auditoria e hardening completo de seguranca HTTP em frontend e backend, com CSP enforcement gradual e rate limiting reforçado.

---

## Acceptance Criteria

### Frontend — CSP Enforcement

- [ ] **AC1:** Promover CSP de `Content-Security-Policy-Report-Only` para `Content-Security-Policy` em `next.config.js:57` e `middleware.ts:38`
- [ ] **AC2:** Configurar CSP report-uri para endpoint de coleta (Sentry CSP ou custom):
  - `report-uri /api/csp-report`
  - `report-to` directive com Reporting API v1
- [ ] **AC3:** Criar endpoint `frontend/app/api/csp-report/route.ts` que:
  - Recebe violation reports (POST JSON)
  - Log estruturado com: `violated_directive`, `blocked_uri`, `document_uri`
  - Rate limit: max 100 reports/min para evitar flood
- [ ] **AC4:** Auditar e whitelist todos os dominios necessarios no CSP:
  - `script-src`: self, Sentry, Mixpanel, Stripe.js
  - `connect-src`: self, API backend, Supabase, Sentry, Mixpanel, Stripe
  - `frame-src`: Stripe (checkout iframe)
  - `img-src`: self, Supabase storage, data:, blob:
  - `style-src`: self, 'unsafe-inline' (Tailwind requer)
- [ ] **AC5:** Remover duplicacao de headers entre `next.config.js` e `middleware.ts` — unificar em um so local (preferir middleware para controle dinamico)

### Frontend — Headers Adicionais

- [ ] **AC6:** Adicionar `Cross-Origin-Opener-Policy: same-origin` (previne Spectre-like attacks)
- [ ] **AC7:** Adicionar `Cross-Origin-Embedder-Policy: require-corp` (se nao quebrar iframes Stripe)
- [ ] **AC8:** Adicionar `X-DNS-Prefetch-Control: off` (previne DNS leak de links em emails)

### Backend — Security Middleware

- [ ] **AC9:** Auditar `SecurityHeadersMiddleware` em `backend/main.py`:
  - Garantir mesmos headers do frontend (HSTS, X-Content-Type, X-Frame, Referrer-Policy)
  - Adicionar `Cache-Control: no-store` em endpoints autenticados
- [ ] **AC10:** Rate limiting por IP em endpoints publicos:
  - `/health`: 60 req/min
  - `/plans`: 30 req/min
  - `/webhook/stripe`: sem limit (Stripe IPs)
  - `/buscar`: usar token bucket existente (Redis)
- [ ] **AC11:** Adicionar `Permissions-Policy` no backend alinhado com frontend

### Backend — Input Validation Hardening

- [ ] **AC12:** Auditar todos os endpoints para SQL injection patterns:
  - Garantir que Supabase client escapa inputs (ORM-level protection)
  - Validar que nenhum raw SQL e construido com string concatenation
- [ ] **AC13:** Auditar `term_parser.py` para ReDoS (regex denial of service):
  - Limitar tamanho maximo de input de busca (256 chars)
  - Timeout em regex matching (re com timeout nao existe nativo, usar signal/thread)
- [ ] **AC14:** Validar que `log_sanitizer.py` sanitiza todos os campos sensiveis:
  - user_id (parcial), email (mascarado), access_token (nunca logado)

### Infra — HTTPS / TLS

- [ ] **AC15:** Verificar que Railway forca HTTPS redirect (nao aceita HTTP)
- [ ] **AC16:** Verificar HSTS preload elegibility (max-age >= 31536000, includeSubDomains, preload directive)
- [ ] **AC17:** Submeter `smartlic.tech` para HSTS preload list (hstspreload.org) se elegivel

### Testes

- [ ] **AC18:** Teste automatizado que valida presenca de todos os headers esperados em responses
- [ ] **AC19:** Teste CSP violation report endpoint
- [ ] **AC20:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| CSP (Report-Only) | `frontend/next.config.js:57-73` | Existe, precisa enforce |
| Security headers (FE) | `frontend/middleware.ts:22-53` | Existe, duplicado |
| Security headers (FE) | `frontend/next.config.js:27-76` | Existe, duplicado |
| SecurityHeadersMiddleware (BE) | `backend/main.py:50` | Existe, auditar |
| Rate limiting (Redis) | `backend/auth.py` token bucket | Existe |
| Log sanitizer | `backend/log_sanitizer.py` | Existe |
| Header tests | `frontend/__tests__/middleware-security-headers.test.ts` | Existe |

## Files Esperados (Output)

**Novos:**
- `frontend/app/api/csp-report/route.ts`
- `backend/tests/test_security_headers.py`

**Modificados:**
- `frontend/next.config.js`
- `frontend/middleware.ts`
- `backend/main.py`

## Dependencias

- Nenhuma (independente)

## Riscos

- CSP enforce pode quebrar funcionalidades se whitelist incompleta — monitorar CSP reports apos deploy
- `Cross-Origin-Embedder-Policy` pode bloquear iframe do Stripe Checkout — testar antes de enforce
- HSTS preload e irreversivel (requer HTTPS para sempre no dominio)
