/**
 * Referral stats proxy — requires auth.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { GET } = createProxyRoute({
  backendPath: "/v1/referral/stats",
  requireAuth: true,
  errorMessage: "Erro ao obter estatísticas de indicação.",
});
