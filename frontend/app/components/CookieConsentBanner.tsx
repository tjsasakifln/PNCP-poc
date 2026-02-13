"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

export interface CookieConsent {
  analytics: boolean;
  timestamp: string;
}

const CONSENT_KEY = "bidiq_cookie_consent";

export function getCookieConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (typeof parsed.analytics === "boolean" && typeof parsed.timestamp === "string") {
      return parsed as CookieConsent;
    }
    return null;
  } catch {
    return null;
  }
}

export function setCookieConsent(analytics: boolean): CookieConsent {
  const consent: CookieConsent = {
    analytics,
    timestamp: new Date().toISOString(),
  };
  localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
  window.dispatchEvent(new CustomEvent("cookie-consent-changed", { detail: consent }));
  return consent;
}

export function clearCookieConsent(): void {
  localStorage.removeItem(CONSENT_KEY);
  window.dispatchEvent(new CustomEvent("cookie-consent-changed", { detail: null }));
}

export function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = getCookieConsent();
    if (!consent) {
      setVisible(true);
    }
  }, []);

  // Listen for "manage cookies" event from footer link
  useEffect(() => {
    const handleManage = () => {
      clearCookieConsent();
      setVisible(true);
    };
    window.addEventListener("manage-cookies", handleManage);
    return () => window.removeEventListener("manage-cookies", handleManage);
  }, []);

  const handleAcceptAll = useCallback(() => {
    setCookieConsent(true);
    setVisible(false);
  }, []);

  const handleRejectNonEssential = useCallback(() => {
    setCookieConsent(false);
    setVisible(false);
  }, []);

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Consentimento de cookies"
      className="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-6 bg-[var(--surface-0)] border-t border-[var(--border-strong)] shadow-lg"
    >
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div className="flex-1">
          <p className="text-sm text-[var(--ink)] font-semibold mb-1">
            Utilizamos cookies
          </p>
          <p className="text-sm text-[var(--ink-secondary)]">
            Usamos <strong>cookies essenciais</strong> (autenticação, segurança) que são sempre
            ativos, e <strong>cookies analíticos</strong> (Mixpanel) para melhorar sua
            experiência. Você pode aceitar todos ou rejeitar os não essenciais.{" "}
            <Link
              href="/privacidade"
              className="text-[var(--brand-blue)] hover:underline"
            >
              Saiba mais
            </Link>
          </p>
        </div>
        <div className="flex gap-3 flex-shrink-0">
          <button
            onClick={handleRejectNonEssential}
            className="px-4 py-2 text-sm font-medium rounded-button border border-[var(--border)]
                       text-[var(--ink-secondary)] bg-[var(--surface-0)]
                       hover:bg-[var(--surface-1)] transition-colors"
          >
            Rejeitar Não Essenciais
          </button>
          <button
            onClick={handleAcceptAll}
            className="px-4 py-2 text-sm font-medium rounded-button
                       bg-[var(--brand-blue)] text-white
                       hover:bg-[var(--brand-navy)] transition-colors"
          >
            Aceitar Todos
          </button>
        </div>
      </div>
    </div>
  );
}
