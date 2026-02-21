/**
 * API Proxy Route — GET /api/buscar-results/{searchId}
 *
 * GTM-RESILIENCE-A04 AC9: Proxies to backend GET /v1/buscar-results/{search_id}
 * to fetch live results from a completed background fetch (progressive delivery).
 */

import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ searchId: string }> },
) {
  const { searchId } = await params;

  if (!searchId) {
    return NextResponse.json(
      { error: "searchId is required" },
      { status: 400 },
    );
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return NextResponse.json(
      { error: "Server not configured" },
      { status: 503 },
    );
  }

  const authHeader = request.headers.get("Authorization");
  // CRIT-004 AC4: Forward X-Correlation-ID for end-to-end tracing
  const correlationId = request.headers.get("X-Correlation-ID");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }
  if (correlationId) {
    headers["X-Correlation-ID"] = correlationId;
  }

  try {
    const backendResponse = await fetch(
      `${backendUrl}/v1/buscar-results/${encodeURIComponent(searchId)}`,
      { headers },
    );

    if (!backendResponse.ok) {
      const errorBody = await backendResponse.text().catch(() => "");
      return NextResponse.json(
        { error: errorBody || "Backend error" },
        { status: backendResponse.status },
      );
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("[buscar-results proxy] Error:", error);
    return NextResponse.json(
      { error: "Failed to connect to backend" },
      { status: 502 },
    );
  }
}
