/**
 * CRIT-003 AC11: Proxy for search status polling endpoint.
 *
 * GET /api/search-status?search_id=xxx → backend GET /v1/search/{search_id}/status
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const searchId = request.nextUrl.searchParams.get("search_id");

  if (!searchId) {
    return NextResponse.json(
      { error: "search_id is required" },
      { status: 400 }
    );
  }

  const authHeader = request.headers.get("authorization");
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
    const res = await fetch(
      `${BACKEND_URL}/v1/search/${encodeURIComponent(searchId)}/status`,
      { headers, cache: "no-store" }
    );

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.error("Search status proxy error:", err);
    return NextResponse.json(
      { error: "Failed to fetch search status" },
      { status: 502 }
    );
  }
}
