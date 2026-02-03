# ADR-002: Plan Capabilities & Quota Management Architecture

**Status:** Proposed
**Date:** 2026-02-03
**Author:** @architect (Aria)
**Story:** PNCP-165
**Supersedes:** Current credit-based system in `backend/quota.py`

---

## Context

Smart PNCP is restructuring from 6 credit-based plans to 3 time-based subscription tiers + FREE trial:

**Current System (To Be Replaced):**
- Credit packs (1, 5, 10, 20 searches)
- Unlimited monthly/annual plans
- Free tier (3 lifetime searches)
- Credits stored in `user_subscriptions.credits_remaining`

**New System (STORY-165):**
- FREE Trial (7 days, forced upgrade)
- Consultor Ágil (R$ 297/month)
- Máquina (R$ 597/month)
- Sala de Guerra (R$ 1497/month)

**Key Business Requirements:**
1. **Time-based limits:** Historical data access varies by tier (7 days → 5 years)
2. **Feature gating:** Excel export available only on Máquina+ tiers
3. **Dual quota system:** Monthly search quota + per-minute rate limiting
4. **AI token control:** Summary length varies by tier (200 → 1000 tokens)
5. **Upgrade flow:** Clear UX for locked features with upgrade CTAs

---

## Decision 1: Plan Capabilities - Hardcoded Python Constants

### Decision

**Use hardcoded Python constants in `backend/quota.py` with TypedDict and Pydantic validation.**

**NOT** using:
- Database table (`plans` table with JSON capabilities)
- External config file (YAML, JSON)
- Environment variables
- Feature flags service (e.g., LaunchDarkly)

### Rationale

