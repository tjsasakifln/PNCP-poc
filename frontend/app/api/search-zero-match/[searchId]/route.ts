import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * CRIT-059 AC4: Proxy for GET /v1/search/{search_id}/zero-match
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ searchId: string }> }
) {
  const { searchId } = await params;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const authHeader = request.headers.get("authorization");
  if (authHeader) {
    headers["Authorization"] = authHeader;
  }

  try {
    const response = await fetch(
      `${BACKEND_URL}/v1/search/${encodeURIComponent(searchId)}/zero-match`,
      { headers, cache: "no-store" }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "Zero-match results not available" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("[CRIT-059] Zero-match proxy error:", error);
    return NextResponse.json(
      { error: "Failed to fetch zero-match results" },
      { status: 502 }
    );
  }
}
