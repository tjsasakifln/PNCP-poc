/**
 * STORY-258: Proxy for GET /v1/auth/check-email?email=...
 *
 * Checks whether an email address is disposable or corporate.
 * Transforms backend response fields:
 *   backend:  { available, disposable, corporate }
 *   frontend: { is_disposable, is_corporate, available }
 */
import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../../lib/proxy-error-handler";

export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("[auth/check-email] BACKEND_URL is not configured");
    return NextResponse.json(
      { message: "Serviço temporariamente indisponível" },
      { status: 503 }
    );
  }

  const email = request.nextUrl.searchParams.get("email");
  if (!email) {
    return NextResponse.json(
      { message: "Parâmetro email obrigatório" },
      { status: 400 }
    );
  }

  // Forward correlation ID for distributed tracing
  const correlationId =
    request.headers.get("X-Correlation-ID") ?? crypto.randomUUID();

  const headers: Record<string, string> = {
    "X-Correlation-ID": correlationId,
  };

  // Forward auth header if present (not required for this endpoint)
  const authHeader = request.headers.get("authorization");
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }

  try {
    const response = await fetch(
      `${backendUrl}/v1/auth/check-email?email=${encodeURIComponent(email)}`,
      { headers }
    );

    // Forward 429 rate-limit responses directly
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      return NextResponse.json(
        { message: "Muitas requisições. Tente novamente em instantes." },
        {
          status: 429,
          headers: retryAfter ? { "Retry-After": retryAfter } : {},
        }
      );
    }

    const body = await response.text();
    const sanitized = sanitizeProxyError(
      response.status,
      body,
      response.headers.get("content-type")
    );
    if (sanitized) return sanitized;

    if (!response.ok) {
      try {
        const data = JSON.parse(body);
        return NextResponse.json(
          { message: data.detail || data.message || "Erro ao verificar email" },
          { status: response.status }
        );
      } catch {
        return NextResponse.json(
          { message: "Erro temporário de comunicação" },
          { status: 502 }
        );
      }
    }

    // Transform backend fields to frontend-expected shape:
    //   backend:  { available, disposable, corporate }
    //   frontend: { is_disposable, is_corporate, available }
    const data = JSON.parse(body);
    return NextResponse.json({
      available: data.available ?? true,
      is_disposable: data.disposable ?? false,
      is_corporate: data.corporate ?? false,
    });
  } catch (error) {
    console.error(
      "[auth/check-email] Network error:",
      error instanceof Error ? error.message : error
    );
    return sanitizeNetworkError(error);
  }
}
