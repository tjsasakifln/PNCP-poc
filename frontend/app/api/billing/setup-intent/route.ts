/**
 * Setup intent proxy (STORY-CONV-003b AC2).
 *
 * Pre-signup: no auth header required. Backend enforces IP rate limit
 * via the same bucket as /auth/signup (3 req / 10 min).
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/billing/setup-intent",
  methods: ["POST"],
  requireAuth: false,
  errorMessage: "Não foi possível preparar a coleta do cartão.",
});
