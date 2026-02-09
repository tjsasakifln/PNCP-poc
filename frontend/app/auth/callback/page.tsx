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
      try {
        // Check for error in URL params
        const params = new URLSearchParams(window.location.search);
        const error = params.get("error");
        const errorDescription = params.get("error_description");

        if (error) {
          console.error("[OAuth Callback] Error:", error, errorDescription);
          setStatus("error");
          setErrorMessage(errorDescription || error);
          return;
        }

        // Check for authorization code (PKCE flow from OAuth providers like Google)
        const code = params.get("code");

        if (code) {
          const { data: { session }, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

          if (exchangeError) {
            console.error("[OAuth Callback] Code exchange error:", exchangeError);
            setStatus("error");
            setErrorMessage(exchangeError.message);
            return;
          }

          if (session) {
            setStatus("success");
            // Full page navigation ensures cookies are sent to middleware
            window.location.href = "/buscar";
            return;
          }
        }

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
