# System Architecture - BidIQ Uniformes POC v0.2

**Version:** 2.0 (Brownfield Discovery)  
**Date:** 2026-01-30  
**Status:** ✅ Production Deployed  
**Architect:** @architect (Aria)

---

## ✅ Phase 1 Complete: System Documentation

### Executive Summary

BidIQ Uniformes is a **production-ready MVP** with:
- ✅ 96.69% backend test coverage (82 tests)
- ✅ Deployed to Railway (backend) + Vercel (frontend)
- ✅ 25/25 E2E tests passing
- ⚠️ 17 technical debt issues identified (4 P0, 5 P1, 5 P2, 3 P3)

### System Health

| Metric | Status | Value |
|--------|--------|-------|
| Backend Coverage | ✅ Excellent | 96.69% |
| Frontend Coverage | ⚠️ Needs Work | 0% (tests pending) |
| E2E Tests | ✅ Passing | 25/25 |
| Technical Debt | ⚠️ Moderate | 17 issues |
| Deployment | ✅ Automated | Railway + Vercel |

---

## Architecture Overview

**Stack:**
- Backend: FastAPI (Python 3.11), requests, OpenAI SDK, openpyxl
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Deployment: Railway (backend), Vercel (frontend)

**Key Modules:**
1. **pncp_client.py** (501 lines, 98% coverage) - Resilient PNCP API client
2. **filter.py** (547 lines, 99% coverage) - Keyword matching engine
3. **llm.py** (327 lines, 100% coverage) - GPT-4.1-nano integration
4. **excel.py** (253 lines, 100% coverage) - Excel generator
5. **page.tsx** (923 lines, ⚠️ MONOLITH) - Main frontend SPA

---

## 🚨 Critical Technical Debt (P0)

### P0-1: CORS Security Vulnerability
- **Issue:** `allow_origins=["*"]` exposes API to XSS/CSRF
- **Location:** main.py:49
- **Fix:** Restrict to production domain
- **Effort:** 15 minutes

### P0-2: File Storage Doesn't Scale
- **Issue:** tmpdir storage (single instance, no persistence)
- **Location:** api/buscar/route.ts:72
- **Fix:** Migrate to S3/GCS
- **Effort:** 2 days

### P0-3: No Async I/O
- **Issue:** Blocking `requests` library
- **Location:** pncp_client.py, main.py
- **Fix:** Migrate to `httpx` async
- **Effort:** 3 days

### P0-4: LLM Hallucination Workaround
- **Issue:** Override instead of fixing prompt
- **Location:** main.py:340
- **Fix:** Improve prompt engineering
- **Effort:** 1 day

**Total P0 Effort:** ~7 days

---

## Quality Metrics

**Backend:**
- Lines: ~2,800
- Coverage: 96.69%
- Tests: 82
- Complexity: Moderate (well-modularized)

**Frontend:**
- Lines: ~2,500
- Coverage: 0% (tests pending)
- Tests: 0
- Complexity: High (page.tsx monolith)

---

## Next Steps

1. **Week 1:** Fix CORS, add rate limiting, write frontend tests, add caching
2. **Month 1:** Migrate to async I/O, refactor frontend, migrate to S3
3. **Quarter 1:** Enable deadline filter, add observability, mobile optimization

**Full documentation:** See backup at `system-architecture.md.backup`

---

**END PHASE 1** ✅
