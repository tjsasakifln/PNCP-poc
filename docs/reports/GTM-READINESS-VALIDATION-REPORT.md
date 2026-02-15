# GTM Readiness Validation Report

**Date:** 2026-02-14
**Squad:** QA Lead + Playwright Simulator + DevOps Observer
**Environment:** Production (smartlic.tech / api.smartlic.tech)
**Method:** Manual testing via Playwright MCP simulating 4 user personas

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall GTM Readiness** | **NOT READY** |
| Critical Issues (Blocking) | **3** |
| Major Issues (High Priority) | **4** |
| Minor Issues (Polish) | **4** |
| UX Improvements | **2** |
| **Personas Tested** | 1 of 4 (3 blocked by auth failure) |

**The system is completely non-functional for authenticated users.** A Supabase JWT key rotation from HS256 to ECC P-256 (ES256) 11 days ago broke ALL backend authentication. Every authenticated API endpoint returns 401 Unauthorized.

---

## CRITICAL Issues (System Down / Blocking GTM)

### CRIT-1: JWT Algorithm Mismatch — ALL Authentication Broken

**Severity:** P0 / CRITICAL / SYSTEM DOWN
**Impact:** 100% of authenticated functionality broken
**Affected:** Every logged-in user, every authenticated API endpoint

**Root Cause:**
Supabase rotated the JWT signing key from **Legacy HS256 (Shared Secret)** to **ECC P-256 (ES256)** approximately 11 days ago (around 2026-02-03).

| Setting | Value |
|---------|-------|
| **Current Supabase signing key** | ECC P-256 (Key ID: `86b16415-6286-4650-974f-f9faabddb460`) |
| **Previous key (legacy)** | HS256 (Key ID: `20061205-8ad8-43b9-ae1f-572245ad6c6f`) — rotated 11 days ago |
| **Backend auth.py expects** | `algorithms=["HS256"]` (line ~90) |
| **Tokens arriving** | Signed with ES256 |

**Railway Backend Logs (Feb 13, 2026 21:55 BRT):**
```
Invalid JWT token: InvalidAlgorithmError  funcName: warning  logger_name: auth
GET /me -> 401 (3ms)
GET /api/messages/unread-count -> 401 (3ms)
POST /buscar -> 401 (2ms)
GET /buscar-progress/{search_id} -> 401 (1ms)
```

**Supabase Dashboard Evidence:**
- Settings > JWT Keys > JWT Signing Keys tab shows current key is **ECC (P-256)**
- Settings > JWT Keys > Legacy JWT Secret tab shows migration warning:
  > "Legacy JWT secret has been migrated to new JWT Signing Keys"
- Legacy HS256 secret still visible: `yaoxIpjUyUIckV5j...` (used only for verification of old tokens)

**Fix Required:**
1. **Option A (Recommended):** Update `backend/auth.py` to support ES256 validation using Supabase's JWKS endpoint or the public key from the ECC P-256 keypair
2. **Option B (Quick):** Revert Supabase to HS256 signing (if possible via dashboard)
3. Also update `SUPABASE_JWT_SECRET` in Railway if switching to asymmetric verification (will need the public key, not the shared secret)

**Affected Endpoints (all return 401):**
- `GET /me` — user profile
- `POST /buscar` — search execution
- `GET /buscar-progress/{id}` — SSE progress
- `GET /api/messages/unread-count` — message count
- All other authenticated routes

---

### CRIT-2: CSP (Content Security Policy) Blocks API Communication

**Severity:** P0 / CRITICAL
**Impact:** Frontend cannot communicate with backend API via custom domain

**Details:**
The CSP `connect-src` directive does NOT include `api.smartlic.tech`:

```
connect-src 'self' https://*.supabase.co https://*.supabase.in https://api.stripe.com https://*.railway.app https://*.ingest.sentry.io
```

**Missing:** `https://api.smartlic.tech`

**Console Errors:**
```
Connecting to 'https://api.smartlic.tech/me' violates the following Content Security Policy directive: "connect-src 'self' ..."
Connecting to 'https://api.smartlic.tech/plans' violates the following Content Security Policy directive: "connect-src 'self' ..."
```

**Impact:**
- `/me` endpoint blocked → header shows "Entrar" instead of user avatar
- `/plans` endpoint blocked → plans page shows no plan cards
- Any direct API call to `api.smartlic.tech` is blocked

