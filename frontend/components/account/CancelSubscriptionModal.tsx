"use client";

import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import FocusTrap from "focus-trap-react";

type CancelReason =
  | "too_expensive"
  | "not_using"
  | "missing_features"
  | "found_alternative"
  | "other";

type Step = "reason" | "retention" | "confirm" | "feedback";

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCancelled: (endsAt: string) => void;
  accessToken: string;
}

const REASONS: { value: CancelReason; label: string }[] = [
  { value: "too_expensive", label: "Está caro para mim" },
  { value: "not_using", label: "Não estou usando o suficiente" },
  { value: "missing_features", label: "Falta funcionalidade que preciso" },
  { value: "found_alternative", label: "Encontrei outra solução" },
  { value: "other", label: "Outro motivo" },
];

const BENEFITS = [
  "1000 análises mensais",
  "Histórico completo",
  "Exportação Excel com análise IA",
  "Filtros avançados por setor",
];

export function CancelSubscriptionModal({
  isOpen,
  onClose,
  onCancelled,
  accessToken,
}: CancelSubscriptionModalProps) {
  const [step, setStep] = useState<Step>("reason");
  const [reason, setReason] = useState<CancelReason | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [endsAt, setEndsAt] = useState<string | null>(null);

  const triggerRef = useRef<Element | null>(null);

  // Capture trigger element and lock body scroll
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement;
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [isOpen]);

  if (!isOpen) return null;

  const resetAndClose = () => {
    setStep("reason");
    setReason(null);
    setConfirmed(false);
    setCancelling(false);
    setSubmittingFeedback(false);
    setFeedback("");
    setError(null);
    setEndsAt(null);
    onClose();
  };

  const handleSelectReason = () => {
    if (!reason) return;
    if (reason === "too_expensive" || reason === "not_using") {
      setStep("retention");
    } else {
      setStep("confirm");
    }
  };

  const handleRetentionDecline = () => {
    setStep("confirm");
  };

  const handleCancel = async () => {
    setCancelling(true);
    setError(null);
    try {
      const res = await fetch("/api/subscriptions/cancel", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || data.message || "Erro ao cancelar");
      }

      const data = await res.json();
      setEndsAt(data.ends_at);
      toast.success("Cancelamento confirmado. Acesso mantido até o fim do período.");
      onCancelled(data.ends_at);
      setStep("feedback");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cancelar");
    } finally {
      setCancelling(false);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedback.trim()) {
      resetAndClose();
      return;
    }
    setSubmittingFeedback(true);
    try {
      await fetch("/api/subscriptions/cancel-feedback", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ feedback: feedback.trim() }),
      });
      toast.success("Obrigado pelo feedback!");
    } catch {
      // Non-critical — don't block UX
    } finally {
      setSubmittingFeedback(false);
      resetAndClose();
    }
  };

  return (
    <FocusTrap
      active={isOpen}
      focusTrapOptions={{
        escapeDeactivates: true,
        onDeactivate: resetAndClose,
        allowOutsideClick: true,
        returnFocusOnDeactivate: true,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        role="alertdialog"
        aria-labelledby="cancel-title"
        aria-describedby="cancel-desc"
        className="bg-[var(--surface-0)] rounded-card border border-[var(--border)] p-6 max-w-md w-full shadow-xl"
      >
        {/* Step 1: Reason Selection (AC1) */}
        {step === "reason" && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--warning-subtle)] flex items-center justify-center flex-shrink-0">
                <svg
                  role="img"
                  aria-label="Atenção"
                  className="w-5 h-5 text-[var(--warning)]"
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
                Por que deseja cancelar?
              </h3>
            </div>

            <p id="cancel-desc" className="text-sm text-[var(--ink-secondary)] mb-4">
              Sua opinião nos ajuda a melhorar o SmartLic.
            </p>

            <div className="space-y-2 mb-6">
              {REASONS.map((r) => (
                <label
                  key={r.value}
                  className={`flex items-center gap-3 p-3 rounded-input border cursor-pointer transition-colors ${
                    reason === r.value
                      ? "border-[var(--brand-blue)] bg-[var(--brand-blue-subtle)]"
                      : "border-[var(--border)] hover:bg-[var(--surface-1)]"
                  }`}
                >
                  <input
                    type="radio"
                    name="cancel-reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="accent-[var(--brand-blue)]"
                  />
                  <span className="text-sm text-[var(--ink)]">{r.label}</span>
                </label>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={resetAndClose}
                className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                           text-[var(--ink)] bg-[var(--surface-0)]
                           hover:bg-[var(--surface-1)] transition-colors text-sm"
              >
                Voltar
              </button>
              <button
                onClick={handleSelectReason}
                disabled={!reason}
                className="flex-1 px-4 py-2.5 rounded-button bg-[var(--brand-blue)] text-white
                           hover:opacity-90 transition-opacity text-sm
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continuar
              </button>
            </div>
          </>
        )}

        {/* Step 2: Retention Offer (AC2, AC3, AC4) */}
        {step === "retention" && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--brand-blue-subtle)] flex items-center justify-center flex-shrink-0">
                <svg
                  role="img"
                  aria-label="Oferta"
                  className="w-5 h-5 text-[var(--brand-blue)]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-[var(--ink)]">
                {reason === "too_expensive"
                  ? "Temos uma oferta para você"
                  : "Que tal uma pausa?"}
              </h3>
            </div>

            {reason === "too_expensive" ? (
              /* AC3: Discount Offer */
              <div className="mb-6">
                <div className="p-4 rounded-input bg-[var(--brand-blue-subtle)] border border-[var(--brand-blue)] mb-4">
                  <p className="text-sm font-medium text-[var(--brand-blue)]">
                    20% de desconto nos próximos 3 meses
                  </p>
                  <p className="text-xs text-[var(--ink-secondary)] mt-1">
                    Continue com acesso completo por um valor reduzido enquanto avalia o retorno do SmartLic.
                  </p>
                </div>
                <a
                  href="/mensagens?assunto=desconto"
                  className="w-full py-3 px-4 rounded-button bg-[var(--brand-blue)] text-white
                             hover:opacity-90 transition-opacity
                             flex items-center justify-center gap-2 text-sm font-medium"
                >
                  Quero o desconto
                </a>
              </div>
            ) : (
              /* AC4: Pause Offer */
              <div className="mb-6">
                <div className="p-4 rounded-input bg-[var(--brand-blue-subtle)] border border-[var(--brand-blue)] mb-4">
                  <p className="text-sm font-medium text-[var(--brand-blue)]">
                    Pause sua assinatura por 30 dias
                  </p>
                  <p className="text-xs text-[var(--ink-secondary)] mt-1">
                    Sem cobrança durante a pausa. Seus dados e histórico ficam salvos para quando voltar.
                  </p>
                </div>
                <a
                  href="/mensagens?assunto=pausa"
                  className="w-full py-3 px-4 rounded-button bg-[var(--brand-blue)] text-white
                             hover:opacity-90 transition-opacity
                             flex items-center justify-center gap-2 text-sm font-medium"
                >
                  Quero pausar
                </a>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => setStep("reason")}
                className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                           text-[var(--ink)] bg-[var(--surface-0)]
                           hover:bg-[var(--surface-1)] transition-colors text-sm"
              >
                Voltar
              </button>
              <button
                onClick={handleRetentionDecline}
                className="flex-1 px-4 py-2.5 rounded-button border border-[var(--error)]
                           text-[var(--error)] bg-transparent
                           hover:bg-[var(--error-subtle)] transition-colors text-sm"
              >
                Continuar cancelamento
              </button>
            </div>
          </>
        )}

        {/* Step 3: Final Confirmation (AC5) */}
        {step === "confirm" && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--error-subtle)] flex items-center justify-center flex-shrink-0">
                <svg
                  role="img"
                  aria-label="Atenção"
                  className="w-5 h-5 text-[var(--error)]"
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
              <h3 className="text-lg font-semibold text-[var(--ink)]">
                Confirmar cancelamento
              </h3>
            </div>

            <p className="text-sm text-[var(--ink-secondary)] mb-4">
              Ao cancelar, você perderá acesso aos seguintes benefícios ao final do período:
            </p>

            <ul className="text-sm text-[var(--ink-secondary)] mb-4 space-y-2">
              {BENEFITS.map((benefit) => (
                <li key={benefit} className="flex items-center gap-2">
                  <svg
                    aria-hidden="true"
                    className="w-4 h-4 text-[var(--error)]"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                  {benefit}
                </li>
              ))}
            </ul>

            <label className="flex items-start gap-3 p-3 rounded-input border border-[var(--border)] mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="mt-0.5 accent-[var(--error)]"
              />
              <span className="text-sm text-[var(--ink)]">
                Entendo que perderei acesso aos benefícios ao final do período atual
              </span>
            </label>

            {error && (
              <div className="mb-4 p-3 bg-[var(--error-subtle)] text-[var(--error)] rounded-input text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setConfirmed(false);
                  setError(null);
                  if (reason === "too_expensive" || reason === "not_using") {
                    setStep("retention");
                  } else {
                    setStep("reason");
                  }
                }}
                disabled={cancelling}
                className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                           text-[var(--ink)] bg-[var(--surface-0)]
                           hover:bg-[var(--surface-1)] transition-colors text-sm"
              >
                Voltar
              </button>
              <button
                onClick={handleCancel}
                disabled={!confirmed || cancelling}
                className="flex-1 px-4 py-2.5 rounded-button bg-[var(--error)] text-white
                           hover:opacity-90 transition-opacity text-sm
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cancelling ? "Cancelando..." : "Confirmar cancelamento"}
              </button>
            </div>
          </>
        )}

        {/* Step 4: Post-Cancellation Feedback (AC6) */}
        {step === "feedback" && (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[var(--surface-1)] flex items-center justify-center flex-shrink-0">
                <svg
                  role="img"
                  aria-label="Feedback"
                  className="w-5 h-5 text-[var(--ink-secondary)]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-[var(--ink)]">
                Uma última coisa
              </h3>
            </div>

            <p className="text-sm text-[var(--ink-secondary)] mb-4">
              {endsAt
                ? `Seu acesso continua até ${formatDate(endsAt)}. `
                : ""}
              Tem algo que poderíamos ter feito diferente?
            </p>

            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Conte como podemos melhorar... (opcional)"
              maxLength={2000}
              rows={4}
              className="w-full p-3 rounded-input border border-[var(--border)] bg-[var(--surface-0)]
                         text-sm text-[var(--ink)] placeholder:text-[var(--ink-muted)]
                         resize-none mb-4 focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]"
            />

            <div className="flex gap-3">
              <button
                onClick={resetAndClose}
                disabled={submittingFeedback}
                className="flex-1 px-4 py-2.5 rounded-button border border-[var(--border)]
                           text-[var(--ink)] bg-[var(--surface-0)]
                           hover:bg-[var(--surface-1)] transition-colors text-sm"
              >
                Pular
              </button>
              <button
                onClick={handleSubmitFeedback}
                disabled={submittingFeedback}
                className="flex-1 px-4 py-2.5 rounded-button bg-[var(--brand-blue)] text-white
                           hover:opacity-90 transition-opacity text-sm
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submittingFeedback ? "Enviando..." : "Enviar feedback"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
    </FocusTrap>
  );
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}
