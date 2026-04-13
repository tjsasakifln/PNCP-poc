/**
 * UX-434 STUB: Placeholder until alerts feature is implemented (STORY-301).
 * Returns 200 with empty data to eliminate 404 console errors during navigation.
 * Real implementation will proxy to BACKEND_URL/v1/alerts.
 */
import { NextRequest, NextResponse } from "next/server";

function requireAuth(request: NextRequest): NextResponse | null {
  if (!request.headers.get("authorization")) {
    return NextResponse.json(
      { message: "Autenticação necessária" },
      { status: 401 },
    );
  }
  return null;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const authError = requireAuth(request);
  if (authError) return authError;
  return NextResponse.json([], { status: 200 });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  const authError = requireAuth(request);
  if (authError) return authError;
  return NextResponse.json(
    { id: null, message: "Funcionalidade em breve" },
    { status: 200 },
  );
}
