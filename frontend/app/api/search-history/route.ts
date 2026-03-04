import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../lib/serverAuth";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

// ---------------------------------------------------------------------------
// STORY-257B AC11: API route to fetch user's latest saved search
// ---------------------------------------------------------------------------

export async function GET(request: NextRequest) {
  try {
    // Prefer server-side refreshed token, fall back to header
    const refreshedToken = await getRefreshedToken();
    const authHeader = refreshedToken
      ? `Bearer ${refreshedToken}`
      : request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { message: "Autenticacao necessaria. Faca login para continuar." },
        { status: 401 }
      );
    }

    // Get optional setor_id from query params
    const { searchParams } = new URL(request.url);
    const setor_id = searchParams.get("setor_id");

    // Backend URL
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      console.error("BACKEND_URL environment variable is not configured");
      return NextResponse.json(
        { message: "Servidor nao configurado. Contate o suporte." },
        { status: 503 }
      );
    }

    // Build backend endpoint URL
    const url = new URL(`${backendUrl}/v1/search-history/latest`);
    if (setor_id) {
      url.searchParams.set("setor_id", setor_id);
    }

    // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
    const correlationId = request.headers.get("X-Correlation-ID");
    const headers: Record<string, string> = {
      "Authorization": authHeader,
    };
    if (correlationId) {
      headers["X-Correlation-ID"] = correlationId;
    }

    // Fetch from backend
    const response = await fetch(url.toString(), {
      method: "GET",
      headers,
    });

    // If backend doesn't have this endpoint yet, return 404
    if (response.status === 404) {
      return NextResponse.json(
        { message: "Nenhuma análise anterior encontrada" },
        { status: 404 }
      );
    }

    // Handle auth errors
    if (response.status === 401) {
      return NextResponse.json(
        { message: "Sessao expirada. Faca login novamente." },
        { status: 401 }
      );
    }

    if (!response.ok) {
      const body = await response.text();
      const sanitized = sanitizeProxyError(response.status, body, response.headers.get("content-type"));
      if (sanitized) return sanitized;
      try {
        const data = JSON.parse(body);
        return NextResponse.json(data, { status: response.status });
      } catch {
        return NextResponse.json(
          { message: "Servico temporariamente indisponivel. Tente novamente em instantes." },
          { status: response.status }
        );
      }
    }

    // Parse and forward response
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error("[search-history] Error fetching latest search:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}
