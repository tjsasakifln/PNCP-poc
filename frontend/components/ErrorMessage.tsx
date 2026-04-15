"use client";

/**
 * STORY-2.3: Componente padronizado de mensagens de erro.
 *
 * Renderiza erros humanizados (catálogo em lib/errorCatalog.ts) com:
 * - Severidade visual (error/warning/info)
 * - Sentry trace ID copyable
 * - Ação primária opcional (retry/refresh/support/custom)
 * - Telemetria Mixpanel (error_message_shown)
 * - ARIA correto (role="alert" para error, role="status" para outros)
 */

import { useEffect, useState } from 'react';
import { AlertCircle, AlertTriangle, Info, Copy, Check } from 'lucide-react';
import type { ErrorSeverity } from '@/lib/errorCatalog';

export interface ErrorMessageProps {
  /** Título curto, sem jargão */
  title: string;
  /** Causa + próxima ação */
  body: string;
  /** Visual: error=vermelho, warning=âmbar, info=azul */
  severity?: ErrorSeverity;
  /** Botão de ação primária */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Sentry event ID para suporte (renderiza botão "Copiar código") */
  sentryEventId?: string;
  /** Chave do catálogo para telemetria (e.g. "search.timeout") */
  telemetryKey: string;
  /** Classes Tailwind extras */
  className?: string;
}

const SEVERITY_STYLES: Record<ErrorSeverity, { container: string; icon: string; Icon: typeof AlertCircle; ariaRole: 'alert' | 'status' }> = {
  error: {
    container: 'bg-red-50 border-red-200 text-red-900',
    icon: 'text-red-600',
    Icon: AlertCircle,
    ariaRole: 'alert',
  },
  warning: {
    container: 'bg-amber-50 border-amber-200 text-amber-900',
    icon: 'text-amber-600',
    Icon: AlertTriangle,
    ariaRole: 'status',
  },
  info: {
    container: 'bg-blue-50 border-blue-200 text-blue-900',
    icon: 'text-blue-600',
    Icon: Info,
    ariaRole: 'status',
  },
};

export function ErrorMessage({
  title,
  body,
  severity = 'error',
  action,
  sentryEventId,
  telemetryKey,
  className = '',
}: ErrorMessageProps) {
  const [copied, setCopied] = useState(false);
  const styles = SEVERITY_STYLES[severity];
  const Icon = styles.Icon;

  // STORY-2.3 AC4: emitir telemetria Mixpanel no mount
  useEffect(() => {
    if (typeof window === 'undefined') return;
    void (async () => {
      try {
        const mod = await import('mixpanel-browser');
        const mixpanel = mod.default ?? mod;
        if (mixpanel && typeof mixpanel.track === 'function') {
          mixpanel.track('error_message_shown', {
            error_type: telemetryKey,
            page: window.location.pathname,
            severity,
          });
        }
      } catch {
        // mixpanel not initialized (consent not granted) — silent
      }
    })();
  }, [telemetryKey, severity]);

  const handleCopySentryId = async () => {
    if (!sentryEventId) return;
    try {
      await navigator.clipboard.writeText(sentryEventId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  };

  return (
    <div
      role={styles.ariaRole}
      aria-live={severity === 'error' ? 'assertive' : 'polite'}
      data-testid="error-message"
      data-error-type={telemetryKey}
      className={`flex gap-3 rounded-lg border p-4 ${styles.container} ${className}`}
    >
      <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${styles.icon}`} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-sm">{body}</p>
        {(action || sentryEventId) && (
          <div className="mt-3 flex flex-wrap items-center gap-3">
            {action && (
              <button
                type="button"
                onClick={action.onClick}
                className="inline-flex items-center rounded-md bg-white px-3 py-1.5 text-sm font-medium shadow-sm border border-current hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current focus-visible:ring-offset-2"
              >
                {action.label}
              </button>
            )}
            {sentryEventId && (
              <button
                type="button"
                onClick={handleCopySentryId}
                className="inline-flex items-center gap-1.5 text-xs underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current focus-visible:ring-offset-2 rounded"
                aria-label={`Copiar código de erro ${sentryEventId}`}
              >
                {copied ? <Check className="h-3 w-3" aria-hidden="true" /> : <Copy className="h-3 w-3" aria-hidden="true" />}
                {copied ? 'Copiado' : `Código: ${sentryEventId.slice(0, 8)}…`}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
