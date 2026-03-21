"use client";

import { useState } from "react";
import { Clock, Bell, CheckCircle } from "lucide-react";

interface ComingSoonPageProps {
  /** Feature title (e.g. "Alertas por E-mail") */
  title: string;
  /** Brief description of what the feature will do */
  description: string;
  /** Optional estimated launch date (e.g. "Abril 2026") */
  launchEstimate?: string;
  /** Optional callback when user opts in for notification */
  onNotifyRequest?: () => void;
}

/**
 * DEBT-FE-012: Distinctive "Coming Soon" page for feature-gated routes.
 * Shows a clear "Em breve" state instead of broken/error pages.
 */
export function ComingSoonPage({
  title,
  description,
  launchEstimate,
  onNotifyRequest,
}: ComingSoonPageProps) {
  const [notifyRequested, setNotifyRequested] = useState(false);

  const handleNotify = () => {
    setNotifyRequested(true);
    onNotifyRequest?.();
  };

  return (
    <div
      className="min-h-[70vh] flex items-center justify-center px-4"
      data-testid="coming-soon-page"
    >
      <div className="max-w-lg w-full text-center">
        {/* Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--brand-blue-subtle)] to-[var(--surface-1)]">
          <Clock
            className="h-10 w-10 text-[var(--brand-blue)]"
            strokeWidth={1.5}
            aria-hidden="true"
          />
        </div>

        {/* Heading */}
        <h1 className="text-2xl font-bold text-[var(--ink)] mb-2">
          Em breve
        </h1>
        <h2 className="text-lg font-semibold text-[var(--ink-secondary)] mb-4">
          {title}
        </h2>

        {/* Description */}
        <p className="text-sm text-[var(--ink-secondary)] mb-6 max-w-md mx-auto leading-relaxed">
          {description}
        </p>

        {/* Launch estimate */}
        {launchEstimate && (
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--surface-1)] text-sm text-[var(--ink-secondary)] mb-6">
            <Clock className="w-4 h-4" strokeWidth={1.5} aria-hidden="true" />
            <span>Previsao: {launchEstimate}</span>
          </div>
        )}

        {/* Notify button */}
        <div className="mt-2">
          {notifyRequested ? (
            <div
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-button bg-[var(--success-subtle)] text-[var(--success)] text-sm font-medium"
              data-testid="coming-soon-notified"
            >
              <CheckCircle className="w-4 h-4" strokeWidth={1.5} />
              Voce sera notificado quando estiver disponivel
            </div>
          ) : (
            <button
              onClick={handleNotify}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-button bg-[var(--brand-navy)] text-white text-sm font-semibold hover:bg-[var(--brand-blue)] transition-colors"
              data-testid="coming-soon-notify-btn"
            >
              <Bell className="w-4 h-4" strokeWidth={1.5} />
              Avise-me quando lancar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
