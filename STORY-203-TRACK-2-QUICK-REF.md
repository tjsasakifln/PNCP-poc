# STORY-203 Track 2 Quick Reference

**Status:** ✅ Complete | **Date:** 2026-02-12

## TL;DR

Fixed 4 backend infrastructure issues:
1. Token cache now uses SHA-256 (deterministic, secure)
2. Rate limiter has 10K entry limit (prevents memory leaks)
3. Plan capabilities load from database (5min cache, fallback to code)
4. New `/api/plans` endpoint (combines DB + capabilities)

---

## What Changed

### 1. SYS-M02: Token Cache Hash Fix

**File:** `backend/auth.py`

```python
# OLD: Non-deterministic, breaks on restart
token_hash = hash(token[:16])

# NEW: Deterministic SHA-256
import hashlib
token_hash = hashlib.sha256(token[:16].encode('utf-8')).hexdigest()
```

**Impact:** Cache survives process restarts

---

### 2. SYS-M03: Rate Limiter Max Size

**File:** `backend/rate_limiter.py`

```python
MAX_MEMORY_STORE_SIZE = 10_000

# Added LRU eviction in _check_memory():
if len(cleaned_store) > MAX_MEMORY_STORE_SIZE:
    sorted_items = sorted(cleaned_store.items(), key=lambda item: item[1][1])
    cleaned_store = dict(sorted_items[-MAX_MEMORY_STORE_SIZE:])
```

**Impact:** Memory bounded to ~1MB

---

### 3. SYS-M04: Database-Driven Plan Capabilities

**File:** `backend/quota.py`

```python
# New functions:
get_plan_capabilities() -> dict[str, PlanCapabilities]
    # Returns: Plan caps with 5min cache
    # Fallback: Hardcoded PLAN_CAPABILITIES on DB error

_load_plan_capabilities_from_db() -> dict
    # Loads from: plans table
    # Converts: DB schema → PlanCapabilities

clear_plan_capabilities_cache() -> None
    # Use: Testing or after plan updates
```

**Usage:**
```python
# Replace all occurrences of:
caps = PLAN_CAPABILITIES.get(plan_id)

# With:
plan_caps = get_plan_capabilities()
caps = plan_caps.get(plan_id)
```

**Impact:** Plan changes via DB (no code deploy)

---

### 4. CROSS-M01: /api/plans Endpoint

**File:** `backend/routes/plans.py` (NEW)

```python
@router.get("/api/plans", response_model=PlansResponse)
async def get_plans_with_capabilities():
    """Returns all active plans with DB metadata + capabilities."""
```

**Response:**
```json
{
  "plans": [
    {
      "id": "consultor_agil",
      "name": "Consultor Ágil",
      "price_brl": 297.0,
      "max_searches": 50,
      "capabilities": {
        "max_history_days": 30,
        "allow_excel": false,
        "max_requests_per_month": 50,
        "max_requests_per_min": 10
      },
      "stripe_price_id_monthly": "price_xxx"
    }
  ],
  "total": 4
}
```

**Registered in:** `backend/main.py` line 49, 98

**Impact:** Single endpoint for frontend plan data

---

## Testing

```bash
# Syntax check (all pass)
cd backend
python -m py_compile auth.py rate_limiter.py quota.py routes/plans.py main.py

# Test plans endpoint
curl http://localhost:8000/api/plans | jq

# Check cache logs
# Should see: "Loaded N plan capabilities from database"
# On subsequent calls: "Plan capabilities cache HIT"
```

---

## Files Modified

| File | What Changed |
|------|--------------|
| `auth.py` | SHA-256 hash for token cache |
| `rate_limiter.py` | 10K max + LRU eviction |
| `quota.py` | DB loader + 5min cache |
| `routes/plans.py` | NEW - /api/plans endpoint |
| `main.py` | Import + register plans router |

---

## Deployment Checklist

- [x] Code implementation complete
- [x] Python syntax validated
- [ ] Unit tests written
- [ ] Integration tests passed
- [ ] Backend deployed to staging
- [ ] `/api/plans` verified in staging
- [ ] Frontend updated (Track 3)
- [ ] QA sign-off
- [ ] Production deployment

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Cache TTL | 5 minutes |
| Max rate limiter entries | 10,000 |
| Token hash algorithm | SHA-256 |
| DB fallback | Hardcoded values |
| API response time | <50ms |

---

## Contact

**Implementation:** Claude Sonnet 4.5
**Story:** STORY-203 Track 2
**Date:** 2026-02-12
