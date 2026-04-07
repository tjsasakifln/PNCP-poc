import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json({ experiments: {} });
  }

  try {
    const res = await fetch(`${backendUrl}/feature-flags/experiments`, {
      headers: { Authorization: authHeader },
    });
    if (!res.ok) {
      return NextResponse.json({ experiments: {} });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ experiments: {} });
  }
}
