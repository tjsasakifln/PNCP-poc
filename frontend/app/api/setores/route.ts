import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servidor nao configurado" },
      { status: 503 }
    );
  }

  // CRIT-004 AC4: Forward X-Correlation-ID for distributed tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {};
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const response = await fetch(`${backendUrl}/v1/setores`, { headers });

    if (!response.ok) {
      return NextResponse.json(
        { message: "Erro ao buscar setores" },
        { status: response.status }
      );
    }

    const data = await response.json().catch(() => null);
    if (!data) {
      return NextResponse.json(
        { message: "Resposta inesperada do servidor" },
        { status: 502 }
      );
    }
    return NextResponse.json(data);
  } catch (error) {
    console.error("Erro ao buscar setores:", error);
    return NextResponse.json(
      { message: "Backend indisponível" },
      { status: 503 }
    );
  }
}
