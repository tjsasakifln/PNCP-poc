/**
 * Trial extension proxy — POST /v1/trial/extend — requires auth.
 * Zero-Churn P2 §8.2
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/trial/extend",
  methods: ["POST"],
  requireAuth: true,
  errorMessage: "Erro ao estender trial",
});
