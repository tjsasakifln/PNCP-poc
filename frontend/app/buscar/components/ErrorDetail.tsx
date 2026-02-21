"use client";

import { useState } from "react";
import type { SearchError } from "../hooks/useSearch";
import { toast } from "sonner";

interface ErrorDetailProps {
  /** CRIT-009 AC7: Structured error object from useSearch */
  error?: SearchError | null;
  /** Legacy fallback props for backward compatibility */
  searchId?: string | null;
  errorMessage?: string;
  timestamp?: string;
}

// CRIT-002 AC4: Error classification labels
const ERROR_CODE_LABELS: Record<string, string> = {
  TIMEOUT: "Tempo esgotado",
  RATE_LIMITED: "Muitas consultas",
  INTERNAL_ERROR: "Erro interno",
  SOURCE_UNAVAILABLE: "Fonte indisponível",
  AUTH_REQUIRED: "Sessão expirada",
  VALIDATION_ERROR: "Dados inválidos",
  QUOTA_EXCEEDED: "Limite atingido",
};

/**
 * CRIT-009 AC8-AC10: Collapsible technical detail section for error cards.
 * Shows structured error metadata (search_id, request_id, correlation_id, error_code, etc.).
 * Includes "Copiar detalhes" button that copies JSON for support tickets.
 */
export function ErrorDetail({ error, searchId, errorMessage, timestamp }: ErrorDetailProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  // CRIT-009 AC8: Support both structured SearchError and legacy props
  const effectiveSearchId = error?.searchId || searchId;
  const effectiveTimestamp = error?.timestamp || timestamp || new Date().toISOString();
  const effectiveMessage = error?.rawMessage || errorMessage;
  const errorCode = error?.errorCode;
  const correlationId = error?.correlationId;
  const requestId = error?.requestId;
  const httpStatus = error?.httpStatus;

  if (!effectiveSearchId && !effectiveMessage) return null;

  // CRIT-009 AC9: Build JSON for clipboard — formatted for support tickets
  const clipboardData: Record<string, any> = {};
  if (effectiveSearchId) clipboardData.search_id = effectiveSearchId;
  if (requestId) clipboardData.request_id = requestId;
  if (correlationId) clipboardData.correlation_id = correlationId;
  if (errorCode) clipboardData.error_code = errorCode;
  if (httpStatus) clipboardData.http_status = httpStatus;
  clipboardData.timestamp = effectiveTimestamp;
  if (effectiveMessage) clipboardData.message = effectiveMessage;

  const handleCopy = async () => {
    const jsonText = JSON.stringify(clipboardData, null, 2);
    try {
      await navigator.clipboard.writeText(jsonText);
      setCopied(true);
      toast.success("Detalhes copiados para a área de transferência");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers / non-HTTPS
      try {
        const textarea = document.createElement("textarea");
        textarea.value = jsonText;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        setCopied(true);
        toast.success("Detalhes copiados para a área de transferência");
        setTimeout(() => setCopied(false), 2000);
      } catch {
        toast.error("Não foi possível copiar. Copie manualmente.");
      }
    }
  };

  return (
    <div className="mt-2" data-testid="error-detail" role="alert" aria-label="Detalhes técnicos do erro">
      {/* CRIT-002 AC4: Error classification badge */}
      {errorCode && ERROR_CODE_LABELS[errorCode] && (
        <div className="mb-2">
          <span className="inline-flex items-center rounded-md bg-red-100 dark:bg-red-900/30 px-2 py-1 text-xs font-medium text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
            {ERROR_CODE_LABELS[errorCode]}
          </span>
        </div>
      )}
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
          {effectiveSearchId && <p>ID da busca: {effectiveSearchId}</p>}
          {requestId && <p>ID da requisicao: {requestId}</p>}
          {correlationId && <p>ID de correlacao: {correlationId}</p>}
          {errorCode && <p>Codigo do erro: {errorCode}</p>}
          {httpStatus && <p>Status HTTP: {httpStatus}</p>}
          <p>Horario: {effectiveTimestamp}</p>
          {effectiveMessage && <p>Mensagem original: {effectiveMessage}</p>}
          <button
            onClick={handleCopy}
            aria-label="Copiar detalhes técnicos do erro para a área de transferência"
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
