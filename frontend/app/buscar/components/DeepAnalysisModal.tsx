"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import FocusTrap from "focus-trap-react";

interface DeepAnalysisData {
  score?: number;
  decisao?: string;
  acao_recomendada?: string;
  prazo_analise?: string;
  requisitos?: string[];
  competitividade?: string;
  riscos?: string[];
  justificativas_favoraveis?: string[];
  justificativas_contra?: string[];
  recomendacao_final?: string;
  compatibilidade_pct?: number;
}

interface DeepAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  bidId: string;
  searchId?: string;
  bidData?: {
    objeto?: string;
    orgao?: string;
    valor?: number;
    modalidade?: string;
    uf?: string;
  };
  accessToken?: string | null;
  onAddToPipeline?: (bidId: string) => void;
}

function ScoreBadge({ score }: { score: number }) {
  let colorClass: string;
  if (score >= 7) {
    colorClass = "text-emerald-600 dark:text-emerald-400 border-emerald-400 dark:border-emerald-500";
  } else if (score >= 4) {
    colorClass = "text-amber-600 dark:text-amber-400 border-amber-400 dark:border-amber-500";
  } else {
    colorClass = "text-slate-500 dark:text-slate-400 border-slate-400 dark:border-slate-500";
  }

  return (
    <div
      className={`w-20 h-20 rounded-full border-4 flex flex-col items-center justify-center ${colorClass}`}
      aria-label={`Pontuação ${score} de 10`}
      data-testid="score-badge"
    >
      <span className="text-2xl font-bold leading-none">{score}</span>
      <span className="text-[10px] font-medium opacity-70">/10</span>
    </div>
  );
}

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={`bg-[var(--surface-1)] rounded animate-pulse ${className ?? "h-4 w-full"}`}
    />
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6" data-testid="loading-skeleton">
      {/* Score placeholder */}
      <div className="flex justify-center">
        <div className="w-20 h-20 rounded-full bg-[var(--surface-1)] animate-pulse" />
      </div>
      {/* Decisao */}
      <SkeletonBlock className="h-6 w-2/3 mx-auto" />
      {/* Fields */}
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <SkeletonBlock className="h-3 w-24" />
          <SkeletonBlock className="h-4 w-full" />
          <SkeletonBlock className="h-4 w-4/5" />
        </div>
      ))}
      {/* Justificativas columns */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <SkeletonBlock className="h-3 w-20" />
          {[1, 2].map((i) => (
            <SkeletonBlock key={i} className="h-4" />
          ))}
        </div>
        <div className="space-y-2">
          <SkeletonBlock className="h-3 w-20" />
          {[1, 2].map((i) => (
            <SkeletonBlock key={i} className="h-4" />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * STORY-259: Modal for deep bid analysis display.
 * Full-screen on mobile, standard modal on desktop.
 * Fetches analysis from POST /api/bid-analysis/{bidId}.
 */
export default function DeepAnalysisModal({
  isOpen,
  onClose,
  bidId,
  searchId,
  bidData,
  accessToken,
  onAddToPipeline,
}: DeepAnalysisModalProps) {
  const [analysis, setAnalysis] = useState<DeepAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addedToPipeline, setAddedToPipeline] = useState(false);
  const overlayRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const fetchAnalysis = useCallback(async () => {
    if (!bidId) return;
    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (accessToken) {
        headers["Authorization"] = `Bearer ${accessToken}`;
      }

      const res = await fetch(`/api/bid-analysis/${bidId}`, {
        method: "POST",
        headers,
        body: JSON.stringify({ search_id: searchId, bid_data: bidData }),
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        let msg = "Erro ao carregar análise";
        try {
          const parsed = JSON.parse(text);
          msg = parsed.detail || parsed.message || msg;
        } catch {
          // ignore
        }
        setError(msg);
        return;
      }

      const data = await res.json();
      setAnalysis(data);
    } catch {
      setError("Não foi possível carregar a análise. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }, [bidId, searchId, bidData, accessToken]);

  // Fetch when opened
  useEffect(() => {
    if (isOpen && !analysis && !loading) {
      fetchAnalysis();
    }
  }, [isOpen, analysis, loading, fetchAnalysis]);

  // Reset state on close
  useEffect(() => {
    if (!isOpen) {
      setAnalysis(null);
      setError(null);
      setAddedToPipeline(false);
    }
  }, [isOpen]);

  // Focus trap handles Escape key and initial focus via focus-trap-react

  // Click outside overlay
  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === overlayRef.current) onClose();
    },
    [onClose],
  );

  const handleAddToPipeline = () => {
    onAddToPipeline?.(bidId);
    setAddedToPipeline(true);
  };

  if (!isOpen) return null;

  return (
    <FocusTrap
      active={isOpen}
      focusTrapOptions={{
        escapeDeactivates: true,
        onDeactivate: onClose,
        allowOutsideClick: true,
        initialFocus: () => closeButtonRef.current || false,
        returnFocusOnDeactivate: true,
        tabbableOptions: { displayCheck: "none" },
      }}
    >
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Análise detalhada do edital"
      data-testid="deep-analysis-modal"
    >
      <div className="relative w-full sm:max-w-2xl sm:mx-4 max-h-[95dvh] sm:max-h-[85vh] overflow-y-auto bg-[var(--surface-0)] rounded-t-2xl sm:rounded-2xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-0)]">
          <h2 className="text-lg font-semibold text-[var(--ink)]">
            Análise Detalhada
          </h2>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="p-2 rounded-full text-[var(--ink-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--ink)] transition-colors"
            aria-label="Fechar modal"
            data-testid="modal-close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Bid context */}
        {bidData?.objeto && (
          <div className="px-6 pt-4 pb-2">
            <p className="text-sm text-[var(--ink-secondary)] line-clamp-2">
              {bidData.objeto}
            </p>
            {bidData.orgao && (
              <p className="text-xs text-[var(--ink-muted)] mt-0.5">
                {bidData.orgao}
                {bidData.uf ? ` — ${bidData.uf}` : ""}
              </p>
            )}
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-4 flex-1">
          {loading && <LoadingSkeleton />}

          {error && (
            <div className="text-center py-8">
              <p className="text-[var(--error)] text-sm mb-4">{error}</p>
              <button
                onClick={fetchAnalysis}
                className="px-4 py-2 text-sm bg-[var(--brand-navy)] text-white rounded-button hover:opacity-90 transition-opacity"
              >
                Tentar novamente
              </button>
            </div>
          )}

          {analysis && (
            <div className="space-y-6" data-testid="analysis-content">
              {/* Score + Decisao */}
              <div className="flex flex-col sm:flex-row items-center gap-4">
                {analysis.score != null && (
                  <ScoreBadge score={analysis.score} />
                )}
                <div className="text-center sm:text-left">
                  {analysis.decisao && (
                    <p className="text-xl font-bold text-[var(--ink)]">
                      {analysis.decisao}
                    </p>
                  )}
                  {analysis.acao_recomendada && (
                    <p className="text-sm text-[var(--ink-secondary)] mt-0.5">
                      {analysis.acao_recomendada}
                    </p>
                  )}
                  {analysis.compatibilidade_pct != null && (
                    <p className="text-xs text-[var(--ink-muted)] mt-1">
                      Compatibilidade: {Math.round(analysis.compatibilidade_pct)}%
                    </p>
                  )}
                </div>
              </div>

              {/* Key info grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {analysis.prazo_analise && (
                  <div className="p-3 bg-[var(--surface-1)] rounded-input">
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink-muted)] mb-1">
                      Prazo
                    </p>
                    <p className="text-sm text-[var(--ink)]">
                      {analysis.prazo_analise}
                    </p>
                  </div>
                )}
                {analysis.competitividade && (
                  <div className="p-3 bg-[var(--surface-1)] rounded-input">
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink-muted)] mb-1">
                      Competitividade
                    </p>
                    <p className="text-sm text-[var(--ink)]">
                      {analysis.competitividade}
                    </p>
                  </div>
                )}
              </div>

              {/* Requisitos */}
              {analysis.requisitos && analysis.requisitos.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)] mb-2">
                    Requisitos
                  </p>
                  <ul className="space-y-1">
                    {analysis.requisitos.map((req, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-[var(--ink)]"
                      >
                        <span className="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--ink-muted)] flex-shrink-0" />
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Riscos */}
              {analysis.riscos && analysis.riscos.length > 0 && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[var(--ink-muted)] mb-2">
                    Riscos
                  </p>
                  <ul className="space-y-1">
                    {analysis.riscos.map((risco, i) => (
                      <li
                        key={i}
                        className="flex items-start gap-2 text-sm text-[var(--error)]"
                      >
                        <svg
                          className="w-3.5 h-3.5 mt-0.5 flex-shrink-0"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          aria-hidden="true"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                          />
                        </svg>
                        {risco}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Justificativas — 2 columns */}
              {((analysis.justificativas_favoraveis &&
                analysis.justificativas_favoraveis.length > 0) ||
                (analysis.justificativas_contra &&
                  analysis.justificativas_contra.length > 0)) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {analysis.justificativas_favoraveis &&
                    analysis.justificativas_favoraveis.length > 0 && (
                      <div className="p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-input">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700 dark:text-emerald-400 mb-2">
                          A favor
                        </p>
                        <ul className="space-y-1">
                          {analysis.justificativas_favoraveis.map((j, i) => (
                            <li
                              key={i}
                              className="flex items-start gap-1.5 text-xs text-emerald-800 dark:text-emerald-300"
                            >
                              <span className="mt-1 text-emerald-500">+</span>
                              {j}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  {analysis.justificativas_contra &&
                    analysis.justificativas_contra.length > 0 && (
                      <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-input">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-red-700 dark:text-red-400 mb-2">
                          Contra
                        </p>
                        <ul className="space-y-1">
                          {analysis.justificativas_contra.map((j, i) => (
                            <li
                              key={i}
                              className="flex items-start gap-1.5 text-xs text-red-800 dark:text-red-300"
                            >
                              <span className="mt-1 text-red-500">-</span>
                              {j}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              )}

              {/* Recomendacao Final */}
              {analysis.recomendacao_final && (
                <div className="p-4 border border-[var(--border)] rounded-input bg-[var(--surface-0)]">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-[var(--ink-muted)] mb-1.5">
                    Recomendação Final
                  </p>
                  <p className="text-sm text-[var(--ink)] leading-relaxed">
                    {analysis.recomendacao_final}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer CTA */}
        {(analysis || loading) && (
          <div className="sticky bottom-0 px-6 py-4 border-t border-[var(--border)] bg-[var(--surface-0)]">
            <button
              onClick={handleAddToPipeline}
              disabled={loading || addedToPipeline}
              className={`w-full py-3 rounded-button font-semibold text-sm transition-colors ${
                addedToPipeline
                  ? "bg-emerald-600 text-white cursor-default"
                  : "bg-[var(--brand-navy)] text-white hover:bg-[var(--brand-blue)] disabled:opacity-50 disabled:cursor-not-allowed"
              }`}
              data-testid="add-to-pipeline-btn"
            >
              {addedToPipeline ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2.5}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Adicionado ao Pipeline
                </span>
              ) : (
                "Adicionar ao Pipeline"
              )}
            </button>
          </div>
        )}
      </div>
    </div>
    </FocusTrap>
  );
}
