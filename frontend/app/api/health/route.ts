import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.BACKEND_URL;

  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { status: "degraded", details: { backend: "not configured" } },
      { status: 503 }
    );
  }

  try {
    // Check backend connectivity with 5-second timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${backendUrl}/health`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.error(`Backend health check failed with status: ${response.status}`);
      return NextResponse.json(
        { status: "degraded", details: { backend: "unhealthy" } },
        { status: 503 }
      );
    }

    return NextResponse.json({ status: "healthy" }, { status: 200 });
  } catch (error) {
    // Handle network errors, timeouts, etc.
    const errorMessage = error instanceof Error ? error.message : "unknown error";
    console.error(`Backend health check error: ${errorMessage}`);

    return NextResponse.json(
      { status: "degraded", details: { backend: "unreachable" } },
      { status: 503 }
    );
  }
}
