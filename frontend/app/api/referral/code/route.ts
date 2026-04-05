/**
 * Referral code proxy — requires auth.
 * Returns the authenticated user's referral code (creates lazily if missing).
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { GET } = createProxyRoute({
  backendPath: "/v1/referral/code",
  requireAuth: true,
  errorMessage: "Erro ao obter código de indicação.",
});
