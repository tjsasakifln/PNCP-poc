/**
 * STORY-BIZ-001: founding customer checkout proxy.
 * No auth required — called from the public /founding landing.
 * Backend enforces rate-limiting, CNPJ validation, and duplicate-email check.
 */
import { createProxyRoute } from "../../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: "/v1/founding/checkout",
  requireAuth: false,
  methods: ["POST"],
  errorMessage:
    "Nao foi possivel processar sua solicitacao. Revise os dados e tente novamente.",
  logPrefix: "founding-checkout",
});

export const runtime = "nodejs";
