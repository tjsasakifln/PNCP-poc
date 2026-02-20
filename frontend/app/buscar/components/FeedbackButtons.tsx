"use client";

import { useState, useCallback, useEffect } from "react";

/**
 * GTM-RESILIENCE-D05 AC4: Feedback buttons for search result cards.
 *
 * Thumbs-up = "correct", Thumbs-down = opens category dropdown.
 * State persisted in localStorage by search_id:bid_id.
 */

type FeedbackVerdict = "correct" | "false_positive" | "false_negative";
type FeedbackCategory =
  | "wrong_sector"
  | "irrelevant_modality"
  | "too_small"
  | "too_large"
  | "closed"
  | "other";

interface FeedbackState {
  verdict: FeedbackVerdict;
  category?: FeedbackCategory;
}

interface FeedbackButtonsProps {
  searchId: string;
  bidId: string;
  /** Context for enrichment */
  setorId?: string;
  bidObjeto?: string;
  bidValor?: number;
  bidUf?: string;
  confidenceScore?: number;
  relevanceSource?: string;
  /** Auth token for API calls */
  accessToken?: string | null;
}

const CATEGORIES: { value: FeedbackCategory; label: string }[] = [
  { value: "wrong_sector", label: "Setor errado" },
  { value: "irrelevant_modality", label: "Modalidade irrelevante" },
  { value: "too_small", label: "Valor muito baixo" },
  { value: "too_large", label: "Valor muito alto" },
  { value: "closed", label: "Ja encerrada" },
  { value: "other", label: "Outro motivo" },
];

function getFeedbackKey(searchId: string, bidId: string): string {
  return `feedback:${searchId}:${bidId}`;
}

function getSavedFeedback(searchId: string, bidId: string): FeedbackState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(getFeedbackKey(searchId, bidId));
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveFeedback(searchId: string, bidId: string, state: FeedbackState): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(getFeedbackKey(searchId, bidId), JSON.stringify(state));
  } catch {
    // localStorage full or unavailable — silently fail
  }
}

