import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
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

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    Authorization: authHeader,
  };
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const res = await fetch(`${backendUrl}/v1/trial-status`, { headers });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json(
        { error: errorText },
        { status: res.status }
      );
    }

    const data = await res.json().catch(() => null);
    if (!data) {
      return NextResponse.json(
        { error: "Resposta inesperada do servidor" },
        { status: 502 }
      );
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Falha ao conectar com o servidor" },
      { status: 502 }
    );
  }
}
