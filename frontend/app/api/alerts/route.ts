import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

const getBackendUrl = () => process.env.BACKEND_URL;

function getAuthHeader(request: NextRequest): string | null {
  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) return null;
  return authHeader;
}

/**
 * STORY-301: API proxy for email alerts CRUD.
 * GET /api/alerts → GET BACKEND_URL/v1/alerts
 */
export async function GET(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servico temporariamente indisponivel" },
      { status: 503 },
    );
  }

  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json(
      { message: "Autenticacao necessaria." },
      { status: 401 },
    );
  }

  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = { Authorization: auth };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const response = await fetch(`${backendUrl}/v1/alerts`, { headers });

    if (!response.ok) {
      const body = await response.text();
      const sanitized = sanitizeProxyError(
        response.status,
        body,
        response.headers.get("content-type"),
      );
      if (sanitized) return sanitized;

      try {
        const data = JSON.parse(body);
        return NextResponse.json(
          { message: data.detail || data.message || "Erro ao carregar alertas" },
          { status: response.status },
        );
      } catch {
        return NextResponse.json(
          { message: "Erro temporario de comunicacao" },
          { status: response.status },
        );
      }
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error(
      "[alerts] Network error:",
      error instanceof Error ? error.message : error,
    );
    return sanitizeNetworkError(error);
  }
}

/**
 * POST /api/alerts → POST BACKEND_URL/v1/alerts
 */
export async function POST(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servico temporariamente indisponivel" },
      { status: 503 },
    );
  }

  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json(
      { message: "Autenticacao necessaria." },
      { status: 401 },
    );
  }

  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Authorization: auth,
    "Content-Type": "application/json",
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const body = await request.json();
    const response = await fetch(`${backendUrl}/v1/alerts`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const responseBody = await response.text();
      const sanitized = sanitizeProxyError(
        response.status,
        responseBody,
        response.headers.get("content-type"),
      );
      if (sanitized) return sanitized;

      try {
        const data = JSON.parse(responseBody);
        return NextResponse.json(
          { message: data.detail || data.message || "Erro ao criar alerta" },
          { status: response.status },
        );
      } catch {
        return NextResponse.json(
          { message: "Erro temporario de comunicacao" },
          { status: response.status },
        );
      }
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error(
      "[alerts] Network error:",
      error instanceof Error ? error.message : error,
    );
    return sanitizeNetworkError(error);
  }
}
