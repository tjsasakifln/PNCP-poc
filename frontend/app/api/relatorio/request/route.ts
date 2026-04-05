/**
 * Panorama 2026 T1 — lead capture proxy (email-gated report).
 * No auth required: this endpoint is called from the public landing page.
 * Backend is responsible for validation, rate-limiting, email delivery.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/relatorio-2026-t1/request",
  requireAuth: false,
  methods: ["POST"],
  errorMessage: "Nao foi possivel processar sua solicitacao. Tente novamente.",
  logPrefix: "relatorio-2026-t1",
});

export const runtime = "nodejs";
