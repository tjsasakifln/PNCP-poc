import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

const POST_ENDPOINTS = ["track-cta"];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !["summary", "searches-over-time", "top-dimensions", "trial-value"].includes(endpoint)) {
    return NextResponse.json({ error: "Invalid endpoint" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { error: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  // Build backend URL with query params (excluding 'endpoint')
  const backendParams = new URLSearchParams();
  searchParams.forEach((value, key) => {
    if (key !== "endpoint") backendParams.set(key, value);
  });

  const fullUrl = `${backendUrl}/v1/analytics/${endpoint}${backendParams.toString() ? `?${backendParams}` : ""}`;

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Authorization: authHeader,
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const res = await fetch(fullUrl, { headers });

    if (!res.ok) {
      // CRIT-017: Sanitize non-JSON / infrastructure errors
      const body = await res.text();
      const sanitized = sanitizeProxyError(res.status, body, res.headers.get("content-type"));
      if (sanitized) return sanitized;

      // Structured backend error — parse and forward
      try {
        const parsed = JSON.parse(body);
        return NextResponse.json(
          { error: parsed.detail || parsed.message || "Erro do servidor" },
          { status: res.status }
        );
      } catch {
        return NextResponse.json(
          { error: "Erro do servidor" },
          { status: res.status }
        );
      }
    }

    const data = await res.json().catch(() => null);
    if (!data) {
      return NextResponse.json(
        { error: "Resposta inesperada do servidor" },
        { status: 502 }
      );
    }
    return NextResponse.json(data);
  } catch (error) {
    // CRIT-017: Sanitize network errors
    console.error("[analytics] Network error:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}

// STORY-312 AC11: POST handler for CTA event tracking
export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !POST_ENDPOINTS.includes(endpoint)) {
    return NextResponse.json({ error: "Invalid endpoint" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return new NextResponse(null, { status: 204 }); // Silently ignore if no backend
  }

  try {
    const body = await request.json();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (authHeader) {
      headers["Authorization"] = authHeader;
    }

    await fetch(`${backendUrl}/v1/analytics/${endpoint}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    return new NextResponse(null, { status: 204 });
  } catch {
    // Fire-and-forget — always return 204
    return new NextResponse(null, { status: 204 });
  }
}
