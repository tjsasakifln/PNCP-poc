import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !["summary", "searches-over-time", "top-dimensions"].includes(endpoint)) {
    return NextResponse.json({ error: "Invalid endpoint" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Build backend URL with query params (excluding 'endpoint')
  const backendParams = new URLSearchParams();
  searchParams.forEach((value, key) => {
    if (key !== "endpoint") backendParams.set(key, value);
  });

  const backendUrl = `${BACKEND_URL}/analytics/${endpoint}${backendParams.toString() ? `?${backendParams}` : ""}`;

  try {
    const res = await fetch(backendUrl, {
      headers: { Authorization: authHeader },
    });

    if (!res.ok) {
      const errorText = await res.text();
      return NextResponse.json(
        { error: errorText },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { error: "Falha ao conectar com o servidor" },
      { status: 502 }
    );
  }
}
