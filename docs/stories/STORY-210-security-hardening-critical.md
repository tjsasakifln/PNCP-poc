# STORY-210: Security Hardening — Critical & High Fixes

**Status:** Pending
**Priority:** P0 — Blocks GTM Launch
**Sprint:** Sprint 1 (Week 1)
**Estimated Effort:** 3 days
**Source:** AUDIT-FRENTE-2-SECURITY (CRIT-01→04, HIGH-01→06), AUDIT-CONSOLIDATED (Tier 0 + Tier 1)
**Squad:** team-bidiq-backend (architect, dev, qa)

---

## Context

The security audit identified 4 CRITICAL and 6 HIGH findings. Several are exploitable today in production. The token cache collision (CVSS 9.1) can cause complete identity confusion between users. The debug endpoint leaks infrastructure details. The encryption fallback uses an all-zeros hardcoded key.

## Problem

1. **Token cache key collision** — `auth.py:58` hashes only first 16 chars of JWT. All Supabase HS256 tokens share the same 16-char prefix (`eyJhbGciOiJIUzI1`). User B gets User A's cached identity within 60s window.
2. **Debug env-check endpoint** — `frontend/app/api/debug/env-check/route.ts` leaks `BACKEND_URL`, partial `SUPABASE_ANON_KEY`, and OAuth config. No auth required.
3. **Download route open redirect + path traversal** — `frontend/app/api/download/route.ts:27-29,42` redirects to unvalidated URL; path constructed from unsanitized `id` parameter.
4. **Hardcoded encryption fallback** — `backend/oauth.py:51-56` falls back to all-zeros key when `ENCRYPTION_KEY` not set. Source-visible key.
5. **OAuth CSRF forgeable** — `backend/routes/auth_oauth.py:82-84` state param is predictable `base64(user_id:redirect)`. No cryptographic nonce.
6. **JWT audience verification disabled** — `backend/auth.py:94` has `verify_aud: False`.
7. **Swagger/OpenAPI/debug in production** — `backend/main.py:65-68` exposes `/docs`, `/redoc`, `/openapi.json`. Plus `/debug/pncp-test` (line 365) is unauthenticated.
8. **No security headers** — Missing CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
9. **Plans endpoint leaks Stripe Price IDs** — `routes/plans.py:105-106` returns `stripe_price_id_monthly/annual` without auth.
10. **No rate limiting on `/change-password`** — `routes/user.py:21` allows brute-force.

## Impact

- Identity confusion: User A sees User B's data (CVSS 9.1)
- Infrastructure reconnaissance via debug endpoint
- Open redirect enables phishing via trusted domain
- OAuth token compromise if `ENCRYPTION_KEY` unset
- CSRF on Google OAuth linking flow

## Acceptance Criteria

### Tier 0 — Ops Only (0 code changes)

- [ ] AC1: Verify `SUPABASE_JWT_SECRET` is correctly set in Railway production (run health check with test JWT)
- [ ] AC2: Verify `ENCRYPTION_KEY` is set in Railway production (not the all-zeros default)

### Tier 1 — Quick Fixes (< 30 min each)

- [ ] AC3: **Fix token cache key** — `auth.py:58` hashes FULL token: `hashlib.sha256(token.encode('utf-8')).hexdigest()` (remove `[:16]`)
- [ ] AC4: **Delete debug env-check** — Remove `frontend/app/api/debug/env-check/route.ts` entirely
- [ ] AC5: **Fix download open redirect** — Validate `url` parameter against allowed domains (Supabase storage only). Validate `id` with UUID-only regex `/^[0-9a-f-]{36}$/`
- [ ] AC6: **Fix encryption fallback** — Raise `RuntimeError` when `ENCRYPTION_KEY` not set AND `ENVIRONMENT=production` (keep warning for dev)
- [ ] AC7: **Enable JWT audience verification** — Remove `options={"verify_aud": False}` from `auth.py:94`. Test with real production JWT.
- [ ] AC8: **Disable docs in production** — Conditionally set `docs_url=None`, `redoc_url=None`, `openapi_url=None` when `ENVIRONMENT` in `("production", "prod")`
- [ ] AC9: **Protect or remove `/debug/pncp-test`** — Add `Depends(require_admin)` or delete endpoint
- [ ] AC10: **Add security headers middleware** — Add FastAPI middleware for: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()`. Add frontend `headers` in `next.config.js` for CSP and HSTS.
- [ ] AC11: **Remove Stripe Price IDs from public response** — Strip `stripe_price_id_monthly`, `stripe_price_id_annual` from `/api/plans` response
- [ ] AC12: **Rate limit `/change-password`** — Add per-user rate limit (5 attempts per 15 minutes)

### Tier 1 — Moderate Fixes (1-2 hours each)

- [ ] AC13: **Secure OAuth CSRF** — Replace predictable `base64(user_id:redirect)` state param with `secrets.token_urlsafe(32)` nonce stored server-side (Redis or in-memory with TTL). Verify nonce on callback. Validate redirect_path against whitelist.
- [ ] AC14: **Add `smartlic.tech` to CORS** — Add `https://smartlic.tech` and `https://www.smartlic.tech` to `PRODUCTION_ORIGINS` in `config.py`

### Testing

- [ ] AC15: Unit test for full-token cache key (verify different tokens produce different keys)
- [ ] AC16: Unit test for encryption key — production raises error when missing
- [ ] AC17: Unit test for download route — rejects non-UUID ids, rejects external redirect URLs
- [ ] AC18: Unit test for OAuth state — nonce is cryptographically random, callback rejects forged state
- [ ] AC19: Integration test — JWT with wrong audience is rejected
- [ ] AC20: Verify all tests pass after changes (`pytest` + `npm test`)

## Validation Metric

- Zero CRITICAL security findings on re-audit
- `curl https://bidiq-backend-production.up.railway.app/docs` returns 404
- `curl https://bidiq-frontend-production.up.railway.app/api/debug/env-check` returns 404
- Two different JWTs produce different cache keys

## Risk Mitigated

- P0: Identity confusion / session hijacking (CVSS 9.1)
- P0: Infrastructure reconnaissance
- P0: Open redirect phishing
- P0: OAuth token compromise
- P1: CSRF on Google OAuth
- P1: Brute-force password change

## File References

| File | Lines | Change |
|------|-------|--------|
| `backend/auth.py` | 58, 94 | Fix cache key, enable audience verification |
| `backend/oauth.py` | 51-56 | Raise error on missing ENCRYPTION_KEY in prod |
| `backend/routes/auth_oauth.py` | 82-84 | Cryptographic nonce for OAuth state |
| `backend/main.py` | 57-68, 365 | Disable docs in prod, protect debug endpoint |
| `backend/config.py` | 241-244 | Add smartlic.tech to CORS |
| `backend/routes/plans.py` | 105-106 | Strip Stripe Price IDs |
| `backend/routes/user.py` | 21 | Rate limit change-password |
| `frontend/app/api/debug/env-check/route.ts` | ALL | DELETE |
| `frontend/app/api/download/route.ts` | 27-29, 42 | URL validation + UUID validation |
| `frontend/next.config.js` | NEW | Security headers |
