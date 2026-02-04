import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@supabase/ssr";

/**
 * OAuth Callback Handler
 *
 * This route handles the OAuth callback from Supabase (Google, Magic Link, etc).
 * It exchanges the authorization code for a session and sets the session cookies.
 *
 * IMPORTANT: Uses @supabase/ssr with getAll/setAll pattern for proper cookie handling.
 * This is compatible with createBrowserClient on the client side.
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
    // Exchange the code for a session - this will set cookies via setAll
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
