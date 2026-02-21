import { NextResponse } from "next/server";

/**
 * Liveness health check — always returns 200 if the frontend process is up.
 *
 * Backend connectivity is reported as informational metadata but does NOT
 * block the healthcheck. This prevents Railway deployment failures caused
 * by the backend starting slower than the frontend.
 *
 * CRIT-010 AC8: Checks backend `ready` field to distinguish "starting" from "healthy".
 */
export async function GET() {
  const backendUrl = process.env.BACKEND_URL;

  if (!backendUrl) {
    return NextResponse.json(
      { status: "healthy", backend: "not configured" },
      { status: 200 }
    );
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${backendUrl}/health`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.error(`Backend health check failed with status: ${response.status}`);
      return NextResponse.json(
        { status: "healthy", backend: "unhealthy" },
        { status: 200 }
      );
    }

    // CRIT-010 AC8: Parse ready field — backend may be up but not yet ready
    const body = await response.json();
    const backendStatus = body.ready === false ? "starting" : "healthy";

    return NextResponse.json(
      { status: "healthy", backend: backendStatus },
      { status: 200 }
    );
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "unknown error";
    console.error(`Backend health check error: ${errorMessage}`);

    return NextResponse.json(
      { status: "healthy", backend: "unreachable" },
      { status: 200 }
    );
  }
}
