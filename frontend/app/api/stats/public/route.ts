import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET() {
  try {
    const resp = await fetch(`${BACKEND_URL}/v1/stats/public`, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 21600 }, // 6h
    });

    if (!resp.ok) {
      return NextResponse.json(
        { message: await resp.text() },
        { status: resp.status }
      );
    }

    const data = await resp.json();
    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "public, s-maxage=21600, stale-while-revalidate=43200",
      },
    });
  } catch {
    return NextResponse.json({ message: "Erro de conexão" }, { status: 502 });
  }
}