**Pros (Hardcoded):**
- ✅ **Security:** Prevents database tampering (admin user can't modify plan limits)
- ✅ **Type safety:** Pydantic/TypedDict validation at compile/startup time
- ✅ **Performance:** Zero database queries for plan lookup
- ✅ **Simplicity:** No migration scripts, no config parsing
- ✅ **Version control:** Plan changes tracked in Git with code review

**Cons:**
- ❌ Requires code deployment to change plan limits
- ❌ Can't A/B test plan variations without feature flags

**Why not database?**
- POC stage - plan structure unlikely to change frequently
- Security risk: SQL injection or admin panel vulnerability could modify limits
- Adds latency to every quota check

**Why not config file?**
- Requires file parsing on every deploy
- Easy to accidentally commit wrong values
- Not type-safe until runtime

**Compromise for Future:**
- Add feature flag for gradual rollout (`ENABLE_NEW_PRICING: 0% → 100%`)
- If plan structure becomes dynamic, migrate to DB with admin audit log

### Implementation

```python
# backend/quota.py

from typing import TypedDict
from enum import Enum

class PlanPriority(str, Enum):
    """Processing priority for background jobs (future use)."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class PlanCapabilities(TypedDict):
    """Immutable plan capabilities - DO NOT modify without PR review."""
    max_history_days: int
    allow_excel: bool
    max_requests_per_month: int
    max_requests_per_min: int
    max_summary_tokens: int
    priority: PlanPriority

PLAN_CAPABILITIES: dict[str, PlanCapabilities] = {
    "free_trial": {
        "max_history_days": 7,
        "allow_excel": False,
        "max_requests_per_month": 999999,  # Unlimited during trial (quota by expiry)
        "max_requests_per_min": 2,
        "max_summary_tokens": 200,
        "priority": PlanPriority.LOW,
    },
    "consultor_agil": {
        "max_history_days": 30,
        "allow_excel": False,
        "max_requests_per_month": 50,
        "max_requests_per_min": 10,
        "max_summary_tokens": 200,
        "priority": PlanPriority.NORMAL,
    },
    "maquina": {
        "max_history_days": 365,
        "allow_excel": True,
        "max_requests_per_month": 300,
        "max_requests_per_min": 30,
        "max_summary_tokens": 500,
        "priority": PlanPriority.HIGH,
    },
    "sala_guerra": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "max_requests_per_month": 1000,
        "max_requests_per_min": 60,
        "max_summary_tokens": 1000,
        "priority": PlanPriority.CRITICAL,
    },
}

# Display names for UI
PLAN_NAMES: dict[str, str] = {
    "free_trial": "FREE Trial",
    "consultor_agil": "Consultor Ágil",
    "maquina": "Máquina",
    "sala_guerra": "Sala de Guerra",
}

# Upgrade path suggestions (for error messages)
UPGRADE_SUGGESTIONS: dict[str, dict[str, str]] = {
    "max_history_days": {
        "free_trial": "consultor_agil",
        "consultor_agil": "maquina",
        "maquina": "sala_guerra",
    },
    "allow_excel": {
        "free_trial": "maquina",
        "consultor_agil": "maquina",
    },
    "max_requests_per_month": {
        "consultor_agil": "maquina",
        "maquina": "sala_guerra",
    },
}
```

---

## Decision 2: Rate Limiting - Hybrid (Redis + In-Memory Fallback)

### Decision

**Implement rate limiting with Redis (primary) and in-memory fallback (development/degraded mode).**

**Algorithm:** Token bucket (allows bursts, smooth long-term rate)

### Rationale

**Why Token Bucket?**
- Allows short bursts (better UX than fixed window)
- Standard algorithm (well-documented, proven)
- Efficient in Redis (single key per user)

**Why Redis Primary?**
- ✅ Distributed (works with multiple API instances)
- ✅ TTL support (automatic cleanup)
- ✅ Atomic operations (INCR, EXPIRE)
- ✅ Low latency (<5ms)

**Why In-Memory Fallback?**
- ✅ Local development without Redis
- ✅ Graceful degradation if Redis unavailable (don't block all requests)
- ❌ Rate limits not shared across API instances (acceptable for POC)

### Implementation

**Redis Key Structure:**
```
rate_limit:{user_id}:{minute}  →  request_count (int)
TTL: 60 seconds (auto-expire)

Example:
rate_limit:user-123:2026-02-03T14:30  →  5 requests
```

**Algorithm:**
```python
# backend/rate_limiter.py

import redis
from datetime import datetime
from typing import Optional
from functools import lru_cache
import os
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter with Redis + in-memory fallback."""

    def __init__(self):
        self.redis_client = self._connect_redis()
        self._memory_store: dict[str, tuple[int, float]] = {}  # {key: (count, timestamp)}

    def _connect_redis(self) -> Optional[redis.Redis]:
        """Connect to Redis (fallback to None if unavailable)."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("REDIS_URL not set - using in-memory rate limiting")
            return None

        try:
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logger.info("Redis connected for rate limiting")
            return client
        except Exception as e:
            logger.error(f"Redis connection failed: {e} - fallback to in-memory")
            return None

    def check_rate_limit(self, user_id: str, max_requests_per_min: int) -> tuple[bool, int]:
        """
        Check if user is within rate limit.

        Returns:
            tuple: (allowed: bool, retry_after_seconds: int)
        """
        minute_key = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
        key = f"rate_limit:{user_id}:{minute_key}"

        if self.redis_client:
            return self._check_redis(key, max_requests_per_min)
        else:
            return self._check_memory(key, max_requests_per_min)

    def _check_redis(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using Redis."""
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                self.redis_client.expire(key, 60)  # TTL 60 seconds

            if count > limit:
                # Calculate retry-after
                ttl = self.redis_client.ttl(key)
                return (False, max(1, ttl))

            return (True, 0)

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e} - allowing request")
            return (True, 0)  # Fail open (don't block on Redis errors)

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory dict (local dev only)."""
        now = datetime.utcnow().timestamp()

        # Cleanup old entries (simple garbage collection)
        self._memory_store = {
            k: (count, ts)
            for k, (count, ts) in self._memory_store.items()
            if now - ts < 60
        }

        if key in self._memory_store:
            count, timestamp = self._memory_store[key]
            if now - timestamp >= 60:
                # Expired, reset
                self._memory_store[key] = (1, now)
                return (True, 0)
            elif count >= limit:
                retry_after = int(60 - (now - timestamp))
                return (False, max(1, retry_after))
            else:
                self._memory_store[key] = (count + 1, timestamp)
                return (True, 0)
        else:
            self._memory_store[key] = (1, now)
            return (True, 0)

# Global instance
rate_limiter = RateLimiter()
```

**Usage in main.py:**
```python
from rate_limiter import rate_limiter

@app.post("/api/buscar")
async def buscar(request: BuscaRequest, user_id: str = Depends(get_current_user)):
    quota_info = check_quota(user_id)

    # Rate limiting
    allowed, retry_after = rate_limiter.check_rate_limit(
        user_id,
        quota_info.capabilities["max_requests_per_min"]
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "message": f"Limite de requisições excedido ({quota_info.capabilities['max_requests_per_min']} req/min). Aguarde {retry_after}s.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)}
        )
    # ... rest of endpoint
```

**Environment Variables:**
```bash
# .env
REDIS_URL=redis://localhost:6379  # Optional - falls back to in-memory
```

---

## Decision 3: Quota Tracking - Supabase Monthly Quota Table

### Decision

**Create `monthly_quota` table in Supabase with lazy reset logic.**

**NOT** using:
- Incrementing `user_subscriptions.credits_remaining` (wrong model for time-based plans)
- Redis expiry (loses data on restart)
- Daily quota (monthly aligns with billing)

### Rationale

**Why Monthly Quota?**
- Aligns with subscription billing cycle
- Industry standard (AWS, Stripe, etc. use monthly quotas)
- Simple UX: "50 buscas/mês" is clear

**Why Lazy Reset?**
- ✅ No cron job needed (one less moving part)
- ✅ Automatically handles timezone issues
- ✅ Database does the work (month comparison in SQL)
- ❌ Slightly more complex query

**Alternative Considered: Cron Job**
- Requires scheduler (Railway Cron, GitHub Actions, etc.)
- Risk: Missed runs = quota not reset
- Unnecessary complexity for POC

### Implementation

**Database Schema:**
```sql
-- Supabase migration

CREATE TABLE monthly_quota (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL,  -- Format: "2026-02"
    searches_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, month_year)
);

CREATE INDEX idx_monthly_quota_user_month ON monthly_quota(user_id, month_year);

-- RLS Policies
ALTER TABLE monthly_quota ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own quota" ON monthly_quota
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "API can manage quota" ON monthly_quota
    FOR ALL USING (true);  -- Backend service role has full access
```

**Quota Tracking Functions:**
```python
# backend/quota.py

from datetime import datetime
from supabase_client import get_supabase

def get_current_month_key() -> str:
    """Get current month key (e.g., '2026-02')."""
    return datetime.utcnow().strftime("%Y-%m")

def get_monthly_quota_used(user_id: str) -> int:
    """
    Get searches used this month (lazy reset).

    If no record exists for current month, returns 0.
    Old month records are ignored (automatic reset).
    """
    sb = get_supabase()
    month_key = get_current_month_key()

    result = (
        sb.table("monthly_quota")
        .select("searches_count")
        .eq("user_id", user_id)
        .eq("month_year", month_key)
        .single()
        .execute()
    )

    if result.data:
        return result.data["searches_count"]
    else:
        return 0

def increment_monthly_quota(user_id: str) -> int:
    """
    Increment monthly quota by 1 (upsert pattern).

    Returns new count after increment.
    """
    sb = get_supabase()
    month_key = get_current_month_key()

    # Upsert: increment if exists, insert 1 if not
    result = (
        sb.table("monthly_quota")
        .upsert({
            "user_id": user_id,
            "month_year": month_key,
            "searches_count": 1,  # Will be incremented if exists
        })
        .execute()
    )

    # If record existed, increment
    current = get_monthly_quota_used(user_id)
    if current > 1:
        sb.table("monthly_quota").update({
            "searches_count": current,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("user_id", user_id).eq("month_year", month_key).execute()

    return current

def get_quota_reset_date() -> datetime:
    """Get next quota reset date (1st of next month)."""
    now = datetime.utcnow()
    if now.month == 12:
        return datetime(now.year + 1, 1, 1)
    else:
        return datetime(now.year, now.month + 1, 1)
```

**Quota Check in `check_quota()`:**
```python
def check_quota(user_id: str) -> QuotaInfo:
    # ... existing code to get plan_id ...

    # Get capabilities
    caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES["free_trial"])

    # Check monthly quota
    quota_used = get_monthly_quota_used(user_id)
    quota_limit = caps["max_requests_per_month"]
    quota_remaining = max(0, quota_limit - quota_used)

    if quota_used >= quota_limit:
        reset_date = get_quota_reset_date()
        return QuotaInfo(
            allowed=False,
            plan_id=plan_id,
            plan_name=PLAN_NAMES[plan_id],
            capabilities=caps,
            quota_used=quota_used,
            quota_remaining=0,
            quota_reset_date=reset_date,
            error_message=f"Limite de {quota_limit} buscas mensais atingido. Renovação em {reset_date.strftime('%d/%m/%Y')} ou faça upgrade.",
        )

    return QuotaInfo(
        allowed=True,
        plan_id=plan_id,
        plan_name=PLAN_NAMES[plan_id],
        capabilities=caps,
        quota_used=quota_used,
        quota_remaining=quota_remaining,
        quota_reset_date=get_quota_reset_date(),
        error_message=None,
    )
```

**Cleanup (Optional - Run Monthly):**
```sql
-- Delete quota records older than 3 months (optional cleanup)
DELETE FROM monthly_quota
WHERE month_year < to_char(now() - interval '3 months', 'YYYY-MM');
```

---

## Decision 4: Error Response Structure - Standardized Upgrade CTAs

### Decision

**Use consistent error response schema for 403/429 errors with upgrade guidance.**

### Rationale

**Why Standard Structure?**
- ✅ Frontend can parse errors consistently
- ✅ Clear upgrade path (suggest next tier)
- ✅ Analytics-friendly (track upgrade clicks)
- ✅ User-friendly messages (not technical jargon)

**Why Include Suggested Plan?**
- Reduces friction (user doesn't need to research plans)
- Contextual upgrade (date range → Máquina, quota → higher tier)

### Implementation

**Error Response Schema:**
```python
# backend/schemas.py

from pydantic import BaseModel
from typing import Optional

class ErrorDetail(BaseModel):
    """Standardized error response with upgrade guidance."""
    message: str
    error_code: str
    upgrade_cta: Optional[str] = None
    suggested_plan: Optional[str] = None
    suggested_plan_name: Optional[str] = None
    suggested_plan_price: Optional[str] = None
    retry_after: Optional[int] = None  # For 429 errors

# Error codes
ERROR_CODES = {
    "TRIAL_EXPIRED": "trial_expired",
    "QUOTA_EXHAUSTED": "quota_exhausted",
    "RATE_LIMIT_EXCEEDED": "rate_limit_exceeded",
    "DATE_RANGE_EXCEEDED": "date_range_exceeded",
    "EXCEL_NOT_ALLOWED": "excel_not_allowed",
}
```

**Usage in Endpoints:**
```python
# backend/main.py

from schemas import ErrorDetail, ERROR_CODES
from quota import UPGRADE_SUGGESTIONS, PLAN_NAMES

@app.post("/api/buscar")
async def buscar(request: BuscaRequest, user_id: str = Depends(get_current_user)):
    quota_info = check_quota(user_id)

    # Quota exhausted (403)
    if not quota_info.allowed:
        suggested_plan_id = UPGRADE_SUGGESTIONS["max_requests_per_month"].get(quota_info.plan_id)
        raise HTTPException(
            status_code=403,
            detail=ErrorDetail(
                message=quota_info.error_message,
                error_code=ERROR_CODES["QUOTA_EXHAUSTED"],
                upgrade_cta="Fazer Upgrade",
                suggested_plan=suggested_plan_id,
                suggested_plan_name=PLAN_NAMES.get(suggested_plan_id),
                suggested_plan_price="R$ 597/mês" if suggested_plan_id == "maquina" else None,
            ).dict()
        )

    # Date range validation (403)
    days_requested = (datetime.fromisoformat(request.data_final) - datetime.fromisoformat(request.data_inicial)).days
    max_days = quota_info.capabilities["max_history_days"]

    if days_requested > max_days:
        suggested_plan_id = UPGRADE_SUGGESTIONS["max_history_days"].get(quota_info.plan_id)
        raise HTTPException(
            status_code=403,
            detail=ErrorDetail(
                message=f"Seu plano {quota_info.plan_name} permite buscas de até {max_days} dias. Você solicitou {days_requested} dias.",
                error_code=ERROR_CODES["DATE_RANGE_EXCEEDED"],
                upgrade_cta="Fazer Upgrade",
                suggested_plan=suggested_plan_id,
                suggested_plan_name=PLAN_NAMES.get(suggested_plan_id),
                suggested_plan_price="R$ 597/mês" if suggested_plan_id == "maquina" else "R$ 1.497/mês",
            ).dict()
        )

    # Rate limiting (429)
    allowed, retry_after = rate_limiter.check_rate_limit(user_id, quota_info.capabilities["max_requests_per_min"])
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=ErrorDetail(
                message=f"Limite de {quota_info.capabilities['max_requests_per_min']} requisições por minuto excedido. Aguarde {retry_after}s.",
                error_code=ERROR_CODES["RATE_LIMIT_EXCEEDED"],
                retry_after=retry_after,
            ).dict(),
            headers={"Retry-After": str(retry_after)}
        )

    # ... rest of endpoint logic
```

**Frontend Error Handling:**
```typescript
// frontend/lib/api.ts

interface ErrorDetail {
  message: string;
  error_code: string;
  upgrade_cta?: string;
  suggested_plan?: string;
  suggested_plan_name?: string;
  suggested_plan_price?: string;
  retry_after?: number;
}

async function buscar(request: BuscaRequest) {
  try {
    const response = await fetch('/api/buscar', { /* ... */ });
    if (!response.ok) {
      const error: ErrorDetail = await response.json();

      // Show upgrade modal if suggested plan
      if (error.suggested_plan) {
        showUpgradeModal({
          message: error.message,
          plan: error.suggested_plan,
          planName: error.suggested_plan_name,
          price: error.suggested_plan_price,
        });
      } else if (error.error_code === 'rate_limit_exceeded') {
        showRetryAlert(error.retry_after);
      }

      throw new Error(error.message);
    }
    return await response.json();
  } catch (error) {
    // Handle error
  }
}
```

---

## Decision 5: API Contract - Enhanced /api/me and /api/buscar

### Decision

**Extend `/api/me` to return capabilities and quota info.**
**Modify `/api/buscar` response to include quota and Excel availability.**

### Rationale

**Why `/api/me` Returns Capabilities?**
- ✅ Frontend gets all plan info in one request (no additional quota endpoint)
- ✅ Can pre-validate date range before submitting (better UX)
- ✅ Can conditionally render locked features (Excel button, quota counter)

**Why `/api/buscar` Returns Quota Info?**
- ✅ Real-time quota update (user sees "49/50" after search)
- ✅ Excel availability flag (frontend knows whether to show download button)

### Implementation

**Enhanced `/api/me` Response:**
```python
# backend/schemas.py

class UserProfileResponse(BaseModel):
    """User profile with plan capabilities."""
    user_id: str
    email: str
    plan_id: str
    plan_name: str
    capabilities: dict  # PlanCapabilities
    quota_used: int
    quota_remaining: int
    quota_reset_date: str  # ISO format
    trial_expires_at: Optional[str] = None
    subscription_status: str  # "active", "trial", "expired"

# backend/main.py

@app.get("/api/me", response_model=UserProfileResponse)
async def get_user_profile(user_id: str = Depends(get_current_user)):
    """Get current user profile with plan capabilities."""
    quota_info = check_quota(user_id)

    # Get user from Supabase
    sb = get_supabase()
    user = sb.table("users").select("*").eq("id", user_id).single().execute().data

    return UserProfileResponse(
        user_id=user_id,
        email=user["email"],
        plan_id=quota_info.plan_id,
        plan_name=quota_info.plan_name,
        capabilities=quota_info.capabilities,
        quota_used=quota_info.quota_used,
        quota_remaining=quota_info.quota_remaining,
        quota_reset_date=quota_info.quota_reset_date.isoformat(),
        trial_expires_at=quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
        subscription_status="trial" if quota_info.plan_id == "free_trial" else "active",
    )
```

**Enhanced `/api/buscar` Response:**
```python
# backend/schemas.py

class BuscaResponse(BaseModel):
    """Enhanced search response with quota and Excel availability."""
    resumo: ResumoLicitacoes
    excel_base64: Optional[str] = None  # None if not allowed
    excel_available: bool
    quota_used: int
    quota_remaining: int
    total_raw: int
    total_filtrado: int
    filter_stats: Optional[FilterStats] = None
    upgrade_message: Optional[str] = None  # Shown if Excel blocked

# backend/main.py

@app.post("/api/buscar", response_model=BuscaResponse)
async def buscar(request: BuscaRequest, user_id: str = Depends(get_current_user)):
    # ... quota checks, rate limiting, date validation ...

    # Fetch from PNCP
    licitacoes = await fetch_from_pncp(request)

    # Excel generation (conditional)
    excel_base64 = None
    excel_available = quota_info.capabilities["allow_excel"]
    upgrade_message = None

    if excel_available:
        excel_buffer = create_excel(licitacoes)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode()
    else:
        upgrade_message = "Exportar Excel disponível no plano Máquina (R$ 597/mês)."

    # Increment quota
    new_quota_used = increment_monthly_quota(user_id)

    return BuscaResponse(
        resumo=gerar_resumo(licitacoes, quota_info.capabilities["max_summary_tokens"]),
        excel_base64=excel_base64,
        excel_available=excel_available,
        quota_used=new_quota_used,
        quota_remaining=max(0, quota_info.capabilities["max_requests_per_month"] - new_quota_used),
        total_raw=len(raw_results),
        total_filtrado=len(licitacoes),
        filter_stats=calculate_filter_stats(raw_results, licitacoes),
        upgrade_message=upgrade_message,
    )
```

---

## Consequences

### Positive

1. **Security:** Plan limits are code-controlled, preventing tampering
2. **Performance:** Zero DB queries for plan lookup (hardcoded constants)
3. **Type Safety:** Pydantic validation ensures correct data types
4. **Scalability:** Redis rate limiting supports multiple API instances
5. **UX:** Clear upgrade CTAs with contextual plan suggestions
6. **Simplicity:** No cron jobs needed (lazy quota reset)

### Negative

1. **Flexibility:** Changing plan limits requires code deployment
2. **A/B Testing:** Can't test plan variations without feature flags
3. **Redis Dependency:** Production requires Redis (added infrastructure)

### Mitigation

1. **Feature Flag:** Add `ENABLE_NEW_PRICING` for gradual rollout
2. **Redis Fallback:** In-memory rate limiting for development/degraded mode
3. **Monitoring:** Track 403/429 errors, upgrade clicks, quota exhaustion

---

## Acceptance Criteria (Technical)

- [ ] `PLAN_CAPABILITIES` defined in `backend/quota.py` with TypedDict
- [ ] `check_quota()` returns `QuotaInfo` with capabilities, quota, reset date
- [ ] `monthly_quota` table created in Supabase with RLS policies
- [ ] Rate limiter implemented (Redis + in-memory fallback)
- [ ] `/api/me` returns user profile + capabilities
- [ ] `/api/buscar` validates date range before PNCP call
- [ ] `/api/buscar` conditionally generates Excel based on `allow_excel`
- [ ] `/api/buscar` increments monthly quota on success
- [ ] Error responses include upgrade CTAs and suggested plans
- [ ] Unit tests for quota logic (>=70% coverage)
- [ ] Integration tests for rate limiting

---

## References

- **Story:** `docs/stories/STORY-165-plan-restructuring.md`
- **Current Implementation:** `backend/quota.py`, `backend/schemas.py`
- **Rate Limiting Algorithms:** [Token Bucket vs Leaky Bucket](https://en.wikipedia.org/wiki/Token_bucket)
- **Lazy Reset Pattern:** [Stripe Quota Reset](https://stripe.com/docs/api/usage_records)

---

**Review Status:** Awaiting approval from @pm and @dev
