# GTM-FIX-009: Fix Email Confirmation Dead End

## Dimension Impact
- Moves D03 (Mobile Experience) +0.5 (many signups happen on mobile)
- Moves D08 (Onboarding) +1

## Problem
After email signup, user sees a static "Check your email" screen with no resend button, no polling for confirmation status, and no auto-detection (signup/page.tsx:183-200). If email is delayed or goes to spam, user is stuck with no recovery path. Industry benchmarks show 20-40% abandonment rate for this pattern.

## Solution
1. Add "Resend confirmation email" button with rate limiting (max 1 per 60s)
2. Add countdown timer: "Didn't receive? Resend in 57s..."
3. Implement client-side polling every 5s to check confirmation status
4. Auto-redirect to /onboarding when confirmation detected
5. Add "Check spam folder" helper text with visual guide
6. Add "Change email address" link (back to signup form with email pre-filled)

## Acceptance Criteria
- [ ] AC1: Signup success screen shows "Resend email" button (initially disabled for 60s)
- [ ] AC2: Button includes countdown: "Resend in 57s" → "Resend email"
- [ ] AC3: Clicking "Resend" calls `POST /api/auth/resend-confirmation`
- [ ] AC4: Backend endpoint calls Supabase `auth.resend({ type: 'signup', email })`
- [ ] AC5: After resend, button disabled again for 60s with new countdown
- [ ] AC6: Toast notification: "Email reenviado! Verifique sua caixa de entrada."
- [ ] AC7: Client polls `GET /api/auth/status` every 5s
- [ ] AC8: Endpoint returns `{ confirmed: boolean, user_id?: string }`
- [ ] AC9: When `confirmed === true`, auto-redirect to /onboarding
- [ ] AC10: Show transition message: "Email confirmado! Redirecionando..."
- [ ] AC11: "Não recebeu?" section includes spam folder GIF/illustration
- [ ] AC12: "Alterar email" link → back to signup with email field pre-filled
- [ ] AC13: Backend test: test_resend_confirmation_rate_limit()
- [ ] AC14: Backend test: test_auth_status_returns_confirmation_state()
- [ ] AC15: Frontend test: test_resend_button_countdown()
- [ ] AC16: Frontend test: test_auto_redirect_on_confirmation()

## Effort: S (4h)
## Priority: P1 (High abandonment risk)
## Dependencies: None

## Files to Modify
- `frontend/app/signup/page.tsx` (update confirmation screen)
- `frontend/app/api/auth/resend-confirmation/route.ts` (NEW)
- `frontend/app/api/auth/status/route.ts` (NEW)
- `backend/routes/auth.py` (add resend_confirmation, auth_status endpoints)
- `backend/tests/test_auth.py` (add resend/status tests)
- `frontend/__tests__/auth/signup-confirmation.test.tsx` (NEW)

## Testing Strategy
1. Unit test (backend): test_resend_confirmation_within_60s_blocked()
2. Unit test (backend): test_resend_confirmation_after_60s_succeeds()
3. Unit test (frontend): Mock timer → verify countdown updates every second
4. Unit test (frontend): Mock polling → verify redirect on confirmation
5. Integration test: Real signup → wait for email → verify resend works
6. Manual test: Complete signup flow on mobile device (iOS + Android)

## UI Design Spec

**Confirmation Screen (updated):**
```tsx
<div className="max-w-md mx-auto p-6 text-center">
  <Mail className="w-16 h-16 text-blue-500 mx-auto mb-4" />

  <h1 className="text-2xl font-bold mb-2">
    Confirme seu email
  </h1>

  <p className="text-gray-600 mb-4">
    Enviamos um link de confirmação para:
    <br />
    <strong>{email}</strong>
  </p>

  {/* Auto-detection status */}
  {isPolling && (
    <p className="text-sm text-blue-600 mb-4">
      🔄 Aguardando confirmação...
    </p>
  )}

  {/* Resend button with countdown */}
  <button
    onClick={handleResend}
    disabled={countdown > 0}
    className="w-full py-3 bg-blue-600 text-white rounded-lg disabled:bg-gray-300"
  >
    {countdown > 0 ? `Reenviar em ${countdown}s` : 'Reenviar email'}
  </button>

  {/* Helper section */}
  <div className="mt-6 p-4 bg-yellow-50 rounded-lg text-left">
    <h3 className="font-semibold text-sm mb-2">
      📧 Não recebeu o email?
    </h3>
    <ul className="text-sm space-y-1 text-gray-700">
      <li>• Verifique sua caixa de spam/lixo eletrônico</li>
      <li>• Aguarde até 5 minutos</li>
      <li>• Confirme se o email está correto</li>
    </ul>
    <button
      onClick={() => router.push('/signup?email=' + encodeURIComponent(email))}
      className="text-blue-600 text-sm mt-2 underline"
    >
      Alterar email
    </button>
  </div>
</div>
```

## Backend Endpoints

**POST /v1/auth/resend-confirmation:**
```python
@router.post("/resend-confirmation")
async def resend_confirmation(request: ResendRequest):
    # Check rate limit (Redis or in-memory cache)
    last_sent = get_last_resend_time(request.email)
    if last_sent and (now - last_sent) < 60:
        raise HTTPException(429, "Wait 60s before resending")

    # Resend via Supabase
    response = supabase.auth.resend({
        "type": "signup",
        "email": request.email,
    })

    set_last_resend_time(request.email, now)
    return {"success": True}
```

**GET /v1/auth/status:**
```python
@router.get("/status")
async def auth_status(email: str):
    # Query Supabase auth.users
    user = supabase.auth.admin.list_users(filters={"email": email})
    if user and user.email_confirmed_at:
        return {"confirmed": True, "user_id": user.id}
    return {"confirmed": False}
```

## Polling Implementation

```tsx
useEffect(() => {
  if (!isWaitingForConfirmation) return;

  const interval = setInterval(async () => {
    const response = await fetch(`/api/auth/status?email=${email}`);
    const data = await response.json();

    if (data.confirmed) {
      setIsPolling(false);
      toast.success("Email confirmado! Redirecionando...");
      setTimeout(() => router.push('/onboarding'), 1500);
    }
  }, 5000); // Poll every 5s

  return () => clearInterval(interval);
}, [isWaitingForConfirmation, email]);
```

## Future Enhancement (not in scope)
- WebSocket for instant confirmation (no polling delay)
- Magic link alternative: "Skip email, login with magic link instead"
- Social auth alternatives: "Or continue with Google/LinkedIn"
- SMS confirmation as fallback for problematic email providers
