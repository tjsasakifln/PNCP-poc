import { NextRequest, NextResponse } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

/**
 * OAuth Callback Handler
 *
 * This route handles the OAuth callback from Supabase (Google, Magic Link, etc).
 * It exchanges the authorization code for a session and sets the session cookies.
 *
 * IMPORTANT: Uses @supabase/ssr to properly set cookies in the response.
 * This fixes the race condition where the redirect happened before cookies were set.
 */
export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");

  // Handle OAuth errors
  if (error) {
    console.error("OAuth error:", error, errorDescription);
    const loginUrl = new URL("/login", origin);
    loginUrl.searchParams.set("error", error);
    if (errorDescription) {
      loginUrl.searchParams.set("error_description", errorDescription);
    }
    return NextResponse.redirect(loginUrl);
  }

  if (!code) {
    // No code provided - redirect to login
    return NextResponse.redirect(new URL("/login", origin));
  }

  // Create response that we'll add cookies to
  const response = NextResponse.redirect(new URL("/", origin));

  // Create Supabase client that can set cookies on the response
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: CookieOptions) {
          // Set cookie on both request (for any subsequent middleware) and response
          response.cookies.set({
            name,
            value,
            ...options,
            // Ensure cookies work across the domain
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
    }
  );

  try {
    // Exchange the code for a session - this will set cookies via our handler above
    const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

    if (exchangeError) {
      console.error("Error exchanging code for session:", exchangeError);
      const loginUrl = new URL("/login", origin);
      loginUrl.searchParams.set("error", "auth_failed");
      loginUrl.searchParams.set("error_description", exchangeError.message);
      return NextResponse.redirect(loginUrl);
    }

    // Success! The cookies are already set on the response
    // Add a flag so the client knows this is a fresh auth
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
