/**
 * UX-434 STUB: Placeholder until profile completeness is implemented (STORY-260).
 * Returns 200 with default empty data to eliminate 404 console errors on Dashboard.
 * Real implementation will proxy to BACKEND_URL/v1/profile/completeness.
 */
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest): Promise<NextResponse> {
  if (!request.headers.get("authorization")) {
    return NextResponse.json(
      { message: "Autenticação necessária" },
      { status: 401 },
    );
  }
  return NextResponse.json(
    {
      completeness_pct: null,
      is_complete: false,
      filled_fields: 0,
      total_fields: 0,
      missing_fields: [],
    },
    { status: 200 },
  );
}
