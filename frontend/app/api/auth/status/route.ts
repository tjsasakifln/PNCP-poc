/**
 * GTM-FIX-009: Proxy for GET /v1/auth/status?email=...
 * Checks if a signup email has been confirmed.
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const email = request.nextUrl.searchParams.get("email");
    if (!email) {
      return NextResponse.json(
        { confirmed: false, error: "Email required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${BACKEND_URL}/v1/auth/status?email=${encodeURIComponent(email)}`
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ confirmed: false }, { status: 500 });
  }
}
