# 🚨 HOTFIX Deployment Guide - 2026-02-10

## Executive Summary

**Severity:** P0 (Critical)
**Impact:** User-facing bugs blocking core functionality
**Squad:** search-export-bugfix-squad
**Timeline:** 1h45min estimated for complete fix

### Bugs Identified

1. **Search Returns Only 2 Results (P0)**
   - User selects all states, all modalities → Gets only 2 results
   - Root cause: `max_pages=50` in `pncp_client.py` (limits to 1000 records per UF+modality)

2. **Google Sheets Export HTTP 404 (P0)**
   - Export button fails with 404 error
   - Root cause: TBD (route registration or runtime issue)

---

## 🔍 Root Cause Analysis

### Bug #1: Search Pagination Limit

**File:** `backend/pncp_client.py:461`

**Current Code:**
```python
def _fetch_by_uf(
    self,
    ...,
    max_pages: int = 50,  # ← TOO LOW!
) -> Generator[Dict[str, Any], None, None]:
```

**Problem:**
- Limits to 50 pages × 20 items/page = **1000 records per UF+modality**
- With 27 UFs and 8 modalities = 216 combinations
- If any combination hits the limit, results are incomplete

**Proposed Fix:**
```python
max_pages: int = 500,  # 10,000 records per UF+modality

# Add warning when limit is reached
if pagina >= max_pages and tem_proxima_pagina:
    logger.warning(
        f"⚠️ MAX_PAGES ({max_pages}) reached for UF={uf}, "
        f"modalidade={modalidade}. Results may be incomplete!"
    )
```

---

### Bug #2: Google Sheets Export 404

**File:** `backend/routes/export_sheets.py`, `backend/main.py`

**Current Status:**
- ✅ Route defined: `@router.post("/google-sheets")`
- ✅ Router registered: `app.include_router(export_sheets_router)`
- ✅ Prefix correct: `prefix="/api/export"`
- ✅ Frontend calls correct URL: `/api/export/google-sheets`

**Diagnostic Required:**
```bash
# Run quick diagnostic
bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh

# Expected checks:
# 1. Backend is running (curl http://localhost:8000/health)
# 2. Route is in OpenAPI spec (curl http://localhost:8000/openapi.json)
# 3. POST to route returns 401 (not 404) when no auth
```

---

## 🛠️ Squad Deployed

**Location:** `squads/search-export-bugfix-squad/`

**Key Files:**
- ✅ `squad.yaml` - Manifest
- ✅ `README.md` - Squad overview
- ✅ `agents/search-specialist.md` - Search expert
- ✅ `agents/export-specialist.md` - Export expert
- ✅ `tasks/diagnose-search-bug.md` - Diagnostic task (20 min)
- ✅ `tasks/diagnose-export-bug.md` - Diagnostic task (15 min)
- ✅ `tools/quick-diagnostic.sh` - Automated diagnostic script

---

## 📋 Quick Start

### Run Automated Diagnostic

```bash
cd "T:\GERAL\SASAKI\Licitações"
bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh
```

This will check:
1. ✅ Backend health
2. ✅ Export route accessibility
3. ✅ OpenAPI spec
4. ✅ CORS configuration
5. ✅ Search pagination limit (max_pages value)

---

## 🚀 Next Steps

1. **Run Diagnostic** (5 min)
   ```bash
   bash squads/search-export-bugfix-squad/tools/quick-diagnostic.sh
   ```

2. **Apply Fixes** (45 min)
   - Search: Edit `backend/pncp_client.py:461` (change max_pages to 500)
   - Export: Based on diagnostic results

3. **Test** (30 min)
   - Run regression tests
   - Manual E2E testing
   - Verify fixes work

4. **Deploy** (15 min)
   - Create hotfix PR
   - Merge after review
   - Deploy to production

**Total Time:** ~1h35min

---

## 📊 Success Metrics

**Search Bug:**
- ✅ Search returns > 100 results for wide params
- ✅ Performance < 4 min for 27 UFs
- ✅ All UFs+modalidades processed

**Export Bug:**
- ✅ Export returns HTTP 200 (not 404)
- ✅ Spreadsheet opens successfully
- ✅ Export latency < 10s

---

## 📞 Contact

**Squad Lead:** Tiago Sasaki
**Created:** 2026-02-10 21:30 UTC
**Priority:** P0 (Critical)

---

**Squad Directory:** `squads/search-export-bugfix-squad/`
**Design Blueprint:** `squads/.designs/search-bugfix-squad-design.yaml`
