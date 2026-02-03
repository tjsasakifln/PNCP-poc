# Story PNCP-165: Plan Restructuring - 3 Paid Tiers + FREE Trial

**Story ID:** PNCP-165
**GitHub Issue:** #165 (to be created)
**Epic:** GTM (Go-to-Market) Preparation
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** product owner,
**I want** to restructure the monetization model from 6 plans to 3 paid tiers + FREE trial,
**So that** we have a simpler pricing strategy aligned with GTM launch and clear upgrade paths.

---

## Business Context

### Strategic Shift
- **Previous:** 6 plans (single access: 1, 5, 10, 20 + monthly + annual unlimited)
- **New:** 3 paid tiers + FREE trial (Consultor Ágil R$ 297, Máquina R$ 597, Sala de Guerra R$ 1497)
- **Status:** No paying users yet (preparing GTM launch)
- **Trial Strategy:** 7-day FREE trial with forced upgrade after expiration

### Value Proposition by Tier

| Plan | Price | Target User | Key Differentiator |
|------|-------|-------------|-------------------|
| **FREE Trial** | R$ 0 (7 days) | Evaluators | Limited history, no Excel, forces upgrade |
| **Consultor Ágil** | R$ 297/month | Solo consultants | 30-day history, screen-only (no Excel) |
| **Máquina** | R$ 597/month | Small teams | 1-year history, Excel export enabled |
| **Sala de Guerra** | R$ 1497/month | Large organizations | 5-year history, priority processing |

---

## Objective

Implement plan-based capabilities system that:

1. Hardcodes plan rules in backend (secure, no DB tampering)
2. Enforces limits server-side (date range, Excel generation)
3. Implements dual quota control (monthly quota + rate limiting)
4. Provides clear UX for upgrade paths (locked features, tooltips)
5. Tracks AI summary token limits by tier

---

## Acceptance Criteria

### AC1: Backend - Plan Capabilities Definition
- [ ] `PLAN_CAPABILITIES` dictionary in `backend/quota.py` with 4 plans
- [ ] Each plan defines: `max_history_days`, `allow_excel`, `max_requests_per_month`, `max_requests_per_min`, `max_summary_tokens`, `priority`
- [ ] Plan IDs: `free_trial`, `consultor_agil`, `maquina`, `sala_guerra`
- [ ] Type-safe constants (no magic numbers)

### AC2: Backend - Quota Check Enhancement
- [ ] `check_quota()` returns extended object: `{allowed, plan_id, capabilities, quota_used, quota_remaining}`
- [ ] Capabilities object includes all plan limits
- [ ] Quota tracking integrated with Supabase (monthly reset)
- [ ] Rate limiting tracked (requests per minute)

### AC3: Backend - Date Range Validation
- [ ] `/api/buscar` validates `(data_final - data_inicial).days <= capabilities.max_history_days`
- [ ] HTTP 403 error with message: `"Seu plano {plan_name} permite buscas de até {max_days} dias. Faça upgrade para acessar histórico completo."`
- [ ] Validation occurs BEFORE calling PNCP API (fail-fast)
- [ ] Error includes upgrade CTA and target plan suggestion

### AC4: Backend - Excel Export Gating
- [ ] `/api/buscar` checks `capabilities.allow_excel` before generating Excel
- [ ] If `allow_excel == false`: skip Excel generation (save CPU)
- [ ] Response includes `excel_available: false` + upgrade message
- [ ] If `allow_excel == true`: generate Excel normally

### AC5: Backend - Monthly Quota Enforcement
- [ ] Track `searches_this_month` in Supabase per user
- [ ] Increment counter on successful `/api/buscar` call
- [ ] HTTP 429 error when `searches_this_month >= max_requests_per_month`
- [ ] Error message: `"Você atingiu o limite de {quota} buscas mensais do plano {plan_name}. Aguarde renovação em {reset_date} ou faça upgrade."`
- [ ] Quota resets automatically on first day of month

### AC6: Backend - Rate Limiting
- [ ] Implement rate limiting using Redis (or in-memory fallback)
- [ ] Enforce `max_requests_per_min` per user per plan
- [ ] HTTP 429 error: `"Limite de requisições excedido ({rate_limit} req/min). Aguarde {retry_after} segundos."`
- [ ] Include `Retry-After` header in response

