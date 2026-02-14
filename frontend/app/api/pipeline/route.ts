import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

function getAuthHeader(request: NextRequest): string | null {
  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ")) return null;
  return authHeader;
}

export async function GET(request: NextRequest) {
  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json({ message: "Autenticação necessária." }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const queryString = searchParams.toString();
  const path = searchParams.get("_path") || "/pipeline";
  const cleanParams = new URLSearchParams(searchParams);
  cleanParams.delete("_path");
  const qs = cleanParams.toString();

  const url = `${BACKEND_URL}/v1${path}${qs ? `?${qs}` : ""}`;

  try {
    const response = await fetch(url, {
      headers: { Authorization: auth },
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ message: "Erro ao conectar com servidor." }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json({ message: "Autenticação necessária." }, { status: 401 });
  }

  try {
    const body = await request.json();
    const response = await fetch(`${BACKEND_URL}/v1/pipeline`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: auth,
      },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ message: "Erro ao conectar com servidor." }, { status: 502 });
  }
}

export async function PATCH(request: NextRequest) {
  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json({ message: "Autenticação necessária." }, { status: 401 });
  }

  try {
    const body = await request.json();
    const { item_id, ...updateData } = body;
    const response = await fetch(`${BACKEND_URL}/v1/pipeline/${item_id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: auth,
      },
      body: JSON.stringify(updateData),
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ message: "Erro ao conectar com servidor." }, { status: 502 });
  }
}

export async function DELETE(request: NextRequest) {
  const auth = getAuthHeader(request);
  if (!auth) {
    return NextResponse.json({ message: "Autenticação necessária." }, { status: 401 });
  }

  try {
    const { searchParams } = new URL(request.url);
    const itemId = searchParams.get("id");
    if (!itemId) {
      return NextResponse.json({ message: "ID do item é obrigatório." }, { status: 400 });
    }
    const response = await fetch(`${BACKEND_URL}/v1/pipeline/${itemId}`, {
      method: "DELETE",
      headers: { Authorization: auth },
    });
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ message: "Erro ao conectar com servidor." }, { status: 502 });
  }
}
