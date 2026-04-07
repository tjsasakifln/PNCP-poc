/**
 * Trial extensions status proxy — GET /v1/trial/extensions — requires auth.
 * Zero-Churn P2 §8.2
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { GET } = createProxyRoute({
  backendPath: "/v1/trial/extensions",
  methods: ["GET"],
  requireAuth: true,
  errorMessage: "Erro ao carregar extensoes do trial",
});
