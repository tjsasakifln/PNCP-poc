import { NextRequest, NextResponse } from "next/server";
import { sanitizeProxyError, sanitizeNetworkError } from "../../../lib/proxy-error-handler";

const ALLOWED_ENDPOINTS = ["status", "recovery-codes", "verify-recovery", "regenerate-recovery"];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint") || "status";

  if (!ALLOWED_ENDPOINTS.includes(endpoint)) {
    return NextResponse.json({ error: "Endpoint inválido" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json({ error: "Servidor não configurado" }, { status: 503 });
  }

  const headers: Record<string, string> = { Authorization: authHeader };
  const correlationId = request.headers.get("X-Correlation-ID");
  if (correlationId) headers["X-Correlation-ID"] = correlationId;

  try {
    const res = await fetch(`${backendUrl}/v1/mfa/${endpoint}`, { headers });
    if (!res.ok) {
      const body = await res.text();
      const sanitized = sanitizeProxyError(res.status, body, res.headers.get("content-type"));
      if (sanitized) return sanitized;
      try {
        const parsed = JSON.parse(body);
        return NextResponse.json(
          { error: parsed.detail || "Erro do servidor" },
          { status: res.status }
        );
      } catch {
        return NextResponse.json({ error: "Erro do servidor" }, { status: res.status });
      }
    }
    const data = await res.json().catch(() => null);
    if (!data) return NextResponse.json({ error: "Resposta inesperada" }, { status: 502 });
    return NextResponse.json(data);
  } catch (error) {
    console.error("[mfa-proxy] Network error:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !ALLOWED_ENDPOINTS.includes(endpoint)) {
    return NextResponse.json({ error: "Endpoint inválido" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json({ error: "Servidor não configurado" }, { status: 503 });
  }

  const headers: Record<string, string> = {
    Authorization: authHeader,
    "Content-Type": "application/json",
  };

  let body: string | undefined;
  try {
    body = await request.text();
  } catch {
    body = undefined;
  }

  try {
    const res = await fetch(`${backendUrl}/v1/mfa/${endpoint}`, {
      method: "POST",
      headers,
      body: body || undefined,
    });
    if (!res.ok) {
      const resBody = await res.text();
      const sanitized = sanitizeProxyError(res.status, resBody, res.headers.get("content-type"));
      if (sanitized) return sanitized;
      try {
        const parsed = JSON.parse(resBody);
        return NextResponse.json(
          { error: parsed.detail || "Erro do servidor" },
          { status: res.status }
        );
      } catch {
        return NextResponse.json({ error: "Erro do servidor" }, { status: res.status });
      }
    }
    const data = await res.json().catch(() => null);
    if (!data) return NextResponse.json({ error: "Resposta inesperada" }, { status: 502 });
    return NextResponse.json(data);
  } catch (error) {
    console.error("[mfa-proxy] Network error:", error instanceof Error ? error.message : error);
    return sanitizeNetworkError(error);
  }
}
