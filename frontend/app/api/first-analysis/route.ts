import { NextRequest, NextResponse } from "next/server";

const getBackendUrl = () => process.env.BACKEND_URL;

export async function POST(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
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
    const body = await request.json();
    const response = await fetch(`${backendUrl}/v1/first-analysis`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao iniciar analise" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error starting first analysis:", error);
    return NextResponse.json(
      { message: "Erro ao conectar com servidor" },
      { status: 503 },
    );
  }
}
