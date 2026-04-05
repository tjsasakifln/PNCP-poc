/**
 * Referral redeem proxy — requires auth (called right after signup).
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/referral/redeem",
  requireAuth: true,
  methods: ["POST"],
  errorMessage: "Erro ao registrar indicação.",
});
