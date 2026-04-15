"use client";

/**
 * STORY-2.4: Banner de feedback do estado da conexão SSE.
 *
 * 3 variantes:
 * - reconnecting (amarelo) — "Conexão lenta. Tentando reconectar... ({tentativa}/{max})"
 * - failed       (vermelho) — "Não foi possível reconectar" + botão "Tentar novamente"
 * - polling      (azul)    — "Modo polling — atualizações a cada 3s"
 *
 * Quando state for 'connected' ou 'idle', retorna null.
 */

import { WifiOff, AlertCircle, RefreshCw } from "lucide-react";
import type { SseConnectionState } from "@/lib/sseConnectionState";

export interface ConnectionBannerProps {
  state: SseConnectionState;
  attempt?: number;
  maxAttempts?: number;
  onRetry?: () => void;
  className?: string;
}

export function ConnectionBanner({
  state,
  attempt,
  maxAttempts = 5,
  onRetry,
  className = "",
}: ConnectionBannerProps) {
  if (state === "connected" || state === "idle") return null;

  if (state === "reconnecting") {
    return (
      <div
        role="status"
        aria-live="polite"
        data-testid="connection-banner-reconnecting"
        className={`flex items-start gap-3 rounded-lg border bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-900/10 dark:border-amber-800 dark:text-amber-200 p-3 text-sm ${className}`}
      >
        <WifiOff className="h-5 w-5 flex-shrink-0 mt-0.5 text-amber-600" aria-hidden="true" />
        <div>
          <p className="font-medium">Conexão lenta. Tentando reconectar…</p>
          {attempt && (
            <p className="text-xs opacity-80 mt-0.5">
              Tentativa {attempt} de {maxAttempts}
            </p>
          )}
        </div>
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div
        role="alert"
        aria-live="assertive"
        data-testid="connection-banner-failed"
        className={`flex items-start gap-3 rounded-lg border bg-red-50 border-red-200 text-red-900 dark:bg-red-900/10 dark:border-red-800 dark:text-red-200 p-3 text-sm ${className}`}
      >
        <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5 text-red-600" aria-hidden="true" />
        <div className="flex-1">
          <p className="font-medium">Não foi possível reconectar ao servidor</p>
          <p className="text-xs opacity-80 mt-0.5">
            Tentamos várias vezes, mas a conexão não foi restaurada.
          </p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-2 inline-flex items-center rounded-md bg-white px-3 py-1.5 text-xs font-medium text-red-700 border border-red-300 hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
            >
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    );
  }

  // polling
  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="connection-banner-polling"
      className={`flex items-start gap-3 rounded-lg border bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-900/10 dark:border-blue-800 dark:text-blue-200 p-3 text-sm ${className}`}
    >
      <RefreshCw className="h-5 w-5 flex-shrink-0 mt-0.5 text-blue-600" aria-hidden="true" />
      <div>
        <p className="font-medium">Modo polling ativo</p>
        <p className="text-xs opacity-80 mt-0.5">
          A conexão em tempo real falhou — atualizações chegam a cada 3 segundos.
        </p>
      </div>
    </div>
  );
}
