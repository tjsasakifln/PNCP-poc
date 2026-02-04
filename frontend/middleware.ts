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
  "/",           // Main search page requires auth
  "/historico",  // Search history
  "/conta",      // Account settings
  "/admin",      // Admin dashboard
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

  // Allow API routes to handle their own auth
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
    // Get and verify the user session
    // This also refreshes the session if needed and updates cookies via setAll
    const { data: { user }, error } = await supabase.auth.getUser();

    if (error || !user) {
      // No valid session - redirect to login
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);

      if (error) {
        loginUrl.searchParams.set("reason", "session_expired");
      }

      return NextResponse.redirect(loginUrl);
    }

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
