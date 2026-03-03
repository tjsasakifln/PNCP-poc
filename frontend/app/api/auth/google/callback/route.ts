import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/**
 * STORY-361 AC2: Proxy GET /api/auth/google/callback → backend OAuth callback.
 *
 * Forwards code, state, and error query params to the backend.  The backend
 * verifies the CSRF nonce, exchanges the authorization code for tokens,
 * and returns a 302 redirect back to the frontend page.
 *
 * NOTE: In normal operation Google's redirect_uri points directly at the
 * backend, so this route acts as a safety net / fallback.
 */
export async function GET(request: NextRequest) {
  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    console.error("BACKEND_URL environment variable is not configured");
    return NextResponse.json(
      { message: "Servidor nao configurado. Contate o suporte." },
      { status: 503 }
    );
  }

  // Preserve all query params (code, state, error, etc.)
  const { searchParams } = new URL(request.url);
  const params = new URLSearchParams();
  searchParams.forEach((value, key) => {
    params.set(key, value);
  });

  try {
    const backendCallbackUrl = `${backendUrl}/api/auth/google/callback?${params.toString()}`;
    const response = await fetch(backendCallbackUrl, {
      method: "GET",
      redirect: "manual", // Capture the 302 — don't follow it server-side
    });

    // Backend returns 302 back to frontend page (e.g. /buscar?google_oauth=success)
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get("location");
      if (location) {
        return NextResponse.redirect(location);
      }
    }

    // Non-redirect response — something went wrong
    console.error(`Backend OAuth callback returned ${response.status}`);
    return NextResponse.redirect(
      new URL("/buscar?error=oauth_callback_failed", request.url)
    );
  } catch (error) {
    console.error("OAuth callback proxy error:", error);
    return NextResponse.redirect(
      new URL("/buscar?error=oauth_network_error", request.url)
    );
  }
}
