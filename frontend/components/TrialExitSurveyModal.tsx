"use client";

/**
 * STORY-369 AC3: Exit survey modal shown when trial expires.
 * Collects qualitative feedback on why user didn't convert.
 */

import { useState } from "react";
import { useAnalytics } from "../hooks/useAnalytics";

const SURVEY_OPTIONS = [
  { value: "no_editais", label: "Não encontrei editais relevantes para meu setor" },
  { value: "preco_alto", label: "O preço não cabe no meu orçamento agora" },
  { value: "ainda_avaliando", label: "Ainda estou avaliando, preciso de mais tempo" },
  { value: "outro", label: "Outro motivo" },
] as const;

type SurveyReason = (typeof SURVEY_OPTIONS)[number]["value"];

const STORAGE_KEY = "trial_exit_survey_submitted";

interface TrialExitSurveyModalProps {
  onClose: () => void;
}

export function TrialExitSurveyModal({ onClose }: TrialExitSurveyModalProps) {
  const [selectedReason, setSelectedReason] = useState<SurveyReason | null>(null);
  const [otherText, setOtherText] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const { trackEvent } = useAnalytics();

  const handleSubmit = async () => {
    if (!selectedReason) return;
    setLoading(true);
    try {
      await fetch("/api/trial/exit-survey", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: selectedReason,
          reason_text: selectedReason === "outro" ? otherText || null : null,
        }),
      });
      // Mark as submitted regardless of response (409 = already submitted, also OK)
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, "true");
      }
      trackEvent("trial_exit_survey_submitted", {
        reason: selectedReason,
        has_text: selectedReason === "outro" && otherText.length > 0,
      });
      setSubmitted(true);
      setTimeout(onClose, 1500);
    } catch {
      // Fail silently — survey is best-effort
      localStorage.setItem(STORAGE_KEY, "true");
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, "true");
    }
    trackEvent("trial_exit_survey_skipped");
    onClose();
  };

  if (submitted) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
        <div className="bg-[var(--canvas)] rounded-card p-8 max-w-md w-full text-center shadow-xl">
          <div className="text-4xl mb-4">🙏</div>
          <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">Obrigado pelo feedback!</h2>
          <p className="text-[var(--ink-secondary)] text-sm">Sua resposta nos ajuda a melhorar o SmartLic.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--canvas)] rounded-card p-8 max-w-md w-full shadow-xl">
        <h2 className="text-xl font-semibold text-[var(--ink)] mb-2">
          Antes de sair — pode nos contar?
        </h2>
        <p className="text-[var(--ink-secondary)] text-sm mb-6">
          Seu trial expirou. O que fez você não assinar o SmartLic Pro?
        </p>

        <div className="space-y-3 mb-6">
          {SURVEY_OPTIONS.map((option) => (
            <label
              key={option.value}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedReason === option.value
                  ? "border-[var(--brand-blue)] bg-blue-50 dark:bg-blue-950/20"
                  : "border-[var(--border)] hover:border-[var(--brand-blue)]/50"
              }`}
            >
              <input
                type="radio"
                name="survey-reason"
                value={option.value}
                checked={selectedReason === option.value}
                onChange={() => setSelectedReason(option.value)}
                className="mt-0.5 accent-[var(--brand-blue)]"
              />
              <span className="text-sm text-[var(--ink)]">{option.label}</span>
            </label>
          ))}
        </div>

        {selectedReason === "outro" && (
          <div className="mb-6">
            <textarea
              className="w-full p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--ink)] text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--brand-blue)]/50"
              rows={3}
              placeholder="Conte-nos mais (opcional)..."
              value={otherText}
              onChange={(e) => setOtherText(e.target.value)}
              maxLength={500}
            />
          </div>
        )}

        <div className="flex items-center justify-between gap-4">
          <button
            onClick={handleSkip}
            className="text-sm text-[var(--ink-secondary)] hover:text-[var(--ink)] transition-colors"
            disabled={loading}
          >
            Pular
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedReason || loading}
            className="px-6 py-2.5 bg-[var(--brand-blue)] text-white rounded-lg font-medium text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
          >
            {loading ? "Enviando..." : "Enviar resposta"}
          </button>
        </div>
      </div>
    </div>
  );
}
