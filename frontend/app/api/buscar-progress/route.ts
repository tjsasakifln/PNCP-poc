/**
 * SSE Proxy Route - /api/buscar-progress
 *
 * Proxies Server-Sent Events from the backend /buscar-progress/{search_id}
 * endpoint to the browser. This allows real-time progress updates during
 * PNCP search operations.
 */

import { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const searchId = request.nextUrl.searchParams.get("search_id");
  const token = request.nextUrl.searchParams.get("token");

  if (!searchId) {
    return new Response("search_id is required", { status: 400 });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return new Response("Server not configured", { status: 503 });
  }

  // CRIT-004 AC2: Forward Authorization + X-Correlation-ID
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    "Accept": "text/event-stream",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const backendResponse = await fetch(
      `${backendUrl}/v1/buscar-progress/${encodeURIComponent(searchId)}`,
      { headers }
    );

    if (!backendResponse.ok) {
      return new Response("Backend error", { status: backendResponse.status });
    }

    if (!backendResponse.body) {
      return new Response("No stream body", { status: 502 });
    }

    // Proxy the SSE stream directly to the browser
    return new Response(backendResponse.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
      },
    });
  } catch (error) {
    console.error("SSE proxy error:", error);
    return new Response("Failed to connect to backend", { status: 502 });
  }
}
