import { NextResponse } from "next/server";

/**
 * STORY-316 AC3: Public status API proxy.
 * Proxies /api/status → backend /status (public, no auth).
 */
export async function GET(request: Request) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json(
      { status: "unknown", error: "Backend not configured" },
      { status: 200 }
    );
  }

  const url = new URL(request.url);
  const path = url.searchParams.get("path") || "";

  // Allow sub-paths: /api/status?path=incidents, /api/status?path=uptime-history
  const endpoint = path ? `${backendUrl}/status/${path}` : `${backendUrl}/status`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(endpoint, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      return NextResponse.json(
        { status: "unknown", error: `Backend returned ${response.status}` },
        { status: 200 }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, {
      status: 200,
      headers: { "Cache-Control": "public, max-age=30, s-maxage=30" },
    });
  } catch {
    return NextResponse.json(
      { status: "unknown", error: "Backend unreachable" },
      { status: 200 }
    );
  }
}
