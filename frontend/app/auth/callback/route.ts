import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * OAuth/Magic Link Callback Handler
 *
 * Handles callbacks from Supabase Auth:
 * - OAuth (Google): comes with ?code=xxx
 * - Magic Link: comes with ?token=xxx&type=magiclink
 *
 * IMPORTANT: Uses @supabase/ssr with getAll/setAll pattern for proper cookie handling.
 */
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const token = searchParams.get("token");
  const type = searchParams.get("type");
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  // Use public URL instead of request origin (which may be internal container address)
  const publicUrl = process.env.NEXT_PUBLIC_SITE_URL
    || (process.env.RAILWAY_PUBLIC_DOMAIN
      ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}`
      : "https://bidiq-frontend-production.up.railway.app");
  const origin = publicUrl;

  // Handle OAuth errors from URL params
  if (error) {
    console.error("Auth error:", error, errorDescription);
    const loginUrl = new URL("/login", origin);
    loginUrl.searchParams.set("error", error);
    if (errorDescription) {
      loginUrl.searchParams.set("error_description", errorDescription);
    }
    return NextResponse.redirect(loginUrl);
  }

  // No auth params - redirect to login
  if (!code && !token) {
    return NextResponse.redirect(new URL("/login", origin));
  }

  // Create response that we'll add cookies to
  let response = NextResponse.redirect(new URL("/", origin));

  // Create Supabase client with getAll/setAll cookie pattern (recommended)
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
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
    }
  );

  try {
    let authError = null;

    if (token && type === "magiclink") {
      // Magic Link flow: verify the OTP token directly
      const { error } = await supabase.auth.verifyOtp({
        token_hash: token,
        type: "magiclink",
      });
      authError = error;
    } else if (code) {
      // OAuth flow: exchange code for session
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      authError = error;
    }

    if (authError) {
      console.error("Auth verification error:", authError);
      const loginUrl = new URL("/login", origin);
      loginUrl.searchParams.set("error", "auth_failed");
      loginUrl.searchParams.set("error_description", authError.message);
      return NextResponse.redirect(loginUrl);
    }

    // Success! The cookies are already set on the response
    response.cookies.set({
      name: "auth_callback_success",
      value: "true",
      path: "/",
      maxAge: 10, // Short-lived flag
    });

    return response;

  } catch (err) {
    console.error("Unexpected error in auth callback:", err);
    const loginUrl = new URL("/login", origin);
    loginUrl.searchParams.set("error", "unexpected_error");
    return NextResponse.redirect(loginUrl);
  }
}
