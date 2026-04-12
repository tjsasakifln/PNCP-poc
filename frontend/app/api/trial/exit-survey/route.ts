/**
 * STORY-369 AC2: Proxy for trial exit survey endpoint.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/trial/exit-survey",
  methods: ["POST"],
  requireAuth: true,
  errorMessage: "Erro ao enviar resposta",
});