### AC7: Backend - AI Summary Token Control
- [ ] Pass `max_summary_tokens` to LLM service
- [ ] Consultor Ágil: 200 tokens (basic)
- [ ] Máquina: 500 tokens (detailed)
- [ ] Sala de Guerra: 1000 tokens (comprehensive)
- [ ] All use `gpt-4.1-nano` model (same quality, different length)

### AC8: Backend - User Endpoint Enhancement
- [ ] `/api/me` returns user profile + `capabilities` object
- [ ] Frontend receives all plan limits in single API call
- [ ] Include `quota_used`, `quota_remaining`, `quota_reset_date`
- [ ] Include `trial_expires_at` for FREE trial users

### AC9: Frontend - Plan Badge Display
- [ ] Show current plan badge in header/sidebar
- [ ] Badge colors: FREE (gray), Consultor Ágil (blue), Máquina (green), Sala de Guerra (gold)
- [ ] Display trial countdown for FREE users: "Trial: 3 dias restantes"
- [ ] Clickable badge opens upgrade modal

### AC10: Frontend - Excel Export UX
- [ ] If `capabilities.allow_excel == false`: show button with lock icon 🔒
- [ ] Tooltip on hover: "Exportar Excel disponível no plano Máquina (R$ 597/mês)"
- [ ] Click opens upgrade modal with pre-selected Máquina plan
- [ ] If `allow_excel == true`: normal functional button

### AC11: Frontend - Date Range Validation
- [ ] Date picker shows max allowed range visually
- [ ] Warning message if user selects range > `max_history_days`
- [ ] Message: "⚠️ Seu plano permite buscas de até {max_days} dias. Ajuste as datas ou faça upgrade."
- [ ] Disable search button until range is valid
- [ ] Real-time validation (no need to submit)

### AC12: Frontend - Quota Counter Display
- [ ] Show quota usage: "Buscas este mês: 23/50" (progress bar)
- [ ] Color coding: green (<70%), yellow (70-90%), red (>90%)
- [ ] Tooltip shows reset date: "Renovação em: 01/03/2026"
- [ ] When quota exhausted: show upgrade CTA

### AC13: Frontend - Error Handling (403, 429)
- [ ] Parse error messages from backend
- [ ] Display user-friendly alerts (not raw API errors)
- [ ] Include upgrade button in error dialog
- [ ] Track upgrade click events (analytics)

### AC14: Frontend - Upgrade Flow
- [ ] "Fazer Upgrade" button throughout UI (locked features)
- [ ] Modal with plan comparison table
- [ ] Highlight benefits of higher tiers
- [ ] Clear CTAs for each plan

### AC15: Testing - Backend Coverage
- [ ] Unit tests for each plan's capabilities
- [ ] Test date range validation (edge cases: 30 days, 31 days, leap year)
- [ ] Test Excel gating (allowed vs blocked)
- [ ] Test quota enforcement (at limit, over limit)
- [ ] Test rate limiting (burst, sustained)
- [ ] Test FREE trial expiration
- [ ] Coverage >= 70%

### AC16: Testing - Frontend Coverage
- [ ] Test plan badge rendering for each tier
- [ ] Test Excel button states (locked vs unlocked)
- [ ] Test date range validation UI
- [ ] Test quota counter display
- [ ] Test error handling (403, 429)
- [ ] Coverage >= 60%

### AC17: Deployment - Feature Flag
- [ ] Implement feature flag: `ENABLE_NEW_PRICING`
- [ ] Gradual rollout: 0% → 10% → 50% → 100%
- [ ] Monitor error rates, upgrade clicks
- [ ] Rollback plan if issues detected

### AC18: Documentation
- [ ] Update PRD.md with new pricing model
- [ ] Document plan capabilities in `docs/architecture/plan-capabilities.md`
- [ ] Update API documentation (`/api/me`, `/api/buscar` responses)
- [ ] Create pricing comparison page (docs/pricing.md)

---

## Technical Tasks

### Task 1: Backend - Plan Capabilities (3 SP)
- [ ] Create `PLAN_CAPABILITIES` in `backend/quota.py`
- [ ] Update `check_quota()` to return capabilities
- [ ] Add type hints and Pydantic models for capabilities
- [ ] Unit tests for each plan configuration

