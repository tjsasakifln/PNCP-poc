import { NextRequest, NextResponse } from "next/server";

const POST_ENDPOINTS = ["tour-event"];

// STORY-313 AC18: POST handler for onboarding tour event tracking
export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !POST_ENDPOINTS.includes(endpoint)) {
    return NextResponse.json({ error: "Invalid endpoint" }, { status: 400 });
  }

  const authHeader = request.headers.get("authorization");
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return new NextResponse(null, { status: 204 });
  }

  try {
    const body = await request.json();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (authHeader) {
      headers["Authorization"] = authHeader;
    }

    await fetch(`${backendUrl}/v1/onboarding/${endpoint}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    return new NextResponse(null, { status: 204 });
  } catch {
    return new NextResponse(null, { status: 204 }); // Fire-and-forget
  }
}
