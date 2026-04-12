import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
} as const;

// Preflight handler para embed em domínios externos (STORY-432 AC4)
export async function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const setor = searchParams.get("setor");
  const uf = searchParams.get("uf");

  if (!setor || !uf) {
    return NextResponse.json(
      { message: "Parâmetros 'setor' e 'uf' são obrigatórios" },
      { status: 400 }
    );
  }

  try {
    const resp = await fetch(
      `${BACKEND_URL}/v1/calculadora/dados?setor=${encodeURIComponent(setor)}&uf=${encodeURIComponent(uf)}`,
      {
        headers: { "Content-Type": "application/json" },
        next: { revalidate: 3600 },
      }
    );

    if (!resp.ok) {
      const detail = await resp.text();
      return NextResponse.json(
        { message: detail || "Erro ao buscar dados" },
        { status: resp.status }
      );
    }

    const data = await resp.json();
    // STORY-432 AC4: CORS para suporte a embed em domínios externos
    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=7200",
        ...CORS_HEADERS,
      },
    });
  } catch (error) {
    return NextResponse.json(
      { message: "Erro de conexão com o servidor" },
      { status: 502 }
    );
  }
}