### Task 2: Backend - Date Range & Excel Validation (2 SP)
- [ ] Implement date range validation in `/api/buscar`
- [ ] Implement Excel gating logic
- [ ] Add error messages with upgrade CTAs
- [ ] Unit tests for validation logic

### Task 3: Backend - Quota & Rate Limiting (5 SP)
- [ ] Implement monthly quota tracking in Supabase
- [ ] Implement rate limiting (Redis or in-memory)
- [ ] Add quota reset logic (cron or lazy reset)
- [ ] Handle 429 errors with `Retry-After`
- [ ] Unit tests for quota enforcement

### Task 4: Backend - AI Summary Token Control (1 SP)
- [ ] Pass `max_summary_tokens` to LLM service
- [ ] Update `llm.py` to respect token limit
- [ ] Test token truncation at each tier

### Task 5: Backend - User Endpoint Enhancement (1 SP)
- [ ] Update `/api/me` to return capabilities
- [ ] Include quota usage and reset date
- [ ] Update response schema
- [ ] Unit tests for endpoint

### Task 6: Frontend - Plan Badge & UI (2 SP)
- [ ] Create `PlanBadge` component
- [ ] Add badge to header/sidebar
- [ ] Implement trial countdown
- [ ] Style for each tier (colors, icons)

### Task 7: Frontend - Excel & Date Range UX (3 SP)
- [ ] Implement locked Excel button with tooltip
- [ ] Implement date range validation UI
- [ ] Add warning messages
- [ ] Connect to capabilities from `/api/me`

### Task 8: Frontend - Quota Counter & Errors (2 SP)
- [ ] Create `QuotaCounter` component
- [ ] Implement progress bar with color coding
- [ ] Handle 403/429 errors with upgrade CTAs
- [ ] Add analytics tracking for upgrade clicks

### Task 9: Frontend - Upgrade Modal (2 SP)
- [ ] Create `UpgradeModal` component
- [ ] Plan comparison table
- [ ] Highlight benefits of each tier
- [ ] CTAs for Stripe checkout (or payment gateway)

### Task 10: Testing - Backend Suite (2 SP)
- [ ] Comprehensive test suite for all plan logic
- [ ] Edge cases (leap year, timezone, quota reset)
- [ ] Integration tests with mocked Supabase/Redis
- [ ] Ensure >= 70% coverage

### Task 11: Testing - Frontend Suite (2 SP)
- [ ] Test all UI components (badge, counter, modal)
- [ ] Test validation logic (date range, quota)
- [ ] Test error handling
- [ ] Ensure >= 60% coverage

### Task 12: Deployment & Monitoring (1 SP)
- [ ] Implement feature flag
- [ ] Deploy to staging
- [ ] Monitor error rates, performance
- [ ] Gradual rollout to production
- [ ] Document rollback procedure

---

## Implementation Design

### PLAN_CAPABILITIES Structure

```python
# backend/quota.py

from typing import TypedDict
from enum import Enum

class PlanPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class PlanCapabilities(TypedDict):
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
        "max_requests_per_month": 999999,  # Unlimited during trial
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

# Plan display names
PLAN_NAMES = {
    "free_trial": "FREE Trial",
    "consultor_agil": "Consultor Ágil",
    "maquina": "Máquina",
    "sala_guerra": "Sala de Guerra",
}

# Upgrade suggestions for error messages
UPGRADE_SUGGESTIONS = {
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

### Enhanced check_quota() Return

```python
# backend/quota.py

from pydantic import BaseModel
from datetime import datetime

class QuotaInfo(BaseModel):
    allowed: bool
    plan_id: str
    plan_name: str
    capabilities: PlanCapabilities
    quota_used: int
    quota_remaining: int
    quota_reset_date: datetime
    trial_expires_at: datetime | None
    error_message: str | None