**Fix:** Add `https://api.smartlic.tech` to the `connect-src` CSP directive in the Next.js config (likely `next.config.js` or middleware headers).

---

### CRIT-3: Plans Page Shows No Plans

**Severity:** P0 / CRITICAL (directly impacts revenue)
**Impact:** Visitors cannot see pricing or subscribe

**Details:**
The `/planos` page only shows the ROI calculator. The actual plan cards (Gratuito, Consultor Ágil, Pro, Enterprise) are **not rendered** because the API call to `GET /plans` is blocked by CSP (see CRIT-2).

**Screenshot:** `persona1-planos-page.png` — shows only "Calcule sua Economia" section, toggle Mensal/Anual, but zero plan cards.

**User Impact:** A visitor who clicks "Ver planos" sees prices for nothing. Conversion funnel is completely broken.

---

## MAJOR Issues (High Priority)

### MAJ-1: Header Shows "Entrar" for Logged-In Users

**Severity:** P1 / MAJOR
**Impact:** User confusion, broken navigation
**Page:** `/buscar`

**Details:**
Even with valid Supabase auth cookies present in the browser, the `/buscar` page header displays "Entrar" and "Criar conta" links instead of the user's name/avatar and logout option.

**Root Causes (compound):**
1. CSP blocks the call to `api.smartlic.tech/me` (CRIT-2)
2. Even if CSP is fixed, the backend would return 401 due to JWT mismatch (CRIT-1)

**User Experience:** User logs in successfully, sees success toast "Login realizado com sucesso!", but then the header doesn't recognize them.

---

### MAJ-2: Search Fails with 401 Loop

**Severity:** P1 / MAJOR
**Impact:** Core feature completely broken

**Details:**
When logged-in user clicks "Buscar":
1. `POST /api/buscar` returns 401
2. SSE connection to `/buscar-progress/{id}` also returns 401
3. User is redirected to `/login`
4. Login page says "Você já está autenticado!"
5. User clicks "Ir para o painel" → goes back to `/buscar` → tries again → 401 → infinite loop

**Railway Logs:**
```
POST /buscar -> 401 (2ms) [req_id=7d128e9f-2c87-4968-a08a-17240efa4030]
GET /buscar-progress/e7153738-... -> 401 (1ms) [req_id=bef57397-...]
```

---

### MAJ-3: Login Page Missing "Forgot Password" Link

**Severity:** P1 / MAJOR
**Impact:** Users locked out cannot recover accounts
**Page:** `/login`

**Details:**
The login page has email/password fields and "Entrar com Google" but NO "Esqueci minha senha" link. The FAQ at `/ajuda` explicitly mentions this feature exists:
> "Na tela de login, clique em 'Esqueci minha senha'"

But the link is absent from the actual login UI.

---

### MAJ-4: Footer "Central de Ajuda" Links to /mensagens Instead of /ajuda

**Severity:** P1 / MAJOR
**Impact:** Dead end for unauthenticated users seeking help
**Pages:** `/buscar` footer, potentially other pages

**Details:**
The footer on `/buscar` has:
- "Central de Ajuda" → links to `/mensagens` (requires login)
- "Contato" → links to `/mensagens` (requires login)

Should be:
- "Central de Ajuda" → `/ajuda` (public page that exists and works)
- "Contato" → could remain `/mensagens` but add email fallback

---

## MINOR Issues (Polish)

### MIN-1: CSP Blocks Cloudflare Insights

**Severity:** P2 / MINOR
**Impact:** Analytics not loading
**Every page**

```
Loading the script 'https://static.cloudflareinsights.com/beacon.min.js/...' violates the following Content Security Policy directive: "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com"
```

**Fix:** Add `https://static.cloudflareinsights.com` to `script-src` in CSP.

---

### MIN-2: Redirect Reason Says "session_expired" for Never-Logged-In Users

**Severity:** P2 / MINOR
**Impact:** Misleading UX messaging
**Page:** `/login?redirect=...&reason=session_expired`

When an anonymous user tries to access `/buscar` directly, the redirect reason is `session_expired`. Should be `login_required` or similar since there was never a session.

---

### MIN-3: Deprecated Route Warnings in Backend

**Severity:** P2 / MINOR
**Impact:** Technical debt

**Railway Logs:**
```
DEPRECATED route accessed: GET /api/messages/unread-count — migrate to /v1/api/messages/unread-count before 2026-06-01
```

