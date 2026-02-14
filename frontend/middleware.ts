import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * Next.js Middleware for route protection.
 * Uses @supabase/ssr with getAll/setAll pattern for proper cookie handling.
 *
 * Protected routes: / (main search page), /historico, /conta, /admin/*
 * Public routes: /login, /signup, /planos, /auth/callback
 *
 * IMPORTANT: This middleware uses the recommended getAll/setAll cookie pattern
 * which is compatible with createBrowserClient on the client side.
 */

const PROTECTED_ROUTES = [
  "/buscar",     // Main search page requires auth
  "/historico",  // Search history
  "/conta",      // Account settings
  "/admin",      // Admin dashboard
  "/dashboard",  // Personal analytics dashboard
  "/mensagens",  // Message center
  "/planos/obrigado", // Post-purchase thank you page
];

const PUBLIC_ROUTES = [
  "/login",
  "/signup",
  "/planos",
  "/auth/callback",
];

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const host = request.headers.get("host") || "";

  // Allow API routes first (includes /api/health for Railway healthcheck)
  if (pathname.startsWith("/api/")) {
    return NextResponse.next();
  }

  // CRITICAL: Force canonical domain redirect (railway.app → smartlic.tech)
  // Must run BEFORE public route check so OAuth callbacks also get redirected
  const canonicalDomain = process.env.NEXT_PUBLIC_CANONICAL_URL?.replace(/^https?:\/\//, "") || "smartlic.tech";
  const isRailwayDomain = host.includes("railway.app");
  const isLocalhost = host.includes("localhost");

  if (isRailwayDomain && !isLocalhost) {
    const canonicalUrl = `https://${canonicalDomain}${pathname}${search}`;
    return NextResponse.redirect(canonicalUrl, { status: 301 });
  }

  // Allow public routes without auth check
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
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

  // Get Supabase config
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Supabase environment variables not configured");
    return NextResponse.next();
  }

  // Create response - cookies will be set on this
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  // Create Supabase client with getAll/setAll cookie pattern (recommended)
  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        // Set cookies on both request (for subsequent middleware) and response
        cookiesToSet.forEach(({ name, value, options }) => {
          request.cookies.set(name, value);
        });
        // Recreate response with updated request
        response = NextResponse.next({
          request: {
            headers: request.headers,
          },
        });
        // Set cookies on response
        cookiesToSet.forEach(({ name, value, options }) => {
          response.cookies.set(name, value, {
            ...options,
            // Ensure proper cookie settings for auth
            path: options?.path || "/",
            sameSite: options?.sameSite || "lax",
            secure: process.env.NODE_ENV === "production",
          });
        });
      },
    },
  });

  try {
    // Get user - this validates the session with Supabase server (secure)
    // SECURITY FIX: Use getUser() instead of getSession() to ensure user is authentic
    // getUser() validates the session by contacting Supabase Auth server
    const { data: { user }, error } = await supabase.auth.getUser();

    if (error || !user) {
      // No valid session - redirect to login
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);

      // AC1/AC2: Distinguish "never logged in" vs "session expired"
      // Supabase stores auth in cookies with names starting with "sb-"
      const hasAuthCookies = request.cookies.getAll().some(
        (c) => c.name.startsWith("sb-") && c.name.includes("auth-token")
      );

      if (hasAuthCookies && error) {
        // Had auth cookies but getUser() failed → session expired
        loginUrl.searchParams.set("reason", "session_expired");
      } else if (!hasAuthCookies) {
        // No auth cookies at all → never logged in
        loginUrl.searchParams.set("reason", "login_required");
      }

      return NextResponse.redirect(loginUrl);
    }

    // User is now validated by Supabase server (secure)

    // Valid session - add user info to headers and allow access
    const requestHeaders = new Headers(request.headers);
    requestHeaders.set("x-user-id", user.id);
    requestHeaders.set("x-user-email", user.email || "");

    // Return response with any updated session cookies
    return NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    });

  } catch (error) {
    console.error("Middleware auth error:", error);
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
