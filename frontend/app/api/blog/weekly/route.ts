import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const year = searchParams.get("year");
  const week = searchParams.get("week");

  const endpoint =
    year && week
      ? `${BACKEND_URL}/v1/blog/weekly/${encodeURIComponent(year)}/${encodeURIComponent(week)}`
      : `${BACKEND_URL}/v1/blog/weekly/latest`;

  try {
    const resp = await fetch(endpoint, {
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 3600 },
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
        "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=7200",
      },
    });
  } catch {
    return NextResponse.json({ message: "Erro de conexão" }, { status: 502 });
  }
}
