/**
 * STORY-BIZ-002: proxy for GET /v1/user/recommended-plan.
 * Requires auth; backend caches result in Redis for 24h per user.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { GET } = createProxyRoute({
  backendPath: "/v1/user/recommended-plan",
  requireAuth: true,
  methods: ["GET"],
  errorMessage: "Nao foi possivel carregar sua recomendacao de plano.",
  logPrefix: "recommended-plan",
});

export const runtime = "nodejs";
