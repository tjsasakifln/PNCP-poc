# STORY-221 Track 3: Lifespan Migration - Completion Report

## Overview
Migrated from deprecated `@app.on_event` decorators to FastAPI lifespan context manager pattern. Added environment variable validation at startup.

## Changes Implemented

### 1. `backend/config.py` - Added `validate_env_vars()`
**Location:** Lines 364-387

**Function:**
```python
def validate_env_vars() -> None:
    """Validate required and recommended environment variables at startup.
    
    AC12: Check required vars: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
    AC13: Warn on recommended vars: OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN
    AC14: Raise RuntimeError if critical vars missing AND ENVIRONMENT=production
    """
```

**Behavior:**
- **Required vars:** SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
  - Production: Raises RuntimeError if missing (prevents startup)
  - Non-production: Logs warning, allows startup with degraded functionality
- **Recommended vars:** OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN
  - Logs warning if missing (any environment)

### 2. `backend/main.py` - Lifespan Context Manager
**Lines 135-194:** Created lifespan function to replace 3 deprecated decorators

**Structure:**
```python
from contextlib import asynccontextmanager
from redis_pool import startup_redis, shutdown_redis

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # === STARTUP ===
    validate_env_vars()           # AC12-AC14: Env validation
    await startup_redis()         # STORY-217: Redis pool
    _log_registered_routes(app)   # HOTFIX STORY-183: Route diagnostics
    
    yield
    
    # === SHUTDOWN ===
    await shutdown_redis()        # STORY-217: Redis pool cleanup
```

**FastAPI Constructor:** Line 208
```python
app = FastAPI(
    ...,
    lifespan=lifespan,  # STORY-221: Lifespan context manager
)
```

**Removed:** Lines 279-317 (old code)
- ❌ Deleted: `@app.on_event("startup")` for Redis init
- ❌ Deleted: `@app.on_event("shutdown")` for Redis cleanup
- ❌ Deleted: `@app.on_event("startup")` for route logging
- ❌ Deleted: Duplicate `from redis_pool import ...` line

### 3. `backend/redis_client.py` - Verification (AC4/AC5)
**Status:** ✅ ALREADY FIXED by STORY-217

**Current state:** Deprecated shim that redirects to `redis_pool.py`
- No `asyncio.run()` usage (the AC4/AC5 concern was already resolved)
- No changes needed for this track

## Acceptance Criteria Status

| AC | Description | Status | Evidence |
|----|-------------|--------|----------|
| AC1 | Single `lifespan` function replaces all 3 `@app.on_event` | ✅ | Lines 165-194 in main.py |
| AC2 | Imports `asynccontextmanager` from contextlib | ✅ | Line 23 in main.py |
| AC3 | `lifespan` placed before `app = FastAPI(...)` | ✅ | Lifespan at 165, FastAPI at 197 |
| AC4 | No `asyncio.run()` in redis_client.py | ✅ | Verified - shim redirects to redis_pool |
| AC5 | No crashes from asyncio.run | ✅ | Already fixed by STORY-217 |
| AC10 | `lifespan` calls `startup_redis()` on startup | ✅ | Line 184 |
| AC11 | `lifespan` calls `shutdown_redis()` on shutdown | ✅ | Line 192 |
| AC12 | Validates SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET | ✅ | Lines 371-382 in config.py |
| AC13 | Warns if OPENAI_API_KEY, STRIPE_SECRET_KEY, SENTRY_DSN missing | ✅ | Lines 383-387 in config.py |
| AC14 | Raises RuntimeError in production if required vars missing | ✅ | Lines 378-382 in config.py |

## Testing

### Import Test
```bash
cd backend && python -c "import main; print('✅ main.py imports successfully')"
```
**Result:** ✅ Success (module imports without errors)

### Manual Verification
```bash
grep -n "@app.on_event" backend/main.py
```
**Result:** ✅ No matches (only in comments/docstrings)

## Files Modified

1. **backend/config.py**
   - Added `validate_env_vars()` function (lines 364-387)
   - AC12-AC14 implementation

2. **backend/main.py**
   - Added `asynccontextmanager` import (line 23)
   - Added `validate_env_vars` to config import (line 37)
   - Moved `redis_pool` imports to top (line 41)
   - Created `_log_registered_routes()` helper (lines 138-161)
   - Created `lifespan` context manager (lines 165-194)
   - Updated FastAPI constructor with `lifespan=lifespan` (line 208)
   - Removed 3 deprecated `@app.on_event` decorators (old lines 279-317)

## Migration Impact

### Startup Sequence (NEW)
1. FastAPI constructor called with `lifespan=lifespan`
2. Lifespan startup phase begins:
   - Validate environment variables (fail-fast in production)
   - Initialize Redis connection pool
   - Log all registered routes for diagnostics
3. Application ready to serve requests

### Shutdown Sequence (NEW)
1. FastAPI receives shutdown signal
2. Lifespan shutdown phase begins:
   - Close Redis connection pool gracefully
3. Application terminates

### Advantages
- **Single source of truth:** All lifecycle logic in one place
- **Type-safe:** FastAPI properly manages async context
- **Clearer flow:** Startup/shutdown in obvious sequence
- **Modern:** Uses recommended FastAPI 0.100+ pattern
- **Fail-fast:** Env validation before expensive operations

## Next Steps (Other Tracks)

This track (T3) is complete. Remaining work:
- **T4 (Tests):** Add unit tests for `validate_env_vars()` and lifespan function
- **T1 (Authorization):** Handle authorization helper deprecations
- **T2 (Stripe):** Modernize webhook handlers

## Notes

- The lifespan pattern is FastAPI's recommended approach since 0.100.0
- The `@app.on_event` decorators are deprecated and will be removed in FastAPI 1.0
- This migration improves testability (lifespan can be mocked/tested independently)
- No breaking changes to API behavior - only internal lifecycle management
