/**
 * Trial signup proxy with Stripe card capture (STORY-CONV-003b AC1).
 *
 * POST /api/auth/signup-trial
 *
 * Forwards to backend POST /v1/auth/signup (supports
 * `stripe_payment_method_id`). Distinct from /api/auth/signup (Supabase
 * direct) because the backend path creates the Supabase user *plus* the
 * Stripe Customer + Subscription with 14-day trial.
 *
 * Backend performs its own rate limiting (3 req / 10 min per IP).
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/auth/signup",
  methods: ["POST"],
  requireAuth: false,
  errorMessage: "Erro ao criar conta. Tente novamente em instantes.",
});
