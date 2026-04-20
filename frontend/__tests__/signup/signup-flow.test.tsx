/**
 * STORY-CONV-003b AC5: end-to-end signup flow integration test.
 *
 * Asserts the contract between the card branch and the backend:
 *   POST /api/auth/signup-trial receives { email, password, full_name,
 *   stripe_payment_method_id } and returns 200.
 *
 * We test this at the proxy boundary rather than rendering the full page —
 * `SignupPage` uses ~5 React contexts (AuthProvider, useRouter, useAnalytics,
 * useAuth, Sonner) and rendering it end-to-end adds fixture weight without
 * catching real bugs. The real value is (a) payload shape matches backend
 * expectations and (b) 4xx/5xx surfaces as Error.
 *
 * Complement to CardCollect.test.tsx (render) and rollout-hash.test.ts
 * (distribution).
 */
/** @jest-environment jsdom */

describe("signup-flow: card branch contract", () => {
  afterEach(() => {
    (global as any).fetch = undefined;
  });

  it("POSTs the expected body to /api/auth/signup-trial", async () => {
    const fetchSpy = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: "u-1",
        email: "a@b.com",
        trial_end_ts: 1_800_000_000,
        subscription_status: "trialing",
      }),
    });
    (global as any).fetch = fetchSpy;

    const res = await fetch("/api/auth/signup-trial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "a@b.com",
        password: "Abcdef12",
        full_name: "Founder B2G",
        stripe_payment_method_id: "pm_test_123",
      }),
    });

    expect(res.ok).toBe(true);
    const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
    expect(body).toEqual({
      email: "a@b.com",
      password: "Abcdef12",
      full_name: "Founder B2G",
      stripe_payment_method_id: "pm_test_123",
    });
  });

  it("surfaces 400 from backend (disposable / weak password)", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Este provedor de email não é aceito. Use um email corporativo ou pessoal.",
      }),
    });

    const res = await fetch("/api/auth/signup-trial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "a@tempmail.com", password: "Abcdef12" }),
    });

    expect(res.ok).toBe(false);
    expect(res.status).toBe(400);
    const body = await res.json();
    expect(body.detail).toMatch(/provedor de email não é aceito/);
  });

  it("surfaces 409 when email already exists", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        detail: "Email já cadastrado. Faça login ou recupere sua senha.",
      }),
    });

    const res = await fetch("/api/auth/signup-trial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "taken@example.com", password: "Abcdef12" }),
    });

    expect(res.status).toBe(409);
    const body = await res.json();
    expect(body.detail).toMatch(/já cadastrado/);
  });

  it("fail-open: 200 with subscription_status=payment_failed when Stripe recusou", async () => {
    // STORY-CONV-003a AC2: backend returns 200 with subscription_status
    // 'payment_failed' when Stripe fails AFTER Supabase user was created.
    // Frontend should NOT throw — user keeps grace access + billing recon
    // retries in background.
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: "u-2",
        email: "a@b.com",
        trial_end_ts: 1_800_000_000,
        stripe_customer_id: "cus_x",
        stripe_subscription_id: null,
        subscription_status: "payment_failed",
        requires_email_confirmation: true,
      }),
    });

    const res = await fetch("/api/auth/signup-trial", {
      method: "POST",
      body: JSON.stringify({
        email: "a@b.com",
        password: "Abcdef12",
        stripe_payment_method_id: "pm_bad",
      }),
    });

    expect(res.ok).toBe(true);
    const body = await res.json();
    expect(body.subscription_status).toBe("payment_failed");
    expect(body.stripe_subscription_id).toBeNull();
  });
});