def check_quota(user_id: str) -> QuotaInfo:
    """
    Check user's plan and quota status.

    Returns complete quota info including capabilities and usage.
    """
    # Fetch from Supabase
    user = get_user_from_db(user_id)
    plan_id = user.get("plan_id", "free_trial")

    # Get capabilities
    caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES["free_trial"])

    # Check trial expiration
    trial_expires_at = user.get("trial_expires_at")
    if trial_expires_at and datetime.utcnow() > trial_expires_at:
        return QuotaInfo(
            allowed=False,
            plan_id=plan_id,
            plan_name=PLAN_NAMES[plan_id],
            capabilities=caps,
            quota_used=0,
            quota_remaining=0,
            quota_reset_date=datetime.utcnow(),
            trial_expires_at=trial_expires_at,
            error_message="Trial expirado. Faça upgrade para continuar usando o Smart PNCP.",
        )

    # Check monthly quota
    quota_used = get_monthly_quota_used(user_id)
    quota_limit = caps["max_requests_per_month"]
    quota_remaining = max(0, quota_limit - quota_used)

    if quota_used >= quota_limit:
        reset_date = get_next_month_start()
        return QuotaInfo(
            allowed=False,
            plan_id=plan_id,
            plan_name=PLAN_NAMES[plan_id],
            capabilities=caps,
            quota_used=quota_used,
            quota_remaining=0,
            quota_reset_date=reset_date,
            trial_expires_at=trial_expires_at,
            error_message=f"Limite de {quota_limit} buscas mensais atingido. Renovação em {reset_date.strftime('%d/%m/%Y')} ou faça upgrade.",
        )

    return QuotaInfo(
        allowed=True,
        plan_id=plan_id,
        plan_name=PLAN_NAMES[plan_id],
        capabilities=caps,
        quota_used=quota_used,
        quota_remaining=quota_remaining,
        quota_reset_date=get_next_month_start(),
        trial_expires_at=trial_expires_at,
        error_message=None,
    )
```

### Date Range Validation in /api/buscar

```python
# backend/main.py

from datetime import datetime
from fastapi import HTTPException, status

@app.post("/api/buscar")
async def buscar(request: BuscaRequest, user_id: str = Depends(get_current_user)):
    # Check quota
    quota_info = check_quota(user_id)
    if not quota_info.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": quota_info.error_message,
                "upgrade_cta": "Fazer Upgrade",
                "suggested_plan": "maquina",  # Logic to suggest next tier
            }
        )

    # Validate date range
    date_start = datetime.strptime(request.data_inicial, "%Y-%m-%d")
    date_end = datetime.strptime(request.data_final, "%Y-%m-%d")
    days_requested = (date_end - date_start).days

    max_days = quota_info.capabilities["max_history_days"]
    if days_requested > max_days:
        suggested_plan = UPGRADE_SUGGESTIONS["max_history_days"].get(quota_info.plan_id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": f"Seu plano {quota_info.plan_name} permite buscas de até {max_days} dias. Você solicitou {days_requested} dias.",
                "upgrade_cta": "Fazer Upgrade",
                "suggested_plan": suggested_plan,
                "suggested_plan_name": PLAN_NAMES.get(suggested_plan, ""),
            }
        )

    # Fetch from PNCP
    licitacoes = await fetch_from_pncp(request)

    # Excel generation (conditional)
    excel_base64 = ""
    excel_available = quota_info.capabilities["allow_excel"]
    if excel_available:
        excel_buffer = create_excel(licitacoes)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode()

    # Increment quota
    increment_monthly_quota(user_id)

    return {
        "licitacoes": licitacoes,
        "excel_base64": excel_base64 if excel_available else None,
        "excel_available": excel_available,
        "quota_remaining": quota_info.quota_remaining - 1,
        "upgrade_message": None if excel_available else "Exportar Excel disponível no plano Máquina.",
    }
```

### Frontend - PlanBadge Component

```tsx
// frontend/components/PlanBadge.tsx

import { useEffect, useState } from 'react';

interface PlanBadgeProps {
  planId: string;
  planName: string;
  trialExpiresAt?: string;
}

const PLAN_COLORS = {
  free_trial: 'bg-gray-500',
  consultor_agil: 'bg-blue-500',
  maquina: 'bg-green-500',
  sala_guerra: 'bg-yellow-500',
};

