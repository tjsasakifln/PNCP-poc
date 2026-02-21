"use client";

import { useEffect, useState, useRef } from "react";
import { supabase } from "../../../lib/supabase";
import { useAnalytics } from "../../../hooks/useAnalytics";

/**
 * Client-side Auth Callback Handler
 *
 * Handles the PKCE flow callback where authorization code comes in URL params.
 * Uses window.location.href for redirect (not router.push) to ensure
 * auth cookies are sent on a full page load — avoids Next.js router cache
 * causing the middleware to miss the session on soft navigation.
 *
 * UX-336: Fallback chain ensures the loading spinner is shown throughout
 * the entire recovery process — never flashes an error screen when the
 * login can still be recovered via getUser() or onAuthStateChange.
 */
export default function AuthCallbackPage() {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { identifyUser } = useAnalytics();

  // Store identifyUser in a ref so useEffect can access it without re-running
  const identifyUserRef = useRef(identifyUser);
  identifyUserRef.current = identifyUser;

  // UX-336 AC3: Run callback exactly once on mount (no [status] dependency)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    const handleCallback = async () => {
      const startTime = Date.now();

      // UX-336 AC5: 15s timeout (was 30s — too long for UX)
      const callbackTimeout = setTimeout(() => {
        console.error("[OAuth Callback] TIMEOUT after 15 seconds");
        setStatus("error");
        setErrorMessage("Não foi possível completar o login. Tente novamente.");
      }, 15000);

      try {
        // Clear stale auth storage that might interfere
        // Source: https://github.com/orgs/supabase/discussions/20353
        try {
          const keysToRemove = [
            'supabase.auth.token',
            'sb-auth-token',
            'supabase.auth.expires_at',
          ];

          keysToRemove.forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
          });

          // Clear Supabase-specific keys (preserve code_verifier!)
          Object.keys(localStorage).forEach(key => {
            if (key.startsWith('sb-') && !key.includes('code_verifier')) {
              localStorage.removeItem(key);
            }
          });
        } catch (storageError) {
          console.warn("[OAuth Callback] Could not clear storage:", storageError);
        }

        // Check for error in URL params (explicit OAuth rejection)
        const params = new URLSearchParams(window.location.search);
        const error = params.get("error");
        const errorDescription = params.get("error_description");

        if (process.env.NODE_ENV === 'development') {
          console.log("[OAuth Callback] ===== STARTING OAUTH CALLBACK =====");
          console.log("[OAuth Callback] Full URL:", window.location.href);
          console.log("[OAuth Callback] Query params:", Object.fromEntries(params.entries()));
        }

        // Explicit OAuth error (user denied, invalid grant, etc.) — no fallback possible
        if (error) {
          console.error("[OAuth Callback] OAuth error:", error, errorDescription);
          clearTimeout(callbackTimeout);
          setStatus("error");
          setErrorMessage(humanizeAuthError(errorDescription || error));
          return;
        }

        // --- Phase 1: Try code exchange (PKCE flow) ---
        const code = params.get("code");
        let codeExchangeSucceeded = false;

        if (code) {
          console.log("[OAuth Callback] Authorization code found, exchanging...");

          let session = null;
          let exchangeError = null;
          let retries = 0;
          const maxRetries = 3;

          while (retries < maxRetries && !session && !exchangeError) {
            if (retries > 0) {
              const backoff = Math.pow(2, retries) * 1000;
              console.log(`[OAuth Callback] Retry ${retries}/${maxRetries} after ${backoff}ms...`);
              await new Promise(resolve => setTimeout(resolve, backoff));
            }

            const result = await supabase.auth.exchangeCodeForSession(code);
            session = result.data.session;
            exchangeError = result.error;
            retries++;
          }

          const duration = Date.now() - startTime;
          console.log("[OAuth Callback] Code exchange took:", duration, "ms", `(${retries} attempts)`);

          if (session) {
            console.log("[OAuth Callback] Session obtained via code exchange");
            if (process.env.NODE_ENV === 'development') {
              console.log("[OAuth Callback] User:", session.user.email);
            }

            await supabase.auth.setSession({
              access_token: session.access_token,
              refresh_token: session.refresh_token,
            });

            clearTimeout(callbackTimeout);
            setStatus("success");
            identifyUserRef.current(session.user.id, {
              plan_type: 'unknown',
              signup_method: 'google',
              signup_date: session.user.created_at,
            });
            window.location.href = "/buscar";
            return;
          }

          // UX-336 AC1: Code exchange failed — log warning and fall through to getUser()
          // Do NOT setStatus("error") here — keep showing the loading spinner
          if (exchangeError) {
            console.warn(
              "[OAuth Callback] Code exchange failed, trying fallback...",
              exchangeError.message
            );
          }
        } else {
          console.warn("[OAuth Callback] No authorization code in URL");
        }

        // --- Phase 2: Fallback via getUser() (uses HTTP cookies) ---
        console.log("[OAuth Callback] Attempting getUser() fallback...");
        const { data: { user }, error: userError } = await supabase.auth.getUser();

        if (user) {
          const duration = Date.now() - startTime;
          console.warn(
            `[OAuth Callback] Recovered via getUser() fallback (${duration}ms)`,
            "— code exchange had failed but cookies were valid"
          );
          clearTimeout(callbackTimeout);
          identifyUserRef.current(user.id, { signup_method: 'google' });
          setStatus("success");
          window.location.href = "/buscar";
          return;
        }

        if (userError) {
          console.warn("[OAuth Callback] getUser() failed:", userError.message);
        }

        // --- Phase 3: Last resort — listen for onAuthStateChange ---
        console.log("[OAuth Callback] Attempting onAuthStateChange fallback...");
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
          if (event === "SIGNED_IN" && session) {
            const duration = Date.now() - startTime;
            console.warn(
              `[OAuth Callback] Recovered via onAuthStateChange (${duration}ms)`
            );
            clearTimeout(callbackTimeout);
            identifyUserRef.current(session.user.id, {
              signup_method: 'google',
              signup_date: session.user.created_at,
            });
            setStatus("success");
            subscription.unsubscribe();
            window.location.href = "/buscar";
          }
        });

        // UX-336 AC5: 10s timeout for onAuthStateChange (was 5s)
        setTimeout(() => {
          subscription.unsubscribe();
          clearTimeout(callbackTimeout);
          const duration = Date.now() - startTime;
          console.error(
            `[OAuth Callback] All fallbacks exhausted after ${duration}ms`
          );
          setStatus("error");
          setErrorMessage("Não foi possível completar o login com Google. Isso pode acontecer por instabilidade temporária. Tente novamente.");
        }, 10000);

      } catch (err) {
        clearTimeout(callbackTimeout);
        console.error("[OAuth Callback] Unexpected error:", err);
        setStatus("error");
        setErrorMessage("Erro inesperado ao processar o login. Tente novamente.");
      }
    };

    handleCallback();
  }, []);

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
          <div className="text-red-500 text-5xl mb-4">&#10005;</div>
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
        <div className="text-green-500 text-5xl mb-4">&#10003;</div>
        <p className="text-ink/70">Autenticação bem-sucedida! Redirecionando...</p>
      </div>
    </div>
  );
}

/**
 * UX-336 AC4: Convert technical Supabase error messages into user-friendly Portuguese.
 * Technical details are logged to console, never shown to users.
 */
function humanizeAuthError(message: string): string {
  const lower = message.toLowerCase();

  if (lower.includes('pkce') || lower.includes('code_verifier') || lower.includes('code verifier')) {
    return "Não foi possível completar o login com Google. Isso pode acontecer por instabilidade temporária. Tente novamente.";
  }
  if (lower.includes('access_denied') || lower.includes('access denied')) {
    return "O acesso foi negado. Verifique se você autorizou o SmartLic na tela do Google.";
  }
  if (lower.includes('invalid_grant') || lower.includes('invalid grant')) {
    return "A sessão de login expirou. Tente novamente.";
  }
  if (lower.includes('timeout')) {
    return "O login demorou mais que o esperado. Tente novamente.";
  }

  // Generic fallback — still no technical jargon
  return "Não foi possível completar o login. Tente novamente.";
}
