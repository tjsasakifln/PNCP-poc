# FRENTE 2 -- SECURITY AUDIT REPORT

**Auditor:** Claude Opus 4.6 (Automated Security Audit)
**Date:** 2026-02-12
**Scope:** SmartLic/BidIQ full-stack application (backend + frontend)
**Commit:** f1d7fdb (main branch)

---

## Executive Summary

**Overall Security Posture: MEDIUM RISK -- Conditionally GTM-Ready**

The SmartLic codebase demonstrates **above-average security awareness** for a Brazilian SaaS startup at POC/early-production stage. Notable positives include comprehensive log sanitization (Issue #168), atomic quota operations to prevent TOCTOU race conditions (Issue #189), UUID validation on admin endpoints (Issue #203), PostgREST injection prevention (Issue #205), Stripe webhook signature verification, and PKCE-based OAuth.

However, **seven findings require remediation before GTM**, the most critical being an open debug endpoint that leaks infrastructure details, a path traversal vulnerability in the download route, a JWT token cache collision that could cause identity confusion, and the fallback encryption key that defaults to all-zeros.

**CRITICAL: 2 findings | HIGH: 5 findings | MEDIUM: 8 findings | LOW: 6 findings**

---

## 1. Authentication & Session Security

### 1.1 JWT Validation -- Audience Verification Disabled

**File:** `backend/auth.py:89-95`
**Severity: HIGH**

```python
payload = jwt.decode(
    token,
    jwt_secret,
    algorithms=["HS256"],
    audience="authenticated",  # Supabase default audience
    options={"verify_aud": False}  # Relax audience check for compatibility
)
```

The `verify_aud: False` option disables audience claim verification. This means a JWT issued for a *different* Supabase project sharing the same signing key (e.g., in a multi-tenant environment or if the JWT secret leaks) could be accepted. The code even sets the correct `audience="authenticated"` but then immediately disables verification of it.

**Risk:** If `SUPABASE_JWT_SECRET` is shared or leaked, any JWT from any Supabase project using that secret would be accepted.

**Recommendation:** Remove `options={"verify_aud": False}` and ensure `audience="authenticated"` is actually verified. Test thoroughly -- if any legitimate tokens fail, investigate the root cause rather than disabling verification.

### 1.2 Token Cache Key Collision -- Identity Confusion

**File:** `backend/auth.py:58`
**Severity: CRITICAL**

```python
token_hash = hashlib.sha256(token[:16].encode('utf-8')).hexdigest()
```

Only the first 16 characters of the JWT are used for the cache key hash. All Supabase JWTs using HS256 start with the same base64-encoded header (e.g., `eyJhbGciOiJIUzI1`). This means the SHA256 hash of the first 16 characters produces the **same cache key for every single token**. The cache will contain exactly one entry, and whichever user's token was validated first within the 60-second TTL window will have their identity returned for ALL subsequent requests.

**Risk:** Complete authentication bypass -- User A authenticates, their identity is cached. User B (or an unauthenticated attacker with any valid-looking JWT) sends a request within 60 seconds and receives User A's identity from cache. This is a **session fixation / identity confusion** vulnerability.

**Recommendation:** Hash the **entire token** to generate the cache key:
```python
token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
```

### 1.3 OAuth State Parameter -- Weak CSRF Protection

**File:** `backend/routes/auth_oauth.py:82-84`
**Severity: MEDIUM**

```python
state = base64.urlsafe_b64encode(
    f"{user['id']}:{redirect}".encode()
).decode()
```

The OAuth state parameter encodes `user_id:redirect_path` in base64, but this is **not cryptographically signed or unpredictable**. An attacker who knows (or guesses) the user's UUID and desired redirect path can forge the state parameter. The purpose of the state parameter is CSRF protection -- it should be unpredictable.

**Risk:** CSRF on OAuth callback. An attacker could craft a state parameter and trick a victim into authorizing Google Sheets access that links to the attacker's account.

**Recommendation:** Include a cryptographic nonce (e.g., `secrets.token_urlsafe(32)`) in the state, store it in a server-side session or signed cookie, and verify it on callback.

### 1.4 Session Management -- Good Practices Observed

**File:** `frontend/middleware.ts:122-126`
**Severity: INFORMATIONAL (Positive Finding)**

The frontend middleware correctly uses `getUser()` instead of `getSession()` for server-side validation:
```typescript
const { data: { user }, error } = await supabase.auth.getUser();
```

This is the secure approach -- `getUser()` validates the session against the Supabase Auth server, while `getSession()` only reads the local JWT without server verification. This prevents tampered JWTs from being accepted on the frontend.

### 1.5 Frontend Supabase Client -- PKCE Flow Correctly Used

**File:** `frontend/lib/supabase.ts:14-18`
**Severity: INFORMATIONAL (Positive Finding)**

```typescript
export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey, {
  auth: { flowType: "pkce" },
});
```

PKCE (Proof Key for Code Exchange) is the correct choice for browser-based OAuth. This prevents authorization code interception attacks.

### 1.6 Cookie Security Settings

**File:** `frontend/middleware.ts:110-117`
**Severity: LOW**

Cookies are set with `secure: process.env.NODE_ENV === "production"` and `sameSite: "lax"`. The `httpOnly` flag is not explicitly set -- it depends on Supabase SSR defaults. Supabase SSR typically handles this correctly, but explicit enforcement would be more robust.

**Risk:** If Supabase SSR defaults change in a future version, cookies could become accessible to JavaScript.

**Recommendation:** Explicitly set `httpOnly: true` for auth cookies.

### Section Risk Level: CRITICAL (due to cache key collision)

---

## 2. Authorization & Access Control

### 2.1 Admin Authorization -- Properly Implemented

**File:** `backend/admin.py:212-233`
**Severity: INFORMATIONAL (Positive Finding)**

All admin endpoints use `Depends(require_admin)` which checks both `ADMIN_USER_IDS` environment variable and `profiles.is_admin` from Supabase. Admin IDs from environment variables are validated as UUID v4 format (Issue #203). All 8 admin endpoints are protected.

### 2.2 IDOR Risk -- Properly Mitigated

**File:** `backend/routes/sessions.py:26-30`
**Severity: LOW**

Sessions are properly filtered by `user_id` from the authenticated JWT, preventing IDOR. However, the backend uses the **service role key** (which bypasses RLS), so the application-level filter is the sole protection. If a code bug were to omit the `.eq("user_id", ...)` filter, all user data would be exposed.

**Recommendation:** Enable RLS on all user-data tables as defense-in-depth, even though the backend uses service role key.

### 2.3 Unauthenticated Endpoints Audit

The following backend endpoints require NO authentication:

| Endpoint | File | Risk Assessment |
|----------|------|-----------------|
| `GET /` | `main.py:164` | Safe -- returns API metadata only |
| `GET /health` | `main.py:193` | Safe -- health check (standard practice) |
| `GET /sources/health` | `main.py:269` | Safe -- source health info |
| `GET /setores` | `main.py:359` | Safe -- public sector list |
| `GET /debug/pncp-test` | `main.py:365` | **HIGH** -- exposes PNCP API connectivity details |
| `GET /plans` | `routes/billing.py:18` | Safe -- public plan catalog |
| `GET /api/plans` | `routes/plans.py:44` | **MEDIUM** -- exposes Stripe price IDs |
| `POST /webhooks/stripe` | `webhooks/stripe.py:51` | Safe -- verified via Stripe signature |
| `GET /openapi.json` | FastAPI default | **MEDIUM** -- exposes full API schema |
| `GET /docs` | FastAPI default | **MEDIUM** -- exposes Swagger UI |
| `GET /redoc` | FastAPI default | **MEDIUM** -- exposes ReDoc UI |

All authenticated endpoints were verified: 28 endpoints across 12 route modules use `Depends(require_auth)` or `Depends(require_admin)`.

### 2.4 Quota Bypass -- Fail-Open on Error

**File:** `backend/routes/search.py:383-405`
**Severity: MEDIUM**

When the quota check fails with an unexpected exception, the system falls back to allowing the request with `quota_remaining=999999`. This is a conscious design decision ("fail open") documented in the code, balancing availability vs. quota enforcement.

**Risk:** If Supabase is unreachable for an extended period, all users effectively have unlimited access.

**Recommendation:** Add monitoring/alerting on quota fallback activation. Consider a circuit breaker that blocks after N consecutive fallback activations within a time window.

### Section Risk Level: MEDIUM

---

## 3. Input Validation & Injection Prevention

### 3.1 No eval/exec/subprocess Usage

**Severity: INFORMATIONAL (Positive Finding)**

No instances of `eval()`, `exec()`, or `subprocess` were found in the backend Python code. The application does not execute shell commands or dynamically evaluate code.

### 3.2 dangerouslySetInnerHTML -- Safe Usage

**File:** `frontend/app/layout.tsx:72-88`
**Severity: LOW**

The only use of `dangerouslySetInnerHTML` is for a hardcoded theme-detection script in the HTML `<head>`. This is a static, developer-authored string with no user input interpolation. This is a standard pattern for preventing FOUC (Flash of Unstyled Content) in dark-mode implementations and is **safe**.

### 3.3 PostgREST Injection Prevention -- Well Implemented

**File:** `backend/admin.py:37-98`
**Severity: INFORMATIONAL (Positive Finding)**

Search input sanitization strips dangerous characters, SQL comment markers (`--`), and PostgREST operators (`.eq.`, `.ilike.`, etc.). Input length is limited to 100 characters. This addresses Issue #205 comprehensively.

### 3.4 Pydantic Validation on API Inputs

**File:** `backend/schemas.py`
**Severity: INFORMATIONAL (Positive Finding)**

All API request bodies use Pydantic models with proper validation:
- UUID validation pattern for user IDs (Issue #203)
- Plan ID validation against allowed pattern
- Date pattern validation
- Enum validation for status, modalidade, esfera

### 3.5 Download Route -- Path Traversal + Open Redirect

**File:** `frontend/app/api/download/route.ts:27-29, 42`
**Severity: CRITICAL**

```typescript
// Line 27-29: Open redirect via unvalidated URL parameter
if (url) {
    return NextResponse.redirect(url);
}

// Line 42: Path traversal via download ID
const filePath = join(tmpDir, `bidiq_${id}.xlsx`);
```

**Two vulnerabilities in one endpoint:**

1. **Open Redirect:** The `url` query parameter is passed directly to `NextResponse.redirect()` without any validation. An attacker could craft a URL like `/api/download?url=https://evil.com/phishing` to redirect authenticated users to a malicious site through SmartLic's trusted domain.

2. **Path Traversal:** The `id` parameter is used directly in filesystem path construction. While the `bidiq_` prefix and `.xlsx` suffix provide some protection, an `id` like `../../../etc/passwd` would produce a path like `/tmp/bidiq_../../../etc/passwd.xlsx` -- `join()` on some platforms resolves `..` segments. The auth check only verifies Bearer token presence (not validity), so the endpoint is accessible to anyone with any Bearer string.

**Risk:** Open redirect is directly exploitable for phishing campaigns using SmartLic's domain reputation. Path traversal risk depends on platform behavior.

**Recommendation:**
- Validate `url` against a whitelist of allowed domains (e.g., Supabase storage domain only)
- Validate `id` with a UUID-only regex pattern (`/^[0-9a-f-]{36}$/`) before constructing file paths
- Use `path.resolve()` and verify the resulting path starts with `tmpdir()` before serving

### Section Risk Level: CRITICAL

---

## 4. Transport & Data Security

### 4.1 CORS Configuration -- Properly Restrictive

**File:** `backend/config.py:247-332`
**Severity: INFORMATIONAL (Positive Finding)**

CORS is well-implemented:
- Wildcard `*` is explicitly rejected with a warning
- Production origins are auto-detected from Railway environment variables
- Development defaults are restricted to `localhost:3000` and `127.0.0.1:3000`
- Production domains are explicitly whitelisted

### 4.2 CORS Missing Custom Domain

**File:** `backend/config.py:241-244`
**Severity: MEDIUM**

```python
PRODUCTION_ORIGINS: list[str] = [
    "https://bidiq-frontend-production.up.railway.app",
    "https://bidiq-uniformes-production.up.railway.app",
]
```

The custom domain `https://smartlic.tech` is NOT in the hardcoded `PRODUCTION_ORIGINS` list. It may be set via `CORS_ORIGINS` env var, but if that var is unset, the frontend at `smartlic.tech` would be blocked by CORS.

**Recommendation:** Add `https://smartlic.tech` and `https://www.smartlic.tech` to `PRODUCTION_ORIGINS`.

### 4.3 Sensitive Data in Logs -- Comprehensive Sanitization

**File:** `backend/log_sanitizer.py`
**Severity: INFORMATIONAL (Positive Finding)**

The log sanitization module is thorough:
- Emails masked (`u***@example.com`)
- API keys masked (`sk-***cdef`)
- JWT tokens masked (`eyJ***[JWT]`)
- User IDs partially masked (`550e8400-***`)
- Passwords fully redacted (`[PASSWORD_REDACTED]`)
- IP addresses partially masked (`192.168.x.x`)
- Auto-detection of sensitive patterns in free-text strings
- Production logs suppress DEBUG level (Issue #168)

### 4.4 Debug Endpoint Exposes Infrastructure Details

**File:** `frontend/app/api/debug/env-check/route.ts`
**Severity: CRITICAL**

This endpoint is accessible **without authentication** (frontend API routes bypass middleware per `middleware.ts:37-39`) and exposes:
- `NEXT_PUBLIC_CANONICAL_URL` value
- `NEXT_PUBLIC_SUPABASE_URL` value
- First 20 characters of `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `BACKEND_URL` value (internal service URL)
- OAuth redirect URL configuration
- Infrastructure configuration issues

The file itself contains: `DELETE THIS FILE after debugging is complete!`

**Risk:** Leaks internal infrastructure URLs and partial API keys. The `BACKEND_URL` is particularly sensitive as it reveals the internal service-to-service topology.

**Recommendation:** **Delete this file immediately.** It was a temporary debugging tool.

### 4.5 OpenAPI/Swagger Exposed in Production

**File:** `backend/main.py:57-68`
**Severity: HIGH**

```python
app = FastAPI(
    ...
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

The OpenAPI schema, Swagger UI, and ReDoc are available without authentication. This reveals the complete API surface including all endpoints, parameters, models, error codes, and authentication schemes.

**Recommendation:** Disable in production:
```python
is_prod = os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")
app = FastAPI(
    ...
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json",
)
```

### 4.6 Encryption Key Fallback to Insecure Default

**File:** `backend/oauth.py:51-56`
**Severity: HIGH**

```python
if not ENCRYPTION_KEY_B64:
    logger.warning("ENCRYPTION_KEY not set. Generate with: openssl rand -base64 32")
    ENCRYPTION_KEY_B64 = base64.urlsafe_b64encode(b"0" * 32).decode()
```

If `ENCRYPTION_KEY` is not set, the code falls back to a hardcoded all-zeros key. This key is visible in the source code. If this reaches production, all OAuth tokens would be encrypted with a known key -- effectively stored in plaintext.

**Risk:** If `ENCRYPTION_KEY` is accidentally unset in production, all Google OAuth tokens become recoverable by anyone with database read access and source code.

**Recommendation:** Raise a `RuntimeError` instead of using a fallback key when `ENVIRONMENT=production`. The warning-only approach is insufficient.

### 4.7 .gitignore Coverage for Secrets

**File:** `.gitignore`
**Severity: INFORMATIONAL (Positive Finding)**

The `.gitignore` properly excludes:
- `.env`, `.env.*` (root level)
- `backend/.env*` (backend specific)
- `frontend/.env*` (frontend specific)
- `.env.local`, `.env.*.local` patterns
- `.env.example` files are correctly included (not ignored)

### Section Risk Level: CRITICAL (due to debug endpoint)

---

## 5. Rate Limiting & DoS Protection

### 5.1 Rate Limiting -- Plan-Based, Redis-Backed

**File:** `backend/rate_limiter.py`
**Severity: INFORMATIONAL (Positive Finding)**

Rate limiting is implemented with Redis as primary storage and in-memory fallback. Limits are plan-based (`max_requests_per_min` from plan capabilities). Memory store has LRU eviction at 10,000 entries (STORY-203 SYS-M03).

### 5.2 Rate Limiting on Search Endpoint

**File:** `backend/routes/search.py:311-336`
**Severity: INFORMATIONAL (Positive Finding)**

The `/buscar` endpoint checks per-minute rate limits before processing. Admin/master users bypass rate limits. `Retry-After` header is returned on 429 responses.

### 5.3 No Rate Limiting on Auth-Sensitive Endpoints

**File:** `backend/routes/user.py:21-41`
**Severity: HIGH**

The following endpoints lack rate limiting:

| Endpoint | Risk |
|----------|------|
| `POST /change-password` | Brute-force password change |
| `POST /checkout` | Excessive Stripe session creation |
| `GET /me` | Information disclosure under rapid polling |
| `POST /admin/users/{id}/reset-password` | Admin endpoint, but still vulnerable |

**Risk:** Brute-force attacks on password change. An attacker with a stolen token could try thousands of new passwords per minute.

**Recommendation:** Apply rate limiting to at minimum `/change-password` (e.g., 5 attempts per 15 minutes per user).

### 5.4 Login Rate Limiting via Supabase

**Severity: MEDIUM**

Login is handled by Supabase Auth. Supabase has built-in rate limiting, but the default limits (typically 30 requests/minute) may be more generous than desired. The application does not add additional rate limiting.

**Recommendation:** Configure Supabase Auth rate limits in the dashboard. Consider adding CAPTCHA after failed attempts.

### 5.5 Rate Limiter Fails Open

**File:** `backend/rate_limiter.py:84-86`
**Severity: LOW**

Redis errors cause rate limiting to fail open. This is a conscious design choice but means Redis outages disable rate limiting entirely.

### Section Risk Level: HIGH

---

## 6. LGPD Compliance

### 6.1 Data Minimization

**Severity: MEDIUM**

The application collects:
- Email address (required for auth)
- Full name (optional, `profiles.full_name`)
- Company name (optional, `profiles.company`)
- Search history (`search_sessions` table)
- Google OAuth tokens (encrypted, `user_oauth_tokens`)
- Stripe customer/subscription IDs (`user_subscriptions`)
- Monthly search usage (`monthly_quota`)

Collection is generally proportionate. Search history is a user-facing feature.

**Recommendation:** Document collected data in a privacy policy.

### 6.2 Data Retention -- No Defined Policy

**Severity: MEDIUM**

No evidence of:
- Automatic expiration/deletion for search sessions
- Cleanup of old `monthly_quota` records
- Cleanup of `stripe_webhook_events` records
- Expiration of `user_oauth_tokens` after prolonged inactivity

**Risk:** Personal data accumulates indefinitely, violating LGPD data minimization principle (Art. 6, III).

**Recommendation:** Define retention periods and implement automated cleanup jobs.

### 6.3 Right to Data Deletion -- No Self-Service

**Severity: MEDIUM**

- Admin can delete users via `DELETE /admin/users/{user_id}` (cascade via Supabase FK)
- No **self-service** deletion for end users (LGPD Art. 18, V)
- No data export/portability feature (LGPD Art. 18, V)
- Unclear if all related tables cascade-delete (search_sessions, monthly_quota, user_oauth_tokens)

**Recommendation:** Implement self-service "delete my account" or document the manual deletion request process.

### 6.4 Consent Collection

**Severity: LOW**

The signup flow does not appear to collect explicit LGPD consent for data processing. While service usage implies consent, explicit consent with a privacy policy link is recommended.

### 6.5 Log Sanitization -- LGPD Compliant

**File:** `backend/log_sanitizer.py`
**Severity: INFORMATIONAL (Positive Finding)**

Comprehensive log sanitization prevents PII from appearing in log files. This is a strong LGPD compliance measure.

### Section Risk Level: MEDIUM

---

## 7. Stripe/Payment Security

### 7.1 Webhook Signature Verification -- Properly Implemented

**File:** `backend/webhooks/stripe.py:88-98`
**Severity: INFORMATIONAL (Positive Finding)**

Stripe webhook signature verification is correctly implemented with:
- Missing `stripe-signature` header rejection (400)
- Invalid payload rejection (400)
- Signature verification failure rejection (400)
- Idempotency via `stripe_webhook_events` table
- `profiles.plan_type` sync for fallback reliability

### 7.2 PCI Compliance -- Correct Approach

**Severity: INFORMATIONAL (Positive Finding)**

The application uses Stripe Checkout Sessions (redirect mode). Card data never touches SmartLic servers. This is the correct approach for PCI SAQ A compliance.

### 7.3 Stripe Keys via Environment Variables

**Severity: INFORMATIONAL (Positive Finding)**

All Stripe keys (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) are loaded from environment variables and never hardcoded or logged.

### 7.4 Stripe Price IDs in Public API

**File:** `backend/routes/plans.py:105-106`
**Severity: MEDIUM**

The public `/api/plans` endpoint returns `stripe_price_id_monthly` and `stripe_price_id_annual`. While not secret per se, these provide information about your Stripe product configuration that is unnecessary for the frontend and could be used for reconnaissance.

**Recommendation:** Exclude Stripe price IDs from the public response. The frontend does not need them -- the backend handles checkout session creation.

### Section Risk Level: LOW

---

## 8. Prioritized Security Risks

| # | Risk | Severity | Exploitability | File Reference | Recommended Fix |
|---|------|----------|---------------|----------------|-----------------|
| 1 | Token cache key uses identical JWT prefix -- identity confusion for all users | **CRITICAL** | **High** -- affects every request | `backend/auth.py:58` | Hash the full token, not first 16 chars |
| 2 | Debug env-check endpoint leaks infrastructure details | **CRITICAL** | **Trivial** -- no auth, public URL | `frontend/app/api/debug/env-check/route.ts` | **Delete the file** |
| 3 | Download route open redirect + path traversal | **CRITICAL** | **Medium** -- requires crafted URL | `frontend/app/api/download/route.ts:27-29,42` | Validate URL domain; validate ID as UUID |
| 4 | JWT audience verification disabled | **HIGH** | Low -- requires JWT secret leak | `backend/auth.py:94` | Remove `verify_aud: False` |
| 5 | Encryption key falls back to all-zeros | **HIGH** | Low -- requires env misconfiguration | `backend/oauth.py:51-56` | Raise error in production |
| 6 | No rate limiting on `/change-password` | **HIGH** | **Medium** -- automated brute force | `backend/routes/user.py:21` | Add per-user rate limit |
| 7 | OpenAPI/Swagger exposed without auth | **HIGH** | **Trivial** -- publicly accessible | `backend/main.py:65-68` | Disable in production |
| 8 | `/debug/pncp-test` unauthenticated | **HIGH** | **Trivial** -- reveals connectivity | `backend/main.py:365` | Add `require_admin` or remove |
| 9 | OAuth state parameter is predictable | **MEDIUM** | Medium -- requires user ID | `backend/routes/auth_oauth.py:82-84` | Include cryptographic nonce |
| 10 | CORS missing `smartlic.tech` domain | **MEDIUM** | Low -- may be set via env var | `backend/config.py:241-244` | Add to `PRODUCTION_ORIGINS` |
| 11 | Quota check fails open with unlimited access | **MEDIUM** | Low -- requires DB outage | `backend/routes/search.py:383-405` | Add circuit breaker / monitoring |
| 12 | No data retention policy (LGPD) | **MEDIUM** | N/A -- compliance | Multiple files | Define and implement retention |
| 13 | No self-service account deletion (LGPD) | **MEDIUM** | N/A -- compliance | N/A | Implement delete account |
| 14 | No rate limiting on Supabase login | **MEDIUM** | Medium -- brute force | Supabase Auth | Configure rate limits |
| 15 | Stripe price IDs in public API | **MEDIUM** | Trivial | `routes/plans.py:105-106` | Exclude from response |
| 16 | Password minimum length only 6 chars | **LOW** | Low | `backend/routes/user.py:29` | Increase to 8+ |
| 17 | Rate limiter fails open on Redis error | **LOW** | Low -- requires Redis outage | `backend/rate_limiter.py:84-86` | Add fallback tracking |
| 18 | No explicit `httpOnly` on auth cookies | **LOW** | Low -- defaults may be correct | `frontend/middleware.ts:110-117` | Explicitly set |
| 19 | No CAPTCHA on signup/login | **LOW** | Medium -- automated creation | Supabase Auth | Add reCAPTCHA |
| 20 | No explicit LGPD consent checkbox | **LOW** | N/A -- compliance | Frontend signup | Add consent checkbox |
| 21 | Incomplete user ID masking in some log paths | **LOW** | Low -- requires log access | `backend/routes/user.py:66` | Use `mask_user_id` consistently |

---

## 9. Security Debt Summary

### MUST Fix Before GTM (P0 -- Blocking)

These items are actively exploitable or represent compliance-blocking issues:

| # | Item | Effort | File |
|---|------|--------|------|
| 1 | **Fix token cache key** -- hash full token instead of first 16 chars | 15 min | `backend/auth.py:58` |
| 2 | **Delete `debug/env-check/route.ts`** | 1 min | `frontend/app/api/debug/env-check/route.ts` |
| 3 | **Fix download route** -- validate URL domain + validate ID as UUID | 30 min | `frontend/app/api/download/route.ts` |
| 4 | **Enable JWT audience verification** -- remove `verify_aud: False` | 15 min | `backend/auth.py:94` |
| 5 | **Disable docs/redoc/openapi in production** | 10 min | `backend/main.py:65-68` |
| 6 | **Remove or protect `/debug/pncp-test`** | 5 min | `backend/main.py:365` |
| 7 | **Fix encryption key fallback** -- raise error in production | 10 min | `backend/oauth.py:51-56` |

**Total estimated effort for P0 blockers: ~1.5 hours**

### Should Fix Before GTM (P1 -- High Priority)

| # | Item | Effort |
|---|------|--------|
| 8 | Add rate limiting to `/change-password` | 30 min |
| 9 | Add `smartlic.tech` to CORS `PRODUCTION_ORIGINS` | 5 min |
| 10 | Strengthen OAuth state parameter with cryptographic nonce | 1 hour |
| 11 | Increase minimum password length to 8+ characters | 10 min |
| 12 | Remove Stripe price IDs from public `/api/plans` response | 15 min |

**Total estimated effort for P1: ~2 hours**

### Can Wait Post-GTM (P2 -- Technical Debt)

| # | Item | Effort |
|---|------|--------|
| 13 | LGPD data retention policy + automated cleanup | 4 hours |
| 14 | Self-service account deletion feature | 8 hours |
| 15 | LGPD consent checkbox on signup | 2 hours |
| 16 | Add CAPTCHA to login/signup | 2 hours |
| 17 | Add monitoring/alerting on quota fallback activation | 2 hours |
| 18 | Enable RLS on all Supabase tables as defense-in-depth | 4 hours |
| 19 | Explicit `httpOnly` cookie enforcement | 30 min |
| 20 | Circuit breaker for quota check failures | 3 hours |

---

## Appendix A: Security Strengths

The following items represent good security practices already in place:

1. **Log Sanitization (Issue #168):** Comprehensive PII protection in logs with dedicated `log_sanitizer.py` module
2. **Atomic Quota Operations (Issue #189):** TOCTOU race condition prevention via PostgreSQL atomic functions
3. **UUID Validation (Issue #203):** All admin endpoint parameters validated as UUID v4
4. **PostgREST Injection Prevention (Issue #205):** Search input sanitization strips operators and comment markers
5. **Stripe Webhook Verification:** Proper signature validation with idempotency
6. **PKCE OAuth Flow:** Correct implementation preventing code interception
7. **Frontend getUser() over getSession():** Server-validated sessions prevent JWT tampering
8. **Structured Error Types:** Custom exception hierarchy (PNCPAPIError, PNCPRateLimitError)
9. **No eval/exec/subprocess:** Zero dynamic code execution
10. **Production Log Level Enforcement:** DEBUG suppressed in production

## Appendix B: Files Audited

### Backend (22 files)
- `backend/auth.py`, `backend/authorization.py`, `backend/admin.py`
- `backend/config.py`, `backend/log_sanitizer.py`, `backend/main.py`
- `backend/middleware.py`, `backend/oauth.py`, `backend/quota.py`
- `backend/rate_limiter.py`, `backend/schemas.py`, `backend/supabase_client.py`
- `backend/routes/auth_oauth.py`, `backend/routes/billing.py`
- `backend/routes/features.py`, `backend/routes/messages.py`
- `backend/routes/plans.py`, `backend/routes/search.py`
- `backend/routes/sessions.py`, `backend/routes/subscriptions.py`
- `backend/routes/user.py`, `backend/webhooks/stripe.py`

### Frontend (10 files)
- `frontend/middleware.ts`, `frontend/lib/supabase.ts`, `frontend/lib/supabase-server.ts`
- `frontend/app/layout.tsx`
- `frontend/app/api/admin/[...path]/route.ts`, `frontend/app/api/buscar/route.ts`
- `frontend/app/api/change-password/route.ts`, `frontend/app/api/debug/env-check/route.ts`
- `frontend/app/api/download/route.ts`, `frontend/app/api/me/route.ts`

### Configuration (1 file)
- `.gitignore`

---

*Report generated by Claude Opus 4.6 automated security audit. All findings reference specific files and line numbers from commit f1d7fdb on main branch. Date: 2026-02-12.*
