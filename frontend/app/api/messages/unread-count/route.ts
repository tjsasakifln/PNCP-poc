import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../../lib/serverAuth";

const backendUrl = process.env.BACKEND_URL;

export async function GET(request: NextRequest) {
  if (!backendUrl)
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });

  // STORY-253 AC7: Prefer server-side refreshed token, fall back to header
  const refreshedToken = await getRefreshedToken();
  const authHeader = refreshedToken
    ? `Bearer ${refreshedToken}`
    : request.headers.get("authorization");

  if (!authHeader)
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });

  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");

  try {
    const res = await fetch(`${backendUrl}/v1/api/messages/unread-count`, {
      headers: { Authorization: authHeader, "Content-Type": "application/json", ...(correlationId && { "X-Correlation-ID": correlationId }) },
    });

    // If 401 even after refresh, signal session expired
    if (res.status === 401) {
      return NextResponse.json(
        { message: "Sessao expirada", session_expired: true },
        { status: 401 }
      );
    }

    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ message: "Erro ao conectar com servidor" }, { status: 503 });
  }
}
