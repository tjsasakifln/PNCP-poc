"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../../../lib/supabase";

/**
 * Client-side Auth Callback Handler
 *
 * Handles the implicit flow callback where tokens come in the URL hash fragment.
 * This is necessary because hash fragments are not sent to the server.
 */
export default function AuthCallbackPage() {
  const router = useRouter();
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
          setStatus("error");
          setErrorMessage(errorDescription || error);
          return;
        }

        // Check for authorization code (PKCE flow from OAuth providers like Google)
        const code = params.get("code");

        if (code) {
          // Exchange authorization code for session (PKCE flow)
          // Supabase SDK automatically handles code exchange with PKCE verifier
          const { data: { session }, error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);

          if (exchangeError) {
            console.error("Code exchange error:", exchangeError);
            setStatus("error");
            setErrorMessage(exchangeError.message);
            return;
          }

          if (session) {
            setStatus("success");
            // Small delay to ensure cookies are set
            setTimeout(() => {
              router.push("/buscar");
            }, 500);
            return;
          }
        }

        // Fallback: Check if we already have a session (e.g., from hash fragment or cookies)
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          console.error("Session error:", sessionError);
          setStatus("error");
          setErrorMessage(sessionError.message);
          return;
        }

        if (session) {
          setStatus("success");
          // Small delay to ensure cookies are set
          setTimeout(() => {
            router.push("/buscar");
          }, 500);
        } else {
          // No session yet - listen for auth state change
          const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === "SIGNED_IN" && session) {
              setStatus("success");
              subscription.unsubscribe();
              router.push("/buscar");
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
        console.error("Callback error:", err);
        setStatus("error");
        setErrorMessage("Erro inesperado. Tente novamente.");
      }
    };

    handleCallback();
  }, [router, status]);

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
