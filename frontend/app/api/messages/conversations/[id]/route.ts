import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  if (!backendUrl)
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });

  const authHeader = request.headers.get("authorization");
  if (!authHeader)
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });

  const { id } = await params;

  try {
    const res = await fetch(
      `${backendUrl}/api/messages/conversations/${id}`,
      { headers: { Authorization: authHeader, "Content-Type": "application/json" } },
    );
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ message: "Erro ao conectar com servidor" }, { status: 503 });
  }
}
