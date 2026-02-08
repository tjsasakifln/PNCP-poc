import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL;

function errorResponse(msg: string, status: number) {
  return NextResponse.json({ message: msg }, { status });
}

export async function GET(request: NextRequest) {
  if (!backendUrl) return errorResponse("Servidor nao configurado", 503);

  const authHeader = request.headers.get("authorization");
  if (!authHeader) return errorResponse("Autenticacao necessaria", 401);

  const { searchParams } = new URL(request.url);
  const qs = searchParams.toString();
  const url = `${backendUrl}/api/messages/conversations${qs ? `?${qs}` : ""}`;

  try {
    const res = await fetch(url, {
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
    });
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return errorResponse("Erro ao conectar com servidor", 503);
  }
}

export async function POST(request: NextRequest) {
  if (!backendUrl) return errorResponse("Servidor nao configurado", 503);

  const authHeader = request.headers.get("authorization");
  if (!authHeader) return errorResponse("Autenticacao necessaria", 401);

  try {
    const body = await request.json();
    const res = await fetch(`${backendUrl}/api/messages/conversations`, {
      method: "POST",
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return errorResponse("Erro ao conectar com servidor", 503);
  }
}
