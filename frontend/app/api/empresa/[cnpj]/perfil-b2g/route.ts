import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ cnpj: string }> }
) {
  const { cnpj } = await params;

  if (!cnpj || cnpj.replace(/\D/g, "").length !== 14) {
    return NextResponse.json(
      { message: "CNPJ inválido" },
      { status: 400 }
    );
  }

  try {
    const resp = await fetch(
      `${BACKEND_URL}/v1/empresa/${encodeURIComponent(cnpj)}/perfil-b2g`,
      {
        headers: { "Content-Type": "application/json" },
        next: { revalidate: 86400 },
      }
    );

    if (!resp.ok) {
      const detail = await resp.text();
      return NextResponse.json(
        { message: detail || "Erro ao buscar perfil" },
        { status: resp.status }
      );
    }

    const data = await resp.json();
    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, s-maxage=86400, stale-while-revalidate=172800" },
    });
  } catch {
    return NextResponse.json(
      { message: "Erro de conexão com o servidor" },
      { status: 502 }
    );
  }
}
