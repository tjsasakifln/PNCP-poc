/**
 * PARITY-FIX-3: Proxy for search cancel endpoint.
 *
 * POST /api/search-cancel?search_id=xxx -> backend POST /v1/search/{search_id}/cancel
 */

import type { NextRequest } from "next/server";
import { createProxyRoute } from "../../../lib/create-proxy-route";

export const { POST } = createProxyRoute({
  backendPath: (request: NextRequest) => {
    const searchId = new URL(request.url).searchParams.get("search_id") || "";
    return `/v1/search/${encodeURIComponent(searchId)}/cancel`;
  },
  methods: ["POST"],
  requireAuth: true,
  allowRefresh: true,
  forwardQuery: false,
  errorMessage: "Erro ao cancelar busca",
});