export default function FeedbackButtons({
  searchId,
  bidId,
  setorId,
  bidObjeto,
  bidValor,
  bidUf,
  confidenceScore,
  relevanceSource,
  accessToken,
}: FeedbackButtonsProps) {
  const [feedbackState, setFeedbackState] = useState<FeedbackState | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showReasonInput, setShowReasonInput] = useState(false);
  const [reason, setReason] = useState("");
  const [sending, setSending] = useState(false);
  const [toast, setToast] = useState(false);

  // Load saved state from localStorage
  useEffect(() => {
    const saved = getSavedFeedback(searchId, bidId);
    if (saved) setFeedbackState(saved);
  }, [searchId, bidId]);

  const sendFeedback = useCallback(async (
    verdict: FeedbackVerdict,
    category?: FeedbackCategory,
    reasonText?: string,
  ) => {
    setSending(true);
    try {
      const body: Record<string, unknown> = {
        search_id: searchId,
        bid_id: bidId,
        user_verdict: verdict,
        setor_id: setorId,
        bid_objeto: bidObjeto?.slice(0, 200),
        bid_valor: bidValor,
        bid_uf: bidUf,
        confidence_score: confidenceScore,
        relevance_source: relevanceSource,
      };
      if (category) body.category = category;
      if (reasonText) body.reason = reasonText.slice(0, 200);

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

      await fetch("/api/feedback", {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      const state: FeedbackState = { verdict, category };
      setFeedbackState(state);
      saveFeedback(searchId, bidId, state);
      setShowDropdown(false);
      setShowReasonInput(false);
      setReason("");

      // Show toast
      setToast(true);
      setTimeout(() => setToast(false), 3000);
    } catch (err) {
      // Silent fail — feedback is best-effort
      console.error("Feedback submit error:", err);
    } finally {
      setSending(false);
    }
  }, [searchId, bidId, setorId, bidObjeto, bidValor, bidUf, confidenceScore, relevanceSource, accessToken]);

  const handleThumbsUp = useCallback(() => {
    if (feedbackState) return; // Already submitted
    sendFeedback("correct");
  }, [feedbackState, sendFeedback]);

  const handleThumbsDown = useCallback(() => {
    if (feedbackState) return;
    setShowDropdown(prev => !prev);
  }, [feedbackState]);

  const handleCategorySelect = useCallback((cat: FeedbackCategory) => {
    if (cat === "other") {
      setShowReasonInput(true);
    } else {
      sendFeedback("false_positive", cat);
    }
  }, [sendFeedback]);

  const handleReasonSubmit = useCallback(() => {
    sendFeedback("false_positive", "other", reason);
  }, [sendFeedback, reason]);

  // Determine button states
  const isCorrect = feedbackState?.verdict === "correct";
  const isFP = feedbackState?.verdict === "false_positive";
  const hasSubmitted = feedbackState !== null;

  return (
    <div className="relative inline-flex items-center gap-1">
      {/* Thumbs Up */}
      <button
        onClick={handleThumbsUp}
        disabled={hasSubmitted || sending}
        className={`p-1.5 rounded-md transition-colors ${
          isCorrect
            ? "text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30"
            : hasSubmitted
            ? "text-ink-faint cursor-not-allowed"
            : "text-ink-muted hover:text-green-600 hover:bg-green-50 dark:hover:text-green-400 dark:hover:bg-green-900/20"
        }`}
        title={isCorrect ? "Marcado como relevante" : "Resultado relevante"}
        aria-label={isCorrect ? "Marcado como relevante" : "Marcar como relevante"}
      >
        {isCorrect ? (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M2 20h2V8H2v12zM7 20h11a2 2 0 002-1.7l1-6A2 2 0 0019 10h-6V4a2 2 0 00-2-2h-1L7 8v12z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
          </svg>
        )}
      </button>

      {/* Thumbs Down */}
      <button
        onClick={handleThumbsDown}
        disabled={hasSubmitted || sending}
        className={`p-1.5 rounded-md transition-colors ${
          isFP
            ? "text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30"
            : hasSubmitted
            ? "text-ink-faint cursor-not-allowed"
            : "text-ink-muted hover:text-red-600 hover:bg-red-50 dark:hover:text-red-400 dark:hover:bg-red-900/20"
        }`}
        title={isFP ? "Marcado como irrelevante" : "Resultado irrelevante"}
        aria-label={isFP ? "Marcado como irrelevante" : "Marcar como irrelevante"}
      >
        {isFP ? (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M22 4h-2v12h2V4zM17 4H6a2 2 0 00-2 1.7l-1 6A2 2 0 005 14h6v6a2 2 0 002 2h1l3-6V4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5" />
          </svg>
        )}
      </button>

      {/* Category Dropdown */}
      {showDropdown && !hasSubmitted && (
        <div className="absolute right-0 top-full mt-1 z-50 w-52 bg-surface-0 border border-strong rounded-lg shadow-lg py-1 animate-fade-in">
          {!showReasonInput ? (
            CATEGORIES.map((cat) => (
              <button
                key={cat.value}
                onClick={() => handleCategorySelect(cat.value)}
                disabled={sending}
                className="w-full text-left px-3 py-2 text-sm text-ink hover:bg-surface-1 transition-colors disabled:opacity-50"
              >
                {cat.label}
              </button>
            ))
          ) : (
            <div className="px-3 py-2 space-y-2">
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Motivo (max 200 chars)"
                maxLength={200}
                className="w-full text-sm border border-border rounded px-2 py-1.5 bg-surface-0 text-ink placeholder:text-ink-faint focus:outline-none focus:ring-1 focus:ring-brand-blue"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter" && reason.trim()) handleReasonSubmit();
                  if (e.key === "Escape") { setShowReasonInput(false); setShowDropdown(false); }
                }}
              />
              <button
                onClick={handleReasonSubmit}
                disabled={sending || !reason.trim()}
                className="w-full text-sm px-2 py-1.5 bg-brand-navy text-white rounded font-medium hover:bg-brand-blue-hover transition-colors disabled:opacity-50"
              >
                Enviar
              </button>
            </div>
          )}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-50 px-4 py-3 bg-green-600 text-white rounded-lg shadow-lg text-sm font-medium animate-fade-in-up">
          Feedback recebido. Obrigado por nos ajudar a melhorar!
        </div>
      )}
    </div>
  );
}
