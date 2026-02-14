# STORY-227: Fix JWT ES256 Validation After Supabase Key Rotation

**Status:** In Progress
**Priority:** P0 — EMERGENCY
**Sprint:** Immediate (Sprint 3 — Hotfix)
**Estimated Effort:** S (2-4h)
**Source:** GTM-READINESS-VALIDATION-REPORT.md (CRIT-1)
**Squad:** team-bidiq-backend (dev, devops)

---

## Context

Supabase rotated the JWT signing key from **HS256 (shared secret)** to **ECC P-256 (ES256)** around 2026-02-03. The backend `auth.py` still validates tokens using `algorithms=["HS256"]`, causing **100% of authenticated API calls to fail with 401 Unauthorized**.

Railway backend logs confirm:
```
Invalid JWT token: InvalidAlgorithmError
GET /me -> 401 (3ms)
POST /buscar -> 401 (2ms)
```

This is a **total system outage** for all authenticated functionality: search, profile, billing, admin, messages.

## Acceptance Criteria

### JWT Validation Update

- [x] AC1: `backend/auth.py` supports **ES256** algorithm for JWT validation (not just HS256)
- [x] AC2: JWT validation uses Supabase's **JWKS endpoint** (`https://<project-ref>.supabase.co/.well-known/jwks.json`) to dynamically fetch public keys, OR uses the ECC P-256 public key configured as an environment variable
- [x] AC3: If using JWKS, keys are cached with a TTL (e.g., 5 minutes) to avoid per-request network calls
- [x] AC4: Backward compatibility: if both HS256 and ES256 tokens could be in-flight during transition, accept both algorithms temporarily
- [ ] AC5: Railway environment variable `SUPABASE_JWT_SECRET` is updated — if asymmetric (ES256), set to the **public key** (PEM format), not the shared secret

### Verification

- [ ] AC6: `GET /me` returns 200 with valid user profile for a logged-in user
- [ ] AC7: `POST /buscar` returns 200 and executes search for authenticated user
- [ ] AC8: `GET /buscar-progress/{search_id}` SSE stream connects successfully
- [ ] AC9: `GET /health` continues to return 200 (unauthenticated endpoint unaffected)
- [ ] AC10: Invalid/expired tokens still correctly return 401

### Tests

- [x] AC11: Unit test for ES256 token validation in `test_auth_es256.py` (8 tests)
- [x] AC12: Unit test confirming HS256 tokens accepted for backward compat (6 tests)
- [x] AC13: Unit test for JWKS key caching behavior (8 tests)
- [x] AC14: Integration test: authenticated endpoint returns 200 with valid ES256 token (10 tests)

### Deployment

- [ ] AC15: Deploy to Railway production
- [ ] AC16: Verify via production smoke test (`curl -H "Authorization: Bearer <token>" https://api.smartlic.tech/me`)

## Technical Notes

- Supabase JWKS endpoint: `https://fqqyovlzdzimiwfofdjk.supabase.co/.well-known/jwks.json`
- Current signing key ID: `86b16415-6286-4650-974f-f9faabddb460`
- Legacy key ID: `20061205-8ad8-43b9-ae1f-572245ad6c6f` (rotated ~11 days ago)
- Python library `PyJWT` supports ES256 with `cryptography` package
- Consider using `jwt.PyJWKClient` for automatic JWKS fetching

## Dependencies

- None (standalone fix)

## Blocks

- STORY-231 (header auth state)
- MAJ-2 (search 401 loop)
- All authenticated functionality

## File List

| File | Action | Description |
|------|--------|-------------|
| `backend/auth.py` | Modify | Update JWT validation to support ES256 + JWKS |
| `backend/requirements.txt` | Modify | Add `cryptography` if not already present |
| `backend/tests/test_auth_es256.py` | Create | 44 new ES256 validation tests (AC11-AC14) |
| Railway env vars | Modify | Update `SUPABASE_JWT_SECRET` to public key |
