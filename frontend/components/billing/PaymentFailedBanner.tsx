"use client";

import { usePlan } from "../../hooks/usePlan";
import { useAuth } from "../../app/components/AuthProvider";
import { useState } from "react";

/**
 * GTM-FIX-007 AC7-AC10: Payment failed banner
 * Shown when subscription_status === 'past_due' (Stripe payment failure).
 * Persistent, non-dismissable, shown on ALL pages via layout.tsx.
 */
export function PaymentFailedBanner() {
  const { planInfo } = usePlan();
  const { session } = useAuth();
  const [loading, setLoading] = useState(false);

  // AC7: Only show when subscription_status is past_due
  if (!planInfo || planInfo.subscription_status !== "past_due") return null;

  const handleUpdateCard = async () => {
    if (!session?.access_token) return;
    setLoading(true);
    try {
      const response = await fetch("/api/billing-portal", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
      });
      if (response.ok) {
        const data = await response.json();
        window.open(data.url, "_blank");
      }
    } catch (error) {
      console.error("Failed to open billing portal:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="fixed top-0 left-0 right-0 z-[9999] bg-red-50 border-b-2 border-red-400 px-4 py-3 shadow-lg"
      data-testid="payment-failed-banner"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* Warning icon */}
          <svg
            className="w-5 h-5 text-red-600 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          {/* AC9: Banner text */}
          <p className="text-sm text-red-800 font-medium">
            Falha no pagamento da assinatura. Atualize seu cartão para continuar.
          </p>
        </div>
        {/* AC10: Update card button → Stripe billing portal */}
        <button
          onClick={handleUpdateCard}
          disabled={loading}
          className="inline-flex items-center px-4 py-1.5 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 transition-colors whitespace-nowrap disabled:opacity-50"
        >
          {loading ? "Abrindo..." : "Atualizar Cartão"}
        </button>
      </div>
    </div>
  );
}
