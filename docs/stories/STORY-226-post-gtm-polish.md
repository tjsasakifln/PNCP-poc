# STORY-226: Post-GTM Polish — Architecture Cleanup & Technical Debt

**Status:** Pending
**Priority:** P3 — Post-GTM
**Sprint:** Sprint 4+ (Ongoing)
**Estimated Effort:** 10 days
**Source:** AUDIT-FRENTE-1-CODEBASE (MED-01 to MED-12, LOW), AUDIT-FRENTE-4 (audit log persistence, SLI/SLO), AUDIT-FRENTE-6 (FAQ, support)
**Squad:** Rotating

---

## Context

This story consolidates all non-blocking Medium/Low findings into a single technical debt backlog. These items improve code quality, maintainability, and operational maturity but are not required for GTM.

## Acceptance Criteria — Architecture

### Dependency Injection

- [ ] AC1: Replace 35 deferred `get_supabase()` imports with FastAPI dependency injection pattern
- [ ] AC2: Create `Depends(get_db)` provider for Supabase client
- [ ] AC3: At minimum 5 modules migrated as proof of pattern

### Code Cleanup

- [ ] AC4: Extract `sectors.py` (1600+ lines) to YAML configuration loaded at startup
- [ ] AC5: Extract `dateDiffInDays` to shared utility (currently duplicated)
- [ ] AC6: Fix `Optional[any]` type annotations to proper types in `redis_client.py`, `rate_limiter.py`, `progress.py`
- [ ] AC7: Eliminate 8 `any` types in frontend TypeScript
- [ ] AC8: Rename `_` prefix functions that are used cross-module (`authorization.py`)
- [ ] AC9: Implement data-driven plan capabilities (replace if/elif chain in `quota.py`)
- [ ] AC10: Add size limit (LRU) to `InMemoryCache` in `cache.py`
- [ ] AC11: Fix `response.text()` on consumed body in `api/buscar/route.ts:168`

### Error Boundaries

- [ ] AC12: Add route-specific error boundaries for `/buscar`, `/dashboard`, `/admin`
- [ ] AC13: Error boundary shows localized error + retry, not full-page crash

### Infrastructure

- [ ] AC14: Remove dual router mounting (legacy routes) or add deprecation warnings + `Deprecation` header
- [ ] AC15: Remove filesystem Excel fallback (rely exclusively on object storage URLs)
- [ ] AC16: Make feature flags runtime-reloadable (not just at import time)
- [ ] AC17: Strengthen password policy: 8+ chars, at least 1 uppercase + 1 digit

## Acceptance Criteria — Observability

### Audit Log Persistence

- [ ] AC18: Create `audit_events` table in Supabase with columns: `id`, `timestamp`, `event_type`, `actor_id_hash`, `target_id_hash`, `details`, `ip_hash`
- [ ] AC19: Log auth events, admin actions, billing events, and data access to `audit_events` table (in addition to stdout)
- [ ] AC20: Retention policy: 12 months

### SLI/SLO Definitions

- [ ] AC21: Define target SLIs: search latency (p95 < 15s), API availability (99.5%), error rate (< 1%)
- [ ] AC22: Document in `docs/sli-slo.md`

### Trace Propagation

- [ ] AC23: Forward `X-Request-ID` in outgoing requests to PNCP API, OpenAI API, Supabase
- [ ] AC24: Frontend logs generated correlation IDs to console (for debugging)

## Acceptance Criteria — Business Readiness

### FAQ Page

- [ ] AC25: Create `/ajuda` or `/faq` page with searchable Q&A
- [ ] AC26: Cover: how to search, plan differences, payment methods, data sources, account management
- [ ] AC27: Link from footer "Central de Ajuda" to FAQ
- [ ] AC28: Link from error pages to FAQ

### Support Improvements

- [ ] AC29: Add published contact email (e.g., `suporte@smartlic.tech`) on privacy policy and footer
- [ ] AC30: Error page (`error.tsx` line 60) links to `/mensagens` instead of just saying "entre em contato"
- [ ] AC31: Replace `alert()` in checkout error handling (`planos/page.tsx:408`) with `sonner` toast

### Checkout UX

- [ ] AC32: Replace `alert()` with toast notification for payment errors
- [ ] AC33: Add loading state during Stripe redirect

## Validation Metric

- Zero `any` types in frontend production code
- `sectors.py` is < 100 lines (data moved to YAML)
- FAQ page accessible at `/ajuda`
- Audit events persisted in database

## File References

(Multiple files across entire codebase — see individual ACs for specific files)
