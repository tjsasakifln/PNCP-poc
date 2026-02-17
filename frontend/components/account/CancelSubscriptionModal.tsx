"use client";

import { useState } from "react";
import { toast } from "sonner";

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCancelled: (endsAt: string) => void;
  accessToken: string;
}

export function CancelSubscriptionModal({
  isOpen,
  onClose,
  onCancelled,
  accessToken,
}: CancelSubscriptionModalProps) {
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleCancel = async () => {
    setCancelling(true);
    setError(null);
    try {
      const res = await fetch("/api/subscriptions/cancel", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.message || "Erro ao cancelar");
      }

      const data = await res.json();
      toast.success("Cancelamento confirmado. Acesso mantido até o fim do período.");
      onCancelled(data.ends_at);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cancelar");
    } finally {
      setCancelling(false);
    }
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        role="alertdialog"
        aria-labelledby="cancel-title"
        aria-describedby="cancel-desc"
        className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-6 max-w-md w-full shadow-xl"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-[var(--warning-subtle,#fef3cd)] flex items-center justify-center flex-shrink-0">
            <svg
              role="img"
              aria-label="Atenção"
              className="w-5 h-5 text-[var(--warning,#856404)]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h3 id="cancel-title" className="text-lg font-semibold text-[var(--ink)]">
            Tem certeza que deseja cancelar?
          </h3>
        </div>

        <p id="cancel-desc" className="text-sm text-[var(--ink-secondary)] mb-4">
          Você perderá acesso aos seguintes benefícios ao final do período:
        </p>

        <ul className="text-sm text-[var(--ink-secondary)] mb-6 space-y-2">
          <li className="flex items-center gap-2">
            <svg aria-hidden="true" className="w-4 h-4 text-[var(--error,#dc2626)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            1000 análises mensais
          </li>
          <li className="flex items-center gap-2">
            <svg aria-hidden="true" className="w-4 h-4 text-[var(--error,#dc2626)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Histórico de 5 anos (1825 dias)
          </li>
          <li className="flex items-center gap-2">
            <svg aria-hidden="true" className="w-4 h-4 text-[var(--error,#dc2626)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Exportação Excel com análise IA
          </li>
          <li className="flex items-center gap-2">
            <svg aria-hidden="true" className="w-4 h-4 text-[var(--error,#dc2626)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Filtros avançados por setor
          </li>
        </ul>

        {error && (
          <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-3">
          <a
            href="mailto:suporte@smartlic.tech"
            className="w-full py-3 px-4 rounded-button border border-[var(--brand-blue)]
                       text-[var(--brand-blue)] bg-transparent
                       hover:bg-[var(--brand-blue-subtle)] transition-colors
                       flex items-center justify-center gap-2 text-sm font-medium"
          >
            <svg aria-hidden="true" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            Falar com Suporte
          </a>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={cancelling}
              className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                         text-[var(--ink)] bg-[var(--surface-0)]
                         hover:bg-[var(--surface-1)] transition-colors text-sm"
            >
              Manter acesso
            </button>
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="flex-1 px-4 py-2.5 rounded-button bg-[var(--error,#dc2626)] text-white
                         hover:opacity-90 transition-opacity text-sm
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelling ? "Cancelando..." : "Confirmar cancelamento"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
