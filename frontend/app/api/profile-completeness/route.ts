import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

const getBackendUrl = () => process.env.BACKEND_URL;

/**
 * STORY-260: API proxy for profile completeness.
 * GET /api/profile-completeness → GET BACKEND_URL/v1/profile/completeness
 */
export async function GET(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Serviço temporariamente indisponível" },
      { status: 503 }
    );
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json(
      { message: "Autenticação necessária" },
      { status: 401 }
    );
  }

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Authorization: authHeader,
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const response = await fetch(`${backendUrl}/v1/profile/completeness`, {
      headers,
    });

    if (!response.ok) {
      const body = await response.text();
      const sanitized = sanitizeProxyError(
        response.status,
        body,
        response.headers.get("content-type")
      );
      if (sanitized) return sanitized;

      try {
        const data = JSON.parse(body);
        return NextResponse.json(
          { message: data.detail || data.message || "Erro ao obter completude do perfil" },
          { status: response.status }
        );
      } catch {
        return NextResponse.json(
          { message: "Erro temporário de comunicação" },
          { status: response.status }
        );
      }
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(
      "[profile-completeness] Error:",
      error instanceof Error ? error.message : error
    );
    return sanitizeNetworkError(error);
  }
}
