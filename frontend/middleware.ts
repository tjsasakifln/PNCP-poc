import { NextRequest, NextResponse } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

/**
 * Next.js Middleware for route protection.
 * Uses @supabase/ssr for proper cookie handling.
 *
 * Protected routes: / (main search page), /historico, /conta, /admin/*
 * Public routes: /login, /signup, /planos, /auth/callback
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

  // Create response (we may need to update cookies for session refresh)
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  });

  // Create Supabase client with cookie handling
  const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      get(name: string) {
        return request.cookies.get(name)?.value;
      },
      set(name: string, value: string, options: CookieOptions) {
        // Update cookies on response for session refresh
        response.cookies.set({
          name,
          value,
          ...options,
          path: "/",
          sameSite: "lax",
          secure: process.env.NODE_ENV === "production",
        });
      },
      remove(name: string, options: CookieOptions) {
        response.cookies.set({
          name,
          value: "",
          ...options,
          path: "/",
          maxAge: 0,
        });
      },
    },
  });

  try {
    // Get and verify the user session
    // This also refreshes the session if needed and updates cookies
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
