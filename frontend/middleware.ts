import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * Next.js Middleware for route protection.
 * Validates Supabase session before allowing access to protected routes.
 *
 * Protected routes: /buscar (main search page), /historico, /conta, /admin/*
 * Public routes: /login, /signup, /planos, /auth/callback
 */

const PROTECTED_ROUTES = [
  "/",           // Main search page requires auth
  "/historico",  // Search history
  "/conta",      // Account settings
  "/admin",      // Admin dashboard (also requires admin role, checked in component)
];

const PUBLIC_ROUTES = [
  "/login",
  "/signup",
  "/planos",
  "/auth/callback",
];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes without auth check
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Allow API routes to handle their own auth (they check Authorization header)
  if (pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // Allow static assets and Next.js internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check if route requires protection
  const isProtectedRoute = PROTECTED_ROUTES.some(route =>
    pathname === route || pathname.startsWith(`${route}/`)
  );

  if (!isProtectedRoute) {
    return NextResponse.next();
  }

  // Get Supabase auth token from cookies
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Supabase environment variables not configured");
    // Allow access in misconfigured state (fail open for development)
    return NextResponse.next();
  }

  // Look for Supabase session in cookies
  // Supabase stores the session in cookies with format: sb-{project-ref}-auth-token
  const cookies = request.cookies;
  const projectRef = supabaseUrl.replace("https://", "").split(".")[0];
  const authCookieName = `sb-${projectRef}-auth-token`;
  const authCookie = cookies.get(authCookieName);

  // Also check for access_token in various cookie formats Supabase might use
  const accessTokenCookie = cookies.get("sb-access-token") ||
                           cookies.get(`sb-${projectRef}-auth-token.0`) ||
                           authCookie;

  if (!accessTokenCookie?.value) {
    // No session cookie found - redirect to login
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  try {
    // Parse the session from cookie (it's JSON with access_token and refresh_token)
    let sessionData;
    try {
      sessionData = JSON.parse(accessTokenCookie.value);
    } catch {
      // Cookie might be just the token string in some formats
      sessionData = { access_token: accessTokenCookie.value };
    }

    const accessToken = sessionData.access_token || accessTokenCookie.value;

    if (!accessToken) {
      throw new Error("No access token in session");
    }

    // Verify the token by calling Supabase
    const supabase = createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    });

    const { data: { user }, error } = await supabase.auth.getUser(accessToken);

    if (error || !user) {
      // Invalid or expired token - redirect to login
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      loginUrl.searchParams.set("reason", "session_expired");

      // Clear the invalid cookie
      const response = NextResponse.redirect(loginUrl);
      response.cookies.delete(authCookieName);
      return response;
    }

    // Valid session - allow access
    // Add user info to headers for downstream use if needed
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-user-id", user.id);
    requestHeaders.set("x-user-email", user.email || "");

    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });

  } catch (error) {
    console.error("Middleware auth error:", error);
    // On any error, redirect to login
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