export function PlanBadge({ planId, planName, trialExpiresAt }: PlanBadgeProps) {
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);

  useEffect(() => {
    if (trialExpiresAt) {
      const now = new Date();
      const expires = new Date(trialExpiresAt);
      const daysLeft = Math.ceil((expires.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      setTrialDaysLeft(Math.max(0, daysLeft));
    }
  }, [trialExpiresAt]);

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-full text-white text-sm font-medium ${PLAN_COLORS[planId]} cursor-pointer hover:opacity-90`}>
      {planName}
      {trialDaysLeft !== null && (
        <span className="ml-2 text-xs">
          ({trialDaysLeft} dias restantes)
        </span>
      )}
    </div>
  );
}
```

### Frontend - QuotaCounter Component

```tsx
// frontend/components/QuotaCounter.tsx

interface QuotaCounterProps {
  quotaUsed: number;
  quotaLimit: number;
  resetDate: string;
}

export function QuotaCounter({ quotaUsed, quotaLimit, resetDate }: QuotaCounterProps) {
  const percentage = (quotaUsed / quotaLimit) * 100;
  const color = percentage < 70 ? 'bg-green-500' : percentage < 90 ? 'bg-yellow-500' : 'bg-red-500';

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span>Buscas este mês: {quotaUsed}/{quotaLimit}</span>
        <span className="text-gray-500">Renovação: {new Date(resetDate).toLocaleDateString('pt-BR')}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all duration-300`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}
```

---

## Definition of Done

- [ ] PLAN_CAPABILITIES implemented in backend
- [ ] check_quota() returns extended info
- [ ] Date range validation enforced
- [ ] Excel gating implemented
- [ ] Monthly quota tracking working
- [ ] Rate limiting implemented
- [ ] AI summary token control working
- [ ] /api/me returns capabilities
- [ ] Plan badge displayed in frontend
- [ ] Excel button locked for non-eligible plans
- [ ] Date range validation in UI
- [ ] Quota counter displayed
- [ ] Error handling (403, 429) with upgrade CTAs
- [ ] Upgrade modal functional
- [ ] Backend tests >= 70% coverage
- [ ] Frontend tests >= 60% coverage
- [ ] Feature flag implemented
- [ ] Deployed to staging
- [ ] Documentation updated
- [ ] Code reviewed by peer

---

## Story Points: 26 SP

**Complexity:** High (multi-layer changes: backend validation, frontend UX, quota tracking, rate limiting)
**Uncertainty:** Low (clear requirements, no external dependencies)

---

## Dependencies

None (standalone feature, no dependencies on other stories)

---

## Blocks

- GTM launch (cannot launch without pricing structure)
- Payment gateway integration (future story)

---

## Test Scenarios

1. **FREE trial user (day 1)** - Can search 7-day range, no Excel, see trial countdown
2. **FREE trial user (day 7)** - Trial expires, forced to upgrade
3. **Consultor Ágil user** - Can search 30-day range, no Excel, sees quota counter
4. **Consultor Ágil user (quota exhausted)** - Gets 429 error, sees reset date and upgrade CTA
5. **Máquina user** - Can search 1-year range, Excel enabled, higher quota
6. **Sala de Guerra user** - Can search 5-year range, Excel enabled, highest quota
7. **User tries 60-day search on 30-day plan** - Gets 403 error with upgrade suggestion
8. **User clicks locked Excel button** - Opens upgrade modal with Máquina pre-selected
9. **Rate limiting** - User makes 11 requests/min on Consultor Ágil plan, gets 429 error
10. **Quota reset** - On 1st of month, quota counter resets to 0

---

## Migration Plan

### User Migration (N/A - No Paying Users)
Since there are no paying users yet, no migration is needed. All new users will start with FREE trial.

### Database Schema Updates
```sql
-- Add trial tracking
ALTER TABLE users ADD COLUMN trial_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP;

-- Add quota tracking
CREATE TABLE monthly_quota (
    user_id UUID REFERENCES users(id),
    month_year VARCHAR(7),  -- Format: "2026-02"
    searches_count INT DEFAULT 0,
    PRIMARY KEY (user_id, month_year)
);

-- Add plan_id column (if not exists)
ALTER TABLE users ADD COLUMN plan_id VARCHAR(50) DEFAULT 'free_trial';
```

### Rollout Strategy
1. **Week 1 (Staging):** Deploy to staging, test all flows
2. **Week 2 (10% rollout):** Enable for 10% of users (feature flag)
3. **Week 3 (50% rollout):** Expand to 50% if no issues
4. **Week 4 (100% rollout):** Full deployment

---

## References

- PRD: `PRD.md` (to be updated)
- Architecture: `docs/architecture/plan-capabilities.md` (to be created)
- Pricing Page: `docs/pricing.md` (to be created)

---

**Story Status:** READY FOR DEVELOPMENT
**Estimated Duration:** 8-10 days
**Priority:** P0 - Critical (GTM blocker)
