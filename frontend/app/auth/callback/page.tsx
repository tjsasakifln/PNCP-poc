"use client";

import { useEffect, useState } from "react";
import { supabase } from "../../../lib/supabase";

/**
 * Client-side Auth Callback Handler
 *
 * Handles the PKCE flow callback where authorization code comes in URL params.
 * Uses window.location.href for redirect (not router.push) to ensure
 * auth cookies are sent on a full page load — avoids Next.js router cache
 * causing the middleware to miss the session on soft navigation.
 */
export default function AuthCallbackPage() {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // CRITICAL: Add timeout at the start to prevent infinite loading
      // Community recommends 30s+ for slow networks (auth code valid for 5 minutes)
      const callbackTimeout = setTimeout(() => {
        console.error("[OAuth Callback] TIMEOUT after 30 seconds - forcing error state");
        setStatus("error");
        setErrorMessage("Timeout ao processar login com Google. Use email/senha ou tente novamente.");
      }, 30000); // 30 second timeout (was 15s)

      try {
        // COMMUNITY FIX: Clear any stale auth storage that might interfere
        // Source: https://github.com/orgs/supabase/discussions/20353
        try {
          console.log("[OAuth Callback] Clearing stale auth storage...");
          const keysToRemove = [
            'supabase.auth.token',
            'sb-auth-token',
            'supabase.auth.expires_at',
          ];

          // Clear from both localStorage and sessionStorage
          keysToRemove.forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
          });

          // Clear any Supabase-specific keys
          Object.keys(localStorage).forEach(key => {
            if (key.startsWith('sb-') && !key.includes('code_verifier')) {
              console.log("[OAuth Callback] Removing stale key:", key);
              localStorage.removeItem(key);
            }
          });

          console.log("[OAuth Callback] ✅ Stale storage cleared");
        } catch (storageError) {
          console.warn("[OAuth Callback] Could not clear storage:", storageError);
        }

        // Check for error in URL params
        const params = new URLSearchParams(window.location.search);
        const error = params.get("error");
        const errorDescription = params.get("error_description");

        // DEBUG: Log troubleshooting info (STORY-211 AC15: dev only to prevent PII leaks)
        if (process.env.NODE_ENV === 'development') {
          console.log("[OAuth Callback] ===== STARTING OAUTH CALLBACK =====");
          console.log("[OAuth Callback] Full URL:", window.location.href);
          console.log("[OAuth Callback] Query params:", Object.fromEntries(params.entries()));
        }

        if (error) {
          console.error("[OAuth Callback] OAuth error parameter found:", error, errorDescription);
          clearTimeout(callbackTimeout);
          setStatus("error");
          setErrorMessage(errorDescription || error);
          return;
        }

        // Check for authorization code (PKCE flow from OAuth providers like Google)
        const code = params.get("code");

        if (code) {
          console.log("[OAuth Callback] Authorization code found, length:", code.length);
          console.log("[OAuth Callback] Exchanging code for session...");

          // COMMUNITY FIX: Retry logic with exponential backoff for slow networks
          // Source: https://github.com/supabase/auth-js/issues/782
          let session = null;
          let exchangeError = null;
          let retries = 0;
          const maxRetries = 3;

          const startTime = Date.now();

          while (retries < maxRetries && !session && !exchangeError) {
            if (retries > 0) {
              const backoff = Math.pow(2, retries) * 1000; // 2s, 4s, 8s
              console.log(`[OAuth Callback] Retry ${retries}/${maxRetries} after ${backoff}ms...`);
              await new Promise(resolve => setTimeout(resolve, backoff));
            }

            const result = await supabase.auth.exchangeCodeForSession(code);
            session = result.data.session;
            exchangeError = result.error;

            if (!exchangeError && !session) {
              console.warn(`[OAuth Callback] No session and no error on attempt ${retries + 1}`);
            }

            retries++;
          }

          const duration = Date.now() - startTime;
          console.log("[OAuth Callback] Code exchange took:", duration, "ms", `(${retries} attempts)`);
          clearTimeout(callbackTimeout);

          if (exchangeError) {
            console.error("[OAuth Callback] Code exchange FAILED:", exchangeError);
            console.error("[OAuth Callback] Error details:", JSON.stringify(exchangeError));
            setStatus("error");
            setErrorMessage(exchangeError.message);
            return;
          }

          if (session) {
            console.log("[OAuth Callback] ✅ Session obtained successfully!");
            // STORY-211 AC15: Gate sensitive session details behind dev check
            if (process.env.NODE_ENV === 'development') {
              console.log("[OAuth Callback] User:", session.user.email);
              console.log("[OAuth Callback] Access Token (first 20 chars):", session.access_token.substring(0, 20) + "...");
              console.log("[OAuth Callback] Refresh Token exists:", !!session.refresh_token);
              console.log("[OAuth Callback] Expires at:", new Date(session.expires_at! * 1000).toISOString());
            }

            // COMMUNITY FIX: Force set session in supabase client to ensure it's available
            // Source: https://github.com/supabase/auth-js/issues/762
            await supabase.auth.setSession({
              access_token: session.access_token,
              refresh_token: session.refresh_token,
            });

            console.log("[OAuth Callback] Session manually set in Supabase client");

            // Verify session was set correctly
            const { data: { session: verifiedSession } } = await supabase.auth.getSession();
            if (verifiedSession) {
              console.log("[OAuth Callback] ✅ Session verification passed!");
            } else {
              console.error("[OAuth Callback] ❌ Session verification failed!");
            }

            setStatus("success");
            // Full page navigation ensures cookies are sent to middleware
            console.log("[OAuth Callback] Redirecting to /buscar");
            window.location.href = "/buscar";
            return;
          } else {
            console.warn("[OAuth Callback] ⚠️  No session returned after code exchange");
          }
        } else {
          console.warn("[OAuth Callback] ⚠️  No authorization code found in URL");
        }

        clearTimeout(callbackTimeout);

        // Fallback: Check if we have a validated user (SECURITY FIX)
        // Use getUser() instead of getSession() for secure validation
        const { data: { user }, error: userError } = await supabase.auth.getUser();

        if (userError) {
          console.error("[OAuth Callback] User validation error:", userError);
          setStatus("error");
          setErrorMessage(userError.message);
          return;
        }

        if (user) {
          setStatus("success");
          window.location.href = "/buscar";
        } else {
          // No session yet - listen for auth state change
          const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === "SIGNED_IN" && session) {
              setStatus("success");
              subscription.unsubscribe();
              window.location.href = "/buscar";
            }
          });

          // Timeout after 5 seconds
          setTimeout(() => {
            subscription.unsubscribe();
            if (status === "loading") {
              setStatus("error");
              setErrorMessage("Timeout ao processar autenticação. Tente novamente.");
            }
          }, 5000);
        }
      } catch (err) {
        console.error("[OAuth Callback] Unexpected error:", err);
        setStatus("error");
        setErrorMessage("Erro inesperado. Tente novamente.");
      }
    };

    handleCallback();
  }, [status]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue mx-auto mb-4"></div>
          <p className="text-ink/70">Processando autenticação...</p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-canvas">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-red-500 text-5xl mb-4">✕</div>
          <h1 className="text-xl font-semibold text-ink mb-2">Falha na autenticação</h1>
          <p className="text-ink/70 mb-6">{errorMessage || "Erro desconhecido"}</p>
          <a
            href="/login"
            className="inline-block bg-brand-blue text-white px-6 py-3 rounded-button font-semibold hover:bg-brand-blue/90 transition-colors"
          >
            Tentar novamente
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-canvas">
      <div className="text-center">
        <div className="text-green-500 text-5xl mb-4">✓</div>
        <p className="text-ink/70">Autenticação bem-sucedida! Redirecionando...</p>
      </div>
    </div>
  );
}
