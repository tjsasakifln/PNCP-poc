# Feature Flag: ENABLE_NEW_PRICING

**Story:** PNCP-165 (Plan Restructuring - 3 Paid Tiers + FREE Trial)  
**Status:** Implemented (AC17 completed)  
**Default:** `false` (disabled for safety)

## Overview

Controls the new pricing model with plan-based capabilities, quota enforcement, and Excel gating. When enabled, the system enforces subscription tiers and usage limits. When disabled, the system operates in legacy mode with unlimited access.

## Configuration

### Backend (Python)

**Environment Variable:** `ENABLE_NEW_PRICING`  
**Location:** `backend/config.py`  
**Valid Values:** `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off` (case-insensitive)  
**Default:** `false`

### Frontend (TypeScript)

**Environment Variable:** `NEXT_PUBLIC_ENABLE_NEW_PRICING`  
**Location:** `frontend/lib/config.ts`  
**Valid Values:** `true`, `false`, `1`, `0`, `yes`, `no`, `on`, `off` (case-insensitive)  
**Default:** `false`

## Rollout Strategy

1. **0% (Testing):** Both flags = `false` (current state)
2. **10% (Canary):** Enable for 10% of users
3. **50% (Gradual):** Expand to 50% of users
4. **100% (Full):** All users

## Testing

```bash
# Test with flag OFF
export ENABLE_NEW_PRICING=false
export NEXT_PUBLIC_ENABLE_NEW_PRICING=false

# Test with flag ON
export ENABLE_NEW_PRICING=true
export NEXT_PUBLIC_ENABLE_NEW_PRICING=true
```

## Rollback

Set both flags to `false` and redeploy.

---

**Related:** [STORY-165](../stories/STORY-165-plan-restructuring.md)
