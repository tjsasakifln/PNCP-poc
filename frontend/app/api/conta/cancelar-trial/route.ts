/**
 * Cancel-trial proxy (STORY-CONV-003c AC7).
 *
 * GET  /api/conta/cancelar-trial?token=<jwt> → backend returns trial
 *      metadata (no state mutation).
 * POST /api/conta/cancelar-trial with { token } → backend executes
 *      Stripe.Subscription.cancel + DB state transition. Idempotent.
 *
 * Anonymous (no auth header) — the JWT token is the credential. Backend
 * validates signature, TTL (48h), action claim, and user existence.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { GET, POST } = createProxyRoute({
  backendPath: "/v1/conta/cancelar-trial",
  methods: ["GET", "POST"],
  requireAuth: false,
  errorMessage: "Link de cancelamento inválido ou expirado.",
});
