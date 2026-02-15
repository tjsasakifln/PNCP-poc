"use client";

import { supabase } from "./supabase";

/**
 * STORY-253 AC5: Fetch wrapper that automatically retries on 401
 * by refreshing the Supabase session and retrying with the new token.
 *
 * If the retry also returns 401, redirects to /login?reason=session_expired.
 */
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  // AC5: If 401, attempt one refresh + retry
  if (response.status === 401) {
    if (process.env.NODE_ENV === "development") {
      console.info("[fetchWithAuth] Got 401, attempting token refresh...");
    }

    const { data: { session: refreshedSession }, error } =
      await supabase.auth.refreshSession();

    if (error || !refreshedSession?.access_token) {
      // AC8: Refresh failed — redirect to login
      if (process.env.NODE_ENV === "development") {
        console.warn("[fetchWithAuth] Token refresh failed, redirecting to login");
      }
      const currentPath = typeof window !== "undefined" ? window.location.pathname : "/";
      window.location.href = `/login?reason=session_expired&redirect=${encodeURIComponent(currentPath)}`;
      // Return the original 401 response (redirect will take over)
      return response;
    }

    // Retry with the new token
    const retryHeaders = new Headers(options.headers);
    retryHeaders.set("Authorization", `Bearer ${refreshedSession.access_token}`);

    const retryResponse = await fetch(url, { ...options, headers: retryHeaders });

    // AC8: If retry also fails with 401, redirect to login
    if (retryResponse.status === 401) {
      if (process.env.NODE_ENV === "development") {
        console.warn("[fetchWithAuth] Retry also returned 401, redirecting to login");
      }
      const currentPath = typeof window !== "undefined" ? window.location.pathname : "/";
      window.location.href = `/login?reason=session_expired&redirect=${encodeURIComponent(currentPath)}`;
      return retryResponse;
    }

    return retryResponse;
  }

  return response;
}
