import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../../lib/proxy-error-handler";

const getBackendUrl = () => process.env.BACKEND_URL;

/**
 * STORY-259: API proxy for deep bid analysis.
 * POST /api/bid-analysis/{bidId} → POST BACKEND_URL/v1/bid-analysis/{bidId}
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ bidId: string }> }
) {
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

  const { bidId } = await params;
  if (!bidId) {
    return NextResponse.json({ message: "bidId obrigatório" }, { status: 400 });
  }

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Authorization: authHeader,
    "Content-Type": "application/json",
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const body = await request.json().catch(() => ({}));
    const response = await fetch(`${backendUrl}/v1/bid-analysis/${bidId}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const responseBody = await response.text();
      const sanitized = sanitizeProxyError(
        response.status,
        responseBody,
        response.headers.get("content-type")
      );
      if (sanitized) return sanitized;

      try {
        const data = JSON.parse(responseBody);
        return NextResponse.json(
          { message: data.detail || data.message || "Erro ao obter análise" },
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
      "[bid-analysis] Error:",
      error instanceof Error ? error.message : error
    );
    return sanitizeNetworkError(error);
  }
}