Frontend is still calling deprecated routes.

---

### MIN-4: Header on /buscar Not Translucent Like Landing Page

**Severity:** P2 / MINOR
**Impact:** Visual inconsistency
**Page:** `/buscar` vs `/` (landing)

The landing page header has a translucent/glass effect. The `/buscar` page header is solid/opaque. This creates visual inconsistency across the app.

---

## UX Improvement Opportunities

### UX-1: /mensagens Requires Login but Linked from Public /ajuda

**Current:** FAQ "Enviar Mensagem" button links to `/mensagens` which requires auth → anonymous user hits dead end.
**Suggested:** Add a public contact form or show `suporte@smartlic.tech` email link alongside the button.

---

### UX-2: Signup Page Terms Consent Scroll UX

**Current:** User must scroll the terms text box to the bottom before the checkbox becomes enabled.
**Observation:** This is legally correct but could frustrate users. Consider showing a summary with "Read full terms" expandable section.

---

## Positive Observations

1. **Landing page is excellent** — professional, persuasive, complete with comparison table, testimonials, sectors
2. **Route protection works** — anonymous users correctly redirected to login when accessing protected routes
3. **Cookie consent is LGPD-compliant** — proper consent dialog with reject/accept options
4. **Privacy policy and Terms of Service are complete** — professional legal documents
5. **FAQ/Help page is comprehensive** — 25 FAQs across 5 categories with search
6. **Signup form is well-designed** — good validation, sector selection, WhatsApp field
7. **Backend health endpoint works** — `GET /health -> 200`, `GET /setores -> 200`
8. **Custom domain working** — `smartlic.tech` and `api.smartlic.tech` both resolve correctly
9. **SSL certificates valid** — HTTPS working on both domains

---

## Action Plan for PM — Story Recommendations

### Sprint Priority 1: EMERGENCY FIX (Must deploy within hours)

| Story | Title | ACs | Effort |
|-------|-------|-----|--------|
| **STORY-227** | Fix JWT ES256 validation after Supabase key rotation | Update auth.py to support ES256 algorithm with JWKS or public key; update Railway env vars; verify all auth endpoints work | **S** (2-4h) |
| **STORY-228** | Fix CSP to allow api.smartlic.tech and Cloudflare Insights | Add `api.smartlic.tech` to `connect-src`; add `cloudflareinsights.com` to `script-src`; verify /plans and /me calls work | **XS** (1h) |

### Sprint Priority 2: GTM Blockers (Deploy within 1-2 days)

| Story | Title | ACs | Effort |
|-------|-------|-----|--------|
| **STORY-229** | Add "Forgot Password" flow to login page | Add password reset link; wire to Supabase resetPasswordForEmail; add reset confirmation page | **S** (2-3h) |
| **STORY-230** | Fix footer navigation links | Central de Ajuda → /ajuda; add public contact option from /ajuda; fix all footer inconsistencies | **XS** (1h) |
| **STORY-231** | Fix header auth state on /buscar | Header must show user avatar/name when logged in; fix CSP + auth dependency; show logout option | **S** (tied to STORY-227 + STORY-228) |

### Sprint Priority 3: Polish (Deploy before GTM launch)

| Story | Title | ACs | Effort |
|-------|-------|-----|--------|
| **STORY-232** | Visual consistency: header translucency across pages | Match /buscar header style to landing page glass effect | **XS** (30min) |
| **STORY-233** | Fix redirect reason messaging | Use "login_required" instead of "session_expired" for unauthenticated access | **XS** (30min) |
| **STORY-234** | Migrate deprecated API routes | Frontend: update /api/messages/unread-count to /v1/ version | **XS** (30min) |

---

## Re-Validation Plan

After STORY-227 and STORY-228 are deployed:
1. Re-run full 4-persona test suite
2. Validate search flow end-to-end (search → results → download)
3. Validate plan purchase flow (view plans → checkout → Stripe)
4. Validate admin and master user features
5. Performance testing (search response times)

---

## Appendix: Evidence Files

| File | Description |
|------|-------------|
| `persona1-planos-page.png` | Plans page showing no plan cards |
| `railway-backend-logs.png` | Railway logs showing InvalidAlgorithmError + 401s |
| `supabase-jwt-keys.png` | Supabase JWT Keys page showing ECC P-256 current key |
| `.playwright-mcp/console-*.log` | Browser console logs with CSP violations |
