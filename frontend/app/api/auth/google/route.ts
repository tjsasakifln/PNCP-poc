import { NextRequest, NextResponse } from "next/server";
import { getRefreshedToken } from "../../../../lib/serverAuth";

export const dynamic = "force-dynamic";

/**
 * STORY-361 AC1: Proxy GET /api/auth/google → backend OAuth initiate.
 *
 * The backend endpoint requires auth (Bearer token) and returns a 302
 * redirect to Google's consent screen.  Because the browser navigates
 * here via window.location.href (no custom headers), we obtain the
 * auth token server-side via getRefreshedToken() and relay the
 * backend's redirect to the browser.
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

  const { searchParams } = new URL(request.url);
  const redirect = searchParams.get("redirect") || "/buscar";

  // Server-side token refresh — browser navigation has no auth header
  const token = await getRefreshedToken();
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", redirect);
    return NextResponse.redirect(loginUrl);
  }

  try {
    const backendOAuthUrl = `${backendUrl}/api/auth/google?redirect=${encodeURIComponent(redirect)}`;
    const response = await fetch(backendOAuthUrl, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      redirect: "manual", // Capture the 302 — don't follow it server-side
    });

    // Backend returns 302/307 to Google consent screen
    if (response.status >= 300 && response.status < 400) {
      const location = response.headers.get("location");
      if (location) {
        return NextResponse.redirect(location);
      }
    }

    // Non-redirect error from backend
    console.error(`Backend OAuth initiate returned ${response.status}`);
    return NextResponse.redirect(
      new URL(`${redirect}?error=oauth_init_failed`, request.url)
    );
  } catch (error) {
    console.error("OAuth proxy error:", error);
    return NextResponse.redirect(
      new URL(`${redirect}?error=oauth_network_error`, request.url)
    );
  }
}
