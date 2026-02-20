"use client";

import { useState } from "react";

interface ErrorDetailProps {
  searchId?: string | null;
  errorMessage?: string;
  timestamp?: string;
}

/**
 * CRIT-006 AC25-26: Collapsible technical detail section for error cards.
 * Shows search_id, timestamp, and error details. Includes "Copy details" button.
 */
export function ErrorDetail({ searchId, errorMessage, timestamp }: ErrorDetailProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const details = [
    searchId && `ID da busca: ${searchId}`,
    timestamp && `Horario: ${timestamp}`,
    errorMessage && `Detalhes: ${errorMessage}`,
  ].filter(Boolean).join("\n");

  if (!searchId && !errorMessage) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(details);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = details;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="mt-2" data-testid="error-detail">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-xs text-ink-muted hover:text-ink-secondary transition-colors underline-offset-2 hover:underline flex items-center gap-1"
        aria-expanded={isOpen}
      >
        <svg
          className={`h-3 w-3 transition-transform ${isOpen ? "rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        Detalhes tecnicos
      </button>

      {isOpen && (
        <div className="mt-2 p-3 bg-surface-1 rounded-md text-xs text-ink-muted font-mono space-y-1">
          {searchId && <p>ID: {searchId}</p>}
          {timestamp && <p>Horario: {timestamp}</p>}
          {errorMessage && <p>Erro: {errorMessage}</p>}
          <button
            onClick={handleCopy}
            className="mt-2 inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-surface-2 hover:bg-surface-3 text-ink-secondary transition-colors"
          >
            {copied ? (
              <>
                <svg className="h-3 w-3 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                Copiado!
              </>
            ) : (
              <>
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copiar detalhes
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
