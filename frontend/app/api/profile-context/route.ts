import { NextRequest, NextResponse } from "next/server";

const getBackendUrl = () => process.env.BACKEND_URL;

export async function GET(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
  }

  try {
    const response = await fetch(`${backendUrl}/v1/profile/context`, {
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao obter contexto" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching profile context:", error);
    return NextResponse.json({ message: "Erro ao conectar com servidor" }, { status: 503 });
  }
}

export async function PUT(request: NextRequest) {
  const backendUrl = getBackendUrl();
  if (!backendUrl) {
    return NextResponse.json({ message: "Servidor nao configurado" }, { status: 503 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ message: "Autenticacao necessaria" }, { status: 401 });
  }

  try {
    const body = await request.json();
    const response = await fetch(`${backendUrl}/v1/profile/context`, {
      method: "PUT",
      headers: { Authorization: authHeader, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      return NextResponse.json(
        { message: error.detail || "Erro ao salvar contexto" },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error saving profile context:", error);
    return NextResponse.json({ message: "Erro ao conectar com servidor" }, { status: 503 });
  }
}
