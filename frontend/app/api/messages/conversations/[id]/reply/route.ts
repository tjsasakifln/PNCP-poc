import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL;

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!backendUrl)
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });

  const authHeader = request.headers.get("authorization");
  if (!authHeader)
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });

  const { id } = await params;

  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");

  try {
    const body = await request.json();
    const res = await fetch(
      `${backendUrl}/v1/api/messages/conversations/${id}/reply`,
      {
        method: "POST",
        headers: { Authorization: authHeader, "Content-Type": "application/json", ...(correlationId && { "X-Correlation-ID": correlationId }) },
        body: JSON.stringify(body),
      },
    );
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ message: "Erro ao conectar com servidor" }, { status: 503 });
  }
}
