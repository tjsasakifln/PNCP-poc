import { NextResponse } from "next/server";

/**
 * Environment Variables Debug Endpoint
 *
 * PURPOSE: Check OAuth-related environment variables in production
 *
 * SECURITY: Only enable in Railway with proper IP restrictions or auth token
 *
 * USAGE: GET https://your-app.railway.app/api/debug/env-check
 *
 * DELETE THIS FILE after debugging is complete!
 */

export async function GET(request: Request) {
  // SECURITY: Check for debug token (optional but recommended)
  const url = new URL(request.url);
  const debugToken = url.searchParams.get("token");

  // Uncomment and set a random token in Railway to secure this endpoint:
  // const EXPECTED_TOKEN = process.env.DEBUG_TOKEN;
  // if (!EXPECTED_TOKEN || debugToken !== EXPECTED_TOKEN) {
  //   return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  // }

  const envVars = {
    NEXT_PUBLIC_CANONICAL_URL: process.env.NEXT_PUBLIC_CANONICAL_URL || "NOT SET",
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || "NOT SET",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
      ? `${process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY.substring(0, 20)}...`
      : "NOT SET",
    BACKEND_URL: process.env.BACKEND_URL || "NOT SET",
  };

  // Calculate OAuth redirect URL
  const canonicalUrl = process.env.NEXT_PUBLIC_CANONICAL_URL;
  const redirectUrl = canonicalUrl
    ? `${canonicalUrl}/auth/callback`
    : "WILL USE window.location.origin (may be unstable)";

  // Check for issues
  const issues: string[] = [];

  if (!process.env.NEXT_PUBLIC_CANONICAL_URL) {
    issues.push(
      "CRITICAL: NEXT_PUBLIC_CANONICAL_URL not set - OAuth redirect URL will be dynamic and may fail"
    );
  }

  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    issues.push("ERROR: NEXT_PUBLIC_SUPABASE_URL not set - Supabase will not work");
  }

  if (!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    issues.push("ERROR: NEXT_PUBLIC_SUPABASE_ANON_KEY not set - Supabase will not work");
  }

  const status = issues.length === 0 ? "OK" : "ISSUES_DETECTED";

  return NextResponse.json({
    status,
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || "unknown",
    envVars,
    oauthRedirectUrl: redirectUrl,
    issues,
    recommendation:
      issues.length > 0
        ? "Set missing environment variables in Railway Dashboard → Variables tab"
        : "Configuration looks good! If OAuth still fails, check Google Cloud Console redirect URIs.",
    nextSteps:
      issues.length > 0
        ? [
            "1. Go to Railway Dashboard",
            "2. Select your service",
            "3. Go to Variables tab",
            "4. Add NEXT_PUBLIC_CANONICAL_URL = https://smartlic.tech",
            "5. Verify NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "6. Redeploy service",
            "7. Delete this debug endpoint after fixing",
          ]
        : [
            "1. Verify Google Cloud Console → OAuth 2.0 Client ID → Authorized redirect URIs",
            "2. Ensure it includes: " + redirectUrl,
            "3. Verify Supabase Dashboard → Authentication → URL Configuration",
            "4. Check browser console logs during OAuth attempt",
            "5. Delete this debug endpoint after fixing",
          ],
  });
}
