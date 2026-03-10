import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * Next.js Middleware for route protection + security headers.
 * Uses @supabase/ssr with getAll/setAll pattern for proper cookie handling.
 *
 * STORY-300: Initial security headers setup.
 * STORY-311: Security hardening — CSP enforcement, report-uri, COOP, HSTS preload.
 *
 * Protected routes: /buscar, /historico, /conta, /admin/*, /dashboard, /mensagens
 * Public routes: /login, /signup, /planos, /auth/callback
 */

/**
 * STORY-311: Security headers hardening.
 *
 * AC1: CSP promoted from Report-Only to enforcing Content-Security-Policy.
 * AC2: report-uri + report-to directives for violation collection.
 * AC4: Whitelisted domains: Stripe, Sentry, Supabase, Mixpanel, Cloudflare.
 * AC5: Headers unified here (removed from next.config.js).
 * AC6: Cross-Origin-Opener-Policy: same-origin.
 * AC7: COEP skipped — require-corp breaks Stripe checkout iframe (no CORP headers).
 * AC8: X-DNS-Prefetch-Control: off.
 *
 * DEBT-108: CSP nonce-based script-src (removes 'unsafe-inline' / 'unsafe-eval').
 * A per-request nonce is generated here, set on x-nonce response header, and
 * read by app/layout.tsx to hydrate Script / inline-script nonce attributes.
 * 'strict-dynamic' lets nonced scripts load their own child scripts automatically.
 *
 * DEBT-108 AC6: To rollback CSP nonce, replace the script-src line below with:
 * "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com https://cdn.sentry.io https://www.clarity.ms https://www.googletagmanager.com",
 * and remove the nonce generation + x-nonce header lines.
 */
function addSecurityHeaders(response: NextResponse): NextResponse {
  // DEBT-108: Generate a cryptographically random nonce per request
  const nonce = Buffer.from(crypto.randomUUID()).toString("base64");

  // AC1+AC4: Content Security Policy — enforcing mode with nonce-based script-src
  const csp = [
    "default-src 'self'",
    // DEBT-108: nonce + strict-dynamic replaces unsafe-inline/unsafe-eval.
    // 'strict-dynamic' propagates trust to scripts loaded by nonced scripts.
    // Fallback hosts kept for browsers that do not support strict-dynamic/nonces.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://js.stripe.com https://static.cloudflareinsights.com https://cdn.sentry.io https://www.clarity.ms https://www.googletagmanager.com`,
    // DEBT-116: style-src unsafe-inline is an accepted risk.
    // Tailwind CSS and Next.js inject inline styles at runtime (className -> style).
    // Nonce-based styles would require a custom PostCSS plugin + Next.js config changes
    // with marginal security benefit (inline styles are low-risk vs inline scripts).
    // Revisit if Next.js adds native CSP nonce support for styles.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https: blob:",
    "font-src 'self' data:",
    "connect-src 'self' https://*.supabase.co https://*.supabase.in https://api.stripe.com https://*.railway.app https://*.ingest.sentry.io https://*.sentry.io https://*.smartlic.tech https://api-js.mixpanel.com https://api.mixpanel.com wss://*.supabase.co https://*.clarity.ms",
    "frame-src 'self' https://js.stripe.com",
    "object-src 'none'",
    "base-uri 'self'",
    "report-uri /api/csp-report",
    "report-to csp-endpoint",
  ].join("; ");

  // AC1: Enforcing CSP (promoted from Report-Only in STORY-300)
  response.headers.set("Content-Security-Policy", csp);

  // DEBT-108: Expose nonce to layout.tsx via response header
  response.headers.set("x-nonce", nonce);

  // AC2: Reporting API v1 — report-to group definition
  response.headers.set(
    "Report-To",
    JSON.stringify({
      group: "csp-endpoint",
      max_age: 86400,
      endpoints: [{ url: "/api/csp-report" }],
    })
  );

  // Prevent MIME type sniffing
  response.headers.set("X-Content-Type-Options", "nosniff");

  // Prevent clickjacking
  response.headers.set("X-Frame-Options", "DENY");

  // Legacy XSS protection
  response.headers.set("X-XSS-Protection", "1; mode=block");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");

  // AC16: HSTS with preload directive for hstspreload.org eligibility
  response.headers.set(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains; preload"
  );

  // AC6: Prevent window.opener attacks (Spectre-like)
  response.headers.set("Cross-Origin-Opener-Policy", "same-origin");

  // AC8: Prevent DNS prefetch leaking visited links
  response.headers.set("X-DNS-Prefetch-Control", "off");

  return response;
}

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
    return addSecurityHeaders(NextResponse.next());
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
    return addSecurityHeaders(NextResponse.next());
  }

  // Allow static assets and Next.js internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return addSecurityHeaders(NextResponse.next());
  }

  // Check if route requires protection
  const isProtectedRoute = PROTECTED_ROUTES.some(route =>
    pathname === route || pathname.startsWith(`${route}/`)
  );

  if (!isProtectedRoute) {
    return addSecurityHeaders(NextResponse.next());
  }

  // Get Supabase config
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Supabase environment variables not configured");
    return addSecurityHeaders(NextResponse.next());
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

    // Return response with any updated session cookies + security headers
    return addSecurityHeaders(NextResponse.next({
      request: {
        headers: requestHeaders,
      },
    }));

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
