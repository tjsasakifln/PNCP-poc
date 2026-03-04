"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../app/components/AuthProvider";

interface PaymentRecoveryModalProps {
  daysRemaining: number;
  trialValue?: { total_opportunities: number; total_value: number } | null;
  onClose?: () => void;
}

const formatCurrency = (val: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(val);

export function PaymentRecoveryModal({ daysRemaining, trialValue, onClose }: PaymentRecoveryModalProps) {
  const router = useRouter();
  const { session } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleUpdatePayment = async () => {
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

  // Escape key → navigate to /planos
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        router.push("/planos");
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [router]);

  const hasData = trialValue && trialValue.total_opportunities > 0;

  return (
    <div
      className="fixed inset-0 z-[60] bg-gradient-to-br from-red-50 to-red-100 dark:from-red-950/50 dark:to-red-900/30 flex items-center justify-center p-4 overflow-y-auto"
      data-testid="payment-recovery-modal"
    >
      {/* Close → /planos */}
      <button
        onClick={() => router.push("/planos")}
        className="fixed top-4 right-4 z-[61] p-2 rounded-full bg-white/80 hover:bg-white text-red-600 hover:text-red-800 transition-colors shadow-sm"
        aria-label="Fechar"
      >
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <div className="max-w-lg w-full bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 md:p-12 border border-red-200 dark:border-red-800">
        {/* Urgency icon */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-2xl md:text-3xl font-bold text-center mb-4 text-red-800 dark:text-red-200">
          Regularize seu pagamento
        </h1>

        {/* Countdown */}
        <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-4 mb-6 text-center border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-600 dark:text-red-300 mb-1">Tempo restante</p>
          <p className="text-4xl font-bold text-red-700 dark:text-red-200">
            {daysRemaining} {daysRemaining === 1 ? "dia" : "dias"}
          </p>
        </div>

        {/* Value display */}
        {hasData && (
          <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-4 mb-6">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-2 text-center">
              Valor que voce ja analisou
            </p>
            <p className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">
              {formatCurrency(trialValue!.total_value)}
            </p>
            <p className="text-sm text-center text-gray-500 dark:text-gray-400 mt-1">
              {trialValue!.total_opportunities} oportunidades encontradas
            </p>
          </div>
        )}

        {/* Message */}
        <p className="text-gray-600 dark:text-gray-300 text-center mb-6">
          Novas análises estao suspensas ate a regularizacao do pagamento.
          Seu historico e pipeline continuam acessiveis.
        </p>

        {/* CTA */}
        <button
          onClick={handleUpdatePayment}
          disabled={loading}
          className="w-full px-6 py-4 rounded-xl font-semibold text-lg bg-red-600 text-white hover:bg-red-700 hover:-translate-y-0.5 hover:shadow-xl transition-all disabled:opacity-50"
        >
          {loading ? "Abrindo portal de pagamento..." : "Atualizar Pagamento Agora"}
        </button>

        {/* Footer */}
        <p className="text-xs text-gray-400 dark:text-gray-500 text-center mt-4">
          Apos o pagamento, o acesso e restaurado imediatamente.
        </p>
      </div>
    </div>
  );
}
